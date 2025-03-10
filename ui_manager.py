import os
from typing import Optional
from PySide6.QtCore import Qt, QDir, QObject, Slot
from PySide6.QtGui import QAction, QFont, QIcon, QFontDatabase
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSlider,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QComboBox,
)
# import pyqtspinner

from icons import Icons
from playing_modes import ModArchiveSource, PlayingMode, PlayingSource, LocalSource


class UIManager(QObject):
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        from playing_engine import PlayingEngine

        self.playing_engine: Optional[PlayingEngine] = None

        self.icons = Icons()
        self.setup_ui()

        self.slider_value: int = 0
        self.update_slider: bool = True
        self.slider_last_length: int = -1
        self.slider_handle_default_style: str = ""

    def setup_ui(self) -> None:
        self.setup_labels()
        self.setup_buttons()
        self.setup_slider()
        self.setup_multiline_label()
        self.setup_playing_settings()
        self.setup_additional_buttons()
        self.setup_layout()
        self.setup_tray()

    def setup_labels(self) -> None:
        self.title_label = QLabel("Unknown")
        self.filename_label = QLabel("Unknown")
        self.filename_label.linkActivated.connect(self.main_window.open_module_link)
        self.subsong_label = QLabel("Unknown")
        self.player_backend_label = QLabel("Unknown")

    def setup_buttons(self) -> None:
        self.play_button = QPushButton()
        self.play_button.setIcon(self.icons.pixmap_icons["play"])
        self.play_button.clicked.connect(self.main_window.on_play_pause_pressed)
        self.play_button.setToolTip("Play/Pause")

        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.icons.pixmap_icons["stop"])
        self.stop_button.clicked.connect(self.main_window.on_stop_pressed)
        self.stop_button.setToolTip("Stop")

        self.previous_button = QPushButton()
        self.previous_button.setIcon(self.icons.pixmap_icons["backward"])
        self.previous_button.clicked.connect(self.main_window.on_previous_pressed)
        self.previous_button.setToolTip("Previous")

        self.next_button = QPushButton()
        self.next_button.setIcon(self.icons.pixmap_icons["forward"])
        self.next_button.clicked.connect(self.main_window.on_next_pressed)
        self.next_button.setToolTip("Next")

        self.add_favorite_button = QPushButton()
        self.add_favorite_button.setIcon(
            QIcon(fileName=str(self.icons.icons["star_empty"]))
        )
        self.add_favorite_button.clicked.connect(
            self.main_window.add_favorite_button_clicked
        )
        self.add_favorite_button.setToolTip("Add to favorites")
        self.add_favorite_button.setFlat(True)
        sp_retain = self.add_favorite_button.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.add_favorite_button.setSizePolicy(sp_retain)
        self.show_favorite_button(False)

    def setup_slider(self) -> None:
        self.progress_slider = QSlider()
        self.progress_slider.setOrientation(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderMoved.connect(self.slider_moved)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        self.slider_handle_default_style = self.progress_slider.styleSheet()

    def setup_multiline_label(self) -> None:
        self.multiline_label = QLabel("No module loaded")
        self.multiline_label.setWordWrap(True)
        self.setup_fonts()

        self.message_scroll_area = QScrollArea()
        self.message_scroll_area.setWidget(self.multiline_label)
        self.message_scroll_area.setWidgetResizable(True)
        self.message_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.message_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.message_scroll_area.setMinimumHeight(
            self.main_window.fontMetrics().height() * 15
        )

    def setup_playing_settings(self) -> None:
        self.playing_mode_label = QLabel("Playing Mode")
        self.playing_mode_combo_box = QComboBox()
        self.playing_mode_combo_box.addItem("Linear")
        self.playing_mode_combo_box.addItem("Random")
        self.playing_mode_combo_box.currentIndexChanged.connect(
            lambda index: self.on_playing_mode_changed(PlayingMode(index))
        )

        self.playing_source_label = QLabel("Playing Source")
        self.playing_source_combo_box = QComboBox()
        self.playing_source_combo_box.addItem("Local")
        self.playing_source_combo_box.addItem("ModArchive")
        self.playing_source_combo_box.currentIndexChanged.connect(
            lambda index: self.on_playing_source_changed(PlayingSource(index))
        )

        self.modarchive_source_label = QLabel("ModArchive Source")
        self.modarchive_source_combo_box = QComboBox()
        self.modarchive_source_combo_box.addItem("All")
        self.modarchive_source_combo_box.addItem("Favorites")
        self.modarchive_source_combo_box.addItem("Artist")
        self.modarchive_source_combo_box.currentIndexChanged.connect(
            lambda index: self.on_modarchive_source_changed(ModArchiveSource(index))
        )

        self.local_source_label = QLabel("Local Source")
        self.local_source_combo_box = QComboBox()
        self.local_source_combo_box.addItem("Playlist")
        self.local_source_combo_box.addItem("Folder")
        self.local_source_combo_box.currentIndexChanged.connect(
            lambda index: self.on_local_source_changed(LocalSource(index))
        )

    def setup_additional_buttons(self) -> None:
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.main_window.open_settings_dialog)
        self.settings_button.setToolTip("Settings")
        self.settings_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogListView
            )
        )

        self.history_button = QPushButton("History")
        self.history_button.clicked.connect(self.main_window.open_history_dialog)
        self.history_button.setToolTip("History")
        self.history_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogContentsView
            )
        )

        self.meta_data_button = QPushButton("Meta Data")
        self.meta_data_button.clicked.connect(self.main_window.open_meta_data_dialog)
        self.meta_data_button.setToolTip("Meta Data")
        self.meta_data_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogInfoView
            )
        )

        self.playlists_button = QPushButton("Playlists")
        self.playlists_button.clicked.connect(self.main_window.open_playlists_dialog)
        self.playlists_button.setToolTip("Playlists")
        self.playlists_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )

    def setup_layout(self) -> None:
        form_layout = QFormLayout()
        form_layout.addRow("Title:", self.title_label)
        form_layout.addRow("Filename:", self.filename_label)
        form_layout.addRow("Subsong:", self.subsong_label)
        form_layout.addRow("Player backend:", self.player_backend_label)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.stop_button)
        hbox_layout.addWidget(self.previous_button)
        hbox_layout.addWidget(self.next_button)
        hbox_layout.addWidget(self.add_favorite_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(form_layout)
        vbox_layout.addLayout(hbox_layout)

        slider_layout = QHBoxLayout()
        self.time_display = QLabel("00:00 / 00:00")
        slider_layout.addWidget(self.progress_slider)
        slider_layout.addWidget(self.time_display)

        vbox_layout.addLayout(slider_layout)
        vbox_layout.addWidget(self.message_scroll_area)

        self.artist_label = QLabel("Artist")
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Artist")
        self.artist_input.textChanged.connect(self.save_artist_input)

        artist_layout = QHBoxLayout()
        artist_layout.addWidget(self.artist_label)
        artist_layout.addWidget(self.artist_input)

        self.artist_label.setVisible(False)
        self.artist_input.setVisible(False)

        playing_layout = QVBoxLayout()
        playing_layout.addWidget(self.playing_mode_label)
        playing_layout.addWidget(self.playing_mode_combo_box)
        playing_layout.addWidget(self.playing_source_label)
        playing_layout.addWidget(self.playing_source_combo_box)
        playing_layout.addWidget(self.modarchive_source_label)
        playing_layout.addWidget(self.modarchive_source_combo_box)
        playing_layout.addLayout(artist_layout)
        playing_layout.addWidget(self.local_source_label)
        playing_layout.addWidget(self.local_source_combo_box)

        self.playing_group_box = QGroupBox("Playing Settings")
        self.playing_group_box.setLayout(playing_layout)
        vbox_layout.addWidget(self.playing_group_box)

        buttons_hbox_layout = QHBoxLayout()
        vbox_layout.addLayout(buttons_hbox_layout)

        additional_buttons_layout = QHBoxLayout()
        additional_buttons_layout.addWidget(self.settings_button)
        additional_buttons_layout.addWidget(self.history_button)
        additional_buttons_layout.addWidget(self.meta_data_button)
        additional_buttons_layout.addWidget(self.playlists_button)
        vbox_layout.addLayout(additional_buttons_layout)

        container = QWidget()
        container.setLayout(vbox_layout)
        self.main_window.setCentralWidget(container)

    def setup_fonts(self) -> None:
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
        self.multiline_label.setMinimumHeight(
            self.main_window.fontMetrics().height() * 8
        )

    def setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self.main_window)
        self.tray_icon.setIcon(self.icons.pixmap_icons["application_icon"])

        # Create tray menu
        self.tray_menu = self.create_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Minimize to tray
        self.tray_icon.activated.connect(self.main_window.tray_icon_activated)
        self.main_window.hide()

    def create_tray_menu(self) -> QMenu:
        tray_menu = QMenu(self.main_window)

        play_pause_action = QAction("Play/Pause", self.main_window)
        play_pause_action.triggered.connect(self.main_window.on_play_pause_pressed)
        tray_menu.addAction(play_pause_action)

        stop_action = QAction("Stop", self.main_window)
        stop_action.triggered.connect(self.main_window.on_stop_pressed)
        tray_menu.addAction(stop_action)

        next_action = QAction("Next", self.main_window)
        next_action.triggered.connect(self.main_window.on_next_pressed)
        tray_menu.addAction(next_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self.main_window)
        quit_action.triggered.connect(self.main_window.close)
        tray_menu.addAction(quit_action)

        return tray_menu

    def update_loading_ui(self) -> None:
        self.title_label.setText("Loading...")
        self.filename_label.setText("Loading...")
        self.message_scroll_area.verticalScrollBar().setValue(0)

    @Slot(str)
    def update_title_label(self, text: str) -> None:
        self.title_label.setText(text)

    def update_filename_label(self, text: str) -> None:
        self.filename_label.setText(text)

    @Slot(int, int)
    def update_subsong_info(self, current: int, max: int) -> None:
        self.subsong_label.setText(f"{current} / {max}")

    def update_player_backend_label(self, text: str) -> None:
        self.player_backend_label.setText(text)

    def set_play_button_icon(self, icon_name: str) -> None:
        self.play_button.setIcon(self.icons.pixmap_icons[icon_name])

    def set_stop_button_icon(self, icon_name: str) -> None:
        self.stop_button.setIcon(self.icons.pixmap_icons[icon_name])

    def update_progress(self, position: int, length: int) -> None:
        if length != self.slider_last_length:
            if length == 0:
                self.progress_slider.setStyleSheet(
                    "QSlider::handle:horizontal {background: transparent;}"
                )
            else:
                self.progress_slider.setStyleSheet(self.slider_handle_default_style)
            self.slider_last_length = length

        if self.update_slider:
            self.progress_slider.setMaximum(length)
            self.progress_slider.setValue(position)

        self.progress_slider.setDisabled(length == 0)

        # Update the time display
        position_minutes, position_seconds = divmod(position, 60)
        length_minutes, length_seconds = divmod(length, 60)
        self.time_display.setText(
            f"{position_minutes:02}:{position_seconds:02} / {length_minutes:02}:{length_seconds:02}"
        )

    def slider_pressed(self) -> None:
        self.update_slider = False

    def slider_moved(self) -> None:
        self.slider_value = self.progress_slider.value()

    def slider_released(self) -> None:
        self.update_slider = True
        self.update_progress(self.slider_value, self.progress_slider.maximum())
        self.main_window.seek(self.slider_value)

    def set_favorite_button_state(self, is_favorite: bool) -> None:
        self.add_favorite_button.setIcon(
            QIcon(str(self.icons.icons["star_full"]))
            if is_favorite
            else QIcon(str(self.icons.icons["star_empty"]))
        )

    def show_favorite_button(self, show: bool) -> None:
        self.add_favorite_button.setVisible(show)

    def set_play_button(self, state: bool) -> None:
        if state:
            self.set_play_button_icon("play")
            self.stop_button.setEnabled(False)
        else:
            self.set_play_button_icon("pause")
            self.stop_button.setEnabled(True)

    def set_message_label(self, module_message: str) -> None:
        self.multiline_label.setText(
            module_message.replace("\r\n", "\n").replace("\r", "\n")
        )

        # # Set height of the scroll area to the height of the text
        # self.message_scroll_area.setMinimumHeight(
        #     self.multiline_label.fontMetrics().height()
        #     * self.multiline_label.text().count("\n")
        #     + 1
        # )

    def get_artist_input(self) -> str:
        return self.artist_input.text()

    def on_playing_mode_changed(self, mode: PlayingMode) -> None:
        if self.playing_engine:
            self.playing_engine.set_playing_mode(mode)

    def on_playing_source_changed(self, source: PlayingSource) -> None:
        if self.playing_engine:
            self.playing_engine.set_playing_source(source)

        if source == PlayingSource.LOCAL:
            self.modarchive_source_label.hide()
            self.modarchive_source_combo_box.hide()
            self.local_source_label.show()
            self.local_source_combo_box.show()
        else:
            self.modarchive_source_label.show()
            self.modarchive_source_combo_box.show()
            self.local_source_label.hide()
            self.local_source_combo_box.hide()

    def on_modarchive_source_changed(self, source: ModArchiveSource) -> None:
        if self.playing_engine:
            self.playing_engine.set_modarchive_source(source)

        if source == ModArchiveSource.ARTIST:
            self.artist_label.setVisible(True)
            self.artist_input.setVisible(True)
        else:
            self.artist_label.setVisible(False)
            self.artist_input.setVisible(False)

    def on_local_source_changed(self, source: LocalSource) -> None:
        if self.playing_engine:
            self.playing_engine.set_local_source(source)

    def load_settings(self) -> None:
        self.update_source_input()

        artist: str = self.main_window.settings_manager.get_artist()
        if artist:
            self.artist_input.setText(artist)

    def update_source_input(self) -> None:
        # Enable/disable favorite functions based on member id
        member_id_set: bool = self.main_window.settings_manager.get_member_id() != ""

        # self.favorite_radio_button.setEnabled(member_id_set)

    def save_artist_input(self) -> None:
        self.main_window.settings_manager.set_artist(self.artist_input.text())

    def show_tray_notification(self, title: str, message: str) -> None:
        self.tray_icon.showMessage(
            title,
            message,
            self.main_window.icon,
            10000,
        )
        self.tray_icon.setToolTip(message)

    def set_stopped(self) -> None:
        self.stop_button.setEnabled(False)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)

    def set_playing(self) -> None:
        self.stop_button.setEnabled(True)
        self.progress_slider.setEnabled(True)

    def get_playing_mode(self) -> PlayingMode:
        if self.playing_mode_combo_box.currentText() == "Linear":
            return PlayingMode.LINEAR
        elif self.playing_mode_combo_box.currentText() == "Random":
            return PlayingMode.RANDOM
        else:
            return PlayingMode.RANDOM

    def set_playing_mode(self, mode: PlayingMode) -> None:
        if mode == PlayingMode.LINEAR:
            self.playing_mode_combo_box.setCurrentIndex(0)
        elif mode == PlayingMode.RANDOM:
            self.playing_mode_combo_box.setCurrentIndex(1)

    def get_playing_source(self) -> PlayingSource:
        if self.playing_source_combo_box.currentText() == "Local":
            return PlayingSource.LOCAL
        elif self.playing_source_combo_box.currentText() == "ModArchive":
            return PlayingSource.MODARCHIVE
        else:
            return PlayingSource.MODARCHIVE

    def set_playing_source(self, source: PlayingSource) -> None:
        if source == PlayingSource.LOCAL:
            self.playing_source_combo_box.setCurrentIndex(0)
        elif source == PlayingSource.MODARCHIVE:
            self.playing_source_combo_box.setCurrentIndex(1)

    def get_modarchive_source(self) -> ModArchiveSource:
        if self.modarchive_source_combo_box.currentText() == "All":
            return ModArchiveSource.ALL
        elif self.modarchive_source_combo_box.currentText() == "Favorites":
            return ModArchiveSource.FAVORITES
        elif self.modarchive_source_combo_box.currentText() == "Artist":
            return ModArchiveSource.ARTIST
        else:
            return ModArchiveSource.ALL

    def set_modarchive_source(self, source: ModArchiveSource) -> None:
        if source == ModArchiveSource.ALL:
            self.modarchive_source_combo_box.setCurrentIndex(0)
        elif source == ModArchiveSource.FAVORITES:
            self.modarchive_source_combo_box.setCurrentIndex(1)
        elif source == ModArchiveSource.ARTIST:
            self.modarchive_source_combo_box.setCurrentIndex(2)

    def get_local_source(self) -> LocalSource:
        if self.local_source_combo_box.currentText() == "Playlist":
            return LocalSource.PLAYLIST
        elif self.local_source_combo_box.currentText() == "Folder":
            return LocalSource.FOLDER
        else:
            return LocalSource.PLAYLIST

    def set_local_source(self, source: LocalSource) -> None:
        if source == LocalSource.PLAYLIST:
            self.local_source_combo_box.setCurrentIndex(0)
        elif source == LocalSource.FOLDER:
            self.local_source_combo_box.setCurrentIndex(1)

    def load_fonts_from_dir(self, directory: str) -> set[str]:
        families = set()
        for file_info in QDir(directory).entryInfoList(["*.ttf"]):
            _id = QFontDatabase.addApplicationFont(file_info.absoluteFilePath())
            families |= set(QFontDatabase.applicationFontFamilies(_id))
        return families

    def close(self) -> None:
        self.tray_icon.hide()
