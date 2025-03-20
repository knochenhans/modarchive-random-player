import os
import time

from loguru import logger
import psutil
import pytest

from loaders.local_file_loader import ModuleTester, SongEmitter
from player_backends.Song import Song
from player_backends.libuade.player_backend_libuade import (
    PlayerBackendLibUADE,
    PlayerBackend,
)
from playlist.playlist import Playlist


@pytest.fixture
def memory_usage_logger():
    last_memory_usage = {"value": 0}

    def log_memory_usage():
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        logger.debug(f"Memory usage: {mem_info.rss / 1024 ** 2:.2f} MB")

        diff = mem_info.rss - last_memory_usage["value"]
        last_memory_usage["value"] = mem_info.rss

        return diff

    return log_memory_usage


def test_memory_usage1(memory_usage_logger):
    log_memory_usage = memory_usage_logger
    log_memory_usage()
    song = Song(filename="tests/knallhatten.mod")

    for _ in range(100):
        log_memory_usage()
        player_backend = PlayerBackendLibUADE()
        player_backend.song = song
        player_backend.check_module()
        player_backend.prepare_playing()
        player_backend.cleanup()

        # assert log_memory_usage() == 0

    # Wait 5 seconds
    time.sleep(5)

    assert log_memory_usage() == 0


def test_lots_of_files(memory_usage_logger):
    log_memory_usage = memory_usage_logger
    # path = "/mnt/Daten/Musik/Retro/Amiga Games/"
    path = "/mnt/Daten/Musik/Retro/Amiga Games/BiondMyKontrol.mod"

    # Get all files in the directory
    # files = os.listdir(path)

    songs = [Song(filename=path)]

    # for file in files:
    #     songs.append(Song(filename=os.path.join(path, file)))
    # player_backend = PlayerBackendLibUADE()
    # player_backend.song = song
    # player_backend.check_module()
    # player_backend.prepare_playing()
    # module_length: float = player_backend.get_module_length()

    # # for _ in range(100):
    # #     count, buffer = player_backend.read_chunk(44100, 1024)
    # # player_backend.free_module()
    # player_backend.cleanup()

    log_memory_usage()

    playlist = Playlist(name="Test Playlist", songs=songs)

    # log_memory_usage()

    def song_checked_callback(song: Song):
        # logger.debug(f"Song checked: {song.title}")
        # playlist.add_song(song)
        # log_memory_usage()
        del song

    def song_info_retrieved_callback(song: Song):
        # logger.debug(f"Song info retrieved: {song.title}")
        del song

    # assert log_memory_usage() == 0

    emitter = SongEmitter(song_checked_callback, song_info_retrieved_callback)

    song = songs[0]

    print(song.filename)
    # assert log_memory_usage() == 0

    tester = ModuleTester(song, {"LibUADE": PlayerBackendLibUADE}, emitter)

    # assert log_memory_usage() == 0

    tester.test_backends()
    tester = None
    emitter = None
    playlist = None
    songs = None

    time.sleep(10)

    assert log_memory_usage() == 0
