from PySide6.QtCore import Signal
from typing import Optional

from loguru import logger

from player_backends.Song import Song
from loaders.module_loader_thread import ModuleLoaderThread


class LocalLoaderThread(ModuleLoaderThread):
    module_loaded = Signal(Song)

    def __init__(self) -> None:
        super().__init__()

        self.files: list[str] = []

    def load_module(self) -> Optional[Song]:
        if self.files:
            song: Song = Song()
            song.filename = self.files.pop(0)
            song.is_ready = True
            logger.info(f"Loading local module: {song.filename}")
            return song
        return None
