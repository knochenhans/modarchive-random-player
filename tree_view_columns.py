from typing import TypedDict


class TreeViewColumn(TypedDict):
    name: str
    width: int
    order: int


tree_view_columns_dict: dict[str, TreeViewColumn] = {
    "playing": {"name": "", "width": 20, "order": 0},
    "filename": {"name": "Filename", "width": 150, "order": 2},
    "title": {"name": "Title", "width": 150, "order": 1},
    "duration": {"name": "Duration", "width": 100, "order": 3},
    "backend": {"name": "Backend", "width": 100, "order": 4},
    "path": {"name": "Path", "width": 200, "order": 5},
    "subsong": {"name": "Subsong", "width": 50, "order": 6},
    "artist": {"name": "Artist", "width": 150, "order": 7},
}
