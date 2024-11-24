import ctypes
from ctypes.util import find_library
import sys

libgme_path = find_library("gme")

try:
    libgme = ctypes.CDLL(libgme_path, mode=ctypes.RTLD_GLOBAL)
except OSError as e:
    sys.exit(f"Failed to load libgme: {e}")

# Define ctypes structures and types
class Music_Emu(ctypes.Structure):
    pass

class gme_info_t(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_int),
        ("intro_length", ctypes.c_int),
        ("loop_length", ctypes.c_int),
        ("play_length", ctypes.c_int),
        ("fade_length", ctypes.c_int),
        ("i5", ctypes.c_int),
        ("i6", ctypes.c_int),
        ("i7", ctypes.c_int),
        ("i8", ctypes.c_int),
        ("i9", ctypes.c_int),
        ("i10", ctypes.c_int),
        ("i11", ctypes.c_int),
        ("i12", ctypes.c_int),
        ("i13", ctypes.c_int),
        ("i14", ctypes.c_int),
        ("i15", ctypes.c_int),
        ("system", ctypes.c_char_p),
        ("game", ctypes.c_char_p),
        ("song", ctypes.c_char_p),
        ("author", ctypes.c_char_p),
        ("copyright", ctypes.c_char_p),
        ("comment", ctypes.c_char_p),
        ("dumper", ctypes.c_char_p),
        ("s7", ctypes.c_char_p),
        ("s8", ctypes.c_char_p),
        ("s9", ctypes.c_char_p),
        ("s10", ctypes.c_char_p),
        ("s11", ctypes.c_char_p),
        ("s12", ctypes.c_char_p),
        ("s13", ctypes.c_char_p),
        ("s14", ctypes.c_char_p),
        ("s15", ctypes.c_char_p),
    ]

class gme_equalizer_t(ctypes.Structure):
    _fields_ = [
        ("treble", ctypes.c_double),
        ("bass", ctypes.c_double),
        ("d2", ctypes.c_double),
        ("d3", ctypes.c_double),
        ("d4", ctypes.c_double),
        ("d5", ctypes.c_double),
        ("d6", ctypes.c_double),
        ("d7", ctypes.c_double),
        ("d8", ctypes.c_double),
        ("d9", ctypes.c_double),
    ]

gme_err_t = ctypes.c_char_p
gme_type_t = ctypes.c_void_p
gme_reader_t = ctypes.CFUNCTYPE(gme_err_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int)
gme_user_cleanup_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

