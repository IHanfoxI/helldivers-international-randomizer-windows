#!/usr/bin/env python3
"""
Build the "Helldivers International (rebuild)" Arsenal mod.

The mod overrides the voice packages the game actually loads (the BASE
language = the game's own language) with audio from the language you pick
per voice type in Arsenal. The two dimensions are independent:

  * BASE language  = the language your GAME is set to (which package the
                     game loads). Each zip targets one base language so the
                     mod works no matter what language you play in.
  * voice language = chosen per voice type in Arsenal (the src_lang of the
                     embedded audio). The full menu is available in every zip.

We build one output (manifest + patches) per base language X, with
BASE_LANGS = ["us", X] (the game always also loads the English base as
fallback). The manifest UI is localized to X as well.

Output: mod/HelldiversInternational/ with one folder per (voice, src_lang)
combo and a manifest.json exposing 4 voice slots, each selectable per
language, in the Arsenal mod manager.
"""
import sys, os, types, json, shutil, struct, hashlib

sys.modules['pyaudio'] = types.ModuleType('pyaudio')
# frozen (randomize_voices.py, PyInstaller): data files ship next to the exe
# in _MEIPASS instead of alongside this .py source.
HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools", "hd2-audio-modder"))
import slim, core

GAMEDATA = "/home/diegoc/.local/share/Steam/steamapps/common/Helldivers 2/data"
OUT = os.path.join(HERE, "mod", "HelldiversInternational")
FLAGS_SRC = os.path.join(HERE, "flags")  # flags/<lang>.png, copied into the mod
# A language with no flag file just loses its menu image, which is easy to ship
# without noticing (Korean did). Warn once per language instead.
_MISSING_FLAGS = set()
COVERS_SRC = os.path.join(HERE, "covers")  # cover art, copied into the mod

# Cover shown by the mod manager (manifest "IconPath"). The +Fandubs build is
# the same mod with extra languages, so it wears the same cover.
COVER = "international.png"

VOICES = [
    "helldiver_soldier_female1_VO",  # predeterminada 1
    "helldiver_soldier_male1_VO",    # predeterminada 2
    "helldiver_soldier_female2_VO",  # predeterminada 3
    "helldiver_purist_VO",           # predeterminada 4
]

# folder names (language-neutral, used in Include paths)
VOICE_SHORT = {
    "helldiver_soldier_male1_VO":   "male1",
    "helldiver_soldier_female1_VO": "female1",
    "helldiver_soldier_female2_VO": "female2",
    "helldiver_purist_VO":          "purist",
}

# full cross-group (v5): each voice slot can be filled by ANY of the 4 voice
# types, not just its within-group partner. Made viable by voice_crosswalk.json
# (content-verified line matching, not positional) -- validated 87.8-95.7%
# coverage across all 6 possible pairs, cross-gender included (most lines are
# shared system/mechanic script across all 4 actors, not gender-specific).
# self first (own type), then the other 3 in CANONICAL_VOICES order.
CANONICAL_VOICES = [
    "helldiver_soldier_female1_VO",
    "helldiver_soldier_female2_VO",
    "helldiver_soldier_male1_VO",
    "helldiver_purist_VO",
]
GROUP = {v: [v] + [o for o in CANONICAL_VOICES if o != v] for v in CANONICAL_VOICES}

# cross-type (different actor) index alignment: no shared hierarchy ids exist
# between actors, so a positional swap was assumed. Validated by transcript
# matching (voice_crosswalk_extract.py + voice_crosswalk_match.py): 78-86% of
# raw positions were actually misaligned (differing variation-take counts per
# actor drift the flat index), causing wrong lines to play (e.g. "yes" for
# "no", bug barks during automaton fights). voice_crosswalk.json holds only
# the subset of positions verified to match by actual line content (~70-80%
# coverage); everything else is left unmapped so build_combo_patch falls back
# to the native (correct) line instead of guessing. Language-independent:
# hierarchy id/order for a given voice is identical across all 9 languages,
# so a crosswalk built once from the English package is valid everywhere.
_CROSSWALK_PATH = os.path.join(HERE, "voice_crosswalk.json")
CROSSWALK = json.load(open(_CROSSWALK_PATH)) if os.path.exists(_CROSSWALK_PATH) else {}

def cross_type_index_map(target_voice, src_voice):
    """{target_index: src_index} for a verified cross-type (different actor)
    line match, or None for same-actor (target==src, cross-language only),
    which stays fully positional -- exact, since hierarchy ids/order are
    identical for the same voice across languages (validated separately).

    The crosswalk stores the two directions of a pair separately, keyed by
    target voice inside the group: one source take may answer for several
    target takes (the actors record different numbers of takes per line), and
    that many-to-one shape does not survive being inverted. Group key is
    "<a>_<b>" with a, b in CANONICAL_VOICES order (matches
    voice_crosswalk_match.py's PAIRS naming)."""
    if target_voice == src_voice:
        return None
    a, b = sorted((target_voice, src_voice), key=CANONICAL_VOICES.index)
    group = CROSSWALK.get(f"{VOICE_SHORT[a]}_{VOICE_SHORT[b]}", {})
    return {int(t): s for t, s in group.get(VOICE_SHORT[target_voice], {}).items()}

