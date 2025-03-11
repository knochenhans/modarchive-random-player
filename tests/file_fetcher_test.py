import pytest
from unittest.mock import patch, MagicMock
from playlist.file_fetcher import FileFetcher


@patch("os.walk")
def test_get_files_recursively(mock_walk):
    # Mock the os.walk to simulate directory structure
    mock_walk.return_value = [
        ("/root", ["dir1", "dir2"], ["file1.txt", "file2.txt"]),
        ("/root/dir1", [], ["file3.txt"]),
        ("/root/dir2", [], ["file4.txt", "file5.txt"]),
    ]

    fetcher = FileFetcher()
    result = fetcher.get_files_recursively("/root")

    expected_files = [
        "/root/file1.txt",
        "/root/file2.txt",
        "/root/dir1/file3.txt",
        "/root/dir2/file4.txt",
        "/root/dir2/file5.txt",
    ]

    assert result == expected_files


@patch("os.walk")
def test_get_files_recursively_empty_directory(mock_walk):
    # Mock the os.walk to simulate an empty directory
    mock_walk.return_value = [("/root", [], [])]

    fetcher = FileFetcher()
    result = fetcher.get_files_recursively("/root")

    assert result == []


@patch("os.walk")
def test_get_files_recursively_with_nested_directories(mock_walk):
    # Mock the os.walk to simulate nested directory structure
    mock_walk.return_value = [
        ("/root", ["dir1"], ["file1.txt"]),
        ("/root/dir1", ["dir2"], ["file2.txt"]),
        ("/root/dir1/dir2", [], ["file3.txt"]),
    ]

    fetcher = FileFetcher()
    result = fetcher.get_files_recursively("/root")

    expected_files = [
        "/root/file1.txt",
        "/root/dir1/file2.txt",
        "/root/dir1/dir2/file3.txt",
    ]

    assert result == expected_files


@patch("os.walk")
def test_get_files_recursively_with_symlinks(mock_walk):
    # Mock the os.walk to simulate directory structure with symlinks
    mock_walk.return_value = [
        ("/root", ["dir1"], ["file1.txt"]),
        ("/root/dir1", ["symlink"], ["file2.txt"]),
    ]

    fetcher = FileFetcher()
    result = fetcher.get_files_recursively("/root")

    expected_files = [
        "/root/file1.txt",
        "/root/dir1/file2.txt",
    ]

    assert result == expected_files


@patch("os.walk")
def test_get_files_recursively_with_hidden_files(mock_walk):
    # Mock the os.walk to simulate directory structure with hidden files
    mock_walk.return_value = [
        ("/root", ["dir1"], [".hidden_file", "file1.txt"]),
        ("/root/dir1", [], [".hidden_file2", "file2.txt"]),
    ]

    fetcher = FileFetcher()
    result = fetcher.get_files_recursively("/root")

    expected_files = [
        "/root/.hidden_file",
        "/root/file1.txt",
        "/root/dir1/.hidden_file2",
        "/root/dir1/file2.txt",
    ]

    assert result == expected_files


@patch("os.walk")
def test_get_files_recursively_with_no_permissions(mock_walk):
    # Mock the os.walk to simulate directory structure with no permissions
    mock_walk.side_effect = PermissionError("Permission denied")

    fetcher = FileFetcher()
    with pytest.raises(PermissionError):
        fetcher.get_files_recursively("/root")
