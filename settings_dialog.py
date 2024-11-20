from PySide6.QtCore import QSettings, Slot
from PySide6.QtGui import QIntValidator
from typing import Optional, Any
from PySide6.QtWidgets import QWidget

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
)


class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.settings: QSettings = settings
        self.setWindowTitle("Settings")

        self.member_id_label: QLabel = QLabel("Member ID:")
        self.member_id_input: QLineEdit = QLineEdit()
        self.member_id_input.setPlaceholderText("Member ID")
        self.member_id_input.setValidator(QIntValidator())

        # Load the member input data from settings
        member_id: str = str(self.settings.value("member_id", ""))
        if member_id:
            self.member_id_input.setText(member_id)

        # Save the member input data when it changes
        self.member_id_input.textChanged.connect(self.save_member_input)

        # Add dark/light theme option
        self.theme_checkbox: QCheckBox = QCheckBox("Enable Dark Theme")
        theme_enabled: bool = bool(self.settings.value("dark_theme", False))
        self.theme_checkbox.setChecked(theme_enabled)
        self.theme_checkbox.stateChanged.connect(self.save_theme_preference)

        layout: QVBoxLayout = QVBoxLayout()
        member_id_layout: QHBoxLayout = QHBoxLayout()
        member_id_layout.addWidget(self.member_id_label)
        member_id_layout.addWidget(self.member_id_input)
        layout.addLayout(member_id_layout)

        layout.addWidget(self.theme_checkbox)

        self.buffer_size_label: QLabel = QLabel("Audio Buffer Size:")
        self.buffer_size_input: QLineEdit = QLineEdit()
        self.buffer_size_input.setPlaceholderText("8192")
        self.buffer_size_input.setValidator(QIntValidator())

        # Load the buffer size input data from settings
        buffer_size: str = str(self.settings.value("buffer_size", "8192"))
        if buffer_size:
            self.buffer_size_input.setText(buffer_size)

        # Save the buffer size input data when it changes
        self.buffer_size_input.textChanged.connect(self.save_buffer_size_input)

        buffer_size_layout: QHBoxLayout = QHBoxLayout()
        buffer_size_layout.addWidget(self.buffer_size_label)
        buffer_size_layout.addWidget(self.buffer_size_input)
        layout.addLayout(buffer_size_layout)

        self.max_duration_label: QLabel = QLabel("Max Duration for Songs (seconds):")
        self.max_duration_input: QLineEdit = QLineEdit()
        self.max_duration_input.setPlaceholderText("300")
        self.max_duration_input.setValidator(QIntValidator())

        # Load the max duration input data from settings
        max_duration: str = str(self.settings.value("max_duration", "300"))
        if max_duration:
            self.max_duration_input.setText(max_duration)

        # Save the max duration input data when it changes
        self.max_duration_input.textChanged.connect(self.save_max_duration_input)

        max_duration_layout: QHBoxLayout = QHBoxLayout()
        max_duration_layout.addWidget(self.max_duration_label)
        max_duration_layout.addWidget(self.max_duration_input)
        
        layout.addLayout(max_duration_layout)

        button_layout: QHBoxLayout = QHBoxLayout()
        ok_button: QPushButton = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button: QPushButton = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    @Slot()
    def save_member_input(self) -> None:
        self.settings.setValue("member_id", self.member_id_input.text())

    @Slot()
    def save_theme_preference(self) -> None:
        self.settings.setValue("dark_theme", self.theme_checkbox.isChecked())

    @Slot()
    def save_buffer_size_input(self) -> None:
        self.settings.setValue("buffer_size", self.buffer_size_input.text())

    @Slot()
    def save_max_duration_input(self) -> None:
        self.settings.setValue("max_duration", self.max_duration_input.text())