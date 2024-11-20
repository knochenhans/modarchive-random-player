from PySide6.QtWidgets import QDialog, QVBoxLayout
from player_backends.Song import Song
from playlist.playlist import Playlist
from typing import Optional
from PySide6.QtCore import Signal

from playlist.playlist_tab_widget import PlaylistTabWidget


class HistoryDialog(QDialog):
    song_on_tab_double_clicked = Signal(Song)

    def __init__(self, playlist: Optional[Playlist], parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("History")
        self.setGeometry(100, 100, 600, 400)

        self.tab_widget = PlaylistTabWidget(self, False)
        self.tab_widget.song_double_clicked.connect(self.on_song_double_clicked)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)

        self.setLayout(self.main_layout)

        self.tab_widget.add_tab("History")

        if playlist:
            for song in playlist.songs:
                self.add_song(song)

        self.show()

    def on_song_double_clicked(self, song: Song) -> None:
        self.song_on_tab_double_clicked.emit(song)

    def add_song(self, song: Song) -> None:
        self.tab_widget.add_song(song)

    def update_song_info(self, song: Song) -> None:
        self.tab_widget.update_song_info(song)
