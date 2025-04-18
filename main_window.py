import json
import os
import sys
from typing import Any, Dict, List, Optional

from appdirs import user_config_dir, user_data_dir
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMenuBar,
    QVBoxLayout,
    QWidget,
)

from icons import Icons
from playlist.playlist_tab_widget import PlaylistTabWidget
from playlist.playlist_tree_view import PlaylistTreeView
from settings.settings import Settings
from loguru import logger


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.settings: Settings = Settings(
            "playlist_configuration",
            os.path.join(user_config_dir(), self.application_name),
        )
        self.settings.load()

        self.playlists_path: str = os.path.join(
            user_data_dir(self.application_name), "playlist"
        )
        os.makedirs(self.playlists_path, exist_ok=True)

        self.tab_widget: PlaylistTabWidget = PlaylistTabWidget(self, self.settings)
        layout.addWidget(self.tab_widget)
        self.tab_widget.tab_added.connect(self.create_new_playlist)
        self.tab_widget.tab_deleted.connect(self.delete_playlist)
        self.tab_widget.tab_renamed.connect(self.rename_playlist)

        self.create_menu_bar()

        self.load_playlists()

        self.current_playlist: PlaylistTreeView = self.tab_widget.get_current_tab()

    def create_menu_bar(self) -> None:
        menu_bar: QMenuBar = self.menuBar()

        file_menu: QMenu = menu_bar.addMenu("&File")

        new_playlist_action: QAction = QAction("&New Playlist", self)
        new_playlist_action.triggered.connect(self.create_new_playlist)
        file_menu.addAction(new_playlist_action)

        import_action: QAction = QAction("&Import Playlist", self)
        import_action.triggered.connect(self.import_playlist)
        file_menu.addAction(import_action)

        export_action: QAction = QAction("&Export Playlist", self)
        export_action.triggered.connect(self.export_playlist)
        file_menu.addAction(export_action)

        delete_playlist_action: QAction = QAction("&Delete Playlist", self)
        delete_playlist_action.triggered.connect(self.on_delete_playlist)
        file_menu.addAction(delete_playlist_action)

        file_menu.addSeparator()

        exit_action: QAction = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_new_playlist(self) -> None:
        playlist_name = "New Playlist"
        new_playlist_tree_view: PlaylistTreeView = PlaylistTreeView(
            Icons(self.settings, self.style()), self.settings, self
        )
        new_playlist_tree_view.setWindowTitle(playlist_name)
        self.tab_widget.addTab(new_playlist_tree_view, playlist_name)
        new_playlist_tree_view.item_double_clicked.connect(self.on_item_double_clicked)

    def import_playlist(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Playlist", "", "JSON Files (*.json)"
        )
        if file_path:
            with open(file_path, "r") as f:
                playlist_data = json.load(f)
                playlist_name = playlist_data["name"]
                playlist_items = playlist_data["data"]
                column_widths = playlist_data.get("column_widths", [])
                self.add_playlist(playlist_name, playlist_items, column_widths)
                logger.info(f"Imported playlist: {playlist_name}")

    def export_playlist(self) -> None:
        if self.current_playlist:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Playlist", "", "JSON Files (*.json)"
            )
            if file_path:
                playlist_data = self.current_playlist.get_playlist_data()
                playlist_name = self.current_playlist.windowTitle()
                column_widths = self.current_playlist.get_column_widths()
                with open(file_path, "w") as f:
                    json.dump(
                        {
                            "name": playlist_name,
                            "data": playlist_data,
                            "column_widths": column_widths,
                        },
                        f,
                        indent=4,
                    )
                logger.info(f"Exported playlist to {file_path}")

    def on_delete_playlist(self) -> None:
        self.delete_playlist()

    def delete_playlist(self, playlist_index: Optional[int] = None) -> None:
        if playlist_index is None:
            playlist_index = self.tab_widget.currentIndex()

        if playlist_index != -1:
            playlist_name = self.tab_widget.tabText(playlist_index)
            self.tab_widget.removeTab(playlist_index)
            logger.info(f"Deleted playlist: {playlist_name}")
        else:
            logger.warning("No playlist selected to delete.")

    def rename_playlist(self, new_name: str) -> None:
        # Rename the current playlist tab via window title
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.tab_widget.setTabText(current_index, new_name)
            self.tab_widget.widget(current_index).setWindowTitle(new_name)
            logger.info(f"Renamed playlist to: {new_name}")

    def on_item_double_clicked(self, row: int) -> None:
        sender = self.sender()
        if isinstance(sender, PlaylistTreeView):
            sender.set_currently_playing_row(row)
            self.current_playlist = sender

    def add_playlist(
        self,
        playlist_name: str,
        playlist_data: List[Dict[str, Any]],
        column_widths: list[int] = [],
    ) -> None:
        icons: Icons = Icons(self.settings, self.style())

        new_playlist_tree_view: PlaylistTreeView = PlaylistTreeView(
            icons, self.settings, self
        )
        self.tab_widget.addTab(new_playlist_tree_view, playlist_name)

        new_playlist_tree_view.setWindowTitle(playlist_name)
        new_playlist_tree_view.set_playlist_data(playlist_data)
        new_playlist_tree_view.item_double_clicked.connect(self.on_item_double_clicked)

        new_playlist_tree_view.set_column_widths(column_widths)

    def load_playlists(self) -> None:
        for filename in sorted(os.listdir(self.playlists_path)):
            if filename.endswith(".json"):
                playlist_file_path = os.path.join(self.playlists_path, filename)
                with open(playlist_file_path, "r") as f:
                    playlist_data = json.load(f)
                    playlist_name = playlist_data["name"]
                    playlist_items = playlist_data["data"]
                    column_widths = playlist_data.get("column_widths", [])

                    self.add_playlist(playlist_name, playlist_items, column_widths)
                    logger.info(f"Loaded playlist: {playlist_name}")

    def save_playlists(self) -> None:
        # Remove existing files in the playlists directory
        for filename in os.listdir(self.playlists_path):
            file_path = os.path.join(self.playlists_path, filename)
            if os.path.isfile(file_path) and filename.endswith(".json"):
                os.remove(file_path)

        # Save current playlists
        for i in range(self.tab_widget.count()):
            playlist_tree_view = self.tab_widget.widget(i)

            if isinstance(playlist_tree_view, PlaylistTreeView):
                playlist_data = playlist_tree_view.get_playlist_data()
                playlist_name = self.tab_widget.tabText(i)
                column_widths = playlist_tree_view.get_column_widths()
                playlist_file_path = os.path.join(self.playlists_path, f"{i}.json")

                with open(playlist_file_path, "w") as f:
                    json.dump(
                        {
                            "name": playlist_name,
                            "data": playlist_data,
                            "column_widths": column_widths,
                        },
                        f,
                        indent=4,
                    )
                logger.info(f"Playlist saved to {playlist_file_path}")

    def closeEvent(self, event) -> None:
        self.save_playlists()
        event.accept()


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
