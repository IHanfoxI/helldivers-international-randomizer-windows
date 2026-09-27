#!/usr/bin/env python3
"""
Ventana para randomize_voices.py: elegir las carpetas de los mods (principal,
Ship & Air, Mission; basta con una) y la del juego (se guardan), tildar que
idiomas sacar del sorteo, restringir por voz que genero puede tocarle a cada
slot Helldiver, sumar fandubs si el mod elegido los trae, randomizar todo o un
mod suelto, y abrir el juego. Toda la logica real vive en
randomize_voices.run_all; esto es solo la interfaz (CustomTkinter).

Interfaz localizada a 11 idiomas (los 9 del juego + ruso/coreano de
fandub), default ingles, se recuerda el ultimo elegido. Los nombres de
idioma de voz (LANG_NAMES) y de tipo de voz (VOICE_DISPLAY) tambien estan
en I18N por idioma de interfaz -- copiados de build_mod.STRINGS a mano en
vez de importar build_mod (import pesado: numpy/lz4/core, se difiere al
primer click de Randomizar para no romper el arranque de la ventana).
"""
import json, os, queue, sys, threading, tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

STEAM_APPID = "553850"  # Helldivers 2
DEFAULT_UI_LANG = "us"
VOICE_ORDER = ["male1", "purist", "female1", "female2"]  # hombre 1, 2, mujer 1, 2
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

# nombre de cada voz para el jugador: "Hombre 1", "Mujer 2"... en vez de
# "Predeterminada 1-4" (el nombre del juego), que no dice que cambio.
# female1/female2 = mujer 1/2, male1/purist = hombre 1/2.
VOICE_NUM = {"male1": ("m", 1), "purist": ("m", 2), "female1": ("f", 1), "female2": ("f", 2)}
VOICE_WORDS = {  # (hombre, mujer)
    "us": ("Man", "Woman"), "es": ("Hombre", "Mujer"), "jp": ("男性", "女性"),
    "de": ("Mann", "Frau"), "fr": ("Homme", "Femme"), "it": ("Uomo", "Donna"),
    "bp": ("Homem", "Mulher"), "cn": ("男声", "女声"),
    "ru": ("Мужчина", "Женщина"),
    "ko": ("남성", "여성"),
}
VOICE_WORDS["ms"] = VOICE_WORDS["es"]
VOICE_WORDS_NO_SPACE = {"jp", "cn"}  # sin espacio antes del numero

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

