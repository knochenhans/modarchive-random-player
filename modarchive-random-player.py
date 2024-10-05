import ctypes
import os
import sys
import tempfile
import warnings
from io import BytesIO

import pyaudio
import requests
from bs4 import BeautifulSoup, Tag
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

if len(sys.argv) > 1:
    libopenmpt_path = sys.argv[1]
else:
    raise ValueError(
        "Please provide the path to libopenmpt_py as a command-line argument."
    )

sys.path.append(libopenmpt_path)
import webbrowser

from libopenmpt_py import libopenmpt
from PySide6.QtWidgets import QSlider


def log_callback(user_data, level, message):
    pass


def error_callback(user_data, message):
    pass


def libopenmpt_example_print_error(
    func_name: ctypes.c_char, mod_err: int, mod_err_str: ctypes.c_char | None
):
    if not func_name:
        func_name = ctypes.c_char(b"unknown function")

    if mod_err == libopenmpt.OPENMPT_ERROR_OUT_OF_MEMORY:
        mod_err_str = libopenmpt.openmpt_error_string(mod_err)
        if not mod_err_str:
            warnings.warn("Error: OPENMPT_ERROR_OUT_OF_MEMORY")
        else:
            warnings.warn(f"Error: {mod_err_str}")
            mod_err_str = None
    else:
        if not mod_err_str:
            mod_err_str = libopenmpt.openmpt_error_string(mod_err)
            if not mod_err_str:
                warnings.warn(f"Error: {func_name} failed.")
            else:
                warnings.warn(f"Error: {func_name} failed: {mod_err_str}")
            libopenmpt.openmpt_free_string(mod_err_str)
            mod_err_str = None


class PlayerThread(QThread):
    position_changed = Signal(int, int)  # Signal to emit position and length

    def __init__(self, module_data, module_size, parent=None):
        super().__init__(parent)
        self.module_data = module_data
        self.module_size = module_size
        self.stop_flag = False
        self.pause_flag = False

    def run(self):
        SAMPLERATE = 48000
        BUFFERSIZE = 1024
        buffer = (ctypes.c_int16 * (BUFFERSIZE * 2))()

        openmpt_log_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        openmpt_error_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        load_mod = libopenmpt.openmpt_module_create_from_memory2

        ctls = ctypes.c_void_p()
        error = ctypes.c_int()
        error_message = ctypes.c_char_p()

        mod = load_mod(
            self.module_data,  # const void * filedata
            self.module_size,  # size_t filesize
            openmpt_log_func(log_callback),  # openmpt_log_func logfunc
            None,  # void * loguser
            openmpt_error_func(error_callback),  # openmpt_error_func errfunc
            None,  # void * erruser
            ctypes.byref(error),  # int * error
            ctypes.byref(error_message),  # const char ** error_message
            ctls,  # const openmpt_module_initial_ctl * ctls
        )

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=SAMPLERATE,
            output=True,
            frames_per_buffer=BUFFERSIZE,
        )

        module_length = libopenmpt.openmpt_module_get_duration_seconds(mod)

        while not self.stop_flag:
            if self.pause_flag:
                self.msleep(100)  # Sleep for a short time to avoid busy-waiting
                continue

            libopenmpt.openmpt_module_error_clear(mod)
            count = libopenmpt.openmpt_module_read_interleaved_stereo(
                mod, SAMPLERATE, BUFFERSIZE, buffer
            )
            mod_err = libopenmpt.openmpt_module_error_get_last(mod)
            mod_err_str = libopenmpt.openmpt_module_error_get_last_message(mod)
            if mod_err != libopenmpt.OPENMPT_ERROR_OK:
                libopenmpt_example_print_error(
                    ctypes.c_char(b"openmpt_module_read_interleaved_stereo()"),
                    mod_err,
                    mod_err_str,
                )
                libopenmpt.openmpt_free_string(mod_err_str)
                mod_err_str = None
            if count == 0:
                break
            stream.write(bytes(buffer))

            # Emit position changed signal
            current_position = libopenmpt.openmpt_module_get_position_seconds(mod)
            self.position_changed.emit(int(current_position), int(module_length))

        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.stop_flag = True

    def pause(self):
        self.pause_flag = not self.pause_flag


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.name = "Mod Archive Random Player"
        self.setWindowTitle(self.name)

        self.module_label = QLabel("No module loaded")
        self.module_label.setOpenExternalLinks(True)
        self.module_label.linkActivated.connect(self.open_module_link)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_pause)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setEnabled(False)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_module)

        self.progress_slider = QSlider()
        self.progress_slider.setOrientation(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderMoved.connect(self.seek)

        layout = QVBoxLayout()
        layout.addWidget(self.module_label)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.progress_slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.player_thread = None

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.tray_icon.show()

    @Slot()
    def play_pause(self):
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.pause()
            if self.player_thread.pause_flag:
                self.play_button.setText("Play")
                self.stop_button.setEnabled(False)
            else:
                self.play_button.setText("Pause")
                self.stop_button.setEnabled(True)
        else:
            self.load_and_play_module()

    @Slot()
    def stop(self):
        if self.player_thread:
            self.player_thread.stop()
            self.player_thread.wait()
            self.play_button.setText("Play")
            self.stop_button.setEnabled(False)
            self.progress_slider.setEnabled(False)

    @Slot()
    def next_module(self):
        self.stop()
        self.load_and_play_module()

    @Slot()
    def open_module_link(self, link):
        # Open the link in the system's default web browser
        webbrowser.open(link)

    @Slot()
    def seek(self, position):
        # if self.player_thread:
        #     self.player_thread.seek(position)
        pass

    def load_and_play_module(self):
        self.module_label.setText("Loading...")
        url = "https://modarchive.org/index.php?request=view_player&query=random"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        link_tag = soup.find("a", href=True, string=True, class_="standard-link")
        if not link_tag:
            raise Exception("No module link found in the HTML response.")

        if isinstance(link_tag, Tag):
            module_url = link_tag["href"]
            if isinstance(module_url, str):
                module_response = requests.get(module_url)
            else:
                raise ValueError("Invalid module URL")
            module_response.raise_for_status()

            if isinstance(module_url, str):
                module_url_parts = module_url.split("/")[-1].split("?")[-1].split("#")
                module_id = module_url_parts[0].split("=")[-1]
                module_name = module_url_parts[1]
                module_link = f"https://modarchive.org/module.php?{module_id}"
                self.module_label.setText(f'<a href="{module_link}">{module_name}</a>')
                self.setWindowTitle(f"{self.name} - {module_name}")

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=module_name
                ) as temp_file:
                    temp_file.write(module_response.content)
                    filename = temp_file.name

                    with open(filename, "rb") as f:
                        module_data = f.read()
                        module_size = len(module_data)

                    self.player_thread = PlayerThread(module_data, module_size)
                    self.player_thread.finished.connect(
                        self.next_module
                    )  # Connect finished signal
                    self.player_thread.position_changed.connect(
                        self.update_progress
                    )  # Connect position changed signal
                    self.player_thread.start()
                    self.play_button.setText("Pause")
                    self.stop_button.setEnabled(True)
                    self.progress_slider.setEnabled(True)

                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
                self.tray_icon.showMessage("Now Playing", module_name, icon, 3000)
        else:
            raise ValueError("Invalid module URL")

    @Slot()
    def update_progress(self, position, length):
        self.progress_slider.setMaximum(length)
        self.progress_slider.setValue(position)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
