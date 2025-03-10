from abc import ABC, abstractmethod
import hashlib
from typing import Any, Callable, Optional

from player_backends.Song import Song


class PlayerBackend:
    def __init__(self, name: str) -> None:
        self.song: Optional[Song] = None
        self.mod: Any = None
        self.name: str = name
        self.current_subsong: int = 0
        self.subsong_changed_callback: Optional[Callable[[int, int], None]] = None
        self.song_name_changed_callback: Optional[Callable[[str], None]] = None

    def set_subsong_changed_callback(
        self, callback: Callable[[int, int], None]
    ) -> None:
        self.subsong_changed_callback = callback

    def set_song_name_changed_callback(self, callback: Callable[[str], None]) -> None:
        self.song_name_changed_callback = callback

    def check_module(self) -> bool:
        return False

    def prepare_playing(self, subsong_nr: int = -1) -> None:
        pass

    def retrieve_song_info(self) -> None:
        pass

    def get_module_length(self) -> float:
        return 0.0

    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        return 0, b""

    def get_position_seconds(self) -> float:
        return 0.0

    def get_current_subsong(self) -> int:
        return self.current_subsong

    def free_module(self) -> None:
        pass

    def calculate_checksums(self) -> None:
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()

        if not self.song:
            return

        with open(self.song.filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
                sha1.update(chunk)

        self.song.md5 = md5.hexdigest()
        self.song.sha1 = sha1.hexdigest()

    def seek(self, position: int) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def notify_subsong_changed(self, current: int, total: int) -> None:
        if self.subsong_changed_callback:
            self.subsong_changed_callback(current, total)

    def notify_song_name_changed(self, name: str) -> None:
        if self.song_name_changed_callback:
            self.song_name_changed_callback(name)
