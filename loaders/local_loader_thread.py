from PySide6.QtCore import Signal
from typing import Optional

from loguru import logger

from player_backends.Song import Song
from loaders.module_loader_thread import ModuleLoaderThread


class LocalLoaderThread(ModuleLoaderThread):
    module_loaded = Signal(Song)

    def __init__(self) -> None:
        super().__init__()

        self.filename: Optional[str] = None

    def load_module(self) -> Optional[Song]:
        if self.filename:
            song: Song = Song()
            song.filename = self.filename
            song.is_ready = True
            logger.info(f"Loading local module: {song.filename}")
            return song
        return None
