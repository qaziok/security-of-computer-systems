from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget, QSizePolicy


class MessageWidget(QWidget):
    class __Message(QWidget):
        def __init__(self, message, sent, file_name, **kwargs):
            super().__init__()

            self.file_download_function = kwargs.get('file_download_function')
            self.message = QLabel(message or file_name)
            self.message.setWordWrap(True)
            self.layout = QHBoxLayout()
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.addWidget(self.message)
            self.setLayout(self.layout)
            self.message.setAlignment(Qt.AlignmentFlag.AlignLeft)
            if sent:
                self.layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            else:
                self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

            self.setStyleSheet('''
                        border: 2px solid black;
                        border-radius: 10px;
                        padding: 5px;
                    ''')

        def mouseReleaseEvent(self, event):
            if self.file_download_function:
                self.file_download_function()

    def __init__(self, message, sent, file_name, **kwargs):
        super().__init__()

        self.message = self.__Message(message, sent, file_name, **kwargs)
        self.layout = QHBoxLayout()
        balance = [1, 6]

        if sent:
            left = QWidget()
            right = self.message
        else:
            right = QWidget()
            left = self.message
            balance.reverse()

        self.layout.addWidget(left)
        self.layout.addWidget(right)
        self.layout.setStretch(0, balance[0])
        self.layout.setStretch(1, balance[1])

        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
