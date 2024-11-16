from loguru import logger
from typing import Optional, List, Dict
from PySide6.QtCore import QObject, Slot, Signal

from current_playing_mode import CurrentPlayingMode
from loaders.local_loader_thread import LocalLoaderThread
from loaders.modarchive_loader_thread import ModArchiveLoaderThread
from player_backends.player_backend import PlayerBackend
from web_helper import WebHelper
from player_backends.Song import Song


class ModuleLoader(QObject):
    module_loaded = Signal(Song)

    def __init__(
        self,
        current_playing_mode: CurrentPlayingMode,
        local_files: List[str],
        web_helper: object,
        temp_dir: str,
        player_backends: Dict[str, type[PlayerBackend]]
    ) -> None:
        super().__init__()
        self.current_playing_mode = current_playing_mode
        self.local_files = local_files
        self.web_helper = web_helper
        self.temp_dir = temp_dir
        self.module_loader_threads: List[QObject] = []
        self.player_backends = player_backends

    def load_module(self, song: Song) -> None:
        logger.debug("Loading module")

        if self.current_playing_mode == CurrentPlayingMode.LOCAL:
            module_loader_thread = LocalLoaderThread()
            module_loader_thread.files = self.local_files
        else:
            module_loader_thread = ModArchiveLoaderThread()
            module_loader_thread.song = song
            module_loader_thread.web_helper = WebHelper()
            module_loader_thread.temp_dir = self.temp_dir

        self.module_loader_threads.append(module_loader_thread)

        module_loader_thread.module_loaded.connect(self.on_module_loaded)
        module_loader_thread.start()

    @Slot()
    def on_module_loaded(self, song: Song) -> None:
        if song:
            updated_song = self.update_song_info(song)

            if updated_song:
                song = updated_song
                self.module_loaded.emit(song)
        else:
            logger.error("Failed to load module")

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
