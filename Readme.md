# Mod Archive Random Player
A simple music player application using `libopenmpt` to play module files. This application is built with Python and PySide6 for the GUI, and uses `pyaudio` for audio playback. This is using [libopenmpt_py](https://github.com/shroom00/libopenmpt_py) to interface with `libopenmpt`.

## Features

- Play, pause, and stop downloaded module file.
- Load random module files from [The Mod Archive](https://modarchive.org).
- Display the current module name with a link to its page on The Mod Archive.
- System tray notifications for the currently playing module.
- Progress slider to show the current playback position.
- Tray icon to show/hide the main window, also provides play/pause/stop controls.

## Requirements

- Python 3.6+
- `libopenmpt`
- `pyaudio`
- `requests`
- `beautifulsoup4`
- `PySide6`
