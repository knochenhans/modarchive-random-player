from collections import deque
from typing import List, Optional

from player_backends.Song import Song


class QueueManager:
    def __init__(self) -> None:
        self.queue: deque[Song] = deque()
        self.history: List[Song] = []

    def add_song(self, song: Song) -> None:
        self.queue.append(song)

    def add_songs(self, songs: List[Song]) -> None:
        self.queue.extend(songs)

    def update_song(self, song: Song) -> None:
        if song in self.queue:
            index = self.queue.index(song)
            self.queue[index] = song

    def pop_next_song(self) -> Optional[Song]:
        if self.queue:
            song = self.queue.popleft()
            self.history.append(song)
            return song
        return None

    def peek_next_song(self) -> Optional[Song]:
        return self.queue[0] if self.queue else None

    def prioritize_song(self, song: Song) -> None:
        if song in self.queue:
            self.queue.remove(song)
            self.queue.appendleft(song)

    def clear_queue(self) -> None:
        self.queue.clear()

    def get_queue(self) -> List[Song]:
        return list(self.queue)

    def undo_last(self) -> None:
        if self.history:
            self.queue.appendleft(self.history.pop())

    def is_empty(self) -> bool:
        return not bool(self.queue)
