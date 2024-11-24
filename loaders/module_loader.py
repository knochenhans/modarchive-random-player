from loguru import logger
from typing import List, Dict
from PySide6.QtCore import QObject

from playing_modes import PlayingSource
from loaders.abstract_loader import AbstractLoader
from loaders.local_loader_thread import LocalLoaderThread
from loaders.modarchive_downloader_thread import ModArchiveDownloaderThread
from player_backends.player_backend import PlayerBackend
from playing_settings import PlayingSettings
from web_helper import WebHelper
from player_backends.Song import Song


class ModuleLoader(AbstractLoader):
    def __init__(
        self,
        playing_settings: PlayingSettings,
        local_file: str,
        web_helper: object,
        temp_dir: str,
        player_backends: Dict[str, type[PlayerBackend]],
    ) -> None:
        super().__init__(player_backends)
        self.playing_settings = playing_settings
        self.local_file = local_file
        self.web_helper = web_helper
        self.temp_dir = temp_dir
        self.module_loader_threads: List[QObject] = []
        self.player_backends = player_backends

    def load_modules(self, song: Song) -> None:
        logger.debug("Loading module")

        if self.playing_settings.playing_source == PlayingSource.LOCAL:
            module_loader_thread = LocalLoaderThread()
            module_loader_thread.filename = self.local_file
        elif self.playing_settings.playing_source == PlayingSource.MODARCHIVE:
            module_loader_thread = ModArchiveDownloaderThread()
            module_loader_thread.song = song
            module_loader_thread.web_helper = WebHelper()
            module_loader_thread.temp_dir = self.temp_dir

        self.module_loader_threads.append(module_loader_thread)

        module_loader_thread.module_loaded.connect(self.on_module_loaded)
        module_loader_thread.start()
