from abc import ABC, abstractmethod
from PySide6.QtCore import QThread, Signal
from typing import Optional

from player_backends.Song import Song


class ModuleLoaderThread(QThread):
    module_loaded = Signal(Song)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        song: Optional[Song] = self.load_module()
        if song:
            self.module_loaded.emit(song)
        else:
            self.module_loaded.emit({})

    @abstractmethod
    def load_module(self) -> Optional[Song]:
        pass
