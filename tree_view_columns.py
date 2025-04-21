from typing import TypedDict


class TreeViewColumn(TypedDict):
    width: int
    order: int
    visible: bool


tree_view_columns_dict: dict[str, TreeViewColumn] = {
    "id": {"width": 50, "order": 1, "visible": False},
    "playing": {"width": 20, "order": 0, "visible": True},
    "filename": {"width": 150, "order": 2, "visible": True},
    "title": {"width": 150, "order": 3, "visible": True},
    "duration": {"width": 100, "order": 4, "visible": True},
    "backend": {"width": 100, "order": 5, "visible": True},
    "path": {"width": 200, "order": 6, "visible": True},
    "subsong": {"width": 50, "order": 7, "visible": False},
    "artist": {"width": 150, "order": 8, "visible": True},
    "player": {"width": 100, "order": 9, "visible": True},
}
