# Mod Archive Random Player

![grafik](https://github.com/user-attachments/assets/08d67a9b-7e61-4688-b349-0bb50951f84b)

A simple music player application using `libopenmpt` and `libuade` to play random module files from The Mod Archive. This application is built with Python and PySide6 for the GUI, and uses `pyaudio` for audio playback. It chooses the best player based on the module type. This is using [libopenmpt_py](https://github.com/shroom00/libopenmpt_py) to interface with `libopenmpt`.

Only tested under Linux for now.

## Features

- Play, pause, and stop downloaded module files.
- Load random module files from [The Mod Archive](https://modarchive.org).
- Display the current module name with a link to its page on The Mod Archive.
- Display module meta data.
- System tray notifications for the currently playing module.
- Progress slider to show the current playback position.
- Tray icon to show/hide the main window, also provides play/pause/stop controls.

## How to use

- Hit Play to load and play a random file from The Mod Archive

## Requirements

- Python 3.6+
- `libopenmpt`
- `libuade`
- `pyaudio`
- `requests`
- `beautifulsoup4`
- `PySide6`
