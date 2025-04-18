from typing import Optional

from PySide6.QtCore import QModelIndex, QRect, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QBrush,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QPalette,
    QStandardItem,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QProxyStyle,
    QStyle,
    QStyleOption,
    QTreeView,
    QWidget,
)

from icons import Icons
from playlist.playlist_model import PlaylistModel
from settings.settings import Settings
from tree_view_columns import tree_view_columns_dict


class CustomItemViewStyle(QProxyStyle):
    def __init__(self, style=None):
        super().__init__(style)

    def drawPrimitive(self, element, option, painter, widget=None):
        if (
            element == QStyle.PrimitiveElement.PE_IndicatorItemViewItemDrop
            and not option.rect.isNull()  # type: ignore
        ):
            opt = QStyleOption(option)
            opt.rect.setLeft(0)  # type: ignore
            if widget:
                opt.rect.setRight(widget.width())  # type: ignore

            pen = painter.pen()
            pen.setWidth(3)
            painter.setPen(pen)

            super().drawPrimitive(element, opt, painter, widget)
            return
        super().drawPrimitive(element, option, painter, widget)


class PlaylistTreeView(QTreeView):
    item_double_clicked = Signal(int)
    files_dropped = Signal(list)
    rows_moved = Signal(list)

    def __init__(
        self, icons: Icons, settings: Settings, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.settings = settings
        self.icons = icons

        # Enable drag-and-drop reordering
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        # Apply custom style for the drop indicator
        self.setStyle(CustomItemViewStyle(self.style()))

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.doubleClicked.connect(self.on_item_double_clicked)

        model = PlaylistModel(self, 0)
        header_settings = self.settings.get("columns", [])
        column_names = [col["name"] for col in header_settings]
        model.setHorizontalHeaderLabels(column_names)

        self.setModel(model)

        self.model().rowsMoved.connect(self.on_rows_moved)

        self.dropIndicatorRect: QRect = QRect(0, 0, 0, 0)

        self.previous_row: int = 0

        # Add actions to the tree view
        self.add_context_menu_actions()

    def add_context_menu_actions(self):
        # Action to remove selected rows
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected_rows)
        self.addAction(remove_action)

        # Action to play the selected item
        play_action = QAction("Play", self)
        play_action.triggered.connect(self.play_selected_item)
        self.addAction(play_action)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.remove_selected_rows()
        else:
            super().keyPressEvent(event)

    def remove_selected_rows(self):
        selected_rows = self.get_selected_rows()
        for row in reversed(selected_rows):  # Reverse to avoid index shifting
            self.remove_row(row)

    def play_selected_item(self):
        index = self.currentIndex()
        if index.isValid():
            row = index.row()
            print(f"Playing item at row {row}")
            self.set_currently_playing_row(row)

    def setModel(self, model: PlaylistModel) -> None:
        super().setModel(model)
        self.playlist_model = model

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        self.item_double_clicked.emit(index.row())

    def set_playlist_data(self, data: list[dict]) -> None:
        self.playlist_model.removeRows(0, self.playlist_model.rowCount())
        for row_data in data:
            self.add_row(row_data)

    def get_playlist_data(self) -> list[dict]:
        data = []
        for row in range(self.playlist_model.rowCount()):
            row_data = self.get_row_data(row)
            if row_data:
                data.append(row_data)
        return data

    def add_row(self, row_data: dict) -> None:
        tree_cols = []
        for col_name, _ in tree_view_columns_dict.items():
            item = QStandardItem(row_data.get(col_name, ""))
            tree_cols.append(item)
        self.playlist_model.appendRow(tree_cols)

    def get_row_data(self, row: int) -> Optional[dict]:
        if row < self.playlist_model.rowCount():
            row_data = {}
            for column_id in tree_view_columns_dict:
                col_info = tree_view_columns_dict[column_id]
                col = col_info["order"]
                item = self.playlist_model.item(row, col)
                if item:
                    row_data[column_id] = item.text()
            return row_data
        return None

    def remove_row(self, row: int) -> None:
        self.playlist_model.removeRow(row)

    def get_selected_rows(self) -> list[int]:
        return sorted(set(index.row() for index in self.selectedIndexes()))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        super().dropEvent(event)

    def _set_play_status(self, row: int, enable: bool) -> None:
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

    def set_currently_playing_row(self, row: int) -> None:
        self._set_play_status(self.previous_row, False)
        self._set_play_status(row, True)
        self.previous_row = row

    def get_current_item(self) -> Optional[QStandardItem]:
        index = self.currentIndex()
        if index.isValid():
            return self.playlist_model.itemFromIndex(index)
        return None

    def get_column_widths(self) -> list[int]:
        column_widths = []
        for i in range(self.playlist_model.columnCount()):
            column_widths.append(self.columnWidth(i))
        return column_widths

    def set_column_widths(self, widths: list[int]) -> None:
        for i, width in enumerate(widths):
            self.setColumnWidth(i, width)

    def on_rows_moved(
        self,
        parent: QModelIndex,
        start: int,
        end: int,
        destination: QModelIndex,
        row: int,
    ) -> None:

        # Emit the new order of rows
        new_order = [
            self.model().index(i, 0).row() for i in range(self.model().rowCount())
        ]
        self.rows_moved.emit(new_order)
