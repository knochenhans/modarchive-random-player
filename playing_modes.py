from enum import Enum


class PlayingMode(Enum):
    LINEAR = 0
    RANDOM = 1


class PlayingSource(Enum):
    LOCAL = 0
    MODARCHIVE = 1


class ModArchiveSource(Enum):
    ALL = 0
    FAVORITES = 1
    ARTIST = 2

class LocalSource(Enum):
    PLAYLIST = 0
    FOLDER = 1