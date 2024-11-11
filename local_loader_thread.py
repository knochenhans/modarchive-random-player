from PySide6.QtCore import Signal
from typing import Optional

from loguru import logger

from player_backends.player_backend import Song
from module_loader_thread import ModuleLoaderThread


class LocalLoaderThread(ModuleLoaderThread):
    module_loaded = Signal(Song)

    def __init__(self) -> None:
        super().__init__()

        self.files: list[str] = []

    def load_module(self) -> Optional[Song]:
        if self.files:
            song: Song = Song()
            song.filename = self.files.pop(0)
            logger.info(f"Loading module: {song.filename}")
            return song
        return None
