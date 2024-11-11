from PySide6.QtCore import QSettings
from current_playing_mode import CurrentPlayingMode


class SettingsManager:
    def __init__(self, settings: QSettings) -> None:
        self.settings = settings

    def get_member_id(self) -> int:
        member_id = str(self.settings.value("member_id", 0))
        return  int(member_id)

    def set_member_id(self, member_id: str) -> None:
        self.settings.setValue("member_id", member_id)

    def get_artist(self) -> str:
        return str(self.settings.value("artist", ""))

    def set_artist(self, artist: str) -> None:
        self.settings.setValue("artist", artist)

    def get_current_playing_mode(self) -> CurrentPlayingMode:
        return CurrentPlayingMode(
            self.settings.value("current_playing_mode", CurrentPlayingMode.RANDOM, type=int)
        )

    def set_current_playing_mode(self, mode: CurrentPlayingMode) -> None:
        self.settings.setValue("current_playing_mode", mode.value)

    def close(self) -> None:
        self.settings.sync()

    def get_audio_buffer(self) -> int:
        result = str(self.settings.value("audio_buffer", 8192))

        return int(result)

    def set_audio_buffer(self, buffer_size: int) -> None:
        self.settings.setValue("audio_buffer", buffer_size)

    def get_local_folder(self) -> str:
        return str(self.settings.value("local_folder", ""))

    def set_local_folder(self, folder: str) -> None:
        self.settings.setValue("local_folder", folder)
