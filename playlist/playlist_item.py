from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem

class PlaylistItem(QStandardItem):
    def __init__(self):
        super().__init__()

    def flags(self, index):
        return Qt.ItemFlag.NoItemFlags