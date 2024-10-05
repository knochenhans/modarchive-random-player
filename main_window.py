import tempfile
import webbrowser

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSlider,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from player_thread import PlayerThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.name = "Mod Archive Random Player"
        self.setWindowTitle(self.name)
        self.icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.setWindowIcon(QIcon(self.icon))

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
        self.tray_icon.setIcon(self.icon)

        # Create tray menu
        self.tray_menu = self.create_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Minimize to tray
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.hide()

    def create_tray_menu(self):
        tray_menu = QMenu(self)

        play_pause_action = QAction("Play/Pause", self)
        play_pause_action.triggered.connect(self.play_pause)
        tray_menu.addAction(play_pause_action)

        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop)
        tray_menu.addAction(stop_action)

        next_action = QAction("Next", self)
        next_action.triggered.connect(self.next_module)
        tray_menu.addAction(next_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        return tray_menu

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
            print("Stopping player thread")
            self.player_thread.stop()
            if not self.player_thread.wait(5000):
                self.player_thread.terminate()
                self.player_thread.wait()
            self.play_button.setText("Play")
            self.stop_button.setEnabled(False)
            self.progress_slider.setEnabled(False)
            print("Player thread stopped")

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
        print("Loading and playing module")
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
                self.player_thread.song_finished.connect(
                    self.next_module
                )  # Connect finished signal
                self.player_thread.position_changed.connect(
                    self.update_progress
                )  # Connect position changed signal
                self.player_thread.start()
                self.play_button.setText("Pause")
                self.stop_button.setEnabled(True)
                self.progress_slider.setEnabled(True)

                self.tray_icon.showMessage("Now Playing", module_name, self.icon, 10000)
                print("Module loaded and playing")
        else:
            raise ValueError("Invalid module URL")

    @Slot()
    def update_progress(self, position, length):
        self.progress_slider.setMaximum(length)
        self.progress_slider.setValue(position)

    @Slot()
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    @Slot()
    def closeEvent(self, event):
        self.tray_icon.hide()
        event.accept()

    @Slot()
    def quit(self):
        self.close()
