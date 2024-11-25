from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout
from player_backends.Song import Song
from playing_engine import PlayingEngine
from playlist.playlist import Playlist
from typing import Optional
from PySide6.QtCore import Signal, Qt

from playlist.playlist_manager import PlaylistManager
from playlist.playlist_tab_widget import PlaylistTabWidget
from settings_manager import SettingsManager


class HistoryDialog(QDialog):
    song_on_tab_double_clicked = Signal(Song)

    def __init__(
        self,
        playing_engine: PlayingEngine,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)

        self.playing_engine = playing_engine

        self.setWindowTitle("History")
        self.setGeometry(self.playing_engine.settings_manager.get_history_dialog_geometry())

        self.tab_widget = PlaylistTabWidget(self, self.playing_engine.playlist_manager, False)
        self.tab_widget.song_double_clicked.connect(self.on_song_double_clicked)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)

        self.setLayout(self.main_layout)

        self.tab_widget.add_tab(self.playing_engine.playlist_manager.get_history_playlist())

        self.show()

        # Hide first column
        self.tab_widget.get_current_tab().setColumnHidden(0, True)

    def on_song_double_clicked(self, song: Song, row: int) -> None:
        self.song_on_tab_double_clicked.emit(song)

    def add_song(self, song: Song) -> None:
        self.tab_widget.add_song(song)

    def update_song_info(self, song: Song) -> None:
        # self.tab_widget.update_song_info(song)
        pass

    def closeEvent(self, event: QCloseEvent) -> None:
        self.playing_engine.settings_manager.set_history_dialog_geometry(self.geometry())
        event.accept()
