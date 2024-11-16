from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QStandardItemModel
from PySide6.QtWidgets import QTreeView, QStyleOption, QAbstractItemView


from player_backends.Song import Song

class PlaylistTreeView(QTreeView):
    item_double_clicked = Signal(Song)

    def __init__(self, parent=None) -> None:
        super(PlaylistTreeView, self).__init__(parent)
        self.dropIndicatorRect = QRect()

        # Currently playing row for this tab
        self.current_row: int = 0

        self.setDragDropMode(self.DragDropMode.InternalMove)
        self.setSelectionMode(self.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
        self.setEditTriggers(self.EditTrigger.NoEditTriggers)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Hide left-hand space from hidden expand sign
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)

        self.doubleClicked.connect(self.on_item_double_clicked)

    def on_item_double_clicked(self, item):
        row = item.row()
        model = self.model()
        if isinstance(model, QStandardItemModel):
            song = model.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.item_double_clicked.emit(song)

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        self.drawTree(painter, event.region())
        self.paintDropIndicator(painter)
        painter.end()

    def paintDropIndicator(self, painter):
        if self.state() == QAbstractItemView.State.DraggingState:
            opt = QStyleOption()
            opt.initFrom(self)
            opt.rect = self.dropIndicatorRect
            rect = opt.rect

            brush = QBrush(QColor(Qt.GlobalColor.black))

            if rect.height() == 0:
                pen = QPen(brush, 2, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawLine(rect.topLeft(), rect.topRight())
            else:
                pen = QPen(brush, 2, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawRect(rect)