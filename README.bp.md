<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>Sorteie voz e idioma para cada espaço vocal dos Helldivers. Ferramenta complementar ao mod Helldivers International.</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/raw/refs/heads/main/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 O que faz

> **Mod necessário:** este aplicativo complementar não funciona sozinho. Primeiro, baixe e instale [Helldivers International no Nexus Mods](https://www.nexusmods.com/helldivers2/mods/14183). Use o arquivo principal para os nove idiomas do jogo e o arquivo **Fandubs** da mesma página para as vozes em russo ou coreano. Selecione a pasta do mod instalado; se não usar o Arsenal, extraia primeiro o arquivo baixado. O Randomizer não inclui o mod nem os áudios.

Sorteia tipo de voz e idioma para os quatro espaços vocais dos Helldivers e grava arquivos patch na pasta de dados de Helldivers 2. Aceita os nove idiomas do jogo e, quando incluídos no mod selecionado, os fandubs em russo e coreano.

## 🚀 Instalação e uso

1. Baixe **HelldiversInternational-Randomizer.exe** pelo botão acima.
2. Selecione a pasta do mod que contém **manifest.json**.
3. Selecione a pasta **data** de Helldivers 2 que contém **bundles.nxa**.
4. Escolha as opções e clique em **Randomize**.

Se atualizar ou implantar novamente o mod principal pelo Arsenal, execute o Randomizer depois.

## 🛡️ Código-fonte e build

O executável é compilado do código Python deste repositório pelo GitHub Actions. O teste de inicialização no Windows passou. Não inclui áudio do jogo; ao executar, lê o mod instalado e grava os arquivos patch.

O build usa Python 3.12 e PyInstaller. O parser de áudio é obtido no commit fixado **c408a44**. Nenhum arquivo do jogo é incluído.

**SHA-256:** A3005AADDF57AE3EE7208DCDFDDBEBC4030D5C5C415C296132A03B1E6D094D62

[Código-fonte](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [Workflow de build](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [Build do Windows concluído](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36000112609)
