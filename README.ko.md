<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>헬다이버 음성 슬롯마다 음성 종류와 언어를 무작위로 선택합니다. Helldivers International 모드와 함께 사용하는 도구입니다.</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/releases/latest/download/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 기능

> **필수 모드:** 이 앱은 단독으로 작동하지 않습니다. 먼저 [Nexus Mods에서 Helldivers International을 다운로드하고 설치하세요](https://www.nexusmods.com/helldivers2/mods/14183). 게임 내 9개 언어에는 메인 파일을, 러시아어 또는 한국어 음성에는 같은 페이지의 **Fandubs** 파일을 사용하세요. 설치된 모드 폴더를 선택하고, Arsenal을 사용하지 않는 경우 다운로드한 압축 파일을 먼저 풀어 주세요. Randomizer에는 모드와 오디오가 포함되어 있지 않습니다.

네 개의 헬다이버 음성 슬롯에 음성 종류와 언어를 무작위로 지정하고 Helldivers 2의 data 폴더에 patch 파일을 씁니다. 게임 내 9개 언어를 지원하며, 선택한 모드에 포함된 경우 러시아어와 한국어 팬더빙도 사용할 수 있습니다.

## 🚀 설치 및 사용

1. 위 버튼에서 **HelldiversInternational-Randomizer.exe**를 다운로드합니다.
2. **manifest.json**이 들어 있는 모드 폴더를 선택합니다.
3. **bundles.nxa**가 들어 있는 Helldivers 2 **data** 폴더를 선택합니다.
4. 옵션을 설정하고 **Randomize**를 누릅니다.

Arsenal에서 메인 모드를 다시 배포하거나 업데이트했다면 Randomizer를 다시 실행하세요.

## 🛡️ 소스 및 빌드

실행 파일은 이 저장소의 Python 소스를 GitHub Actions로 빌드합니다. Windows 실행 smoke test가 통과했습니다. 게임 오디오는 포함되지 않으며, 실행할 때 설치된 모드를 읽고 patch 파일을 씁니다.

빌드는 Python 3.12와 PyInstaller를 사용합니다. 오디오 파서는 공개 저장소의 고정 커밋 **c408a44**에서 가져옵니다. 게임 파일은 포함되지 않습니다.

**SHA-256:** 911B24B4A0A2F2F335FB14A603C9D9861DF8E963ECB606FE86BBE92FD992EAAA

[소스 코드](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [빌드 workflow](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [성공한 Windows 빌드](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36005520789)
