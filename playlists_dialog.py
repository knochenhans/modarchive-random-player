import ntpath
from PySide6.QtCore import QRect, Qt, Slot, Signal
from PySide6.QtGui import QKeyEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QToolButton,
    QTreeView,
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QTabBar,
    QLineEdit,
)

from playlist import Playlist
from datetime import timedelta
from player_backends.Song import Song
from playlist_manager import PlaylistManager
from typing import TypedDict


class TreeViewColumn(TypedDict):
    name: str
    width: int
    order: int


tree_view_columns: dict[str, TreeViewColumn] = {
    "playing": {"name": "", "width": 20, "order": 0},
    "filename": {"name": "Filename", "width": 150, "order": 2},
    "title": {"name": "Title", "width": 150, "order": 1},
    "duration": {"name": "Duration", "width": 100, "order": 3},
    "backend": {"name": "Backend", "width": 100, "order": 4},
    "path": {"name": "Path", "width": 200, "order": 5},
    "subsong": {"name": "Subsong", "width": 50, "order": 6},
    "artist": {"name": "Artist", "width": 150, "order": 7},
}


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

    def __init__(self, playlist_manager: PlaylistManager, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Playlists")
        self.setGeometry(100, 100, 600, 400)

        self.tab_widget = PlaylistTab(self)
        self.tab_widget.song_double_clicked.connect(self.on_song_double_clicked)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)

        self.setLayout(self.main_layout)

        for playlist in playlist_manager.playlists:
            self.add_playlist(playlist)

        self.show()

    def add_playlist(self, playlist: Playlist) -> None:
        self.tab_widget.add_tab(playlist.name)
        for song in playlist.songs:
            self.tab_widget.add_song(song)

    def on_song_double_clicked(self, song: Song) -> None:
        self.song_on_tab_double_clicked.emit(song)


class PlaylistItem(QStandardItem):
    def __init__(self):
        super().__init__()

    def flags(self, index):
        return Qt.ItemFlag.NoItemFlags


class PlaylistTreeView(QTreeView):
    item_double_clicked = Signal(Song)

    def __init__(self, parent=None) -> None:
        super(PlaylistTreeView, self).__init__(parent)
        self.dropIndicatorRect = QRect()

        # Currently playing row for this tab
        self.current_row: int = 0

        self.setDragDropMode(self.DragDropMode.InternalMove)
        self.setSelectionMode(self.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
        self.setEditTriggers(self.EditTrigger.NoEditTriggers)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Hide left-hand space from hidden expand sign
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)

        self.doubleClicked.connect(self.on_item_double_clicked)

    def on_item_double_clicked(self, item):
        row = item.row()
        model = self.model()
        if isinstance(model, QStandardItemModel):
            song = model.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.item_double_clicked.emit(song)


class PlaylistTabBarEdit(QLineEdit):
    def __init__(self, parent, rect: QRect) -> None:
        super().__init__(parent)

        self.setGeometry(rect)
        self.textChanged.connect(parent.tabBar().rename)
        self.editingFinished.connect(parent.tabBar().editing_finished)
        self.returnPressed.connect(self.close)

    def focusOutEvent(self, event):
        parent = self.parent()

        if isinstance(parent, PlaylistTab):
            tab_bar = parent.tabBar()

            if isinstance(tab_bar, PlaylistTabBar):
                tab_bar.editing_finished()
                self.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

        super().keyPressEvent(event)


class PlaylistTabBar(QTabBar):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.edit_text = ""
        self.edit_index = 0
        self.setMovable(True)

    @Slot()
    def rename(self, text) -> None:
        self.edit_text = text

    @Slot()
    def editing_finished(self) -> None:
        self.setTabText(self.edit_index, self.edit_text)


