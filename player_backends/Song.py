import uuid
from dataclasses import dataclass, field
from player_backends.libuade.songinfo import Credits


@dataclass
class Song:
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    backend_name: str = ""
    modarchive_id: int = 0
    is_ready: bool = False
    artist: str = ""
    duration: int = 0
    container: str = ""
    container_long: str = ""
    date: str = ""
    extensions: str = ""
    formatname: str = ""
    message: str = ""
    message_raw: str = ""
    md5: str = ""
    modulebytes: int = 0
    originaltype: str = ""
    originaltype_long: str = ""
    playername: str = ""
    playerfname: str = ""
    sha1: str = ""
    title: str = ""
    tracker: str = ""
    type: str = ""
    type_long: str = ""
    warnings: str = ""
    credits: Credits = field(
        default_factory=lambda: Credits(
            song_title="",
            artistname="",
            file_length="",
            file_name="",
            file_prefix="",
            max_positions=0,
            modulename="",
            specialinfo="",
            instruments=[],
        )
    )
