import tempfile
from typing import Optional, Dict

from loguru import logger
from PySide6.QtCore import Slot, QObject, Signal, QTimer

from audio_backends.pyaudio.audio_backend_pyuadio import AudioBackendPyAudio
from loaders.modarchive_random_module_fetcher import ModArchiveRandomModuleFetcherThread
from playing_settings import PlayingSettings
from playing_modes import LocalSource, PlayingMode, PlayingSource, ModArchiveSource
from loaders.module_loader import ModuleLoader
from playlist.playlist import Playlist
from player_backends.player_backend import PlayerBackend, Song
from player_thread import PlayerThread
from playlist.playlist_manager import PlaylistManager
from queue_manager import QueueManager
from settings_manager import SettingsManager
from ui_manager import UIManager
from web_helper import WebHelper


class PlayingEngine(QObject):
    set_window_title = Signal(str)

    def __init__(
        self,
        ui_manager: UIManager,
        settings_manager: SettingsManager,
        player_backends: Dict[str, type[PlayerBackend]],
    ) -> None:
        super().__init__()

        self.ui_manager = ui_manager
        self.settings_manager = settings_manager
        self.player_backends = player_backends

        self.player_backend: Optional[PlayerBackend] = None
        self.audio_backend: Optional[AudioBackendPyAudio] = None
        self.player_thread: Optional[PlayerThread] = None
        self.random_module_fetcher_threads: list[
            ModArchiveRandomModuleFetcherThread
        ] = []

        self.song_waiting_for_playback: Optional[Song] = None
        self.current_module_is_favorite: bool = False

        self.local_file: str = ""

        self.playing_settings = PlayingSettings(self.settings_manager)
        self.playlist_manager = PlaylistManager(self.settings_manager)
        self.history_playlist = self.playlist_manager.new_playlist("History")

        self.playlist_manager.load_playlists()

        self.queue_manager = QueueManager(self.history_playlist)

        self.web_helper = WebHelper()

        self.temp_dir = tempfile.mkdtemp()

        self.module_loader = ModuleLoader(
            self.playing_settings,
            self.local_file,
            WebHelper(),
            self.temp_dir,
            self.player_backends,
        )

        self.queue_check_timer = QTimer(self)
        self.queue_check_timer.timeout.connect(self.check_queue)

    def get_current_song(self) -> Optional[Song]:
        if self.player_backend:
            return self.player_backend.song

    def play_module(self, song: Optional[Song]) -> None:
        if song:
            if song.is_ready:
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
                    self.player_backend.song = song
                    self.player_backend.set_subsong_changed_callback(
                        self.ui_manager.update_subsong_info
                    )
                    self.player_backend.set_song_name_changed_callback(
                        self.ui_manager.update_title_label
                    )

                    module_title: str = song.title or "Unknown"
                    module_message: str = song.message or ""
                    self.ui_manager.update_title_label(module_title)

                    filename = filename.split("/")[-1]

                    self.ui_manager.update_filename_label(f'<a href="#">{filename}</a>')
                    self.ui_manager.update_player_backend_label(
                        self.player_backend.name
                    )
                    self.set_window_title.emit(module_title)
                    self.ui_manager.set_message_label(module_message)

                    self.player_thread = PlayerThread(
                        self.player_backend, self.audio_backend
                    )
                    self.player_thread.song_finished.connect(self.on_playing_finished)
                    self.player_thread.position_changed.connect(
                        self.ui_manager.update_progress
                    )
                    self.player_thread.start()

                    self.ui_manager.set_play_button_icon("pause")
                    self.ui_manager.set_playing()
                    self.ui_manager.show_tray_notification("Now Playing", module_title)
                    logger.debug("Module loaded and playing")
                    self.ui_manager.update_subsong_info(
                        self.player_backend.get_current_subsong() + 1,
                        self.player_backend.song.subsongs,
                    )

                    if self.playing_settings.playing_source == PlayingSource.MODARCHIVE:
                        self.ui_manager.show_favorite_button(True)
                        self.current_module_is_favorite = self.check_favorite(
                            self.settings_manager.get_member_id()
                        )
                    elif self.playing_settings.playing_source == PlayingSource.LOCAL:
                        self.ui_manager.show_favorite_button(False)

                        if self.playing_settings.local_source == LocalSource.PLAYLIST:
                            song = self.get_current_song()
                            if self.playlist_manager.current_playlist and song:
                                self.playlist_manager.current_playlist.set_current_song(
                                    song
                                )
                else:
                    raise ValueError("No player backend loaded")
            else:
                logger.debug("Module not ready, waiting for module to load")
                self.song_waiting_for_playback = song
        else:
            logger.error("No module to play")

    def play_pause(self) -> None:
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.pause()
            self.ui_manager.set_play_button(self.player_thread.pause_flag)
        else:
            self.play_queue()

    def stop(self, close_audio_stream: bool = False) -> None:
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

        if close_audio_stream and self.audio_backend:
            logger.debug("Closing audio stream")
            self.audio_backend = None

    def check_favorite(self, member_id: int) -> bool:
        # Check if the module is the current members favorite
        member_favorites_id_list = self.web_helper.get_member_module_id_list(member_id)

        is_favorite = False

        song = self.get_current_song()

        if song:
            if song.modarchive_id:
                is_favorite = song.modarchive_id in member_favorites_id_list
                self.ui_manager.set_favorite_button_state(is_favorite)

                if is_favorite:
                    logger.debug("Current module is a member favorite")

        return is_favorite

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
    def on_playing_finished(self) -> None:
        self.play_next()

    def play_next(self) -> None:
        self.play_queue()

    def play_previous(self) -> None:
        if self.playing_settings.playing_mode == PlayingMode.RANDOM:
            self.queue_manager.clear()
            previous_song = self.history_playlist.get_previous_song()

            if previous_song:
                self.queue_manager.add_song(previous_song)
                self.play_queue()
        elif self.playing_settings.playing_mode == PlayingMode.LINEAR:
            current_playlist = self.playlist_manager.current_playlist

            if current_playlist:
                songs = current_playlist.get_songs_from(
                    current_playlist.current_song_index - 1
                )
                self.queue_manager.set_queue(songs)
                self.play_queue()

    def play_playlist_modules(self, songs: list[Song], playlist: Playlist) -> None:
        self.set_playing_mode(PlayingMode.LINEAR)
        self.set_local_source(LocalSource.PLAYLIST)
        self.set_playing_source(PlayingSource.LOCAL)
        if songs:
            self.queue_manager.set_queue(songs)
            self.playlist_manager.set_current_playlist(playlist)
            self.play_queue()

    def populate_queue(self) -> None:
        if self.playing_settings.playing_source == PlayingSource.MODARCHIVE:
            if self.playing_settings.playing_mode == PlayingMode.RANDOM:
                song = Song()
                self.get_random_module(song)
                self.queue_manager.add_song(song)
        elif self.playing_settings.playing_source == PlayingSource.LOCAL:
            if self.playing_settings.local_source == LocalSource.PLAYLIST:
                current_playlist = self.playlist_manager.current_playlist

                if current_playlist:
                    songs = current_playlist.songs

                    if len(songs) > 0:
                        self.queue_manager.add_songs(songs)

    def get_random_module(self, song) -> None:
        random_module_fetcher_thread = ModArchiveRandomModuleFetcherThread(
            song,
            self.playing_settings.playing_mode,
            self.playing_settings.playing_source,
            self.playing_settings.modarchive_source,
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

    def set_playing_mode(self, new_playing_mode) -> None:
        if new_playing_mode != self.playing_settings.playing_mode:
            self.playing_settings.playing_mode = new_playing_mode
            self.update_playing_mode()
        self.ui_manager.set_playing_mode(new_playing_mode)

    def set_playing_source(self, new_playing_source) -> None:
        if new_playing_source != self.playing_settings.playing_source:
            self.playing_settings.playing_source = new_playing_source
            self.update_playing_mode()
        if new_playing_source == PlayingSource.LOCAL:
            self.module_loader.local_file = self.local_file
        self.ui_manager.set_playing_source(new_playing_source)

    def set_modarchive_source(self, new_modarchive_source) -> None:
        self.playing_settings.modarchive_source = new_modarchive_source
        if new_modarchive_source == ModArchiveSource.ARTIST:
            self.populate_queue()
        self.ui_manager.set_modarchive_source(new_modarchive_source)

    def set_local_source(self, new_local_source) -> None:
        self.playing_settings.local_source = new_local_source
        if new_local_source == LocalSource.PLAYLIST:
            self.module_loader.local_file = self.local_file
        self.ui_manager.set_local_source(new_local_source)

    def update_playing_mode(self) -> None:
        logger.debug(
            "Playing mode or source changed, clearing queue and terminating loader and fetcher threads"
        )

        self.queue_manager.clear()

        for thread in self.random_module_fetcher_threads:
            thread.terminate()
            thread.wait()
        self.random_module_fetcher_threads.clear()

        self.check_playing_mode()

        if self.playing_settings.playing_mode == PlayingMode.RANDOM:
            self.populate_queue()
            self.queue_check_timer.start(10000)

    def check_playing_mode(self) -> None:
        if (
            self.playing_settings.modarchive_source == ModArchiveSource.ARTIST
            and self.ui_manager.get_artist_input() == ""
        ):
            logger.error("No artist input, changing ModArchive source to ALL")
            self.playing_settings.modarchive_source = ModArchiveSource.ALL
            self.ui_manager.set_modarchive_source(ModArchiveSource.ALL)
        return

    def load_module(self, song: Song) -> None:
        self.module_loader.load_modules(song)
        self.module_loader.song_loaded.connect(self.on_module_loaded)

    @Slot()
    def on_module_loaded(self, song: Song) -> None:
        if song:
            # Check if we have been waiting for the module to load (when pressing play after starting the application)
            if self.song_waiting_for_playback == song:
                self.play_module(song)
                self.song_waiting_for_playback = None

    def check_queue(self) -> None:
        if (
            self.queue_manager.is_empty()
            and self.playing_settings.playing_mode == PlayingMode.RANDOM
        ):
            logger.debug("Random mode is active, queue is empty, preparing next module")
            self.populate_queue()

    def seek(self, position: int) -> None:
        if self.player_thread:
            self.player_thread.seek(position)

    def close(self) -> None:
        self.stop()
        self.playlist_manager.save_playlists()
        self.playing_settings.save()
