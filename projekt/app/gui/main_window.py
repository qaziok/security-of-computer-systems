import sys
import socket
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QLineEdit, QFileDialog, QListWidget, QListWidgetItem, QLabel


class Client(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create GUI elements
        self.setGeometry(100, 100, 700, 500)
        self.setWindowTitle('Client')
        self.text_box = QTextEdit(self)
        self.text_box.move(10, 10)
        self.text_box.resize(480, 300)
        self.input_box = QLineEdit(self)
        self.input_box.move(10, 320)
        self.input_box.resize(380, 30)
        self.send_button = QPushButton('Send', self)
        self.send_button.move(400, 320)
        self.send_button.resize(80, 30)
        self.send_file_button = QPushButton('Send File', self)
        self.send_file_button.move(10, 360)
        self.send_file_button.resize(80, 30)
        self.active_user_list = QListWidget(self)
        self.active_user_list.move(500, 10)
        self.active_user_list.resize(90, 480)

        # Connect GUI elements to functions
        self.send_button.clicked.connect(self.send_message)
        self.send_file_button.clicked.connect(self.send_file)

        # Create socket object
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to server
        self.host = 'localhost'  # Replace with your server's IP address or hostname
        self.port = 12345  # Replace with your server's port number
        # try:
        #     self.sock.connect((self.host, self.port))
        # except Exception as e:
        #     self.text_box.append(str(e))
        #     sys.exit()
        #
        # # Get list of active users from server
        # self.sock.sendall(b'get_users')
        # users = self.sock.recv(1024).decode().split(',')
        # for user in users:
        #     if user != '':
        #         self.active_users_list.addItem(QListWidgetItem(user))

    def send_message(self):
        # Get message from input box
        message = self.input_box.text()

        # Send message to server
        self.sock.sendall(message.encode())

        # Clear input box
        self.input_box.clear()

        # Receive response from server
        response = self.sock.recv(1024).decode()

        # Display response in text box
        self.text_box.append(response)

    def send_file(self):
        # Get filename from file dialog
        filename = QFileDialog.getOpenFileName(self, 'Select File')[0]

        # Check if filename is not empty
        if filename:
            # Get file size
            filesize = os.path.getsize(filename)

            # Send file size to server
            self.sock.sendall(str(filesize).encode())

            # Send file to server
            with open(filename, 'rb') as f:
                data = f.read()
                self.sock.sendall(data)

            # Receive response from server
            response = self.sock.recv(1024).decode()

            # Display response in text box
            self.text_box.append(response)

    def update_active_users(self, users):
        # Clear active users list
        self.active_users_list.clear()

        # Add new active users
        for user in users:
            if user != '':
                self.active_users_list.addItem(QListWidgetItem(user))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = Client()
    client.show()
    sys.exit(app.exec())
