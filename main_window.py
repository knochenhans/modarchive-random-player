import tempfile
import webbrowser
from typing import Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSlider,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from audio_backend_pyuadio import AudioBackendPyAudio
from player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_thread import PlayerThread


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.name: str = "Mod Archive Random Player"
        self.setWindowTitle(self.name)
        self.icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.setWindowIcon(QIcon(self.icon))

        self.artist_label: QLabel = QLabel("Artist: Unknown")
        self.title_label: QLabel = QLabel("Title: Unknown")
        self.filename_label: QLabel = QLabel("Filename: Unknown")
        self.filename_label.setOpenExternalLinks(True)
        self.filename_label.linkActivated.connect(self.open_module_link)

        self.play_button: QPushButton = QPushButton()
        self.play_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.play_button.clicked.connect(self.play_pause)

        self.stop_button: QPushButton = QPushButton()
        self.stop_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
        )
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setEnabled(False)

        self.next_button: QPushButton = QPushButton()
        self.next_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward)
        )
        self.next_button.clicked.connect(self.next_module)

        self.progress_slider: QSlider = QSlider()
        self.progress_slider.setOrientation(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderMoved.connect(self.seek)

        # Create a multiline text label with fixed-width font
        self.multiline_label: QLabel = QLabel("No module loaded")
        self.multiline_label.setWordWrap(True)
        self.multiline_label.setFont(QFont("Courier", 10))  # Use a fixed-width font
        # self.multiline_label.setMinimumWidth(
        #     self.fontMetrics().horizontalAdvance(" " * 22 * 5)
        # )

        # Set maximum lines shown to 8 and show scrollbar if more are displayed
        self.multiline_label.setMaximumHeight(self.fontMetrics().height() * 8)
        self.message_scroll_area: QScrollArea = QScrollArea()
        self.message_scroll_area.setWidget(self.multiline_label)
        self.message_scroll_area.setWidgetResizable(True)
        self.message_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.message_scroll_area.setMinimumWidth(
            self.multiline_label.fontMetrics().horizontalAdvance(" " * 24)
        )

        # Create a vertical layout for the existing elements
        vbox_layout: QVBoxLayout = QVBoxLayout()
        vbox_layout.addWidget(self.artist_label)
        vbox_layout.addWidget(self.title_label)
        vbox_layout.addWidget(self.filename_label)
        vbox_layout.addWidget(self.play_button)
        vbox_layout.addWidget(self.stop_button)
        vbox_layout.addWidget(self.next_button)
        vbox_layout.addWidget(self.progress_slider)

        # Create a horizontal layout and add the vertical layout and multiline label to it
        hbox_layout: QHBoxLayout = QHBoxLayout()
        hbox_layout.addLayout(vbox_layout)
        hbox_layout.addWidget(self.message_scroll_area)

        container: QWidget = QWidget()
        container.setLayout(hbox_layout)
        self.setCentralWidget(container)

        self.player_backend: Optional[PlayerBackendLibOpenMPT] = None
        self.audio_backend: Optional[AudioBackendPyAudio] = None
        self.player_thread: Optional[PlayerThread] = None

        self.tray_icon: QSystemTrayIcon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon)

        # Create tray menu
        self.tray_menu: QMenu = self.create_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Minimize to tray
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.hide()

    def create_tray_menu(self) -> QMenu:
        tray_menu: QMenu = QMenu(self)

        play_pause_action: QAction = QAction("Play/Pause", self)
        play_pause_action.triggered.connect(self.play_pause)
        tray_menu.addAction(play_pause_action)

        stop_action: QAction = QAction("Stop", self)
        stop_action.triggered.connect(self.stop)
        tray_menu.addAction(stop_action)

        next_action: QAction = QAction("Next", self)
        next_action.triggered.connect(self.next_module)
        tray_menu.addAction(next_action)

        tray_menu.addSeparator()

        quit_action: QAction = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        return tray_menu

    @Slot()
    def play_pause(self) -> None:
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.pause()
            if self.player_thread.pause_flag:
                self.play_button.setIcon(
                    self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
                )
                self.stop_button.setEnabled(False)
            else:
                self.play_button.setIcon(
                    self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
                )
                self.stop_button.setEnabled(True)
        else:
            self.load_and_play_module()

    @Slot()
    def stop(self) -> None:
        if self.player_thread:
            logger.debug("Stopping player thread")
            self.player_thread.stop()
            if not self.player_thread.wait(5000):
                self.player_thread.terminate()
                self.player_thread.wait()

            self.player_backend = None
            self.audio_backend = None

            self.play_button.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            )
            self.stop_button.setEnabled(False)
            self.progress_slider.setEnabled(False)
            logger.debug("Player thread stopped")

    @Slot()
    def next_module(self) -> None:
        self.stop()
        self.load_and_play_module()

    @Slot()
    def open_module_link(self, link: str) -> None:
        # Open the link in the system's default web browser
        webbrowser.open(link)

    @Slot()
    def seek(self, position: int) -> None:
        # if self.player_thread:
        #     self.player_thread.seek(position)
        pass

    def load_and_play_module(self) -> None:
        logger.debug("Loading and playing module")
        self.artist_label.setText("Artist: Loading...")
        self.title_label.setText("Title: Loading...")
        self.filename_label.setText("Filename: Loading...")
        url: str = "https://modarchive.org/index.php?request=view_player&query=random"
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        result = soup.find("a", href=True, string=True, class_="standard-link")
        link_tag: Optional[Tag] = result if isinstance(result, Tag) else None
        if not link_tag:
            raise Exception("No module link found in the HTML response.")

        if isinstance(link_tag, Tag):
            href = link_tag["href"]
            module_url: str = href[0] if isinstance(href, list) else href
            if isinstance(module_url, list):
                module_url = module_url[0]
            if isinstance(module_url, str):
                module_response: requests.Response = requests.get(module_url)
            else:
                raise ValueError("Invalid module URL")
            module_response.raise_for_status()

            if isinstance(module_url, str):
                module_url_parts: list[str] = (
                    module_url.split("/")[-1].split("?")[-1].split("#")
                )
                module_id: str = module_url_parts[0].split("=")[-1]
                module_filename: str = module_url_parts[1]
                module_link: str = f"https://modarchive.org/module.php?{module_id}"

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_file_path: str = f"{temp_dir}/{module_filename}"
                    with open(temp_file_path, "wb") as temp_file:
                        temp_file.write(module_response.content)
                    filename: str = temp_file_path

                    with open(filename, "rb") as f:
                        module_data: bytes = f.read()
                        module_size: int = len(module_data)
                    filename = temp_file.name

                self.player_backend = PlayerBackendLibOpenMPT(module_data, module_size)
                self.audio_backend = AudioBackendPyAudio(48000, 1024)

                if not self.player_backend.load_module():
                    logger.error("Failed to load module")
                    return

                module_title: str = self.player_backend.module_metadata.get(
                    "title", "Unknown"
                )
                module_artist: str = self.player_backend.module_metadata.get(
                    "artist", "Unknown"
                )
                module_message: str = self.player_backend.module_metadata.get(
                    "message", ""
                )
                self.artist_label.setText(f"Artist: {module_artist}")
                self.title_label.setText(f"Title: {module_title}")
                self.filename_label.setText(
                    f'<a href="{module_link}">{module_filename}</a>'
                )
                self.setWindowTitle(f"{self.name} - {module_artist} - {module_title}")
                self.multiline_label.setText(
                    module_message.replace("\r\n", "\n").replace("\r", "\n")
                )

                self.player_thread = PlayerThread(
                    self.player_backend, self.audio_backend
                )
                self.player_thread.song_finished.connect(
                    self.next_module
                )  # Connect finished signal
                self.player_thread.position_changed.connect(
                    self.update_progress
                )  # Connect position changed signal
                self.player_thread.start()
                self.play_button.setIcon(
                    self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
                )
                self.stop_button.setEnabled(True)
                self.progress_slider.setEnabled(True)

                self.tray_icon.showMessage(
                    "Now Playing", f"{module_artist} - {module_title}", self.icon, 10000
                )
                logger.debug("Module loaded and playing")
        else:
            raise ValueError("Invalid module URL")

    @Slot()
    def update_progress(self, position: int, length: int) -> None:
        self.progress_slider.setMaximum(length)
        self.progress_slider.setValue(position)

    @Slot()
    def tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    @Slot()
    def closeEvent(self, event) -> None:
        self.stop()
        self.tray_icon.hide()
        event.accept()
