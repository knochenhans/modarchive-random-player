import json
from typing import Callable, List, Optional
from uuid import uuid4


class Playlist:
    def __init__(
        self,
        name: str = "Empty Playlist",
        song_ids: Optional[List[str]] = None,
        on_song_added: Optional[Callable[[str], None]] = None,
        on_song_removed: Optional[Callable[[str], None]] = None,
        on_song_moved: Optional[Callable[[str, int], None]] = None,
    ) -> None:
        self.id: str = str(uuid4())
        self.name: str = name
        self.song_ids: List[str] = song_ids if song_ids else []
        self.on_song_added = on_song_added
        self.on_song_removed = on_song_removed
        self.on_song_moved = on_song_moved

    def add_song(self, song_id: str) -> None:
        self.song_ids.append(song_id)
        if self.on_song_added:
            self.on_song_added(song_id)

    def remove_song(self, song_id: str) -> None:
        self.song_ids.remove(song_id)
        if self.on_song_removed:
            self.on_song_removed(song_id)

    def move_song(self, song_id: str, index: int) -> None:
        self.song_ids.remove(song_id)
        self.song_ids.insert(index, song_id)
        if self.on_song_moved:
            self.on_song_moved(song_id, index)

    def get_length(self) -> int:
        return len(self.song_ids)

    def to_json(self, filename: str) -> None:
        playlist_data = {
            "id": self.id,
            "name": self.name,
            "song_ids": self.song_ids,
        }
        with open(filename, "w") as f:
            json.dump(playlist_data, f)

    @classmethod
    def from_json(cls, filename: str) -> "Playlist":
        with open(filename, "r") as f:
            playlist_data = json.load(f)
            playlist = cls(playlist_data["name"], playlist_data["song_ids"])
            playlist.id = playlist_data["id"]
            return playlist
