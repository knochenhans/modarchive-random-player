import os
from typing import Optional

from platformdirs import user_config_dir
from player_backends.Song import Song
from playlist.playlist import Playlist
from PySide6.QtCore import QObject, Signal

from settings_manager import SettingsManager


class PlaylistManager(QObject):
    song_added_to_playlist = Signal(Playlist, Song)
    song_removed_from_playlist = Signal(Playlist, Song)
    song_moved_on_playlist = Signal(Playlist, Song, int)

    def __init__(self, settings_manager: SettingsManager) -> None:
        super().__init__()
        self.settings_manager = settings_manager
        self.playlists: list[Playlist] = []
        self.current_playlist: Optional[Playlist] = None
        self.config_dir = user_config_dir(self.settings_manager.get_app_name())

    def load_playlists(self) -> None:
        for file_name in os.listdir(self.config_dir):
            if file_name.endswith(".playlist"):
                self.load_playlist(os.path.join(self.config_dir, file_name))

        # If only history playlist exists, create a default playlist
        if len(self.playlists) == 1:
            self.new_playlist("Default Playlist")
        self.sort()

    def save_playlists(self) -> None:
        for playlist in self.playlists:
            if playlist.name != "History":
                self.save_playlist(playlist)

    def save_playlist(self, playlist: Playlist):
        filename = os.path.join(self.config_dir, f"{playlist.uuid}.playlist")
        playlist.to_json(filename)

    def add_playlist(self, playlist: Playlist) -> None:
        self.playlists.append(playlist)
        playlist.song_added.connect(
            lambda song: self.on_song_added_to_playlist(playlist, song)
        )
        playlist.song_removed.connect(
            lambda song: self.on_song_removed_from_playlist(playlist, song)
        )
        playlist.song_moved.connect(
            lambda song, index: self.on_song_moved_on_playlist(playlist, song, index)
        )
        self.current_playlist = playlist

    def new_playlist(self, name: str = "") -> Playlist:
        playlist = Playlist(name)
        playlist.tab_index = self.get_new_tab_index()
        self.add_playlist(playlist)
        return playlist
    
    def get_new_tab_index(self) -> int:
        return len(self.playlists)

    def delete_playlist(self, index: int) -> None:
        del self.playlists[index]
        if self.current_playlist == index:
            self.current_playlist = None

    def get_playlist(self, index: int) -> Playlist:
        return self.playlists[index]

    def get_current_playlist(self) -> Optional[Playlist]:
        return self.current_playlist
    
    def set_current_playlist(self, playlist: Playlist) -> None:
        self.current_playlist = playlist

    def set_current_playlist_by_index(self, index: int) -> None:
        # Set current playlist (index + 1 because of history playlist being at index 0)
        self.current_playlist = self.playlists[index + 1]

    # def set_current_song(self, song: Song) -> None:
    #     self.current_playlist.set_current_song(song)

    def on_song_added_to_playlist(self, playlist: Playlist, song: Song) -> None:
        self.song_added_to_playlist.emit(playlist, song)

    def on_song_removed_from_playlist(self, playlist: Playlist, song: Song) -> None:
        self.song_removed_from_playlist.emit(playlist, song)

    def on_song_moved_on_playlist(
        self, playlist: Playlist, song: Song, index: int
    ) -> None:
        self.song_moved_on_playlist.emit(playlist, song, index)

    def load_playlist(self, filename: str):
        playlist = Playlist.from_json(filename)

        self.add_playlist(playlist)

    def get_history_playlist(self) -> Optional[Playlist]:
        for playlist in self.playlists:
            if playlist.name == "History":
                return playlist
        return None
    
    def sort(self):
        self.playlists.sort(key=lambda x: x.tab_index)

    def playlist_moved(self, from_index: int, to_index: int):
        self.playlists[from_index].tab_index = to_index
        self.playlists[to_index].tab_index = from_index
        self.sort()
