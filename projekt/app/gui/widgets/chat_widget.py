import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QProgressBar

from projekt.app.gui.widgets.message_widget import MessageWidget


class ChatWidget(QWidget):
    def __init__(self, user_id, users_controller):
        super().__init__()
        self.user_id = user_id
        self.users_controller = users_controller

        self.scroll = QScrollArea()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.widget = QWidget()
        self.widgets = {}
        self.progress_bars = {}

        self.widget.setLayout(self.layout)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.main = QVBoxLayout()
        self.main.setContentsMargins(0, 0, 0, 0)
        self.main.addWidget(self.scroll)
        self.setLayout(self.main)

    def __create_message(self, *, message=None, sent=False, file_name=None, **kwargs):
        widget = MessageWidget(message, sent, file_name, **kwargs)
        self.layout.addWidget(widget)
        self.update()
        self.scroll.verticalScrollBar().setMaximum(self.scroll.verticalScrollBar().maximum() + widget.height())
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def __build_message(self, message, sent, file_info):
        if message:
            self.__create_message(message=message, sent=sent)
        if file_info:
            self.__create_message(sent=sent, **file_info)

    def create_progress_bar(self, file_id, file_name):
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFormat(file_name)
        self.main.addWidget(progress_bar)
        self.progress_bars[file_id] = progress_bar

    def update_progress_bar(self, file_id, file_size):
        try:
            self.progress_bars[file_id].setValue(file_size)
        except KeyError:
            pass

    def remove_progress_bar(self, file_id):
        self.main.removeWidget(self.progress_bars[file_id])
        self.progress_bars[file_id].deleteLater()
        del self.progress_bars[file_id]

    def sent(self, message, file_path=None):
        file_info = {
            'file_name': os.path.basename(file_path),
            'file_download_function': lambda: os.system(f'start {file_path}')
        } if file_path else {}

        self.__build_message(message, True, file_info)

    def received_message(self, message, file_data=None):
        file_info = {
            "file_name": file_data[1],
            "file_download_function": lambda: self.users_controller.download_file(self.user_id, file_data[0])
        } if file_data else {}

        self.__build_message(message, False, file_info)


