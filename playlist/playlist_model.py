from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel


class PlaylistModel(QStandardItemModel):
    def __init__(self, parent, length) -> None:
        super().__init__(parent, length)

    def flags(self, index) -> Qt.ItemFlag:
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

    def mimeTypes(self) -> list[str]:
        return ["application/x-qstandarditemmodeldatalist"]

    def moveRows(
        self,
        sourceParent: QModelIndex,
        sourceRow: int,
        count: int,
        destinationParent: QModelIndex,
        destinationChild: int,
    ) -> bool:
        if sourceRow == destinationChild or sourceRow + count == destinationChild:
            return False  # Prevent moving rows to the same position

        self.beginMoveRows(
            sourceParent,
            sourceRow,
            sourceRow + count - 1,
            destinationParent,
            destinationChild,
        )

        # Perform the row move
        rows = [self.takeRow(sourceRow) for _ in range(count)]
        for i, row in enumerate(rows):
            self.insertRow(destinationChild + i, row)

        self.endMoveRows()
        return True
