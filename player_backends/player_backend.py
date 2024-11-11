from abc import ABC, abstractmethod
import hashlib
from typing import Any
from dataclasses import dataclass, field

from player_backends.libuade.songinfo import Credits


@dataclass
class Song:
    filename: str = ""
    backend_name: str = ""
    modarchive_id: str = ""
    artist: str = ""
    container: str = ""
    container_long: str = ""
    date: str = ""
    extensions: str = ""
    formatname: str = ""
    message: str = ""
    message_raw: str = ""
    md5: str = ""
    modulebytes: int = 0
    originaltype: str = ""
    originaltype_long: str = ""
    playername: str = ""
    playerfname: str = ""
    sha1: str = ""
    title: str = ""
    tracker: str = ""
    type: str = ""
    type_long: str = ""
    warnings: str = ""
    credits: Credits = field(default_factory=lambda: Credits(
        song_title="",
        artistname="",
        file_length="",
        file_name="",
        file_prefix="",
        max_positions=0,
        modulename="",
        specialinfo="",
        instruments=[],
    ))


class PlayerBackend(ABC):
    def __init__(self, name: str) -> None:
        self.song: Song = Song()
        self.mod: Any = None
        self.name: str = name

    @abstractmethod
    def check_module(self) -> bool:
        pass

    @abstractmethod
    def retrieve_song_info(self) -> None:
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

    def calculate_checksums(self) -> None:
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()

        with open(self.song.filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
                sha1.update(chunk)

        self.song.md5 = md5.hexdigest()
        self.song.sha1 = sha1.hexdigest()

    @abstractmethod
    def seek(self, position: int) -> None:
        pass
