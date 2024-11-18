from typing import List, Optional
from uuid import uuid4
from player_backends.Song import Song
from PySide6.QtCore import Signal, QObject


class Playlist(QObject):
    song_added = Signal(Song)
    song_removed = Signal(Song)
    song_moved = Signal(Song, int)
    current_song_changed = Signal(Song, int)

    def __init__(
        self, name: str = "Empty Playlist", songs: List[Song] | None = None
    ) -> None:
        super().__init__()
        self.uuid: str = str(uuid4())
        self.name: str = name
        self.songs: List[Song] = songs if songs else []
        self.current_song_index: int = 0

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
        self.current_song_index += 1
        if self.current_song_index < len(self.songs):
            self.current_song_changed.emit(self.songs[self.current_song_index], self.current_song_index)
            return self.songs[self.current_song_index]
        return None

    def previous_song(self) -> Optional[Song]:
        self.current_song_index -= 1
        if self.current_song_index > 0:
            self.current_song_changed.emit(self.songs[self.current_song_index], self.current_song_index)
            return self.songs[self.current_song_index]
        return None

    def set_current_song(self, index: int) -> None:
        self.current_song_index = index
        self.current_song_changed.emit(self.songs[self.current_song_index], self.current_song_index)

    def get_song(self, index: int) -> Song:
        return self.songs[index]

    def clear(self) -> None:
        self.songs.clear()

    def get_length(self) -> int:
        return len(self.songs)

    def __str__(self) -> str:
        return f"Playlist: {self.name}\nSongs: {self.songs}"

    def to_json(self, filename: str) -> None:
        with open(filename, "w") as f:
            for song in self.songs:
                f.write(song.to_json() + "\n")

    @classmethod
    def from_json(cls, filename: str) -> "Playlist":
        with open(filename, "r") as f:
            songs = []
            for line in f:
                songs.append(Song.from_json(line))
            return cls(songs=songs)
