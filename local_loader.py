from typing import Optional
from player_backends.player_backend import Song


class LocalLoader:
    def __init__(self) -> None:
        self.local_files: list[str] = []

    def load_module(self) -> Optional[Song]:

        return None
