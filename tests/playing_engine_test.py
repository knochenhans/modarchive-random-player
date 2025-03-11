import pytest
from unittest.mock import MagicMock
from player_backends.libgme.player_backend_libgme import PlayerBackendLibGME
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from playing_engine import (
    PlayingEngine,
    Song,
    PlayingSettings,
    PlaylistManager,
    QueueManager,
    UIManager,
    SettingsManager,
    WebHelper,
    AudioBackendPyAudio,
    PlayerThread,
    ModArchiveRandomModuleFetcherThread,
)


@pytest.fixture
def playing_engine():
    ui_manager = MagicMock(spec=UIManager)
    settings_manager = MagicMock(spec=SettingsManager)
    player_backends = {
        "LibUADE": PlayerBackendLibUADE,
        "LibOpenMPT": PlayerBackendLibOpenMPT,
        "LibGME": PlayerBackendLibGME,
    }
    return PlayingEngine(ui_manager, settings_manager, player_backends)


def test_get_current_song(playing_engine):
    song = Song()
    playing_engine.player_backend = MagicMock()
    playing_engine.player_backend.song = song
    assert playing_engine.get_current_song() == song


def test_play_module(playing_engine):
    song = Song()
    song.is_ready = True
    song.filename = "tests/knallhatten.mod"
    song.backend_name = "LibUADE"
    playing_engine.audio_backend = MagicMock(spec=AudioBackendPyAudio)
    playing_engine.play_module(song)
    assert playing_engine.player_thread is not None
    assert playing_engine.player_thread.isRunning()


# def test_play_pause(playing_engine):
#     playing_engine.player_thread = MagicMock(spec=PlayerThread)
#     playing_engine.player_thread.isRunning.return_value = True
#     playing_engine.play_pause()
#     playing_engine.player_thread.pause.assert_called_once()

# def test_stop(playing_engine):
#     playing_engine.player_thread = MagicMock(spec=PlayerThread)
#     playing_engine.stop()
#     playing_engine.player_thread.stop.assert_called_once()

# def test_check_favorite(playing_engine):
#     song = Song()
#     song.modarchive_id = 123
#     playing_engine.player_backend = MagicMock()
#     playing_engine.player_backend.song = song
#     playing_engine.web_helper.get_member_module_id_list.return_value = [123]
#     assert playing_engine.check_favorite(1)

# def test_play_queue(playing_engine):
#     song = Song()
#     playing_engine.queue_manager.pop_next_song.return_value = song
#     playing_engine.play_queue()
#     assert playing_engine.player_thread is not None

# def test_on_playing_finished(playing_engine):
#     playing_engine.play_next = MagicMock()
#     playing_engine.on_playing_finished()
#     playing_engine.play_next.assert_called_once()

# def test_play_next(playing_engine):
#     playing_engine.queue_manager.pop_next_song.return_value = None
#     playing_engine.play_next()
#     assert playing_engine.player_thread is None

# def test_play_previous(playing_engine):
#     playing_engine.playing_settings.playing_mode = "RANDOM"
#     playing_engine.history_playlist.get_previous_song.return_value = Song()
#     playing_engine.play_previous()
#     assert playing_engine.player_thread is not None

# def test_play_playlist_modules(playing_engine):
#     songs = [Song()]
#     playlist = MagicMock(spec=Playlist)
#     playing_engine.play_playlist_modules(songs, playlist)
#     assert playing_engine.player_thread is not None

# def test_populate_queue(playing_engine):
#     playing_engine.playing_settings.playing_source = "MODARCHIVE"
#     playing_engine.playing_settings.playing_mode = "RANDOM"
#     playing_engine.populate_queue()
#     assert len(playing_engine.queue_manager.queue) > 0

def test_get_random_module(playing_engine):
    song = Song()
    playing_engine.get_random_module(song)
    assert len(playing_engine.random_module_fetcher_threads) > 0

def test_on_random_module_fetched(playing_engine):
    song = Song()
    playing_engine.load_module = MagicMock()
    playing_engine.on_random_module_fetched(song)
    playing_engine.load_module.assert_called_once_with(song)

# def test_set_playing_mode(playing_engine):
#     new_mode = "LINEAR"
#     playing_engine.set_playing_mode(new_mode)
#     assert playing_engine.playing_settings.playing_mode == new_mode

# def test_set_playing_source(playing_engine):
#     new_source = "LOCAL"
#     playing_engine.set_playing_source(new_source)
#     assert playing_engine.playing_settings.playing_source == new_source

def test_set_modarchive_source(playing_engine):
    new_source = "ARTIST"
    playing_engine.set_modarchive_source(new_source)
    assert playing_engine.playing_settings.modarchive_source == new_source

def test_set_local_source(playing_engine):
    new_source = "PLAYLIST"
    playing_engine.set_local_source(new_source)
    assert playing_engine.playing_settings.local_source == new_source

def test_update_playing_mode(playing_engine):
    playing_engine.update_playing_mode()
    assert playing_engine.queue_manager.is_empty()

# def test_check_playing_mode(playing_engine):
#     playing_engine.ui_manager.get_artist_input.return_value = ""
#     playing_engine.playing_settings.modarchive_source = "ARTIST"
#     playing_engine.check_playing_mode()
#     assert playing_engine.playing_settings.modarchive_source == "ALL"

def test_load_module(playing_engine):
    song = Song()
    playing_engine.module_loader.load_modules = MagicMock()
    playing_engine.load_module(song)
    playing_engine.module_loader.load_modules.assert_called_once_with(song)

def test_on_module_loaded(playing_engine):
    song = Song()
    playing_engine.song_waiting_for_playback = song
    playing_engine.play_module = MagicMock()
    playing_engine.on_module_loaded(song)
    playing_engine.play_module.assert_called_once_with(song)

# def test_check_queue(playing_engine):
#     playing_engine.queue_manager.is_empty.return_value = True
#     playing_engine.playing_settings.playing_mode = "RANDOM"
#     playing_engine.check_queue()
#     assert len(playing_engine.queue_manager.queue) > 0

# def test_seek(playing_engine):
#     playing_engine.player_thread = MagicMock(spec=PlayerThread)
#     playing_engine.seek(100)
#     playing_engine.player_thread.seek.assert_called_once_with(100)

def test_close(playing_engine):
    playing_engine.stop = MagicMock()
    playing_engine.close()
    playing_engine.stop.assert_called_once()