# -- cadenas para los mods NPC (Ship & Air, Mission) y los botones por mod.
# Van aparte y se mezclan en I18N para no reescribir los bloques de arriba. --
I18N_NPC = {
"us": {
    "log_working": 'Randomizing... this can take a minute.', "log_done": 'Done. Start the game to hear the new voices.',
    "ship_title": "Ship & Air Voices",
    "ship_sub": "Optional. Folder where you unzipped \"Helldivers International - ShipAir\". "
                "Each character (Eagle-1, Pelican-1, ship crew...) gets a random language.",
    "mission_title": "Mission Voices",
    "mission_sub": "Optional. Folder where you unzipped \"Helldivers International - Mission\". "
                   "SEAF troopers and civilians each get a random language.",
    "btn_randomize_all": "RANDOMIZE ALL", "only_label": "Only:", "btn_clear": "Clear",
    "err_no_mods": "Choose at least one mod folder (main, Ship & Air or Mission).",
    "err_kind_wrong": "That folder isn't the \"{name}\" mod. Choose the folder where you "
                      "unzipped it.",
},
"es": {
    "log_working": 'Randomizando... puede tardar un minuto.', "log_done": 'Listo. Entra al juego para escuchar las voces nuevas.',
    "ship_title": "Voces de Nave y Aire",
    "ship_sub": "Opcional. Carpeta donde descomprimiste \"Helldivers International - ShipAir\". "
                "Cada personaje (Águila-1, Pelícano-1, tripulación...) recibe un idioma al azar.",
    "mission_title": "Voces de Misión",
    "mission_sub": "Opcional. Carpeta donde descomprimiste \"Helldivers International - Mission\". "
                   "Los soldados SEAF y los civiles reciben cada uno un idioma al azar.",
    "btn_randomize_all": "RANDOMIZAR TODO", "only_label": "Solo:", "btn_clear": "Quitar",
    "err_no_mods": "Elige al menos una carpeta de mod (principal, Nave y Aire o Misión).",
    "err_kind_wrong": "Esa carpeta no es el mod \"{name}\". Elige la carpeta donde lo "
                      "descomprimiste.",
},
"jp": {
    "log_working": 'ランダマイズ中…1分ほどかかることがあります。', "log_done": '完了。ゲームを起動して新しい声を聴いてください。',
    "ship_title": "艦艇・航空ボイス",
    "ship_sub": "任意。「Helldivers International - ShipAir」を解凍したフォルダ。各キャラクター"
                "（イーグル1、ペリカン1、乗組員など）にランダムな言語が割り当てられます。",
    "mission_title": "ミッションボイス",
    "mission_sub": "任意。「Helldivers International - Mission」を解凍したフォルダ。SEAF兵と"
                   "民間人にそれぞれランダムな言語が割り当てられます。",
    "btn_randomize_all": "すべてランダマイズ", "only_label": "個別：", "btn_clear": "解除",
    "err_no_mods": "MODフォルダを少なくとも1つ選んでください（メイン、艦艇・航空、ミッション）。",
    "err_kind_wrong": "そのフォルダは「{name}」MODではありません。解凍したフォルダを選んでください。",
},
"de": {
    "log_working": 'Würfeln... das kann eine Minute dauern.', "log_done": 'Fertig. Starte das Spiel, um die neuen Stimmen zu hören.',
    "ship_title": "Schiffs- & Luftstimmen",
    "ship_sub": "Optional. Ordner, in den du \"Helldivers International - ShipAir\" entpackt "
                "hast. Jede Figur (Eagle-1, Pelican-1, Schiffscrew...) bekommt eine zufällige "
                "Sprache.",
    "mission_title": "Missionsstimmen",
    "mission_sub": "Optional. Ordner, in den du \"Helldivers International - Mission\" entpackt "
                   "hast. SEAF-Soldaten und Zivilisten bekommen je eine zufällige Sprache.",
    "btn_randomize_all": "ALLES WÜRFELN", "only_label": "Nur:", "btn_clear": "Entfernen",
    "err_no_mods": "Wähle mindestens einen Mod-Ordner (Haupt, Schiff & Luft oder Mission).",
    "err_kind_wrong": "Dieser Ordner ist nicht der Mod \"{name}\". Wähle den Ordner, in den du "
                      "ihn entpackt hast.",
},
"fr": {
    "log_working": 'Randomisation... cela peut prendre une minute.', "log_done": 'Terminé. Lance le jeu pour entendre les nouvelles voix.',
    "ship_title": "Voix Vaisseau & Aérien",
    "ship_sub": "Facultatif. Dossier où tu as décompressé « Helldivers International - "
                "ShipAir ». Chaque personnage (Eagle-1, Pelican-1, équipage...) reçoit une "
                "langue au hasard.",
    "mission_title": "Voix de mission",
    "mission_sub": "Facultatif. Dossier où tu as décompressé « Helldivers International - "
                   "Mission ». Les soldats SEAF et les civils reçoivent chacun une langue au "
                   "hasard.",
    "btn_randomize_all": "TOUT RANDOMISER", "only_label": "Seulement :", "btn_clear": "Retirer",
    "err_no_mods": "Choisis au moins un dossier de mod (principal, Vaisseau & Aérien ou Mission).",
    "err_kind_wrong": "Ce dossier n'est pas le mod « {name} ». Choisis le dossier où tu l'as "
                      "décompressé.",
},
"it": {
    "log_working": 'Randomizzazione... può richiedere un minuto.', "log_done": 'Fatto. Avvia il gioco per ascoltare le nuove voci.',
    "ship_title": "Voci Nave & Aria",
    "ship_sub": "Facoltativo. Cartella dove hai estratto \"Helldivers International - ShipAir\". "
                "Ogni personaggio (Eagle-1, Pelican-1, equipaggio...) riceve una lingua a caso.",
    "mission_title": "Voci di missione",
    "mission_sub": "Facoltativo. Cartella dove hai estratto \"Helldivers International - "
                   "Mission\". I soldati SEAF e i civili ricevono ciascuno una lingua a caso.",
    "btn_randomize_all": "RANDOMIZZA TUTTO", "only_label": "Solo:", "btn_clear": "Rimuovi",
    "err_no_mods": "Scegli almeno una cartella di mod (principale, Nave & Aria o Missione).",
    "err_kind_wrong": "Quella cartella non è la mod \"{name}\". Scegli la cartella dove l'hai "
                      "estratta.",
},
"bp": {
    "log_working": 'Randomizando... pode levar um minuto.', "log_done": 'Pronto. Entre no jogo para ouvir as novas vozes.',
    "ship_title": "Vozes da Nave e Aéreas",
    "ship_sub": "Opcional. Pasta onde você descompactou \"Helldivers International - ShipAir\". "
                "Cada personagem (Eagle-1, Pelican-1, tripulação...) recebe um idioma aleatório.",
    "mission_title": "Vozes de Missão",
    "mission_sub": "Opcional. Pasta onde você descompactou \"Helldivers International - "
                   "Mission\". Os soldados SEAF e os civis recebem cada um um idioma aleatório.",
    "btn_randomize_all": "RANDOMIZAR TUDO", "only_label": "Só:", "btn_clear": "Remover",
    "err_no_mods": "Escolha pelo menos uma pasta de mod (principal, Nave e Aéreas ou Missão).",
    "err_kind_wrong": "Essa pasta não é o mod \"{name}\". Escolha a pasta onde você o "
                      "descompactou.",
},
"cn": {
    "log_working": '正在随机分配……可能需要一分钟。', "log_done": '完成。启动游戏即可听到新语音。',
    "ship_title": "舰船与空中语音",
    "ship_sub": "可选。解压「Helldivers International - ShipAir」的文件夹。每个角色（鹰-1、"
                "鹈鹕-1、舰上人员等）会随机分配一种语言。",
    "mission_title": "任务语音",
    "mission_sub": "可选。解压「Helldivers International - Mission」的文件夹。SEAF士兵和平民"
                   "各自随机分配一种语言。",
    "btn_randomize_all": "全部随机分配", "only_label": "仅：", "btn_clear": "移除",
    "err_no_mods": "请至少选择一个MOD文件夹（主MOD、舰船与空中或任务）。",
    "err_kind_wrong": "该文件夹不是「{name}」MOD。请选择解压它的文件夹。",
},
"ru": {
    "log_working": 'Рандомизация... это может занять минуту.', "log_done": 'Готово. Запустите игру, чтобы услышать новые голоса.',
    "ship_title": "Голоса корабля и авиации",
    "ship_sub": "Необязательно. Папка, куда вы распаковали «Helldivers International - "
                "ShipAir». Каждый персонаж (Орёл-1, Пеликан-1, экипаж...) получает случайный "
                "язык.",
    "mission_title": "Голоса миссий",
    "mission_sub": "Необязательно. Папка, куда вы распаковали «Helldivers International - "
                   "Mission». Солдаты SEAF и гражданские получают каждый случайный язык.",
    "btn_randomize_all": "РАНДОМИЗИРОВАТЬ ВСЁ", "only_label": "Только:", "btn_clear": "Убрать",
    "err_no_mods": "Выберите хотя бы одну папку мода (основной, корабль и авиация или миссии).",
    "err_kind_wrong": "Эта папка — не мод «{name}». Выберите папку, куда вы его распаковали.",
},
"ko": {
    "log_working": '랜덤화 중... 1분 정도 걸릴 수 있습니다.', "log_done": '완료. 게임을 실행해 새 음성을 들어보세요.',
    "ship_title": "함선 및 항공 음성",
    "ship_sub": "선택 사항. \"Helldivers International - ShipAir\"의 압축을 푼 폴더. 각 캐릭터"
                "(이글-1, 펠리컨-1, 승무원 등)에 무작위 언어가 지정됩니다.",
    "mission_title": "임무 음성",
    "mission_sub": "선택 사항. \"Helldivers International - Mission\"의 압축을 푼 폴더. SEAF "
                   "병사와 민간인에게 각각 무작위 언어가 지정됩니다.",
    "btn_randomize_all": "모두 랜덤화", "only_label": "개별:", "btn_clear": "제거",
    "err_no_mods": "모드 폴더를 하나 이상 선택하세요(메인, 함선 및 항공, 임무).",
    "err_kind_wrong": "이 폴더는 \"{name}\" 모드가 아닙니다. 압축을 푼 폴더를 선택하세요.",
},
}
for _lang, _strings in I18N_NPC.items():
    I18N[_lang].update(_strings)  # "ms" es el mismo dict que "es"