# UI strings per interface language. Keyed by language code; ms reuses
# Spanish text (Spanish LatAm). Placeholders: {voice}, {lang}.
STRINGS = {
    "us": {
        "mod_name": "Helldivers International (rebuild)",
        "mod_desc": "Choose the voice language for each Helldiver voice type. "
                    "Rebuild of the original mod. Audio is embedded, so it "
                    "works no matter what language your game is set to.",
        "native_name": "Native (game language)",
        "native_desc": "{voice} unchanged",
        "slot_desc": "Voice language for {voice}",
        "sub_desc": "{voice} in {lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "Default voice 1 (female 1)",
            "helldiver_soldier_male1_VO":   "Default voice 2 (male 1)",
            "helldiver_soldier_female2_VO": "Default voice 3 (female 2)",
            "helldiver_purist_VO":          "Default voice 4 (male 2)",
        },
        "lang": {
            "us": "English", "jp": "Japanese", "de": "German", "fr": "French",
            "it": "Italian", "es": "Spanish (Spain)", "ms": "Spanish (LatAm)",
            "bp": "Portuguese (Brazil)", "cn": "Chinese (Simplified)",
            "ru": "Russian (fan dub — DubDivers)",
            "ko": "Korean (fan dub — HACKPUNCH2954)",
        },
    },
    "es": {
        "mod_name": "Helldivers International (rebuild)",
        "mod_desc": "Elige el idioma de voz de cada tipo de Helldiver. "
                    "Reconstrucción del mod original. Audio embebido, "
                    "funciona sin importar el idioma de tu juego.",
        "native_name": "Nativo (idioma del juego)",
        "native_desc": "{voice} sin cambios",
        "slot_desc": "Idioma de voz para {voice}",
        "sub_desc": "{voice} en {lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "Voz predeterminada 1 (femenina 1)",
            "helldiver_soldier_male1_VO":   "Voz predeterminada 2 (masculina 1)",
            "helldiver_soldier_female2_VO": "Voz predeterminada 3 (femenina 2)",
            "helldiver_purist_VO":          "Voz predeterminada 4 (masculina 2)",
        },
        "lang": {
            "us": "Inglés", "jp": "Japonés", "de": "Alemán", "fr": "Francés",
            "it": "Italiano", "es": "Español (España)", "ms": "Español (LatAm)",
            "bp": "Portugués (Brasil)", "cn": "Chino (simplificado)",
            "ru": "Ruso (fandub — DubDivers)",
            "ko": "Coreano (fandub — HACKPUNCH2954)",
        },
    },
    "jp": {
        "mod_name": "Helldivers International (再構築版)",
        "mod_desc": "各ヘルダイバーのボイスタイプごとに音声言語を選べます。"
                    "オリジナルMODの再構築版。音声は埋め込み済みで、"
                    "ゲームの言語設定を問わず動作します。",
        "native_name": "ネイティブ（ゲームの言語）",
        "native_desc": "{voice}（変更なし）",
        "slot_desc": "{voice} の音声言語",
        "sub_desc": "{voice}：{lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "デフォルトボイス1（女性1）",
            "helldiver_soldier_male1_VO":   "デフォルトボイス2（男性1）",
            "helldiver_soldier_female2_VO": "デフォルトボイス3（女性2）",
            "helldiver_purist_VO":          "デフォルトボイス4（男性2）",
        },
        "lang": {
            "us": "英語", "jp": "日本語", "de": "ドイツ語", "fr": "フランス語",
            "it": "イタリア語", "es": "スペイン語（スペイン）",
            "ms": "スペイン語（中南米）", "bp": "ポルトガル語（ブラジル）",
            "cn": "中国語（簡体）",
            "ru": "ロシア語（ファン吹き替え・DubDivers）",
            "ko": "韓国語（ファン吹き替え・HACKPUNCH2954）",
        },
    },
    "de": {
        "mod_name": "Helldivers International (Neuauflage)",
        "mod_desc": "Wähle die Sprachausgabe für jeden Helldiver-Stimmtyp. "
                    "Neuauflage des ursprünglichen Mods. Audio ist eingebettet "
                    "und funktioniert unabhängig von der Spielsprache.",
        "native_name": "Original (Spielsprache)",
        "native_desc": "{voice} unverändert",
        "slot_desc": "Sprachausgabe für {voice}",
        "sub_desc": "{voice} auf {lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "Standardstimme 1 (weiblich 1)",
            "helldiver_soldier_male1_VO":   "Standardstimme 2 (männlich 1)",
            "helldiver_soldier_female2_VO": "Standardstimme 3 (weiblich 2)",
            "helldiver_purist_VO":          "Standardstimme 4 (männlich 2)",
        },
        "lang": {
            "us": "Englisch", "jp": "Japanisch", "de": "Deutsch",
            "fr": "Französisch", "it": "Italienisch", "es": "Spanisch (Spanien)",
            "ms": "Spanisch (Lateinamerika)", "bp": "Portugiesisch (Brasilien)",
            "cn": "Chinesisch (vereinfacht)",
            "ru": "Russisch (Fan-Dub — DubDivers)",
            "ko": "Koreanisch (Fan-Dub — HACKPUNCH2954)",
        },
    },
    "fr": {
        "mod_name": "Helldivers International (refonte)",
        "mod_desc": "Choisissez la langue des voix pour chaque type de voix de "
                    "Helldiver. Refonte du mod original. L'audio est intégré et "
                    "fonctionne quelle que soit la langue du jeu.",
        "native_name": "Natif (langue du jeu)",
        "native_desc": "{voice} inchangé",
        "slot_desc": "Langue de la voix pour {voice}",
        "sub_desc": "{voice} en {lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "Voix par défaut 1 (féminine 1)",
            "helldiver_soldier_male1_VO":   "Voix par défaut 2 (masculine 1)",
            "helldiver_soldier_female2_VO": "Voix par défaut 3 (féminine 2)",
            "helldiver_purist_VO":          "Voix par défaut 4 (masculine 2)",
        },
        "lang": {
            "us": "Anglais", "jp": "Japonais", "de": "Allemand", "fr": "Français",
            "it": "Italien", "es": "Espagnol (Espagne)",
            "ms": "Espagnol (Amérique latine)", "bp": "Portugais (Brésil)",
            "cn": "Chinois (simplifié)",
            "ru": "Russe (fandub — DubDivers)",
            "ko": "Coréen (fandub — HACKPUNCH2954)",
        },
    },
    "it": {
        "mod_name": "Helldivers International (ricostruzione)",
        "mod_desc": "Scegli la lingua della voce per ogni tipo di voce dei "
                    "Helldiver. Ricostruzione del mod originale. L'audio è "
                    "incorporato e funziona con qualsiasi lingua del gioco.",
        "native_name": "Nativo (lingua del gioco)",
        "native_desc": "{voice} invariato",
        "slot_desc": "Lingua della voce per {voice}",
        "sub_desc": "{voice} in {lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "Voce predefinita 1 (femminile 1)",
            "helldiver_soldier_male1_VO":   "Voce predefinita 2 (maschile 1)",
            "helldiver_soldier_female2_VO": "Voce predefinita 3 (femminile 2)",
            "helldiver_purist_VO":          "Voce predefinita 4 (maschile 2)",
        },
        "lang": {
            "us": "Inglese", "jp": "Giapponese", "de": "Tedesco",
            "fr": "Francese", "it": "Italiano", "es": "Spagnolo (Spagna)",
            "ms": "Spagnolo (America Latina)", "bp": "Portoghese (Brasile)",
            "cn": "Cinese (semplificato)",
            "ru": "Russo (fandub — DubDivers)",
            "ko": "Coreano (fandub — HACKPUNCH2954)",
        },
    },
    "bp": {
        "mod_name": "Helldivers International (reconstrução)",
        "mod_desc": "Escolha o idioma de voz para cada tipo de voz de Helldiver. "
                    "Reconstrução do mod original. O áudio é incorporado e "
                    "funciona independentemente do idioma do jogo.",
        "native_name": "Nativo (idioma do jogo)",
        "native_desc": "{voice} sem alterações",
        "slot_desc": "Idioma de voz para {voice}",
        "sub_desc": "{voice} em {lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "Voz padrão 1 (feminina 1)",
            "helldiver_soldier_male1_VO":   "Voz padrão 2 (masculina 1)",
            "helldiver_soldier_female2_VO": "Voz padrão 3 (feminina 2)",
            "helldiver_purist_VO":          "Voz padrão 4 (masculina 2)",
        },
        "lang": {
            "us": "Inglês", "jp": "Japonês", "de": "Alemão", "fr": "Francês",
            "it": "Italiano", "es": "Espanhol (Espanha)",
            "ms": "Espanhol (América Latina)", "bp": "Português (Brasil)",
            "cn": "Chinês (simplificado)",
            "ru": "Russo (fandub — DubDivers)",
            "ko": "Coreano (fandub — HACKPUNCH2954)",
        },
    },
    "cn": {
        "mod_name": "Helldivers International (重制版)",
        "mod_desc": "为每种绝地战兵语音类型选择语音语言。原版MOD的重制版。"
                    "音频已内嵌，无论游戏设为何种语言都能使用。",
        "native_name": "原生（游戏语言）",
        "native_desc": "{voice}（不更改）",
        "slot_desc": "{voice} 的语音语言",
        "sub_desc": "{voice}：{lang}",
        "voice": {
            "helldiver_soldier_female1_VO": "默认语音1（女性1）",
            "helldiver_soldier_male1_VO":   "默认语音2（男性1）",
            "helldiver_soldier_female2_VO": "默认语音3（女性2）",
            "helldiver_purist_VO":          "默认语音4（男性2）",
        },
        "lang": {
            "us": "英语", "jp": "日语", "de": "德语", "fr": "法语",
            "it": "意大利语", "es": "西班牙语（西班牙）", "ms": "西班牙语（拉美）",
            "bp": "葡萄牙语（巴西）", "cn": "中文（简体）",
            "ru": "俄语（粉丝配音·DubDivers）",
            "ko": "韩语（粉丝配音·HACKPUNCH2954）",
        },
    },
}
# ms (Spanish LatAm) reuses Spanish UI text
STRINGS["ms"] = STRINGS["es"]

