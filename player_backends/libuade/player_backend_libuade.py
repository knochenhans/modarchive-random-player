import ctypes

from player_backends.libuade import songinfo
from player_backends.libuade.ctypes_classes import (
    UADE_BYTES_PER_FRAME,
    UADE_MAX_MESSAGE_SIZE,
    UADE_NOTIFICATION_TYPE,
    UADE_SEEK_MODE,
    uade_config,
    uade_event,
    uade_event_data,
    uade_event_songend,
    uade_event_union,
    uade_notification,
    uade_song_info,
    uade_state,
    uade_subsong_info,
)
from player_backends.libuade.ctypes_functions import libuade, libc
from loguru import logger

from player_backends.player_backend import PlayerBackend


class PlayerBackendLibUADE(PlayerBackend):
    def __init__(self, name: str = "LibUADE") -> None:
        super().__init__(name)
        self.state_ptr: ctypes._Pointer[uade_state] = libuade.uade_new_state(None)
        self.config_ptr: ctypes._Pointer[uade_config] = libuade.uade_new_config()
        # self.config = ctypes.cast(libuade.uade_new_config(), ctypes.POINTER(uade_config))

        logger.debug("PlayerBackendUADE initialized")

    def check_module(self) -> bool:
        self.module_size = ctypes.c_size_t()
        ret = libuade.uade_read_file(
            ctypes.byref(self.module_size), str.encode(self.song.filename)
        )

        if not ret:
            error_message = f"Could not read file {self.song.filename}"
            logger.error(error_message)
            return False

        ret = libuade.uade_play_from_buffer(
            None, ret, self.module_size, -1, self.state_ptr
        )

        if ret < 1:
            logger.warning(f"LibUADE is unable to play {self.song.filename}")
            return False

        return True

    def prepare_playing(self, subsong_nr: int = -1) -> None:
        self.state_ptr = libuade.uade_new_state(None)

        if not self.state_ptr:
            raise Exception("uade_state is NULL")

        size = ctypes.c_size_t()

        ret = libuade.uade_read_file(ctypes.byref(size), str.encode(self.song.filename))

        if not ret:
            raise ValueError(f"Can not read file {self.song.filename}")

        match libuade.uade_play(
            str.encode(self.song.filename), subsong_nr, self.state_ptr
        ):
            case -1:
                # Fatal error
                libuade.uade_cleanup_state(self.state_ptr)
                raise RuntimeError
            # case 0:
            #     # Not playable
            #     raise ValueError
            # case 1:
            #     self.stream = self.pyaudio.open(
            #         format=self.pyaudio.get_format_from_width(2),
            #         channels=2,
            #         rate=samplerate,
            #         output=True,
            #     )

    def retrieve_song_info(self) -> None:
        info = libuade.uade_get_song_info(self.state_ptr).contents

        self.song.credits = songinfo.get_credits(self.song.filename)
        self.song.formatname = info.formatname.decode("cp1251")
        self.song.extensions = info.detectioninfo.ext.decode("cp1251")
        self.song.modulebytes = info.modulebytes
        self.song.title = info.modulename.decode("cp1251")
        # self.song.title = self.song.credits["song_title"]
        # self.song.md5 = info.modulemd5.decode("cp1251")
        self.song.playerfname = info.playerfname.decode("cp1251")
        self.song.playername = info.playername.decode("cp1251")
        self.song.type = info.formatname.decode("cp1251")
        self.song.duration = int(self.get_module_length())

        subsongs: uade_subsong_info = info.subsongs

        self.song.subsongs = subsongs.max

        self.song.message = "\n".join(
            instrument["name"] for instrument in self.song.credits["instruments"]
        )

        self.calculate_checksums()

    def get_module_length(self) -> float:
        info = libuade.uade_get_song_info(self.state_ptr).contents
        bytes_per_second = UADE_BYTES_PER_FRAME * libuade.uade_get_sampling_rate(
            self.state_ptr
        )
        deciseconds = (info.subsongbytes * 10) // bytes_per_second

        if info.duration > 0:
            return info.duration
        else:
            return deciseconds / 10.0

    def get_position_seconds(self) -> float:
        info = libuade.uade_get_song_info(self.state_ptr).contents
        bytes_per_second = UADE_BYTES_PER_FRAME * libuade.uade_get_sampling_rate(
            self.state_ptr
        )
        deciseconds = (info.subsongbytes * 10) // bytes_per_second

        return deciseconds / 10.0

    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        # debugpy.debug_this_thread()
        buf = (ctypes.c_char * buffersize)()
        n = uade_notification()

        nbytes = libuade.uade_read(buf, ctypes.sizeof(buf), self.state_ptr)

        while libuade.uade_read_notification(n, self.state_ptr):
            try:
                if not self.handle_notification(n):
                    break
            except EOFError as e:
                logger.info("handle_notification: {}", e)
                raise e
            except RuntimeError as e:
                logger.error("handle_notification: {}", e)
                raise e
            except RuntimeWarning as e:
                logger.warning("handle_notification: {}", e)
            libuade.uade_cleanup_notification(n)

        if nbytes < 0:
            raise RuntimeError("Playback error")

        if nbytes == 0:
            logger.info("Song end")

        return nbytes, bytes(buf)

    def handle_notification(self, n: uade_notification) -> bool:
        if n.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_MESSAGE:
            logger.info(f"Amiga message: {n.uade_notification_union.msg}")
        elif n.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_SONG_END:
            if n.uade_notification_union.song_end.happy:
                # Subsong ended
                self.current_subsong += 1
                self.notify_subsong_changed(self.current_subsong, self.song.subsongs)
                logger.info("Sub song end")
                return False
            else:
                logger.error("Bad Song end")
        else:
            raise RuntimeWarning("Unknown notification type from libuade")
        return True

    def get_event(self) -> uade_event:
        charbytes256 = (ctypes.c_char * 256)()
        event_songend = uade_event_songend(
            happy=0, stopnow=0, tailbytes=0, reason=bytes(charbytes256)
        )
        a = (ctypes.c_ubyte * UADE_MAX_MESSAGE_SIZE)()
        size = ctypes.c_size_t()
        event_data = uade_event_data(size=size, data=a)
        si = uade_subsong_info(0, 0, 0, 0)
        charbytes1024 = (ctypes.c_char * 1024)()
        event_union = uade_event_union(
            data=event_data,
            msg=bytes(charbytes1024),
            songend=event_songend,
            subsongs=si,
        )
        event = uade_event(type=0, uade_event_union=event_union)
        e = libuade.uade_get_event(ctypes.byref(event), self.state_ptr)
        logger.info("event type: {}", event.type)
        return event

    def free_module(self) -> None:
        if self.state_ptr:
            libuade.uade_cleanup_state(self.state_ptr)
            self.state_ptr = libuade.uade_new_state(None)
            logger.info("UADE instance deleted")

    def seek(self, position: int) -> None:
        songinfo: uade_song_info = libuade.uade_get_song_info(self.state_ptr).contents

        if (
            libuade.uade_seek(
                UADE_SEEK_MODE.UADE_SEEK_SUBSONG_RELATIVE,
                position,
                songinfo.subsongs.cur,
                self.state_ptr,
            )
            != 0
        ):
            logger.error("Seeking failed")

    def cleanup(self) -> None:
        if self.state_ptr:
            libuade.uade_cleanup_state(self.state_ptr)

        if self.config_ptr:
            libc.free(self.config_ptr)


        logger.info("UADE cleaned up")
