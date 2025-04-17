from typing import Dict, List, Optional
from player_backends.Song import Song


class SongLibrary:
    def __init__(self):
        self.songs: Dict[str, Song] = {}

    def add_song(self, song: Song) -> None:
        self.songs[song.id] = song

    def get_song(self, song_id: str) -> Optional[Song]:
        return self.songs.get(song_id)

    def remove_song(self, song_id: str) -> None:
        if song_id in self.songs:
            del self.songs[song_id]

    def get_all_songs(self) -> List[Song]:
        return list(self.songs.values())
