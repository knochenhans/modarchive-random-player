from PySide6.QtCore import QThread, Signal
from typing import Optional

from player_backends.Song import Song
from playing_modes import ModArchiveSource, PlayingMode, PlayingSource
from web_helper import WebHelper
from loguru import logger


class ModArchiveRandomModuleFetcherThread(QThread):
    module_fetched = Signal(Song)

    def __init__(
        self,
        song: Song,
        current_playing_mode: PlayingMode,
        current_playing_source: PlayingSource,
        current_modarchive_source: ModArchiveSource,
        web_helper: WebHelper,
        artist_name: str | None = None,
        member_id: int | None = None,
    ) -> None:
        super().__init__()

        self.song = song
        self.current_playing_mode = current_playing_mode
        self.current_playing_source = current_playing_source
        self.current_modarchive_source = current_modarchive_source
        self.web_helper = web_helper
        self.artist_name = artist_name
        self.member_id = member_id

    def run(self) -> None:
        self.fetch_random_module_id()

        if self.song:
            self.module_fetched.emit(self.song)
        else:
            self.module_fetched.emit({})

    def fetch_random_module_id(self) -> None:
        id: int | None = None

        if self.current_playing_mode == PlayingMode.RANDOM:
            if self.current_playing_source == PlayingSource.MODARCHIVE:
                match self.current_modarchive_source:
                    case ModArchiveSource.ALL:
                        logger.info("Getting random module")
                        id = self.web_helper.get_random_module_id()
                    case ModArchiveSource.FAVORITES:
                        if self.member_id:
                            logger.info("Getting random favorite module")
                            id = self.web_helper.get_random_favorite_module_id(
                                self.member_id
                            )
                    case ModArchiveSource.ARTIST:
                        if self.artist_name:
                            logger.info("Getting random artist module")
                            id = self.web_helper.get_random_artist_module_id(
                                self.artist_name
                            )
            if id:
                self.song.modarchive_id = id
