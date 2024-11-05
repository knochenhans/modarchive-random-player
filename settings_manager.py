from PySide6.QtCore import QSettings
from current_playing_mode import CurrentPlayingMode

class SettingsManager:
    def __init__(self, settings: QSettings):
        self.settings = settings

    def get_member_id(self):
        return str(self.settings.value("member_id", ""))
    
    def set_member_id(self, member_id: str):
        self.settings.setValue("member_id", member_id)

    def get_artist(self) -> str:
        return str(self.settings.value("artist", ""))
    
    def set_artist(self, artist: str) -> None:
        self.settings.setValue("artist", artist)
    
    def get_current_playing_mode(self) -> CurrentPlayingMode:
        return CurrentPlayingMode(self.settings.value("current_playing_mode", 0, type=int))
    
    def set_current_playing_mode(self, mode: CurrentPlayingMode) -> None:
        self.settings.setValue("current_playing_mode", mode.value)
