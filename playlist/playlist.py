from typing import List, Optional
from player_backends.Song import Song
from PySide6.QtCore import Signal, QObject


class Playlist(QObject):
    song_added = Signal(Song)
    song_removed = Signal(Song)
    song_moved = Signal(Song, int)

    def __init__(
        self, name: str = "Empty Playlist", songs: List[Song] | None = None
    ) -> None:
        super().__init__()
        self.name: str = name
        self.songs: List[Song] = songs if songs else []
        self.current_song: int = 0

    def add_song(self, song: Song) -> None:
        self.songs.append(song)
        self.song_added.emit(song)

    def remove_song(self, song: Song) -> None:
        self.songs.remove(song)
        self.song_removed.emit(song)

    def move_song(self, song: Song, index: int) -> None:
        self.songs.remove(song)
        self.songs.insert(index, song)
        self.song_moved.emit(song, index)

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