# short voice labels for cross-type suboptions (per UI language)
VOICE_BRIEF = {
    "us": {"helldiver_soldier_female1_VO": "Female 1", "helldiver_soldier_male1_VO": "Male 1",
           "helldiver_soldier_female2_VO": "Female 2", "helldiver_purist_VO": "Male 2"},
    "es": {"helldiver_soldier_female1_VO": "Femenina 1", "helldiver_soldier_male1_VO": "Masculina 1",
           "helldiver_soldier_female2_VO": "Femenina 2", "helldiver_purist_VO": "Masculina 2"},
    "jp": {"helldiver_soldier_female1_VO": "女性1", "helldiver_soldier_male1_VO": "男性1",
           "helldiver_soldier_female2_VO": "女性2", "helldiver_purist_VO": "男性2"},
    "de": {"helldiver_soldier_female1_VO": "Weiblich 1", "helldiver_soldier_male1_VO": "Männlich 1",
           "helldiver_soldier_female2_VO": "Weiblich 2", "helldiver_purist_VO": "Männlich 2"},
    "fr": {"helldiver_soldier_female1_VO": "Féminine 1", "helldiver_soldier_male1_VO": "Masculine 1",
           "helldiver_soldier_female2_VO": "Féminine 2", "helldiver_purist_VO": "Masculine 2"},
    "it": {"helldiver_soldier_female1_VO": "Femminile 1", "helldiver_soldier_male1_VO": "Maschile 1",
           "helldiver_soldier_female2_VO": "Femminile 2", "helldiver_purist_VO": "Maschile 2"},
    "bp": {"helldiver_soldier_female1_VO": "Feminina 1", "helldiver_soldier_male1_VO": "Masculina 1",
           "helldiver_soldier_female2_VO": "Feminina 2", "helldiver_purist_VO": "Masculina 2"},
    "cn": {"helldiver_soldier_female1_VO": "女性1", "helldiver_soldier_male1_VO": "男性1",
           "helldiver_soldier_female2_VO": "女性2", "helldiver_purist_VO": "男性2"},
}
VOICE_BRIEF["ms"] = VOICE_BRIEF["es"]

# cross-type suboption Name/Description format per UI language.
# {brief}=partner voice short label, {lang}=language, {slot}=this slot's voice.
CROSS = {
    "us": ("{brief} · {lang}", "{slot} using the {brief} voice in {lang}"),
    "es": ("{brief} · {lang}", "{slot} con la voz {brief} en {lang}"),
    "jp": ("{brief}・{lang}", "{slot} を {brief} の声（{lang}）で"),
    "de": ("{brief} · {lang}", "{slot} mit der Stimme {brief} auf {lang}"),
    "fr": ("{brief} · {lang}", "{slot} avec la voix {brief} en {lang}"),
    "it": ("{brief} · {lang}", "{slot} con la voce {brief} in {lang}"),
    "bp": ("{brief} · {lang}", "{slot} com a voz {brief} em {lang}"),
    "cn": ("{brief}・{lang}", "{slot} 使用 {brief} 的声音（{lang}）"),
}
CROSS["ms"] = CROSS["es"]

