from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
)

from playlist.playlist import Playlist
from player_backends.Song import Song
from playlist.playlist_manager import PlaylistManager
from typing import Optional

from playlist.playlist_tab import PlaylistTab


class PlaylistExport:
    """Playlist representation for export as playlist file"""

    def __init__(
        self, name: str = "", songs=None, current_song=0, current_song_pos=0
    ) -> None:
        self.name = name
        self.songs = songs
        self.current_song = current_song
        self.current_song_pos = current_song_pos


class PlaylistsDialog(QDialog):
    song_on_tab_double_clicked = Signal(Song)

    def __init__(
        self, playlist_manager: Optional[PlaylistManager], parent=None
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Playlists")
        self.setGeometry(100, 100, 600, 400)

        self.tab_widget = PlaylistTab(self)
        self.tab_widget.song_double_clicked.connect(self.on_song_double_clicked)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)

        self.setLayout(self.main_layout)

        if playlist_manager:
            for playlist in playlist_manager.playlists:
                self.add_playlist(playlist)

        self.show()

    def add_playlist(self, playlist: Playlist) -> None:
        self.tab_widget.add_tab(playlist.name)
        for song in playlist.songs:
            self.tab_widget.add_song(song)

    def on_song_double_clicked(self, song: Song) -> None:
        self.song_on_tab_double_clicked.emit(song)
