import ctypes
from loguru import logger

from player_backends.player_backend import PlayerBackend
from player_backends.libgme.ctypes_functions import (
    gme_info_t,
    libgme,
    gme_type_t,
    gme_err_t,
    handle_error,
)


class PlayerBackendLibGME(PlayerBackend):
    def __init__(self, name: str = "LibGME") -> None:
        super().__init__(name)
        self.emulator = ctypes.POINTER(ctypes.c_void_p)()
        self.track_info = None
        self.sample_rate = 44100

        logger.debug("PlayerBackendLibGME initialized")

    def load_file(self) -> bool:
        result = libgme.gme_open_file(
            ctypes.c_char_p(self.song.filename.encode()),
            ctypes.byref(self.emulator),
            self.sample_rate,
        )

        if result:
            logger.error(f"Could not open file {self.song.filename}")
            return False
        return True

    def check_module(self) -> bool:
        file_type = ctypes.c_void_p()

        result = libgme.gme_identify_file(
            ctypes.c_char_p(self.song.filename.encode()),
            ctypes.byref(file_type),
        )
        handle_error(result)

        if result:
            logger.error("gme_identify_file failed")
            return False

        if self.load_file():
            logger.info(f"Successfully loaded file: {self.song.filename}")
            return True
        return False

    def prepare_playing(self, subsong: int = 0) -> None:
        self.load_file()
        if not self.emulator:
            raise ValueError("Emulator instance is not initialized")

        ret = libgme.gme_start_track(self.emulator, subsong)

        if ret:
            logger.error(f"Failed to start track {subsong}")
            raise RuntimeError("Failed to start track")

        logger.info(f"Prepared subsong {subsong} for playback")

    def retrieve_song_info(self) -> None:
        self.track_info = self._get_track_info(0)
        self.song.title = self.track_info.song.decode()
        self.song.duration = int(self.get_module_length())
        self.song.formatname = self.track_info.system.decode()
        self.song.artist = self.track_info.author.decode()

        logger.info(
            f"Song info retrieved: {self.song.title}, Duration: {self.song.duration} ms"
        )

    def get_module_length(self) -> float:
        self.prepare_playing(0)
        self.track_info = self._get_track_info(0)

        if not self.track_info:
            raise ValueError("Track info is not initialized")
        return (
            self.track_info.play_length if self.track_info.play_length != -1 else 150000
        ) / 1000.0  # Convert milliseconds to seconds

    def _get_track_info(self, track: int) -> gme_info_t:
        info_ptr = ctypes.POINTER(gme_info_t)()
        ret = libgme.gme_track_info(self.emulator, ctypes.byref(info_ptr), track)

        if ret:
            logger.error("Failed to retrieve song info")
            raise RuntimeError("Failed to retrieve song info")

        return info_ptr.contents

    def get_position_seconds(self) -> float:
        position_ms = ctypes.c_int()
        return (
            libgme.gme_tell(self.emulator, ctypes.byref(position_ms)) / 1000.0
        )  # Convert milliseconds to seconds

    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        buffer = (ctypes.c_short * buffersize)()
        ret = libgme.gme_play(self.emulator, buffersize, ctypes.byref(buffer))

        if ret:
            logger.error("Failed to read chunk")
            raise RuntimeError("Failed to read chunk")

        ended_ret = libgme.gme_track_ended(self.emulator)

        if ended_ret:
            logger.info("Song has ended")
            return 0, bytes(buffer)

        return buffersize, bytes(buffer)

    def free_module(self) -> None:
        if self.emulator:
            libgme.gme_delete(self.emulator)
            self.emulator = None
            logger.info("LibGME instance deleted")

    def seek(self, position: int) -> None:
        ret = libgme.gme_seek(self.emulator, position * 1000)  # Convert seconds to ms

        if ret:
            logger.error("Seeking failed")
            raise RuntimeError("Seeking failed")

        logger.info(f"Seeked to position: {position} seconds")

    def cleanup(self) -> None:
        self.free_module()
        logger.info("LibGME cleaned up")
