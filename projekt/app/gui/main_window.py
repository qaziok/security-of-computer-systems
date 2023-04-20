import socket
import sys
import threading
from time import sleep

from PyQt6.QtGui import QScreen, QGuiApplication
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QApplication

from projekt.app.connections import ServerManager, UsersController
from projekt.app.gui.screens import ChatScreen, ConnectScreen, WaitScreen
from projekt.functional.encryption import Keys

HOST = socket.gethostname()
SERVER_IP = socket.gethostbyname(HOST)
SERVER_PORT = 5000

KEYS = Keys.generate_keys()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat app")

        self.setGeometry(100, 100, 600, 400)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.users_controller = UsersController(KEYS)
        self.server_manager = ServerManager(SERVER_IP, SERVER_PORT, KEYS, self.users_controller)

        connect_screen = ConnectScreen(self.stacked_widget, self.server_manager, self.users_controller)
        wait_screen = WaitScreen(self.stacked_widget)
        chat_screen = ChatScreen(self.stacked_widget, self.server_manager, self.users_controller)
        self.stacked_widget.addWidget(connect_screen)
        self.stacked_widget.addWidget(wait_screen)
        self.stacked_widget.addWidget(chat_screen)

        self.stacked_widget.setCurrentWidget(connect_screen)

    def closeEvent(self, a0):
        if self.server_manager.connected:
            self.server_manager.stop()
            self.users_controller.stop()
        super().closeEvent(a0)
