import shutil
import tempfile
import webbrowser
from typing import Optional, Dict

from loguru import logger
from PySide6.QtCore import QSettings, Qt, Slot, Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QMainWindow, QMenu, QSystemTrayIcon, QFileDialog

from audio_backends.pyaudio.audio_backend_pyuadio import AudioBackendPyAudio
from current_playing_mode import CurrentPlayingMode
from history_dialog import HistoryDialog
from loaders.module_loader import ModuleLoader
from meta_data_dialog import MetaDataDialog
from playlists_dialog import PlaylistsDialog
from loaders.module_loader_thread import ModuleLoaderThread
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.player_backend import PlayerBackend, Song
from player_thread import PlayerThread
from playlist import Playlist
from playlist_manager import PlaylistManager
from settings_dialog import SettingsDialog
from settings_manager import SettingsManager
from ui_manager import UIManager
from web_helper import WebHelper
import os


class MainWindow(QMainWindow):
    song_added_to_history = Signal(Song)

    def __init__(self) -> None:
        super().__init__()
        self.name: str = "Mod Archive Random Player"
        self.setWindowTitle(self.name)
        self.settings = QSettings("Andre Jonas", "ModArchiveRandomPlayer")

        self.player_backends: Dict[str, type[PlayerBackend]] = {
            "LibUADE": PlayerBackendLibUADE,
            "LibOpenMPT": PlayerBackendLibOpenMPT,
        }
        self.player_backend: Optional[PlayerBackend] = None
        self.audio_backend: Optional[AudioBackendPyAudio] = None
        self.player_thread: Optional[PlayerThread] = None
        self.module_loader_threads: list[ModuleLoaderThread] = []

        self.current_song: Optional[Song] = None
        self.song_waiting_for_playback: Optional[Song] = None
        self.current_module_is_favorite: bool = False
        self.current_playing_mode: CurrentPlayingMode = CurrentPlayingMode.RANDOM
        self.current_playing_mode_changed = False
        self.playback_pending = False

        # self.playlist: Playlist = Playlist()
        self.playlist_manager = PlaylistManager()
        self.history: list[Song] = []
        self.queue: list[Song] = []

        self.local_files: list[str] = []

        self.settings_manager = SettingsManager(self.settings)

        self.web_helper = WebHelper()
        self.ui_manager = UIManager(self)
        self.icon = self.ui_manager.pixmap_icons["application_icon"]
        self.setWindowIcon(self.icon)

        self.ui_manager.load_settings()

        self.temp_dir = tempfile.mkdtemp()

        self.module_loader = ModuleLoader(
            self.current_playing_mode,
            self.local_files,
            WebHelper(),
            self.temp_dir,
            self.player_backends,
        )

        # test_playlist = self.playlist_manager.add_playlist("Default")

        song1 = Song()
        song1.modarchive_id = 79666

        test_playlist.add_song(song1)

        song2 = Song()
        song2.modarchive_id = 66079

        test_playlist.add_song(song2)

        self.load_module(song1)
        self.load_module(song2)

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
        if self.current_playing_mode_changed:
            self.update_playing_mode()
            self.current_playing_mode_changed = False

        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.pause()
            self.ui_manager.set_play_button(self.player_thread.pause_flag)
        else:
            self.play_module(self.current_song)

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

            self.ui_manager.set_play_button_icon("play")
            self.ui_manager.set_stopped()
            logger.debug("Player thread stopped")

    @Slot()
    def on_stop_pressed(self) -> None:
        self.stop()
        self.audio_backend = None

    @Slot()
    def on_playing_finished(self) -> None:
        self.play_next()

    @Slot()
    def on_skip_pressed(self) -> None:
        self.play_next()

    def play_next(self) -> None:
        self.stop()

        song: Song | None = None

        if len(self.queue) > 0:
            song = self.queue.pop(0)
        else:
            if self.current_playing_mode != CurrentPlayingMode.LOCAL:
                song = self.get_random_module()

        if song:
            self.play_module(song)

        # if self.current_playing_mode_changed:
        #     self.update_playing_mode()
        #     self.current_playing_mode_changed = False

        # if len(self.playlist) == 0:
        #     if self.module_loader_thread and self.module_loader_thread.isRunning():
        #         self.module_loader_thread.quit()
        #         self.module_loader_thread.wait()

        # if len(self.playlist) > 0:
        #     self.play_next_in_playlist()
        # else:
        #     # self.ui_manager.update_loading_ui()
        #     self.load_module()

    def get_random_module(self) -> Optional[Song]:
        id: int | None = None
        song: Song | None = None

        if self.current_playing_mode == CurrentPlayingMode.LOCAL:
            pass
        else:
            match self.current_playing_mode:
                case CurrentPlayingMode.RANDOM:
                    logger.info("Getting random module")
                    id = self.web_helper.get_random_module_id()
                case CurrentPlayingMode.FAVORITE:
                    logger.info("Getting random favorite module")
                    id = self.web_helper.get_random_favorite_module_id(
                        self.settings_manager.get_member_id()
                    )
                case CurrentPlayingMode.ARTIST:
                    logger.info("Getting random artist module")
                    id = self.web_helper.get_random_artist_module_id(
                        self.ui_manager.get_artist_input()
                    )

            if id:
                song = Song()
                song.modarchive_id = id
        return song

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
        if self.current_song:
            url: str = self.web_helper.lookup_msm_mod_url(self.current_song)

            if url:
                webbrowser.open(url)

    @Slot()
    def on_lookup_modarchive(self) -> None:
        if self.current_song:
            url: str = self.web_helper.lookup_modarchive_mod_url(self.current_song)

            if url:
                webbrowser.open(url)

    def seek(self, position: int) -> None:
        if self.player_thread:
            self.player_thread.seek(position)

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

    def queue_next_module(self) -> None:
        # Check if the playlist has any modules left
        current_playlist = self.playlist_manager.current_playlist
        if current_playlist:
            next_song = current_playlist.next_song()

            if next_song:
                self.queue.append(next_song)
                return

        self.queue_random_module()

    def queue_random_module(self) -> None:
        if self.current_playing_mode != CurrentPlayingMode.LOCAL:
            random_module = self.get_random_module()

            if random_module:
                self.queue.append(random_module)

                if not self.current_song:
                    self.current_song = random_module

    def update_playing_mode(self) -> None:
        # Clear the playlist and load a new module
        logger.debug("Playing mode changed, clearing playlist and loading new module")

        self.queue.clear()

        self.queue_random_module()

        # if self.current_playing_mode == CurrentPlayingMode.LOCAL:
        #     if len(self.local_files) == 0:
        #         self.on_open_local_folder_dialog()
        #     self.queue.clear()
        # else:
        #     self.queue.clear()
        #     # self.load_module()

        self.check_playing_mode()

    def on_playing_mode_changed(self, new_playing_mode) -> None:
        # self.current_playing_mode_changed = True
        if new_playing_mode != self.current_playing_mode:
            self.current_playing_mode = new_playing_mode
            self.update_playing_mode()

    # def add_to_playlist(self, song: Song) -> None:
    #     self.playlist.add_song(song)
    #     logger.debug(
    #         f"Added {song.filename} to playlist, current playlist length: {self.playlist.get_length()}"
    #     )

    def play_next_in_playlist(self) -> None:
        current_playlist = self.playlist_manager.current_playlist
        if current_playlist:
            song = current_playlist.next_song()

            if song:
                self.play_module(song)
                self.history.append(song)
                self.song_added_to_history.emit(song)

            # Buffer the next module
            # self.load_module()
        else:
            logger.debug("No more modules in playlist")

    def open_history_dialog(self) -> None:
        history_dialog = HistoryDialog(self.history, self)
        self.song_added_to_history.connect(history_dialog.on_new_entry)
        history_dialog.entry_double_clicked.connect(self.play_module)
        history_dialog.show()

    def open_playlists_dialog(self) -> None:
        playlists_dialog = PlaylistsDialog(self.playlist_manager, self)
        # playlists_dialog.entry_double_clicked.connect(self.play_module)
        playlists_dialog.show()

    def open_meta_data_dialog(self) -> None:
        if self.current_song:
            meta_data_dialog = MetaDataDialog(self.current_song, self)
            meta_data_dialog.show()

    def play_module(self, song: Optional[Song]) -> None:
        if not song:
            song = self.get_random_module()

        if song:
            if song.is_ready:
                self.current_song = song

                self.stop()

                logger.debug("Playing module")

                if self.audio_backend is None:
                    self.audio_backend = AudioBackendPyAudio(
                        44100, self.settings_manager.get_audio_buffer()
                    )

                filename = song.filename
                if filename is None:
                    raise ValueError("Module entry does not contain a filename")

                # Create player backend from backend name in song info
                self.player_backend = self.player_backends[song.backend_name](
                    song.backend_name
                )

                if self.player_backend is not None and self.audio_backend is not None:
                    # self.stop()
                    self.player_backend.song = song
                    self.player_backend.check_module()
                    # self.song.filename = filename.split("/")[-1]
                    self.current_song = song

                    module_title: str = song.title or "Unknown"
                    module_message: str = song.message or ""
                    self.ui_manager.update_title_label(module_title)

                    filename = filename.split("/")[-1]

                    self.ui_manager.update_filename_label(f'<a href="#">{filename}</a>')
                    self.ui_manager.update_player_backend_label(
                        self.player_backend.name
                    )
                    self.setWindowTitle(f"{self.name} - {module_title}")
                    self.ui_manager.set_message_label(module_message)

                    self.player_thread = PlayerThread(
                        self.player_backend, self.audio_backend
                    )
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

                    # Preload the next module
                    self.queue_next_module()
                else:
                    raise ValueError("No player backend loaded")
            else:
                logger.debug("Module not ready, waiting for module to load")
                self.song_waiting_for_playback = song
                self.load_module(song)

    def load_module(self, song: Song) -> None:
        self.module_loader.load_module(song)
        self.module_loader.module_loaded.connect(self.on_module_loaded)

    @Slot()
    def on_module_loaded(self, song: Song) -> None:
        if song:
            # Check if we have been waiting for the module to load (when pressing play after starting the application)
            if self.song_waiting_for_playback == song:
                self.play_module(song)
                self.song_waiting_for_playback = None

    def check_favorite(self, member_id: int) -> bool:
        # Check if the module is the current members favorite
        member_favorites_id_list = self.web_helper.get_member_module_id_list(member_id)

        is_favorite = False

        if self.current_song and self.current_song.modarchive_id:
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
    def on_open_local_folder_dialog(self) -> None:
        current_folder = self.settings_manager.get_local_folder()
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder", current_folder
        )
        if folder_path:
            logger.debug(f"Selected folder: {folder_path}")

            self.set_local_folder(folder_path)
            self.settings_manager.set_local_folder(folder_path)

    def set_local_folder(self, local_folder: str) -> None:
        self.local_files = self.get_files_recursive(local_folder)

    def get_files_recursive(self, folder_path: str) -> list[str]:
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            dirs.sort()
            files.sort()
            for dir in dirs:
                file_list.extend(self.get_files_recursive(os.path.join(root, dir)))
            for file in files:
                file_list.append(os.path.join(root, file))
        return file_list

    @Slot()
    def closeEvent(self, event) -> None:
        self.stop()

        # Save current playing mode
        self.settings_manager.set_current_playing_mode(self.current_playing_mode)
        self.settings_manager.close()
        self.ui_manager.close_ui()

        shutil.rmtree(self.temp_dir)

        super().closeEvent(event)
