from PySide6.QtCore import Signal
from typing import Optional

from player_backends.Song import Song
from web_helper import WebHelper
from module_loader_thread import ModuleLoaderThread


class ModArchiveLoaderThread(ModuleLoaderThread):
    module_loaded = Signal(Song)

    def __init__(self) -> None:
        super().__init__()
        self.web_helper: Optional[WebHelper] = None
        self.song: Optional[Song] = None
        self.temp_dir: Optional[str] = None

    def load_module(self) -> Optional[Song]:
        if self.web_helper:
            if self.temp_dir:
                if self.song:
                    filename = self.web_helper.download_module_file(
                        self.song.modarchive_id, self.temp_dir
                    )

                    if filename:
                        song: Song = Song()
                        song.filename = filename
                        song.is_ready = True
                        song.modarchive_id = self.song.modarchive_id
                        return song
                else:
                    raise ValueError("Song ID not set")
            else:
                raise ValueError("Temporary directory not set")
        return None
