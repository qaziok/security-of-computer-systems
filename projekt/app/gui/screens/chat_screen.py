import logging
import queue
import os

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QScrollArea, QFileDialog, QLineEdit, \
    QVBoxLayout, QGridLayout, QComboBox, QProgressBar

from projekt.app.gui.gui_actions import GuiActions
from projekt.app.gui.threads import BackgroundTask, Worker
from projekt.app.gui.widgets import ActiveUsersWidget, TalkWidget


class ChatScreen(QWidget):
    """Chat screen widget - main screen of the app"""

    def __init__(self, stacked_widget, server_manager, users_controller):
        super().__init__()
        self.file_path = None
        self.stacked_widget = stacked_widget
        self.server_manager = server_manager
        self.users_controller = users_controller
        self.server_manager.connect_to_gui(self)
        self.users_controller.connect_to_gui(self)

        self.active_users_list = ActiveUsersWidget(self.server_manager, self.users_controller)
        self.chat_area = TalkWidget(self.users_controller)

        self.send_button = QPushButton("Send")
        self.file_input = QPushButton("File")
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.returnPressed.connect(self.__send_message)

        self.username_edit = QLineEdit()
        self.username_edit_submit = QPushButton("✔️")
        self.username_edit_submit.setFixedSize(30, 30)
        self.username_edit_submit.clicked.connect(self.__change_username)

        self.status_edit = QLineEdit()
        self.status_edit_submit = QPushButton("✔️")
        self.status_edit_submit.setFixedSize(30, 30)
        self.status_edit_submit.clicked.connect(self.__change_status)
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.__logout)

        main_layout = QHBoxLayout()

        chat_buttons = QVBoxLayout()

        file_bar = QHBoxLayout()
        file_bar.addWidget(self.file_input)
        chat_buttons.addLayout(file_bar)

        message_bar = QHBoxLayout()
        message_bar.addWidget(self.chat_input)
        self.encryption_choice = QComboBox()
        self.encryption_choice.addItems(["EAX", "ECB", "CBC"])
        message_bar.addWidget(self.encryption_choice)
        message_bar.addWidget(self.send_button)
        chat_buttons.addLayout(message_bar)

        chat_window = QVBoxLayout()
        chat_window.addWidget(self.chat_area)
        chat_window.addLayout(chat_buttons)
        main_layout.addLayout(chat_window)

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

        users.addWidget(QLabel("Active Users"))
        users.addWidget(self.active_users_list)
        main_layout.addLayout(users)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(1, 1)

        self.setLayout(main_layout)

        self.send_button.clicked.connect(self.__send_message)
        self.file_input.clicked.connect(self.__open_file_dialog)

        self.update_gui_thread = BackgroundTask(sleep_time=300, loop=True)
        self.update_gui_thread.task_completed.connect(self.__update_gui)
        self.update_gui_queue = queue.Queue()

        self.receive_thread_pool = QThreadPool.globalInstance()

    def showEvent(self, a0) -> None:
        username = self.server_manager.username
        self.username_edit.setText(username)

        status = self.server_manager.status
        self.status_edit.setText(status)

        self.update_gui_thread.start()

    def hideEvent(self, a0) -> None:
        self.update_gui_thread.quit()

    def __change_username(self):
        self.server_manager.change_username(self.username_edit.text())

    def __change_status(self):
        self.server_manager.change_status(self.status_edit.text())

    def __logout(self):
        self.server_manager.stop()
        self.users_controller.stop()
        self.stacked_widget.setCurrentIndex(0)

    def __send_message(self):
        user_id, chat = self.chat_area.get_current_chat()

        message = self.chat_input.text()

        if user_id is not None:
            self.users_controller.send(user_id, message, self.file_path)

        # Add message to chat
        if message or self.file_path:
            chat.sent(message, self.file_path)

        # Clear input
        self.chat_input.clear()
        self.file_path = None
        self.file_input.setText("File")

    def notify(self, notification):
        worker = Worker(self.__handle_notification, notification)
        self.receive_thread_pool.start(worker)

    def __handle_notification(self, notification):
        match notification.get("action"):
            case GuiActions.USER_WANTS_TO_CONNECT:
                self.active_users_list.fetch_user(notification.get("user_id")).user_wants_to_connect()
            case GuiActions.USER_ACCEPTED_CONNECTION:
                self.active_users_list.fetch_user(notification.get("user_id")).connecting()
            case GuiActions.USER_CONNECTED:
                self.active_users_list.fetch_user(notification.get("user_id")).connected()
                self.update_gui_queue.put(notification)
            case GuiActions.USER_REJECTED_CONNECTION:
                self.active_users_list.fetch_user(notification.get("user_id")).reject_connection()
            case (GuiActions.USER_LIST | GuiActions.MESSAGE_RECEIVED |
                  GuiActions.CREATE_PROGRESS_BAR | GuiActions.UPDATE_PROGRESS_BAR):
                self.update_gui_queue.put(notification)
            case _:
                logging.error(f"Unknown notification: {notification}")

    def __update_gui(self):
        while not self.update_gui_queue.empty():
            data = self.update_gui_queue.get_nowait()
            match data.get("action"):
                case GuiActions.USER_LIST:
                    users = data.get("users")
                    self.active_users_list.update_list(users)
                case GuiActions.USER_CONNECTED:
                    user_id = data.get("user_id")
                    self.chat_area.create_chat(user_id)
                case GuiActions.MESSAGE_RECEIVED:
                    self.__receive_message(data)
                case GuiActions.CREATE_PROGRESS_BAR:
                    self.__create_progress_bar(data)
                case GuiActions.UPDATE_PROGRESS_BAR:
                    self.chat_area.get_chat(data.get("user_id")
                                            ).update_progress_bar(data.get("file_id"), data.get("progress"))

    def __receive_message(self, data):
        user_id = data.get("user_id")
        message = data.get("message")
        file = data.get("file")

        self.chat_area.get_chat(user_id).received_message(message, file)

    def __open_file_dialog(self):
        self.file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        file_name = os.path.basename(self.file_path)
        self.file_input.setText(file_name)

    def __create_progress_bar(self, data):
        user_id = data.get("user_id")
        chat = self.chat_area.get_chat(user_id)
        file_id = data.get("file_id")
        file_name = data.get("file_name")
        file_size = data.get("number_of_chunks")
        chat.create_progress_bar(file_id, file_name, file_size)

