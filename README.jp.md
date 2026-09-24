<p align="center"><img src="assets/banner.png" alt="Helldivers International" width="900"></p>
<h1 align="center">Helldivers International Randomizer</h1>
<p align="center"><em>ヘルダイバーの各音声枠に音声タイプと言語をランダムに割り当てるツールです。Helldivers International MODと併用します。</em></p>
<p align="center"><a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/raw/refs/heads/main/HelldiversInternational-Randomizer.exe"><img src="https://img.shields.io/badge/Download-Windows%20EXE-20804a?style=for-the-badge&logo=windows" alt="Download EXE"></a> <a href="https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions"><img src="https://img.shields.io/github/actions/workflow/status/IHanfoxI/helldivers-international-randomizer-windows/build-randomizer.yml?branch=main&style=for-the-badge&logo=githubactions&label=Windows%20Build" alt="Build status"></a></p>

| [English](README.md) | [Español · ES](README.es.md) | [Español LATAM · MS](README.ms.md) | [日本語 · JP](README.jp.md) | [Deutsch · DE](README.de.md) | [Français · FR](README.fr.md) | [Italiano · IT](README.it.md) | [Português · BP](README.bp.md) | [简体中文 · CN](README.cn.md) | [Русский · RU](README.ru.md) | [한국어 · KO](README.ko.md) |

---

## 🎮 機能

4つのヘルダイバー音声枠に音声タイプと言語をランダムに割り当て、Helldivers 2 の data フォルダーに patch ファイルを書き込みます。ゲーム内の9言語に対応し、選択したMODに含まれる場合はロシア語と韓国語のファンダブも利用できます。

## 🚀 インストールと使い方

1. 上のボタンから **HelldiversInternational-Randomizer.exe** をダウンロードします。
2. **manifest.json** があるMODフォルダーを選択します。
3. **bundles.nxa** がある Helldivers 2 の **data** フォルダーを選択します。
4. オプションを選び、**Randomize** をクリックします。

Arsenal でメインMODを再配置または更新した場合は、その後に Randomizer を再実行してください。

## 🛡️ ソースとビルド

実行ファイルは本リポジトリの Python ソースから GitHub Actions でビルドされています。Windows の起動確認テストは成功しました。ゲーム音声は含まれず、実行時にインストール済みMODを読み込んで patch ファイルを書き込みます。

GitHub Actions は Python 3.12 と PyInstaller を使用します。音声パーサーは固定コミット **c408a44** から取得し、ゲームデータは同梱しません。

**SHA-256:** A3005AADDF57AE3EE7208DCDFDDBEBC4030D5C5C415C296132A03B1E6D094D62

[ソースコード](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/randomizer_gui.py) · [ビルドワークフロー](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/blob/main/.github/workflows/build-randomizer.yml) · [成功した Windows ビルド](https://github.com/IHanfoxI/helldivers-international-randomizer-windows/actions/runs/36000112609)
