from enum import Enum, auto

from projekt.functional.communication import ServerActions


class GuiActions(Enum):
    """Gui actions codes"""

    # This user received a request to connect - user id - show accept/reject buttons
    USER_WANTS_TO_CONNECT = auto()

    # This user accepted connection - user id - show disconnect button
    USER_ACCEPTED_CONNECTION = auto()

    # This user rejected connection - user id - show connect button
    USER_REJECTED_CONNECTION = auto()

    # This user received a list of users - list of users - update active users list
    USER_LIST = auto()

    @classmethod
    def translate(cls, server_action):
        """Translate server action to gui action"""
        match server_action:
            case ServerActions.ASK_USER_FOR_CONNECTION:
                return cls.USER_WANTS_TO_CONNECT
            case ServerActions.CONNECTION_APPROVED:
                return cls.USER_ACCEPTED_CONNECTION
            case ServerActions.CONNECTION_REJECTED:
                return cls.USER_REJECTED_CONNECTION
            case ServerActions.ACTIVE_USERS:
                return cls.USER_LIST
            case _:
                return None
