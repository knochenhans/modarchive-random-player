from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTreeView,
)
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
)
from PySide6.QtCore import Qt

from player_backends.player_backend import Song
import inspect


class MetaDataDialog(QDialog):
    def __init__(self, song: Song, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Metadata for {song.title}")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(self)
        self.tree = QTreeView(self)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Attribute", "Value"])

        song_attributes = inspect.getmembers(song, lambda a: not (inspect.isroutine(a)))
        song_attributes = [
            a
            for a in song_attributes
            if not (a[0].startswith("__") and a[0].endswith("__"))
        ]

        for key, value in song_attributes:
            self._add_tree_item(key, str(value))

        self.tree.setModel(self.model)
        self.tree.expandAll()
        self.tree.resizeColumnToContents(0)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setVerticalScrollMode(QTreeView.ScrollMode.ScrollPerPixel)

        layout.addWidget(self.tree)
        self.setLayout(layout)

    def _add_tree_item(self, key, value):
        key_item = QStandardItem(key)
        value_item = QStandardItem(value)
        key_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        value_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.model.appendRow([key_item, value_item])
