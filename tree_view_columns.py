from typing import TypedDict


class TreeViewColumn(TypedDict):
    name: str
    width: int
    order: int
    visible: bool


tree_view_columns_dict: dict[str, TreeViewColumn] = {
    "playing": {"name": "", "width": 20, "order": 0, "visible": True},
    "id": {"name": "ID", "width": 50, "order": 1, "visible": False},
    "filename": {"name": "Filename", "width": 150, "order": 2, "visible": True},
    "title": {"name": "Title", "width": 150, "order": 3, "visible": True},
    "duration": {"name": "Duration", "width": 100, "order": 4, "visible": True},
    "backend": {"name": "Backend", "width": 100, "order": 5, "visible": True},
    "path": {"name": "Path", "width": 200, "order": 6, "visible": True},
    "subsong": {"name": "Subsong", "width": 50, "order": 7, "visible": False},
    "artist": {"name": "Artist", "width": 150, "order": 8, "visible": True},
    "player": {"name": "Player", "width": 100, "order": 9, "visible": True},
}
