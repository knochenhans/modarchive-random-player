import weakref
from PySide6.QtCore import QRunnable, QThreadPool, QObject, Signal, QMutex, QMutexLocker
from typing import List, Optional

from loguru import logger

from player_backends.Song import Song
from player_backends.player_backend import PlayerBackend


class SongEmitter(QObject):
    song_loaded = Signal(Song)
    song_info_retrieved = Signal(Song)


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
        self.emitter = SongEmitter()

    def run(self) -> None:
        if self.song:
            filename = self.song.filename
            for backend_name, backend_class in self.player_backends.items():
                logger.debug(f"Trying player backend: {backend_name}")

                player_backend = backend_class(backend_name)
                if player_backend is not None:
                    player_backend.song = self.song
                    if player_backend.check_module():
                        logger.debug(
                            f"Module loaded with player backend: {backend_name}"
                        )

                        self.song.backend_name = backend_name
                        self.emitter.song_loaded.emit(self.song)

                        player_backend.song = self.song
                        player_backend.retrieve_song_info()
                        self.song = player_backend.song
                        self.emitter.song_info_retrieved.emit(self.song)

                        player_backend.cleanup()
                        player_backend = None

                        loader = self.loader()
                        if loader:
                            loader.song_finished_loading()
                        break
            else:
                logger.warning(f'No backend could load the module "{filename}"')


class LocalFileLoader(QObject):
    song_loaded = Signal(Song)
    song_info_retrieved = Signal(Song)
    all_songs_loaded = Signal()

    def __init__(
        self, file_list: List[str], backends: dict[str, type[PlayerBackend]]
    ) -> None:
        super().__init__()
        self.file_list = file_list
        self.backends = backends
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
                worker = LocalFileLoaderWorker(song, self.backends, self)
                worker.emitter.song_loaded.connect(self.song_loaded)
                worker.emitter.song_info_retrieved.connect(self.song_info_retrieved)
                self.thread_pool.start(worker)

    def song_finished_loading(self) -> None:
        with QMutexLocker(self.mutex):
            self.songs_loaded += 1
            if self.songs_loaded == self.songs_to_load:
                self.all_songs_loaded.emit()