# nombres de personaje NPC por idioma de interfaz (copiado de build_npc.MOD;
# ru/ko traducidos a mano)
NPC_NAMES = {
    "us": {"eagle": "Eagle-1", "pelican": "Pelican-1", "shipcomputer": "Ship computer",
           "control": "Mission Control", "democracy": "Democracy Officer",
           "shipmaster": "Ship Master", "engineer": "Engineer", "seaf": "SEAF troopers",
           "civilian": "Civilians"},
    "es": {"eagle": "Águila-1", "pelican": "Pelícano-1", "shipcomputer": "Computadora de la nave",
           "control": "Control de Misión", "democracy": "Oficial de Democracia",
           "shipmaster": "Capitana de la nave", "engineer": "Ingeniera",
           "seaf": "Soldados SEAF", "civilian": "Civiles"},
    "jp": {"eagle": "イーグル1", "pelican": "ペリカン1", "shipcomputer": "艦のコンピューター",
           "control": "ミッションコントロール", "democracy": "民主主義士官", "shipmaster": "艦長",
           "engineer": "エンジニア", "seaf": "SEAF兵", "civilian": "民間人"},
    "de": {"eagle": "Eagle-1", "pelican": "Pelican-1", "shipcomputer": "Schiffscomputer",
           "control": "Einsatzleitung", "democracy": "Demokratieoffizier",
           "shipmaster": "Schiffsmeisterin", "engineer": "Ingenieurin",
           "seaf": "SEAF-Soldaten", "civilian": "Zivilisten"},
    "fr": {"eagle": "Eagle-1", "pelican": "Pelican-1", "shipcomputer": "Ordinateur du vaisseau",
           "control": "Contrôle de mission", "democracy": "Officier de la Démocratie",
           "shipmaster": "Maîtresse du vaisseau", "engineer": "Ingénieure",
           "seaf": "Soldats SEAF", "civilian": "Civils"},
    "it": {"eagle": "Eagle-1", "pelican": "Pelican-1", "shipcomputer": "Computer della nave",
           "control": "Controllo missione", "democracy": "Ufficiale della Democrazia",
           "shipmaster": "Comandante della nave", "engineer": "Ingegnere",
           "seaf": "Soldati SEAF", "civilian": "Civili"},
    "bp": {"eagle": "Eagle-1", "pelican": "Pelican-1", "shipcomputer": "Computador da nave",
           "control": "Controle de Missão", "democracy": "Oficial da Democracia",
           "shipmaster": "Comandante da nave", "engineer": "Engenheira",
           "seaf": "Soldados SEAF", "civilian": "Civis"},
    "cn": {"eagle": "鹰-1", "pelican": "鹈鹕-1", "shipcomputer": "舰船电脑", "control": "任务控制",
           "democracy": "民主官", "shipmaster": "舰长", "engineer": "工程师",
           "seaf": "SEAF士兵", "civilian": "平民"},
    "ru": {"eagle": "Орёл-1", "pelican": "Пеликан-1", "shipcomputer": "Бортовой компьютер",
           "control": "Центр управления", "democracy": "Офицер демократии",
           "shipmaster": "Капитан корабля", "engineer": "Инженер",
           "seaf": "Солдаты SEAF", "civilian": "Гражданские"},
    "ko": {"eagle": "이글-1", "pelican": "펠리컨-1", "shipcomputer": "함선 컴퓨터",
           "control": "임무 통제", "democracy": "민주주의 장교", "shipmaster": "함장",
           "engineer": "엔지니어", "seaf": "SEAF 병사", "civilian": "민간인"},
}
NPC_NAMES["ms"] = NPC_NAMES["es"]

