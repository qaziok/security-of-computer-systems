import logging
import threading
from time import sleep

from PyQt6.QtCore import QRunnable, QThread, QTimer
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout


class ConnectScreen(QWidget):
    def __init__(self, stacked_widget, server_manager, users_controller):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.server_manager = server_manager
        self.users_controller = users_controller

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.connect_button = QPushButton("Connect to Server")

        vbox = QVBoxLayout()
        vbox.addWidget(self.username_label)
        vbox.addWidget(self.username_input)
        vbox.addWidget(self.password_label)
        vbox.addWidget(self.password_input)
        vbox.addWidget(self.connect_button)

        self.setLayout(vbox)

        self.connect_button.clicked.connect(self.login)
        self.timer = QTimer()

    def login(self):
        self.stacked_widget.setCurrentIndex(1)
        self.timer.singleShot(100, self.connect)

    def connect(self):
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            self.users_controller.start(username, password)
            self.server_manager.start(username, password)
            self.stacked_widget.setCurrentIndex(2)
        except Exception as e:
            logging.error(e)
            self.stacked_widget.setCurrentIndex(0)
