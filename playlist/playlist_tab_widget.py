from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QTabWidget, QToolButton

from player_backends.Song import Song
from playlist.playlist import Playlist
from playlist.playlist_manager import PlaylistManager
from playlist.playlist_tab_bar import PlaylistTabBar
from playlist.playlist_tab_bar_edit import PlaylistTabBarEdit
from playlist.playlist_tree_view import PlaylistTreeView


class PlaylistTabWidget(QTabWidget):
    song_double_clicked = Signal(Song, int, Playlist)
    files_dropped = Signal(list, Playlist)
    tab_added = Signal()
    tab_deleted = Signal(int)
    # tab_renamed = Signal(str)

    def __init__(
        self,
        parent,
        playlist_manager: PlaylistManager,
        add_tab_button: bool = True,
    ) -> None:
        super().__init__(parent)

        self.playlist_manager = playlist_manager

        self.tab_bar = PlaylistTabBar(parent)
        self.tab_bar.tab_renamed.connect(self.on_tab_renamed)
        self.setTabBar(self.tab_bar)

        self.tabBarDoubleClicked.connect(self.doubleClicked)

        if add_tab_button:
            self.add_tab_button = QToolButton()
            self.add_tab_button.setText(" + ")
            self.add_tab_button.clicked.connect(lambda: self.tab_added.emit())

            self.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)

        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.on_tab_context_menu)

        self.delete_tab_action = QAction("Delete Playlist", self)
        self.tab_bar.addAction(self.delete_tab_action)
        self.delete_tab_action.triggered.connect(self.on_tab_context_menu)

        # Connect signals for tab management
        self.tabCloseRequested.connect(self.on_tab_close)

        # Connect the tabMoved signal to update the PlaylistManager
        self.tabBar().tabMoved.connect(self.on_tab_moved)

    @Slot()
    def on_tab_context_menu(self, position) -> None:
        tab_index = self.tab_bar.tabAt(position)
        if tab_index != -1:
            menu = QMenu(self)
            delete_action = menu.addAction("Delete Playlist")
            action = menu.exec_(self.tab_bar.mapToGlobal(position))
            if action == delete_action:
                self.tab_deleted.emit(tab_index)

    @Slot()
    def on_tab_moved(self, from_index: int, to_index: int) -> None:
        self.playlist_manager.reorder_playlists(from_index, to_index)

    def get_current_tab(self) -> PlaylistTreeView:
        return self.widget(self.currentIndex())  # type: ignore

    @Slot()
    def doubleClicked(self, index) -> None:
        tab_bar = self.tabBar()
        if isinstance(tab_bar, PlaylistTabBar):
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
    def on_song_double_clicked(self, song: Song, row: int, playlist: Playlist) -> None:
        self.song_double_clicked.emit(song, row, playlist)

    @Slot()
    def on_tab_close(self, index: int) -> None:
        self.playlist_manager.delete_playlist(index)
        self.removeTab(index)

    @Slot()
    def on_tab_renamed(self, new_name: str) -> None:
        index = self.tabBar().currentIndex()
        playlist_view = self.widget(index)
        if isinstance(playlist_view, PlaylistTreeView):
            playlist_view.playlist.name = new_name

    def update_tab_column_widths(self) -> None:
        for i in range(self.count()):
            playlist_view = self.widget(i)
            if isinstance(playlist_view, PlaylistTreeView):
                playlist_view.update_column_width()
