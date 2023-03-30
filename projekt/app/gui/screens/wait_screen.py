from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout


class WaitScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        self.label = QLabel("Connecting to server...")

        vbox = QVBoxLayout()
        vbox.addWidget(self.label, Qt.AlignmentFlag.AlignCenter, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(vbox)
