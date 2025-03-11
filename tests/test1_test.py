import os

from loguru import logger
import psutil

from player_backends.Song import Song
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE


def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logger.debug(f"Memory usage: {mem_info.rss / 1024 ** 2:.2f} MB")


def test_1():
    song = Song(filename="tests/knallhatten.mod")

    player_backend = PlayerBackendLibUADE()
    player_backend.song = song
    player_backend.check_module()
    player_backend.prepare_playing()
    player_backend.cleanup()

    assert "" == ""


def test_lots_of_files():
    path = "/mnt/Daten/Musik/Retro/Amiga Games/"

    # Get all files in the directory
    files = os.listdir(path)

    for file in files:
        song = Song(filename=os.path.join(path, file))
        player_backend = PlayerBackendLibUADE()
        player_backend.song = song
        player_backend.check_module()
        player_backend.prepare_playing()
        module_length: float = player_backend.get_module_length()

        for _ in range(100):
            count, buffer = player_backend.read_chunk(44100, 1024)
        # player_backend.free_module()
        player_backend.cleanup()

        log_memory_usage()
