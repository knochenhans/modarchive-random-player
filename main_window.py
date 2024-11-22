import shutil
import tempfile
import webbrowser
from typing import Optional, Dict

from loguru import logger
from PySide6.QtCore import QSettings, Qt, Slot
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QMainWindow, QMenu, QSystemTrayIcon, QFileDialog

from audio_backends.pyaudio.audio_backend_pyuadio import AudioBackendPyAudio
from icons import Icons
from loaders.modarchive_random_module_fetcher import ModArchiveRandomModuleFetcherThread
from playing_modes import LocalSource, PlayingMode, PlayingSource, ModArchiveSource
from history_dialog import HistoryDialog
from loaders.module_loader import ModuleLoader
from meta_data_dialog import MetaDataDialog
from playlist.playlist import Playlist
from playlist.playlists_dialog import PlaylistsDialog
from loaders.module_loader_thread import ModuleLoaderThread
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.player_backend import PlayerBackend, Song
from player_thread import PlayerThread
from playlist.playlist_manager import PlaylistManager
from queue_manager import QueueManager
from settings_dialog import SettingsDialog
from settings_manager import SettingsManager
from ui_manager import UIManager
from web_helper import WebHelper
import os
from PySide6.QtCore import QTimer


class MainWindow(QMainWindow):
    # song_info_updated = Signal(Song)

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
        self.random_module_fetcher_threads: list[
            ModArchiveRandomModuleFetcherThread
        ] = []

        self.current_song: Optional[Song] = None
        self.song_waiting_for_playback: Optional[Song] = None
        self.current_module_is_favorite: bool = False

        self.playing_mode: PlayingMode = PlayingMode.RANDOM
        self.playing_source: PlayingSource = PlayingSource.MODARCHIVE
        self.modarchive_source: ModArchiveSource = ModArchiveSource.ALL
        self.local_source: LocalSource = LocalSource.PLAYLIST

        self.local_files: list[str] = []

        self.settings_manager = SettingsManager(self.settings)

        self.playlist_manager = PlaylistManager(self.settings_manager)
        self.history_playlist = self.playlist_manager.new_playlist("History")

        self.queue_manager = QueueManager(self.history_playlist)

        self.web_helper = WebHelper()
        self.icons = Icons(self.settings, self.style())
        self.icon = self.icons.pixmap_icons["application_icon"]
        self.ui_manager = UIManager(self)
        self.setWindowIcon(self.icon)

        self.ui_manager.load_settings()

        self.temp_dir = tempfile.mkdtemp()

        self.module_loader = ModuleLoader(
            self.playing_source,
            self.local_files,
            WebHelper(),
            self.temp_dir,
            self.player_backends,
        )

        self.queue_check_timer = QTimer(self)
        self.queue_check_timer.timeout.connect(self.check_queue)

        self.history_dialog = None
        self.playlist_dialog = None
        self.settings_dialog = None
        self.meta_data_dialog = None

        self.playlist_manager.load_playlists()
        self.playlist_manager.sort()

        self.set_playing_mode(self.settings_manager.get_playing_mode())
        self.set_playing_source(self.settings_manager.get_playing_source())
        self.set_modarchive_source(self.settings_manager.get_modarchive_source())
        self.set_local_source(self.settings_manager.get_local_source())

    def check_queue(self) -> None:
        if self.queue_manager.is_empty() and self.playing_mode == PlayingMode.RANDOM:
            logger.debug("Random mode is active, queue is empty, preparing next module")
            self.populate_queue()

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
        if self.settings_dialog:
            self.settings_dialog.close()
            self.settings_dialog = None
        else:
            self.settings_dialog = SettingsDialog(self.settings, self)
            self.settings_dialog.setWindowTitle("Settings")
            self.settings_dialog.exec()

            self.ui_manager.update_source_input()

    def populate_queue(self) -> None:
        if self.playing_source == PlayingSource.MODARCHIVE:
            if self.playing_mode == PlayingMode.RANDOM:
                song = Song()
                self.get_random_module(song)
                self.queue_manager.add_song(song)
        elif self.playing_source == PlayingSource.LOCAL:
            if self.local_source == LocalSource.PLAYLIST:
                current_playlist = self.playlist_manager.current_playlist

                if current_playlist:
                    songs = current_playlist.songs

                    if len(songs) > 0:
                        self.queue_manager.add_songs(songs)

    @Slot()
    def on_play_pause_pressed(self) -> None:
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.pause()
            self.ui_manager.set_play_button(self.player_thread.pause_flag)
        else:
            self.play_queue()

    def play_queue(self) -> None:
        song = self.queue_manager.pop_next_song()

        if song:
            self.play_module(song)
        else:
            if PlayingMode.RANDOM:
                self.populate_queue()
                song = self.queue_manager.pop_next_song()

                if song:
                    self.play_module(song)

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

    @Slot()
    def on_previous_pressed(self) -> None:
        self.play_previous()

    def play_next(self) -> None:
        # self.stop()

        self.play_queue()
        # else:
        #     if self.current_playing_mode == CurrentPlayingMode.PLAYLIST:
        #         self.play_next_in_playlist()
        #     elif self.current_playing_mode != CurrentPlayingMode.LOCAL:
        #         song = self.get_random_module()

    def play_previous(self) -> None:
        self.stop()

    def get_random_module(self, song) -> None:
        random_module_fetcher_thread = ModArchiveRandomModuleFetcherThread(
            song,
            self.playing_mode,
            self.playing_source,
            self.modarchive_source,
            self.web_helper,
            self.ui_manager.get_artist_input(),
            self.settings_manager.get_member_id(),
        )

        random_module_fetcher_thread.module_fetched.connect(
            self.on_random_module_fetched
        )
        self.random_module_fetcher_threads.append(random_module_fetcher_thread)
        random_module_fetcher_thread.start()

    @Slot(Song)
    def on_random_module_fetched(self, song: Song) -> None:
        logger.debug(f"Random module fetched, ModArchive ID: {song.modarchive_id}")
        if song:
            self.load_module(song)

        self.random_module_fetcher_threads = [
            thread
            for thread in self.random_module_fetcher_threads
            if thread.isRunning()
        ]

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
        # self.current_playing_mode = self.ui_manager.get_playing_mode()
        # self.current_playing_source = self.ui_manager.get_playing_source()
        # self.current_modarchive_source = self.ui_manager.get_modarchive_source()

        if (
            self.modarchive_source == ModArchiveSource.ARTIST
            and self.ui_manager.get_artist_input() == ""
        ):
            logger.error("No artist input, changing ModArchive source to ALL")
            self.modarchive_source = ModArchiveSource.ALL
            self.ui_manager.set_modarchive_source(ModArchiveSource.ALL)
        return

    def update_playing_mode(self) -> None:
        # Clear the playlist and load a new module
        logger.debug(
            "Playing mode or source changed, clearing queue and terminating loader and fetcher threads"
        )

        self.queue_manager.clear()

        for thread in self.random_module_fetcher_threads:
            thread.terminate()
            thread.wait()
        self.random_module_fetcher_threads.clear()

        self.check_playing_mode()

        if self.playing_mode == PlayingMode.RANDOM:
            self.populate_queue()
            self.queue_check_timer.start(10000)

    def set_playing_mode(self, new_playing_mode) -> None:
        if new_playing_mode != self.playing_mode:
            self.playing_mode = new_playing_mode
            self.update_playing_mode()
        self.ui_manager.set_playing_mode(new_playing_mode)

    def set_playing_source(self, new_playing_source) -> None:
        self.playing_source = new_playing_source
        if new_playing_source == PlayingSource.LOCAL:
            self.module_loader.local_files = self.local_files
        self.ui_manager.set_playing_source(new_playing_source)

    def set_modarchive_source(self, new_modarchive_source) -> None:
        self.modarchive_source = new_modarchive_source
        if new_modarchive_source == ModArchiveSource.ARTIST:
            self.get_random_module(self.current_song)
        self.ui_manager.set_modarchive_source(new_modarchive_source)

    def set_local_source(self, new_local_source) -> None:
        self.local_source = new_local_source
        if new_local_source == LocalSource.PLAYLIST:
            self.module_loader.local_files = self.local_files
        self.ui_manager.set_local_source(new_local_source)

    def open_history_dialog(self) -> None:
        if self.history_dialog:
            self.history_dialog.close()
            self.history_dialog = None
        else:
            self.history_dialog = HistoryDialog(
                self.settings_manager,
                self.playlist_manager,
                self.history_playlist,
                self,
            )
            self.history_playlist.song_added.connect(self.history_dialog.add_song)
            # self.song_info_updated.connect(history_dialog.update_song_info)
            self.history_dialog.song_on_tab_double_clicked.connect(self.play_module)
            self.history_dialog.show()

    def open_playlists_dialog(self) -> None:
        if self.playlist_dialog:
            self.playlist_dialog.close()
            self.playlist_dialog = None
        else:
            self.playlists_dialog = PlaylistsDialog(
                self.settings_manager, self.playlist_manager, self.player_backends, self
            )
            self.playlists_dialog.song_on_tab_double_clicked.connect(
                self.play_playlist_modules
            )
            self.playlists_dialog.show()

    def open_meta_data_dialog(self) -> None:
        if self.meta_data_dialog:
            self.meta_data_dialog.close()
            self.meta_data_dialog = None
        else:
            if self.current_song:
                self.meta_data_dialog = MetaDataDialog(self.current_song, self)
                self.meta_data_dialog.show()

    def play_module(self, song: Optional[Song]) -> None:
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

                    if self.playing_source == PlayingSource.MODARCHIVE:
                        self.ui_manager.show_favorite_button(True)
                        self.current_module_is_favorite = self.check_favorite(
                            self.settings_manager.get_member_id()
                        )
                    elif self.playing_source == PlayingSource.LOCAL:
                        self.ui_manager.show_favorite_button(False)

                        if self.local_source == LocalSource.PLAYLIST:
                            if self.playlist_manager.current_playlist:
                                self.playlist_manager.current_playlist.set_current_song(
                                    self.current_song
                                )
                else:
                    raise ValueError("No player backend loaded")
            else:
                logger.debug("Module not ready, waiting for module to load")
                self.song_waiting_for_playback = song
        else:
            logger.error("No module to play")

    def play_playlist_modules(self, songs: list[Song], playlist: Playlist) -> None:
        self.set_playing_mode(PlayingMode.LINEAR)
        self.set_local_source(LocalSource.PLAYLIST)
        self.set_playing_source(PlayingSource.LOCAL)
        if songs:
            self.queue_manager.set_queue(songs)
            self.playlist_manager.set_current_playlist(playlist)
            self.play_queue()

    def load_module(self, song: Song) -> None:
        self.module_loader.load_module(song)
        self.module_loader.song_loaded.connect(self.on_module_loaded)

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

        self.playlist_manager.save_playlists()
        self.settings_manager.set_playing_mode(self.playing_mode)
        self.settings_manager.close()
        self.ui_manager.close_ui()

        shutil.rmtree(self.temp_dir)

        super().closeEvent(event)