# One universal build covers every base language in a single file, so it needs
# a single Guid of its own rather than one of the per-base-language ones below.
GUID_UNIVERSAL = "9d4e2f60-71a8-4c35-b0e9-5a8f3c26d417"

# The --fandubs build is the same mod plus the fan-dubbed languages, so it is
# published as a SEPARATE download that REPLACES the plain one -- both fill the
# same four voice slots, and two mods writing the same stream ids would just
# fight over them. Hence its own Guid and its own name in the menu: Arsenal
# keys mods by Guid, and a shared one would make the two look like a single
# mod to the manager.
GUID_UNIVERSAL_FANDUBS = "4b8e17a2-c396-4d05-a72f-8e1d05b3496c"

# Appended to the mod name so the two are told apart at a glance in Arsenal.
FANDUB_SUFFIX = " + Fandubs"

# Appended to the mod description. Crediting the dub authors is a condition of
# using their audio (see EXTRA_LANGS), so it travels inside the mod itself
# rather than living only on the Nexus page.
FANDUB_CREDIT = {
    "us": " Includes fan dubs: Russian by DubDivers (Nexus mod 7515) and Korean by HACKPUNCH2954 (Nexus mod 5731).",
    "es": " Incluye fandubs: ruso por DubDivers (mod 7515 de Nexus) y coreano por HACKPUNCH2954 (mod 5731 de Nexus).",
    "jp": " ファン吹き替えを収録：ロシア語は DubDivers（Nexus mod 7515）、韓国語は HACKPUNCH2954（Nexus mod 5731）。",
    "de": " Enthält Fan-Dubs: Russisch von DubDivers (Nexus-Mod 7515) und Koreanisch von HACKPUNCH2954 (Nexus-Mod 5731).",
    "fr": " Inclut des fandubs : russe par DubDivers (mod Nexus 7515) et coréen par HACKPUNCH2954 (mod Nexus 5731).",
    "it": " Include fandub: russo di DubDivers (mod Nexus 7515) e coreano di HACKPUNCH2954 (mod Nexus 5731).",
    "bp": " Inclui fandubs: russo por DubDivers (mod 7515 do Nexus) e coreano por HACKPUNCH2954 (mod 5731 do Nexus).",
    "cn": " 收录粉丝配音：俄语由 DubDivers 制作（Nexus mod 7515），韩语由 HACKPUNCH2954 制作（Nexus mod 5731）。",
}
FANDUB_CREDIT["ms"] = FANDUB_CREDIT["es"]

# distinct UUID v4 per base language so each Nexus upload imports as a
# separate mod in Arsenal (Arsenal validates the version nibble == 4).
GUID = {
    "us": "3c1d5e7a-9024-4b8f-8c16-2d3e4f5a6b7d",
    "es": "7f3a9c1e-8b24-4d6f-9a05-1c2e3f4a5b6c",
    "jp": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
    "de": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
    "fr": "c3d4e5f6-a7b8-4c9d-8e0f-2a3b4c5d6e7f",
    "it": "d4e5f6a7-b8c9-4d0e-9f1a-3b4c5d6e7f80",
    "bp": "e5f6a7b8-c9d0-4e1f-8a2b-4c5d6e7f8091",
    "ms": "f6a7b8c9-d0e1-4f2a-9b3c-5d6e7f80912a",
    "cn": "a7b8c9d0-e1f2-4a3b-8c4d-6e7f8091a2b3",
}

PATCH_UNK4 = bytes.fromhex(
    "CE09F5F4000000000C729F9E8872B8BD00A06B02000000000079510000000000"
    "000000000000000000000000000000000000000000000000")


# Fan-dub voice languages: not shipped with the game, taken from a third-party
# mod's patch file dropped into assets/<code>/ (not versioned -- see README).
# Such a patch bundles many banks at once, but the bank names and the hierarchy
# ids/order inside them are identical to the game's own packages (verified:
# 916/916 female1/female2 and 921/921 male1/purist ids, same order), so it
# plugs into the normal positional swap and the cross-type crosswalk unchanged.
# Coverage can be partial -- build_combo_patch already leaves any source the
# fan dub didn't record on its native line.
#
#   ru  "Russian voiceover of Helldivers 2" by DubDivers (Nexus mod 7515).
#       Used under that page's asset-use permission, which requires crediting
#       the author. Voice-language only: the game has no Russian package, so
#       "ru" is never a base language and gets no zip of its own. One patch
#       bundles all 4 voice banks (see docstring above), so EXTRA_LANGS points
#       at a single file and ordered_source_ids(bank_name=...) picks the bank.
#
#   ko  Korean dub, Nexus mod 5731, used with permission from its author
#       (HACKPUNCH2954, granted 2026-09-11). Unlike the Russian dub this one
#       ships one patch PER voice actor/type instead of one multi-bank patch,
#       so EXTRA_LANGS maps "ko" to a {voice: path} dict instead of a single
#       path. Confirmed by bank dep name inside each file (not by folder
#       order): Helldiver 1/2/3/4 in the download map to female1/male1/
#       female2/purist respectively -- 1 and 3 share a voice actor (배정현)
#       but are still female1 and female2, i.e. two different in-game
#       characters read by the same actor, same as some of the game's own
#       casting. Each file also carries the actor's own Helldiver_Standard_VO
#       (exertions) bank, unused here -- only the grunt packs already in
#       grunt_packs.json are wired into build_combo_patch's cross-type path.
#       The download also has Eagle-1/Pelican-1/Mission Control/Democracy
#       Officer/Ship Master/Service Technician/SEAF banks (mod 2/3 territory)
#       -- not wired in here, this pass only covers mod 1 (Helldiver voices).
EXTRA_LANGS = {
    "ru": os.path.join("assets", "ru", "9ba626afa44a3aa3.patch_0"),
    "ko": {
        "helldiver_soldier_female1_VO": os.path.join("assets", "ko", "female1", "9ba626afa44a3aa3.patch_0"),
        "helldiver_soldier_male1_VO": os.path.join("assets", "ko", "male1", "9ba626afa44a3aa3.patch_0"),
        "helldiver_soldier_female2_VO": os.path.join("assets", "ko", "female2", "9ba626afa44a3aa3.patch_0"),
        "helldiver_purist_VO": os.path.join("assets", "ko", "purist", "9ba626afa44a3aa3.patch_0"),
    },
}


