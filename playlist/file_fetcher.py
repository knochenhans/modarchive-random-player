import os
from typing import List, Set


class FileFetcher:
    def __init__(self) -> None:
        self.total_files: int = 0
        self.files_fetched: int = 0
        self.visited_dirs: Set[str] = set()

    def get_files_recursively_from_path(self, folder_path: str) -> List[str]:
        file_list: List[str] = []
        if os.path.isfile(folder_path):
            # If the folder_path is a file, add it directly to the list
            file_list.append(os.path.abspath(folder_path))
            return file_list

        for root, dirs, files in os.walk(folder_path, followlinks=False):
            # Normalize the root path to avoid duplicates
            root = os.path.abspath(root)
            if root in self.visited_dirs:
                continue
            self.visited_dirs.add(root)

            dirs.sort(key=lambda s: s.lower())
            files.sort(key=lambda s: s.lower())

            # Add files in the current directory first
            for file in files:
                file_list.append(os.path.join(root, file))

            # Recursively add files from subdirectories
            for dir in dirs:
                file_list.extend(
                    self.get_files_recursively_from_path(os.path.join(root, dir))
                )
        return file_list

    def get_files_recursively_from_path_list(
        self, folder_paths: List[str]
    ) -> List[str]:
        file_list: List[str] = []
        for folder_path in folder_paths:
            file_list.extend(self.get_files_recursively_from_path(folder_path))
        return file_list
