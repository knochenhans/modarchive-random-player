import shutil
from PySide6.QtCore import Signal
from typing import Optional

from current_playing_mode import CurrentPlayingMode
from player_backends.player_backend import Song
from web_helper import WebHelper
from module_loader_thread import ModuleLoaderThread

class ModArchiveLoaderThread(ModuleLoaderThread):
    module_loaded = Signal(Song)

    def __init__(self) -> None:
        super().__init__()
        self.web_helper: Optional[WebHelper] = None
        self.current_playing_mode: Optional[CurrentPlayingMode] = None
        self.member_id: Optional[int] = None
        self.artist: Optional[str] = None
        self.temp_dir: Optional[str] = None

    def load_module(self) -> Optional[Song]:
        if self.web_helper and self.current_playing_mode:
            if self.temp_dir:
                match self.current_playing_mode:
                    case CurrentPlayingMode.RANDOM:
                        return self.web_helper.download_random_module(self.temp_dir)
                    case CurrentPlayingMode.FAVORITE:
                        if self.member_id:
                            return self.web_helper.download_favorite_module(
                                self.member_id, self.temp_dir
                            )
                        else:
                            return None
                    case CurrentPlayingMode.ARTIST:
                        if self.artist:
                            return self.web_helper.download_artist_module(
                                self.artist, self.temp_dir
                            )
            else:
                raise ValueError("Temporary directory not set")
        return None
