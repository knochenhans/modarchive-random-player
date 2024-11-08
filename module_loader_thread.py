from PySide6.QtCore import QThread, Signal
from typing import Optional

from player_backends.player_backend import Song


class ModuleLoaderThread(QThread):
    module_loaded = Signal(Song)

    def __init__(
        self, download_manager, current_playing_mode, member_id, artist_input
    ) -> None:
        super().__init__()
        self.download_manager = download_manager
        self.current_playing_mode = current_playing_mode
        self.member_id = member_id
        self.artist_input = artist_input

        self.module_loader_thread: Optional[ModuleLoaderThread] = None

    def run(self) -> None:
        song = self.download_manager.download_module(
            self.current_playing_mode, self.member_id, self.artist_input
        )
        if song:
            self.module_loaded.emit(song)
        else:
            self.module_loaded.emit({})