def extra_voice_map():
    """{lang: {voice: path}} for the fan-dub sources actually present under
    assets/. Merged on top of voice_map.json (which only ever describes what
    discover_voices.py found in the game's own data dir). A lang entry may be
    one path shared by all 4 voices (one multi-bank patch, e.g. ru) or a
    {voice: path} dict (one patch per voice, e.g. kr); only fully-present
    dicts are used, so a partial download doesn't silently ship 3 voices
    native and 1 dubbed."""
    out = {}
    for lang, rel in EXTRA_LANGS.items():
        if isinstance(rel, dict):
            if all(os.path.isfile(os.path.join(HERE, p)) for p in rel.values()):
                out[lang] = dict(rel)
        elif os.path.isfile(os.path.join(HERE, rel)):
            out[lang] = {v: rel for v in VOICES}
    return out


def base_langs_for(lang):
    """Base package to patch for game language `lang`. Only the active
    language package needs the override -- confirmed in-game (2026-07): with
    only the "ms" package patched (no "us" override), all 4 voice slots
    played correctly on a game set to Spanish-LatAm. The always-loaded
    English base isn't actually used as the audio source for these voice
    banks, so patching it too was pure redundant weight (roughly halved the
    8 non-English zips)."""
    return [lang]


# ---------------------------------------------------------------- exertions
# Grunts of effort, pain screams, coughs, death cries and euphoric shouts do
# NOT live in the per-language voice packages this mod swaps. They sit in
# `content/audio/Helldiver_Standard_VO`, a single NON-localized bank inside
# package f6fb08cc02d24255 (which the game only ships inside bundles.*.nxa --
# slim.get_package_toc reads it from there). That bank is laid out as
# 27 categories x 4 blocks x N takes, one block per Helldiver voice type,
# always the same take count per block, so a block is swapped onto another
# block by position with no alignment guesswork.
#
# Because they are not localized, a slot filled with another language keeps
# its own (correct) exertions -- but a slot filled with another TYPE used to
# keep the slot's exertions, i.e. a female voice in a male slot grunted,
# screamed and died as a man. Reported by users; this is the fix. The
# exertion streams ride inside the same patch as the voice lines, so the swap
# follows the slot's voice choice automatically instead of needing a menu of
# its own (and, being distinct stream ids, still composes across slots).
#
# WHICH block is which actor is not positional -- the four children of a
# category are not in the same order in every category. grunt_packs.py groups
# them by speaker and writes grunt_packs.json; see its docstring.
#
# 143 of each pack's 161 takes are plain STREAM sources, swapped by writing
# their stream file. The other 18 (the whole of the first four categories --
# including the long burning/dying screams) are PREFETCH_STREAM: the take's
# first mem_size bytes sit in the bank's DIDX and the rest streams, so
# rewriting only the stream half would splice two actors inside one scream.
# Those used to be left native, which is exactly the "I burned to death in the
# wrong voice" report.
#
# The fix is to stop them being prefetched: grunt_bank ships a copy of the
# bank whose source structs say STREAM instead of PREFETCH_STREAM, so the
# engine takes the whole take from the stream file -- which is already
# complete, prefetch only duplicates its head -- and the swap rides in the
# stream ids like every other take.
#
# Shipping a bank is what makes this composable. A patch replaces a bank
# wholesale, so if each slot shipped its own edit of this bank the last one in
# the .patch_N chain would win and the other three slots would lose their
# exertions. This edit carries no slot's choice: it only flips how the takes
# are fetched, identical bytes for all four slots, whichever patch wins. The
# per-slot content stays in the stream ids, which are disjoint per slot and
# compose as before.
GRUNT_PKG = "f6fb08cc02d24255"
GRUNT_BANK = "Helldiver_Standard_VO"

_GRUNT_PACKS_PATH = os.path.join(HERE, "grunt_packs.json")
GRUNT_PACKS = (json.load(open(_GRUNT_PACKS_PATH))
               if os.path.exists(_GRUNT_PACKS_PATH) else None)


def grunt_categories(archive):
    """[[block, block, block, block], ...] one entry per exertion category,
    each block a list of (position, source struct) in bank order. The bank
    groups a category under an ActorMixer whose four children are the four
    voice types: a sound's 3rd ancestor is its category, its 2nd its block."""
    bank = None
    for b in archive.wwise_banks.values():
        if b.dep and b.dep.data.strip("\x00").endswith("/" + GRUNT_BANK):
            bank = b
            break
    if bank is None:
        raise SystemExit(f"bank {GRUNT_BANK} not found in {GRUNT_PKG}")
    ents = bank.hierarchy.entries

    def ancestor(hid, levels):
        for _ in range(levels):
            hid = ents[hid].get_parent_id() if hid in ents else None
        return hid

    cats, order, pos = {}, [], 0
    for hid, entry in ents.items():
        for source in getattr(entry, "sources", None) or []:
            cat, block = ancestor(hid, 3), ancestor(hid, 2)
            if cat not in cats:
                order.append(cat)
            cats.setdefault(cat, {}).setdefault(block, []).append((pos, source))
            pos += 1
    out = []
    for cat in order:
        blocks = sorted(cats[cat].values(), key=lambda b: b[0][0])
        if len(blocks) != 4 or len({len(b) for b in blocks}) != 1:
            continue  # not a 4-way voice-type split, leave it alone
        out.append(blocks)
    return out


_GRUNT_CACHE = {}


def unprefetch(archive, categories):
    """Flip every swappable PREFETCH_STREAM exertion source to STREAM, so the
    engine reads the take entirely from its stream file (which already holds
    the whole thing) instead of starting from the copy in the bank's DIDX.
    Returns the number of sources changed. Only touches categories grunt_packs
    grouped -- a category with no pack mapping is never swapped, so there is
    nothing to gain by changing how it loads."""
    from const import STREAM, PREFETCH_STREAM
    changed = 0
    for ci in GRUNT_PACKS["blocks"]:
        for block in categories[int(ci)]:
            for _, source in block:
                if source.stream_type == PREFETCH_STREAM:
                    source.stream_type = STREAM
                    source.mem_size = 0  # nothing of it lives in the bank now
                    changed += 1
    if changed:
        for bank in archive.wwise_banks.values():
            if bank.dep and bank.dep.data.strip("\x00").endswith("/" + GRUNT_BANK):
                bank.raise_modified()
    return changed


