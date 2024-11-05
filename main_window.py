from enum import Enum
import os
import shutil
import tempfile
import webbrowser
from typing import Optional

from loguru import logger
from PySide6.QtCore import QSettings, Qt, Slot, QDir
from PySide6.QtGui import QAction, QFont, QIcon, QFontDatabase, QCursor
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
    QButtonGroup,
    QRadioButton,
    QGroupBox,
)
import hashlib

from audio_backends.pyaudio.audio_backend_pyuadio import AudioBackendPyAudio
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.player_backend import PlayerBackend, SongMetadata
from player_thread import PlayerThread
from settings import SettingsDialog
from web_helper import WebHelper
import darkdetect


class CurrentPlayingMode(Enum):
    RANDOM = 0
    FAVORITE = 1
    ARTIST = 2


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

        self.web_helper = WebHelper()

        self.current_module_id: str | None = None
        self.current_module_is_favorite: bool = False

    def load_fonts_from_dir(self, directory: str) -> set[str]:
        families = set()
        for file_info in QDir(directory).entryInfoList(["*.ttf"]):
            _id = QFontDatabase.addApplicationFont(file_info.absoluteFilePath())
            families |= set(QFontDatabase.applicationFontFamilies(_id))
        return families

    def setup_ui(self) -> None:
        self.icons = {}

        # Check if OS uses a dark theme via darkdetect
        if darkdetect.isDark() or self.settings.value(
            "dark_theme", type=bool, defaultValue=False
        ):
            self.icons["star_empty"] = "icons/star_empty_light.png"
            self.icons["star_full"] = "icons/star_full_light.png"
        else:
            self.icons["star_empty"] = "icons/star_empty.png"
            self.icons["star_full"] = "icons/star_full.png"

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

        # Create button for adding/removing song as favorite
        self.add_favorite_button: QPushButton = QPushButton()
        self.add_favorite_button.setIcon(QIcon(self.icons["star_empty"]))
        self.add_favorite_button.clicked.connect(self.add_favorite_button_clicked)
        self.add_favorite_button.setToolTip("Add to favorites")
        self.add_favorite_button.setFlat(True)

        # Create a horizontal layout for the buttons and slider
        hbox_layout: QHBoxLayout = QHBoxLayout()
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.stop_button)
        hbox_layout.addWidget(self.next_button)
        hbox_layout.addWidget(self.add_favorite_button)
        hbox_layout.addWidget(self.progress_slider)

        # Create a vertical layout and add the form layout and horizontal layout to it
        vbox_layout: QVBoxLayout = QVBoxLayout()
        vbox_layout.addLayout(form_layout)
        vbox_layout.addLayout(hbox_layout)
        vbox_layout.addWidget(self.message_scroll_area)

        # Add a source radio buttons
        self.source_radio_group: QButtonGroup = QButtonGroup()
        self.random_radio_button: QRadioButton = QRadioButton("Random")
        self.random_radio_button.setChecked(True)
        self.favorite_radio_button: QRadioButton = QRadioButton("Favorites")
        self.artist_radio_button: QRadioButton = QRadioButton("Artist")

        self.source_radio_group.addButton(self.random_radio_button)
        self.source_radio_group.addButton(self.favorite_radio_button)
        self.source_radio_group.addButton(self.artist_radio_button)

        self.artist_input: QLineEdit = QLineEdit()
        self.artist_input.setPlaceholderText("Artist")
        self.artist_input.textChanged.connect(self.save_artist_input)

        # Create a horizontal layout for the artist radio button and input field
        artist_layout: QHBoxLayout = QHBoxLayout()
        artist_layout.addWidget(self.artist_radio_button)
        artist_layout.addWidget(self.artist_input)

        # Create a vertical layout for the radio buttons
        radio_layout: QVBoxLayout = QVBoxLayout()
        radio_layout.addWidget(self.random_radio_button)
        radio_layout.addWidget(self.favorite_radio_button)
        radio_layout.addLayout(artist_layout)

        # Create a group box for the radio buttons
        self.source_group_box: QGroupBox = QGroupBox("Source")
        self.source_group_box.setLayout(radio_layout)

        # Add the group box to the vertical layout
        vbox_layout.addWidget(self.source_group_box)

        # Create a horizontal layout for the buttons
        buttons_hbox_layout: QHBoxLayout = QHBoxLayout()

        # Add the buttons horizontal layout to the vertical layout
        vbox_layout.addLayout(buttons_hbox_layout)

        # Add a settings button
        self.settings_button: QPushButton = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        vbox_layout.addWidget(self.settings_button)

        container: QWidget = QWidget()
        container.setLayout(vbox_layout)
        self.setCentralWidget(container)

        artist: str = str(self.settings.value("artist", ""))
        if artist:
            self.artist_input.setText(artist)

        self.update_source_input()

        # Load current playing mode
        self.set_current_playing_mode(
            CurrentPlayingMode(self.settings.value("current_playing_mode", 0))
        )

    def set_current_playing_mode(
        self, current_playing_mode: CurrentPlayingMode
    ) -> None:
        if current_playing_mode == CurrentPlayingMode.FAVORITE:
            self.favorite_radio_button.setChecked(True)
            self.current_playing_mode = CurrentPlayingMode.FAVORITE
        elif current_playing_mode == CurrentPlayingMode.ARTIST:
            self.artist_radio_button.setChecked(True)
            self.current_playing_mode = CurrentPlayingMode.ARTIST
        else:
            self.random_radio_button.setChecked(True)

    def add_favorite_button_clicked(self):
        if self.current_module_id:
            action = (
                "add_favourite"
                if not self.current_module_is_favorite
                else "remove_favourite"
            )
            webbrowser.open(
                f"https://modarchive.org/interactive.php?request={action}&query={self.current_module_id}"
            )

            self.current_module_is_favorite = not self.current_module_is_favorite

            self.add_favorite_button.setIcon(
                QIcon(self.icons["star_full"])
                if self.current_module_is_favorite
                else QIcon(self.icons["star_empty"])
            )

    def update_source_input(self):
        # Enable/disable favorite functions based on member id
        member_id_set = str(self.settings.value("member_id", "")) != ""

        self.favorite_radio_button.setEnabled(member_id_set)

        # Enable/disable artist functions based on artist input
        # artist_set = self.artist_input.text() != ""

        # self.artist_radio_button.setEnabled(artist_set)

    def open_settings_dialog(self) -> None:
        settings_dialog = SettingsDialog(self.settings, self)
        settings_dialog.setWindowTitle("Settings")
        settings_dialog.exec()

        self.update_source_input()

    @Slot()
    def save_artist_input(self) -> None:
        self.settings.setValue("artist", self.artist_input.text())

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

    def get_msm_url(self) -> Optional[str]:
        if self.song_metadata:
            return f'https://modsamplemaster.thegang.nu/module.php?sha1={self.song_metadata.get("sha1")}'
        return None

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

    def check_playing_mode(self):
        if self.random_radio_button.isChecked():
            self.current_playing_mode = CurrentPlayingMode.RANDOM
        elif self.favorite_radio_button.isChecked():
            self.current_playing_mode = CurrentPlayingMode.FAVORITE
        elif self.artist_radio_button.isChecked():
            self.current_playing_mode = CurrentPlayingMode.ARTIST

        if (
            self.current_playing_mode == CurrentPlayingMode.ARTIST
            and self.artist_input.text() == ""
        ):
            self.random_radio_button.setChecked(True)
            self.current_playing_mode = CurrentPlayingMode.RANDOM
            logger.error("No artist input, switching to random")

        return

    def load_and_play_module(self) -> None:
        logger.debug("Loading and playing module")
        self.title_label.setText("Loading...")
        self.filename_label.setText("Loading...")

        # Scroll to the top of the message label
        self.message_scroll_area.verticalScrollBar().setValue(0)

        member_id = str(self.settings.value("member_id", ""))

        self.check_playing_mode()

        match (self.current_playing_mode):
            case CurrentPlayingMode.RANDOM:
                result = self.web_helper.download_random_module(self.temp_dir)
            case CurrentPlayingMode.FAVORITE:
                if member_id:
                    result = self.web_helper.download_favorite_module(
                        member_id, self.temp_dir
                    )
                else:
                    result = None
            case CurrentPlayingMode.ARTIST:
                result = self.web_helper.download_artist_module(
                    self.artist_input.text(), self.temp_dir
                )
            case _:
                result = None

        if result is None:
            logger.error("Failed to download module")
            return

        module_filename = result.get("filename")
        module_link = result.get("module_link")
        self.current_module_id = module_link.split("?")[-1] if module_link else None

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
                self.tray_icon.showMessage(
                    "Now Playing",
                    f"{module_title}",
                    self.icon,
                    10000,
                )
                self.tray_icon.setToolTip(f"{module_title}")
                logger.debug("Module loaded and playing")

                self.current_module_is_favorite = self.check_favorite(
                    str(self.settings.value("member_id", ""))
                )
            else:
                raise ValueError("No player backend could load the module")
        else:
            raise ValueError("Invalid module URL")

    def check_favorite(self, member_id: str) -> bool:
        # Check if the module is the current members favorite
        member_favorites = self.web_helper.get_member_module_id_list(member_id)

        is_favorite = self.current_module_id in member_favorites
        self.add_favorite_button.setIcon(
            QIcon(self.icons["star_full"])
            if is_favorite
            else QIcon(self.icons["star_empty"])
        )

        if is_favorite:
            logger.debug("Current module is a member favorite")

        return is_favorite

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

        # Save current playing mode
        self.settings.setValue("current_playing_mode", self.current_playing_mode.value)

        self.settings.sync()

        self.tray_icon.hide()
        super().closeEvent(event)
