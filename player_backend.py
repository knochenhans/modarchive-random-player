from abc import ABC, abstractmethod

from loguru import logger


class PlayerBackend(ABC):
    def __init__(self, module_data, module_size):
        self.module_data = module_data
        self.module_size = module_size
        self.mod = None
        logger.debug(
            "AbstractPlayerBackend initialized with module size: {}", module_size
        )

    @abstractmethod
    def load_module(self):
        pass

    @abstractmethod
    def get_module_length(self):
        pass

    @abstractmethod
    def read_interleaved_stereo(self, samplerate, buffersize, buffer):
        pass

    @abstractmethod
    def get_position_seconds(self):
        pass

    @abstractmethod
    def free_module(self):
        pass
