from abc import ABC, abstractmethod
from typing import Any, Dict
import os


class PlayerBackend(ABC):
    def __init__(self) -> None:
        self.module_metadata: Dict[str, Any] = {}
        self.mod: Any = None

    @abstractmethod
    def load_module(self, module_filename: str) -> bool:
        pass

    @abstractmethod
    def get_module_length(self) -> float:
        pass

    @abstractmethod
    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        pass

    @abstractmethod
    def get_position_seconds(self) -> float:
        pass

    @abstractmethod
    def free_module(self) -> None:
        pass
