from typing import Callable, List, Optional
import weakref
from PySide6.QtCore import QRunnable, QThreadPool, QObject, QMutex, QMutexLocker, Signal

from loguru import logger

from player_backends.Song import Song
from player_backends.player_backend import PlayerBackend


class SongEmitter:
    def __init__(
        self,
        song_checked: Callable[[Song], None],
        song_info_retrieved: Callable[[Song], None],
    ):
        self.song_checked = song_checked
        self.song_info_retrieved = song_info_retrieved


class ModuleTester:
    def __init__(
        self, song: Song, backends: dict[str, type[PlayerBackend]], emitter: SongEmitter
    ):
        self.song = song
        self.backends = backends
        self.emitter = emitter

    def test_backends(self) -> None:
        for backend_name, backend_class in self.backends.items():
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_class(backend_name)
            if player_backend is not None:
                player_backend.song = self.song
                if player_backend.check_module():
                    logger.debug(f"Module loaded with player backend: {backend_name}")

                    self.song.backend_name = backend_name

                    player_backend.song = self.song
                    player_backend.retrieve_song_info()
                    self.song = player_backend.song
                    self.emitter.song_info_retrieved(self.song)
                    player_backend.cleanup()
                    player_backend = None
                    break
        self.emitter.song_checked(self.song)


class LocalFileLoaderWorker(QRunnable):
    def __init__(
        self,
        song: Song,
        backends: dict[str, type[PlayerBackend]],
        loader: "LocalFileLoader",
    ) -> None:
        super().__init__()
        self.song: Song = song
        self.player_backends: dict[str, type[PlayerBackend]] = backends
        self.loader = weakref.ref(loader)
        self.emitter = SongEmitter(
            self.song_checked_callback, self.song_info_retrieved_callback
        )

    def run(self) -> None:
        if self.song:
            tester = ModuleTester(self.song, self.player_backends, self.emitter)
            tester.test_backends()
            loader = self.loader()
            if loader:
                loader.song_finished_loading()

    def song_checked_callback(self, song: Song) -> None:
        loader = self.loader()
        if loader:
            loader.song_loaded.emit(song)

    def song_info_retrieved_callback(self, song: Song) -> None:
        loader = self.loader()
        if loader:
            loader.song_info_retrieved.emit(song)


class LocalFileLoader(QObject):
    song_loaded = Signal(Song)
    song_info_retrieved = Signal(Song)
    all_songs_loaded = Signal()

    def __init__(
        self, file_list: List[str], player_backends: dict[str, type[PlayerBackend]]
    ) -> None:
        super().__init__()
        self.file_list = file_list
        self.player_backends = player_backends
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(
            1
        )  # Limit to 1 thread for now to avoid sorting issues
        self.songs_to_load = len(file_list)
        self.songs_loaded = 0
        self.mutex = QMutex()

    def load_module(self, filename: str) -> Optional[Song]:
        if filename:
            song: Song = Song()
            song.filename = filename
            song.is_ready = True
            return song
        return None

    def load_modules(self) -> None:
        for file_name in self.file_list:
            song = self.load_module(file_name)
            if song:
                worker = LocalFileLoaderWorker(song, self.player_backends, self)
                self.thread_pool.start(worker)

    def song_finished_loading(self) -> None:
        with QMutexLocker(self.mutex):
            self.songs_loaded += 1
            if self.songs_loaded == self.songs_to_load:
                self.all_songs_loaded.emit()