VOICE_MODE_CODES = ["own", "gender", "any"]

# tipos de mod: carpeta que lo delata, clave de config, titulo en I18N, color.
# = randomize_voices.KIND_MARKER, copiado: importarlo arrastra numpy/lz4/core.
KINDS = ["helldiver", "ship", "mission"]
KIND_MARKER = {"helldiver": "female1", "ship": "eagle", "mission": "seaf"}
KIND_CFG = {"helldiver": "mod_dir", "ship": "ship_dir", "mission": "mission_dir"}
KIND_TITLE = {"helldiver": "mod_title", "ship": "ship_title", "mission": "mission_title"}
KIND_SUB = {"helldiver": "mod_sub", "ship": "ship_sub", "mission": "mission_sub"}
KIND_SHORT = {"helldiver": "Helldivers", "ship": "Ship & Air", "mission": "Mission"}
KIND_ACCENT = {"helldiver": "#ff6b6b", "ship": "#4dd4ff", "mission": "#7ee081"}

# tema oscuro Super Earth: fondo azul-negro, paneles apenas mas claros con
# borde, amarillo Helldivers de acento y un color propio por seccion.
BG = "#0e1116"
PANEL = "#171b23"
PANEL_HI = "#212633"
FIELD = "#0a0c10"
FG = "#ecebe6"
MUTED = "#969aa5"
BORDER = "#2b303c"
ACCENT = "#ffc233"          # amarillo Helldivers
ACCENT_HOVER = "#ffd466"
ACCENT_TEXT = "#1b1500"
CARD_ACCENTS = {"dir": "#8fa3ff", "langs": ACCENT, "voices": "#5be7a9", "fandub": "#c77dff"}
MONO = "Consolas" if sys.platform == "win32" else "DejaVu Sans Mono"

FONTS = {}  # se llenan en App.__init__ (CTkFont necesita la ventana creada)


def voice_display(ui_lang, short):
    gender, n = VOICE_NUM[short]
    word = VOICE_WORDS.get(ui_lang, VOICE_WORDS["us"])[gender == "f"]
    return f"{word}{n}" if ui_lang in VOICE_WORDS_NO_SPACE else f"{word} {n}"


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


