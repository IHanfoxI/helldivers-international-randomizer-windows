# Helldivers International Randomizer for Windows

This repository contains the source and build workflow for the Windows Randomizer executable. A prebuilt `HelldiversInternational-Randomizer.exe` is included in the repository root for review and installation. GitHub Actions rebuilds it from the Python source with PyInstaller. No game audio is included.

## Build

Run the `build-windows` job in `.github/workflows/build-randomizer.yml` on GitHub Actions, or use the same steps on Windows with Python 3.12. The build installs `numpy`, `lz4`, and `pyinstaller`, then fetches `hd2-audio-modder` from its public repository at pinned commit `c408a44` before packaging.

The workflow smoke-launches the resulting application and uploads `HelldiversInternational-Randomizer.exe` as an artifact. The checked-in executable is the Windows artifact from that successful workflow run. The build does not bundle Helldivers 2 audio or modify game files.

## Source files

- `randomizer_gui.py`: Tkinter interface.
- `randomize_voices.py`: randomization and patch-writing logic.
- `build_mod.py`: shared parser and patch-writing functions imported by the randomizer.
- `voice_map.json`, `voice_crosswalk.json`, `grunt_packs.json`: voice and mapping data embedded in the executable.
- `.github/workflows/build-randomizer.yml`: reproducible Windows and Linux packaging workflow.
