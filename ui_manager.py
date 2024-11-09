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
)
import darkdetect

from current_playing_mode import CurrentPlayingMode


class UIManager:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.icons: dict[str, str] = {}
        self.pixmap_icons: dict[str, QPixmap] = {}
        self.default_message_line_count = 30

        self.setup_icons()
        self.setup_ui()
        self.load_settings()

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

        self.next_button = QPushButton()
        self.next_button.setIcon(self.pixmap_icons["forward"])
        self.next_button.clicked.connect(self.main_window.on_skip_pressed)
        self.next_button.setToolTip("Next")

        self.progress_slider = QSlider()
        self.progress_slider.setOrientation(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderMoved.connect(self.main_window.on_seek)

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

        # Add a source radio buttons
        self.source_radio_group = QButtonGroup()
        self.random_radio_button = QRadioButton("Random")
        self.random_radio_button.setChecked(True)
        self.favorite_radio_button = QRadioButton("Favorites")
        self.artist_radio_button = QRadioButton("Artist")

        self.random_radio_button.toggled.connect(self.on_radio_button_toggled)
        self.favorite_radio_button.toggled.connect(self.on_radio_button_toggled)
        self.artist_radio_button.toggled.connect(self.on_radio_button_toggled)

        self.source_radio_group.addButton(self.random_radio_button)
        self.source_radio_group.addButton(self.favorite_radio_button)
        self.source_radio_group.addButton(self.artist_radio_button)

        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Artist")
        self.artist_input.textChanged.connect(self.save_artist_input)

        # Create a horizontal layout for the artist radio button and input field
        artist_layout = QHBoxLayout()
        artist_layout.addWidget(self.artist_radio_button)
        artist_layout.addWidget(self.artist_input)

        # Create a vertical layout for the radio buttons
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.random_radio_button)
        radio_layout.addWidget(self.favorite_radio_button)
        radio_layout.addLayout(artist_layout)

        # Create a group box for the radio buttons
        self.source_group_box = QGroupBox("Source")
        self.source_group_box.setLayout(radio_layout)

        # Add the group box to the vertical layout
        vbox_layout.addWidget(self.source_group_box)

        # Create a horizontal layout for the buttons
        buttons_hbox_layout: QHBoxLayout = QHBoxLayout()

        # Add the buttons horizontal layout to the vertical layout
        vbox_layout.addLayout(buttons_hbox_layout)

        # Add a settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.main_window.open_settings_dialog)
        vbox_layout.addWidget(self.settings_button)

        # Add a history button
        self.history_button = QPushButton("History")
        self.history_button.clicked.connect(self.main_window.open_history_dialog)
        vbox_layout.addWidget(self.history_button)

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

    def on_radio_button_toggled(self) -> None:
        current_mode = self.get_current_playing_mode()
        self.main_window.on_playing_mode_changed(current_mode)

    def set_play_button_icon(self, icon_name: str) -> None:
        self.play_button.setIcon(self.pixmap_icons[icon_name])

    def set_stop_button_icon(self, icon_name: str) -> None:
        self.stop_button.setIcon(self.pixmap_icons[icon_name])

    def get_current_playing_mode(self) -> CurrentPlayingMode:
        if self.random_radio_button.isChecked():
            return CurrentPlayingMode.RANDOM
        elif self.favorite_radio_button.isChecked():
            return CurrentPlayingMode.FAVORITE
        elif self.artist_radio_button.isChecked():
            return CurrentPlayingMode.ARTIST
        else:
            return CurrentPlayingMode.RANDOM

    def set_current_playing_mode(
        self, current_playing_mode: CurrentPlayingMode
    ) -> None:
        if current_playing_mode == CurrentPlayingMode.FAVORITE:
            self.favorite_radio_button.setChecked(True)
            self.main_window.current_playing_mode = CurrentPlayingMode.FAVORITE
        elif current_playing_mode == CurrentPlayingMode.ARTIST:
            self.artist_radio_button.setChecked(True)
            self.main_window.current_playing_mode = CurrentPlayingMode.ARTIST
        else:
            self.random_radio_button.setChecked(True)

    def update_progress(self, position: int, length: int) -> None:
        self.progress_slider.setMaximum(length)
        self.progress_slider.setValue(position)

        self.progress_slider.setDisabled(length == 0)

        # Update the time display
        position_minutes, position_seconds = divmod(position, 60)
        length_minutes, length_seconds = divmod(length, 60)
        self.time_display.setText(
            f"{position_minutes:02}:{position_seconds:02} / {length_minutes:02}:{length_seconds:02}"
        )

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

        self.set_current_playing_mode(
            self.main_window.settings_manager.get_current_playing_mode()
        )

    def update_source_input(self) -> None:
        # Enable/disable favorite functions based on member id
        member_id_set: bool = self.main_window.settings_manager.get_member_id() != ""

        self.favorite_radio_button.setEnabled(member_id_set)

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

    def set_playing(self) -> None:
        self.stop_button.setEnabled(True)
        self.progress_slider.setEnabled(True)

    def get_playing_mode(self) -> CurrentPlayingMode:
        if self.random_radio_button.isChecked():
            return CurrentPlayingMode.RANDOM
        elif self.favorite_radio_button.isChecked():
            return CurrentPlayingMode.FAVORITE
        elif self.artist_radio_button.isChecked():
            return CurrentPlayingMode.ARTIST
        else:
            return CurrentPlayingMode.RANDOM

    def set_playing_mode(self, mode: CurrentPlayingMode) -> None:
        if mode == CurrentPlayingMode.RANDOM:
            self.random_radio_button.setChecked(True)
        elif mode == CurrentPlayingMode.FAVORITE:
            self.favorite_radio_button.setChecked(True)
        elif mode == CurrentPlayingMode.ARTIST:
            self.artist_radio_button.setChecked(True)

    def load_fonts_from_dir(self, directory: str) -> set[str]:
        families = set()
        for file_info in QDir(directory).entryInfoList(["*.ttf"]):
            _id = QFontDatabase.addApplicationFont(file_info.absoluteFilePath())
            families |= set(QFontDatabase.applicationFontFamilies(_id))
        return families

    def close_ui(self) -> None:
        self.tray_icon.hide()
