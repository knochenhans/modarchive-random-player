from PySide6.QtWidgets import QTabBar
from PySide6.QtCore import Slot

class PlaylistTabBar(QTabBar):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.edit_text = ""
        self.edit_index = 0
        self.setMovable(True)

    @Slot()
    def rename(self, text) -> None:
        self.edit_text = text

    @Slot()
    def editing_finished(self) -> None:
        self.setTabText(self.edit_index, self.edit_text)