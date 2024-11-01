from PySide6.QtWidgets import QMainWindow, QListWidget, QWidget, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot

from player_backends.player_backend import SongMetadata


class HistoryWindow(QMainWindow):
    def __init__(self, history: list[SongMetadata]) -> None:
        super().__init__()
        self.setWindowTitle("Recent modules")
        self.setWindowIcon(QIcon("icon.png"))

        self.history = history

        self.setup_ui()

    def setup_ui(self) -> None:
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.play_module)

        for song in self.history:
            title = song.get("title", "Unknown")
            artist = song.get("artist", "Unknown")
            self.history_list.addItem(f"{artist} - {title}")

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.history_list)
        container.setLayout(layout)
        self.setCentralWidget(container)

    @Slot()
    def play_module(self) -> None:
        index = self.history_list.currentRow()
        song = self.history[index]

        parent = self.parentWidget()

        from main_window import MainWindow
        if isinstance(parent, MainWindow):
            parent.song_metadata = song
            parent.load_and_play_module()
            self.close()
