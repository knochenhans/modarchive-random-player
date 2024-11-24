from settings_manager import SettingsManager


class PlayingSettings:
    def __init__(self, settings_manager: SettingsManager) -> None:
        self.settings_manager = settings_manager
        self.playing_mode = settings_manager.get_playing_mode()
        self.playing_source = settings_manager.get_playing_source()
        self.modarchive_source = settings_manager.get_modarchive_source()
        self.local_source = settings_manager.get_local_source()

    def save(self) -> None:
        self.settings_manager.set_playing_mode(self.playing_mode)
        self.settings_manager.set_playing_source(self.playing_source)
        self.settings_manager.set_modarchive_source(self.modarchive_source)
        self.settings_manager.set_local_source(self.local_source)
