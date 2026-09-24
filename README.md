# Helldivers International Randomizer for Windows

This repository contains the source and build workflow for the Windows Randomizer executable. The executable is built from Python source with PyInstaller in GitHub Actions; no prebuilt executable or game audio is included here.

## Build

Run the `build-windows` job in `.github/workflows/build-randomizer.yml` on GitHub Actions, or use the same steps on Windows with Python 3.12. The build installs `numpy`, `lz4`, and `pyinstaller`, then fetches `hd2-audio-modder` from its public repository at pinned commit `c408a44` before packaging.

The workflow smoke-launches the resulting application and uploads `HelldiversInternational-Randomizer.exe` as an artifact. It does not bundle Helldivers 2 audio or modify game files during the build.

## Source files

- `randomizer_gui.py`: Tkinter interface.
- `randomize_voices.py`: randomization and patch-writing logic.
- `build_mod.py`: shared parser and patch-writing functions imported by the randomizer.
- `voice_map.json`, `voice_crosswalk.json`, `grunt_packs.json`: voice and mapping data embedded in the executable.
- `.github/workflows/build-randomizer.yml`: reproducible Windows and Linux packaging workflow.
