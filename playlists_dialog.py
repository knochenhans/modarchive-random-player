import ntpath
from PySide6.QtCore import QRect, Qt, Slot
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


class TREEVIEWCOL:
    PLAYING = 0
    FILENAME = 1
    TITLE = 2
    DURATION = 3
    BACKEND = 4
    PATH = 5
    SUBSONG = 6
    ARTIST = 7


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
    def __init__(self, playlist_manager: PlaylistManager, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Playlists")
        self.setGeometry(100, 100, 600, 400)

        self.tab_widget = PlaylistTab(self)

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


class PlaylistItem(QStandardItem):
    def __init__(self):
        super().__init__()

    def flags(self, index):
        return Qt.ItemFlag.NoItemFlags

    # def dropEvent(self):
    #     print('test')

    # def dragEnterEvent(self):
    #     pass


class PlaylistTreeView(QTreeView):
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

        self.setColumnWidth(0, 20)

        # Hide left-hand space from hidden expand sign
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)

    # def model(self) -> QAbstractItemModel:
    #     return super().model()


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

        # self.tabBarDoubleClicked.connect(self.doubleClicked)

    @Slot()
    def rename(self, text) -> None:
        self.edit_text = text

    @Slot()
    def editing_finished(self) -> None:
        self.setTabText(self.edit_index, self.edit_text)

    # @ Slot()
    # def doubleClicked(self, index) -> None:
    #     print("test")


class PlaylistTab(QTabWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        tab_bar = PlaylistTabBar(parent)
        self.setTabBar(tab_bar)

        self.tabBarDoubleClicked.connect(self.doubleClicked)
        # self.tabBarDoubleClicked.connect(self.tabBarDoubleClicked)

        self.add_tab_button = QToolButton()
        self.add_tab_button.setText(" + ")
        self.add_tab_button.clicked.connect(self.on_add_tab_button_clicked)

        self.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)

    @Slot()
    def on_add_tab_button_clicked(self) -> None:
        self.add_tab()

    def add_song(self, song: Song, tab=None) -> None:
        tree_cols: list[PlaylistItem] = []

        # if hasattr(song, "subsong"):
        #     duration = timedelta(seconds=song.subsong.bytes / 176400)
        #     subsong_nr = song.subsong.nr
        # else:
        duration = timedelta(seconds=song.duration)
        # subsong_nr = 1

        for col in range(len(TREEVIEWCOL.__dict__.keys()) - 3):
            item = PlaylistItem()

            if col == TREEVIEWCOL.PLAYING:
                item.setText("")
            elif col == TREEVIEWCOL.FILENAME:
                item.setText(ntpath.basename(song.filename))
            elif col == TREEVIEWCOL.TITLE:
                item.setText(song.title)
            elif col == TREEVIEWCOL.DURATION:
                item.setText(str(duration).split(".")[0])
            elif col == TREEVIEWCOL.BACKEND:
                item.setText(song.backend_name)
            elif col == TREEVIEWCOL.PATH:
                item.setText(song.filename)
            # elif col == TREEVIEWCOL.SUBSONG:
            #     item.setText(str(subsong_nr))
            elif col == TREEVIEWCOL.ARTIST:
                item.setText(song.artist)

            if col == 0:
                item.setData(song, Qt.ItemDataRole.UserRole)

            tree_cols.append(item)

        if not tab:
            tab = self.get_current_tab()

        if isinstance(tab, PlaylistTreeView):
            model = tab.model()
            if isinstance(model, PlaylistModel):
                model.appendRow(tree_cols)

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

    # def tabBarDoubleClicked(self, index):
    #     print('blabla')

    def add_tab(self, name: str = "New Playlist") -> None:
        tree = PlaylistTreeView(self)
        model = PlaylistModel(0, 3)

        labels = [""] * len(TREEVIEWCOL.__dict__.keys())
        for key in TREEVIEWCOL.__dict__.keys():
            if not key.startswith("__"):
                labels[getattr(TREEVIEWCOL, key)] = key.capitalize()
        model.setHorizontalHeaderLabels(labels)

        tree.setModel(model)

        # tree.doubleClicked.connect(self.item_double_clicked)
        # tree.customContextMenuRequested.connect(self.open_context_menu)

        self.addTab(tree, name)

    def remove_current_tab(self):
        self.removeTab(self.currentIndex())

    # def widget(self, index: int) -> PlaylistTreeView:
    #     return self.widget()


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
