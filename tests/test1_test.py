from typing import Dict
import unittest

from player_backends.Song import Song
from player_backends.libopenmpt.player_backend_libopenmpt import PlayerBackendLibOpenMPT
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.player_backend import PlayerBackend


class LoaderTest(unittest.TestCase):

    def test_1(self):
        player_backends: Dict[str, type[PlayerBackend]] = {
            "LibUADE": PlayerBackendLibUADE,
            "LibOpenMPT": PlayerBackendLibOpenMPT,
        }

        song = Song()

        # module_loader = LocalLoader(player_backends)
        # module_loader.files = ["knallhatten.mod"]
        # module_loader.load_modules(song)
        # module_loader.module_loaded.connect(self.add_song)

        self.assertEqual("", "")

    # def add_song(self, song: Song) -> None:
    #     self.assertEqual(song.filename, "knallhatten.mod")


if __name__ == "__main__":
    unittest.main()
