from current_playing_mode import CurrentPlayingMode
import os
import shutil
import tempfile


class DownloadManager:
    def __init__(self, web_helper):
        self.web_helper = web_helper
        self.temp_dir = tempfile.mkdtemp()

    def download_module(self, mode, member_id=None, artist=None):
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
                return self.web_helper.download_artist_module(artist, self.temp_dir)
            case _:
                return None

    def __del__(self):
        shutil.rmtree(self.temp_dir)
