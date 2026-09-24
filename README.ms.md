<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>Aleatoriza la voz y el idioma de cada espacio de Helldiver. Herramienta complementaria del mod Helldivers International.</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/raw/refs/heads/main/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 Qué hace

> **Mod necesario:** Esta aplicación complementaria no funciona por sí sola. Primero descarga e instala [Helldivers International desde Nexus Mods](https://www.nexusmods.com/helldivers2/mods/14183). Usa el archivo principal para los nueve idiomas del juego y el **Fandubs** de esa página para las voces rusa o coreana. Selecciona la carpeta del mod instalado; si no usas Arsenal, extrae primero el archivo descargado. El Randomizer no incluye el mod ni su audio.

Asigna al azar tipo de voz e idioma a los cuatro espacios de Helldiver y escribe archivos patch en la carpeta de datos de Helldivers 2. Admite los nueve idiomas del juego y, cuando están incluidos en el mod, los fandubs ruso y coreano.

## 🚀 Instalar y usar

1. Descarga **HelldiversInternational-Randomizer.exe** con el botón de arriba.
2. Ábrelo y selecciona la carpeta del mod, donde está **manifest.json**.
3. Selecciona la carpeta **data** de Helldivers 2, donde está **bundles.nxa**.
4. Elige tus opciones y pulsa **Randomize**.

Si vuelves a desplegar o actualizar el mod principal en Arsenal, ejecuta después el Randomizer.

## 🛡️ Código y compilación

El ejecutable se construyó desde el código Python de este repositorio mediante GitHub Actions. El smoke test de Windows pasó. No incluye audio del juego; lee el mod instalado y escribe patch al ejecutarlo.

GitHub Actions usa Python 3.12 y PyInstaller. El parser de audio se obtiene del repositorio público en el commit fijado **c408a44**. No incluye archivos del juego.

**SHA-256:** A3005AADDF57AE3EE7208DCDFDDBEBC4030D5C5C415C296132A03B1E6D094D62

[Código fuente](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [Workflow de compilación](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [Build de Windows exitoso](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36000112609)
