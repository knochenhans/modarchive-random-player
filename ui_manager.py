import os
from PySide6.QtCore import Qt
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


# FILE: ui_manager.py
class UIManager:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.icons: dict[str, str] = {}
        self.pixmap_icons: dict[str, QPixmap] = {}
        self.setup_icons()
        self.setup_ui()
        self.load_settings()

    def setup_ui(self) -> None:
        self.main_window.title_label = QLabel("Unknown")
        self.main_window.filename_label = QLabel("Unknown")
        self.main_window.filename_label.linkActivated.connect(
            self.main_window.open_module_link
        )
        self.main_window.player_backend_label = QLabel("Unknown")

        self.main_window.play_button = QPushButton()
        self.main_window.play_button.setIcon(self.pixmap_icons["play"])
        self.main_window.play_button.clicked.connect(self.main_window.play_pause)

        self.main_window.stop_button = QPushButton()
        self.main_window.stop_button.setIcon(self.pixmap_icons["stop"])
        self.main_window.stop_button.clicked.connect(self.main_window.stop)

        self.main_window.next_button = QPushButton()
        self.main_window.next_button.setIcon(self.pixmap_icons["forward"])
        self.main_window.next_button.clicked.connect(self.main_window.next_module)

        self.main_window.progress_slider = QSlider()
        self.main_window.progress_slider.setOrientation(Qt.Orientation.Horizontal)
        self.main_window.progress_slider.setEnabled(False)
        self.main_window.progress_slider.sliderMoved.connect(self.main_window.seek)

        # Create a multiline text label with fixed-width font
        self.main_window.multiline_label = QLabel("No module loaded")
        self.main_window.multiline_label.setWordWrap(True)
        # self.main_window.multiline_label.setFont(QFont("Courier", 10))

        # Set Topaz font for the multiline label
        font_path: str = os.path.join(os.path.dirname(__file__), "fonts")
        self.main_window.load_fonts_from_dir(font_path)
        font_db = QFontDatabase()
        font = font_db.font("TopazPlus a600a1200a4000", "Regular", 12)
        font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
        font.setFixedPitch(True)
        font.setKerning(False)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        font.setStyleHint(QFont.StyleHint.TypeWriter)

        self.main_window.multiline_label.setFont(font)

        # Set maximum lines shown to 8 and show scrollbar if more are displayed
        self.main_window.multiline_label.setMinimumHeight(
            self.main_window.fontMetrics().height() * 8
        )
        self.main_window.message_scroll_area = QScrollArea()
        self.main_window.message_scroll_area.setWidget(self.main_window.multiline_label)
        self.main_window.message_scroll_area.setWidgetResizable(True)
        self.main_window.message_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.main_window.message_scroll_area.setMinimumWidth(
            self.main_window.multiline_label.fontMetrics().horizontalAdvance(" " * 24)
        )

        # Create a form layout for the labels and their descriptions
        form_layout = QFormLayout()
        form_layout.addRow("Title:", self.main_window.title_label)
        form_layout.addRow("Filename:", self.main_window.filename_label)
        form_layout.addRow("Player backend:", self.main_window.player_backend_label)

        # Create button for adding/removing song as favorite
        self.main_window.add_favorite_button = QPushButton()
        self.main_window.add_favorite_button.setIcon(
            QIcon(fileName=str(self.icons["star_empty"]))
        )
        self.main_window.add_favorite_button.clicked.connect(
            self.main_window.add_favorite_button_clicked
        )
        self.main_window.add_favorite_button.setToolTip("Add to favorites")
        self.main_window.add_favorite_button.setFlat(True)

        # Create a horizontal layout for the buttons and slider
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.main_window.play_button)
        hbox_layout.addWidget(self.main_window.stop_button)
        hbox_layout.addWidget(self.main_window.next_button)
        hbox_layout.addWidget(self.main_window.add_favorite_button)
        hbox_layout.addWidget(self.main_window.progress_slider)

        # Create a vertical layout and add the form layout and horizontal layout to it
        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(form_layout)
        vbox_layout.addLayout(hbox_layout)
        vbox_layout.addWidget(self.main_window.message_scroll_area)

        # Add a source radio buttons
        self.main_window.source_radio_group = QButtonGroup()
        self.main_window.random_radio_button = QRadioButton("Random")
        self.main_window.random_radio_button.setChecked(True)
        self.main_window.favorite_radio_button = QRadioButton("Favorites")
        self.main_window.artist_radio_button = QRadioButton("Artist")

        self.main_window.source_radio_group.addButton(
            self.main_window.random_radio_button
        )
        self.main_window.source_radio_group.addButton(
            self.main_window.favorite_radio_button
        )
        self.main_window.source_radio_group.addButton(
            self.main_window.artist_radio_button
        )

        self.main_window.artist_input = QLineEdit()
        self.main_window.artist_input.setPlaceholderText("Artist")
        self.main_window.artist_input.textChanged.connect(self.save_artist_input)

        # Create a horizontal layout for the artist radio button and input field
        artist_layout = QHBoxLayout()
        artist_layout.addWidget(self.main_window.artist_radio_button)
        artist_layout.addWidget(self.main_window.artist_input)

        # Create a vertical layout for the radio buttons
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.main_window.random_radio_button)
        radio_layout.addWidget(self.main_window.favorite_radio_button)
        radio_layout.addLayout(artist_layout)

        # Create a group box for the radio buttons
        self.main_window.source_group_box = QGroupBox("Source")
        self.main_window.source_group_box.setLayout(radio_layout)

        # Add the group box to the vertical layout
        vbox_layout.addWidget(self.main_window.source_group_box)

        # Create a horizontal layout for the buttons
        buttons_hbox_layout: QHBoxLayout = QHBoxLayout()

        # Add the buttons horizontal layout to the vertical layout
        vbox_layout.addLayout(buttons_hbox_layout)

        # Add a settings button
        self.main_window.settings_button = QPushButton("Settings")
        self.main_window.settings_button.clicked.connect(
            self.main_window.open_settings_dialog
        )
        vbox_layout.addWidget(self.main_window.settings_button)

        container: QWidget = QWidget()
        container.setLayout(vbox_layout)
        self.main_window.setCentralWidget(container)

        self.setup_tray()

    def setup_tray(self) -> None:
        self.main_window.tray_icon = QSystemTrayIcon(self.main_window)
        self.main_window.tray_icon.setIcon(self.pixmap_icons["application_icon"])

        # Create tray menu
        self.main_window.tray_menu = self.create_tray_menu()
        self.main_window.tray_icon.setContextMenu(self.main_window.tray_menu)
        self.main_window.tray_icon.show()

        # Minimize to tray
        self.main_window.tray_icon.activated.connect(
            self.main_window.tray_icon_activated
        )
        self.main_window.hide()

    def create_tray_menu(self) -> QMenu:
        tray_menu = QMenu(self.main_window)

        play_pause_action = QAction("Play/Pause", self.main_window)
        play_pause_action.triggered.connect(self.main_window.play_pause)
        tray_menu.addAction(play_pause_action)

        stop_action = QAction("Stop", self.main_window)
        stop_action.triggered.connect(self.main_window.stop)
        tray_menu.addAction(stop_action)

        next_action = QAction("Next", self.main_window)
        next_action.triggered.connect(self.main_window.next_module)
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
        self.main_window.title_label.setText("Loading...")
        self.main_window.filename_label.setText("Loading...")
        self.main_window.message_scroll_area.verticalScrollBar().setValue(0)

    def update_title_label(self, text: str) -> None:
        self.main_window.title_label.setText(text)

    def update_filename_label(self, text: str) -> None:
        self.main_window.filename_label.setText(text)

    def update_player_backend_label(self, text: str) -> None:
        self.main_window.player_backend_label.setText(text)

    def set_play_button_icon(self, icon_name: str) -> None:
        self.main_window.play_button.setIcon(self.pixmap_icons[icon_name])

    def set_stop_button_icon(self, icon_name: str) -> None:
        self.main_window.stop_button.setIcon(self.pixmap_icons[icon_name])

    def set_current_playing_mode(
        self, current_playing_mode: CurrentPlayingMode
    ) -> None:
        if current_playing_mode == CurrentPlayingMode.FAVORITE:
            self.main_window.favorite_radio_button.setChecked(True)
            self.main_window.current_playing_mode = CurrentPlayingMode.FAVORITE
        elif current_playing_mode == CurrentPlayingMode.ARTIST:
            self.main_window.artist_radio_button.setChecked(True)
            self.main_window.current_playing_mode = CurrentPlayingMode.ARTIST
        else:
            self.main_window.random_radio_button.setChecked(True)

    def update_progress(self, length: int, position: int) -> None:
        self.main_window.progress_slider.setMaximum(length)
        self.main_window.progress_slider.setValue(position)

    def set_favorite_button(self, is_favorite: bool) -> None:
        self.main_window.add_favorite_button.setIcon(
            QIcon(str(self.icons["star_full"]))
            if is_favorite
            else QIcon(str(self.icons["star_empty"]))
        )

    def set_play_button(self, state: bool) -> None:
        if state:
            self.set_play_button_icon("play")
            self.main_window.stop_button.setEnabled(False)
        else:
            self.set_play_button_icon("pause")
            self.main_window.stop_button.setEnabled(True)

    def set_message_label(self, module_message: str) -> None:
        self.main_window.multiline_label.setText(
            module_message.replace("\r\n", "\n").replace("\r", "\n")
        )

    def get_artist_input(self) -> str:
        return self.main_window.artist_input.text()

    def load_settings(self) -> None:
        self.update_source_input()

        artist: str = self.main_window.settings_manager.get_artist()
        if artist:
            self.main_window.artist_input.setText(artist)

        self.set_current_playing_mode(
            self.main_window.settings_manager.get_current_playing_mode()
        )

    def update_source_input(self) -> None:
        # Enable/disable favorite functions based on member id
        member_id_set: bool = self.main_window.settings_manager.get_member_id() != ""

        self.main_window.favorite_radio_button.setEnabled(member_id_set)

        # Enable/disable artist functions based on artist input
        # artist_set = self.artist_input.text() != ""

        # self.artist_radio_button.setEnabled(artist_set)

    def save_artist_input(self) -> None:
        self.main_window.settings_manager.set_artist(
            self.main_window.artist_input.text()
        )

    def show_tray_notification(self, title: str, message: str) -> None:
        self.main_window.tray_icon.showMessage(
            title,
            message,
            self.main_window.icon,
            10000,
        )
        self.main_window.tray_icon.setToolTip(message)

    def set_stopped(self) -> None:
        self.main_window.stop_button.setEnabled(False)
        self.main_window.progress_slider.setEnabled(False)

    def set_playing(self) -> None:
        self.main_window.stop_button.setEnabled(True)
        self.main_window.progress_slider.setEnabled(True)

    def get_playing_mode(self) -> CurrentPlayingMode:
        if self.main_window.random_radio_button.isChecked():
            return CurrentPlayingMode.RANDOM
        elif self.main_window.favorite_radio_button.isChecked():
            return CurrentPlayingMode.FAVORITE
        elif self.main_window.artist_radio_button.isChecked():
            return CurrentPlayingMode.ARTIST
        else:
            return CurrentPlayingMode.RANDOM

    def set_playing_mode(self, mode: CurrentPlayingMode) -> None:
        if mode == CurrentPlayingMode.RANDOM:
            self.main_window.random_radio_button.setChecked(True)
        elif mode == CurrentPlayingMode.FAVORITE:
            self.main_window.favorite_radio_button.setChecked(True)
        elif mode == CurrentPlayingMode.ARTIST:
            self.main_window.artist_radio_button.setChecked(True)

    def close_ui(self) -> None:
        self.main_window.tray_icon.hide()
