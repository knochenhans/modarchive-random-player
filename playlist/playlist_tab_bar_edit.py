from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QKeyEvent



class PlaylistTabBarEdit(QLineEdit):
    def __init__(self, parent, rect: QRect) -> None:
        super().__init__(parent)

        self.setGeometry(rect)
        self.textChanged.connect(parent.tabBar().rename)
        self.editingFinished.connect(parent.tabBar().editing_finished)
        self.returnPressed.connect(self.close)

    def focusOutEvent(self, event):
        parent = self.parent()

        from playlist.playlist_tab_widget import PlaylistTabWidget
        if isinstance(parent, PlaylistTabWidget):
            tab_bar = parent.tabBar()

            from playlist.playlist_tab_bar import PlaylistTabBar
            if isinstance(tab_bar, PlaylistTabBar):
                tab_bar.editing_finished()
                self.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

        super().keyPressEvent(event)
