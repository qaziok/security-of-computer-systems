from enum import Enum, auto


class ServerActions(Enum):
    """Server actions codes"""

    # List of active users was updated - list of active users
    ACTIVE_USERS = auto()

    # User ask for connection to this client - their user id
    ASK_USER_FOR_CONNECTION = auto()

    # This client accepted connection with other user - client id, client public key
    CONNECTION_APPROVED = auto()

    # This client rejected connection with other user - client id
    CONNECTION_REJECTED = auto()
