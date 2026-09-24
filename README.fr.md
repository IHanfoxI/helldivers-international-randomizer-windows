<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>Attribuez au hasard une voix et une langue à chaque emplacement Helldiver. Outil compagnon du mod Helldivers International.</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/releases/latest/download/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 Fonctionnalités

> **Mod requis :** cette application compagnon ne fonctionne pas seule. Téléchargez et installez d’abord [Helldivers International depuis Nexus Mods](https://www.nexusmods.com/helldivers2/mods/14183). Utilisez le fichier principal pour les neuf langues du jeu et le fichier **Fandubs** de la même page pour les voix russe ou coréenne. Sélectionnez le dossier du mod installé ; sans Arsenal, extrayez d’abord l’archive téléchargée. Le Randomizer ne contient ni le mod ni ses fichiers audio.

L’outil choisit au hasard le type de voix et la langue pour les quatre emplacements Helldiver, puis écrit les fichiers patch dans le dossier de données de Helldivers 2. Il prend en charge les neuf langues du jeu et, si le mod les contient, les fandubs russe et coréen.

## 🚀 Installation et utilisation

1. Téléchargez **HelldiversInternational-Randomizer.exe** avec le bouton ci-dessus.
2. Sélectionnez le dossier du mod contenant **manifest.json**.
3. Sélectionnez le dossier **data** de Helldivers 2 contenant **bundles.nxa**.
4. Choisissez vos options et cliquez sur **Randomize**.

Si vous redéployez ou mettez à jour le mod principal dans Arsenal, relancez le Randomizer ensuite.

## 🛡️ Code source et compilation

L’exécutable est compilé à partir du code Python de ce dépôt avec GitHub Actions. Le test de lancement Windows a réussi. Aucun audio du jeu n’est inclus ; l’application lit le mod installé et écrit les fichiers patch lorsqu’elle est lancée.

GitHub Actions utilise Python 3.12 et PyInstaller. Le parseur audio est récupéré au commit fixé **c408a44**. Aucun fichier du jeu n’est embarqué.

**SHA-256:** A3005AADDF57AE3EE7208DCDFDDBEBC4030D5C5C415C296132A03B1E6D094D62

[Code source](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [Workflow de compilation](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [Build Windows réussi](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36000112609)