class Card(ctk.CTkFrame):
    """Panel redondeado con un punto de color y titulo, estilo ficha de
    mision. Cada card tiene su propio color para que la ventana no sea un
    solo tono."""
    def __init__(self, master, title, accent, subtitle=None):
        super().__init__(master, fg_color=PANEL, corner_radius=14, border_width=1,
                         border_color=BORDER)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 0))
        ctk.CTkFrame(head, fg_color=accent, width=10, height=10, corner_radius=5
                     ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(head, text=title.upper(), text_color=accent, font=FONTS["head"],
                     anchor="w").pack(side="left")
        if subtitle:
            ctk.CTkLabel(self, text=subtitle, text_color=MUTED, font=FONTS["small"],
                         anchor="w", justify="left", wraplength=560
                         ).pack(fill="x", padx=18, pady=(4, 0))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=18, pady=(10, 16))


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=BG)
        self.geometry("700x780")
        self.minsize(560, 480)
        FONTS.update(
            title=ctk.CTkFont(size=22, weight="bold"), sub=ctk.CTkFont(size=12),
            head=ctk.CTkFont(size=13, weight="bold"), body=ctk.CTkFont(size=13),
            small=ctk.CTkFont(size=12), btn=ctk.CTkFont(size=16, weight="bold"),
            btn_small=ctk.CTkFont(size=13, weight="bold"), mono=ctk.CTkFont(family=MONO, size=12))
        self.cfg = load_config()
        self._init_vars()
        self.busy = False

        # cabecera fija: titulo + selector de idioma de interfaz. Vive AFUERA
        # del contenido reconstruible, para no perderse a si misma cuando el
        # resto se redibuja al cambiar de idioma.
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=22, pady=(16, 6))
        titles = ctk.CTkFrame(bar, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(titles, text="☄ HELLDIVERS INTERNATIONAL", text_color=ACCENT,
                     font=FONTS["title"], anchor="w").pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(titles, text_color=MUTED, font=FONTS["sub"],
                                           anchor="w")
        self.subtitle_label.pack(anchor="w")
        self.ui_lang_menu = self._option_menu(
            bar, [UI_LANG_ENDONYMS[c] for c in UI_LANG_ORDER], self.ui_lang_display_var,
            self.on_ui_lang_change, width=170)
        self.ui_lang_menu.pack(side="right")
        self.ui_lang_label = ctk.CTkLabel(bar, text_color=MUTED, font=FONTS["small"])
        self.ui_lang_label.pack(side="right", padx=(0, 8))
        ctk.CTkFrame(self, fg_color=ACCENT, height=3, corner_radius=2).pack(fill="x", padx=22)

        # opciones en una region desplazable; las acciones quedan fijas abajo
        # para que Randomizar siempre este a mano.
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=PANEL_HI,
            scrollbar_button_hover_color=BORDER)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(8, 0))
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=22, pady=(8, 14))
        self._build_content()

        # el hilo del sorteo no toca tk: deja ("log"|"done"|"error", dato) aca
        # y _poll lo procesa desde el hilo principal. after() llamado desde
        # otro hilo no siempre llega (probado: la ventana quedaba "ocupada").
        self.events = queue.Queue()
        self._poll()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _poll(self):
        while True:
            try:
                kind, data = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self._append_log(data)
            elif kind == "done":
                self._on_randomize_done(data)
            else:
                self._append_log(f"\u26a0 {data}")
                messagebox.showerror(self.S("err_failed_title"),
                                     self.S("err_failed_body").format(e=data))
                self._end_busy()
        self.after(100, self._poll)

    def S(self, key):
        return I18N.get(self.ui_lang, I18N["us"]).get(key, I18N["us"][key])

    def _init_vars(self):
        self.ui_lang = self.cfg.get("ui_lang", DEFAULT_UI_LANG)
        if self.ui_lang not in I18N:
            self.ui_lang = DEFAULT_UI_LANG
        self.ui_lang_display_var = tk.StringVar(value=UI_LANG_ENDONYMS[self.ui_lang])

        self.dir_vars = {k: tk.StringVar(value=self.cfg.get(KIND_CFG[k], "")) for k in KINDS}
        self.game_dir_var = tk.StringVar(value=self.cfg.get("game_dir", ""))

        excluded = set(self.cfg.get("excluded_langs", []))
        self.lang_vars = {code: tk.BooleanVar(value=code in excluded)
                          for code in LANG_NAMES["us"] if code not in FANDUB_LANGS}

        fandub_enabled = set(self.cfg.get("fandub_langs", []))
        self.fandub_vars = {code: tk.BooleanVar(value=code in fandub_enabled)
                            for code in FANDUB_LANGS}

        saved_modes = self.cfg.get("slot_modes", {})
        self.mode_vars = {short: tk.StringVar(value=saved_modes.get(short, "any"))
                          for short in VOICE_ORDER}  # guarda el CODIGO, no la etiqueta

        self.balance_var = tk.BooleanVar(value=self.cfg.get("balance_genders", False))
        self.avoid_repeat_var = tk.BooleanVar(value=self.cfg.get("avoid_repeat_langs", True))

    def on_ui_lang_change(self, label):
        self.ui_lang = next((c for c in UI_LANG_ORDER if UI_LANG_ENDONYMS[c] == label),
                            DEFAULT_UI_LANG)
        self.save()
        for frame in (self.scroll, self.footer):
            for child in frame.winfo_children():
                child.destroy()
        self._build_content()
        self.scroll._parent_canvas.yview_moveto(0)

    def _build_content(self):
        S = self.S
        self.title(f"Helldivers International - {S('subtitle')}")
        self.subtitle_label.configure(text=S("subtitle"))
        self.ui_lang_label.configure(text=S("ui_lang_label"))
        outer = {"fill": "x", "padx": 12, "pady": 7}
        c = self.scroll

        # -- carpetas de los tres mods (basta con una) y del juego --
        for kind in KINDS:
            card = Card(c, S(KIND_TITLE[kind]), KIND_ACCENT[kind], S(KIND_SUB[kind]))
            card.pack(**outer)
            self._folder_row(card.body, self.dir_vars[kind], KIND_ACCENT[kind],
                             lambda k=kind: self.choose_mod_dir(k),
                             lambda k=kind: self.clear_mod_dir(k))
        card = Card(c, S("dir_title"), CARD_ACCENTS["dir"], S("dir_sub"))
        card.pack(**outer)
        self._folder_row(card.body, self.game_dir_var, CARD_ACCENTS["dir"], self.choose_dir)

        # -- idiomas a excluir (valen para los tres mods) --
        card = Card(c, S("langs_title"), CARD_ACCENTS["langs"], S("langs_sub"))
        card.pack(**outer)
        names = LANG_NAMES.get(self.ui_lang, LANG_NAMES["us"])
        items = sorted(self.lang_vars.items(), key=lambda kv: names.get(kv[0], kv[0]))
        for i, (code, var) in enumerate(items):
            self._check(card.body, names.get(code, code), var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=(0, 18), pady=5)

        # -- restricciones de voz (solo mod Helldiver) --
        card = Card(c, S("voices_title"), CARD_ACCENTS["voices"], S("voices_sub"))
        card.pack(**outer)
        label_by_code = {"own": S("mode_own"), "gender": S("mode_gender"), "any": S("mode_any")}
        code_by_label = {v: k for k, v in label_by_code.items()}
        for short in VOICE_ORDER:
            row = ctk.CTkFrame(card.body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=voice_display(self.ui_lang, short), text_color=FG,
                         font=FONTS["body"], width=150, anchor="w").pack(side="left")
            display_var = tk.StringVar(value=label_by_code[self.mode_vars[short].get()])

            def on_pick(label, short=short):
                self.mode_vars[short].set(code_by_label[label])
                self.save()
            self._option_menu(row, list(label_by_code.values()), display_var, on_pick,
                              width=300).pack(side="left")
        ctk.CTkFrame(card.body, fg_color=BORDER, height=1).pack(fill="x", pady=(10, 8))
        self._switch(card.body, S("balance_label"), self.balance_var).pack(anchor="w", pady=3)
        self._switch(card.body, S("avoid_repeat_label"), self.avoid_repeat_var
                     ).pack(anchor="w", pady=3)

        # -- fandubs --
        # Ojo: NO es una carpeta aparte. Solo tiene efecto si "Mod principal"
        # de arriba apunta a la variante +Fandubs (la gente baja UNA de las
        # dos, no las dos) -- esos idiomas viven en esa misma carpeta.
        card = Card(c, S("fandub_title"), CARD_ACCENTS["fandub"], S("fandub_sub"))
        card.pack(**outer)
        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="x")
        for code in FANDUB_LANGS:
            self._switch(row, names.get(code, code), self.fandub_vars[code]
                         ).pack(side="left", padx=(0, 24))

        # -- acciones --
        self.all_btn = ctk.CTkButton(
            self.footer, text=f"☄  {S('btn_randomize_all')}", command=self.on_randomize,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=ACCENT_TEXT,
            text_color_disabled="#5c4a14", font=FONTS["btn"], height=48, corner_radius=12)
        self.all_btn.pack(fill="x")
        row = ctk.CTkFrame(self.footer, fg_color="transparent")
        row.pack(fill="x", pady=(10, 8))
        ctk.CTkLabel(row, text=S("only_label"), text_color=MUTED, font=FONTS["small"]
                     ).pack(side="left", padx=(2, 10))
        self.kind_btns = {}
        for kind in KINDS:
            b = self._outline_button(row, KIND_SHORT[kind], KIND_ACCENT[kind],
                                     lambda k=kind: self.on_randomize(k))
            b.pack(side="left", padx=(0, 8))
            self.kind_btns[kind] = b
        if sys.platform == "win32":
            # en Linux "steam://run" no siempre tiene un handler registrado
            # (probado, no abre nada) -- mas simple sacar el boton ahi que
            # hacer deteccion de instalacion Steam para lanzar el exe a mano.
            self._outline_button(row, S("btn_open_game"), CARD_ACCENTS["dir"],
                                 self.open_game).pack(side="right")

        self.log_widget = ctk.CTkTextbox(
            self.footer, height=72, fg_color=FIELD, text_color=MUTED, font=FONTS["mono"],
            corner_radius=10, border_width=1, border_color=BORDER, state="disabled")
        self.log_widget.pack(fill="x")
        self._refresh_buttons()

    # -- widgets con el tema aplicado --
    def _outline_button(self, master, text, accent, command, **kw):
        return ctk.CTkButton(master, text=text, command=command, fg_color=PANEL_HI,
                             hover_color=BORDER, text_color=accent, border_color=accent,
                             border_width=1, text_color_disabled="#555a66",
                             font=FONTS["btn_small"], height=34, corner_radius=10, **kw)

    def _folder_row(self, master, var, accent, choose, clear=None):
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, textvariable=var, fg_color=FIELD, text_color=FG, font=FONTS["small"],
                     corner_radius=8, anchor="w", height=34).pack(
            side="left", fill="x", expand=True)
        self._outline_button(row, self.S("btn_choose"), accent, choose, width=100
                             ).pack(side="left", padx=(8, 0))
        if clear:
            self._outline_button(row, "✕", MUTED, clear, width=34
                                 ).pack(side="left", padx=(6, 0))

    def _option_menu(self, master, values, var, command, width):
        return ctk.CTkOptionMenu(
            master, values=values, variable=var, command=command, width=width, height=32,
            fg_color=FIELD, button_color=PANEL_HI, button_hover_color=BORDER, text_color=FG,
            dropdown_fg_color=PANEL, dropdown_hover_color=PANEL_HI, dropdown_text_color=FG,
            font=FONTS["body"], dropdown_font=FONTS["body"], corner_radius=8,
            dynamic_resizing=False)

    def _check(self, master, text, var):
        return ctk.CTkCheckBox(master, text=text, variable=var, command=self.save,
                               fg_color=ACCENT, hover_color=ACCENT_HOVER, border_color=BORDER,
                               checkmark_color=ACCENT_TEXT, text_color=FG, font=FONTS["body"],
                               corner_radius=6, checkbox_width=20, checkbox_height=20)

    def _switch(self, master, text, var):
        return ctk.CTkSwitch(master, text=text, variable=var, command=self.save,
                             progress_color=ACCENT, fg_color=BORDER, button_color=FG,
                             button_hover_color="#ffffff", text_color=FG, font=FONTS["body"])

    def _refresh_buttons(self):
        """Randomizar todo pide al menos un mod; cada boton suelto, el suyo."""
        have = {k: bool(self.dir_vars[k].get()) for k in KINDS}
        idle = "disabled" if self.busy else "normal"
        self.all_btn.configure(state=idle if any(have.values()) else "disabled")
        for kind, b in self.kind_btns.items():
            b.configure(state=idle if have[kind] else "disabled")

    def log(self, msg):
        self.events.put(("log", str(msg)))

    def _append_log(self, msg):
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", msg + "\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def save(self):
        self.cfg["ui_lang"] = self.ui_lang
        for kind in KINDS:
            self.cfg[KIND_CFG[kind]] = self.dir_vars[kind].get()
        self.cfg["game_dir"] = self.game_dir_var.get()
        self.cfg["excluded_langs"] = [c for c, v in self.lang_vars.items() if v.get()]
        self.cfg["fandub_langs"] = [c for c, v in self.fandub_vars.items() if v.get()]
        self.cfg["slot_modes"] = {s: v.get() for s, v in self.mode_vars.items()}
        self.cfg["balance_genders"] = self.balance_var.get()
        self.cfg["avoid_repeat_langs"] = self.avoid_repeat_var.get()
        save_config(self.cfg)

    def choose_mod_dir(self, kind):
        start = self.dir_vars[kind].get() or None
        d = filedialog.askdirectory(title=self.S(KIND_TITLE[kind]), initialdir=start)
        if not d:
            return
        if not os.path.isdir(os.path.join(d, KIND_MARKER[kind])):
            messagebox.showerror(self.S("err_wrong_path_title"), self.S("err_kind_wrong").format(
                name=self.S(KIND_TITLE[kind])))
            return
        self.dir_vars[kind].set(d)
        self.save()
        self._refresh_buttons()

    def clear_mod_dir(self, kind):
        self.dir_vars[kind].set("")
        self.save()
        self._refresh_buttons()

    def choose_dir(self):
        start = self.game_dir_var.get() or None
        d = filedialog.askdirectory(title=self.S("dir_title"), initialdir=start)
        if not d:
            return
        if not os.path.isfile(os.path.join(d, "bundles.nxa")):
            messagebox.showerror(self.S("err_wrong_path_title"), self.S("err_game_dir_wrong"))
            return
        self.game_dir_var.set(d)
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

    def on_randomize(self, only=None):
        """only=None randomiza todos los mods con carpeta; si no, solo ese.
        Los demas conservan lo que salio la vez anterior (write_patch)."""
        S = self.S
        mod_dirs = {k: self.dir_vars[k].get() for k in ([only] if only else KINDS)
                    if self.dir_vars[k].get()}
        if not mod_dirs:
            messagebox.showerror(S("err_missing_folder_title"), S("err_no_mods"))
            return
        game_dir = self.game_dir_var.get()
        if not game_dir:
            messagebox.showerror(S("err_missing_folder_title"), S("err_game_dir_missing"))
            return
        excluded = [c for c, v in self.lang_vars.items() if v.get()]
        if len(excluded) == len(self.lang_vars):
            messagebox.showerror(S("err_no_langs_title"), S("err_no_langs"))
            return
        kw = dict(excluded_langs=excluded, log=lambda msg: None,  # jerga interna, no al jugador
                  fandub_langs=[c for c, v in self.fandub_vars.items() if v.get()],
                  slot_modes={s: v.get() for s, v in self.mode_vars.items()},
                  balance_genders=self.balance_var.get(),
                  avoid_repeat_langs=self.avoid_repeat_var.get())
        self.save()
        self.busy = True
        self._refresh_buttons()
        self.all_btn.configure(text=S("btn_randomizing"))
        self.log(S("log_working"))
        threading.Thread(target=self._randomize_worker, args=(game_dir, mod_dirs, kw),
                         daemon=True).start()

    def _randomize_worker(self, game_dir, mod_dirs, kw):
        try:
            import randomize_voices as rv  # pesado (numpy/lz4/core) -- diferido al primer uso
            self.events.put(("done", rv.run_all(game_dir, mod_dirs, **kw)))
        except Exception as e:
            self.events.put(("error", e))

    def _end_busy(self):
        self.busy = False
        self.all_btn.configure(text=f"☄  {self.S('btn_randomize_all')}")
        self._refresh_buttons()

    def _on_randomize_done(self, results):
        S = self.S
        self._end_busy()
        names = LANG_NAMES.get(self.ui_lang, LANG_NAMES["us"])
        npc_names = NPC_NAMES.get(self.ui_lang, NPC_NAMES["us"])
        for kind in KINDS:
            for pick in results.get(kind, []):
                if kind == "helldiver":
                    t, s, lang = pick
                    self.log(f"{voice_display(self.ui_lang, t)} \u2192 "
                             f"{voice_display(self.ui_lang, s)} \u00b7 {names.get(lang, lang)}")
                else:
                    self.log(f"{npc_names.get(pick[0], pick[0])} \u2192 "
                             f"{names.get(pick[1], pick[1])}")
        self.log(S("log_done"))

        win = ctk.CTkToplevel(self, fg_color=BG)
        win.title(S("result_window_title"))
        win.transient(self)
        ctk.CTkLabel(win, text=f"✨ {S('result_header')}", text_color=ACCENT,
                     font=FONTS["title"]).pack(pady=(22, 2), padx=28)
        ctk.CTkLabel(win, text=S("result_sub"), text_color=MUTED, font=FONTS["sub"]
                     ).pack(pady=(0, 10))

        body = ctk.CTkScrollableFrame(win, fg_color="transparent", width=460,
                                      height=min(520, 120 + 52 * sum(map(len, results.values()))))
        body.pack(padx=18, fill="both", expand=True)
        for kind in KINDS:
            if kind not in results:
                continue
            color = KIND_ACCENT[kind]
            ctk.CTkLabel(body, text=S(KIND_TITLE[kind]).upper(), text_color=color,
                         font=FONTS["head"], anchor="w").pack(fill="x", padx=6, pady=(10, 4))
            for pick in results[kind]:
                if kind == "helldiver":
                    t, s, lang = pick
                    who, voice = voice_display(self.ui_lang, t), voice_display(self.ui_lang, s)
                else:
                    slot, lang = pick
                    who, voice = npc_names.get(slot, slot), None
                row = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=10, border_width=1,
                                   border_color=BORDER)
                row.pack(fill="x", pady=3, padx=4)
                ctk.CTkLabel(row, text=who, text_color=color, font=FONTS["head"], width=170,
                             anchor="w").pack(side="left", padx=(14, 0), pady=8)
                ctk.CTkLabel(row, text="→", text_color=MUTED, font=FONTS["head"]
                             ).pack(side="left", padx=(0, 10))
                if voice:
                    ctk.CTkLabel(row, text=voice, text_color=FG, font=FONTS["head"]
                                 ).pack(side="left")
                    ctk.CTkLabel(row, text="  ·  ", text_color=MUTED, font=FONTS["body"]
                                 ).pack(side="left")
                ctk.CTkLabel(row, text=names.get(lang, lang), text_color=FG if not voice
                             else MUTED, font=FONTS["body"]).pack(side="left")

        ctk.CTkButton(win, text=S("btn_close"), command=win.destroy, fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, text_color=ACCENT_TEXT, font=FONTS["btn_small"],
                      height=38, corner_radius=10).pack(pady=18)
        # CTkToplevel en Windows a veces aparece detras, y en Linux grab_set
        # falla si la ventana todavia no es visible: los dos, un poco despues.
        win.after(150, lambda: (win.lift(), win.focus_force(), win.grab_set()))

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
