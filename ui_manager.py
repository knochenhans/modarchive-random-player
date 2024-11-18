import os
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QAction, QFont, QIcon, QFontDatabase, QPixmap
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
    QButtonGroup,
    QRadioButton,
    QGroupBox,
    QCheckBox,
    QComboBox,
)
import darkdetect
import pyqtspinner

from playing_modes import ModArchiveSource, PlayingMode, PlayingSource, LocalSource


class UIManager:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.icons: dict[str, str] = {}
        self.pixmap_icons: dict[str, QPixmap] = {}
        self.default_message_line_count = 30

        self.setup_icons()
        self.setup_ui()

        self.slider_value: int = 0
        self.update_slider: bool = True
        self.slider_last_length: int = -1
        self.slider_handle_default_style: str = ""

    def setup_ui(self) -> None:
        self.title_label = QLabel("Unknown")
        self.filename_label = QLabel("Unknown")
        self.filename_label.linkActivated.connect(self.main_window.open_module_link)
        self.player_backend_label = QLabel("Unknown")

        self.play_button = QPushButton()
        self.play_button.setIcon(self.pixmap_icons["play"])
        self.play_button.clicked.connect(self.main_window.on_play_pause_pressed)
        self.play_button.setToolTip("Play/Pause")

        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.pixmap_icons["stop"])
        self.stop_button.clicked.connect(self.main_window.on_stop_pressed)
        self.stop_button.setToolTip("Stop")

        self.previous_button = QPushButton()
        self.previous_button.setIcon(self.pixmap_icons["backward"])
        self.previous_button.clicked.connect(self.main_window.on_previous_pressed)
        self.previous_button.setToolTip("Previous")

        self.next_button = QPushButton()
        self.next_button.setIcon(self.pixmap_icons["forward"])
        self.next_button.clicked.connect(self.main_window.on_skip_pressed)
        self.next_button.setToolTip("Next")

        self.progress_slider = QSlider()
        self.progress_slider.setOrientation(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderMoved.connect(self.slider_moved)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        self.slider_handle_default_style = self.progress_slider.styleSheet()

        # Create a multiline text label with fixed-width font
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
        # self.message_scroll_area.setMinimumWidth(
        #     self.multiline_label.fontMetrics().horizontalAdvance(" " * 24)
        # )
        self.message_scroll_area.setMinimumHeight(
            self.main_window.fontMetrics().height() * 15
        )

        # Set height of the scroll area to the height of the text

        # default_height = (
        #     self.multiline_label.fontMetrics().height()
        #     * self.default_message_line_count
        #     + 1
        # )

        # self.message_scroll_area.resize(
        #     self.message_scroll_area.width(),
        #     default_height,
        # )

        # Create a form layout for the labels and their descriptions
        form_layout = QFormLayout()
        form_layout.addRow("Title:", self.title_label)
        form_layout.addRow("Filename:", self.filename_label)
        form_layout.addRow("Player backend:", self.player_backend_label)

        # Create button for adding/removing song as favorite
        self.add_favorite_button = QPushButton()
        self.add_favorite_button.setIcon(QIcon(fileName=str(self.icons["star_empty"])))
        self.add_favorite_button.clicked.connect(
            self.main_window.add_favorite_button_clicked
        )
        self.add_favorite_button.setToolTip("Add to favorites")
        self.add_favorite_button.setFlat(True)

        # Create a horizontal layout for the buttons
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.stop_button)
        hbox_layout.addWidget(self.next_button)
        hbox_layout.addWidget(self.add_favorite_button)

        # Create a vertical layout and add the form layout and horizontal layout to it
        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(form_layout)
        vbox_layout.addLayout(hbox_layout)

        # Create a horizontal layout for the slider and time display
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

        # Create a horizontal layout for the artist radio button and input field
        artist_layout = QHBoxLayout()
        artist_layout.addWidget(self.artist_label)
        artist_layout.addWidget(self.artist_input)

        # Create a vertical layout for the radio buttons
        modarchive_layout = QVBoxLayout()
        modarchive_layout.addLayout(artist_layout)

        # Create a group box for the radio buttons
        self.modarchive_source_group_box = QGroupBox("ModArchive Settings")
        self.modarchive_source_group_box.setLayout(modarchive_layout)

        # Add the group box to the vertical layout
        vbox_layout.addWidget(self.modarchive_source_group_box)

        ### Playing Mode and Source

        self.playing_mode_label = QLabel("Playing Mode")
        self.playing_mode_combo_box = QComboBox()
        self.playing_mode_combo_box.addItem("Linear")
        self.playing_mode_combo_box.addItem("Random")
        self.playing_mode_combo_box.currentIndexChanged.connect(
            lambda index: self.main_window.on_playing_mode_changed(PlayingMode(index))
        )

        self.playing_source_label = QLabel("Playing Source")
        self.playing_source_combo_box = QComboBox()
        self.playing_source_combo_box.addItem("Local")
        self.playing_source_combo_box.addItem("ModArchive")
        self.playing_source_combo_box.currentIndexChanged.connect(
            lambda index: self.main_window.on_playing_source_changed(
                PlayingSource(index)
            )
        )

        self.modarchive_source_label = QLabel("ModArchive Source")
        self.modarchive_source_combo_box = QComboBox()
        self.modarchive_source_combo_box.addItem("All")
        self.modarchive_source_combo_box.addItem("Favorites")
        self.modarchive_source_combo_box.addItem("Artist")
        self.modarchive_source_combo_box.currentIndexChanged.connect(
            lambda index: self.main_window.on_modarchive_source_changed(
                ModArchiveSource(index)
            )
        )

        self.local_source_label = QLabel("Local Source")
        self.local_source_combo_box = QComboBox()
        self.local_source_combo_box.addItem("Playlist")
        self.local_source_combo_box.addItem("Folder")
        self.local_source_combo_box.currentIndexChanged.connect(
            lambda index: self.main_window.on_local_source_changed(LocalSource(index))
        )

        # Preset default values
        self.set_playing_mode(PlayingMode.RANDOM)
        self.set_playing_source(PlayingSource.MODARCHIVE)
        self.set_modarchive_source(ModArchiveSource.ALL)
        self.set_local_source(LocalSource.PLAYLIST)

        # Create a group box for the playing mode and source
        self.playing_group_box = QGroupBox("Playing Settings")
        playing_layout = QVBoxLayout()
        playing_layout.addWidget(self.playing_mode_label)
        playing_layout.addWidget(self.playing_mode_combo_box)
        playing_layout.addWidget(self.playing_source_label)
        playing_layout.addWidget(self.playing_source_combo_box)
        playing_layout.addWidget(self.modarchive_source_label)
        playing_layout.addWidget(self.modarchive_source_combo_box)

        self.playing_group_box.setLayout(playing_layout)

        # Add the group box to the vertical layout
        vbox_layout.addWidget(self.playing_group_box)

        ### Addition Buttons

        # Create a horizontal layout for the buttons
        buttons_hbox_layout: QHBoxLayout = QHBoxLayout()

        # Add the buttons horizontal layout to the vertical layout
        vbox_layout.addLayout(buttons_hbox_layout)

        # Create a horizontal layout for the additional buttons
        additional_buttons_layout = QHBoxLayout()

        # Add a settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.main_window.open_settings_dialog)
        self.settings_button.setToolTip("Settings")
        self.settings_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogListView
            )
        )
        additional_buttons_layout.addWidget(self.settings_button)

        # Add a history button
        self.history_button = QPushButton("History")
        self.history_button.clicked.connect(self.main_window.open_history_dialog)
        self.history_button.setToolTip("History")
        self.history_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogContentsView
            )
        )
        additional_buttons_layout.addWidget(self.history_button)

        # Add a meta data button
        self.meta_data_button = QPushButton("Meta Data")
        self.meta_data_button.clicked.connect(self.main_window.open_meta_data_dialog)
        self.meta_data_button.setToolTip("Meta Data")
        self.meta_data_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogInfoView
            )
        )
        additional_buttons_layout.addWidget(self.meta_data_button)

        # Add a playlists button
        self.playlists_button = QPushButton("Playlists")
        self.playlists_button.clicked.connect(self.main_window.open_playlists_dialog)
        self.playlists_button.setToolTip("Playlists")
        self.playlists_button.setIcon(
            self.main_window.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        additional_buttons_layout.addWidget(self.playlists_button)

        # Add the additional buttons layout to the vertical layout
        vbox_layout.addLayout(additional_buttons_layout)

        container: QWidget = QWidget()
        container.setLayout(vbox_layout)
        self.main_window.setCentralWidget(container)

        self.setup_tray()

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
        self.tray_icon.setIcon(self.pixmap_icons["application_icon"])

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
        next_action.triggered.connect(self.main_window.on_skip_pressed)
        tray_menu.addAction(next_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self.main_window)
        quit_action.triggered.connect(self.main_window.close)
        tray_menu.addAction(quit_action)

        return tray_menu

    def setup_icons(self) -> None:
        # Check if OS uses a dark theme via darkdetect
        if darkdetect.isDark() or self.main_window.settings.value(
            "dark_theme", type=bool, defaultValue=False
        ):
            self.icons["star_empty"] = "icons/star_empty_light.png"
            self.icons["star_full"] = "icons/star_full_light.png"
        else:
            self.icons["star_empty"] = "icons/star_empty.png"
            self.icons["star_full"] = "icons/star_full.png"

        self.pixmap_icons["application_icon"] = self.main_window.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaPlay
        )
        self.pixmap_icons["play"] = self.pixmap_icons["application_icon"]
        self.pixmap_icons["pause"] = self.main_window.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaPause
        )
        self.pixmap_icons["stop"] = self.main_window.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaStop
        )
        self.pixmap_icons["forward"] = self.main_window.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaSkipForward
        )
        self.pixmap_icons["backward"] = self.main_window.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaSkipBackward
        )

    def update_loading_ui(self) -> None:
        self.title_label.setText("Loading...")
        self.filename_label.setText("Loading...")
        self.message_scroll_area.verticalScrollBar().setValue(0)

    def update_title_label(self, text: str) -> None:
        self.title_label.setText(text)

    def update_filename_label(self, text: str) -> None:
        self.filename_label.setText(text)

    def update_player_backend_label(self, text: str) -> None:
        self.player_backend_label.setText(text)

    def set_play_button_icon(self, icon_name: str) -> None:
        self.play_button.setIcon(self.pixmap_icons[icon_name])

    def set_stop_button_icon(self, icon_name: str) -> None:
        self.stop_button.setIcon(self.pixmap_icons[icon_name])

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
            QIcon(str(self.icons["star_full"]))
            if is_favorite
            else QIcon(str(self.icons["star_empty"]))
        )

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

    def load_settings(self) -> None:
        self.update_source_input()

        artist: str = self.main_window.settings_manager.get_artist()
        if artist:
            self.artist_input.setText(artist)

        self.set_playing_mode(self.main_window.settings_manager.get_playing_mode())

        self.set_playing_source(self.main_window.settings_manager.get_playing_source())

        self.set_modarchive_source(
            self.main_window.settings_manager.get_modarchive_source()
        )

        # local_folder: str = self.main_window.settings_manager.get_local_folder()
        # if local_folder:
        #     self.main_window.set_local_folder(local_folder)
        #     self.local_select_folder_button.setToolTip(local_folder)

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
        self.progress_slider.setEnabled(False)
        self.update_progress(0, 0)

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

        self.main_window.settings_manager.set_playing_mode(mode)

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

        self.main_window.settings_manager.set_playing_source(source)

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

        self.main_window.settings_manager.set_modarchive_source(source)

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

        self.main_window.settings_manager.set_local_source(source)

    def load_fonts_from_dir(self, directory: str) -> set[str]:
        families = set()
        for file_info in QDir(directory).entryInfoList(["*.ttf"]):
            _id = QFontDatabase.addApplicationFont(file_info.absoluteFilePath())
            families |= set(QFontDatabase.applicationFontFamilies(_id))
        return families

    def close_ui(self) -> None:
        self.tray_icon.hide()
