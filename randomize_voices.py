#!/usr/bin/env python3
"""
Randomiza los 4 slots de voz Helldiver (tipo + idioma) sin pasar por Arsenal.

La fuente de audio es el mod PRINCIPAL ya descomprimido (el mismo zip de
Nexus, o la carpeta donde Arsenal lo extrajo), no los paquetes crudos del
juego: ese mod ya trae, para cada combinacion (tipo de voz destino, tipo de
voz fuente, idioma), un patch prearmado con las 9 combinaciones de idioma
embebidas (`build_combo_patch` + `--universal` en build_mod.py). Leer de ahi
evita depender de que idiomas bajo el jugador en Steam -- la mayoria solo
tiene el suyo, no los 9, y el mod universal ya resolvio eso una vez para
todos. Los fandubs (ru/ko) funcionan igual: si mod_dir es la variante
+Fandubs, esos idiomas ya estan ahi mismo, no hace falta otra carpeta.

Uso:
    python randomize_voices.py --mod-dir RUTA [--game-dir RUTA] [--seed N]

--mod-dir es la carpeta del mod principal descomprimido (tiene manifest.json
y las subcarpetas female1/, male1/, etc.). --game-dir es la carpeta data/ del
juego, solo como destino de escritura -- sin --game-dir prueba rutas comunes
de Steam y si no encuentra, pregunta. Escribe <hash>.patch_<N>(+.stream) ahi,
eligiendo N mas alto que cualquier patch_N ya presente (para no pisar lo que
puso Arsenal). Correr de nuevo para una mezcla distinta. Si Arsenal reinstala
o actualiza el mod principal, vuelve a correr esto despues (pisa lo nuestro).
"""
import argparse, glob, os, random, re, sys, types

# frozen (PyInstaller): data files ship next to the exe in _MEIPASS instead of
# alongside this .py source.
HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.modules.setdefault("pyaudio", types.ModuleType("pyaudio"))
sys.path.insert(0, os.path.join(HERE, "tools", "hd2-audio-modder"))
import build_mod as bm  # reusa VOICE_SHORT, VOICES, PATCH_UNK4, load(),
                         # write_stream_patch(), core

PATCH_STEM = "9ba626afa44a3aa3"
FANDUB_LANGS = {"ru", "ko"}

# restricciones de voz por slot, todas en nombre corto (female1/female2/
# male1/purist). "purist" es la 4ta, masculina -- el pedido original la
# llama "male2" pero el nombre interno sigue siendo purist en todo el resto
# del repo, no vale la pena renombrar solo por esto.
GENDER = {"female1": "f", "female2": "f", "male1": "m", "purist": "m"}
GENDER_PAIR = {"female1": "female2", "female2": "female1",
               "male1": "purist", "purist": "male1"}
VOICE_MODES = ("own", "gender", "any")  # solo esta voz / mismo genero / cualquiera


def candidates_short(target_short, mode):
    if mode == "own":
        return [target_short]
    if mode == "gender":
        return [target_short, GENDER_PAIR[target_short]]
    return list(GENDER)  # "any": las 4


# ponytail: lista fija de rutas comunes, no lee steamapps libraryfolders.vdf.
# Si no calza, se le pide al usuario que la pegue a mano (input()).
COMMON_GAME_DIRS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Helldivers 2\data",
    r"C:\Steam\steamapps\common\Helldivers 2\data",
    r"D:\SteamLibrary\steamapps\common\Helldivers 2\data",
    r"D:\Steam\steamapps\common\Helldivers 2\data",
    r"E:\SteamLibrary\steamapps\common\Helldivers 2\data",
    os.path.expanduser("~/.local/share/Steam/steamapps/common/Helldivers 2/data"),
    os.path.expanduser("~/.steam/steam/steamapps/common/Helldivers 2/data"),
    os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam"
                        "/steamapps/common/Helldivers 2/data"),
]


def find_game_dir():
    for p in COMMON_GAME_DIRS:
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, "bundles.nxa")):
            return p
    print("No encontre Helldivers 2 en las rutas usuales.")
    p = input("Pega la ruta a la carpeta data/ del juego: ").strip('" ')
    if not os.path.isfile(os.path.join(p, "bundles.nxa")):
        raise SystemExit(f"no hay bundles.nxa en {p}, ruta incorrecta")
    return p


