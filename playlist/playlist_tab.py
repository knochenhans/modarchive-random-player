from datetime import timedelta
import ntpath
from player_backends.Song import Song
from playlist.playlist_item import PlaylistItem
from playlist.playlist_model import PlaylistModel
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QTabWidget, QToolButton

from playlist.playlist_tab_bar import PlaylistTabBar
from playlist.playlist_tab_bar_edit import PlaylistTabBarEdit
from playlist.playlist_tree_view import PlaylistTreeView
from tree_view_columns import tree_view_columns_dict


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

        items = tree_view_columns_dict.items()
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
                for col_name, col_info in tree_view_columns_dict.items():
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

        items = tree_view_columns_dict.items()
        sorted_items = sorted(items, key=lambda x: x[1]["order"])
        labels = [str(col_info["name"]) for _, col_info in sorted_items]
        model.setHorizontalHeaderLabels(labels)

        tree.setModel(model)

        self.addTab(tree, name)

    def remove_current_tab(self):
        self.removeTab(self.currentIndex())