_GRUNT_BANK_CACHE = {}


def grunt_bank():
    """({file id: WwiseBank}, {source id: AudioSource}) for the exertion bank,
    rebuilt with the prefetched takes turned into plain streams (see
    unprefetch). The same bytes for every slot and every language, so the four
    slot patches can all carry it without fighting over the .patch_N chain.
    The audio sources come along because WwiseBank.generate reads them to
    rebuild the DIDX of the takes that stay in the bank."""
    if GRUNT_PACKS is None:
        return {}, {}
    if not _GRUNT_BANK_CACHE:
        archive = load(GRUNT_PKG)
        unprefetch(archive, grunt_categories(archive))
        banks = {k: v for k, v in archive.wwise_banks.items()
                 if v.dep and v.dep.data.strip("\x00").endswith("/" + GRUNT_BANK)}
        _GRUNT_BANK_CACHE["banks"] = banks
        _GRUNT_BANK_CACHE["sources"] = archive.audio_sources
    return _GRUNT_BANK_CACHE["banks"], _GRUNT_BANK_CACHE["sources"]


def grunt_streams(target_voice, src_voice):
    """{stream file id: WwiseStream} carrying src_voice's exertions in
    target_voice's slot, ready to be merged into the combo patch. Cached: the
    audio is language-independent (the exertion bank is not localized), so all
    of a slot's language options for the same source type share one payload.

    Every take is swapped, prefetched ones included: the copy of the bank that
    travels in the same patch (grunt_bank) has already turned those into plain
    streams, so writing the stream file is enough."""
    if GRUNT_PACKS is None:
        return {}
    key = (target_voice, src_voice)
    if key in _GRUNT_CACHE:
        return _GRUNT_CACHE[key]
    pack_of = {v: i for i, v in enumerate(GRUNT_PACKS["pack_voice"])}
    t_pack, s_pack = pack_of[target_voice], pack_of[src_voice]
    archive = load(GRUNT_PKG)
    categories = grunt_categories(archive)
    payload = []
    for ci, blocks in GRUNT_PACKS["blocks"].items():
        category = categories[int(ci)]
        for (_, tgt), (_, src) in zip(category[blocks[t_pack]],
                                      category[blocks[s_pack]]):
            audio = archive.audio_sources.get(src.source_id)
            if audio is not None:
                payload.append((tgt.source_id, bytearray(audio.get_data())))
    for sid, data in payload:  # read every source first: same archive both ways
        audio = archive.audio_sources.get(sid)
        if audio is not None:
            audio.set_data(data)
    streams = {k: v for k, v in archive.wwise_streams.items() if v.modified}
    _GRUNT_CACHE[key] = streams
    return streams


def ordered_source_ids(archive, bank_name=None):
    """Hierarchy source ids of one voice bank, in order. A game voice package
    holds exactly one bank, so the first one is right; a fan-dub patch bundles
    two dozen, so the caller names the one it wants."""
    banks = list(archive.wwise_banks.values())
    bank = banks[0]
    if bank_name is not None and len(banks) > 1:
        for b in banks:
            if b.dep and b.dep.data.strip("\x00").endswith("/" + bank_name):
                bank = b
                break
        else:
            raise SystemExit(f"bank {bank_name} not found in archive")
    ids = []
    for entry in bank.hierarchy.entries.values():
        for s in getattr(entry, "sources", None) or []:
            ids.append(s.source_id)
    return ids


def load(pkg):
    """`pkg` is a package id inside the game's data dir, or -- when it carries
    a path separator -- a repo-relative path to a fan-dub source (EXTRA_LANGS)."""
    path = os.path.join(HERE, pkg) if os.sep in pkg else os.path.join(GAMEDATA, pkg)
    ar = core.GameArchive.from_file(path)
    if ar is None:
        raise SystemExit(f"failed to load {pkg}")
    return ar