def next_patch_num(game_dir):
    nums = [int(m.group(1)) for f in glob.glob(os.path.join(game_dir, f"{PATCH_STEM}.patch_*"))
            if (m := re.fullmatch(rf"{PATCH_STEM}\.patch_(\d+)", os.path.basename(f)))]
    return max(nums, default=-1) + 1


def combo_patch_path(mod_dir, target_voice, src_voice, lang):
    """Ruta al patch prearmado para (target, src_voice, lang) dentro de un
    mod ya descomprimido -- mismo layout para el mod principal y el
    +Fandubs (`<target>/<src_voice>/<lang>/<hash>.patch_0`, ver
    build_mod.gen_patches)."""
    return os.path.join(mod_dir, bm.VOICE_SHORT[target_voice],
                         bm.VOICE_SHORT[src_voice], lang, f"{PATCH_STEM}.patch_0")


def combo_langs(mod_dir, target_voice, src_voice):
    """Idiomas con patch prearmado para este combo, segun lo que el mod
    trae en disco -- no depende de que idiomas bajo el jugador en Steam."""
    base = os.path.join(mod_dir, bm.VOICE_SHORT[target_voice], bm.VOICE_SHORT[src_voice])
    if not os.path.isdir(base):
        return []
    return sorted(d for d in os.listdir(base)
                  if os.path.isfile(os.path.join(base, d, f"{PATCH_STEM}.patch_0")))


def combo_archive(mod_dir, target_voice, src_voice, lang):
    path = combo_patch_path(mod_dir, target_voice, src_voice, lang)
    return bm.load(path) if os.path.isfile(path) else None


def pick_src_voices(rng, slot_modes, balance_genders):
    """{target_short: src_voice_short} para los 4 slots, respetando el modo
    de cada slot (own/gender/any) y, si se pide, forzando 2 fuentes de voz
    masculina y 2 femeninas en total. "own" y "gender" nunca desbalancean
    (la fuente siempre queda del mismo genero que el slot); solo "any" puede,
    asi que el rechazo-y-reintento converge rapido incluso pidiendo balance
    con los 4 slots en "any" (~37% de chance por intento)."""
    targets = list(GENDER)  # female1, female2, male1, purist
    for _ in range(2000):
        picks = {t: rng.choice(candidates_short(t, slot_modes.get(t, "any")))
                 for t in targets}
        if not balance_genders or sum(GENDER[v] == "m" for v in picks.values()) == 2:
            return picks
    raise ValueError("no se pudo balancear 2 y 2 con esas restricciones de voz")


def lang_pool(mod_dir, target_voice, src_voice, excluded_langs=(), fandub_langs=()):
    """Idiomas disponibles para ese (target, src_voice), leyendo lo que el
    mod ya trae en disco. ru/ko solo entran si el jugador los tildo Y su
    mod_dir es la variante +Fandubs (si no, combo_langs directamente no
    los va a encontrar ahi)."""
    present = combo_langs(mod_dir, target_voice, src_voice)
    return [l for l in present if l not in excluded_langs
            and (l not in FANDUB_LANGS or l in fandub_langs)]


def pick_langs(lang_pools, rng, avoid_repeat=True):
    """{target_short: lang} sorteando un idioma por slot de su propio pool.
    Si avoid_repeat, intenta que los 4 salgan distintos (rechazo-y-reintento,
    como pick_src_voices); devuelve None si no lo logra en 2000 intentos
    (algun pool tiene muy pocas opciones, o hay menos de 4 idiomas en total
    entre todos los pools). Un pool vacio siempre devuelve None para ese
    slot sin intentar nada -- el caller decide que hacer (ver run_randomize)."""
    targets = list(lang_pools)
    if any(not p for p in lang_pools.values()):
        avoid_repeat = False  # no hay forma de evitar nada si a alguien no le queda opcion
    if not avoid_repeat:
        return {t: (rng.choice(p) if p else None) for t, p in lang_pools.items()}
    for _ in range(2000):
        picks = {t: rng.choice(p) for t, p in lang_pools.items()}
        if len(set(picks.values())) == len(targets):
            return picks
    return None


