import uuid
from typing import Any, Dict, List, Optional


class Playlist:
    def __init__(
        self, id: Optional[str] = None, name: Optional[str] = None, items: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.items = items or []

    def add_item(self, item: Dict[str, Any]) -> None:
        self.items.append(item)

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self.items):
            self.items.pop(index)

    def get_items(self) -> List[Dict[str, Any]]:
        return self.items
