#!/usr/bin/env python3
"""
Ventana chica para randomize_voices.py: elegir la carpeta del mod y la del
juego (se guardan), tildar que idiomas sacar del sorteo, restringir por voz
que genero puede tocarle a cada slot, sumar fandubs si el mod elegido los
trae, randomizar, y abrir el juego. Toda la logica real vive en
randomize_voices.run_randomize; esto es solo la interfaz.

Interfaz localizada a 11 idiomas (los 9 del juego + ruso/coreano de
fandub), default ingles, se recuerda el ultimo elegido. Los nombres de
idioma de voz (LANG_NAMES) y de tipo de voz (VOICE_DISPLAY) tambien estan
en I18N por idioma de interfaz -- copiados de build_mod.STRINGS a mano en
vez de importar build_mod (import pesado: numpy/lz4/core, se difiere al
primer click de Randomizar para no romper el arranque de la ventana).
"""
import json, os, sys, threading, tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

STEAM_APPID = "553850"  # Helldivers 2
DEFAULT_UI_LANG = "us"
VOICE_ORDER = ["female1", "male1", "female2", "purist"]
FANDUB_LANGS = ["ru", "ko"]

# idioma de interfaz -> nombre nativo, para el selector (siempre en su
# propio idioma, sin importar que interfaz este activa ahora)
UI_LANG_ENDONYMS = {
    "us": "English", "es": "Espa\u00f1ol", "jp": "\u65e5\u672c\u8a9e",
    "de": "Deutsch", "fr": "Fran\u00e7ais", "it": "Italiano",
    "ms": "Espa\u00f1ol (LatAm)", "bp": "Portugu\u00eas (Brasil)",
    "cn": "\u4e2d\u6587", "ru": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439",
    "ko": "\ud55c\uad6d\uc5b4",
}
UI_LANG_ORDER = ["us", "es", "jp", "de", "fr", "it", "ms", "bp", "cn", "ru", "ko"]

# palabra "predeterminada/o" (o equivalente) por idioma de interfaz, para
# armar VOICE_DISPLAY como f"{DEFAULT_WORD} {n}" -- copiado del patron ya
# usado en el manifest del mod (build_mod.STRINGS), version corta.
DEFAULT_WORD = {
    "us": "Default", "es": "Predeterminada", "jp": "\u30c7\u30d5\u30a9\u30eb\u30c8",
    "de": "Standard", "fr": "D\u00e9faut", "it": "Predefinita",
    "bp": "Padr\u00e3o", "cn": "\u9ed8\u8ba4", "ru": "\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u044b\u0439",
    "ko": "\uae30\ubcf8",
}
DEFAULT_WORD["ms"] = DEFAULT_WORD["es"]
DEFAULT_WORD_NO_SPACE = {"jp", "cn", "ko"}  # CJK: sin espacio antes del numero

# nombres de idioma de voz por idioma de interfaz (copiado de build_mod.STRINGS
# para us/es/jp/de/fr/it/bp/cn; ru/ko son nuevos, traducidos a mano)
LANG_NAMES = {
    "us": {"us": "English", "jp": "Japanese", "de": "German", "fr": "French",
           "it": "Italian", "es": "Spanish (Spain)", "ms": "Spanish (LatAm)",
           "bp": "Portuguese (Brazil)", "cn": "Chinese (Simplified)",
           "ru": "Russian (fan dub)", "ko": "Korean (fan dub)"},
    "es": {"us": "Ingl\u00e9s", "jp": "Japon\u00e9s", "de": "Alem\u00e1n", "fr": "Franc\u00e9s",
           "it": "Italiano", "es": "Espa\u00f1ol (Espa\u00f1a)", "ms": "Espa\u00f1ol (LatAm)",
           "bp": "Portugu\u00e9s (Brasil)", "cn": "Chino (simplificado)",
           "ru": "Ruso (fandub)", "ko": "Coreano (fandub)"},
    "jp": {"us": "\u82f1\u8a9e", "jp": "\u65e5\u672c\u8a9e", "de": "\u30c9\u30a4\u30c4\u8a9e",
           "fr": "\u30d5\u30e9\u30f3\u30b9\u8a9e", "it": "\u30a4\u30bf\u30ea\u30a2\u8a9e",
           "es": "\u30b9\u30da\u30a4\u30f3\u8a9e\uff08\u30b9\u30da\u30a4\u30f3\uff09",
           "ms": "\u30b9\u30da\u30a4\u30f3\u8a9e\uff08\u4e2d\u5357\u7c73\uff09",
           "bp": "\u30dd\u30eb\u30c8\u30ac\u30eb\u8a9e\uff08\u30d6\u30e9\u30b8\u30eb\uff09",
           "cn": "\u4e2d\u56fd\u8a9e\uff08\u7c21\u4f53\uff09",
           "ru": "\u30ed\u30b7\u30a2\u8a9e\uff08\u30d5\u30a1\u30f3\u5439\u304d\u66ff\u3048\uff09",
           "ko": "\u97d3\u56fd\u8a9e\uff08\u30d5\u30a1\u30f3\u5439\u304d\u66ff\u3048\uff09"},
    "de": {"us": "Englisch", "jp": "Japanisch", "de": "Deutsch", "fr": "Franz\u00f6sisch",
           "it": "Italienisch", "es": "Spanisch (Spanien)",
           "ms": "Spanisch (Lateinamerika)", "bp": "Portugiesisch (Brasilien)",
           "cn": "Chinesisch (vereinfacht)", "ru": "Russisch (Fan-Dub)",
           "ko": "Koreanisch (Fan-Dub)"},
    "fr": {"us": "Anglais", "jp": "Japonais", "de": "Allemand", "fr": "Fran\u00e7ais",
           "it": "Italien", "es": "Espagnol (Espagne)",
           "ms": "Espagnol (Am\u00e9rique latine)", "bp": "Portugais (Br\u00e9sil)",
           "cn": "Chinois (simplifi\u00e9)", "ru": "Russe (fandub)",
           "ko": "Cor\u00e9en (fandub)"},
    "it": {"us": "Inglese", "jp": "Giapponese", "de": "Tedesco", "fr": "Francese",
           "it": "Italiano", "es": "Spagnolo (Spagna)",
           "ms": "Spagnolo (America Latina)", "bp": "Portoghese (Brasile)",
           "cn": "Cinese (semplificato)", "ru": "Russo (fandub)",
           "ko": "Coreano (fandub)"},
    "bp": {"us": "Ingl\u00eas", "jp": "Japon\u00eas", "de": "Alem\u00e3o", "fr": "Franc\u00eas",
           "it": "Italiano", "es": "Espanhol (Espanha)",
           "ms": "Espanhol (Am\u00e9rica Latina)", "bp": "Portugu\u00eas (Brasil)",
           "cn": "Chin\u00eas (simplificado)", "ru": "Russo (fandub)",
           "ko": "Coreano (fandub)"},
    "cn": {"us": "\u82f1\u8bed", "jp": "\u65e5\u8bed", "de": "\u5fb7\u8bed", "fr": "\u6cd5\u8bed",
           "it": "\u610f\u5927\u5229\u8bed", "es": "\u897f\u73ed\u7259\u8bed\uff08\u897f\u73ed\u7259\uff09",
           "ms": "\u897f\u73ed\u7259\u8bed\uff08\u62c9\u7f8e\uff09",
           "bp": "\u8461\u8404\u7259\u8bed\uff08\u5df4\u897f\uff09",
           "cn": "\u4e2d\u6587\uff08\u7b80\u4f53\uff09",
           "ru": "\u4fc4\u8bed\uff08\u7c89\u4e1d\u914d\u97f3\uff09",
           "ko": "\u97e9\u8bed\uff08\u7c89\u4e1d\u914d\u97f3\uff09"},
    "ru": {"us": "\u0410\u043d\u0433\u043b\u0438\u0439\u0441\u043a\u0438\u0439",
           "jp": "\u042f\u043f\u043e\u043d\u0441\u043a\u0438\u0439",
           "de": "\u041d\u0435\u043c\u0435\u0446\u043a\u0438\u0439",
           "fr": "\u0424\u0440\u0430\u043d\u0446\u0443\u0437\u0441\u043a\u0438\u0439",
           "it": "\u0418\u0442\u0430\u043b\u044c\u044f\u043d\u0441\u043a\u0438\u0439",
           "es": "\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439 (\u0418\u0441\u043f\u0430\u043d\u0438\u044f)",
           "ms": "\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439 (\u041b\u0430\u0442. \u0410\u043c\u0435\u0440\u0438\u043a\u0430)",
           "bp": "\u041f\u043e\u0440\u0442\u0443\u0433\u0430\u043b\u044c\u0441\u043a\u0438\u0439 (\u0411\u0440\u0430\u0437\u0438\u043b\u0438\u044f)",
           "cn": "\u041a\u0438\u0442\u0430\u0439\u0441\u043a\u0438\u0439 (\u0443\u043f\u0440\u043e\u0449\u0451\u043d\u043d\u044b\u0439)",
           "ru": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439 (\u0444\u0430\u043d-\u0434\u0430\u0431)",
           "ko": "\u041a\u043e\u0440\u0435\u0439\u0441\u043a\u0438\u0439 (\u0444\u0430\u043d-\u0434\u0430\u0431)"},
    "ko": {"us": "\uc601\uc5b4", "jp": "\uc77c\ubcf8\uc5b4", "de": "\ub3c5\uc77c\uc5b4",
           "fr": "\ud504\ub791\uc2a4\uc5b4", "it": "\uc774\ud0c8\ub9ac\uc544\uc5b4",
           "es": "\uc2a4\ud398\uc778\uc5b4 (\uc2a4\ud398\uc778)",
           "ms": "\uc2a4\ud398\uc778\uc5b4 (\ub77c\ud2f4\uc544\uba54\ub9ac\uce74)",
           "bp": "\ud3ec\ub974\ud22c\uac08\uc5b4 (\ube0c\ub77c\uc9c8)",
           "cn": "\uc911\uad6d\uc5b4 (\uac04\uccb4)",
           "ru": "\ub7ec\uc2dc\uc544\uc5b4 (\ud32c\ub354\ube59)",
           "ko": "\ud55c\uad6d\uc5b4 (\ud32c\ub354\ube59)"},
}
LANG_NAMES["ms"] = LANG_NAMES["es"]

