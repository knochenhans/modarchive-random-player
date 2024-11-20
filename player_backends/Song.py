import uuid
from dataclasses import dataclass, field
from player_backends.libuade.songinfo import Credits
import json


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
    subsongs: int = 0
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

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> "Song":
        data = json.loads(json_str)
        # data["credits"] = Credits(**data["credits"])
        return cls(**data)