# Define ctypes wrappers for the relevant libgme functions
class LibGME:
    def __init__(self, library_path: str = "libgme.so"):
        """
        Initialize the ctypes interface to the Game Music Emu library.

        Args:
            library_path (str): Path to the Game Music Emu library. Defaults to "libgme.so".

        Attributes:
            lib (ctypes.CDLL): The loaded Game Music Emu library.

        Function Prototypes:
            gme_open_file: Create emulator and load game music file/data into it. Sets *out to new emulator.
            gme_track_count: Number of tracks available.
            gme_start_track: Start a track, where 0 is the first track.
            gme_play: Generate 'count' 16-bit signed samples into 'out'. Output is in stereo.
            gme_delete: Finish using emulator and free memory.
            gme_set_fade: Set time to start fading track out. Once fade ends track_ended() returns true.
            gme_set_fade_msecs: Set fade time in milliseconds.
            gme_set_autoload_playback_limit: Automatically load track length metadata and terminate playback once the track length has been reached.
            gme_autoload_playback_limit: Check if autoload playback limit is enabled.
            gme_track_ended: Check if a track has reached its end.
            gme_tell: Number of milliseconds played since beginning of track.
            gme_tell_samples: Number of samples generated since beginning of track.
            gme_seek: Seek to new time in track.
            gme_seek_samples: Seek to new sample position in track.
            gme_warning: Most recent warning string, or NULL if none.
            gme_load_m3u: Load m3u playlist file.
            gme_clear_playlist: Clear any loaded m3u playlist and any internal playlist.
            gme_track_info: Get information for a particular track.
            gme_free_info: Free track information.
            gme_set_stereo_depth: Adjust stereo echo depth.
            gme_ignore_silence: Disable automatic end-of-track detection and skipping of silence at beginning.
            gme_set_tempo: Adjust song tempo.
            gme_voice_count: Number of voices used by currently loaded file.
            gme_voice_name: Name of voice.
            gme_mute_voice: Mute/unmute voice.
            gme_mute_voices: Set muting state of all voices at once using a bit mask.
            gme_disable_echo: Disable/Enable echo effect for SPC files.
            gme_equalizer: Get current frequency equalizer parameters.
            gme_set_equalizer: Change frequency equalizer parameters.
            gme_enable_accuracy: Enable/disable most accurate sound emulation options.
            gme_type: Type of this emulator.
            gme_type_list: Pointer to array of all music types.
            gme_type_system: Name of game system for this music file type.
            gme_type_multitrack: Check if this music file type supports multiple tracks.
            gme_multi_channel: Check if the pcm output will have all 8 voices rendered to their individual stereo channel.
            gme_open_data: Same as gme_open_file(), but uses file data already in memory.
            gme_identify_header: Determine likely game music type based on first four bytes of file.
            gme_identify_extension: Get corresponding music type for file path or extension.
            gme_type_extension: Get typical file extension for a given music type.
            gme_identify_file: Determine file type based on file's extension or header.
            gme_new_emu: Create new emulator and set sample rate.
            gme_new_emu_multi_channel: Create new multichannel emulator and set sample rate.
            gme_load_file: Load music file into emulator.
            gme_load_data: Load music file from memory into emulator.
            gme_load_tracks: Load multiple single-track music files from memory into emulator.
            gme_fixed_track_count: Return the fixed track count of an emu file type.
            gme_load_custom: Load music file using custom data reader function.
            gme_load_m3u_data: Load m3u playlist file from memory.
            gme_set_user_data: Set pointer to data you want to associate with this emulator.
            gme_user_data: Get pointer to data associated with this emulator.
            gme_set_user_cleanup: Register cleanup function to be called when deleting emulator.
        """
        self.lib = ctypes.CDLL(library_path)

        # Function prototypes
        self.lib.gme_open_file.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.POINTER(Music_Emu)),
            ctypes.c_int,
        ]
        self.lib.gme_open_file.restype = gme_err_t

        self.lib.gme_track_count.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_track_count.restype = ctypes.c_int

        self.lib.gme_start_track.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
        ]
        self.lib.gme_start_track.restype = gme_err_t

        self.lib.gme_play.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_short),
        ]
        self.lib.gme_play.restype = gme_err_t

        self.lib.gme_delete.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_delete.restype = None

        self.lib.gme_set_fade.argtypes = [ctypes.POINTER(Music_Emu), ctypes.c_int]
        self.lib.gme_set_fade.restype = None

        self.lib.gme_set_fade_msecs.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.lib.gme_set_fade_msecs.restype = None

        self.lib.gme_set_autoload_playback_limit.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
        ]
        self.lib.gme_set_autoload_playback_limit.restype = None

        self.lib.gme_autoload_playback_limit.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_autoload_playback_limit.restype = ctypes.c_int

        self.lib.gme_track_ended.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_track_ended.restype = ctypes.c_int

        self.lib.gme_tell.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_tell.restype = ctypes.c_int

        self.lib.gme_tell_samples.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_tell_samples.restype = ctypes.c_int

        self.lib.gme_seek.argtypes = [ctypes.POINTER(Music_Emu), ctypes.c_int]
        self.lib.gme_seek.restype = gme_err_t

        self.lib.gme_seek_samples.argtypes = [ctypes.POINTER(Music_Emu), ctypes.c_int]
        self.lib.gme_seek_samples.restype = gme_err_t

        self.lib.gme_warning.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_warning.restype = ctypes.c_char_p

        self.lib.gme_load_m3u.argtypes = [ctypes.POINTER(Music_Emu), ctypes.c_char_p]
        self.lib.gme_load_m3u.restype = gme_err_t

        self.lib.gme_clear_playlist.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_clear_playlist.restype = None

        self.lib.gme_track_info.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.POINTER(ctypes.POINTER(gme_info_t)),
            ctypes.c_int,
        ]
        self.lib.gme_track_info.restype = gme_err_t

        self.lib.gme_free_info.argtypes = [ctypes.POINTER(gme_info_t)]
        self.lib.gme_free_info.restype = None

        self.lib.gme_set_stereo_depth.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_double,
        ]
        self.lib.gme_set_stereo_depth.restype = None

        self.lib.gme_ignore_silence.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
        ]
        self.lib.gme_ignore_silence.restype = None

        self.lib.gme_set_tempo.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_double,
        ]
        self.lib.gme_set_tempo.restype = None

        self.lib.gme_voice_count.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_voice_count.restype = ctypes.c_int

        self.lib.gme_voice_name.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
        ]
        self.lib.gme_voice_name.restype = ctypes.c_char_p

        self.lib.gme_mute_voice.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.lib.gme_mute_voice.restype = None

        self.lib.gme_mute_voices.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
        ]
        self.lib.gme_mute_voices.restype = None

        self.lib.gme_disable_echo.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
        ]
        self.lib.gme_disable_echo.restype = None

        self.lib.gme_equalizer.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.POINTER(gme_equalizer_t),
        ]
        self.lib.gme_equalizer.restype = None

        self.lib.gme_set_equalizer.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.POINTER(gme_equalizer_t),
        ]
        self.lib.gme_set_equalizer.restype = None

        self.lib.gme_enable_accuracy.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_int,
        ]
        self.lib.gme_enable_accuracy.restype = None

        self.lib.gme_type.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_type.restype = gme_type_t

        self.lib.gme_type_list.argtypes = []
        self.lib.gme_type_list.restype = ctypes.POINTER(gme_type_t)

        self.lib.gme_type_system.argtypes = [gme_type_t]
        self.lib.gme_type_system.restype = ctypes.c_char_p

        self.lib.gme_type_multitrack.argtypes = [gme_type_t]
        self.lib.gme_type_multitrack.restype = ctypes.c_int

        self.lib.gme_multi_channel.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_multi_channel.restype = ctypes.c_int

        self.lib.gme_open_data.argtypes = [
            ctypes.c_void_p,
            ctypes.c_long,
            ctypes.POINTER(ctypes.POINTER(Music_Emu)),
            ctypes.c_int,
        ]
        self.lib.gme_open_data.restype = gme_err_t

        self.lib.gme_identify_header.argtypes = [ctypes.c_void_p]
        self.lib.gme_identify_header.restype = ctypes.c_char_p

        self.lib.gme_identify_extension.argtypes = [ctypes.c_char_p]
        self.lib.gme_identify_extension.restype = gme_type_t

        self.lib.gme_type_extension.argtypes = [gme_type_t]
        self.lib.gme_type_extension.restype = ctypes.c_char_p

        self.lib.gme_identify_file.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(gme_type_t),
        ]
        self.lib.gme_identify_file.restype = gme_err_t

        self.lib.gme_new_emu.argtypes = [gme_type_t, ctypes.c_int]
        self.lib.gme_new_emu.restype = ctypes.POINTER(Music_Emu)

        self.lib.gme_new_emu_multi_channel.argtypes = [gme_type_t, ctypes.c_int]
        self.lib.gme_new_emu_multi_channel.restype = ctypes.POINTER(Music_Emu)

        self.lib.gme_load_file.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_char_p,
        ]
        self.lib.gme_load_file.restype = gme_err_t

        self.lib.gme_load_data.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_void_p,
            ctypes.c_long,
        ]
        self.lib.gme_load_data.restype = gme_err_t

        self.lib.gme_load_tracks.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_long),
            ctypes.c_int,
        ]
        self.lib.gme_load_tracks.restype = gme_err_t

        self.lib.gme_fixed_track_count.argtypes = [gme_type_t]
        self.lib.gme_fixed_track_count.restype = ctypes.c_int

        self.lib.gme_load_custom.argtypes = [
            ctypes.POINTER(Music_Emu),
            gme_reader_t,
            ctypes.c_long,
            ctypes.c_void_p,
        ]
        self.lib.gme_load_custom.restype = gme_err_t

        self.lib.gme_load_m3u_data.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_void_p,
            ctypes.c_long,
        ]
        self.lib.gme_load_m3u_data.restype = gme_err_t

        self.lib.gme_set_user_data.argtypes = [
            ctypes.POINTER(Music_Emu),
            ctypes.c_void_p,
        ]
        self.lib.gme_set_user_data.restype = None

        self.lib.gme_user_data.argtypes = [ctypes.POINTER(Music_Emu)]
        self.lib.gme_user_data.restype = ctypes.c_void_p

        self.lib.gme_set_user_cleanup.argtypes = [
            ctypes.POINTER(Music_Emu),
            gme_user_cleanup_t,
        ]
        self.lib.gme_set_user_cleanup.restype = None

def handle_error(error: ctypes.c_char_p):
    if error:
        raise RuntimeError(error.decode("utf-8"))