CARD_ACCENTS = {
    "mod": "#ff6b6b", "dir": "#4da6ff", "langs": "#ffb000", "voices": "#5be7a9",
    "fandub": "#c77dff",
}

# -- cadenas de interfaz por idioma. "ms" reusa "es" (misma variante de
# idioma, ver STRINGS["ms"] = STRINGS["es"] en build_mod.py). --
I18N = {
"us": {
    "subtitle": "RANDOMIZER", "ui_lang_label": "Interface language",
    "mod_title": "Main mod",
    "mod_sub": "Folder where you unzipped your mod (the Nexus zip, or wherever Arsenal "
               "extracted it): \"Helldivers International\", or the \"+ FANDUBS\" variant "
               "if that's the one you have -- whichever you downloaded, use that one, you "
               "don't need the other. It holds the audio for all 9 languages, no need to "
               "have them downloaded on Steam.",
    "dir_title": "Game folder",
    "dir_sub": "The data/ folder inside your Helldivers 2 install, where the result gets written.",
    "langs_title": "Exclude from the draw", "langs_sub": "These languages will never be picked.",
    "voices_title": "Voice restrictions",
    "voices_sub": "How far each slot's voice can stray from its original.",
    "mode_own": "Only this voice (other languages)",
    "mode_gender": "Same gender (this voice or its pair)", "mode_any": "Any gender",
    "balance_label": "Balance genders (always 2 male and 2 female voices)",
    "avoid_repeat_label": "Don't repeat languages between slots",
    "fandub_title": "Fandubs",
    "fandub_sub": "Only matters if you picked the \"Helldivers International - FANDUBS\" "
                  "folder above (not the regular mod). Tick the languages you want in the draw:",
    "btn_choose": "Choose...", "btn_randomize": "RANDOMIZE",
    "btn_randomizing": "Randomizing...", "btn_open_game": "Open game", "btn_close": "Close",
    "err_missing_folder_title": "Missing folder",
    "err_mod_dir_missing": "Choose the main mod folder first.",
    "err_game_dir_missing": "Choose the game's data/ folder first.",
    "err_wrong_path_title": "Wrong path",
    "err_mod_dir_wrong": "That folder has no manifest.json. Choose the root folder where "
                         "you unzipped \"Helldivers International\" (the one with "
                         "manifest.json inside).",
    "err_game_dir_wrong": "That folder has no bundles.nxa. Choose the data/ folder inside "
                          "your Helldivers 2 install.",
    "err_no_langs_title": "No languages",
    "err_no_langs": "You can't exclude every language.",
    "err_failed_title": "Couldn't randomize",
    "err_failed_body": "Something went wrong:\n\n{e}\n\nCheck that the folders you chose are correct.",
    "err_open_game_title": "Couldn't open the game",
    "err_open_game_body": "{e}\n\nTry opening it manually from Steam.",
    "result_window_title": "Voices assigned", "result_header": "NEW VOICES ASSIGNED",
    "result_sub": "Jump into the game to hear them.",
},
"es": {
    "subtitle": "RANDOMIZADOR", "ui_lang_label": "Idioma de la interfaz",
    "mod_title": "Mod principal",
    "mod_sub": "Carpeta donde descomprimiste tu mod (el zip de Nexus, o donde Arsenal lo "
               "extrajo): \"Helldivers International\", o la variante \"+ FANDUBS\" si es "
               "la que tienes. Usa la que hayas descargado, no hace falta la otra. Ahi "
               "esta el audio de los 9 idiomas, no hace falta tenerlos descargados en Steam.",
    "dir_title": "Carpeta del juego",
    "dir_sub": "La carpeta data/ dentro de tu instalacion de Helldivers 2, donde se escribe el resultado.",
    "langs_title": "Excluir del sorteo", "langs_sub": "Estos idiomas nunca saldran sorteados.",
    "voices_title": "Restricciones de voz",
    "voices_sub": "Que tan lejos puede alejarse cada ranura de su voz original.",
    "mode_own": "Solo esta voz (otros idiomas)",
    "mode_gender": "Mismo genero (esta voz o su pareja)", "mode_any": "Cualquier genero",
    "balance_label": "Equilibrar generos (siempre 2 voces masculinas y 2 femeninas)",
    "avoid_repeat_label": "No repetir idiomas entre ranuras",
    "fandub_title": "Fandubs",
    "fandub_sub": "Solo aplica si arriba elegiste la carpeta de la variante \"Helldivers "
                  "International - FANDUBS\" (no el mod normal). Marca los idiomas que "
                  "quieres incluir en el sorteo:",
    "btn_choose": "Elegir...", "btn_randomize": "RANDOMIZAR",
    "btn_randomizing": "Randomizando...", "btn_open_game": "Abrir juego", "btn_close": "Cerrar",
    "err_missing_folder_title": "Falta la carpeta",
    "err_mod_dir_missing": "Elige primero la carpeta del mod principal.",
    "err_game_dir_missing": "Elige primero la carpeta data/ del juego.",
    "err_wrong_path_title": "Ruta incorrecta",
    "err_mod_dir_wrong": "Esa carpeta no tiene manifest.json. Elige la carpeta raiz donde "
                         "descomprimiste \"Helldivers International\" (la que tiene "
                         "manifest.json adentro).",
    "err_game_dir_wrong": "Esa carpeta no tiene bundles.nxa. Elige la carpeta data/ dentro "
                          "de tu instalacion de Helldivers 2.",
    "err_no_langs_title": "Sin idiomas",
    "err_no_langs": "No puedes excluir todos los idiomas.",
    "err_failed_title": "No se pudo randomizar",
    "err_failed_body": "Algo fallo:\n\n{e}\n\nRevisa que las carpetas elegidas sean correctas.",
    "err_open_game_title": "No se pudo abrir el juego",
    "err_open_game_body": "{e}\n\nIntenta abrirlo manualmente desde Steam.",
    "result_window_title": "Voces asignadas", "result_header": "VOCES NUEVAS ASIGNADAS",
    "result_sub": "Entra al juego para escucharlas.",
},
"jp": {
    "subtitle": "\u30e9\u30f3\u30c0\u30de\u30a4\u30b6\u30fc", "ui_lang_label": "\u8868\u793a\u8a00\u8a9e",
    "mod_title": "\u30e1\u30a4\u30f3MOD",
    "mod_sub": "MOD\u3092\u89e3\u51cd\u3057\u305f\u30d5\u30a9\u30eb\u30c0\uff08Nexus\u306ezip\u3001"
               "\u307e\u305f\u306fArsenal\u304c\u5c55\u958b\u3057\u305f\u5834\u6240\uff09\uff1a"
               "\u300cHelldivers International\u300d\u3001\u307e\u305f\u306f\u6301\u3063\u3066"
               "\u3044\u308b\u306a\u3089\u300c+ FANDUBS\u300d\u7248\u3002\u30c0\u30a6\u30f3\u30ed"
               "\u30fc\u30c9\u3057\u305f\u65b9\u3092\u4f7f\u7528\u3001\u3082\u3046\u4e00\u65b9\u306f"
               "\u4e0d\u8981\u3002\u30029\u8a00\u8a9e\u5206\u306e\u97f3\u58f0\u304c\u5165\u3063\u3066"
               "\u3044\u308b\u306e\u3067\u3001Steam\u3067\u30c0\u30a6\u30f3\u30ed\u30fc\u30c9\u3057"
               "\u3066\u3044\u306a\u304f\u3066\u3082\u5927\u4e08\u592b\u3002",
    "dir_title": "\u30b2\u30fc\u30e0\u30d5\u30a9\u30eb\u30c0",
    "dir_sub": "Helldivers 2\u30a4\u30f3\u30b9\u30c8\u30fc\u30eb\u5185\u306edata/\u30d5\u30a9"
               "\u30eb\u30c0\u3002\u7d50\u679c\u306f\u3053\u3053\u306b\u66f8\u304d\u8fbc\u307e"
               "\u308c\u307e\u3059\u3002",
    "langs_title": "\u62bd\u9078\u304b\u3089\u9664\u5916",
    "langs_sub": "\u3053\u308c\u3089\u306e\u8a00\u8a9e\u306f\u62bd\u9078\u3055\u308c\u307e\u305b\u3093\u3002",
    "voices_title": "\u97f3\u58f0\u306e\u5236\u9650",
    "voices_sub": "\u5404\u30b9\u30ed\u30c3\u30c8\u306e\u58f0\u304c\u5143\u304b\u3089\u3069\u308c"
                  "\u3060\u3051\u96e2\u308c\u3066\u3088\u3044\u304b\u3002",
    "mode_own": "\u3053\u306e\u58f0\u306e\u307f\uff08\u4ed6\u8a00\u8a9e\uff09",
    "mode_gender": "\u540c\u3058\u6027\u5225\uff08\u3053\u306e\u58f0\u304b\u30da\u30a2\uff09",
    "mode_any": "\u6027\u5225\u3092\u554f\u308f\u306a\u3044",
    "balance_label": "\u6027\u5225\u30d0\u30e9\u30f3\u30b9\uff08\u5e38\u306b\u7537\u62002\u30fb"
                     "\u5973\u62002\uff09",
    "avoid_repeat_label": "\u30b9\u30ed\u30c3\u30c8\u9593\u3067\u8a00\u8a9e\u3092\u91cd\u8907\u3055"
                          "\u305b\u306a\u3044",
    "fandub_title": "\u30d5\u30a1\u30f3\u30c0\u30d6",
    "fandub_sub": "\u4e0a\u3067\u300cHelldivers International - FANDUBS\u300d\u30d5\u30a9\u30eb"
                  "\u30c0\u3092\u9078\u3093\u3060\u5834\u5408\u306e\u307f\u6709\u52b9\uff08\u901a"
                  "\u5e38MOD\u3067\u306f\u7121\u52b9\uff09\u3002\u62bd\u9078\u306b\u542b\u3081\u308b"
                  "\u8a00\u8a9e\u306b\u30c1\u30a7\u30c3\u30af\uff1a",
    "btn_choose": "\u9078\u629e...", "btn_randomize": "\u30e9\u30f3\u30c0\u30de\u30a4\u30ba",
    "btn_randomizing": "\u30e9\u30f3\u30c0\u30de\u30a4\u30ba\u4e2d...",
    "btn_open_game": "\u30b2\u30fc\u30e0\u3092\u958b\u304f", "btn_close": "\u9589\u3058\u308b",
    "err_missing_folder_title": "\u30d5\u30a9\u30eb\u30c0\u672a\u9078\u629e",
    "err_mod_dir_missing": "\u5148\u306b\u30e1\u30a4\u30f3MOD\u306e\u30d5\u30a9\u30eb\u30c0\u3092"
                           "\u9078\u3093\u3067\u304f\u3060\u3055\u3044\u3002",
    "err_game_dir_missing": "\u5148\u306b\u30b2\u30fc\u30e0\u306edata/\u30d5\u30a9\u30eb\u30c0\u3092"
                            "\u9078\u3093\u3067\u304f\u3060\u3055\u3044\u3002",
    "err_wrong_path_title": "\u30d1\u30b9\u304c\u9055\u3044\u307e\u3059",
    "err_mod_dir_wrong": "\u305d\u306e\u30d5\u30a9\u30eb\u30c0\u306bmanifest.json\u304c\u3042\u308a"
                         "\u307e\u305b\u3093\u3002\u300cHelldivers International\u300d\u3092\u89e3"
                         "\u51cd\u3057\u305f\u30eb\u30fc\u30c8\u30d5\u30a9\u30eb\u30c0\uff08manifest"
                         ".json\u304c\u5165\u3063\u3066\u3044\u308b\u3082\u306e\uff09\u3092\u9078\u3093"
                         "\u3067\u304f\u3060\u3055\u3044\u3002",
    "err_game_dir_wrong": "\u305d\u306e\u30d5\u30a9\u30eb\u30c0\u306bbundles.nxa\u304c\u3042\u308a"
                          "\u307e\u305b\u3093\u3002Helldivers 2\u30a4\u30f3\u30b9\u30c8\u30fc\u30eb"
                          "\u5185\u306edata/\u30d5\u30a9\u30eb\u30c0\u3092\u9078\u3093\u3067\u304f"
                          "\u3060\u3055\u3044\u3002",
    "err_no_langs_title": "\u8a00\u8a9e\u304c\u3042\u308a\u307e\u305b\u3093",
    "err_no_langs": "\u3059\u3079\u3066\u306e\u8a00\u8a9e\u3092\u9664\u5916\u3059\u308b\u3053\u3068"
                    "\u306f\u3067\u304d\u307e\u305b\u3093\u3002",
    "err_failed_title": "\u30e9\u30f3\u30c0\u30de\u30a4\u30ba\u3067\u304d\u307e\u305b\u3093\u3067"
                        "\u3057\u305f",
    "err_failed_body": "\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f\uff1a\n\n{e}"
                       "\n\n\u9078\u3093\u3060\u30d5\u30a9\u30eb\u30c0\u304c\u6b63\u3057\u3044\u304b"
                       "\u78ba\u8a8d\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    "err_open_game_title": "\u30b2\u30fc\u30e0\u3092\u958b\u3051\u307e\u305b\u3093\u3067\u3057\u305f",
    "err_open_game_body": "{e}\n\nSteam\u304b\u3089\u624b\u52d5\u3067\u958b\u3044\u3066\u307f\u3066"
                          "\u304f\u3060\u3055\u3044\u3002",
    "result_window_title": "\u5272\u308a\u5f53\u3066\u3089\u308c\u305f\u58f0",
    "result_header": "\u65b0\u3057\u3044\u58f0\u304c\u5272\u308a\u5f53\u3066\u3089\u308c\u307e\u3057\u305f",
    "result_sub": "\u30b2\u30fc\u30e0\u306b\u5165\u3063\u3066\u8074\u3044\u3066\u307f\u307e\u3057\u3087\u3046\u3002",
},
"de": {
    "subtitle": "RANDOMIZER", "ui_lang_label": "Oberfl\u00e4chensprache",
    "mod_title": "Hauptmod",
    "mod_sub": "Ordner, in den du deinen Mod entpackt hast (die Nexus-Zip oder wo Arsenal sie "
               "entpackt hat): \"Helldivers International\" oder die Variante \"+ FANDUBS\", "
               "falls du die hast -- welche auch immer du heruntergeladen hast, die andere "
               "brauchst du nicht. Dort liegt das Audio aller 9 Sprachen, du musst sie nicht "
               "\u00fcber Steam heruntergeladen haben.",
    "dir_title": "Spielordner",
    "dir_sub": "Der data/-Ordner in deiner Helldivers-2-Installation, wohin das Ergebnis "
               "geschrieben wird.",
    "langs_title": "Vom Los ausschlie\u00dfen", "langs_sub": "Diese Sprachen werden nie ausgelost.",
    "voices_title": "Stimmen-Einschr\u00e4nkungen",
    "voices_sub": "Wie weit sich die Stimme jedes Slots von der Originalstimme entfernen darf.",
    "mode_own": "Nur diese Stimme (andere Sprachen)",
    "mode_gender": "Gleiches Geschlecht (diese Stimme oder ihr Partner)",
    "mode_any": "Beliebiges Geschlecht",
    "balance_label": "Geschlechter ausgleichen (immer 2 m\u00e4nnliche und 2 weibliche Stimmen)",
    "avoid_repeat_label": "Sprachen nicht zwischen Slots wiederholen",
    "fandub_title": "Fandubs",
    "fandub_sub": "Wirkt nur, wenn oben der Ordner der Variante \"Helldivers International - "
                  "FANDUBS\" gew\u00e4hlt wurde (nicht der normale Mod). Hake die Sprachen an, "
                  "die im Los vorkommen sollen:",
    "btn_choose": "W\u00e4hlen...", "btn_randomize": "ZUF\u00c4LLIG W\u00dcRFELN",
    "btn_randomizing": "W\u00fcrfeln...", "btn_open_game": "Spiel \u00f6ffnen",
    "btn_close": "Schlie\u00dfen",
    "err_missing_folder_title": "Ordner fehlt",
    "err_mod_dir_missing": "W\u00e4hle zuerst den Hauptmod-Ordner.",
    "err_game_dir_missing": "W\u00e4hle zuerst den data/-Ordner des Spiels.",
    "err_wrong_path_title": "Falscher Pfad",
    "err_mod_dir_wrong": "Dieser Ordner enth\u00e4lt keine manifest.json. W\u00e4hle den "
                         "Stammordner, in den du \"Helldivers International\" entpackt hast "
                         "(der mit manifest.json darin).",
    "err_game_dir_wrong": "Dieser Ordner enth\u00e4lt keine bundles.nxa. W\u00e4hle den "
                          "data/-Ordner deiner Helldivers-2-Installation.",
    "err_no_langs_title": "Keine Sprachen",
    "err_no_langs": "Du kannst nicht alle Sprachen ausschlie\u00dfen.",
    "err_failed_title": "W\u00fcrfeln fehlgeschlagen",
    "err_failed_body": "Etwas ist schiefgelaufen:\n\n{e}\n\nPr\u00fcfe, ob die gew\u00e4hlten "
                       "Ordner korrekt sind.",
    "err_open_game_title": "Spiel konnte nicht ge\u00f6ffnet werden",
    "err_open_game_body": "{e}\n\nVersuche, es manuell \u00fcber Steam zu \u00f6ffnen.",
    "result_window_title": "Stimmen zugewiesen", "result_header": "NEUE STIMMEN ZUGEWIESEN",
    "result_sub": "Starte das Spiel, um sie zu h\u00f6ren.",
},
"fr": {
    "subtitle": "RANDOMIZER", "ui_lang_label": "Langue de l'interface",
    "mod_title": "Mod principal",
    "mod_sub": "Dossier o\u00f9 tu as d\u00e9compress\u00e9 ton mod (le zip Nexus, ou l\u00e0 o\u00f9 "
               "Arsenal l'a extrait) : \u00ab Helldivers International \u00bb, ou la variante "
               "\u00ab + FANDUBS \u00bb si c'est celle-ci que tu as -- utilise celle que tu as "
               "t\u00e9l\u00e9charg\u00e9e, l'autre n'est pas n\u00e9cessaire. L'audio des 9 "
               "langues y est d\u00e9j\u00e0, pas besoin de les avoir t\u00e9l\u00e9charg\u00e9es "
               "sur Steam.",
    "dir_title": "Dossier du jeu",
    "dir_sub": "Le dossier data/ de ton installation de Helldivers 2, o\u00f9 le r\u00e9sultat "
               "est \u00e9crit.",
    "langs_title": "Exclure du tirage", "langs_sub": "Ces langues ne seront jamais tir\u00e9es.",
    "voices_title": "Restrictions de voix",
    "voices_sub": "\u00c0 quel point la voix de chaque emplacement peut s'\u00e9loigner de l'originale.",
    "mode_own": "Seulement cette voix (autres langues)",
    "mode_gender": "M\u00eame genre (cette voix ou sa paire)",
    "mode_any": "N'importe quel genre",
    "balance_label": "\u00c9quilibrer les genres (toujours 2 voix masculines et 2 f\u00e9minines)",
    "avoid_repeat_label": "Ne pas r\u00e9p\u00e9ter les langues entre les emplacements",
    "fandub_title": "Fandubs",
    "fandub_sub": "Ne s'applique que si tu as choisi ci-dessus le dossier de la variante "
                  "\u00ab Helldivers International - FANDUBS \u00bb (pas le mod normal). Coche "
                  "les langues \u00e0 inclure dans le tirage :",
    "btn_choose": "Choisir...", "btn_randomize": "RANDOMISER",
    "btn_randomizing": "Randomisation...", "btn_open_game": "Ouvrir le jeu", "btn_close": "Fermer",
    "err_missing_folder_title": "Dossier manquant",
    "err_mod_dir_missing": "Choisis d'abord le dossier du mod principal.",
    "err_game_dir_missing": "Choisis d'abord le dossier data/ du jeu.",
    "err_wrong_path_title": "Chemin incorrect",
    "err_mod_dir_wrong": "Ce dossier n'a pas de manifest.json. Choisis le dossier racine o\u00f9 "
                         "tu as d\u00e9compress\u00e9 \u00ab Helldivers International \u00bb "
                         "(celui qui contient manifest.json).",
    "err_game_dir_wrong": "Ce dossier n'a pas de bundles.nxa. Choisis le dossier data/ de ton "
                          "installation de Helldivers 2.",
    "err_no_langs_title": "Aucune langue",
    "err_no_langs": "Tu ne peux pas exclure toutes les langues.",
    "err_failed_title": "\u00c9chec de la randomisation",
    "err_failed_body": "Un probl\u00e8me est survenu :\n\n{e}\n\nV\u00e9rifie que les dossiers "
                       "choisis sont corrects.",
    "err_open_game_title": "Impossible d'ouvrir le jeu",
    "err_open_game_body": "{e}\n\nEssaie de l'ouvrir manuellement depuis Steam.",
    "result_window_title": "Voix assign\u00e9es", "result_header": "NOUVELLES VOIX ASSIGN\u00c9ES",
    "result_sub": "Lance le jeu pour les entendre.",
},
"it": {
    "subtitle": "RANDOMIZER", "ui_lang_label": "Lingua dell'interfaccia",
    "mod_title": "Mod principale",
    "mod_sub": "Cartella dove hai estratto la tua mod (lo zip di Nexus, o dove Arsenal l'ha "
               "estratta): \"Helldivers International\", oppure la variante \"+ FANDUBS\" se "
               "\u00e8 quella che hai -- usa quella che hai scaricato, non serve l'altra. "
               "Contiene l'audio delle 9 lingue, non serve averle scaricate su Steam.",
    "dir_title": "Cartella del gioco",
    "dir_sub": "La cartella data/ nella tua installazione di Helldivers 2, dove viene scritto "
               "il risultato.",
    "langs_title": "Escludi dal sorteggio",
    "langs_sub": "Queste lingue non verranno mai estratte.",
    "voices_title": "Restrizioni vocali",
    "voices_sub": "Quanto pu\u00f2 allontanarsi ogni slot dalla sua voce originale.",
    "mode_own": "Solo questa voce (altre lingue)",
    "mode_gender": "Stesso genere (questa voce o la sua coppia)", "mode_any": "Qualsiasi genere",
    "balance_label": "Bilancia i generi (sempre 2 voci maschili e 2 femminili)",
    "avoid_repeat_label": "Non ripetere le lingue tra gli slot",
    "fandub_title": "Fandub",
    "fandub_sub": "Vale solo se sopra hai scelto la cartella della variante \"Helldivers "
                  "International - FANDUBS\" (non la mod normale). Seleziona le lingue da "
                  "includere nel sorteggio:",
    "btn_choose": "Scegli...", "btn_randomize": "RANDOMIZZA",
    "btn_randomizing": "Randomizzazione...", "btn_open_game": "Apri il gioco", "btn_close": "Chiudi",
    "err_missing_folder_title": "Cartella mancante",
    "err_mod_dir_missing": "Scegli prima la cartella della mod principale.",
    "err_game_dir_missing": "Scegli prima la cartella data/ del gioco.",
    "err_wrong_path_title": "Percorso errato",
    "err_mod_dir_wrong": "Quella cartella non ha manifest.json. Scegli la cartella radice dove "
                         "hai estratto \"Helldivers International\" (quella con manifest.json "
                         "dentro).",
    "err_game_dir_wrong": "Quella cartella non ha bundles.nxa. Scegli la cartella data/ della "
                          "tua installazione di Helldivers 2.",
    "err_no_langs_title": "Nessuna lingua",
    "err_no_langs": "Non puoi escludere tutte le lingue.",
    "err_failed_title": "Randomizzazione non riuscita",
    "err_failed_body": "Qualcosa \u00e8 andato storto:\n\n{e}\n\nControlla che le cartelle "
                       "scelte siano corrette.",
    "err_open_game_title": "Impossibile aprire il gioco",
    "err_open_game_body": "{e}\n\nProva ad aprirlo manualmente da Steam.",
    "result_window_title": "Voci assegnate", "result_header": "NUOVE VOCI ASSEGNATE",
    "result_sub": "Entra nel gioco per ascoltarle.",
},
"bp": {
    "subtitle": "RANDOMIZER", "ui_lang_label": "Idioma da interface",
    "mod_title": "Mod principal",
    "mod_sub": "Pasta onde voc\u00ea descompactou seu mod (o zip da Nexus, ou onde o Arsenal "
               "extraiu): \"Helldivers International\", ou a variante \"+ FANDUBS\" se for "
               "essa que voc\u00ea tem -- use a que baixou, n\u00e3o precisa da outra. Ali "
               "est\u00e1 o \u00e1udio dos 9 idiomas, n\u00e3o precisa t\u00ea-los baixados na "
               "Steam.",
    "dir_title": "Pasta do jogo",
    "dir_sub": "A pasta data/ dentro da sua instala\u00e7\u00e3o de Helldivers 2, onde o "
               "resultado \u00e9 gravado.",
    "langs_title": "Excluir do sorteio", "langs_sub": "Esses idiomas nunca ser\u00e3o sorteados.",
    "voices_title": "Restri\u00e7\u00f5es de voz",
    "voices_sub": "O quanto a voz de cada slot pode se afastar da original.",
    "mode_own": "S\u00f3 esta voz (outros idiomas)",
    "mode_gender": "Mesmo g\u00eanero (esta voz ou sua parceira)", "mode_any": "Qualquer g\u00eanero",
    "balance_label": "Equilibrar g\u00eaneros (sempre 2 vozes masculinas e 2 femininas)",
    "avoid_repeat_label": "N\u00e3o repetir idiomas entre os slots",
    "fandub_title": "Fandubs",
    "fandub_sub": "S\u00f3 vale se voc\u00ea escolheu acima a pasta da variante \"Helldivers "
                  "International - FANDUBS\" (n\u00e3o o mod normal). Marque os idiomas que "
                  "quer incluir no sorteio:",
    "btn_choose": "Escolher...", "btn_randomize": "RANDOMIZAR",
    "btn_randomizing": "Randomizando...", "btn_open_game": "Abrir jogo", "btn_close": "Fechar",
    "err_missing_folder_title": "Falta a pasta",
    "err_mod_dir_missing": "Escolha primeiro a pasta do mod principal.",
    "err_game_dir_missing": "Escolha primeiro a pasta data/ do jogo.",
    "err_wrong_path_title": "Caminho incorreto",
    "err_mod_dir_wrong": "Essa pasta n\u00e3o tem manifest.json. Escolha a pasta raiz onde "
                         "voc\u00ea descompactou \"Helldivers International\" (a que tem "
                         "manifest.json dentro).",
    "err_game_dir_wrong": "Essa pasta n\u00e3o tem bundles.nxa. Escolha a pasta data/ da sua "
                          "instala\u00e7\u00e3o de Helldivers 2.",
    "err_no_langs_title": "Sem idiomas",
    "err_no_langs": "Voc\u00ea n\u00e3o pode excluir todos os idiomas.",
    "err_failed_title": "N\u00e3o foi poss\u00edvel randomizar",
    "err_failed_body": "Algo deu errado:\n\n{e}\n\nVerifique se as pastas escolhidas est\u00e3o "
                       "corretas.",
    "err_open_game_title": "N\u00e3o foi poss\u00edvel abrir o jogo",
    "err_open_game_body": "{e}\n\nTente abrir manualmente pela Steam.",
    "result_window_title": "Vozes atribu\u00eddas", "result_header": "NOVAS VOZES ATRIBU\u00cdDAS",
    "result_sub": "Entre no jogo para ouvi-las.",
},
"cn": {
    "subtitle": "\u968f\u673a\u5316\u5668", "ui_lang_label": "\u754c\u9762\u8bed\u8a00",
    "mod_title": "\u4e3bMOD",
    "mod_sub": "\u89e3\u538bMOD\u7684\u6587\u4ef6\u5939\uff08Nexus\u7684zip\uff0c\u6216Arsenal"
               "\u89e3\u538b\u7684\u4f4d\u7f6e\uff09\uff1a\u300cHelldivers International\u300d"
               "\uff0c\u6216\u8005\u300c+ FANDUBS\u300d\u7248\u672c\uff08\u5982\u679c\u4f60\u4e0b"
               "\u8f7d\u7684\u662f\u8fd9\u4e2a\uff09\u2014\u2014\u7528\u4f60\u4e0b\u8f7d\u7684\u90a3"
               "\u4e2a\u5c31\u884c\uff0c\u4e0d\u9700\u8981\u53e6\u4e00\u4e2a\u3002\u91cc\u9762\u5df2"
               "\u7ecf\u5305\u542b9\u79cd\u8bed\u8a00\u7684\u97f3\u9891\uff0c\u4e0d\u9700\u8981\u5728"
               "Steam\u4e0a\u4e0b\u8f7d\u8fd9\u4e9b\u8bed\u8a00\u3002",
    "dir_title": "\u6e38\u620f\u6587\u4ef6\u5939",
    "dir_sub": "Helldivers 2\u5b89\u88c5\u76ee\u5f55\u91cc\u7684data/\u6587\u4ef6\u5939\uff0c"
               "\u7ed3\u679c\u4f1a\u5199\u5165\u8fd9\u91cc\u3002",
    "langs_title": "\u4ece\u62bd\u53d6\u4e2d\u6392\u9664",
    "langs_sub": "\u8fd9\u4e9b\u8bed\u8a00\u6c38\u8fdc\u4e0d\u4f1a\u88ab\u62bd\u4e2d\u3002",
    "voices_title": "\u8bed\u97f3\u9650\u5236",
    "voices_sub": "\u6bcf\u4e2a\u4f4d\u7f6e\u7684\u8bed\u97f3\u53ef\u4ee5\u504f\u79bb\u539f\u58f0"
                  "\u591a\u8fdc\u3002",
    "mode_own": "\u4ec5\u6b64\u8bed\u97f3\uff08\u5176\u4ed6\u8bed\u8a00\uff09",
    "mode_gender": "\u540c\u6027\u522b\uff08\u6b64\u8bed\u97f3\u6216\u5176\u914d\u5bf9\uff09",
    "mode_any": "\u4efb\u610f\u6027\u522b",
    "balance_label": "\u6027\u522b\u5e73\u8861\uff08\u59cb\u7ec82\u4e2a\u7537\u58f02\u4e2a\u5973"
                     "\u58f0\uff09",
    "avoid_repeat_label": "\u4e0d\u5728\u5404\u4f4d\u7f6e\u4e4b\u95f4\u91cd\u590d\u8bed\u8a00",
    "fandub_title": "\u7c89\u4e1d\u914d\u97f3",
    "fandub_sub": "\u4ec5\u5f53\u4f60\u5728\u4e0a\u9762\u9009\u62e9\u4e86\u300cHelldivers "
                  "International - FANDUBS\u300d\u7248\u672c\u6587\u4ef6\u5939\u65f6\u624d\u751f"
                  "\u6548\uff08\u666e\u901aMOD\u65e0\u6548\uff09\u3002\u52fe\u9009\u60f3\u52a0\u5165"
                  "\u62bd\u53d6\u7684\u8bed\u8a00\uff1a",
    "btn_choose": "\u9009\u62e9...", "btn_randomize": "\u968f\u673a\u5206\u914d",
    "btn_randomizing": "\u6b63\u5728\u968f\u673a\u5206\u914d...", "btn_open_game": "\u6253\u5f00"
                       "\u6e38\u620f",
    "btn_close": "\u5173\u95ed",
    "err_missing_folder_title": "\u7f3a\u5c11\u6587\u4ef6\u5939",
    "err_mod_dir_missing": "\u8bf7\u5148\u9009\u62e9\u4e3bMOD\u6587\u4ef6\u5939\u3002",
    "err_game_dir_missing": "\u8bf7\u5148\u9009\u62e9\u6e38\u620f\u7684data/\u6587\u4ef6\u5939\u3002",
    "err_wrong_path_title": "\u8def\u5f84\u9519\u8bef",
    "err_mod_dir_wrong": "\u8be5\u6587\u4ef6\u5939\u6ca1\u6709manifest.json\u3002\u8bf7\u9009\u62e9"
                         "\u89e3\u538b\u300cHelldivers International\u300d\u7684\u6839\u6587\u4ef6"
                         "\u5939\uff08\u91cc\u9762\u6709manifest.json\u7684\u90a3\u4e2a\uff09\u3002",
    "err_game_dir_wrong": "\u8be5\u6587\u4ef6\u5939\u6ca1\u6709bundles.nxa\u3002\u8bf7\u9009\u62e9"
                          "Helldivers 2\u5b89\u88c5\u76ee\u5f55\u4e2d\u7684data/\u6587\u4ef6\u5939\u3002",
    "err_no_langs_title": "\u6ca1\u6709\u8bed\u8a00",
    "err_no_langs": "\u4e0d\u80fd\u6392\u9664\u6240\u6709\u8bed\u8a00\u3002",
    "err_failed_title": "\u968f\u673a\u5206\u914d\u5931\u8d25",
    "err_failed_body": "\u51fa\u4e86\u70b9\u95ee\u9898\uff1a\n\n{e}\n\n\u8bf7\u68c0\u67e5\u9009\u62e9"
                       "\u7684\u6587\u4ef6\u5939\u662f\u5426\u6b63\u786e\u3002",
    "err_open_game_title": "\u65e0\u6cd5\u6253\u5f00\u6e38\u620f",
    "err_open_game_body": "{e}\n\n\u8bf7\u5c1d\u8bd5\u4ece Steam \u624b\u52a8\u6253\u5f00\u3002",
    "result_window_title": "\u5df2\u5206\u914d\u8bed\u97f3", "result_header": "\u5df2\u5206\u914d"
                          "\u65b0\u8bed\u97f3",
    "result_sub": "\u8fdb\u5165\u6e38\u620f\u4f53\u9a8c\u5427\u3002",
},
"ru": {
    "subtitle": "\u0420\u0410\u041d\u0414\u041e\u041c\u0410\u0419\u0417\u0415\u0420",
    "ui_lang_label": "\u042f\u0437\u044b\u043a \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u0430",
    "mod_title": "\u041e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u043c\u043e\u0434",
    "mod_sub": "\u041f\u0430\u043f\u043a\u0430, \u043a\u0443\u0434\u0430 \u0432\u044b \u0440\u0430"
               "\u0441\u043f\u0430\u043a\u043e\u0432\u0430\u043b\u0438 \u043c\u043e\u0434 (zip "
               "\u0441 Nexus \u0438\u043b\u0438 \u043a\u0443\u0434\u0430 \u0435\u0433\u043e "
               "\u0440\u0430\u0441\u043f\u0430\u043a\u043e\u0432\u0430\u043b Arsenal): \u00ab"
               "Helldivers International\u00bb \u043b\u0438\u0431\u043e \u0432\u0430\u0440\u0438"
               "\u0430\u043d\u0442 \u00ab+ FANDUBS\u00bb, \u0435\u0441\u043b\u0438 \u0443 \u0432"
               "\u0430\u0441 \u0438\u043c\u0435\u043d\u043d\u043e \u043e\u043d -- \u0438\u0441"
               "\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u0442\u043e\u0442, \u0447"
               "\u0442\u043e \u0441\u043a\u0430\u0447\u0430\u043b\u0438, \u0432\u0442\u043e\u0440"
               "\u043e\u0439 \u043d\u0435 \u043d\u0443\u0436\u0435\u043d. \u0422\u0430\u043c \u0443"
               "\u0436\u0435 \u0435\u0441\u0442\u044c \u0430\u0443\u0434\u0438\u043e \u0434\u043b"
               "\u044f \u0432\u0441\u0435\u0445 9 \u044f\u0437\u044b\u043a\u043e\u0432, \u0441\u043a"
               "\u0430\u0447\u0438\u0432\u0430\u0442\u044c \u0438\u0445 \u0432 Steam \u043d\u0435"
               "\u043d\u0443\u0436\u043d\u043e.",
    "dir_title": "\u041f\u0430\u043f\u043a\u0430 \u0438\u0433\u0440\u044b",
    "dir_sub": "\u041f\u0430\u043f\u043a\u0430 data/ \u0432\u043d\u0443\u0442\u0440\u0438 \u0432"
               "\u0430\u0448\u0435\u0439 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 "
               "Helldivers 2, \u043a\u0443\u0434\u0430 \u0437\u0430\u043f\u0438\u0441\u044b\u0432"
               "\u0430\u0435\u0442\u0441\u044f \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442.",
    "langs_title": "\u0418\u0441\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0438\u0437 \u0436\u0435"
                   "\u0440\u0435\u0431\u044c\u0451\u0432\u043a\u0438",
    "langs_sub": "\u042d\u0442\u0438 \u044f\u0437\u044b\u043a\u0438 \u043d\u0438\u043a\u043e\u0433"
                 "\u0434\u0430 \u043d\u0435 \u0431\u0443\u0434\u0443\u0442 \u0432\u044b\u0431\u0440"
                 "\u0430\u043d\u044b.",
    "voices_title": "\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f \u0433\u043e"
                    "\u043b\u043e\u0441\u0430",
    "voices_sub": "\u041d\u0430\u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0433\u043e\u043b\u043e"
                  "\u0441 \u043a\u0430\u0436\u0434\u043e\u0433\u043e \u0441\u043b\u043e\u0442\u0430 "
                  "\u043c\u043e\u0436\u0435\u0442 \u043e\u0442\u043b\u0438\u0447\u0430\u0442\u044c"
                  "\u0441\u044f \u043e\u0442 \u043e\u0440\u0438\u0433\u0438\u043d\u0430\u043b\u0430.",
    "mode_own": "\u0422\u043e\u043b\u044c\u043a\u043e \u044d\u0442\u043e\u0442 \u0433\u043e\u043b\u043e"
               "\u0441 (\u0434\u0440\u0443\u0433\u0438\u0435 \u044f\u0437\u044b\u043a\u0438)",
    "mode_gender": "\u0422\u043e\u0442 \u0436\u0435 \u043f\u043e\u043b (\u044d\u0442\u043e\u0442 "
                   "\u0433\u043e\u043b\u043e\u0441 \u0438\u043b\u0438 \u0435\u0433\u043e \u043f\u0430"
                   "\u0440\u0430)",
    "mode_any": "\u041b\u044e\u0431\u043e\u0439 \u043f\u043e\u043b",
    "balance_label": "\u0411\u0430\u043b\u0430\u043d\u0441 \u043f\u043e\u043b\u043e\u0432 (\u0432"
                     "\u0441\u0435\u0433\u0434\u0430 2 \u043c\u0443\u0436\u0441\u043a\u0438\u0445 "
                     "\u0438 2 \u0436\u0435\u043d\u0441\u043a\u0438\u0445 \u0433\u043e\u043b\u043e"
                     "\u0441\u0430)",
    "avoid_repeat_label": "\u041d\u0435 \u043f\u043e\u0432\u0442\u043e\u0440\u044f\u0442\u044c "
                          "\u044f\u0437\u044b\u043a\u0438 \u043c\u0435\u0436\u0434\u0443 "
                          "\u0441\u043b\u043e\u0442\u0430\u043c\u0438",
    "fandub_title": "\u0424\u0430\u043d\u0434\u0430\u0431\u044b",
    "fandub_sub": "\u0414\u0435\u0439\u0441\u0442\u0432\u0443\u0435\u0442, \u0442\u043e\u043b\u044c"
                  "\u043a\u043e \u0435\u0441\u043b\u0438 \u0432\u044b\u0448\u0435 \u0432\u044b\u0431"
                  "\u0440\u0430\u043d\u0430 \u043f\u0430\u043f\u043a\u0430 \u0432\u0430\u0440\u0438"
                  "\u0430\u043d\u0442\u0430 \u00abHelldivers International - FANDUBS\u00bb (\u043d"
                  "\u0435 \u043e\u0431\u044b\u0447\u043d\u044b\u0439 \u043c\u043e\u0434). \u041e\u0442"
                  "\u043c\u0435\u0442\u044c\u0442\u0435 \u044f\u0437\u044b\u043a\u0438, \u043a\u043e"
                  "\u0442\u043e\u0440\u044b\u0435 \u0434\u043e\u043b\u0436\u043d\u044b \u0443\u0447"
                  "\u0430\u0441\u0442\u0432\u043e\u0432\u0430\u0442\u044c \u0432 \u0436\u0435\u0440"
                  "\u0435\u0431\u044c\u0451\u0432\u043a\u0435:",
    "btn_choose": "\u0412\u044b\u0431\u0440\u0430\u0442\u044c...",
    "btn_randomize": "\u0420\u0410\u041d\u0414\u041e\u041c\u0418\u0417\u0418\u0420\u041e\u0412\u0410"
                     "\u0422\u042c",
    "btn_randomizing": "\u0420\u0430\u043d\u0434\u043e\u043c\u0438\u0437\u0430\u0446\u0438\u044f...",
    "btn_open_game": "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0438\u0433\u0440\u0443",
    "btn_close": "\u0417\u0430\u043a\u0440\u044b\u0442\u044c",
    "err_missing_folder_title": "\u041d\u0435\u0442 \u043f\u0430\u043f\u043a\u0438",
    "err_mod_dir_missing": "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0432\u044b\u0431\u0435"
                           "\u0440\u0438\u0442\u0435 \u043f\u0430\u043f\u043a\u0443 \u043e\u0441"
                           "\u043d\u043e\u0432\u043d\u043e\u0433\u043e \u043c\u043e\u0434\u0430.",
    "err_game_dir_missing": "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0432\u044b\u0431\u0435"
                            "\u0440\u0438\u0442\u0435 \u043f\u0430\u043f\u043a\u0443 data/ \u0438"
                            "\u0433\u0440\u044b.",
    "err_wrong_path_title": "\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u043f\u0443\u0442\u044c",
    "err_mod_dir_wrong": "\u0412 \u044d\u0442\u043e\u0439 \u043f\u0430\u043f\u043a\u0435 \u043d\u0435"
                         "\u0442 manifest.json. \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 "
                         "\u043a\u043e\u0440\u043d\u0435\u0432\u0443\u044e \u043f\u0430\u043f\u043a"
                         "\u0443, \u043a\u0443\u0434\u0430 \u0432\u044b \u0440\u0430\u0441\u043f"
                         "\u0430\u043a\u043e\u0432\u0430\u043b\u0438 \u00abHelldivers Internatio"
                         "nal\u00bb (\u0442\u0443, \u0433\u0434\u0435 \u043b\u0435\u0436\u0438\u0442 "
                         "manifest.json).",
    "err_game_dir_wrong": "\u0412 \u044d\u0442\u043e\u0439 \u043f\u0430\u043f\u043a\u0435 \u043d\u0435"
                          "\u0442 bundles.nxa. \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 "
                          "\u043f\u0430\u043f\u043a\u0443 data/ \u0432\u043d\u0443\u0442\u0440\u0438 "
                          "\u0432\u0430\u0448\u0435\u0439 \u0443\u0441\u0442\u0430\u043d\u043e\u0432"
                          "\u043a\u0438 Helldivers 2.",
    "err_no_langs_title": "\u041d\u0435\u0442 \u044f\u0437\u044b\u043a\u043e\u0432",
    "err_no_langs": "\u041d\u0435\u043b\u044c\u0437\u044f \u0438\u0441\u043a\u043b\u044e\u0447\u0438"
                    "\u0442\u044c \u0432\u0441\u0435 \u044f\u0437\u044b\u043a\u0438.",
    "err_failed_title": "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0440\u0430\u043d"
                        "\u0434\u043e\u043c\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u0442\u044c",
    "err_failed_body": "\u0427\u0442\u043e-\u0442\u043e \u043f\u043e\u0448\u043b\u043e \u043d\u0435 "
                       "\u0442\u0430\u043a:\n\n{e}\n\n\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442"
                       "\u0435, \u0447\u0442\u043e \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b"
                       "\u0435 \u043f\u0430\u043f\u043a\u0438 \u0443\u043a\u0430\u0437\u0430\u043d\u044b"
                       " \u0432\u0435\u0440\u043d\u043e.",
    "err_open_game_title": "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442"
                           "\u043a\u0440\u044b\u0442\u044c \u0438\u0433\u0440\u0443",
    "err_open_game_body": "{e}\n\n\u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 "
                          "\u043e\u0442\u043a\u0440\u044b\u0442\u044c \u0432\u0440\u0443\u0447\u043d"
                          "\u0443\u044e \u0447\u0435\u0440\u0435\u0437 Steam.",
    "result_window_title": "\u0413\u043e\u043b\u043e\u0441\u0430 \u043d\u0430\u0437\u043d\u0430\u0447"
                           "\u0435\u043d\u044b",
    "result_header": "\u041d\u0410\u0417\u041d\u0410\u0427\u0415\u041d\u042b \u041d\u041e\u0412"
                     "\u042b\u0415 \u0413\u041e\u041b\u041e\u0421\u0410",
    "result_sub": "\u0417\u0430\u0439\u0434\u0438\u0442\u0435 \u0432 \u0438\u0433\u0440\u0443, "
                  "\u0447\u0442\u043e\u0431\u044b \u0438\u0445 \u0443\u0441\u043b\u044b\u0448\u0430"
                  "\u0442\u044c.",
},
"ko": {
    "subtitle": "\ub79c\ub364\ud654\uae30", "ui_lang_label": "\uc778\ud130\ud398\uc774\uc2a4 \uc5b8\uc5b4",
    "mod_title": "\uba54\uc778 \ubaa8\ub4dc",
    "mod_sub": "\ubaa8\ub4dc\ub97c \uc555\ucd95 \ud574\uc81c\ud55c \ud3f4\ub354(Nexus zip "
               "\ud30c\uc77c \ub610\ub294 Arsenal\uc774 \uc555\ucd95\uc744 \ud478\ub7fb \uc704"
               "\uce58): \"Helldivers International\" \ub610\ub294 \uac00\uc9c0\uace0 \uc788"
               "\ub2e4\uba74 \"+ FANDUBS\" \ubc84\uc804. \ub2e4\uc6b4\ub85c\ub4dc\ud55c \uac83"
               "\uc744 \uc0ac\uc6a9\ud558\uc138\uc694, \ub2e4\ub978 \ud558\ub098\ub294 \ud544"
               "\uc694 \uc5c6\uc2b5\ub2c8\ub2e4. 9\uac1c \uc5b8\uc5b4\uc758 \uc624\ub514\uc624"
               "\uac00 \uc774\ubbf8 \ub4e4\uc5b4\uc788\uc5b4 Steam\uc5d0\uc11c \ub530\ub85c "
               "\ubc1b\uc744 \ud544\uc694\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.",
    "dir_title": "\uac8c\uc784 \ud3f4\ub354",
    "dir_sub": "Helldivers 2 \uc124\uce58 \ud3f4\ub354 \uc548\uc758 data/ \ud3f4\ub354\ub85c, "
               "\uacb0\uacfc\uac00 \uc5ec\uae30\uc5d0 \uc800\uc7a5\ub429\ub2c8\ub2e4.",
    "langs_title": "\ucd94\ucca8\uc5d0\uc11c \uc81c\uc678",
    "langs_sub": "\uc774 \uc5b8\uc5b4\ub4e4\uc740 \uc808\ub300 \uc120\ud0dd\ub418\uc9c0 \uc54a"
                 "\uc2b5\ub2c8\ub2e4.",
    "voices_title": "\uc74c\uc131 \uc81c\ud55c",
    "voices_sub": "\uac01 \uc2ac\ub86f\uc758 \uc74c\uc131\uc774 \uc6d0\ubcf8\uc5d0\uc11c \uc5bc"
                  "\ub9c8\ub098 \ubc97\uc5b4\ub0a0 \uc218 \uc788\ub294\uc9c0.",
    "mode_own": "\uc774 \uc74c\uc131\ub9cc(\ub2e4\ub978 \uc5b8\uc5b4)",
    "mode_gender": "\uac19\uc740 \uc131\ubcc4(\uc774 \uc74c\uc131 \ub610\ub294 \uc9dd)",
    "mode_any": "\uc131\ubcc4 \ubb34\uad00",
    "balance_label": "\uc131\ubcc4 \uade0\ud615(\ud56d\uc0c1 \ub0a8\uc131 2, \uc5ec\uc131 2)",
    "avoid_repeat_label": "\uc2ac\ub86f \uac04 \uc5b8\uc5b4 \uc911\ubcf5 \uae08\uc9c0",
    "fandub_title": "\ud32c\ub354\ube59",
    "fandub_sub": "\uc704\uc5d0\uc11c \"Helldivers International - FANDUBS\" \ubc84\uc804 "
                  "\ud3f4\ub354\ub97c \uc120\ud0dd\ud55c \uacbd\uc6b0\uc5d0\ub9cc \uc801\uc6a9"
                  "\ub429\ub2c8\ub2e4(\uc77c\ubc18 \ubaa8\ub4dc\ub294 \ud574\ub2f9 \uc5c6\uc74c)."
                  " \ucd94\ucca8\uc5d0 \ud3ec\ud568\ud560 \uc5b8\uc5b4\ub97c \uc120\ud0dd\ud558"
                  "\uc138\uc694:",
    "btn_choose": "\uc120\ud0dd...", "btn_randomize": "\ub79c\ub364\ud654",
    "btn_randomizing": "\ub79c\ub364\ud654 \uc911...", "btn_open_game": "\uac8c\uc784 \uc5f4\uae30",
    "btn_close": "\ub2eb\uae30",
    "err_missing_folder_title": "\ud3f4\ub354 \uc5c6\uc74c",
    "err_mod_dir_missing": "\uba3c\uc800 \uba54\uc778 \ubaa8\ub4dc \ud3f4\ub354\ub97c \uc120\ud0dd"
                           "\ud558\uc138\uc694.",
    "err_game_dir_missing": "\uba3c\uc800 \uac8c\uc784\uc758 data/ \ud3f4\ub354\ub97c \uc120\ud0dd"
                            "\ud558\uc138\uc694.",
    "err_wrong_path_title": "\uc798\ubabb\ub41c \uacbd\ub85c",
    "err_mod_dir_wrong": "\uc774 \ud3f4\ub354\uc5d0 manifest.json\uc774 \uc5c6\uc2b5\ub2c8\ub2e4. "
                         "\"Helldivers International\"\uc758 \uc555\ucd95\uc744 \ud478\ub7fb "
                         "\ub8e8\ud2b8 \ud3f4\ub354(manifest.json\uc774 \uc788\ub294 \ud3f4\ub354)"
                         "\ub97c \uc120\ud0dd\ud558\uc138\uc694.",
    "err_game_dir_wrong": "\uc774 \ud3f4\ub354\uc5d0 bundles.nxa\uac00 \uc5c6\uc2b5\ub2c8\ub2e4. "
                          "Helldivers 2 \uc124\uce58 \ud3f4\ub354 \uc548\uc758 data/ \ud3f4\ub354"
                          "\ub97c \uc120\ud0dd\ud558\uc138\uc694.",
    "err_no_langs_title": "\uc5b8\uc5b4 \uc5c6\uc74c",
    "err_no_langs": "\ubaa8\ub4e0 \uc5b8\uc5b4\ub97c \uc81c\uc678\ud560 \uc218\ub294 \uc5c6\uc2b5"
                    "\ub2c8\ub2e4.",
    "err_failed_title": "\ub79c\ub364\ud654 \uc2e4\ud328",
    "err_failed_body": "\ubb38\uc81c\uac00 \ubc1c\uc0dd\ud588\uc2b5\ub2c8\ub2e4:\n\n{e}\n\n\uc120"
                       "\ud0dd\ud55c \ud3f4\ub354\uac00 \uc62c\ubc14\ub978\uc9c0 \ud655\uc778\ud558"
                       "\uc138\uc694.",
    "err_open_game_title": "\uac8c\uc784\uc744 \uc5f4 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4",
    "err_open_game_body": "{e}\n\nSteam\uc5d0\uc11c \uc9c1\uc811 \uc5f4\uc5b4\ubcf4\uc138\uc694.",
    "result_window_title": "\ud560\ub2f9\ub41c \uc74c\uc131", "result_header": "\uc0c8 \uc74c\uc131"
                          "\uc774 \ud560\ub2f9\ub418\uc5c8\uc2b5\ub2c8\ub2e4",
    "result_sub": "\uac8c\uc784\uc5d0 \ub4e4\uc5b4\uac00\uc11c \ub4e4\uc5b4\ubcf4\uc138\uc694.",
},
}
I18N["ms"] = I18N["es"]

