from PySide6.QtCore import Signal, Slot

from PySide6.QtWidgets import QDialog, QVBoxLayout, QMenuBar, QProgressBar
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
)
from PySide6.QtCore import Qt

from loaders.local_file_loader import LocalFileLoader
from player_backends.player_backend import PlayerBackend
from playing_engine import PlayingEngine
from playlist.playlist import Playlist
from player_backends.Song import Song
from playlist.playlist_manager import PlaylistManager
from typing import Optional

from playlist.playlist_tab_widget import PlaylistTabWidget
from PySide6.QtWidgets import QMenuBar, QFileDialog
import os

from settings_manager import SettingsManager
from loguru import logger


class PlaylistsDialog(QDialog):
    song_on_tab_double_clicked = Signal(list, Playlist)

    def __init__(
        self,
        settings_manager: SettingsManager,
        playing_engine: PlayingEngine,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)

        self.settings_manager = settings_manager
        self.playing_engine = playing_engine
        self.local_file_loader: Optional[LocalFileLoader] = None

        self.setWindowTitle("Playlists")
        self.setGeometry(self.settings_manager.get_playlist_dialog_geometry())

        self.playlist_tab_widget = PlaylistTabWidget(
            self, self.playing_engine.playlist_manager
        )
        self.playlist_tab_widget.song_double_clicked.connect(
            self.on_song_double_clicked
        )

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.playlist_tab_widget)

        self.setLayout(self.main_layout)

        self.create_menu_bar()

        for playlist in self.playing_engine.playlist_manager.playlists:
            if playlist.name != "History":
                self.add_playlist(playlist)

        self.show()
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)

        self.files_remaining = 0
        self.files_loaded = 0
        self.total_files = 0

    def add_playlist(self, playlist: Optional[Playlist]) -> None:
        self.playlist_tab_widget.add_tab(playlist)

    def on_song_double_clicked(self, song: Song, row: int, playlist: Playlist) -> None:
        # Play all songs on the current playlist starting from the selected song
        songs = playlist.get_songs_from(row)
        self.song_on_tab_double_clicked.emit(songs, playlist)

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)

        file_menu = menu_bar.addMenu("File")

        load_file_action = QAction("Load File", self)
        load_file_action.triggered.connect(self.on_load_files)
        file_menu.addAction(load_file_action)

        load_folder_action = QAction("Load Folder", self)
        load_folder_action.triggered.connect(self.on_load_folder)
        file_menu.addAction(load_folder_action)

        new_playlist_action = QAction("New Playlist", self)
        new_playlist_action.triggered.connect(self.add_playlist)
        file_menu.addAction(new_playlist_action)

        export_playlist_action = QAction("Export Playlist", self)
        # export_playlist_action.triggered.connect(self.export_playlist)
        file_menu.addAction(export_playlist_action)

        self.main_layout.setMenuBar(menu_bar)

    def load_files(self, file_list: list[str]):
        self.progress_bar.show()

        self.total_files = len(file_list)
        self.files_remaining = self.total_files
        self.progress_bar.setMaximum(self.total_files)

        self.local_file_loader = LocalFileLoader(
            file_list, self.playing_engine.player_backends
        )
        self.local_file_loader.song_loaded.connect(self.load_song)
        self.local_file_loader.song_info_retrieved.connect(self.update_song_info)
        self.local_file_loader.all_songs_loaded.connect(self.finished_loading_songs)
        self.local_file_loader.load_modules()

    def load_folder(self, folder_path: str):
        logger.info(f"Loading folder: {folder_path}")
        file_list = self.get_files_recursively(folder_path)
        self.load_files(file_list)

    def on_load_files(self):
        last_folder = self.settings_manager.get_last_folder()

        file_dialog = QFileDialog(self)
        file_paths, _ = file_dialog.getOpenFileNames(self, "Load Files", last_folder)
        if file_paths:
            self.load_files(file_paths)
            self.settings_manager.set_last_folder(os.path.dirname(file_paths[0]))

    @Slot()
    def finished_loading_songs(self):
        logger.info(f"Loaded {self.total_files} files")

    def load_song(self, song: Song) -> None:
        self.files_loaded += 1

        if song:
            if song.backend_name:
                self.playlist_tab_widget.load_song(song)

        if self.files_loaded < self.files_remaining:
            self.progress_bar.setValue(self.files_loaded)
        else:
            self.progress_bar.hide()
            self.files_remaining = 0
            self.files_loaded = 0
        self.update()

    def update_song_info(self, song: Song) -> None:
        self.playlist_tab_widget.update_song_info(-1, song)
        # self.update()

    def add_song(self, song: Song) -> None:
        self.playlist_tab_widget.add_song(song)

    def on_load_folder(self):
        last_folder = self.settings_manager.get_last_folder()

        folder_dialog = QFileDialog(self)
        folder_path = folder_dialog.getExistingDirectory(
            self, "Load Folder", last_folder
        )
        if folder_path:
            self.load_folder(folder_path)
            self.settings_manager.set_last_folder(folder_path)

    def add_song_to_playlist(self, file_path: str):
        song = Song(filename=file_path)
        self.playlist_tab_widget.add_song(song)

    def get_files_recursively(self, folder_path: str) -> list[str]:
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            dirs.sort(key=lambda s: s.lower())
            files.sort(key=lambda s: s.lower())
            for dir in dirs:
                file_list.extend(self.get_files_recursively(os.path.join(root, dir)))
            for file in files:
                file_list.append(os.path.join(root, file))
        return file_list

    def closeEvent(self, event: QCloseEvent) -> None:
        self.settings_manager.set_playlist_dialog_geometry(self.geometry())
        event.accept()
