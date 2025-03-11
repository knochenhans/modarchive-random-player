import pytest
from collections import deque
from unittest.mock import Mock
from player_backends.Song import Song
from playlist.playlist import Playlist
from queue_manager import QueueManager


@pytest.fixture
def history_playlist():
    return Mock(spec=Playlist)


@pytest.fixture
def queue_manager(history_playlist):
    return QueueManager(history_playlist)


@pytest.fixture
def song():
    return Mock(spec=Song)


def test_add_song(queue_manager, song):
    queue_manager.add_song(song)
    assert song in queue_manager.queue


def test_add_songs(queue_manager, song):
    songs = [song, song]
    queue_manager.add_songs(songs)
    assert list(queue_manager.queue) == songs


def test_set_queue(queue_manager, song):
    songs = [song, song]
    queue_manager.set_queue(songs)
    assert list(queue_manager.queue) == songs


# def test_update_song(queue_manager, song):
#     queue_manager.add_song(song)
#     updated_song = Mock(spec=Song)
#     queue_manager.update_song(updated_song)
#     assert updated_song in queue_manager.queue


def test_pop_next_song(queue_manager, song, history_playlist):
    queue_manager.add_song(song)
    next_song = queue_manager.pop_next_song()
    assert next_song == song
    history_playlist.add_song.assert_called_once_with(song)
    assert history_playlist.current_song_index == 0


def test_peek_next_song(queue_manager, song):
    queue_manager.add_song(song)
    assert queue_manager.peek_next_song() == song


def test_prioritize_song(queue_manager, song):
    queue_manager.add_song(song)
    queue_manager.prioritize_song(song)
    assert queue_manager.queue[0] == song


def test_clear(queue_manager, song):
    queue_manager.add_song(song)
    queue_manager.clear()
    assert len(queue_manager.queue) == 0


def test_get_queue(queue_manager, song):
    queue_manager.add_song(song)
    assert queue_manager.get_queue() == [song]


def test_is_empty(queue_manager):
    assert queue_manager.is_empty()
    queue_manager.add_song(Mock(spec=Song))
    assert not queue_manager.is_empty()
