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
)
from PySide6.QtWidgets import (
    QTreeView,
    QStyleOption,
    QAbstractItemView,
    QWidget,
    QStyle,
    QTreeView,
)

from player_backends.Song import Song
from playlist.playlist import Playlist
from playlist.playlist_item import PlaylistItem
from playlist.playlist_model import PlaylistModel
from tree_view_columns import tree_view_columns_dict


class PlaylistTreeView(QTreeView):
    item_double_clicked = Signal(Song, int)

    def __init__(self, playlist: Playlist, parent: Optional[QWidget] = None) -> None:
        super(PlaylistTreeView, self).__init__(parent)
        self.dropIndicatorRect: QRect = QRect()

        self.playlist = playlist

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

        self.icons = {}
        self.icons["play"] = self.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaPlay
        )

    def setModel(self, model: PlaylistModel) -> None:
        super().setModel(model)
        self.playlist_model = model

    def on_item_double_clicked(self, item: QStandardItem) -> None:
        row: int = item.row()
        model = self.model()
        if isinstance(model, PlaylistModel):
            song: Song = model.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.item_double_clicked.emit(song, row)

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

    def add_song(self, song: Song) -> None:
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

        self.playlist_model.appendRow(tree_cols)

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
                self.remove_song_at(row)
                self.add_song(song)
                break

    def remove_song_at(self, row: int, tab=None) -> None:
        self.playlist_model.removeRow(row)

    def move_song(self, from_row: int, to_row: int) -> None:
        self.playlist_model.moveRow(
            self.playlist_model.index(from_row, 0),
            to_row,
            self.playlist_model.index(from_row, 0),
            to_row,
        )

    def update_song_info(self, song: Song, tab=None) -> None:
        for row in range(self.playlist_model.rowCount()):
            item = self.playlist_model.item(row, 0)

            if item.data(Qt.ItemDataRole.UserRole).uid == song.uid:
                item.setData(song, Qt.ItemDataRole.UserRole)

    def set_play_status(self, row: int, enable: bool) -> None:
        col = self.playlist_model.itemFromIndex(self.model().index(row, 0))

        if enable:
            col.setData(self.icons["play"], Qt.ItemDataRole.DecorationRole)
        else:
            col.setData(QIcon(), Qt.ItemDataRole.DecorationRole)

    def set_current_row(self, row: int) -> None:
        self.set_play_status(self.current_row, False)
        self.set_play_status(row, True)
        self.current_row = row

    def get_songs_from(self, starting_from: int = 0) -> list[Song]:
        songs = []
        for row in range(starting_from, self.playlist_model.rowCount()):
            item = self.playlist_model.item(row, 0)
            song: Song = item.data(Qt.ItemDataRole.UserRole)
            songs.append(song)

        return songs

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
