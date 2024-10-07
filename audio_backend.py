from abc import ABC, abstractmethod


class AudioBackend(ABC):
    @abstractmethod
    def write(self, data):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_buffer(self):
        pass
