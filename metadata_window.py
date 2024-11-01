from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QDialog

from player_backends.player_backend import SongMetadata


class MetadataWindow(QDialog):
    def __init__(self, song_metadata: SongMetadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Song Metadata")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Key", "Value"])

        # Calculate the number of rows needed
        num_rows = len(song_metadata)
        if "credits" in song_metadata:
            num_rows += (
                len(song_metadata["credits"]) - 1
            )  # Subtract 1 because 'credits' key itself is already counted

        self.table.setRowCount(num_rows)

        row = 0
        for key, credit_value in song_metadata.items():
            if key == "credits":
                if isinstance(credit_value, dict):
                    for credit, credit_value in credit_value.items():
                        self.table.setItem(
                            row, 0, QTableWidgetItem("Credits: " + str(credit))
                        )
                        self.table.setItem(row, 1, QTableWidgetItem(str(credit_value)))
                        row += 1

                        if credit == "instruments":
                            if isinstance(credit_value, list):
                                for instrument in credit_value:
                                    if isinstance(instrument, dict):
                                        for (
                                            instrument_key,
                                            instrument_value,
                                        ) in instrument.items():
                                            self.table.setItem(
                                                row,
                                                0,
                                                QTableWidgetItem(str(instrument_key)),
                                            )
                                            self.table.setItem(
                                                row,
                                                1,
                                                QTableWidgetItem(str(instrument_value)),
                                            )
                                            row += 1
            else:
                self.table.setItem(row, 0, QTableWidgetItem(str(key)))
                self.table.setItem(row, 1, QTableWidgetItem(str(credit_value)))
                row += 1

        self.table.resizeColumnsToContents()

        layout.addWidget(self.table)
        self.setLayout(layout)
