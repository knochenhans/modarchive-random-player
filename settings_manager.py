import os
from PySide6.QtCore import QSettings
from platformdirs import user_config_dir
from playing_modes import LocalSource, ModArchiveSource, PlayingMode, PlayingSource


class SettingsManager:
    def __init__(self, settings: QSettings) -> None:
        self.settings = settings
        config_dir = user_config_dir(self.get_app_name())

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

    def get_app_name(self) -> str:
        return str(self.settings.applicationName())

    def get_organization_name(self) -> str:
        return str(self.settings.organizationName())

    def get_member_id(self) -> int:
        member_id = str(self.settings.value("member_id", 0))
        return int(member_id)

    def set_member_id(self, member_id: str) -> None:
        self.settings.setValue("member_id", member_id)

    def get_artist(self) -> str:
        return str(self.settings.value("artist", ""))

    def set_artist(self, artist: str) -> None:
        self.settings.setValue("artist", artist)

    # Playing settings

    def get_playing_mode(self) -> PlayingMode:
        return PlayingMode(
            self.settings.value("playing_mode", PlayingMode.RANDOM, type=int)
        )

    def set_playing_mode(self, mode: PlayingMode) -> None:
        self.settings.setValue("playing_mode", mode.value)

    def get_playing_source(self) -> PlayingSource:
        return PlayingSource(
            self.settings.value("playing_source", PlayingSource.MODARCHIVE, type=int)
        )

    def set_playing_source(self, source: PlayingSource) -> None:
        self.settings.setValue("playing_source", source.value)

    def get_modarchive_source(self) -> ModArchiveSource:
        return ModArchiveSource(
            self.settings.value("modarchive_source", ModArchiveSource.ALL, type=int)
        )

    def set_modarchive_source(self, source: ModArchiveSource) -> None:
        self.settings.setValue("modarchive_source", source.value)

    def get_local_source(self) -> LocalSource:
        return LocalSource(
            self.settings.value("local_source", LocalSource.PLAYLIST, type=int)
        )

    def set_local_source(self, source: LocalSource) -> None:
        self.settings.setValue("local_source", source)

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

    def set_last_folder(self, folder: str) -> None:
        self.settings.setValue("last_folder", folder)

    def get_last_folder(self) -> str:
        return str(self.settings.value("last_folder", ""))