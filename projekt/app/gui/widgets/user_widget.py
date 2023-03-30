from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QPushButton, QFrame, QHBoxLayout


class UserWidget(QFrame):
    def __init__(self, user_info, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.id = user_info.get("id")
        self.name = user_info.get("name")
        self.status = user_info.get("status")

        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel(self.status)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.connects_buttons = QHBoxLayout()

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect)
        self.connects_buttons.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect)
        self.connects_buttons.addWidget(self.disconnect_button)
        self.disconnect_button.hide()

        self.request_buttons = QHBoxLayout()

        self.accept_button = QPushButton("✔️")
        self.accept_button.setFixedSize(20, 20)
        self.request_buttons.addWidget(self.accept_button)
        self.accept_button.clicked.connect(self.connection_accepted)
        self.accept_button.hide()

        self.reject_button = QPushButton("❌")
        self.reject_button.setFixedSize(20, 20)
        self.request_buttons.addWidget(self.reject_button)
        self.reject_button.clicked.connect(self.connection_rejected)
        self.reject_button.hide()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.status_label)
        self.layout.addLayout(self.connects_buttons)
        self.layout.addLayout(self.request_buttons)

        self.setFixedHeight(90)
        self.setLayout(self.layout)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Sunken)

    def update_info(self, user_info):
        self.name = user_info.get("name")
        self.status = user_info.get("status")
        self.name_label.setText(self.name)
        self.status_label.setText(self.status)

    def connect(self):
        self.server_manager.ask_for_connection(self.id)

    def disconnect(self):
        print("disconnect")
        #self.server_manager.disconnect(self.id)

    def want_to_connect(self):
        self.connect_button.hide()
        self.accept_button.show()
        self.reject_button.show()

    def connection_accepted(self):
        self.accept_button.hide()
        self.reject_button.hide()
        self.disconnect_button.show()

    def connection_rejected(self):
        self.accept_button.hide()
        self.reject_button.hide()
        self.connect_button.show()