def run_randomize(mod_dir, game_dir, out_dir=None, excluded_langs=(), seed=None, log=print,
                   fandub_langs=(), slot_modes=None, balance_genders=False,
                   avoid_repeat_langs=True):
    """Sortea los 4 slots (excluyendo excluded_langs; ru/ko solo entran si
    estan en fandub_langs Y mod_dir es la variante +Fandubs) leyendo los
    patches prearmados de mod_dir, y escribe UN patch combinado en out_dir
    (o game_dir). slot_modes: {target_short: "own"/"gender"/"any"}.
    avoid_repeat_langs evita que dos slots salgan con el mismo idioma.
    Devuelve [(target_short, src_voice_short, src_lang), ...]. Usada por
    el CLI y por la GUI, mismo camino para las dos."""
    out_dir = out_dir or game_dir
    slot_modes = slot_modes or {}
    rng = random.Random(seed)

    short_to_full = {v: k for k, v in bm.VOICE_SHORT.items()}
    picks_src = pick_src_voices(rng, slot_modes, balance_genders)
    src_voice_of = {t: short_to_full[v] for t, v in picks_src.items()}

    lang_pools = {bm.VOICE_SHORT[target]: lang_pool(
                      mod_dir, target, src_voice_of[bm.VOICE_SHORT[target]],
                      excluded_langs, fandub_langs)
                  for target in bm.VOICES}
    lang_picks = pick_langs(lang_pools, rng, avoid_repeat_langs)
    if lang_picks is None:
        raise ValueError(
            "no se pudo evitar idiomas repetidos con esas restricciones (muy pocos "
            "idiomas disponibles entre los 4 slots). Excluye menos idiomas, o desactiva "
            "\"no repetir idiomas\".")

    picks = []
    modified_streams = {}
    modified_banks = {}
    modified_sources = {}
    for target in bm.VOICES:
        target_short = bm.VOICE_SHORT[target]
        src_voice = src_voice_of[target_short]
        src_lang = lang_picks[target_short]
        if src_lang is None:
            raise ValueError(
                f"no hay combinaciones para {target_short} <- {bm.VOICE_SHORT[src_voice]}. "
                f"Revisa que la carpeta del mod principal sea la correcta.")
        picks.append((target_short, bm.VOICE_SHORT[src_voice], src_lang))
        log(f"  {target_short:8s} <- {bm.VOICE_SHORT[src_voice]}/{src_lang}")

        archive = combo_archive(mod_dir, target, src_voice, src_lang)
        if archive is None:
            continue
        modified_streams.update(archive.wwise_streams)
        modified_banks.update(archive.wwise_banks)      # exertion bank (cross-type), if any
        modified_sources.update(archive.audio_sources)  # its sources, needed to regenerate it

    if not modified_streams:
        raise ValueError("nada que escribir (revisa las carpetas elegidas)")

    patch = bm.core.GameArchive()
    num = next_patch_num(out_dir)
    patch.name = f"{PATCH_STEM}.patch_{num}"
    patch.magic = 0xF0000011
    patch.num_types = patch.num_files = patch.unknown = 0
    patch.unk4Data = bm.PATCH_UNK4
    patch.audio_sources = modified_sources
    patch.wwise_banks = modified_banks
    patch.wwise_streams = modified_streams
    patch.text_banks = {}
    patch.video_sources = {}
    bm.write_stream_patch(patch, out_dir)
    log(f"listo: {patch.name}(+.stream) en {out_dir}")
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod-dir", required=True,
                     help="carpeta del mod principal descomprimido (tiene manifest.json)")
    ap.add_argument("--game-dir", default=None,
                     help="carpeta data/ de Helldivers 2, destino de escritura "
                          "(default: autodetectar/preguntar)")
    ap.add_argument("--seed", type=int, default=None,
                     help="fija la mezcla en vez de sortear una nueva")
    ap.add_argument("--out-dir", default=None,
                     help="donde escribir el patch (default: --game-dir)")
    ap.add_argument("--exclude", default="",
                     help="idiomas separados por coma a sacar del sorteo (ej. jp,cn)")
    args = ap.parse_args()
    game_dir = args.game_dir or find_game_dir()
    excluded = {l.strip() for l in args.exclude.split(",") if l.strip()}
    run_randomize(args.mod_dir, game_dir, args.out_dir, excluded, args.seed)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
    if sys.stdin.isatty():
        input("\nEnter para salir.")
