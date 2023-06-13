import logging
import os

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, \
    QHBoxLayout, QRadioButton, QCheckBox, QFileDialog

from projekt.app.connections import ServerManager, UsersController
from projekt.functional.encryption import Keys

KEYS_DEFAULT_PATH = os.path.join(os.getcwd(), "keys")


class ConnectScreen(QWidget):
    class __TitleLabel(QLabel):
        def __init__(self, text):
            super().__init__(text)
            self.setStyleSheet('font-size: 18px; font-weight: bold;')
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def __init__(self, stacked_widget, server_manager, users_controller):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.server_manager: ServerManager = server_manager
        self.users_controller: UsersController = users_controller

        self.timer = QTimer()

        username_vbox = QVBoxLayout()
        username_vbox.setContentsMargins(0, 0, 0, 5)

        self.username_input = QLineEdit()
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        username_vbox.addWidget(self.__TitleLabel("Username"))
        username_vbox.addWidget(self.username_input)

        password_vbox = QVBoxLayout()
        password_vbox.setContentsMargins(0, 5, 0, 5)

        self.password_input = QLineEdit()
        self.password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        password_vbox.addWidget(self.__TitleLabel("Password"))
        password_vbox.addWidget(self.password_input)

        keys_options_vbox = self.__set_keys_options()

        connect_button = QPushButton("Connect")
        connect_button.setStyleSheet('font-size: 16px')

        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addStretch(1)
        vbox.addLayout(username_vbox)
        vbox.addLayout(password_vbox)
        vbox.addLayout(keys_options_vbox)
        vbox.addWidget(connect_button)
        vbox.addStretch(1)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(vbox, stretch=6)
        hbox.addStretch(1)

        self.setLayout(hbox)

        connect_button.clicked.connect(self.__login)

    def __login(self):
        self.stacked_widget.setCurrentIndex(1)
        self.timer.singleShot(100, self.__connect)

    def __connect(self):
        username = self.username_input.text()
        pp = self.password_input.text()
        password = None if pp == "" else pp

        try:
            keys = self.__get_keys(password)
            self.users_controller.start(keys)
            self.server_manager.start(username, keys)
            self.stacked_widget.setCurrentIndex(2)
        except Exception as e:
            logging.error(e)
            self.stacked_widget.setCurrentIndex(0)

    def __get_keys(self, password):
        if self.generate_option.isChecked():
            keys = Keys.generate_keys(passphrase=password)
            if self.keys_generate_save_checkbox.isChecked():
                keys.save_to_files(KEYS_DEFAULT_PATH)
            return keys
        elif self.load_option.isChecked():
            public_key_path = self.load_public_key_input.text()
            private_key_path = self.load_private_key_input.text()
            return Keys.import_keys(passphrase=password).from_files(public_key_path, private_key_path)

    def __load_file(self, text_input):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "PEM Files (*.pem)")
        text_input.setText(file_path)

    def __set_keys_options(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 5)

        vbox.addWidget(self.__TitleLabel("Keys"), alignment=Qt.AlignmentFlag.AlignCenter)

        # Generate keys
        generate_vbox = QVBoxLayout()
        self.generate_option = QRadioButton("Generate")
        self.generate_option.setChecked(True)

        generate_widget = QWidget()
        generate_widget.setVisible(True)
        generate_widget.setLayout(generate_vbox)

        self.generate_option.toggled.connect(generate_widget.setVisible)

        self.keys_generate_save_checkbox = QCheckBox("Save to file")
        generate_vbox.addWidget(self.keys_generate_save_checkbox)

        # Load keys
        load_vbox = QVBoxLayout()
        self.load_option = QRadioButton("Load from file")
        self.load_option.setChecked(False)

        load_widget = QWidget()
        load_widget.setVisible(False)
        load_widget.setLayout(load_vbox)

        self.load_option.toggled.connect(load_widget.setVisible)

        # Load public key
        load_public_key_hbox = QHBoxLayout()
        load_public_key_hbox.addWidget(QLabel("Public key"))

        self.load_public_key_input = QLineEdit()
        self.load_public_key_input.setText(os.path.join(KEYS_DEFAULT_PATH, "public.pem"))
        load_public_key_button = QPushButton("Browse")
        load_public_key_button.clicked.connect(lambda: self.__load_file(self.load_public_key_input))
        load_public_key_hbox.addWidget(self.load_public_key_input)
        load_public_key_hbox.addWidget(load_public_key_button)

        load_vbox.addLayout(load_public_key_hbox)

        # Load private key
        load_private_key_hbox = QHBoxLayout()
        load_private_key_hbox.addWidget(QLabel("Private key"))

        self.load_private_key_input = QLineEdit()
        self.load_private_key_input.setText(os.path.join(KEYS_DEFAULT_PATH, "private.pem"))
        load_private_key_button = QPushButton("Browse")
        load_private_key_button.clicked.connect(lambda: self.__load_file(self.load_private_key_input))
        load_private_key_hbox.addWidget(self.load_private_key_input)
        load_private_key_hbox.addWidget(load_private_key_button)

        load_vbox.addLayout(load_private_key_hbox)

        # Group radio buttons
        radio_buttons_layout = QVBoxLayout()
        radio_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        radio_buttons_layout.addWidget(self.generate_option)
        radio_buttons_layout.addWidget(self.load_option)

        vbox.addLayout(radio_buttons_layout)
        vbox.addWidget(generate_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(load_widget)

        return vbox
