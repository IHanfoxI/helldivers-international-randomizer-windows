<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>Случайно выбирает голос и язык для каждого голосового слота Хеллдайвера. Дополнение к моду Helldivers International.</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/raw/refs/heads/main/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 Возможности

Программа случайно назначает тип голоса и язык четырём голосовым слотам Хеллдайверов, а затем записывает patch-файлы в папку данных Helldivers 2. Поддерживаются девять игровых языков, а также русская и корейская фан-озвучка, если они есть в выбранной версии мода.

## 🚀 Установка и запуск

1. Скачайте **HelldiversInternational-Randomizer.exe** кнопкой выше.
2. Выберите папку мода с файлом **manifest.json**.
3. Выберите папку **data** игры Helldivers 2 с файлом **bundles.nxa**.
4. Настройте параметры и нажмите **Randomize**.

Если вы повторно развернули или обновили основной мод через Arsenal, снова запустите Randomizer.

## 🛡️ Исходный код и сборка

EXE собран из Python-кода этого репозитория с помощью GitHub Actions. Проверка запуска на Windows прошла успешно. Игровые аудиофайлы не входят в EXE; при запуске программа читает установленный мод и записывает patch-файлы.

Сборка использует Python 3.12 и PyInstaller. Парсер аудио загружается из публичного репозитория на закреплённом коммите **c408a44**. Игровых файлов в сборке нет.

**SHA-256:** A3005AADDF57AE3EE7208DCDFDDBEBC4030D5C5C415C296132A03B1E6D094D62

[Исходный код](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [Workflow сборки](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [Успешная сборка Windows](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36000112609)
