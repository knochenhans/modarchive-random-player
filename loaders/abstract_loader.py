from PySide6.QtCore import QObject, Signal, Slot
from player_backends.player_backend import PlayerBackend
from player_backends.Song import Song
from typing import Optional
from loguru import logger


class AbstractLoader(QObject):
    song_loaded = Signal(Song)

    def __init__(self, player_backends: dict[str, type[PlayerBackend]]) -> None:
        super().__init__()
        self.player_backends = player_backends

    def load_module(self, song: Song) -> None:
        pass

    @Slot()
    def on_module_loaded(self, song: Optional[Song]) -> None:
        if song:
            filename = song.filename
            updated_song = self.update_song_info(song)

            song = updated_song
            if not song:
                logger.warning(
                    f'No backend could load the module "{filename}"'
                )
        self.song_loaded.emit(song)

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
        return None
