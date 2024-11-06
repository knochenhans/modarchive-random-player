from current_playing_mode import CurrentPlayingMode
import os
import shutil
import tempfile
from typing import Dict, Optional
from web_helper import WebHelper


class DownloadManager:
    def __init__(self, web_helper: WebHelper) -> None:
        self.web_helper = web_helper
        self.temp_dir = tempfile.mkdtemp()

    def download_module(
        self,
        mode: CurrentPlayingMode,
        member_id: Optional[str] = None,
        artist: Optional[str] = None,
    ) -> Optional[Dict[str, Optional[str]]]:
        match mode:
            case CurrentPlayingMode.RANDOM:
                return self.web_helper.download_random_module(self.temp_dir)
            case CurrentPlayingMode.FAVORITE:
                if member_id:
                    return self.web_helper.download_favorite_module(
                        member_id, self.temp_dir
                    )
                else:
                    return None
            case CurrentPlayingMode.ARTIST:
                if artist:
                    return self.web_helper.download_artist_module(artist, self.temp_dir)
        return None

    def __del__(self) -> None:
        shutil.rmtree(self.temp_dir)
