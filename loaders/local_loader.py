from loguru import logger
from typing import Optional, List, Dict
from PySide6.QtCore import QObject, Slot, Signal

from loaders.abstract_loader import AbstractLoader
from loaders.local_loader_thread import LocalLoaderThread
from player_backends.player_backend import PlayerBackend
from player_backends.Song import Song


class LocalLoader(AbstractLoader):
    def __init__(self, player_backends: Dict[str, type[PlayerBackend]]) -> None:
        super().__init__(player_backends)
        self.module_loader_threads: List[QObject] = []
        self.player_backends = player_backends
        self.files: list[str] = []

    def load_module(self, song: Song) -> None:
        logger.debug("Loading local module")

        module_loader_thread = LocalLoaderThread()
        module_loader_thread.files = self.files

        self.module_loader_threads.append(module_loader_thread)

        module_loader_thread.module_loaded.connect(self.on_module_loaded)
        module_loader_thread.start()