def write_stream_patch(patch, out_dir):
    """Serialize a stream-only patch, storing each distinct audio blob ONCE and
    pointing every stream id that carries those same bytes at the one copy.

    The archive's table of contents keys each entry by file id and locates its
    audio with an explicit (offset, size) into the `.stream` blob, so nothing
    stops several ids from sharing an offset. core.GameArchive.to_file never
    does: it appends every payload behind a cursor that only moves forward.

    That costs nothing on a per-base-language build, where each id appears once.
    It costs 8x on a --universal build, whose whole point is writing the SAME
    audio into all nine language packages -- identical bytes, different id per
    package, so the naive writer stores eight redundant copies.

    Only the offsets change; every id still gets its own 80-byte toc entry and
    its own 12-byte toc_data header, exactly as before.

    A patch may also carry wwise_banks (with their deps), which go in the toc
    data rather than the stream blob and so are written straight through --
    build_combo_patch ships one, the exertion bank (see grunt_bank). Text banks
    and videos are still not handled here."""
    from const import WWISE_STREAM, WWISE_BANK, WWISE_DEP
    from util import MemoryStream, pad_to_16_byte_align

    assert not patch.text_banks and not patch.video_sources

    streams = list(patch.wwise_streams.values())
    banks = list(patch.wwise_banks.values())
    deps = [b.dep for b in banks if b.dep is not None and not b.dep.skip]
    num_files = len(streams) + len(banks) + len(deps)
    num_types = sum(1 for group in (streams, banks, deps) if group)

    toc_file = MemoryStream()
    toc_file.write(struct.pack("<IIII56s", patch.magic, num_types, num_files,
                               patch.unknown, patch.unk4Data))
    patch.write_type_header(toc_file, WWISE_STREAM, len(streams))
    if banks:
        patch.write_type_header(toc_file, WWISE_BANK, len(banks))
    if deps:
        patch.write_type_header(toc_file, WWISE_DEP, len(deps))

    toc_data_offset = toc_file.tell() + 80 * num_files + 8
    stream_file_offset = 0
    toc_entries, toc_data, stream_data = [], [], []
    seen = {}  # blob digest -> offset already written for those bytes

    for entry_index, stream in enumerate(streams):
        data = stream.get_data()
        s_data = pad_to_16_byte_align(data)
        key = hashlib.blake2b(s_data, digest_size=16).digest()
        offset = seen.get(key)
        if offset is None:
            offset = seen[key] = stream_file_offset
            stream_data.append(s_data)
            stream_file_offset += len(s_data)

        toc_entry = core.TocHeader()
        toc_entry.file_id = stream.get_id()
        toc_entry.type_id = WWISE_STREAM
        toc_entry.toc_data_offset = toc_data_offset
        toc_entry.stream_file_offset = offset
        toc_entry.toc_data_size = 0x0C
        toc_entry.stream_size = len(data)
        toc_entry.entry_index = entry_index
        toc_entries.append(toc_entry)
        toc_data.append(bytes.fromhex("D82F767800000000") + struct.pack("<Q", len(data)))
        toc_data_offset += 16

    entry_index = len(streams)
    for bank in banks:
        bank_data = bank.generate(patch.audio_sources)
        toc_entry = core.TocHeader()
        toc_entry.file_id = bank.get_id()
        toc_entry.type_id = WWISE_BANK
        toc_entry.toc_data_offset = toc_data_offset
        toc_entry.stream_file_offset = stream_file_offset
        toc_entry.toc_data_size = len(bank_data) + 16
        toc_entry.entry_index = entry_index
        toc_entries.append(toc_entry)
        blob = (bytes.fromhex("D82F7678") + struct.pack("<I", len(bank_data))
                + struct.pack("<Q", bank.get_id()) + pad_to_16_byte_align(bank_data))
        toc_data.append(blob)
        toc_data_offset += len(blob)
        entry_index += 1

    for dep in deps:
        dep_data = dep.get_data()
        toc_entry = core.TocHeader()
        toc_entry.file_id = dep.file_id
        toc_entry.type_id = WWISE_DEP
        toc_entry.toc_data_offset = toc_data_offset
        toc_entry.stream_file_offset = stream_file_offset
        toc_entry.toc_data_size = len(dep_data)
        toc_entry.entry_index = entry_index
        toc_entries.append(toc_entry)
        blob = pad_to_16_byte_align(dep_data)
        toc_data.append(blob)
        toc_data_offset += len(blob)
        entry_index += 1

    toc_file.write(b"".join(e.get_data() for e in toc_entries))
    toc_file.advance(8)
    toc_file.write(b"".join(toc_data))

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, patch.name), "w+b") as f:
        min_size = len(toc_entries) * 256
        if len(toc_file.data) < min_size:
            toc_file.write(bytearray(min_size - len(toc_file.data)))
        f.write(toc_file.data)
    with open(os.path.join(out_dir, patch.name + ".stream"), "w+b") as f:
        f.write(b"".join(stream_data))

    return len(streams), len(seen)


def build_combo_patch(target_voice, src_voice, src_lang, base_langs, vmap, out_dir):
    """Fill the `target_voice` slot with `src_voice` audio in `src_lang`,
    overriding every base package in `base_langs` (which hold target_voice's
    own ids). Same-type (target==src) is cross-language: ids/order are
    identical across languages, full positional swap is exact. Different-type
    within the same group is cross-type (different actor, no shared ids):
    aligned via the content-verified voice_crosswalk.json subset instead of
    raw position (see cross_type_index_map), and carries src_voice's exertions
    too (see grunt_streams). Returns number of modified streams, or None if
    nothing to do."""
    src_pkg = vmap.get(src_lang, {}).get(src_voice)
    if not src_pkg:
        return None
    src = load(src_pkg)
    s_ids = ordered_source_ids(src, src_voice)
    cross_map = cross_type_index_map(target_voice, src_voice)

    modified_streams = {}
    for base in base_langs:
        if base == src_lang and target_voice == src_voice:
            continue  # identity, skip (same voice, same language)
        base_pkg = vmap.get(base, {}).get(target_voice)
        if not base_pkg:
            continue
        tgt = load(base_pkg)
        t_ids = ordered_source_ids(tgt, target_voice)
        if cross_map is None:
            if len(t_ids) != len(s_ids):
                print(f"  ! count mismatch {base}/{VOICE_SHORT[target_voice]}<-"
                      f"{VOICE_SHORT[src_voice]} {len(t_ids)}!={len(s_ids)}, skip")
                continue
            pairs = list(zip(t_ids, s_ids))
        else:
            pairs = [(t_ids[t_idx], s_ids[s_idx])
                     for t_idx, s_idx in cross_map.items()
                     if s_idx < len(s_ids) and t_idx < len(t_ids)]
        for ti, si in pairs:
            if ti not in tgt.audio_sources or si not in src.audio_sources:
                continue
            data = src.audio_sources[si].get_data()
            if not data:
                continue
            tgt.audio_sources[ti].set_data(bytearray(data))
        for k, v in tgt.wwise_streams.items():
            if v.modified:
                modified_streams[k] = v

    if cross_map is not None:
        # cross-type: the exertions (grunts, pain, screams) live in their own
        # non-localized bank and are keyed by voice type, so they have to move
        # with the actor or the slot keeps grunting in its own voice/gender.
        modified_streams.update(grunt_streams(target_voice, src_voice))
        grunt_banks, grunt_sources = grunt_bank()
    else:
        grunt_banks, grunt_sources = {}, {}

    if not modified_streams:
        return None

    os.makedirs(out_dir, exist_ok=True)
    patch = core.GameArchive()
    patch.name = "9ba626afa44a3aa3.patch_0"
    patch.magic = 0xF0000011
    patch.num_types = patch.num_files = patch.unknown = 0
    patch.unk4Data = PATCH_UNK4
    patch.audio_sources = grunt_sources
    patch.wwise_banks = grunt_banks
    patch.wwise_streams = modified_streams
    patch.text_banks = {}
    patch.video_sources = {}
    write_stream_patch(patch, out_dir)
    return len(modified_streams)


