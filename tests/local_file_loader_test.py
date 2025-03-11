import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QThreadPool
from loaders.local_file_loader import (
    LocalFileLoader,
    LocalFileLoaderWorker,
    SongEmitter,
)
from player_backends.Song import Song
from player_backends.player_backend import PlayerBackend


@pytest.fixture
def file_list():
    return ["song1.mod", "song2.mod"]


@pytest.fixture
def backends():
    return {"backend1": MagicMock(spec=PlayerBackend)}


@pytest.fixture
def loader(file_list, backends):
    return LocalFileLoader(file_list, backends)


def test_load_module(loader):
    song = loader.load_module("song1.mod")
    assert song is not None
    assert song.filename == "song1.mod"
    assert song.is_ready


def test_load_module_invalid(loader):
    song = loader.load_module("")
    assert song is None


@patch.object(QThreadPool, "start")
def test_load_modules(mock_start, loader, file_list):
    loader.load_modules()
    assert mock_start.call_count == len(file_list)


def test_song_finished_loading(loader):
    loader.songs_loaded = 1
    loader.songs_to_load = 2
    loader.song_finished_loading()
    assert loader.songs_loaded == 2


# @patch.object(LocalFileLoader, "all_songs_loaded")
# def test_song_finished_loading_all_songs_loaded(mock_all_songs_loaded, loader):
#     loader.songs_loaded = 1
#     loader.songs_to_load = 2
#     with patch.object(loader.all_songs_loaded, "emit") as mock_emit:
#         loader.song_finished_loading()
#         mock_emit.assert_called_once()


# @pytest.fixture
# def song():
#     return Song()


# @pytest.fixture
# def worker(song, backends, loader):
#     return LocalFileLoaderWorker(song, backends, loader)


# def test_run(worker, backends, song):
#     backend_instance = backends["backend1"].return_value
#     backend_instance.check_module.return_value = True

#     with patch.object(
#         worker.emitter.song_loaded, "emit"
#     ) as mock_song_loaded_emit, patch.object(
#         worker.emitter.song_info_retrieved, "emit"
#     ) as mock_song_info_retrieved_emit:
#         worker.run()
#         mock_song_loaded_emit.assert_called_once_with(song)
#         mock_song_info_retrieved_emit.assert_called_once_with(song)
#         backend_instance.cleanup.assert_called_once()
