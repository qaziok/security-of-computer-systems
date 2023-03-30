from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout

from projekt.app.gui.widgets import UserWidget


class ActiveUsersWidget(QScrollArea):
    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.widget = QWidget()
        self.widgets = {}

        self.widget.setLayout(self.layout)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)

    def update_list(self, users: dict[hash, dict]):
        users_to_remove = [
            user_id for user_id in self.widgets if user_id not in users.keys()
        ]

        for user_id in users_to_remove:
            self.layout.removeWidget(self.widgets[user_id])
            self.widgets[user_id].deleteLater()
            del self.widgets[user_id]

        for user_id, user_info in users.items():
            if user_id not in self.widgets:
                self.widgets[user_id] = UserWidget(user_info, self.server_manager)
                self.layout.addWidget(self.widgets[user_id])
            else:
                self.widgets[user_id].update_info(user_info)

        self.update()

    def fetch_user(self, user_id):
        return self.widgets[user_id]


