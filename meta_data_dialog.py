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
import json

def add_items(parent, data):
    if isinstance(data, dict):
        for key, value in data.items():
            item = QStandardItem(key)
            parent.appendRow(item)
            add_items(item, value)
    elif isinstance(data, list):
        for i, value in enumerate(data):
            item = QStandardItem(f"Item {i}")
            parent.appendRow(item)
            add_items(item, value)
    else:
        item = QStandardItem(str(data))
        parent.appendRow(item)

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
        self.tree.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.tree)
        self.setLayout(layout)

    def _add_tree_item(self, key, value):
        key_item = QStandardItem(key)
        value_item = QStandardItem(value)
        key_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        value_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.model.appendRow([key_item, value_item])

    def _on_double_click(self, index):
        if not index.isValid():
            return

        key_item = self.model.itemFromIndex(index.siblingAtColumn(0))
        credits_item = self.model.itemFromIndex(index.siblingAtColumn(1)).text()

        if key_item.text() == "credits":
            self._show_credits_dialog(credits_item)

    def _show_credits_dialog(self, credits_item):
        credits_dialog = QDialog(self)
        credits_dialog.setWindowTitle("Credits")
        credits_dialog.setGeometry(150, 150, 300, 200)
        layout = QVBoxLayout(credits_dialog)
        
        credits_dialog.setLayout(layout)
        credits_dialog.show()

        credits_data = json.loads(credits_item.replace("'", "\""))
        credits_model = QStandardItemModel()
        credits_model.setHorizontalHeaderLabels(["Credits"])

        root_item = credits_model.invisibleRootItem()
        add_items(root_item, credits_data)

        credits_tree = QTreeView(credits_dialog)
        credits_tree.setModel(credits_model)
        credits_tree.expandAll()
        credits_tree.resizeColumnToContents(0)

        layout.addWidget(credits_tree)