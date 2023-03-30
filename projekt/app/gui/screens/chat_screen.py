import queue

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QScrollArea, QFileDialog, QLineEdit, \
    QVBoxLayout, QGridLayout

from projekt.app.gui.gui_actions import GuiActions
from projekt.app.gui.threads import BackgroundTask, Worker
from projekt.app.gui.widgets import ActiveUsersWidget


class ChatScreen(QWidget):
    """Chat screen widget - main screen of the app"""
    def __init__(self, stacked_widget, server_manager):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.server_manager = server_manager
        self.server_manager.connect_to_gui(self)
        self.users_managers = {}

        self.active_users_list = ActiveUsersWidget(self.server_manager)

        self.chat_area = QScrollArea()
        self.send_button = QPushButton("Send")
        self.file_input = QPushButton("File")
        self.chat_input = QLineEdit()
        self.logout_button = QPushButton("Logout")

        self.username_edit = QLineEdit()
        self.username_edit_submit = QPushButton("✔️")
        self.username_edit_submit.setFixedSize(30, 30)
        self.username_edit_submit.clicked.connect(self.__change_username)

        self.status_edit = QLineEdit()
        self.status_edit_submit = QPushButton("✔️")
        self.status_edit_submit.setFixedSize(30, 30)
        self.status_edit_submit.clicked.connect(self.__change_status)

        hbox = QHBoxLayout()
        chat_buttons = QHBoxLayout()
        chat_buttons.addWidget(self.chat_input)
        chat_buttons.addWidget(self.file_input)
        chat_buttons.addWidget(self.send_button)
        chat_window = QVBoxLayout()
        chat_window.addWidget(self.chat_area)
        chat_window.addLayout(chat_buttons)
        hbox.addLayout(chat_window)
        users = QVBoxLayout()

        user_edit = QGridLayout()
        user_edit.addWidget(QLabel("Username:"), 0, 0)
        user_edit.addWidget(self.username_edit, 1, 0)
        user_edit.addWidget(self.username_edit_submit, 1, 1)
        user_edit.addWidget(QLabel("Status:"), 2, 0)
        user_edit.addWidget(self.status_edit, 3, 0)
        user_edit.addWidget(self.status_edit_submit, 3, 1)
        user_edit.setColumnStretch(0, 10)
        user_edit.setColumnStretch(1, 1)
        users.addLayout(user_edit)
        users.addWidget(self.logout_button)
        self.logout_button.clicked.connect(self.__logout)

        users.addWidget(QLabel("Active Users"))
        users.addWidget(self.active_users_list)
        hbox.addLayout(users)
        hbox.setStretch(0, 3)
        hbox.setStretch(1, 1)

        self.setLayout(hbox)

        self.send_button.clicked.connect(self.send_message)
        self.file_input.clicked.connect(self.__open_file_dialog)

        self.update_gui_thread = BackgroundTask(sleep_time=300, loop=True)
        self.update_gui_thread.task_completed.connect(self.__update_active_users)
        self.update_gui_queue = queue.Queue()

        self.receive_thread_pool = QThreadPool.globalInstance()

    def showEvent(self, a0) -> None:
        username = self.server_manager.username
        self.username_edit.setText(username)

        status = self.server_manager.status
        self.status_edit.setText(status)

        self.update_gui_thread.start()

    def __change_username(self):
        self.server_manager.change_username(self.username_edit.text())

    def __change_status(self):
        self.server_manager.change_status(self.status_edit.text())

    def __logout(self):
        self.server_manager.stop()
        self.stacked_widget.setCurrentIndex(0)

    def send_message(self):
        pass

    def notify(self, notification):
        worker = Worker(self.__handle_notification, notification)
        self.receive_thread_pool.start(worker)

    def __handle_notification(self, notification):
        match notification.get("action"):
            case GuiActions.USER_WANTS_TO_CONNECT:
                self.active_users_list.fetch_user(notification.get("user_id")).want_to_connect()
            case GuiActions.USER_ACCEPTED_CONNECTION:
                self.active_users_list.fetch_user(notification.get("user_id")).connection_accepted()
            case GuiActions.USER_REJECTED_CONNECTION:
                self.active_users_list.fetch_user(notification.get("user_id")).connection_rejected()
            case GuiActions.USER_LIST:
                self.update_gui_queue.put(notification.get("users"))
            case _:
                print(f"Unknown notification: {notification}")

    def __update_active_users(self):
        while not self.update_gui_queue.empty():
            users = self.update_gui_queue.get_nowait()
            self.active_users_list.update_list(users)

    def __open_file_dialog(self):
        file_name = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        print(file_name)