def gen_patches(vmap, present, base_langs):
    """Generate all patch folders under OUT (slow; loads/extracts audio).
    Layout: OUT/<target>/<src_voice>/<lang>/patch."""
    for target in VOICES:
        tdir = VOICE_SHORT[target]
        for src_voice in GROUP[target]:
            sdir = VOICE_SHORT[src_voice]
            for lang in present:
                if src_voice not in vmap.get(lang, {}):
                    continue
                out_dir = os.path.join(OUT, tdir, sdir, lang)
                n = build_combo_patch(target, src_voice, lang, base_langs, vmap, out_dir)
                tag = f"{tdir}<-{sdir}/{lang}"
                print(f"  {tag}: {'native' if n is None else str(n)+' streams'}")


def gen_manifest(vmap, present, ui_lang, guid=None, fandubs=False):
    """Write manifest.json into OUT in the given interface language.
    Each slot lists Native, then own-type languages, then group-partner
    (cross-type) languages."""
    S = STRINGS[ui_lang]
    options = []
    for target in VOICES:
        tdir = VOICE_SHORT[target]
        vlabel = S["voice"][target]
        suboptions = [{
            "Name": S["native_name"],
            "Description": S["native_desc"].format(voice=vlabel),
            "Include": [],
        }]
        for src_voice in GROUP[target]:
            sdir = VOICE_SHORT[src_voice]
            same = src_voice == target
            for lang in present:
                if src_voice not in vmap.get(lang, {}):
                    continue
                if not os.path.isdir(os.path.join(OUT, tdir, sdir, lang)):
                    continue  # patch not built (e.g. identity-only)
                rel = f"{tdir}/{sdir}/{lang}"
                llabel = S["lang"].get(lang, lang)
                if same:
                    name = llabel
                    desc = S["sub_desc"].format(voice=vlabel, lang=llabel)
                else:
                    brief = VOICE_BRIEF[ui_lang][src_voice]
                    name = CROSS[ui_lang][0].format(brief=brief, lang=llabel)
                    desc = CROSS[ui_lang][1].format(brief=brief, lang=llabel, slot=vlabel)
                sub = {"Name": name, "Description": desc, "Include": [rel]}
                flag = f"flags/{lang}.png"
                if os.path.isfile(os.path.join(OUT, flag)):
                    sub["Image"] = flag  # language flag, for quick visual pick
                elif lang not in _MISSING_FLAGS:
                    _MISSING_FLAGS.add(lang)
                    print(f"  ! no hay flags/{lang}.png: ese idioma sale sin bandera "
                          f"en el menu")
                suboptions.append(sub)
        if len(suboptions) > 1:
            options.append({
                "Name": vlabel,
                "Description": S["slot_desc"].format(voice=vlabel),
                "SubOptions": suboptions,
            })
    manifest = {
        "Version": 1,
        "Guid": guid or GUID[ui_lang],
        "Name": S["mod_name"] + (FANDUB_SUFFIX if fandubs else ""),
        "Description": S["mod_desc"] + (FANDUB_CREDIT[ui_lang] if fandubs else ""),
        "Options": options,
    }
    if os.path.isfile(os.path.join(OUT, "covers", COVER)):
        manifest["IconPath"] = f"covers/{COVER}"
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"),
              indent=2, ensure_ascii=False)
    print(f"manifest [{ui_lang}]: {len(options)} voice slots -> {OUT}/manifest.json")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=list(STRINGS),
                    help="base/game language this build targets (UI + base package)")
    ap.add_argument("--skip-patches", action="store_true",
                    help="solo regenerar manifest (reusa carpetas de patch existentes)")
    ap.add_argument("--universal", action="store_true",
                    help="un solo build que sirve para CUALQUIER idioma de juego: "
                         "cada patch lleva los stream ids de los 9 paquetes base "
                         "a la vez. Pesa ~8x en disco, pero como son 8 copias del "
                         "MISMO audio, un .7z con diccionario grande las deduplica "
                         "y la descarga queda igual que un build de un solo idioma. "
                         "--lang pasa a ser solo el idioma de la interfaz.")
    ap.add_argument("--fandubs", action="store_true",
                    help="incluir los idiomas de fandub de EXTRA_LANGS (ej. ruso). "
                         "Apagado por defecto: son assets de terceros con permisos "
                         "propios, entran solo si se piden explicitamente.")
    args = ap.parse_args()

    slim.slim_init(GAMEDATA)
    vmap = json.load(open(os.path.join(HERE, "voice_map.json")))
    game_langs = sorted(vmap.keys())  # real game packages = possible base languages
    if args.fandubs:
        vmap.update(extra_voice_map())  # fan dubs from assets/, if present
    present = sorted(vmap.keys())      # selectable voice languages (game + fandubs)

    # A fandub has no game package of its own, so it can never be a base language.
    if args.universal:
        base_langs = game_langs
    else:
        base_langs = [b for b in base_langs_for(args.lang) if b in game_langs]
    if args.universal:
        guid = GUID_UNIVERSAL_FANDUBS if args.fandubs else GUID_UNIVERSAL
    else:
        guid = None

    # The fandub build is a separate download, so it gets its own output folder
    # and both can sit side by side instead of overwriting each other.
    global OUT
    if args.fandubs:
        OUT = os.path.join(HERE, "mod", "HelldiversIntlFandubs")

    print(f"languages on disk: {present}")
    if args.universal:
        print(f"build UNIVERSAL  ui={args.lang}  base packages overridden: {base_langs}")
    else:
        print(f"build lang={args.lang}  base packages overridden: {base_langs}")

    if not args.skip_patches:
        if os.path.exists(OUT):
            shutil.rmtree(OUT)
        os.makedirs(OUT, exist_ok=True)
        gen_patches(vmap, present, base_langs)
    elif not os.path.isdir(OUT):
        raise SystemExit("--skip-patches pero no existe mod/; corre sin el flag primero")

    # copy language flags into the mod so suboptions can reference flags/<lang>.png
    if os.path.isdir(FLAGS_SRC):
        dst = os.path.join(OUT, "flags")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(FLAGS_SRC, dst)

    src_cover = os.path.join(COVERS_SRC, COVER)
    if os.path.isfile(src_cover):
        os.makedirs(os.path.join(OUT, "covers"), exist_ok=True)
        shutil.copy(src_cover, os.path.join(OUT, "covers", COVER))

    gen_manifest(vmap, present, args.lang, guid, args.fandubs)


if __name__ == "__main__":
    main()
