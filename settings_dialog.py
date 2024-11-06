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
