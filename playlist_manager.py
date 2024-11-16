from typing import Optional
from playlist import Playlist


class PlaylistManager:
    def __init__(self) -> None:
        self.playlists: list[Playlist] = []
        self.current_playlist: Optional[Playlist] = None

    def add_playlist(self, name: str) -> Playlist:
        playlist = Playlist(name)
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