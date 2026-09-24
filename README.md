<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>Randomize the voice and language of each Helldiver slot. A companion utility for the Helldivers International mod.</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/releases/latest/download/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 What it does

> **Required mod:** This companion app does not work by itself. First download and install [Helldivers International from Nexus Mods](https://www.nexusmods.com/helldivers2/mods/14183). Use the main file for the nine in-game languages, or the **Fandubs** file on that page for Russian or Korean voices. Select the installed mod folder; if you do not use Arsenal, extract the downloaded mod archive first. The Randomizer does not include the mod or its audio.

Randomizes voice type and language across the four Helldiver voice slots, then writes patch files into the Helldivers 2 data folder. Supports all nine in-game languages and, when included in the selected mod, Russian and Korean fandubs.

## 🚀 Install and use

1. Download **HelldiversInternational-Randomizer.exe** with the button above.
2. Open it and select your mod folder (contains **manifest.json**).
3. Select the Helldivers 2 **data** folder (contains **bundles.nxa**).
4. Choose options and click **Randomize**.

If you deploy or update the main mod through Arsenal afterward, run the Randomizer again.

## 🛡️ Source and build

The executable is built from this repository’s Python source by GitHub Actions. The Windows smoke test passed. It contains no game audio; when run, it reads the installed mod and writes patch files.

GitHub Actions uses Python 3.12 and PyInstaller. The audio parser is fetched from its public repository at pinned commit **c408a44**. No game assets are bundled.

**SHA-256:** 911B24B4A0A2F2F335FB14A603C9D9861DF8E963ECB606FE86BBE92FD992EAAA

[Source code](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [Build workflow](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [Successful Windows build](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36005520789)
