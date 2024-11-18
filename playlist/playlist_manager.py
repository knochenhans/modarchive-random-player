from typing import Optional
from player_backends.Song import Song
from playlist.playlist import Playlist
from PySide6.QtCore import QObject, Signal


class PlaylistManager(QObject):
    song_added_to_playlist = Signal(Playlist, Song)
    song_removed_from_playlist = Signal(Playlist, Song)
    song_moved_on_playlist = Signal(Playlist, Song, int)
    current_song_on_playlist_changed = Signal(Playlist, Song, int)

    def __init__(self) -> None:
        super().__init__()
        self.playlists: list[Playlist] = []
        self.current_playlist: Optional[Playlist] = None

    def add_playlist(self, name: str) -> Playlist:
        playlist = Playlist(name)
        playlist.song_added.connect(lambda song: self.on_song_added_to_playlist(playlist, song))
        playlist.song_removed.connect(lambda song: self.on_song_removed_from_playlist(playlist, song))
        playlist.song_moved.connect(lambda song, index: self.on_song_moved_on_playlist(playlist, song, index))
        self.playlists.append(playlist)
        self.current_playlist = playlist
        return playlist

    def delete_playlist(self, index: int) -> None:
        del self.playlists[index]
        if self.current_playlist == index:
            self.current_playlist = None

    def get_playlist(self, index: int) -> Playlist:
        return self.playlists[index]

    def get_current_playlist(self) -> Optional[Playlist]:
        return self.current_playlist

    def on_song_added_to_playlist(self, playlist: Playlist, song: Song) -> None:
        self.song_added_to_playlist.emit(playlist, song)

    def on_song_removed_from_playlist(self, playlist: Playlist, song: Song) -> None:
        self.song_removed_from_playlist.emit(playlist, song)

    def on_song_moved_on_playlist(
        self, playlist: Playlist, song: Song, index: int
    ) -> None:
        self.song_moved_on_playlist.emit(playlist, song, index)

    def on_current_song_on_playlist_changed(
        self, playlist: Playlist, song: Song, index: int
    ) -> None:
        self.current_song_on_playlist_changed.emit(playlist, song, index)

    def save_playlist(self, name: str, filename: str) -> None:
        for playlist in self.playlists:
            if playlist.name == name:
                with open(filename, "w") as f:
                    for song in playlist.songs:
                        f.write(song.to_json() + "\n")
                break
