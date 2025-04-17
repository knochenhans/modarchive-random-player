import darkdetect
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle
from typing import Dict, Optional
from settings.settings import Settings


class Icons:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Icons, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        settings: Settings,
        style: Optional[QStyle] = None    ):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self.icons: Dict[str, str] = {}
        self.pixmap_icons: Dict[str, QIcon] = {}
        self.base_path = "data/icons"

        if settings and style:
            dark_theme = darkdetect.isDark() or settings.get("dark_theme", False)

            if dark_theme:
                self.icons["star_empty"] = f"{self.base_path}/star_empty_light.png"
                self.icons["star_full"] = f"{self.base_path}/star_full_light.png"
            else:
                self.icons["star_empty"] = f"{self.base_path}/star_empty.png"
                self.icons["star_full"] = f"{self.base_path}/star_full.png"

            self.pixmap_icons["application_icon"] = style.standardIcon(
                QStyle.StandardPixmap.SP_MediaPlay
            )
            self.pixmap_icons["play"] = self.pixmap_icons["application_icon"]
            self.pixmap_icons["pause"] = style.standardIcon(
                QStyle.StandardPixmap.SP_MediaPause
            )
            self.pixmap_icons["stop"] = style.standardIcon(
                QStyle.StandardPixmap.SP_MediaStop
            )
            self.pixmap_icons["forward"] = style.standardIcon(
                QStyle.StandardPixmap.SP_MediaSkipForward
            )
            self.pixmap_icons["backward"] = style.standardIcon(
                QStyle.StandardPixmap.SP_MediaSkipBackward
            )
