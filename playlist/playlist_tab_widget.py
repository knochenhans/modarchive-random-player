from typing import Optional
from player_backends.Song import Song
from playlist.playlist import Playlist
from playlist.playlist_manager import PlaylistManager
from playlist.playlist_model import PlaylistModel
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QTabWidget, QToolButton
from PySide6.QtGui import QKeyEvent

from playlist.playlist_tab_bar import PlaylistTabBar
from playlist.playlist_tab_bar_edit import PlaylistTabBarEdit
from playlist.playlist_tree_view import PlaylistTreeView
from tree_view_columns import tree_view_columns_dict


class PlaylistTabWidget(QTabWidget):
    song_double_clicked = Signal(Song, int, Playlist)

    def __init__(
        self, parent, playlist_manager: PlaylistManager, add_tab_button: bool = True
    ) -> None:
        super().__init__(parent)

        self.playlist_manager = playlist_manager

        self.tab_bar = PlaylistTabBar(parent)
        self.setTabBar(self.tab_bar)

        self.tabBarDoubleClicked.connect(self.doubleClicked)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)
        self.currentChanged.connect(self.current_tab_changed)

        if add_tab_button:
            self.add_tab_button = QToolButton()
            self.add_tab_button.setText(" + ")
            self.add_tab_button.clicked.connect(self.on_add_tab_button_clicked)

            self.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)

    @Slot()
    def current_tab_changed(self, index: int) -> None:
        tab = self.widget(index)
        if tab:
            self.playlist_manager.set_current_playlist_by_index(index)

    @Slot()
    def on_tab_moved(self, from_index: int, to_index: int) -> None:
        self.playlist_manager.playlist_moved(from_index, to_index)

        # Print playlists with tab_index
        for playlist in self.playlist_manager.playlists:
            print(playlist.name, playlist.tab_index)

    @Slot()
    def on_add_tab_button_clicked(self) -> None:
        self.add_tab()
        
        # Focus the new tab
        self.setCurrentIndex(self.count() - 1)

    def get_current_tab(self) -> PlaylistTreeView:
        return self.widget(self.currentIndex())  # type: ignore

    @Slot()
    def doubleClicked(self, index) -> None:
        tab_bar = self.tabBar()
        if isinstance(tab_bar, PlaylistTabBar):
            tab_bar.tab_renamed.connect(self.on_tab_renamed)
            tab_bar.edit_index = index
        edit = PlaylistTabBarEdit(self, self.tabBar().tabRect(index))
        edit.show()
        edit.setFocus()

        edit.editingFinished.connect(self.on_editing_finished)

    @Slot()
    def on_editing_finished(self) -> None:
        tab_bar = self.tabBar()
        if isinstance(tab_bar, PlaylistTabBar):
            tab_bar.editing_finished()

    @Slot()
    def on_tab_renamed(self, text: str) -> None:
        # self.tab_renamed.emit(text)
        tab = self.get_current_tab()
        if tab:
            tab.set_name(text)

    @Slot()
    def on_song_double_clicked(self, song: Song, row: int, playlist: Playlist) -> None:
        self.song_double_clicked.emit(song, row, playlist)

    def add_tab(self, playlist: Optional[Playlist] = None) -> PlaylistTreeView:
        if not playlist:
            playlist = Playlist("New Playlist")
            self.playlist_manager.add_playlist(playlist)

        tree = PlaylistTreeView(playlist, self)
        model = PlaylistModel(0, 3)

        tree.item_double_clicked.connect(self.on_song_double_clicked)

        items = tree_view_columns_dict.items()
        sorted_items = sorted(items, key=lambda x: x[1]["order"])
        labels = [str(col_info["name"]) for _, col_info in sorted_items]
        model.setHorizontalHeaderLabels(labels)

        tree.setModel(model)

        tree.set_playlist(playlist)

        self.addTab(tree, playlist.name)
        tree.update_current_row()

        return tree

    def add_song(self, song: Song) -> None:
        tab = self.get_current_tab()
        if tab:
            tab.add_song(song)

    def load_song(self, song: Song) -> None:
        tab = self.get_current_tab()
        if tab:
            tab.load_song(song)

    def remove_song_at(self, index: int) -> None:
        tab = self.get_current_tab()
        if tab:
            tab.remove_song_at(index)

    def update_song_info(self, index: int, song: Song) -> None:
        tab = self.get_current_tab()
        if tab:
            tab.update_song_info(index, song)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            tab = self.get_current_tab()
            if tab:
                tab.remove_selected_songs()
        super().keyPressEvent(event)
