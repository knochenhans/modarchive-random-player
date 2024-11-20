from collections import deque
from typing import List, Optional

from loguru import logger

from player_backends.Song import Song
from playlist.playlist import Playlist


class QueueManager:
    def __init__(self, history_playlist: Playlist) -> None:
        self.queue: deque[Song] = deque()
        self.history_playlist = history_playlist

    def add_song(self, song: Song) -> None:
        self.queue.append(song)

    def add_songs(self, songs: List[Song]) -> None:
        self.queue.extend(songs)

    def set_queue(self, songs: List[Song]) -> None:
        self.queue = deque(songs)

    def update_song(self, song: Song) -> None:
        if song in self.queue:
            index = self.queue.index(song)
            self.queue[index] = song

    def pop_next_song(self) -> Optional[Song]:
        if self.queue:
            song = self.queue.popleft()
            self.history_playlist.add_song(song)
            
            if len(self.queue) > 0:
                logger.debug(
                    f'Playing "{song.title}" from queue, remaining: {len(self.queue)}'
                )
            else:
                logger.debug(f'Queue is empty.')
            return song
        return None

    def peek_next_song(self) -> Optional[Song]:
        return self.queue[0] if self.queue else None

    def prioritize_song(self, song: Song) -> None:
        if song in self.queue:
            self.queue.remove(song)
            self.queue.appendleft(song)

    def clear(self) -> None:
        self.queue.clear()

    def get_queue(self) -> List[Song]:
        return list(self.queue)

    def undo_last(self) -> None:
        if self.history_playlist.get_length() > 0:
            song = self.history_playlist.previous_song()

            if song:
                self.queue.appendleft(song)
                self.history_playlist.remove_song(song)

    def is_empty(self) -> bool:
        return not bool(self.queue)
