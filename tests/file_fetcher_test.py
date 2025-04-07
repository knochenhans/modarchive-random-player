import os
import pytest
import tempfile
from playlist.file_fetcher import FileFetcher


def create_temp_structure(base_dir, structure):
    """
    Helper function to create a directory structure.
    :param base_dir: The base directory where the structure will be created.
    :param structure: A dictionary representing the directory structure.
    """
    for name, content in structure.items():
        path = os.path.join(base_dir, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_temp_structure(path, content)
        else:
            with open(path, "w") as f:
                f.write(content)


def test_get_files_recursively_from_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        structure = {
            "file1.txt": "content1",
            "file2.txt": "content2",
            "dir1": {
                "file3.txt": "content3",
            },
            "dir2": {
                "file4.txt": "content4",
                "file5.txt": "content5",
            },
        }
        create_temp_structure(temp_dir, structure)

        fetcher = FileFetcher()
        result = fetcher.get_files_recursively_from_path(temp_dir)

        expected_files = [
            os.path.join(temp_dir, "file1.txt"),
            os.path.join(temp_dir, "file2.txt"),
            os.path.join(temp_dir, "dir1", "file3.txt"),
            os.path.join(temp_dir, "dir2", "file4.txt"),
            os.path.join(temp_dir, "dir2", "file5.txt"),
        ]

        assert sorted(result) == sorted(expected_files)


def test_get_files_recursively_empty_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        fetcher = FileFetcher()
        result = fetcher.get_files_recursively_from_path(temp_dir)

        assert result == []


def test_get_files_recursively_with_nested_directories():
    with tempfile.TemporaryDirectory() as temp_dir:
        structure = {
            "file1.txt": "content1",
            "dir1": {
                "file2.txt": "content2",
                "dir2": {
                    "file3.txt": "content3",
                },
            },
        }
        create_temp_structure(temp_dir, structure)

        fetcher = FileFetcher()
        result = fetcher.get_files_recursively_from_path(temp_dir)

        expected_files = [
            os.path.join(temp_dir, "file1.txt"),
            os.path.join(temp_dir, "dir1", "file2.txt"),
            os.path.join(temp_dir, "dir1", "dir2", "file3.txt"),
        ]

        assert sorted(result) == sorted(expected_files)


def test_get_files_recursively_with_hidden_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        structure = {
            ".hidden_file": "hidden_content1",
            "file1.txt": "content1",
            "dir1": {
                ".hidden_file2": "hidden_content2",
                "file2.txt": "content2",
            },
        }
        create_temp_structure(temp_dir, structure)

        fetcher = FileFetcher()
        result = fetcher.get_files_recursively_from_path(temp_dir)

        expected_files = [
            os.path.join(temp_dir, ".hidden_file"),
            os.path.join(temp_dir, "file1.txt"),
            os.path.join(temp_dir, "dir1", ".hidden_file2"),
            os.path.join(temp_dir, "dir1", "file2.txt"),
        ]

        assert sorted(result) == sorted(expected_files)


def test_get_files_recursively_from_path_list():
    with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:
        structure1 = {
            "file1.txt": "content1",
            "dir1": {
                "file2.txt": "content2",
            },
        }
        structure2 = {
            "file3.txt": "content3",
            "file4.txt": "content4",
        }
        create_temp_structure(temp_dir1, structure1)
        create_temp_structure(temp_dir2, structure2)

        fetcher = FileFetcher()
        result = fetcher.get_files_recursively_from_path_list([temp_dir1, temp_dir2])

        expected_files = [
            os.path.join(temp_dir1, "file1.txt"),
            os.path.join(temp_dir1, "dir1", "file2.txt"),
            os.path.join(temp_dir2, "file3.txt"),
            os.path.join(temp_dir2, "file4.txt"),
        ]

        assert sorted(result) == sorted(expected_files)


def test_get_files_recursively_from_path_list_empty():
    with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:
        fetcher = FileFetcher()
        result = fetcher.get_files_recursively_from_path_list([temp_dir1, temp_dir2])

        assert result == []

def test_get_files_recursively_from_path_list_simple():
    with tempfile.TemporaryDirectory() as temp_dir:
        structure = {
            "file1.txt": "content1",
            "file2.txt": "content2",
        }
        create_temp_structure(temp_dir, structure)

        fetcher = FileFetcher()
        result = fetcher.get_files_recursively_from_path_list([temp_dir])

        expected_files = [
            os.path.join(temp_dir, "file1.txt"),
            os.path.join(temp_dir, "file2.txt"),
        ]

        assert sorted(result) == sorted(expected_files)
