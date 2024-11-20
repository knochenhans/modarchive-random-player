from typing import Optional
from player_backends.Song import Song
from playlist.playlist import Playlist
from playlist.playlist_model import PlaylistModel
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QTabWidget, QToolButton

from playlist.playlist_tab_bar import PlaylistTabBar
from playlist.playlist_tab_bar_edit import PlaylistTabBarEdit
from playlist.playlist_tree_view import PlaylistTreeView
from tree_view_columns import tree_view_columns_dict


class PlaylistTabWidget(QTabWidget):
    song_double_clicked = Signal(Song, int)
    new_tab_added = Signal(str)
    tab_renamed = Signal(str)

    def __init__(self, parent, add_tab_button: bool = True) -> None:
        super().__init__(parent)

        tab_bar = PlaylistTabBar(parent)
        self.setTabBar(tab_bar)

        self.tabBarDoubleClicked.connect(self.doubleClicked)

        if add_tab_button:
            self.add_tab_button = QToolButton()
            self.add_tab_button.setText(" + ")
            self.add_tab_button.clicked.connect(self.on_add_tab_button_clicked)

            self.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)

    @Slot()
    def on_add_tab_button_clicked(self) -> None:
        self.add_tab()

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
        self.tab_renamed.emit(text)

    @Slot()
    def on_song_double_clicked(self, song: Song, row: int) -> None:
        self.song_double_clicked.emit(song, row)

    def add_tab(self, playlist: Optional[Playlist]) -> PlaylistTreeView:
        if not playlist:
            playlist = Playlist("New Playlist")

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
        return tree

    def remove_current_tab(self):
        self.removeTab(self.currentIndex())

    def add_song(self, song: Song) -> None:
        tab = self.get_current_tab()
        if tab:
            tab.add_song(song)

    def remove_song_at(self, index: int) -> None:
        tab = self.get_current_tab()
        if tab:
            tab.remove_song_at(index)

    def get_songs_from(self, index: int) -> list[Song]:
        tab = self.get_current_tab()
        if tab:
            return tab.get_songs_from(index)
        return []
