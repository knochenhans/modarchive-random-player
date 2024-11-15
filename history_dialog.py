from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, Slot, Signal

from player_backends.Song import Song


class HistoryDialog(QDialog):
    entry_double_clicked = Signal(Song)

    def __init__(self, history: list[Song], parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Title", "Filename", "Backend"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setRowCount(len(history))
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        for row, song in enumerate(history):
            self._add_table_item(row, 0, song.title)
            self._add_table_item(row, 1, song.filename)
            self._add_table_item(row, 2, song.backend_name)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def _add_table_item(self, row, column, text):
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, column, item)

    @Slot()
    def on_new_entry(self, song: Song):
        row = self.table.rowCount()
        self.table.setRowCount(row + 1)
        self._add_table_item(row, 0, song.title)
        self._add_table_item(row, 1, song.filename)
        self._add_table_item(row, 2, song.backend_name)
        self.table.scrollToBottom()
        self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, song)

    @Slot()
    def _on_item_double_clicked(self, item):
        row = item.row()
        song = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.entry_double_clicked.emit(song)
