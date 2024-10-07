import ctypes

import pyaudio
from loguru import logger
from PySide6.QtCore import QThread, Signal

from player_backend_libopenmpt import PlayerBackendLibOpenMPT


class PlayerThread(QThread):
    position_changed = Signal(int, int)  # Signal to emit position and length
    song_finished = Signal()  # Signal to emit when song is finished

    def __init__(self, module_data, module_size, parent=None):
        super().__init__(parent)
        self.backend = PlayerBackendLibOpenMPT(module_data, module_size)
        self.stop_flag = False
        self.pause_flag = False
        logger.debug("PlayerThread initialized with module size: {}", module_size)

    def run(self):
        SAMPLERATE = 48000
        BUFFERSIZE = 1024
        buffer = (ctypes.c_int16 * (BUFFERSIZE * 2))()

        if not self.backend.load_module():
            logger.error("Failed to load module")
            return

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=SAMPLERATE,
            output=True,
            frames_per_buffer=BUFFERSIZE,
        )

        module_length = self.backend.get_module_length()
        logger.debug("Module length: {} seconds", module_length)

        count = 0

        while not self.stop_flag:
            if self.pause_flag:
                # logger.debug("Playback paused")
                self.msleep(100)  # Sleep for a short time to avoid busy-waiting
                continue

            count = self.backend.read_interleaved_stereo(SAMPLERATE, BUFFERSIZE, buffer)
            if count == 0:
                logger.debug("End of module reached")
                break
            stream.write(bytes(buffer))

            # Emit position changed signal
            current_position = self.backend.get_position_seconds()
            self.position_changed.emit(int(current_position), int(module_length))

        stream.stop_stream()
        stream.close()
        p.terminate()

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