class PlaylistTab(QTabWidget):
    song_double_clicked = Signal(Song)

    def __init__(self, parent) -> None:
        super().__init__(parent)

        tab_bar = PlaylistTabBar(parent)
        self.setTabBar(tab_bar)

        self.tabBarDoubleClicked.connect(self.doubleClicked)

        self.add_tab_button = QToolButton()
        self.add_tab_button.setText(" + ")
        self.add_tab_button.clicked.connect(self.on_add_tab_button_clicked)

        self.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)

    @Slot()
    def on_add_tab_button_clicked(self) -> None:
        self.add_tab()

    def add_song(self, song: Song, tab=None) -> None:
        tree_cols: list[PlaylistItem] = []

        duration = timedelta(seconds=song.duration)

        items = tree_view_columns.items()
        sorted_items = sorted(items, key=lambda x: x[1]["order"])

        for col_name, col_info in sorted_items:
            item = PlaylistItem()

            if col_name == "playing":
                item.setText("")
            elif col_name == "filename":
                item.setText(ntpath.basename(song.filename))
            elif col_name == "title":
                item.setText(song.title)
            elif col_name == "duration":
                item.setText(str(duration).split(".")[0])
            elif col_name == "backend":
                item.setText(song.backend_name)
            elif col_name == "path":
                item.setText(song.filename)
            elif col_name == "artist":
                item.setText(song.artist)

            if col_info["order"] == 0:
                item.setData(song, Qt.ItemDataRole.UserRole)

            tree_cols.append(item)

        if not tab:
            tab = self.get_current_tab()

        if isinstance(tab, PlaylistTreeView):
            model = tab.model()
            if isinstance(model, PlaylistModel):
                model.appendRow(tree_cols)

                # Set column width
                for col_name, col_info in tree_view_columns.items():
                    width = col_info["width"]

                    tab.setColumnWidth(col_info["order"], width)

    def update_song(self, song: Song, tab=None) -> None:
        if not tab:
            tab = self.get_current_tab()

        if isinstance(tab, PlaylistTreeView):
            model = tab.model()
            if isinstance(model, PlaylistModel):
                for row in range(model.rowCount()):
                    item = model.item(row, 0)
                    current_song = Song(item.data(Qt.ItemDataRole.UserRole))
                    if current_song.uid == song.uid:
                        self.remove_song(row, tab)
                        self.add_song(song, tab)
                        break

    def remove_song(self, row: int, tab=None) -> None:
        if not tab:
            tab = self.get_current_tab()

        if isinstance(tab, PlaylistTreeView):
            model = tab.model()
            if isinstance(model, PlaylistModel):
                model.removeRow(row)

    def get_current_tab(self):
        return self.widget(self.currentIndex())

    @Slot()
    def doubleClicked(self, index) -> None:
        tab_bar = self.tabBar()
        if isinstance(tab_bar, PlaylistTabBar):
            tab_bar.edit_index = index
        edit = PlaylistTabBarEdit(self, self.tabBar().tabRect(index))
        edit.show()
        edit.setFocus()

    @Slot()
    def on_song_double_clicked(self, song: Song) -> None:
        self.song_double_clicked.emit(song)

    def add_tab(self, name: str = "New Playlist") -> None:
        tree = PlaylistTreeView(self)
        model = PlaylistModel(0, 3)

        tree.item_double_clicked.connect(self.on_song_double_clicked)

        items = tree_view_columns.items()
        sorted_items = sorted(items, key=lambda x: x[1]["order"])
        labels = [str(col_info["name"]) for _, col_info in sorted_items]
        model.setHorizontalHeaderLabels(labels)

        tree.setModel(model)

        self.addTab(tree, name)

    def remove_current_tab(self):
        self.removeTab(self.currentIndex())


class PlaylistModel(QStandardItemModel):
    def __init__(self, parent, length):
        super().__init__(parent, length)

    def flags(self, index):
        default_flags = super().flags(index)

        if index.isValid():
            return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsDragEnabled
            )

        return default_flags

    def dropMimeData(self, data, action, row, col, parent):
        # Prevent shifting colums
        response = super().dropMimeData(data, Qt.DropAction.CopyAction, row, 0, parent)
        return response
