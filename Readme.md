# Mod Archive Random Player

![grafik](https://github.com/user-attachments/assets/02af2173-9183-4aae-9f5b-46e750428a6b)

A simple music player application using `libopenmpt` and `libuade` to play random module files from *[The Mod Archive](https://modarchive.org)*. This application is built with Python and PySide6 for the GUI, and uses `pyaudio` for audio playback. It chooses the best player based on the module type.

Uses [libopenmpt_py](https://github.com/shroom00/libopenmpt_py) to interface with `libopenmpt` via Python.

Only works under Linux for now.

## Features

- Play, pause, and stop downloaded module files.
- Load random module files from *The Mod Archive* or member favourites.
- Display the current module name with a link to its page on *The Mod Archive*.
- Display module meta data.
- System tray notifications for the currently playing module.
- Progress slider to show the current playback position.
- Tray icon to show/hide the main window, also provides play/pause/stop controls.
- Allows looking up the current module on *The Mod Archive* and *.mod Sample Master*.

## How to use

- Enter Member ID if you want to load random files from a member's favourites.
- Hit Play to load and play a random file from *The Mod Archive* or member favourites.
- After finishing, the next random file will be loaded and played.
- Click on the tray icon to show/hide the main window, or press Escape to hide it.

## Requirements

- Python 3.6+
- `libopenmpt` (if using Linux)
- `libuade`
- `pyaudio`
- `requests`
- `beautifulsoup4`
- `PySide6`