VOICE_MODE_CODES = ["own", "gender", "any"]

# tema oscuro estilo Super Earth, con una franja de color distinta por card
BG = "#121214"
PANEL = "#1c1c1f"
FIELD = "#0c0c0e"
FG = "#eae7dd"
MUTED = "#8f8d85"
ACCENT = "#ffb000"       # amarillo Helldivers
BORDER = "#333338"
FONT_TITLE = ("Segoe UI", 17, "bold")
FONT_SUB = ("Segoe UI", 9)
FONT_HEAD = ("Segoe UI", 10, "bold")
FONT_BODY = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 11, "bold")


def voice_display(ui_lang, short):
    n = VOICE_ORDER.index(short) + 1
    word = DEFAULT_WORD.get(ui_lang, DEFAULT_WORD["us"])
    return f"{word}{n}" if ui_lang in DEFAULT_WORD_NO_SPACE else f"{word} {n}"


def config_path():
    # junto al exe (o al script en dev), portatil como el resto del mod.
    base = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False)
                                            else __file__))
    return os.path.join(base, "randomizer_config.json")


def load_config():
    try:
        return json.load(open(config_path(), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    try:
        json.dump(cfg, open(config_path(), "w", encoding="utf-8"), indent=2)
    except OSError:
        pass


class Card(tk.Frame):
    """Panel con franja de color y titulo, estilo ficha de mision -- no un
    LabelFrame generico. Cada card tiene su propio color de franja para que
    la ventana no sea un solo tono."""
    def __init__(self, master, title, accent, subtitle=None):
        super().__init__(master, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        strip = tk.Frame(self, bg=accent, width=4)
        strip.pack(side="left", fill="y")
        inner = tk.Frame(self, bg=PANEL)
        inner.pack(side="left", fill="both", expand=True)
        tk.Label(inner, text=title.upper(), bg=PANEL, fg=accent, font=FONT_HEAD,
                  anchor="w").pack(fill="x", padx=12, pady=(10, 0))
        if subtitle:
            tk.Label(inner, text=subtitle, bg=PANEL, fg=MUTED, font=("Segoe UI", 8),
                      anchor="w", justify="left", wraplength=430).pack(
                fill="x", padx=12, pady=(2, 0))
        self.body = tk.Frame(inner, bg=PANEL)
        self.body.pack(fill="both", expand=True, padx=12, pady=(8, 12))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.configure(bg=BG)
        self.geometry("660x680")
        self.minsize(520, 420)
        self.resizable(True, True)
        self.cfg = load_config()
        self._init_style()
        self._init_vars()

        # barra de idioma de interfaz: vive AFUERA del contenido reconstruible,
        # para no perderse a si misma cuando el resto se redibuja.
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=16, pady=(10, 0))
        self.ui_lang_label = tk.Label(bar, bg=BG, fg=MUTED, font=FONT_BODY, anchor="w")
        self.ui_lang_label.pack(side="left")
        self.ui_lang_combo = ttk.Combobox(
            bar, textvariable=self.ui_lang_display_var,
            values=[UI_LANG_ENDONYMS[c] for c in UI_LANG_ORDER],
            state="readonly", width=16, style="Dark.TCombobox")
        self.ui_lang_combo.pack(side="right")
        self.ui_lang_combo.bind("<<ComboboxSelected>>", self.on_ui_lang_change)

        # Las opciones ocupan una region desplazable; las acciones principales
        # quedan fijas abajo para que Randomize siempre este disponible.
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.content, bg=BG, highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(self.content, orient="vertical",
                                       command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.options_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.options_frame, anchor="nw")
        self.options_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_options_frame)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        self.footer = tk.Frame(self, bg=BG)
        self.footer.pack(fill="x", padx=16, pady=(4, 10))
        self._build_content()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def S(self, key):
        return I18N.get(self.ui_lang, I18N["us"]).get(key, I18N["us"][key])

    def _init_vars(self):
        self.ui_lang = self.cfg.get("ui_lang", DEFAULT_UI_LANG)
        if self.ui_lang not in I18N:
            self.ui_lang = DEFAULT_UI_LANG
        self.ui_lang_display_var = tk.StringVar(value=UI_LANG_ENDONYMS[self.ui_lang])

        self.mod_dir_var = tk.StringVar(value=self.cfg.get("mod_dir", ""))
        self.dir_var = tk.StringVar(value=self.cfg.get("game_dir", ""))

        excluded = set(self.cfg.get("excluded_langs", []))
        self.lang_vars = {code: tk.BooleanVar(value=code in excluded)
                           for code in LANG_NAMES["us"] if code != "ru" and code != "ko"}

        fandub_enabled = set(self.cfg.get("fandub_langs", []))
        self.fandub_vars = {code: tk.BooleanVar(value=code in fandub_enabled)
                             for code in FANDUB_LANGS}

        saved_modes = self.cfg.get("slot_modes", {})
        self.mode_vars = {short: tk.StringVar(value=saved_modes.get(short, "any"))
                           for short in VOICE_ORDER}  # guarda el CODIGO, no la etiqueta

        self.balance_var = tk.BooleanVar(value=self.cfg.get("balance_genders", False))
        self.avoid_repeat_var = tk.BooleanVar(value=self.cfg.get("avoid_repeat_langs", True))

    def on_ui_lang_change(self, event=None):
        label = self.ui_lang_display_var.get()
        code = next((c for c in UI_LANG_ORDER if UI_LANG_ENDONYMS[c] == label), DEFAULT_UI_LANG)
        self.ui_lang = code
        self.cfg["ui_lang"] = code
        save_config(self.cfg)
        for child in self.options_frame.winfo_children():
            child.destroy()
        for child in self.footer.winfo_children():
            child.destroy()
        self._build_content()
        self.canvas.yview_moveto(0)

    def _update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_options_frame(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Tk usa delta en Windows/macOS y botones 4/5 en Linux.
        if event.num == 4:
            step = -1
        elif event.num == 5:
            step = 1
        else:
            step = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(step * 3, "units")

    def _build_content(self):
        S = self.S
        self.title(f"Helldivers International - {S('subtitle')}")
        self.ui_lang_label.configure(text=S("ui_lang_label") + ":")

        outer = {"padx": 12, "pady": 6}
        c = self.options_frame

        header = tk.Frame(c, bg=BG)
        header.pack(fill="x")
        tk.Label(header, text="\u2604 HELLDIVERS INTERNATIONAL", bg=BG, fg=ACCENT,
                  font=FONT_TITLE).pack(pady=(8, 0))
        tk.Label(header, text=S("subtitle"), bg=BG, fg=MUTED, font=FONT_SUB).pack(pady=(0, 10))
        tk.Frame(c, bg=ACCENT, height=3).pack(fill="x", padx=16)

        # -- carpeta del mod principal --
        c0 = Card(c, S("mod_title"), CARD_ACCENTS["mod"], S("mod_sub"))
        c0.pack(fill="x", **outer)
        row0 = tk.Frame(c0.body, bg=PANEL)
        row0.pack(fill="x")
        tk.Entry(row0, textvariable=self.mod_dir_var, width=32, state="readonly",
                  bg=FIELD, fg=FG, readonlybackground=FIELD,
                  insertbackground=FG, relief="flat").pack(side="left", fill="x", expand=True,
                                                              ipady=3)
        self._button(row0, S("btn_choose"), self.choose_mod_dir, accent=CARD_ACCENTS["mod"]
                     ).pack(side="left", padx=(8, 0))

        # -- carpeta del juego --
        c1 = Card(c, S("dir_title"), CARD_ACCENTS["dir"], S("dir_sub"))
        c1.pack(fill="x", **outer)
        row = tk.Frame(c1.body, bg=PANEL)
        row.pack(fill="x")
        tk.Entry(row, textvariable=self.dir_var, width=32, state="readonly",
                  bg=FIELD, fg=FG, readonlybackground=FIELD,
                  insertbackground=FG, relief="flat").pack(side="left", fill="x", expand=True,
                                                             ipady=3)
        self._button(row, S("btn_choose"), self.choose_dir, accent=CARD_ACCENTS["dir"]
                     ).pack(side="left", padx=(8, 0))

        # -- idiomas a excluir --
        c2 = Card(c, S("langs_title"), CARD_ACCENTS["langs"], S("langs_sub"))
        c2.pack(fill="x", **outer)
        names = LANG_NAMES.get(self.ui_lang, LANG_NAMES["us"])
        items = sorted(self.lang_vars.items(), key=lambda kv: names.get(kv[0], kv[0]))
        for i, (code, var) in enumerate(items):
            self._check(c2.body, names.get(code, code), var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=(0, 16), pady=3)

        # -- restricciones de voz --
        c4 = Card(c, S("voices_title"), CARD_ACCENTS["voices"], S("voices_sub"))
        c4.pack(fill="x", **outer)
        mode_label_by_code = {"own": S("mode_own"), "gender": S("mode_gender"), "any": S("mode_any")}
        code_by_mode_label = {v: k for k, v in mode_label_by_code.items()}
        for short in VOICE_ORDER:
            row = tk.Frame(c4.body, bg=PANEL)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=voice_display(self.ui_lang, short), bg=PANEL, fg=FG,
                      font=FONT_BODY, width=16, anchor="w").pack(side="left")
            display_var = tk.StringVar(value=mode_label_by_code[self.mode_vars[short].get()])
            cb = ttk.Combobox(row, textvariable=display_var,
                                values=list(mode_label_by_code.values()),
                                state="readonly", width=20, style="Dark.TCombobox")
            cb.pack(side="left")

            def on_pick(e, short=short, display_var=display_var, code_map=code_by_mode_label):
                self.mode_vars[short].set(code_map[display_var.get()])
                self.save()
            cb.bind("<<ComboboxSelected>>", on_pick)
        tk.Frame(c4.body, bg=BORDER, height=1).pack(fill="x", pady=(8, 8))
        self._check(c4.body, S("balance_label"), self.balance_var).pack(anchor="w")
        self._check(c4.body, S("avoid_repeat_label"), self.avoid_repeat_var).pack(anchor="w")

        # -- fandubs --
        # Ojo: NO es una carpeta aparte. Solo tiene efecto si "Mod principal"
        # de arriba apunta a la variante +Fandubs (la gente baja UNA de las
        # dos, no las dos) -- esos idiomas viven en esa misma carpeta.
        c3 = Card(c, S("fandub_title"), CARD_ACCENTS["fandub"], S("fandub_sub"))
        c3.pack(fill="x", **outer)
        frow = tk.Frame(c3.body, bg=PANEL)
        frow.pack(fill="x")
        for code in FANDUB_LANGS:
            self._check(frow, names.get(code, code), self.fandub_vars[code]
                        ).pack(side="left", padx=(0, 16))

        # -- botones principales --
        f3 = tk.Frame(self.footer, bg=BG)
        f3.pack(fill="x", pady=(0, 6))
        self.randomize_btn = self._button(f3, f"\u2604  {S('btn_randomize')}",
                                            self.on_randomize, primary=True)
        self.randomize_btn.pack(side="left", fill="x", expand=True, ipady=4)
        if sys.platform == "win32":
            # en Linux "steam://run" no siempre tiene un handler registrado
            # (probado, no abre nada) -- mas simple sacar el boton ahi que
            # hacer deteccion de instalacion Steam para lanzar el exe a mano.
            self._button(f3, S("btn_open_game"), self.open_game, accent="#4da6ff"
                         ).pack(side="left", padx=(10, 0), ipady=4)

        # -- log --
        self.log_widget = scrolledtext.ScrolledText(
            self.footer, width=60, height=3, state="disabled", bg=FIELD, fg=MUTED,
            insertbackground=FG, relief="flat", font=("Consolas", 9),
            borderwidth=0, highlightbackground=BORDER, highlightthickness=1)
        self.log_widget.pack(fill="x")

    # -- estilo ttk (Combobox no se puede pintar con tk.Button directamente) --
    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TCombobox", fieldbackground=FIELD, background=PANEL,
                          foreground=FG, arrowcolor=ACCENT, bordercolor=BORDER,
                          lightcolor=FIELD, darkcolor=FIELD, padding=4)
        style.map("Dark.TCombobox",
                    fieldbackground=[("readonly", FIELD)],
                    foreground=[("readonly", FG)],
                    background=[("readonly", PANEL)])
        self.option_add("*TCombobox*Listbox.background", FIELD)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", "#161200")

    # -- widgets con el tema aplicado --
    def _button(self, master, text, command, primary=False, accent=ACCENT):
        if primary:
            bg, fg, hover = ACCENT, "#161200", "#ffc94d"
        else:
            bg, fg, hover = PANEL, accent, "#2a2a2e"
        btn = tk.Button(master, text=text, command=command, bg=bg, fg=fg,
                          activebackground=hover, activeforeground=fg,
                          font=FONT_BTN if primary else FONT_BODY, relief="flat",
                          bd=0, highlightbackground=accent, highlightthickness=1 if not primary
                          else 0, padx=14, pady=6, cursor="hand2")
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    def _check(self, master, text, var):
        return tk.Checkbutton(master, text=text, variable=var, command=self.save,
                                bg=PANEL, fg=FG, selectcolor=FIELD,
                                activebackground=PANEL, activeforeground=ACCENT,
                                font=FONT_BODY, highlightthickness=0)

    def log(self, msg):
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", str(msg) + "\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")
        self.update_idletasks()

    def save(self):
        self.cfg["ui_lang"] = self.ui_lang
        self.cfg["mod_dir"] = self.mod_dir_var.get()
        self.cfg["game_dir"] = self.dir_var.get()
        self.cfg["excluded_langs"] = [c for c, v in self.lang_vars.items() if v.get()]
        self.cfg["fandub_langs"] = [c for c, v in self.fandub_vars.items() if v.get()]
        self.cfg["slot_modes"] = {s: v.get() for s, v in self.mode_vars.items()}
        self.cfg["balance_genders"] = self.balance_var.get()
        self.cfg["avoid_repeat_langs"] = self.avoid_repeat_var.get()
        save_config(self.cfg)

    def choose_mod_dir(self):
        start = self.mod_dir_var.get() or None
        d = filedialog.askdirectory(title=self.S("mod_title"), initialdir=start)
        if not d:
            return
        if not os.path.isfile(os.path.join(d, "manifest.json")):
            messagebox.showerror(self.S("err_wrong_path_title"), self.S("err_mod_dir_wrong"))
            return
        self.mod_dir_var.set(d)
        self.save()

    def choose_dir(self):
        start = self.dir_var.get() or None
        d = filedialog.askdirectory(title=self.S("dir_title"), initialdir=start)
        if not d:
            return
        if not os.path.isfile(os.path.join(d, "bundles.nxa")):
            messagebox.showerror(self.S("err_wrong_path_title"), self.S("err_game_dir_wrong"))
            return
        self.dir_var.set(d)
        self.save()

    def open_game(self):
        try:
            os.startfile(f"steam://run/{STEAM_APPID}")
        except Exception as e:
            messagebox.showerror(self.S("err_open_game_title"),
                                  self.S("err_open_game_body").format(e=e))
            return
        self.save()
        self.destroy()

    def on_randomize(self):
        S = self.S
        mod_dir = self.mod_dir_var.get()
        if not mod_dir:
            messagebox.showerror(S("err_missing_folder_title"), S("err_mod_dir_missing"))
            return
        game_dir = self.dir_var.get()
        if not game_dir:
            messagebox.showerror(S("err_missing_folder_title"), S("err_game_dir_missing"))
            return
        excluded = [c for c, v in self.lang_vars.items() if v.get()]
        if len(excluded) == len(self.lang_vars):
            messagebox.showerror(S("err_no_langs_title"), S("err_no_langs"))
            return
        fandub_langs = [c for c, v in self.fandub_vars.items() if v.get()]
        slot_modes = {s: v.get() for s, v in self.mode_vars.items()}
        balance_genders = self.balance_var.get()
        avoid_repeat_langs = self.avoid_repeat_var.get()
        self.save()
        self.randomize_btn.configure(state="disabled", text=S("btn_randomizing"))
        threading.Thread(target=self._randomize_worker,
                          args=(mod_dir, game_dir, excluded, fandub_langs, slot_modes,
                                balance_genders, avoid_repeat_langs),
                          daemon=True).start()

    def _randomize_worker(self, mod_dir, game_dir, excluded, fandub_langs, slot_modes,
                           balance_genders, avoid_repeat_langs):
        try:
            import randomize_voices as rv  # pesado (numpy/lz4/core) -- diferido al primer uso
            picks = rv.run_randomize(mod_dir, game_dir, excluded_langs=excluded, log=self.log,
                                      fandub_langs=fandub_langs, slot_modes=slot_modes,
                                      balance_genders=balance_genders,
                                      avoid_repeat_langs=avoid_repeat_langs)
            self.after(0, self._on_randomize_done, picks)
        except Exception as e:
            self.log(f"ERROR: {e}")
            S = self.S
            self.after(0, lambda: messagebox.showerror(
                S("err_failed_title"), S("err_failed_body").format(e=e)))
            self.after(0, lambda: self.randomize_btn.configure(
                state="normal", text=S("btn_randomize")))

    def _on_randomize_done(self, picks):
        S = self.S
        self.randomize_btn.configure(state="normal",
                                       text=f"\u2604  {S('btn_randomize')}")
        slot_colors = {"female1": CARD_ACCENTS["dir"], "male1": CARD_ACCENTS["voices"],
                        "female2": CARD_ACCENTS["fandub"], "purist": CARD_ACCENTS["mod"]}
        names = LANG_NAMES.get(self.ui_lang, LANG_NAMES["us"])

        win = tk.Toplevel(self, bg=BG)
        win.title(S("result_window_title"))
        win.resizable(False, False)
        win.transient(self)

        tk.Label(win, text=f"\u2728 {S('result_header')}", bg=BG, fg=ACCENT,
                  font=("Segoe UI", 14, "bold")).pack(pady=(20, 2), padx=24)
        tk.Label(win, text=S("result_sub"), bg=BG, fg=MUTED, font=FONT_SUB).pack(pady=(0, 16))

        body = tk.Frame(win, bg=BG)
        body.pack(padx=24, fill="x")
        for t, s, lang in picks:
            color = slot_colors[t]
            row = tk.Frame(body, bg=PANEL, highlightbackground=color, highlightthickness=1)
            row.pack(fill="x", pady=5)
            inner = tk.Frame(row, bg=PANEL)
            inner.pack(fill="x", padx=14, pady=10)
            tk.Label(inner, text=voice_display(self.ui_lang, t), bg=PANEL, fg=color,
                      font=FONT_HEAD, width=15, anchor="w").pack(side="left")
            tk.Label(inner, text="\u2192", bg=PANEL, fg=MUTED,
                      font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 10))
            langname = names.get(lang, lang)
            tk.Label(inner, text=voice_display(self.ui_lang, s), bg=PANEL, fg=FG,
                      font=FONT_HEAD, anchor="w").pack(side="left")
            tk.Label(inner, text=f"  \u00b7  {langname}", bg=PANEL, fg=MUTED, font=FONT_BODY,
                      anchor="w").pack(side="left")

        self._button(win, S("btn_close"), win.destroy, primary=True).pack(
            pady=20, ipady=4, ipadx=10)
        win.grab_set()
        win.focus_set()

    def on_close(self):
        self.save()
        self.destroy()


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception:
        import traceback
        crash_log = os.path.join(os.path.dirname(config_path()), "randomizer_crash.log")
        with open(crash_log, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        raise
