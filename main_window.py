import shutil
import webbrowser
from typing import Dict

from loguru import logger
from PySide6.QtCore import QSettings, Qt, Slot
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QMainWindow, QMenu, QSystemTrayIcon

from icons import Icons
from dialogs.history_dialog import HistoryDialog
from dialogs.meta_data_dialog import MetaDataDialog
from playing_engine import PlayerEngine
from playlist.playlists_dialog import PlaylistsDialog
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.libgme.player_backend_libgme import PlayerBackendLibGME
from player_backends.player_backend import PlayerBackend
from dialogs.settings_dialog import SettingsDialog
from settings_manager import SettingsManager
from ui_manager import UIManager
from web_helper import WebHelper
from PySide6.QtCore import QTimer


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.name: str = "Mod Archive Random Player"
        self.setWindowTitle(self.name)
        self.settings = QSettings("Andre Jonas", "ModArchiveRandomPlayer")

        self.player_backends: Dict[str, type[PlayerBackend]] = {
            "LibUADE": PlayerBackendLibUADE,
            "LibOpenMPT": PlayerBackendLibOpenMPT,
            "LibGME": PlayerBackendLibGME,
        }

        self.settings_manager = SettingsManager(self.settings)

        self.icons = Icons(self.settings, self.style())
        self.icon = self.icons.pixmap_icons["application_icon"]
        self.ui_manager = UIManager(self)
        self.setWindowIcon(self.icon)

        self.ui_manager.load_settings()

        self.player_engine = PlayerEngine(
            self.ui_manager, self.settings_manager, self.player_backends
        )
        self.player_engine.set_window_title.connect(self.set_window_title)

        self.queue_check_timer = QTimer(self)
        self.queue_check_timer.timeout.connect(self.player_engine.check_queue)

        self.history_dialog = None
        self.playlist_dialog = None
        self.settings_dialog = None
        self.meta_data_dialog = None

        self.web_helper = WebHelper()

    @Slot()
    def set_window_title(self, title: str) -> None:
        self.setWindowTitle(f"{self.name} - {title}")

    def add_favorite_button_clicked(self) -> None:
        if self.player_engine.current_song:
            action = (
                "add_favourite"
                if not self.current_module_is_favorite
                else "remove_favourite"
            )
            webbrowser.open(
                f"https://modarchive.org/interactive.php?request={action}&query={self.player_engine.current_song.modarchive_id}"
            )

            self.current_module_is_favorite = not self.current_module_is_favorite
            self.ui_manager.set_favorite_button_state(self.current_module_is_favorite)

    def open_settings_dialog(self) -> None:
        if self.settings_dialog:
            self.settings_dialog.close()
            self.settings_dialog = None
        else:
            self.settings_dialog = SettingsDialog(self.settings, self)
            self.settings_dialog.setWindowTitle("Settings")
            self.settings_dialog.exec()

            self.ui_manager.update_source_input()

    @Slot()
    def on_play_pause_pressed(self) -> None:
        self.player_engine.play_pause()

    @Slot()
    def on_stop_pressed(self) -> None:
        self.player_engine.stop(True)

    @Slot()
    def on_next_pressed(self) -> None:
        self.player_engine.play_next()

    @Slot()
    def on_previous_pressed(self) -> None:
        self.player_engine.play_previous()

    @Slot()
    def open_module_link(self, link: str) -> None:
        menu = QMenu(self)

        lookup_modarchive_action = QAction("Lookup on ModArchive", self)
        lookup_modarchive_action.triggered.connect(self.on_lookup_modarchive)
        menu.addAction(lookup_modarchive_action)

        lookup_msm_action = QAction("Lookup on .mod Sample Master", self)
        lookup_msm_action.triggered.connect(self.on_lookup_msm)
        menu.addAction(lookup_msm_action)

        menu.exec_(QCursor.pos())

    @Slot()
    def on_lookup_msm(self) -> None:
        if self.player_engine.current_song:
            url: str = self.web_helper.lookup_msm_mod_url(
                self.player_engine.current_song
            )

            if url:
                webbrowser.open(url)

    @Slot()
    def on_lookup_modarchive(self) -> None:
        if self.player_engine.current_song:
            url: str = self.web_helper.lookup_modarchive_mod_url(
                self.player_engine.current_song
            )

            if url:
                webbrowser.open(url)

    def open_history_dialog(self) -> None:
        if self.history_dialog:
            self.history_dialog.close()
            self.history_dialog = None
        else:
            self.history_dialog = HistoryDialog(
                self.settings_manager,
                self.player_engine.playlist_manager,
                self.player_engine.history_playlist,
                self,
            )
            self.player_engine.history_playlist.song_added.connect(
                self.history_dialog.add_song
            )
            # self.song_info_updated.connect(history_dialog.update_song_info)
            self.history_dialog.song_on_tab_double_clicked.connect(
                self.player_engine.play_module
            )
            self.history_dialog.show()

    def open_playlists_dialog(self) -> None:
        if self.playlist_dialog:
            self.playlist_dialog.close()
            self.playlist_dialog = None
        else:
            self.playlists_dialog = PlaylistsDialog(
                self.settings_manager,
                self.player_engine.playlist_manager,
                self.player_backends,
                self,
            )
            self.playlists_dialog.song_on_tab_double_clicked.connect(
                self.player_engine.play_playlist_modules
            )
            self.playlists_dialog.show()

    def open_meta_data_dialog(self) -> None:
        if self.meta_data_dialog:
            self.meta_data_dialog.close()
            self.meta_data_dialog = None
        else:
            if self.player_engine.current_song:
                self.meta_data_dialog = MetaDataDialog(
                    self.player_engine.current_song, self
                )
                self.meta_data_dialog.show()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

    @Slot()
    def tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    @Slot()
    def closeEvent(self, event) -> None:
        self.player_engine.stop()

        self.player_engine.playlist_manager.save_playlists()
        self.player_engine.playing_settings.save()
        self.settings_manager.close()
        self.ui_manager.close_ui()

        shutil.rmtree(self.player_engine.temp_dir)

        super().closeEvent(event)
