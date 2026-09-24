<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>为每个 Helldiver 语音槽随机选择语音类型和语言。本工具配合 Helldivers International 模组使用。</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/raw/refs/heads/main/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 功能

> **必需模组：** 本工具不能独立运行。请先从 [Nexus Mods 下载并安装 Helldivers International](https://www.nexusmods.com/helldivers2/mods/14183)。九种游戏内语言请使用主文件；需要俄语或韩语语音时，请使用同一页面上的 **Fandubs** 文件。请选择已安装的模组文件夹；如果不使用 Arsenal，请先解压下载的压缩包。Randomizer 不包含模组或音频。

为四个 Helldiver 语音槽随机分配语音类型和语言，并将 patch 文件写入 Helldivers 2 的 data 文件夹。支持游戏内九种语言；若所选模组包含俄语和韩语同人配音，也可以使用。

## 🚀 安装与使用

1. 点击上方按钮下载 **HelldiversInternational-Randomizer.exe**。
2. 选择包含 **manifest.json** 的模组文件夹。
3. 选择包含 **bundles.nxa** 的 Helldivers 2 **data** 文件夹。
4. 设置选项并点击 **Randomize**。

若之后通过 Arsenal 重新部署或更新主模组，请再次运行 Randomizer。

## 🛡️ 源码与构建

此程序由本仓库的 Python 源码通过 GitHub Actions 构建。Windows 启动 smoke test 已通过。程序不包含游戏音频；运行时读取已安装的模组并写入 patch 文件。

构建使用 Python 3.12 和 PyInstaller。音频解析器来自固定提交 **c408a44**。不包含游戏文件。

**SHA-256:** A3005AADDF57AE3EE7208DCDFDDBEBC4030D5C5C415C296132A03B1E6D094D62

[源代码](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [构建工作流](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [成功的 Windows 构建](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36000112609)
