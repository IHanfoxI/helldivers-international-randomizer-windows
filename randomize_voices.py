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
    python randomize_voices.py [--mod-dir RUTA] [--ship-dir RUTA] [--mission-dir RUTA]
                               [--game-dir RUTA] [--seed N]

Al menos una de las tres carpetas de mod. Ship & Air y Mission solo cambian de
idioma (un idioma por personaje), no hay tipos de voz ahi. Todo sale en UN
patch; randomizar un mod suelto reusa lo que la corrida anterior sorteo para
los otros (ver write_patch).

--mod-dir es la carpeta del mod principal descomprimido (tiene manifest.json
y las subcarpetas female1/, male1/, etc.). --game-dir es la carpeta data/ del
juego, solo como destino de escritura -- sin --game-dir prueba rutas comunes
de Steam y si no encuentra, pregunta. Escribe <hash>.patch_<N>(+.stream) ahi,
eligiendo N mas alto que cualquier patch_N ya presente (para no pisar lo que
puso Arsenal). Correr de nuevo para una mezcla distinta. Si Arsenal reinstala
o actualiza el mod principal, vuelve a correr esto despues (pisa lo nuestro).
"""
import argparse, glob, json, os, random, re, sys, types

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


LEDGER = "helldivers_intl_randomizer.json"
PATCH0 = f"{PATCH_STEM}.patch_0"
KINDS = ("helldiver", "ship", "mission")
# carpeta que delata cada tipo de mod descomprimido (ver mod_kind)
KIND_MARKER = {"helldiver": "female1", "ship": "eagle", "mission": "civilian_f"}


def _stamp(path):
    st = os.stat(path)
    return [st.st_size, st.st_mtime_ns]


def load_ledger(out_dir):
    """{"files": {nombre: [tamano, mtime]}, "parts": {kind: [rutas de patch]}}.
    "files" es lo que escribio la ultima corrida; "parts" de donde salio, por
    mod, para poder re-randomizar uno solo sin perder lo sorteado en los otros.
    El formato viejo (solo {nombre: stamp}) se lee como files sin parts."""
    try:
        ledger = json.load(open(os.path.join(out_dir, LEDGER)))
    except (OSError, ValueError):
        return {"files": {}, "parts": {}}
    if "files" not in ledger:
        ledger = {"files": ledger, "parts": {}}
    return ledger


def remove_own_patches(out_dir, files, log=print):
    """Borra lo que escribio una corrida anterior del randomizer. Sin esto se
    apilan (patch_56..63) y un slot que en esta corrida sale de su mismo tipo
    no trae grunidos, asi que los de un cruce viejo seguian ganando. Solo
    borra un archivo si calza tamano+mtime con lo anotado: un Deploy de
    Arsenal reescribe desde patch_0 y puede reusar ese numero para SU patch,
    que no hay que tocar."""
    for name, stamp in files.items():
        f = os.path.join(out_dir, name)
        try:
            if _stamp(f) == stamp:
                os.remove(f)
                log(f"  borrado patch anterior: {name}")
        except OSError:
            pass


def mod_kind(mod_dir):
    """"helldiver" / "ship" / "mission" segun las carpetas del mod, o None."""
    for kind, marker in KIND_MARKER.items():
        if os.path.isdir(os.path.join(mod_dir, marker)):
            return kind
    return None


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


def pick_helldiver(mod_dir, rng, excluded_langs=(), log=print, fandub_langs=(),
                   slot_modes=None, balance_genders=False, avoid_repeat_langs=True):
    """Sortea los 4 slots Helldiver (excluyendo excluded_langs; ru/ko solo
    entran si estan en fandub_langs Y mod_dir es la variante +Fandubs).
    slot_modes: {target_short: "own"/"gender"/"any"}. avoid_repeat_langs
    evita que dos slots salgan con el mismo idioma. Devuelve
    ([(target_short, src_voice_short, src_lang), ...], [rutas de patch])."""
    slot_modes = slot_modes or {}
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

    picks, paths = [], []
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
        paths.append(combo_patch_path(mod_dir, target, src_voice, src_lang))
    return picks, paths


def npc_slots(mod_dir):
    """{slot: [idiomas con patch]} de un mod Ship & Air o Mission ya
    descomprimido (`<slot>/<lang>/<hash>.patch_0`, ver build_npc.gen_patches).
    Mission trae un slot por actor (seaf_<rol>_<m|f>, civilian_<m|f>), asi
    que cada rol y genero sale con su propio idioma. "random" es la mezcla por
    linea de builds viejos: queda fuera, aca el idioma lo sortea el randomizer."""
    out = {}
    for slot in sorted(os.listdir(mod_dir)):
        d = os.path.join(mod_dir, slot)
        if not os.path.isdir(d):
            continue
        langs = sorted(l for l in os.listdir(d)
                       if l != "random" and os.path.isfile(os.path.join(d, l, PATCH0)))
        if langs:
            out[slot] = langs
    return out


def pick_npc(mod_dir, rng, excluded_langs=(), log=print, avoid_repeat_langs=True):
    """Un idioma por slot del mod NPC. Ship & Air tiene 7 slots: si quedan
    menos idiomas que slots, no repetir es imposible y se sortea sin esa
    restriccion en vez de fallar. Devuelve ([(slot, lang), ...], [rutas])."""
    slots = npc_slots(mod_dir)
    if not slots:
        raise ValueError(f"no hay slots de voz en {mod_dir}")
    pools = {s: [l for l in langs if l not in excluded_langs] for s, langs in slots.items()}
    lang_picks = (pick_langs(pools, rng, avoid_repeat_langs)
                  or pick_langs(pools, rng, False))
    picks, paths = [], []
    for slot, lang in lang_picks.items():
        if lang is None:
            continue
        picks.append((slot, lang))
        log(f"  {slot:17s} <- {lang}")
        paths.append(os.path.join(mod_dir, slot, lang, PATCH0))
    return picks, paths


def write_patch(out_dir, new_parts, log=print):
    """Escribe UN patch con los patches de new_parts ({kind: [rutas]}) mas lo
    que la corrida anterior habia sorteado para los otros mods (ledger), y
    borra el de la corrida anterior. Un solo archivo siempre: randomizar un
    mod suelto no deja huecos en la cadena .patch_N ni pisa lo de los otros."""
    ledger = load_ledger(out_dir)
    parts = {k: v for k, v in ledger["parts"].items()
             if k not in new_parts and all(os.path.isfile(p) for p in v)}
    parts.update(new_parts)

    streams, banks, sources = {}, {}, {}
    for kind in KINDS:
        for path in parts.get(kind, []):
            archive = bm.load(path)
            streams.update(archive.wwise_streams)
            banks.update(archive.wwise_banks)      # exertion bank (cross-type), if any
            sources.update(archive.audio_sources)  # its sources, needed to regenerate it
    if not streams:
        raise ValueError("nada que escribir (revisa las carpetas elegidas)")

    remove_own_patches(out_dir, ledger["files"], log)
    patch = bm.core.GameArchive()
    patch.name = f"{PATCH_STEM}.patch_{next_patch_num(out_dir)}"
    patch.magic = 0xF0000011
    patch.num_types = patch.num_files = patch.unknown = 0
    patch.unk4Data = bm.PATCH_UNK4
    patch.audio_sources = sources
    patch.wwise_banks = banks
    patch.wwise_streams = streams
    patch.text_banks = {}
    patch.video_sources = {}
    bm.write_stream_patch(patch, out_dir)
    files = {n: _stamp(os.path.join(out_dir, n))
             for n in (patch.name, patch.name + ".stream")
             if os.path.exists(os.path.join(out_dir, n))}
    json.dump({"files": files, "parts": parts}, open(os.path.join(out_dir, LEDGER), "w"))
    log(f"listo: {patch.name}(+.stream) en {out_dir}")


def run_all(game_dir, mod_dirs, out_dir=None, excluded_langs=(), seed=None, log=print,
            fandub_langs=(), slot_modes=None, balance_genders=False,
            avoid_repeat_langs=True):
    """Randomiza los mods de mod_dirs ({kind: carpeta}, al menos uno) y
    escribe el patch. Devuelve {kind: picks}. Usada por el CLI y la GUI."""
    if not mod_dirs:
        raise ValueError("elige al menos una carpeta de mod")
    rng = random.Random(seed)
    results, new_parts = {}, {}
    for kind in KINDS:
        mod_dir = mod_dirs.get(kind)
        if not mod_dir:
            continue
        if mod_kind(mod_dir) != kind:
            raise ValueError(f"{mod_dir} no parece el mod {kind} descomprimido "
                             f"(falta la carpeta {KIND_MARKER[kind]}/)")
        log(f"[{kind}]")
        if kind == "helldiver":
            picks, paths = pick_helldiver(mod_dir, rng, excluded_langs, log, fandub_langs,
                                          slot_modes, balance_genders, avoid_repeat_langs)
        else:
            picks, paths = pick_npc(mod_dir, rng, excluded_langs, log, avoid_repeat_langs)
        results[kind], new_parts[kind] = picks, paths
    write_patch(out_dir or game_dir, new_parts, log)
    return results


def run_randomize(mod_dir, game_dir, out_dir=None, **kw):
    """Solo el mod Helldiver (compatibilidad): [(target, src_voice, lang)]."""
    return run_all(game_dir, {"helldiver": mod_dir}, out_dir, **kw)["helldiver"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod-dir", default=None,
                     help="carpeta del mod principal descomprimido (tiene manifest.json)")
    ap.add_argument("--ship-dir", default=None,
                     help="carpeta del mod Ship & Air descomprimido (opcional)")
    ap.add_argument("--mission-dir", default=None,
                     help="carpeta del mod Mission descomprimido (opcional)")
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
    mod_dirs = {k: d for k, d in (("helldiver", args.mod_dir), ("ship", args.ship_dir),
                                  ("mission", args.mission_dir)) if d}
    run_all(game_dir, mod_dirs, args.out_dir, excluded, args.seed)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
    if sys.stdin.isatty():
        input("\nEnter para salir.")
