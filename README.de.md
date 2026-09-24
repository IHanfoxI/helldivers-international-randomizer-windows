<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>Würfelt Stimme und Sprache für jeden Helldiver-Stimmenplatz neu. Ein Begleitprogramm für die Helldivers International-Mod.</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/releases/latest/download/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 Funktionen

> **Erforderliche Mod:** Diese Begleit-App funktioniert nicht allein. Lade zuerst [Helldivers International von Nexus Mods](https://www.nexusmods.com/helldivers2/mods/14183) herunter und installiere es. Für die neun Spielsprachen brauchst du die Hauptdatei; für russische oder koreanische Stimmen die Datei **Fandubs** auf derselben Seite. Wähle den installierten Modordner aus oder entpacke das Archiv zuerst, wenn du Arsenal nicht verwendest. Mod und Audiodateien sind nicht enthalten.

Das Tool lost Stimmtyp und Sprache für alle vier Helldiver-Stimmenplätze aus und schreibt Patch-Dateien in den Datenordner von Helldivers 2. Es unterstützt die neun Spielsprachen sowie russische und koreanische Fandubs, sofern sie in der ausgewählten Mod enthalten sind.

## 🚀 Installation und Nutzung

1. Lade **HelldiversInternational-Randomizer.exe** über die Schaltfläche oben herunter.
2. Wähle den Modordner mit **manifest.json**.
3. Wähle den Helldivers-2-Ordner **data** mit **bundles.nxa**.
4. Lege die Optionen fest und klicke auf **Randomize**.

Wenn du die Hauptmod in Arsenal erneut bereitstellst oder aktualisierst, führe den Randomizer danach erneut aus.

## 🛡️ Quellcode und Build

Die EXE wird aus dem Python-Quellcode dieses Repositorys mit GitHub Actions erstellt. Der Windows-Starttest war erfolgreich. Die EXE enthält keine Spieldateien; beim Start liest sie die installierte Mod und schreibt Patch-Dateien.

GitHub Actions verwendet Python 3.12 und PyInstaller. Der Audio-Parser wird am festgelegten Commit **c408a44** geladen. Spielaudio wird nicht mitgeliefert.

**SHA-256:** 911B24B4A0A2F2F335FB14A603C9D9861DF8E963ECB606FE86BBE92FD992EAAA

[Quellcode](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [Build-Workflow](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [Erfolgreicher Windows-Build](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36005520789)
