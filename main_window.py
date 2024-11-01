import os
import random
import re
import shutil
import tempfile
import webbrowser
from typing import Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger
from PySide6.QtCore import QSettings, Qt, Slot, QDir
from PySide6.QtGui import QAction, QFont, QIcon, QIntValidator, QFontDatabase, QCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSlider,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
)
import hashlib

from audio_backends.pyaudio.audio_backend_pyuadio import AudioBackendPyAudio
from history_window import HistoryWindow
from metadata_window import MetadataWindow
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.player_backend import PlayerBackend, SongMetadata
from player_thread import PlayerThread
from web_helper import WebHelper


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.name: str = "Mod Archive Random Player"
        self.setWindowTitle(self.name)
        self.icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.setWindowIcon(QIcon(self.icon))

        self.settings = QSettings("Andre Jonas", "ModArchiveRandomPlayer")

        self.setup_ui()

        self.player_backends = {
            "LibUADE": PlayerBackendLibUADE,
            "LibOpenMPT": PlayerBackendLibOpenMPT,
        }
        self.player_backend: Optional[PlayerBackend]
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

        self.temp_dir = tempfile.mkdtemp()

        self.song_metadata: SongMetadata | None = None
        self.song_history: list[SongMetadata] = []

        self.web_helper = WebHelper()

    def load_fonts_from_dir(self, directory: str) -> set[str]:
        families = set()
        for file_info in QDir(directory).entryInfoList(["*.ttf"]):
            _id = QFontDatabase.addApplicationFont(file_info.absoluteFilePath())
            families |= set(QFontDatabase.applicationFontFamilies(_id))
        return families

    def setup_ui(self) -> None:
        self.title_label: QLabel = QLabel("Unknown")
        self.filename_label: QLabel = QLabel("Unknown")
        self.filename_label.linkActivated.connect(self.open_module_link)
        self.player_backend_label: QLabel = QLabel("Unknown")

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
        # self.multiline_label.setFont(QFont("Courier", 10))

        # Set Topaz font for the multiline label
        font_path: str = os.path.join(os.path.dirname(__file__), "fonts")
        self.load_fonts_from_dir(font_path)
        font_db = QFontDatabase()
        font = font_db.font("TopazPlus a600a1200a4000", "Regular", 12)
        font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
        font.setFixedPitch(True)
        font.setKerning(False)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        font.setStyleHint(QFont.StyleHint.TypeWriter)

        self.multiline_label.setFont(font)

        # Set maximum lines shown to 8 and show scrollbar if more are displayed
        self.multiline_label.setMinimumHeight(self.fontMetrics().height() * 8)
        self.message_scroll_area: QScrollArea = QScrollArea()
        self.message_scroll_area.setWidget(self.multiline_label)
        self.message_scroll_area.setWidgetResizable(True)
        self.message_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.message_scroll_area.setMinimumWidth(
            self.multiline_label.fontMetrics().horizontalAdvance(" " * 24)
        )

        # Create a form layout for the labels and their descriptions
        form_layout: QFormLayout = QFormLayout()
        form_layout.addRow("Title:", self.title_label)
        form_layout.addRow("Filename:", self.filename_label)
        form_layout.addRow("Player backend:", self.player_backend_label)

        # Create a horizontal layout for the buttons and slider
        hbox_layout: QHBoxLayout = QHBoxLayout()
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.stop_button)
        hbox_layout.addWidget(self.next_button)
        hbox_layout.addWidget(self.progress_slider)

        # Create a vertical layout and add the form layout and horizontal layout to it
        vbox_layout: QVBoxLayout = QVBoxLayout()
        vbox_layout.addLayout(form_layout)
        vbox_layout.addLayout(hbox_layout)
        vbox_layout.addWidget(self.message_scroll_area)

        # Add a checkbox and number input field for member_id
        self.member_id_switch: QCheckBox = QCheckBox()

        self.member_id_label: QLabel = QLabel("Member ID:")
        self.member_id_label.setEnabled(False)
        self.member_id_switch.stateChanged.connect(self.toggle_member_id_input)

        self.member_id_input: QLineEdit = QLineEdit()
        self.member_id_input.setEnabled(False)
        self.member_id_input.setPlaceholderText("Member ID")
        self.member_id_input.setValidator(QIntValidator())

        # Load the member input data from settings
        member_id_switch_enabled: bool = bool(
            self.settings.value("member_id_enabled", type=bool, defaultValue=False)
        )
        self.member_id_switch.setChecked(member_id_switch_enabled)

        if member_id_switch_enabled:
            self.member_id_label.setEnabled(True)
            self.member_id_input.setEnabled(True)

        member_id: str = str(self.settings.value("member_id", ""))
        if member_id:
            self.member_id_input.setText(member_id)

        # Save the member input data when it changes
        self.member_id_input.textChanged.connect(self.save_member_input)
        self.member_id_switch.stateChanged.connect(self.save_member_input)

        # Create a horizontal layout for the switch and input field
        member_id_layout: QHBoxLayout = QHBoxLayout()
        member_id_layout.addWidget(self.member_id_switch)
        member_id_layout.addWidget(self.member_id_label)
        member_id_layout.addWidget(self.member_id_input)

        # Add the member_id layout to the vertical layout
        vbox_layout.addLayout(member_id_layout)

        # Add a checkbox and text input field for author
        self.author_switch: QCheckBox = QCheckBox()

        self.author_label: QLabel = QLabel("Author:")
        self.author_label.setEnabled(False)
        self.author_switch.stateChanged.connect(self.toggle_author_input)

        self.author_input: QLineEdit = QLineEdit()
        self.author_input.setEnabled(False)
        self.author_input.setPlaceholderText("Author")

        # Load the author input data from settings
        author_switch_enabled: bool = bool(
            self.settings.value("author_enabled", type=bool, defaultValue=False)
        )
        self.author_switch.setChecked(author_switch_enabled)

        if author_switch_enabled:
            self.author_label.setEnabled(True)
            self.author_input.setEnabled(True)

        author: str = str(self.settings.value("author", ""))
        if author:
            self.author_input.setText(author)

        # Save the author input data when it changes
        self.author_input.textChanged.connect(self.save_author_input)
        self.author_switch.stateChanged.connect(self.save_author_input)

        # Create a horizontal layout for the switch and input field
        author_layout: QHBoxLayout = QHBoxLayout()
        author_layout.addWidget(self.author_switch)
        author_layout.addWidget(self.author_label)
        author_layout.addWidget(self.author_input)

        # Add the author layout to the vertical layout
        vbox_layout.addLayout(author_layout)

        # Create a horizontal layout for the buttons
        buttons_hbox_layout: QHBoxLayout = QHBoxLayout()

        # Add a button in a new row
        self.history_button: QPushButton = QPushButton("Recent modules")
        self.history_button.clicked.connect(self.show_history)
        buttons_hbox_layout.addWidget(self.history_button)

        # Add a button to open the meta data window
        self.meta_data_button: QPushButton = QPushButton("Show Metadata")
        self.meta_data_button.clicked.connect(self.show_meta_data)
        buttons_hbox_layout.addWidget(self.meta_data_button)

        # Add the buttons horizontal layout to the vertical layout
        vbox_layout.addLayout(buttons_hbox_layout)

        container: QWidget = QWidget()
        container.setLayout(vbox_layout)
        self.setCentralWidget(container)

    @Slot()
    def toggle_member_id_input(self) -> None:
        if self.member_id_switch.isChecked():
            self.member_id_label.setEnabled(True)
            self.member_id_input.setEnabled(True)
            self.author_switch.setChecked(False)
        else:
            self.member_id_label.setEnabled(False)
            self.member_id_input.setEnabled(False)

    @Slot()
    def save_member_input(self) -> None:
        self.settings.setValue("member_id", self.member_id_input.text())
        self.settings.setValue("member_id_enabled", self.member_id_switch.isChecked())

    @Slot()
    def toggle_author_input(self) -> None:
        if self.author_switch.isChecked():
            self.author_label.setEnabled(True)
            self.author_input.setEnabled(True)
            self.member_id_switch.setChecked(False)
        else:
            self.author_label.setEnabled(False)
            self.author_input.setEnabled(False)

    @Slot()
    def save_author_input(self) -> None:
        self.settings.setValue("author", self.author_input.text())
        self.settings.setValue("author_enabled", self.author_switch.isChecked())

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

            if self.player_backend:
                self.player_backend.free_module()
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
        menu = QMenu(self)

        lookup_modarchive_action = QAction("Lookup on ModArchive", self)
        lookup_modarchive_action.triggered.connect(self.lookup_modarchive)
        menu.addAction(lookup_modarchive_action)

        lookup_msm_action = QAction("Lookup on .mod Sample Master", self)
        lookup_msm_action.triggered.connect(self.lookup_msm)
        menu.addAction(lookup_msm_action)

        menu.exec_(QCursor.pos())

    @Slot()
    def lookup_msm(self) -> None:
        if self.song_metadata:
            url: str = self.web_helper.lookup_msm_mod_url(self.song_metadata)

            if url:
                webbrowser.open(url)

    @Slot()
    def lookup_modarchive(self) -> None:
        if self.song_metadata:
            url: str = self.web_helper.lookup_modarchive_mod_url(self.song_metadata)

            if url:
                webbrowser.open(url)

    @Slot()
    def seek(self, position: int) -> None:
        # if self.player_thread:
        #     self.player_thread.seek(position)
        pass

    def get_checksums(self, filename: str) -> dict:
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()

        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
                sha1.update(chunk)

        return {"md5": md5.hexdigest(), "sha1": sha1.hexdigest()}

    def load_and_play_module(self) -> None:
        logger.debug("Loading and playing module")
        self.title_label.setText("Loading...")
        self.filename_label.setText("Loading...")

        # Scroll to the top of the message label
        self.message_scroll_area.verticalScrollBar().setValue(0)

        if self.member_id_switch.isChecked():
            result = self.web_helper.download_favorite_module(
                self.member_id_input.text(), self.temp_dir
            )
        elif self.author_switch.isChecked():
            result = self.web_helper.download_author_module(
                self.author_input.text(), self.temp_dir
            )
        else:
            result = self.web_helper.download_random_module(self.temp_dir)

        if result is None:
            logger.error("Failed to download module")
            return

        module_filename = result.get("filename")
        module_link = result.get("module_link")

        if module_filename:
            # self.audio_backend = AudioBackendPyAudio(44100, 1024)
            self.audio_backend = AudioBackendPyAudio(44100, 8192)
            backend_name = self.find_and_set_player(module_filename)

            if self.player_backend is not None and self.audio_backend is not None:
                self.song_metadata = self.player_backend.song_metadata
                self.song_metadata["filename"] = module_filename.split("/")[-1]

                if self.song_metadata.get("md5") == "":
                    md5 = self.get_checksums(module_filename).get("md5")

                    if md5:
                        self.song_metadata["md5"] = md5

                if self.song_metadata.get("sha1") == "":
                    sha1 = self.get_checksums(module_filename).get("sha1")

                    if sha1:
                        self.song_metadata["sha1"] = sha1

                module_title: str = self.song_metadata.get("title", "Unknown")
                module_message: str = self.song_metadata.get("message", "")
                self.title_label.setText(module_title)

                filename = module_filename.split("/")[-1]

                self.filename_label.setText(f'<a href="#">{filename}</a>')
                self.player_backend_label.setText(backend_name)
                self.setWindowTitle(f"{self.name} - {module_title}")
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

                # Get artist
                # artist_dict = self.web_helper.lookup_modarchive_mod_artist(
                #     self.song_metadata
                # )

                # artist = artist_dict.get("registered_artist", "")

                # if artist == "":
                #     artist = artist_dict.get("guessed_artist", "")

                # if artist != "":
                #     self.song_metadata["artist"] = artist

                self.tray_icon.showMessage(
                    "Now Playing",
                    f"{module_title}",
                    self.icon,
                    10000,
                )
                self.tray_icon.setToolTip(f"{module_title}")
                self.song_history.append(self.song_metadata)
                logger.debug("Module loaded and playing")
            else:
                raise ValueError("No player backend could load the module")
        else:
            raise ValueError("Invalid module URL")

    def find_and_set_player(self, filename) -> str:
        # Try to load the module by going through the available player backends
        for backend_name, backend_class in self.player_backends.items():
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_class()
            if player_backend is not None:
                if player_backend.load_module(filename):
                    self.player_backend = player_backend
                    break

        if self.player_backend is None:
            raise ValueError("No player backend could load the module")
        logger.debug(f"Module loaded with player backend: {backend_name}")
        return backend_name

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

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
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

        self.settings.sync()

        self.tray_icon.hide()
        super().closeEvent(event)

    @Slot()
    def show_history(self) -> None:
        self.history_window = HistoryWindow(self.song_history)
        self.history_window.show()

    @Slot()
    def show_meta_data(self) -> None:
        if self.song_metadata is not None:
            self.meta_data_window = MetadataWindow(self.song_metadata)
            self.meta_data_window.show()
