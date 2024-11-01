from abc import ABC, abstractmethod
from typing import Any, Dict, TypedDict
import os

from player_backends.libuade.songinfo import Credits


class SongMetadata(TypedDict):
    filename: str
    type: str
    type_long: str
    originaltype: str
    originaltype_long: str
    container: str
    container_long: str
    tracker: str
    artist: str
    title: str
    date: str
    message: str
    message_raw: str
    warnings: str
    md5: str
    sha1: str
    playername: str
    playerfname: str
    credits: Credits


class PlayerBackend(ABC):
    def __init__(self) -> None:
        self.song_metadata: SongMetadata = {
            "filename": "",
            "type": "",
            "type_long": "",
            "originaltype": "",
            "originaltype_long": "",
            "container": "",
            "container_long": "",
            "tracker": "",
            "artist": "",
            "title": "",
            "date": "",
            "message": "",
            "message_raw": "",
            "warnings": "",
            "md5": "",
            "sha1": "",
            "playername": "",
            "playerfname": "",
            "credits": {
                "song_title": "",
                "authorname": "",
                "file_length": "",
                "file_name": "",
                "file_prefix": "",
                "max_positions": 0,
                "modulename": "",
                "specialinfo": "",
                "instruments": [],
            },
        }
        self.mod: Any = None

    @abstractmethod
    def load_module(self, module_filename: str) -> bool:
        pass

    @abstractmethod
    def get_module_length(self) -> float:
        pass

    @abstractmethod
    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        pass

    @abstractmethod
    def get_position_seconds(self) -> float:
        pass

    @abstractmethod
    def free_module(self) -> None:
        pass
