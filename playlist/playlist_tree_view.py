from datetime import timedelta
import ntpath
from typing import Optional
from PySide6.QtCore import Qt, QRect, Signal, QEvent
from PySide6.QtGui import (
    QPainter,
    QBrush,
    QColor,
    QPen,
    QStandardItem,
    QIcon,
    QPalette,
    QDropEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QStandardItem,
)
from PySide6.QtWidgets import (
    QTreeView,
    QStyleOption,
    QAbstractItemView,
    QWidget,
    QTreeView,
)

from icons import Icons
from player_backends.Song import Song
from playlist.playlist import Playlist
from playlist.playlist_item import PlaylistItem
from playlist.playlist_model import PlaylistModel
from tree_view_columns import TreeViewColumn, tree_view_columns_dict


class PlaylistTreeView(QTreeView):
    item_double_clicked = Signal(Song, int, Playlist)
    files_dropped = Signal(list)

    def __init__(self, playlist: Playlist, parent: Optional[QWidget] = None) -> None:
        super(PlaylistTreeView, self).__init__(parent)
        self.dropIndicatorRect: QRect = QRect()

        self.playlist = playlist
        self.playlist.current_song_changed.connect(self.set_current_song)

        # Currently playing row for this tab
        self.previous_row: int = 0

        self.setDragDropMode(self.DragDropMode.InternalMove)
        self.setSelectionMode(self.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
        self.setEditTriggers(self.EditTrigger.NoEditTriggers)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.setAcceptDrops(True)

        # Hide left-hand space from hidden expand sign
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)

        self.doubleClicked.connect(self.on_item_double_clicked)

        self.icons = Icons()

    def setModel(self, model: PlaylistModel) -> None:
        super().setModel(model)
        self.playlist_model = model

    def on_item_double_clicked(self, item: QStandardItem) -> None:
        row: int = item.row()
        model = self.model()
        if isinstance(model, PlaylistModel):
            song: Song = model.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.item_double_clicked.emit(song, row, self.playlist)

    def paintEvent(self, event: QEvent) -> None:
        painter: QPainter = QPainter(self.viewport())
        self.drawTree(painter, event.region())
        self.paintDropIndicator(painter)
        painter.end()

    def paintDropIndicator(self, painter: QPainter) -> None:
        if self.state() == QAbstractItemView.State.DraggingState:
            opt: QStyleOption = QStyleOption()
            opt.initFrom(self)
            opt.rect = self.dropIndicatorRect
            rect: QRect = opt.rect

            brush: QBrush = QBrush(QColor(Qt.GlobalColor.black))

            if rect.height() == 0:
                pen: QPen = QPen(brush, 2, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawLine(rect.topLeft(), rect.topRight())
            else:
                pen: QPen = QPen(brush, 2, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawRect(rect)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()

    def load_song(self, song: Song) -> int:
        index = self.add_song(song)
        self.playlist.on_song_added(song)
        return index

    def construct_item(
        self, song: Song, col_name: str, col_info: TreeViewColumn
    ) -> PlaylistItem:
        item = PlaylistItem()

        match col_name:
            case "playing":
                item.setText("")
            case "filename":
                item.setText(ntpath.basename(song.filename))
            case "title":
                item.setText(song.title)
            case "duration":
                duration = timedelta(seconds=song.duration)
                item.setText(str(duration).split(".")[0])
            case "backend":
                item.setText(song.backend_name)
            case "path":
                item.setText(song.filename)
            case "artist":
                item.setText(song.artist)
            case "player":
                item.setText(song.playername)
            case "subsongs":
                item.setText(str(song.subsongs))

        if col_info["order"] == 0:
            item.setData(song, Qt.ItemDataRole.UserRole)

        return item

    def construct_tree_cols(self, song: Song) -> list[PlaylistItem]:
        tree_cols: list[PlaylistItem] = []

        items = tree_view_columns_dict.items()
        sorted_items = sorted(items, key=lambda x: x[1]["order"])

        for col_name, col_info in sorted_items:
            item = self.construct_item(song, col_name, col_info)
            tree_cols.append(item)

        return tree_cols

    def add_song(self, song: Song) -> int:
        tree_cols = self.construct_tree_cols(song)
        self.playlist_model.appendRow(tree_cols)
        return self.playlist_model.indexFromItem(tree_cols[0]).row()

    def remove_song(self, song: Song) -> None:
        for row in range(self.playlist_model.rowCount()):
            item = self.playlist_model.item(row, 0)
            current_song: Song = item.data(Qt.ItemDataRole.UserRole)
            if current_song.uid == song.uid:
                self.remove_song_at(row)
                break

    def update_song(self, song: Song) -> None:
        for row in range(self.playlist_model.rowCount()):
            item = self.playlist_model.item(row, 0)
            current_song: Song = item.data(Qt.ItemDataRole.UserRole)
            if current_song.uid == song.uid:
                item.setData(song, Qt.ItemDataRole.UserRole)
                # self.remove_song_at(row)
                # self.add_song(song)
                break

    def remove_song_at(self, row: int) -> None:
        self.playlist_model.removeRow(row)
        self.playlist.on_song_removed_at(row)

    def move_song(self, from_row: int, to_row: int) -> None:
        self.playlist_model.moveRow(
            self.playlist_model.index(from_row, 0),
            to_row,
            self.playlist_model.index(from_row, 0),
            to_row,
        )

    def find_song_row(self, song: Song) -> int:
        for row in range(self.playlist_model.rowCount()):
            item = self.playlist_model.item(row, 0)
            current_song: Song = item.data(Qt.ItemDataRole.UserRole)
            if current_song.uid == song.uid:
                return row
        return -1

    def update_song_info(self, row: int, song: Song) -> None:
        song_row = self.find_song_row(song)

        if song_row != -1:
            tree_cols = self.construct_tree_cols(song)

            for col_index, item in enumerate(tree_cols):
                self.playlist_model.setItem(song_row, col_index, item)

    def set_play_status(self, row: int, enable: bool) -> None:
        column = self.playlist_model.itemFromIndex(self.model().index(row, 0))

        if column:
            color = column.foreground().color()

            if enable:
                column.setData(
                    self.icons.pixmap_icons["play"], Qt.ItemDataRole.DecorationRole
                )
                color.setRgb(255 - color.red(), 255 - color.green(), 255 - color.blue())
            else:
                column.setData(QIcon(), Qt.ItemDataRole.DecorationRole)

                default_color = self.palette().color(QPalette.ColorRole.Text)
                color.setRgb(
                    default_color.red(), default_color.green(), default_color.blue()
                )

            column.setForeground(QBrush(color))

    def set_current_row(self, row: int) -> None:
        self.set_play_status(self.previous_row, False)
        self.set_play_status(row, True)
        self.previous_row = row

    def update_current_row(self) -> None:
        self.set_current_row(self.playlist.current_song_index)

    def set_current_song(self, song: Song, index: int) -> None:
        for row in range(self.playlist_model.rowCount()):
            item = self.playlist_model.item(row, 0)
            current_song: Song = item.data(Qt.ItemDataRole.UserRole)
            if current_song.uid == song.uid:
                self.set_current_row(row)
                break

    def set_playlist(self, playlist: Playlist) -> None:
        self.playlist = playlist
        self.playlist_model.clear()
        for song in playlist.songs:
            self.add_song(song)

        # Set column names and widths
        for col_info in tree_view_columns_dict.values():
            name = col_info["name"]
            self.playlist_model.setHorizontalHeaderItem(
                col_info["order"], QStandardItem(name)
            )

            width = col_info["width"]
            self.setColumnWidth(col_info["order"], width)

    def get_current_item(self) -> Optional[QStandardItem]:
        index = self.currentIndex()
        if index.isValid():
            return self.playlist_model.itemFromIndex(index)
        return None

    def remove_selected_songs(self) -> None:
        rows = sorted(
            set(index.row() for index in self.selectedIndexes()), reverse=True
        )
        for row in rows:
            self.remove_song_at(row)

    def set_name(self, name: str) -> None:
        self.playlist.name = name
        # self.playlist_model.setHorizontalHeaderItem(0, QStandardItem(name))
        # self.playlist_model.setHeaderData(0, Qt.Orientation.Horizontal, name)
