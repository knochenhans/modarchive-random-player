# Mod Archive Random Player

![grafik](https://github.com/user-attachments/assets/1e9d1c44-2344-43b0-a531-80a131ebbac2)


A simple music player application using `libopenmpt` and `libuade` to play random module files from *[The Mod Archive](https://modarchive.org)*. This application is built with Python and PySide6 for the GUI, and uses `pyaudio` for audio playback. It chooses the best player based on the module type.

Uses [libopenmpt_py](https://github.com/shroom00/libopenmpt_py) to interface with `libopenmpt` via Python.

Only works under Linux for now.

## Features

- Play, pause, and stop downloaded module files.
- Load and play random module files from *The Mod Archive*, member favourites or by artist.
- Display module meta data.
- System tray notifications for the currently playing module.
- Progress slider to show the current playback position.
- Tray icon to show/hide the main window, also provides play/pause/stop controls.
- Allows looking up the current module on *The Mod Archive* and *.mod Sample Master*.
- Preloads the next module while the current one is playing.
- History of played modules, double-click to play songs again.

## How to use

- Enter Member ID in the settings if you want to load random files from a member's favourites.
- Enter artist name if you want to load random files from a specific artist.
- Choose the desired playing mode (random, member favourites, or artist).
- Hit Play to load and play a random file from *The Mod Archive* or member favourites.
- After finishing, the next random file will be loaded and played.
- Click on the tray icon to show/hide the main window, or press Escape to hide it.
- The star icon will show if the current module is in your favourites on *The Mod Archive*.
- To add the current module to your favourites or remove it, click the star icon. This simply calls the respective request page on *The Mod Archive*, so you need to be logged in there.

## Requirements

- Python 3.6+
- `libopenmpt` (if using Linux)
- `libuade`
- `pyaudio`
- `requests`
- `beautifulsoup4`
- `PySide6`

## TODO

- Add support for sub-song playback.
- Silence detection to skip silent intros/outros.
- Fix slight delay when playing/pausing.
