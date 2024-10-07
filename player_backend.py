from abc import ABC, abstractmethod
from typing import Any, Dict

from loguru import logger


class PlayerBackend(ABC):
    def __init__(self, module_data: bytes, module_size: int) -> None:
        self.module_data: bytes = module_data
        self.module_size: int = module_size
        self.module_metadata: Dict[str, Any] = {}
        self.mod: Any = None

    @abstractmethod
    def load_module(self) -> bool:
        pass

    @abstractmethod
    def get_module_length(self) -> float:
        pass

    @abstractmethod
    def read_interleaved_stereo(
        self, samplerate: int, buffersize: int, buffer: Any
    ) -> int:
        pass

    @abstractmethod
    def get_position_seconds(self) -> float:
        pass

    @abstractmethod
    def free_module(self) -> None:
        pass
