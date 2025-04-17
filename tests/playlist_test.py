import pytest
from unittest.mock import Mock
from player_backends.Song import Song
from playlist.playlist import Playlist


@pytest.fixture
def song():
    song = Song()
    song.filename = "tests/knallhatten.mod"
    song.title = "Knallhatten"
    song.artist = "test artist"
    return song


@pytest.fixture
def playlist(song):
    return Playlist(name="Test Playlist", songs=[song])


# def test_add_song(playlist, song):
#     new_song = Mock(spec=Song)
#     playlist.add_song(new_song)
#     assert new_song in playlist.songs
#     assert len(playlist.songs) == 2


def test_remove_song(playlist, song):
    playlist.remove_song(song)
    assert song not in playlist.songs
    assert len(playlist.songs) == 0


# def test_move_song(playlist, song):
#     new_song = Mock(spec=Song)
#     playlist.add_song(new_song)
#     playlist.move_song(new_song, 0)
#     assert playlist.songs[0] == new_song
#     assert playlist.songs[1] == song


def test_get_next_song(playlist, song):
    new_song = Mock(spec=Song)
    playlist.add_song(new_song)
    next_song = playlist.get_next_song()
    assert next_song == new_song


def test_get_previous_song(playlist, song):
    new_song = Mock(spec=Song)
    playlist.add_song(new_song)
    playlist.get_next_song()  # Move to the next song
    previous_song = playlist.get_previous_song()
    assert previous_song == song


# def test_set_current_song(playlist, song):
#     new_song = Mock(spec=Song)
#     playlist.add_song(new_song)
#     playlist.set_current_song(new_song)
#     assert playlist.current_song_index == 1


def test_clear(playlist):
    playlist.clear()
    assert len(playlist.songs) == 0


def test_get_length(playlist):
    assert playlist.get_length() == 1


def test_to_json(playlist, tmp_path):
    json_file = tmp_path / "playlist.json"
    playlist.to_json(str(json_file))
    assert json_file.exists()


def test_from_json(playlist, tmp_path):
    json_file = tmp_path / "playlist.json"
    playlist.to_json(str(json_file))
    loaded_playlist = Playlist.from_json(str(json_file))
    assert loaded_playlist.name == playlist.name
    assert loaded_playlist.id == playlist.uuid
    assert loaded_playlist.current_song_index == playlist.current_song_index
    assert loaded_playlist.tab_index == playlist.tab_index
    assert len(loaded_playlist.songs) == len(playlist.songs)


def test_get_songs_from(playlist, song):
    new_song = Mock(spec=Song)
    playlist.add_song(new_song)
    songs_from = playlist.get_songs_from(1)
    assert songs_from == [new_song]
