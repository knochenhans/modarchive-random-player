import json
from typing import Any, Dict, List, Optional


class ColumnManager:
    def __init__(self, columns: Optional[List[Dict[str, Any]]] = None) -> None:
        self.columns = {col["id"]: col for col in columns} if columns else {}
        self.column_order = [col["id"] for col in columns] if columns else []

    def get_column_ids(self) -> List[str]:
        return self.column_order

    def get_column_name(self, column_id: str) -> str:
        return self.columns[column_id]["name"]

    def get_column_names(self) -> List[str]:
        return [self.get_column_name(col_id) for col_id in self.column_order]

    def get_column_width(self, column_id: str) -> int:
        return self.columns[column_id]["width"]

    def get_column_widths(self) -> List[int]:
        return [
            self.get_column_width(col_id)
            for col_id in self.column_order
            if self.is_column_visible(col_id)
        ]

    def set_column_width(self, column_id: str, width: int) -> None:
        self.columns[column_id]["width"] = width

    def is_column_visible(self, column_id: str) -> bool:
        return self.columns[column_id]["visible"]

    def set_column_visibility(self, column_id: str, visible: bool) -> None:
        self.columns[column_id]["visible"] = visible

    def set_column_order(self, new_order: List[str]) -> None:
        if set(new_order) != set(self.columns.keys()):
            raise ValueError("New order must include all column IDs.")
        self.column_order = new_order

    def save_to_json(self, file_path: str) -> None:
        data = {
            "columns": list(self.columns.values()),
            "order": self.column_order,
        }
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    @classmethod
    def load_from_json(cls, file_path: str) -> "ColumnManager":
        with open(file_path, "r") as file:
            data = json.load(file)
        instance = cls(data["columns"])
        instance.column_order = data["order"]
        return instance
