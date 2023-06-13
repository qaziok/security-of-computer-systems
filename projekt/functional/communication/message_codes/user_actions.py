from enum import Enum, auto


class UserActions(Enum):
    """User actions codes"""

    MESSAGE = auto()

    DOWNLOAD_FILE = auto()

    FILE = auto()

    FILE_HEADER = auto()

    FILE_PROGRESS = auto()

    CHANGED_ENCRYPTION = auto()

    FILE_DOWNLOADED = auto()
