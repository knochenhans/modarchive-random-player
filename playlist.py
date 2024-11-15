from typing import List, Optional
from player_backends.Song import Song


class Playlist:
    def __init__(
        self, name: str = "Empty Playlist", songs: List[Song] | None = None
    ) -> None:
        self.name: str = name
        self.songs: List[Song] = songs if songs else []
        self.current_song: int = 0

    def add_song(self, song: Song) -> None:
        self.songs.append(song)

    def remove_song(self, song: Song) -> None:
        self.songs.remove(song)

    def next_song(self) -> Optional[Song]:
        self.current_song += 1
        if self.current_song < len(self.songs):
            return self.songs[self.current_song]
        return None

    def previous_song(self) -> Optional[Song]:
        self.current_song -= 1
        if self.current_song > 0:
            return self.songs[self.current_song]
        return None

    def get_song(self, index: int) -> Song:
        return self.songs[index]

    def clear(self) -> None:
        self.songs.clear()

    def get_length(self) -> int:
        return len(self.songs)

    def __str__(self) -> str:
        return f"Playlist: {self.name}\nSongs: {self.songs}"
