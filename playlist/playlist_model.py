from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel


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

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction
