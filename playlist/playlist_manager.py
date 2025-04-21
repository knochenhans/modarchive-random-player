import json
import os
from typing import List, Optional

from appdirs import user_data_dir
from loguru import logger

from playlist.playlist import Playlist


class PlaylistManager:
    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self.playlists_path = os.path.join(user_data_dir(self.app_name), "playlist")
        os.makedirs(self.playlists_path, exist_ok=True)
        self.playlists: List[Playlist] = []

    def add_playlist(self, playlist: Playlist) -> None:
        self.playlists.append(playlist)
        logger.info(f"Added playlist: {playlist.name}")

    def delete_playlist(self, index: int) -> None:
        if 0 <= index < len(self.playlists):
            playlist_name = self.playlists[index].name
            del self.playlists[index]
            logger.info(f"Deleted playlist: {playlist_name}")
        else:
            logger.warning("Invalid playlist index to delete.")

    def load_playlists(self) -> None:
        self.playlists.clear()
        for filename in sorted(os.listdir(self.playlists_path)):
            if filename.endswith(".json"):
                playlist_file_path = os.path.join(self.playlists_path, filename)
                playlist = self.load_playlist(playlist_file_path)
                if playlist:
                    self.playlists.append(playlist)
                    logger.info(f"Loaded playlist: {playlist.name}")

    def save_playlists(self) -> None:
        # Remove existing files in the playlists directory
        for filename in os.listdir(self.playlists_path):
            file_path = os.path.join(self.playlists_path, filename)
            if os.path.isfile(file_path) and filename.endswith(".json"):
                os.remove(file_path)

        # Save current playlists
        for i, playlist in enumerate(self.playlists):
            playlist_file_path = os.path.join(self.playlists_path, f"{i}.json")
            self.save_playlist(playlist, playlist_file_path)

    def load_playlist(self, file_path: str) -> Optional[Playlist]:
        try:
            with open(file_path, "r") as f:
                playlist_data = json.load(f)
                return Playlist(
                    id=playlist_data["id"],
                    name=playlist_data["name"],
                    items=playlist_data["data"],
                )
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.error(f"Failed to load playlist from {file_path}: {e}")
            return None

    def save_playlist(self, playlist: Playlist, file_path: str) -> None:
        try:
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "id": playlist.id,
                        "name": playlist.name,
                        "data": playlist.get_items(),
                    },
                    f,
                    indent=4,
                )
            logger.info(f"Playlist saved to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save playlist to {file_path}: {e}")

    def reorder_playlists(self, from_index: int, to_index: int) -> None:
        if 0 <= from_index < len(self.playlists) and 0 <= to_index < len(
            self.playlists
        ):
            playlist = self.playlists.pop(from_index)
            self.playlists.insert(to_index, playlist)
            logger.info(f"Reordered playlists: {from_index} -> {to_index}")
        else:
            logger.warning("Invalid indices for playlist reordering.")
