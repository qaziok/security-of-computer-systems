from PyQt6.QtWidgets import QStackedWidget

from projekt.app.gui.widgets import ChatWidget


class TalkWidget(QStackedWidget):
    def __init__(self, users_controller):
        super().__init__()
        self.active_user_id = None
        self.users_controller = users_controller
        self.user_to_chat = {}

        hello_widget = self.create_chat(None)
        hello_widget.sent("Hello, this is a chat app")
        hello_widget.received_message("Really?")
        hello_widget.sent("Yes, really! :D")
        hello_widget.received_message("Wow, that's cool!")

        self.addWidget(hello_widget)
        self.setCurrentWidget(hello_widget)

    def create_chat(self, user_id):
        widget = ChatWidget(user_id, self.users_controller)
        self.addWidget(widget)
        self.user_to_chat[user_id] = widget
        self.set_chat(user_id)
        return widget

    def get_current_chat(self):
        return self.active_user_id, self.currentWidget()

    def get_chat(self, user_id):
        return self.user_to_chat.get(user_id)

    def set_chat(self, user_id):
        self.active_user_id = user_id
        self.setCurrentWidget(self.user_to_chat[user_id])

    def remove_chat(self, user_id):
        self.removeWidget(self.user_to_chat[user_id])
        del self.user_to_chat[user_id]
