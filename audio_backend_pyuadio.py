import ctypes

import pyaudio
from loguru import logger

from audio_backend import AudioBackend


class AudioBackendPyAudio(AudioBackend):
    def __init__(self, samplerate=48000, buffersize=1024):
        self.samplerate = samplerate
        self.buffersize = buffersize
        self.buffer = (ctypes.c_int16 * (self.buffersize * 2))()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=self.samplerate,
            output=True,
            frames_per_buffer=self.buffersize,
        )
        logger.debug(
            "PyAudio AudioBackend initialized with samplerate: {} and buffersize: {}",
            samplerate,
            buffersize,
        )

    def write(self, data):
        self.stream.write(bytes(data))

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        logger.debug("PyAudio AudioBackend stopped")

    def get_buffer(self):
        return self.buffer
