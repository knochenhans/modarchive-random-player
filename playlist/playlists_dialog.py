from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QMenuBar,
)
from PySide6.QtGui import (
    QAction,
)

from loaders.local_loader import LocalLoader
from player_backends.player_backend import PlayerBackend
from playlist.playlist import Playlist
from player_backends.Song import Song
from playlist.playlist_manager import PlaylistManager
from typing import Optional

from playlist.playlist_tab import PlaylistTab
from PySide6.QtWidgets import QMenuBar, QFileDialog
import os


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
        self,
        playlist_manager: Optional[PlaylistManager],
        backends: dict[str, type[PlayerBackend]],
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.backends = backends
        self.module_loaders = []

        self.setWindowTitle("Playlists")
        self.setGeometry(100, 100, 600, 400)

        self.tab_widget = PlaylistTab(self)
        self.tab_widget.song_double_clicked.connect(self.on_song_double_clicked)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)

        self.setLayout(self.main_layout)

        self.create_menu_bar()

        self.playlist_manager = playlist_manager

        if self.playlist_manager:
            for playlist in self.playlist_manager.playlists:
                self.add_playlist(playlist)

        self.show()

    def add_playlist(self, playlist: Playlist) -> None:
        self.tab_widget.add_tab(playlist.name)
        for song in playlist.songs:
            self.tab_widget.add_song(song)

    def on_song_double_clicked(self, song: Song) -> None:
        self.song_on_tab_double_clicked.emit(song)

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)

        file_menu = menu_bar.addMenu("File")

        load_file_action = QAction("Load File", self)
        load_file_action.triggered.connect(self.on_load_file)
        file_menu.addAction(load_file_action)

        load_folder_action = QAction("Load Folder", self)
        load_folder_action.triggered.connect(self.on_load_folder)
        file_menu.addAction(load_folder_action)

        self.main_layout.setMenuBar(menu_bar)

    def load_file(self, file_path: str):
        song = Song()
        song.filename = file_path

        module_loader = LocalLoader(self.backends)
        module_loader.files = [file_path]
        module_loader.load_module(song)
        module_loader.module_loaded.connect(self.add_song)
        
        self.module_loaders.append(module_loader)

    def load_folder(self, folder_path: str):
        file_list = self.get_files_recursively(folder_path)
        for file_path in file_list:
            self.load_file(file_path)

    def on_load_file(self):
        file_dialog = QFileDialog(self)
        file_paths, _ = file_dialog.getOpenFileNames(self, "Load Files")
        if file_paths:
            for file_path in file_paths:
                self.load_file(file_path)

    def add_song(self, song: Song) -> None:
        self.tab_widget.add_song(song)
        if self.playlist_manager:
            if self.playlist_manager.current_playlist:
                self.playlist_manager.current_playlist.add_song(song)

    def on_load_folder(self):
        folder_dialog = QFileDialog(self)
        folder_path = folder_dialog.getExistingDirectory(self, "Load Folder")
        if folder_path:
            self.load_folder(folder_path)

    def add_song_to_playlist(self, file_path: str):
        song = Song(file_path)
        self.tab_widget.add_song(song)

    def add_folder_to_playlist(self, folder_path: str):
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                self.add_song_to_playlist(file_path)

    def get_files_recursively(self, folder_path: str) -> list[str]:
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            dirs.sort()
            files.sort()
            for dir in dirs:
                file_list.extend(self.get_files_recursively(os.path.join(root, dir)))
            for file in files:
                file_list.append(os.path.join(root, file))
        return file_list
