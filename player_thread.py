from loguru import logger
from PySide6.QtCore import QThread, Signal

from audio_backend_pyuadio import AudioBackendPyAudio
from player_backend_libopenmpt import PlayerBackendLibOpenMPT


class PlayerThread(QThread):
    position_changed = Signal(int, int)  # Signal to emit position and length
    song_finished = Signal()  # Signal to emit when song is finished

    def __init__(self, module_data, module_size, parent=None):
        super().__init__(parent)
        self.backend = PlayerBackendLibOpenMPT(module_data, module_size)
        self.audio_backend = AudioBackendPyAudio()
        self.stop_flag = False
        self.pause_flag = False
        logger.debug("PlayerThread initialized with module size: {}", module_size)

    def run(self):
        if not self.backend.load_module():
            logger.error("Failed to load module")
            return

        module_length = self.backend.get_module_length()
        logger.debug("Module length: {} seconds", module_length)

        count = 0

        while not self.stop_flag:
            if self.pause_flag:
                self.msleep(100)  # Sleep for a short time to avoid busy-waiting
                continue

            buffer = self.audio_backend.get_buffer()
            count = self.backend.read_interleaved_stereo(
                self.audio_backend.samplerate, self.audio_backend.buffersize, buffer
            )
            if count == 0:
                logger.debug("End of module reached")
                break
            self.audio_backend.write(buffer)

            # Emit position changed signal
            current_position = self.backend.get_position_seconds()
            self.position_changed.emit(int(current_position), int(module_length))

        self.audio_backend.stop()

        if count == 0:
            self.song_finished.emit()
            logger.debug("Song finished")

        self.backend.free_module()
        logger.debug("Playback stopped")

    def stop(self):
        logger.debug("Stop signal received")
        self.stop_flag = True

    def pause(self):
        self.pause_flag = not self.pause_flag
        logger.debug("Pause toggled: {}", self.pause_flag)
