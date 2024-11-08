import webbrowser
from typing import Optional, Dict

from loguru import logger
from PySide6.QtCore import QSettings, Qt, Slot, QThread, Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
)
import hashlib

from audio_backends.pyaudio.audio_backend_pyuadio import AudioBackendPyAudio
from current_playing_mode import CurrentPlayingMode
from download_manager import DownloadManager
from module_loader_thread import ModuleLoaderThread
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.player_backend import PlayerBackend, Song
from player_thread import PlayerThread
from settings_dialog import SettingsDialog
from settings_manager import SettingsManager
from ui_manager import UIManager
from web_helper import WebHelper


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.name: str = "Mod Archive Random Player"
        self.setWindowTitle(self.name)
        self.settings = QSettings("Andre Jonas", "ModArchiveRandomPlayer")
        self.settings_manager = SettingsManager(self.settings)

        self.ui_manager = UIManager(self)
        self.icon = self.ui_manager.pixmap_icons["application_icon"]
        self.setWindowIcon(self.icon)
        self.web_helper = WebHelper()
        self.download_manager = DownloadManager(self.web_helper)

        self.player_backends: Dict[str, type[PlayerBackend]] = {
            "LibUADE": PlayerBackendLibUADE,
            "LibOpenMPT": PlayerBackendLibOpenMPT,
        }
        self.player_backend: Optional[PlayerBackend] = None
        self.audio_backend: Optional[AudioBackendPyAudio] = None
        self.player_thread: Optional[PlayerThread] = None
        self.module_loader_thread: Optional[ModuleLoaderThread] = None

        self.song: Optional[Song] = None

        self.current_song: Optional[Song] = None
        self.current_module_is_favorite: bool = False
        self.current_playing_mode: CurrentPlayingMode = CurrentPlayingMode.RANDOM

        self.ui_manager.load_settings()

        self.playlist: list[Song] = []

        self.wait_for_loading = False

    def add_favorite_button_clicked(self) -> None:
        if self.current_song:
            action = (
                "add_favourite"
                if not self.current_module_is_favorite
                else "remove_favourite"
            )
            webbrowser.open(
                f"https://modarchive.org/interactive.php?request={action}&query={self.current_song.modarchive_id}"
            )

            self.current_module_is_favorite = not self.current_module_is_favorite
            self.ui_manager.set_favorite_button_state(self.current_module_is_favorite)

    def open_settings_dialog(self) -> None:
        settings_dialog = SettingsDialog(self.settings, self)
        settings_dialog.setWindowTitle("Settings")
        settings_dialog.exec()

        self.ui_manager.update_source_input()

    @Slot()
    def on_play_pause_pressed(self) -> None:
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.pause()
            self.ui_manager.set_play_button(self.player_thread.pause_flag)
        else:
            # self.ui_manager.update_loading_ui()
            self.load_random_module()
            self.wait_for_loading = True

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

            self.ui_manager.set_play_button_icon("play")
            self.ui_manager.set_stopped()
            logger.debug("Player thread stopped")

    @Slot()
    def on_stop_pressed(self) -> None:
        self.stop()

    @Slot()
    def on_playing_finished(self) -> None:
        self.play_next()

    @Slot()
    def on_skip_pressed(self) -> None:
        self.play_next()

    def play_next(self) -> None:
        self.stop()

        if len(self.playlist) == 0:
            if self.module_loader_thread and self.module_loader_thread.isRunning():
                self.module_loader_thread.quit()
                self.module_loader_thread.wait()

        if len(self.playlist) > 0:
            self.play_next_in_playlist()
        else:
            # self.ui_manager.update_loading_ui()
            self.load_random_module()

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
        if self.song:
            url: str = self.web_helper.lookup_msm_mod_url(self.song)

            if url:
                webbrowser.open(url)

    @Slot()
    def on_lookup_modarchive(self) -> None:
        if self.song:
            url: str = self.web_helper.lookup_modarchive_mod_url(self.song)

            if url:
                webbrowser.open(url)

    @Slot()
    def on_seek(self, position: int) -> None:
        # if self.player_thread:
        #     self.player_thread.seek(position)
        pass

    def check_playing_mode(self) -> None:
        # self.current_playing_mode = self.settings_manager.get_current_playing_mode()
        self.current_playing_mode = self.ui_manager.get_current_playing_mode()

        if (
            self.current_playing_mode == CurrentPlayingMode.ARTIST
            and self.ui_manager.get_artist_input() == ""
        ):
            self.current_playing_mode = CurrentPlayingMode.RANDOM
            self.ui_manager.set_current_playing_mode(self.current_playing_mode)
            logger.error("No artist input, switching to random")
        return

    def on_playing_mode_changed(self, new_playing_mode) -> None:
        if new_playing_mode != self.current_playing_mode:
            # Clear the playlist and load a new module
            logger.debug("Playing mode changed, clearing playlist and loading new module")
            self.playlist.clear()
            self.load_random_module()

        self.current_playing_mode = new_playing_mode
        self.check_playing_mode()

    def add_to_playlist(self, song: Song) -> None:
        self.playlist.append(song)
        logger.debug(
            f"Added {song.filename} to playlist, current playlist length: {len(self.playlist)}"
        )

    def play_next_in_playlist(self) -> None:
        if self.playlist:
            self.play_module(self.playlist.pop(0))
        else:
            logger.debug("No more modules in playlist")

    def play_module(self, song: Song) -> None:
        logger.debug("Playing module")

        self.audio_backend = AudioBackendPyAudio(
            44100, self.settings_manager.get_audio_buffer()
        )

        filename = song.filename
        if filename is None:
            raise ValueError("Module entry does not contain a filename")

        # Create player backend from backend name in song info
        self.player_backend = self.player_backends[song.backend_name](song.backend_name)

        if self.player_backend is not None and self.audio_backend is not None:
            self.player_backend.song = song
            self.player_backend.check_module()
            # self.song.filename = filename.split("/")[-1]
            self.current_song = song

            module_title: str = song.title or "Unknown"
            module_message: str = song.message or ""
            self.ui_manager.update_title_label(module_title)

            filename = filename.split("/")[-1]

            self.ui_manager.update_filename_label(f'<a href="#">{filename}</a>')
            self.ui_manager.update_player_backend_label(self.player_backend.name)
            self.setWindowTitle(f"{self.name} - {module_title}")
            self.ui_manager.set_message_label(module_message)

            self.player_thread = PlayerThread(self.player_backend, self.audio_backend)
            self.player_thread.song_finished.connect(self.on_playing_finished)
            self.player_thread.position_changed.connect(self.update_progress)
            self.player_thread.start()

            self.ui_manager.set_play_button_icon("pause")
            self.ui_manager.set_playing()
            self.ui_manager.show_tray_notification("Now Playing", module_title)
            logger.debug("Module loaded and playing")

            self.current_module_is_favorite = self.check_favorite(
                self.settings_manager.get_member_id()
            )

            # Buffer the next module
            self.load_random_module()
        else:
            raise ValueError("No player backend loaded")

    def load_random_module(self) -> None:
        logger.debug("Loading random module")

        self.check_playing_mode()
        member_id = self.settings_manager.get_member_id()
        artist_input = self.ui_manager.get_artist_input()

        self.module_loader_thread = ModuleLoaderThread(
            self.download_manager, self.current_playing_mode, member_id, artist_input
        )
        self.module_loader_thread.module_loaded.connect(self.on_module_loaded)
        self.module_loader_thread.start()

    @Slot()
    def on_module_loaded(self, song: Song) -> None:
        if song:
            result = self.update_song_info(song)

            if result:
                self.add_to_playlist(song)
        else:
            logger.error("Failed to download module")

        # Check if we have been waiting for the module to load (when pressing play after starting the application)
        if self.wait_for_loading:
            self.wait_for_loading = False
            self.play_next_in_playlist()

    def check_favorite(self, member_id: str) -> bool:
        # Check if the module is the current members favorite
        member_favorites_id_list = self.web_helper.get_member_module_id_list(member_id)

        if self.current_song:
            is_favorite = self.current_song.modarchive_id in member_favorites_id_list
            self.ui_manager.set_favorite_button_state(is_favorite)

            if is_favorite:
                logger.debug("Current module is a member favorite")

        return is_favorite

    def update_song_info(self, song: Song) -> Optional[Song]:
        # Try to load the module by going through the available player backends
        for backend_name, backend_class in self.player_backends.items():
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_class(backend_name)
            if player_backend is not None:
                player_backend.song = song
                if player_backend.check_module():
                    logger.debug(f"Module loaded with player backend: {backend_name}")
                    song.backend_name = backend_name
                    player_backend.song = song
                    player_backend.retrieve_song_info()
                    return player_backend.song
            else:
                raise ValueError("No player backend could load the module")
        return None

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

    @Slot()
    def update_progress(self, position: int, length: int) -> None:
        self.ui_manager.update_progress(position, length)

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

        # Save current playing mode
        self.settings_manager.set_current_playing_mode(self.current_playing_mode)
        self.settings_manager.close()
        self.ui_manager.close_ui()

        super().closeEvent(event)
