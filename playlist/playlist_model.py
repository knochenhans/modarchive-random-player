from typing import List

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel


class PlaylistModel(QStandardItemModel):
    def __init__(self, parent) -> None:
        super().__init__(parent, 0)

        # self.set_column_names()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.ItemIsDropEnabled
        else:
            return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsDragEnabled
            )

    def dropMimeData(self, data, action, row, col, parent) -> bool:
        if action == Qt.DropAction.IgnoreAction:
            return False

        if action == Qt.DropAction.MoveAction:
            if action == Qt.DropAction.IgnoreAction:
                return False

        if action == Qt.DropAction.MoveAction:
            # Prevent shifting columns
            return super().dropMimeData(data, Qt.DropAction.CopyAction, row, 0, parent)

        return False

    def supportedDragActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def mimeTypes(self) -> List[str]:
        return ["application/x-qstandarditemmodeldatalist"]

    def set_column_names(self, column_names: List[str]) -> None:
        self.setHorizontalHeaderLabels(column_names)
