from enum import Enum, auto


class ClientActions(Enum):
    """Client actions codes"""

    # User is active - no args
    ACTIVE = auto()

    # User is leaving - no args
    LEAVE = auto()

    # User is updating their information - changed information
    USER_UPDATE = auto()

    # User is asking for connection with other user - their user id
    ASK_FOR_CONNECTION = auto()

    # User is accepting connection with other user - their user id
    ACCEPT_CONNECTION = auto()

    # User is rejecting connection with other user - their user id
    REJECT_CONNECTION = auto()
