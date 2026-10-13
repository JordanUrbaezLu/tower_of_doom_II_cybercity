"""THE SILENT-SOUNDS GATE (asset pack PK02, 2026-10-04): every sound the map's scripts play BY NAME is defined where
the build loads aliases from, and no custom alias rides the one play call this map has proven silent.

THE GAP THIS CLOSES (verified 2026-10-04): an alias no loaded table defines plays NOTHING, with no error at link time
and none in game. The map shipped three of them for weeks: zmb_no_purchase (25 refusal sites: every door, crate,
altar, teleporter, the class terminal, the Black Market, the Battle Arena, the finale - docs/43 B1) and the Pack-a-
Punch's cw_mus_perks_packa_sting / _jingle (docs/43 B2). Separately, PlaySoundAtPosition plays nothing audible for a
CUSTOM alias here (v19.21c: the hoop sting, the riot shield break and the C4 blast all paid for it) - the BO6 elites'
death tails still went through it. PK02 defines the three aliases in sound/aliases/tod_ui.csv and moves the death tails
onto a script_origin carrier; this gate keeps both classes from coming back.

  python tools/sfx/silent_sounds/check_wiring.py --check [--root DIR]   the build gate (exit 1 on a failure)
  python tools/sfx/silent_sounds/check_wiring.py --list  [--root DIR]   every literal alias, where it is defined
  python tools/sfx/silent_sounds/check_wiring.py --selftest             the planted-error controls

DIR (default the repo) is any tree laid out like the repo (a staged overlay). The private tools root
(C:/BO3Tools/TOD2Cybercity) is only READ: a table the zone config names that the repo does not carry (the vendored
zm_cwpap_sound.csv) is read from its share/raw/sound/aliases, and a FileSpec may live in either sound_assets.

THE RULES
  1. RESOLVE - every string literal (or a #define of one) passed as the alias of a sound call in scripts/**/*.gsc|csc|gsh
     names a row of an ALIAS table sound/zoneconfig/zm_tod2_cybercity.szc loads. A literal concatenated with a number
     ("tod_spin_tick_" + n) must prefix a defined row. A name nothing defines FAILS unless STOCK lists it with a reason
     (a stock zm alias these tables cannot see: unverifiable from here, so it is listed, never assumed). A STOCK name
     that a table now defines is reported for pruning.
  2. BO6 LANE - every BO6 source name _tod_bo6_audio.gsc and its generated note table can emit
     (evt|fly|vox|prj|wpn|dst _ai_*) is defined as hb_bo6_<name>.
  3. NO SILENT LANE - no PlaySoundAtPosition plays a map-defined alias (literal, #define or a bare variable inside the
     BO6 audio lane) except the retired / unreachable sites PSAP_RETIRED lists.
  4. THE PK02 ROWS - zmb_no_purchase, cw_mus_perks_packa_sting and cw_mus_perks_packa_jingle are defined, 3D,
     NONLOOPING, carry no sound context (lint_tod_sound_context.js), and point at an existing mono 48 kHz 16-bit wav.
  5. THE MANGLER'S FOOTFALLS - test_mangler_steps.js (beside this file) runs the shipping _tod_mangler.gsc
     step_crossed() through tools/sky_ships/gsc_eval.js: six footfalls a run cycle on the clip's notes at every
     playback rate, none on a restart / jump / freeze, two negative controls.
  6. THE JINGLE'S HOLD - zm_cwpap::jingle_hold_reason reads level.tod_fall_siren_on (_tod_fall), level.tod_music_ee
     and the intro alias "tod_fall_intro" (_tod_atmosphere); a rename in either owner fails here, not in a playtest.
  7. THE KEYED HELPER - zm_utility::play_sound_at_pos( ref, pos ) / play_sound_on_ent( ref ) take a level.zombie_sounds
     KEY, not an alias: a literal (or #define) key must be one stock _zm.gsc registers (STOCK_KEYS) or one a script here
     add_sound's. Any other key plays nothing (every door slide did, until 2026-10-05).
"""
import argparse, csv, json, os, re, subprocess, sys, tempfile, wave

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PRIVATE = r"C:\BO3Tools\TOD2Cybercity"
SZC = os.path.join("sound", "zoneconfig", "zm_tod2_cybercity.szc")

# Stock aliases the scripts play that none of this map's tables define. They are expected in the stock zm sound
# banks every usermap loads; nothing here can prove that, so each is listed with where it is played and why it is
# accepted. Adding a name here is a decision: a NEW unresolved name is far more likely the next zmb_no_purchase.
STOCK = {
    "zmb_cha_ching": "stock purchase cha-ching (zm common); PaP, crates, altars, teleports, the shop",
    "zmb_hellhound_prespawn": "stock hellhound spawn tell (zm common, dog rounds); the elites' spawn tell",
    "zmb_hellhound_bolt": "stock hellhound spawn bolt (zm common, dog rounds); the elites' spawn tell",
    "zmb_perks_power_on": "stock perk-machine power-on (zm common); _tod_perk_scatter",
    "zmb_switch_flip": "stock power switch flip (_zm_power.gsc plays it); the Fall's alarm lever",
    "zmb_turn_on": "stock power-on (_zm_power.gsc plays it); the Fall's alarm lever",
    # (zmb_heavy_door_open left 2026-10-05: the user's run logged SoundGetPlaybackTime -1 for it - NOT loaded in
    # this usermap - so sound/aliases/tod_ui.csv now defines it: an original BO1 hydraulic door, sound_assets/tod/doors)
    # (the Panzer pack's, the Apothicon Fury's and the hellhound director's stock rows left 2026-10-05 with those
    # systems, retired whole by W2E - nothing in the tree plays them now)
    "prj_bullet_impact_robot_headshot": "stock bullet impact; the Civil Protector companion client script",
    "zmb_bgb_abh_teleport_in": "stock gobblegum (Anywhere But Here); the Mage's Blink (the Mage is being retired)",
}

# PlaySoundAtPosition sites of a map-defined alias that are retired or unreachable, so their silence costs nothing.
# file (repo-relative, forward slashes) -> {alias: why}. Bring one back to life and it must move to a carrier first.
PSAP_RETIRED = {
    "scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc": {
        "tod_thor_clap": "THOR'S THUNDER retired 2026-09-26 (Warrior card cut)",
        "tod_thor_zap": "THOR'S THUNDER retired 2026-09-26 (Warrior card cut)",
        "tod_thor_storm1": "THOR'S THUNDER retired 2026-09-26 (Warrior card cut)",
        "tod_thor_storm2": "THOR'S THUNDER retired 2026-09-26 (Warrior card cut)",
    },
    "scripts/zm/zm_tod2_cybercity/_tod_lunge.gsc": {
        "tod_warp": "CHAIN LUNGE removed 2026-08-24 (_tod_main.gsc: the module is not threaded)",
    },
}

# BO6 source names the shared audio module knows but this map never voices: Hellbound's Amalgam is not ported
# (no actor is ever attached with kind "amalgam", and no hb_bo6_amalgam table ships). Port it and its rows first.
BO6_ABSENT = {
    "evt_ai_amalgam_death": "the Amalgam is not in TOD II",
    "fly_ai_amalgam_grab_hit": "the Amalgam is not in TOD II",
    "vox_ai_amalgam_pain": "the Amalgam is not in TOD II",
    "vox_ai_amalgam_spawn": "the Amalgam is not in TOD II",
}

PK02_ROWS = ("zmb_no_purchase", "cw_mus_perks_packa_sting", "cw_mus_perks_packa_jingle")

# THE KEYED HELPER (2026-10-05): stock zm_utility::play_sound_at_pos / play_sound_on_ent look `ref` up in
# level.zombie_sounds and, for a key nobody add_sound'ed, hit AssertMsg + return: no sound, and no text in a retail
# console. These are the keys stock _zm.gsc init_sounds() registers for every map (read from share/raw 2026-10-05;
# "none" is the helper's own early return). Stock MAPS register the rest themselves (zm_giant: zmb_heavy_door_open);
# the usermap template registers nothing, so _tod_doors' slide and unseal cue played silently until they moved to a
# script_origin carrier.
STOCK_KEYS = frozenset((
    "end_of_round", "end_of_game", "chalk_one_up", "purchase", "no_purchase", "playerzombie_usebutton_sound",
    "playerzombie_attackbutton_sound", "playerzombie_adsbutton_sound", "zombie_head_gib", "rebuild_barrier_piece",
    "rebuild_barrier_metal_piece", "rebuild_barrier_hover", "debris_hover_loop", "break_barrier_piece",
    "grab_metal_bar", "break_metal_bar", "drop_metal_bar", "blocker_end_move", "barrier_rebuild_slam",
    "bar_rebuild_slam", "zmb_rock_fix", "zmb_vent_fix", "door_slide_open", "door_rotate_open", "debris_move",
    "open_chest", "music_chest", "close_chest", "weapon_show", "break_stone", "none"))
KEYED_RE = re.compile(r"\b(play_sound_at_pos|play_sound_on_ent)\s*\(", re.I)
ADD_SOUND_RE = re.compile(r'\badd_sound\s*\(\s*"([^"]+)"', re.I)

# name -> index of the alias argument (0-based). GSC/CSC calls are case-insensitive; a CSC entity call carries the
# localClientNum first (playsound( 0, "x" )), which ALIAS_ARG_SKIP_NUMERIC handles.
CALLS = {
    "playsound": 0, "playlocalsound": 0, "playsoundtoplayer": 0, "playsoundtoteam": 0, "playloopsound": 0,
    "playsoundontag": 0, "playsoundatposition": 0, "playsoundwithnotify": 0, "playloopatposition": 0,
    "play_sound_at_origin": 1, "sound_at": 0, "soundgetplaybacktime": 0,
}
CALL_RE = re.compile(r"\b(" + "|".join(sorted(CALLS, key=len, reverse=True)) + r")\s*\(", re.I)
DEFINE_RE = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+"([^"]*)"', re.M)
BO6_NAME = re.compile(r"^(evt|fly|vox|prj|wpn|dst)_ai_[a-z0-9_]+$")
BO6_FILES = ("_tod_bo6_audio.gsc", "_tod_bo6_audio_events.gsh")


def strip_comments(text):
    """Remove // and /* */ comments, keeping string literals and line numbers intact."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * text.count("\n", i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def split_args(text, start):
    """Top-level arguments of the call whose '(' is at text[start - 1]; returns (args, end index)."""
    depth, i, cur, args, n = 0, start, [], [], len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            cur.append(text[i:j + 1])
            i = j + 1
            continue
        if c in "([":
            depth += 1
        elif c in ")]":
            if depth == 0:
                args.append("".join(cur).strip())
                return args, i
            depth -= 1
        elif c == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    return args, n


def read_tables(root):
    """{lowercased alias name: (table file, row dict)} for every ALIAS source the zone config loads."""
    szc = json.load(open(os.path.join(root, SZC), encoding="utf-8-sig"))
    defined, sources, missing = {}, [], []
    for s in szc.get("Sources", []):
        if s.get("Type") != "ALIAS":
            continue
        fn = s["Filename"]
        path = os.path.join(root, "sound", "aliases", fn)
        if not os.path.exists(path):
            path = os.path.join(PRIVATE, "share", "raw", "sound", "aliases", fn)
        if not os.path.exists(path):
            missing.append(fn)
            continue
        sources.append(path)
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                name = (row.get("Name") or "").strip()
                if name and not name.startswith("#"):
                    defined.setdefault(name.lower(), (fn, row))
    return defined, sources, missing


def scan_scripts(root):
    """[(file, line, call, alias or None, kind, raw)] kind: literal | prefix | define | variable."""
    files, defines = [], {}
    for dp, _, fns in os.walk(os.path.join(root, "scripts")):
        for fn in fns:
            if fn.lower().endswith((".gsc", ".csc", ".gsh")):
                p = os.path.join(dp, fn)
                text = strip_comments(open(p, encoding="utf-8", errors="replace").read())
                files.append((p, text))
                for m in DEFINE_RE.finditer(text):
                    defines.setdefault(m.group(1), m.group(2))
    uses = []
    for p, text in files:
        rel = os.path.relpath(p, root).replace("\\", "/")
        local = dict(defines)
        local.update({m.group(1): m.group(2) for m in DEFINE_RE.finditer(text)})
        for m in CALL_RE.finditer(text):
            name = m.group(1).lower()
            args, _ = split_args(text, m.end())
            idx = CALLS[name]
            # a client entity call carries localClientNum first: playsound( 0, "x" ) / playsound( localclientnum, "x" )
            if p.lower().endswith(".csc") and idx == 0 and len(args) > 1 and not args[0].startswith('"') \
                    and args[1].startswith('"'):
                idx = 1
            if idx >= len(args):
                continue
            a = args[idx]
            line = text.count("\n", 0, m.start()) + 1
            lit = re.match(r'^"([A-Za-z0-9_]+)"\s*(\+.*)?$', a)
            if lit:
                uses.append((rel, line, name, lit.group(1), "prefix" if lit.group(2) else "literal", a))
            elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", a) and a in local:
                uses.append((rel, line, name, local[a], "define", a))
            else:
                uses.append((rel, line, name, None, "variable", a))
    return uses, files


def bo6_names(files):
    out = set()
    for p, text in files:
        if os.path.basename(p) in BO6_FILES:
            for lit in re.findall(r'"([a-z0-9_@]+)"', text):
                lit = lit.split("@", 1)[-1]
                if BO6_NAME.match(lit):
                    out.add(lit)
    return out


def wav_info(root, filespec):
    rel = filespec.replace("\\", "/")
    for base in (os.path.join(root, "sound_assets"), os.path.join(PRIVATE, "sound_assets")):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            try:
                with wave.open(p, "rb") as w:
                    return p, w.getnchannels(), w.getframerate(), w.getsampwidth() * 8
            except Exception:
                return p, None, None, None
    return None, None, None, None


def check(root, verbose=False):
    errors, notes = [], []
    defined, sources, missing = read_tables(root)
    for fn in missing:
        errors.append("the zone config loads %s but neither the tree nor the private root carries it" % fn)
    uses, files = scan_scripts(root)

    # rule 1: resolve
    seen_stock, unresolved = set(), {}
    for rel, line, call, alias, kind, raw in uses:
        if alias is None:
            continue
        key = alias.lower()
        if kind == "prefix":
            ok = any(k.startswith(key) for k in defined)
        else:
            ok = key in defined
        if ok:
            continue
        if key in STOCK:
            seen_stock.add(key)
            continue
        unresolved.setdefault(alias, []).append("%s:%d %s(%s)" % (rel, line, call, raw))
    for alias, where in sorted(unresolved.items()):
        errors.append("UNDEFINED alias '%s' (plays nothing): %s%s" % (alias, where[0],
                      (" (+%d more)" % (len(where) - 1)) if len(where) > 1 else ""))
    for key in sorted(STOCK):
        if key in defined:
            notes.append("STOCK entry '%s' is now defined by %s - prune it from STOCK" % (key, defined[key][0]))
        elif key not in seen_stock:
            notes.append("STOCK entry '%s' is no longer played by any script - prune it from STOCK" % key)

    # rule 2: the BO6 lane
    names = bo6_names(files)
    for n in sorted(names):
        if ("hb_bo6_" + n) in defined:
            if n in BO6_ABSENT:
                notes.append("BO6_ABSENT entry '%s' now has its row - prune it" % n)
        elif n not in BO6_ABSENT:
            errors.append("BO6 lane: '%s' has no hb_bo6_%s row (sound/aliases/hb_bo6_*.csv)" % (n, n))
    # ...and every full alias name the module spells out (sound_at() tails, the bank probe's list) is defined too
    # (not the generated .gsh: its hb_bo6_step_ghoul_* strings are NOTETRACK names, not aliases)
    for p, text in files:
        if os.path.basename(p) == BO6_FILES[0]:
            for lit in sorted(set(re.findall(r'"((?:hb_bo6_|zmb_|cw_)[a-z0-9_]+)"', text))):
                if lit not in defined and lit not in STOCK:
                    errors.append("BO6 lane: %s names '%s', which no loaded table defines" % (os.path.basename(p), lit))

    # rule 3: no custom alias through PlaySoundAtPosition
    for rel, line, call, alias, kind, raw in uses:
        if call != "playsoundatposition":
            continue
        if alias is None:
            if os.path.basename(rel) in BO6_FILES:
                errors.append("SILENT LANE: %s:%d PlaySoundAtPosition( %s ) in the BO6 audio lane - use sound_at()"
                              % (rel, line, raw))
            continue
        if alias.lower() in defined and alias not in PSAP_RETIRED.get(rel, {}):
            errors.append("SILENT LANE: %s:%d PlaySoundAtPosition( \"%s\" ) - a custom alias plays nothing through "
                          "it here (v19.21c); use a script_origin carrier (tod_perk_scatter::play_sound_at_origin)"
                          % (rel, line, alias))

    # rule 4: the PK02 rows
    for name in PK02_ROWS:
        if name not in defined:
            errors.append("PK02 row '%s' is not defined by any loaded table" % name)
            continue
        fn, row = defined[name]
        if (row.get("PanType") or "").lower() != "3d":
            errors.append("PK02 row '%s' (%s) must be 3d: every caller plays it on an entity" % (name, fn))
        if (row.get("Looping") or "").upper() != "NONLOOPING":
            errors.append("PK02 row '%s' (%s) must be NONLOOPING" % (name, fn))
        for col in ("ContextType", "ContextValue", "ContextType1", "ContextValue1"):
            if (row.get(col) or "").strip():
                errors.append("PK02 row '%s' (%s) carries %s - this map sets no sound context, it would be silent"
                              % (name, fn, col))
        p, ch, sr, bits = wav_info(root, row.get("FileSpec") or "")
        if p is None:
            errors.append("PK02 row '%s' FileSpec %s exists in neither sound_assets" % (name, row.get("FileSpec")))
        elif (ch, sr, bits) != (1, 48000, 16):
            errors.append("PK02 row '%s' wav %s is %s ch / %s Hz / %s bit (want mono 48000 16)" % (name, p, ch, sr, bits))

    # rule 6: the PaP jingle's hold reads state other modules own - fail if an owner renames it (the hold would
    # silently stop holding and the jingle would play under the siren / the intro / the teddy-bear song again)
    pap = os.path.join(root, "scripts", "zm", "zm_cwpap.gsc")
    if os.path.exists(pap) and "function jingle_hold_reason()" in open(pap, encoding="utf-8").read():
        owners = (("_tod_fall.gsc", "level.tod_fall_siren_on = true;", "level.tod_fall_siren_on"),
                  ("_tod_atmosphere.gsc", "level.tod_music_ee = true;", "level.tod_music_ee"),
                  ("_tod_atmosphere.gsc", '#define TOD_MUSIC_INTRO_ALIAS   "tod_fall_intro"', '"tod_fall_intro"'))
        for fn, needle, what in owners:
            p = os.path.join(root, "scripts", "zm", "zm_tod2_cybercity", fn)
            if not os.path.exists(p) or needle not in open(p, encoding="utf-8").read():
                errors.append("PaP jingle hold: %s no longer carries `%s` - zm_cwpap::jingle_hold_reason reads %s"
                              % (fn, needle, what))

    # rule 7: the keyed helper - its first argument is a level.zombie_sounds KEY, so a literal / #define key must be
    # registered by stock (STOCK_KEYS) or by an add_sound here; a variable key cannot be judged from here
    keys, all_defines = set(STOCK_KEYS), {}
    for p, text in files:
        keys.update(k.lower() for k in ADD_SOUND_RE.findall(text))
        for m in DEFINE_RE.finditer(text):
            all_defines.setdefault(m.group(1), m.group(2))
    for p, text in files:
        rel = os.path.relpath(p, root).replace("\\", "/")
        local = dict(all_defines)
        local.update({m.group(1): m.group(2) for m in DEFINE_RE.finditer(text)})
        for m in KEYED_RE.finditer(text):
            if re.search(r"\bfunction\s+$", text[max(0, m.start() - 24):m.start()]):
                continue   # the helper's own definition (a vendored _zm_utility)
            args, _ = split_args(text, m.end())
            if not args or not args[0]:
                continue
            a = args[0]
            lit = re.match(r'^"([^"]*)"$', a)
            key = lit.group(1) if lit else (local.get(a) if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", a) else None)
            if key is None or key.lower() in keys:
                continue
            line = text.count("\n", 0, m.start()) + 1
            errors.append("KEYED SOUND: %s:%d %s( %s ) takes a level.zombie_sounds KEY and nothing registers '%s' "
                          "(stock _zm.gsc or an add_sound here) - it plays NOTHING; play the alias on a script_origin "
                          "carrier (tod_perk_scatter::play_sound_at_origin)" % (rel, line, m.group(1), a, key))

    # rule 5: the Mangler's footfalls - the shipping step_crossed() through gsc_eval (test_mangler_steps.js)
    steps = "skipped (no _tod_mangler.gsc in this tree)"
    if os.path.exists(os.path.join(root, "scripts", "zm", "zm_tod2_cybercity", "_tod_mangler.gsc")):
        try:
            r = subprocess.run(["node", os.path.join(HERE, "test_mangler_steps.js"), "--root", root],
                               capture_output=True, text=True, timeout=120)
            out = (r.stdout + r.stderr).strip().splitlines()
            steps = out[-1] if out else "(no output)"
            if r.returncode != 0:
                fails = [l.strip() for l in out if l.strip().startswith("FAIL")] or out[-3:]
                errors.append("MANGLER STEPS (tools/sfx/silent_sounds/test_mangler_steps.js): " + " | ".join(fails[:4]))
        except (OSError, subprocess.TimeoutExpired) as e:
            errors.append("MANGLER STEPS could not run node: %s" % e)

    if verbose:
        rows, kinds = {}, {}
        for rel, line, call, alias, kind, raw in uses:
            if alias:
                rows.setdefault(alias, []).append("%s:%d" % (rel, line))
                kinds[alias] = kind
        for alias in sorted(rows, key=str.lower):
            key = alias.lower()
            pref = [k for k in defined if k.startswith(key)] if kinds[alias] == "prefix" else []
            where = defined[key][0] if key in defined else (
                ("%s (prefix of %d)" % (defined[pref[0]][0], len(pref))) if pref else
                ("STOCK" if key in STOCK else "UNDEFINED"))
            print("  %-44s %-26s %3d site(s)  %s" % (alias, where, len(rows[alias]), rows[alias][0]))
    return errors, notes, dict(tables=len(sources), aliases=len(defined), uses=len(uses),
                               literal=sum(1 for u in uses if u[3]), stock=len(seen_stock), bo6=len(names), steps=steps)


def selftest():
    """Plant each failure in a scratch tree and require the gate to catch it; plant two legal shapes and require a pass."""
    hdr = "Name,Behavior,Storage,FileSpec,Template,PanType,Looping,ContextType,ContextValue"
    ok_rows = [
        "tod_ok,,,x.wav,UIN_MOD,3d,NONLOOPING,,",
        "tod_tick_1,,,x.wav,UIN_MOD,2d,NONLOOPING,,",
        "zmb_no_purchase,,,x.wav,UIN_MOD,3d,NONLOOPING,,",
        "cw_mus_perks_packa_sting,,,x.wav,UIN_MOD,3d,NONLOOPING,,",
        "cw_mus_perks_packa_jingle,,,x.wav,UIN_MOD,3d,NONLOOPING,,",
        "hb_bo6_fly_ai_ok,,,x.wav,UIN_MOD,3d,NONLOOPING,,",
    ]
    cases = [
        # (label, script text, table extra rows, expect failure substring or None)
        ("defined literal", 'function f() { self PlaySound( "tod_ok" ); }', [], None),
        ("prefix + n", 'function f( n ) { self PlayLocalSound( "tod_tick_" + n ); }', [], None),
        ("stock listed", 'function f() { self PlaySound( "zmb_cha_ching" ); }', [], None),
        ("commented out", '// self PlaySound( "tod_nope" );\nfunction f() {}', [], None),
        ("undefined literal", 'function f() { player PlaySound( "tod_nope" ); }', [], "UNDEFINED alias 'tod_nope'"),
        ("undefined define", '#define SND "tod_nope2"\nfunction f() { self PlaySound( SND ); }', [], "tod_nope2"),
        ("csc client num", 'function f( lcn ) { self playsound( lcn, "tod_nope3" ); }', [], "tod_nope3"),
        ("psap custom", 'function f() { PlaySoundAtPosition( "tod_ok", self.origin ); }', [], "SILENT LANE"),
        ("missing PK02 row", 'function f() {}', ["-zmb_no_purchase"], "PK02 row 'zmb_no_purchase'"),
        ("2d PK02 row", 'function f() {}', ["~cw_mus_perks_packa_jingle,,,x.wav,UIN_MOD,2d,NONLOOPING,,"], "must be 3d"),
        ("context row", 'function f() {}', ["~zmb_no_purchase,,,x.wav,UIN_MOD,3d,NONLOOPING,water,over"], "ContextType"),
        ("bo6 lane ok", 'function f( a ) { emit( a, "fly_ai_ok", "x" ); }', [], None),
        ("bo6 lane row missing", 'function f( a ) { emit( a, "fly_ai_missing", "x" ); }', [], "BO6 lane: 'fly_ai_missing'"),
        ("bo6 lane full name missing", 'function f() { probe = array( "hb_bo6_fly_ai_ok", "hb_bo6_gone" ); }', [],
         "names 'hb_bo6_gone'"),
        ("bo6 lane psap variable", 'function f( a ) { alias = "hb_bo6_fly_ai_ok"; PlaySoundAtPosition( alias, a.origin ); }',
         [], "SILENT LANE"),
        ("keyed stock key", 'function f() { zm_utility::play_sound_at_pos( "purchase", self.origin ); }', [], None),
        ("keyed key added here", 'function f() { zm_utility::add_sound( "tod_key", "tod_ok" ); '
         'zm_utility::play_sound_at_pos( "tod_key", self.origin ); }', [], None),
        ("keyed alias not key", 'function f() { zm_utility::play_sound_at_pos( "zmb_heavy_door_open", self.origin ); }',
         [], "KEYED SOUND"),
        ("keyed define (the 2026-10-05 door)", '#define SLIDE "zmb_heavy_door_open"\n'
         'function f( d ) { self zm_utility::play_sound_on_ent( SLIDE ); zm_utility::play_sound_at_pos( SLIDE, d.org ); }',
         [], "KEYED SOUND"),
    ]
    failures = 0
    for label, script, extra, expect in cases:
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "sound", "aliases"))
            os.makedirs(os.path.join(d, "sound", "zoneconfig"))
            os.makedirs(os.path.join(d, "scripts", "zm"))
            os.makedirs(os.path.join(d, "sound_assets"))
            with wave.open(os.path.join(d, "sound_assets", "x.wav"), "wb") as w:
                w.setnchannels(1); w.setframerate(48000); w.setsampwidth(2); w.writeframes(b"\0\0" * 480)
            rows = list(ok_rows)
            for e in extra:
                if e.startswith("-"):
                    rows = [r for r in rows if not r.startswith(e[1:] + ",")]
                elif e.startswith("~"):
                    name = e[1:].split(",", 1)[0]
                    rows = [r for r in rows if not r.startswith(name + ",")] + [e[1:]]
            open(os.path.join(d, "sound", "aliases", "t.csv"), "w", newline="").write("\r\n".join([hdr] + rows) + "\r\n")
            json.dump({"Sources": [{"Type": "ALIAS", "Name": "t", "Filename": "t.csv"}]},
                      open(os.path.join(d, SZC), "w"))
            fname = "_tod_bo6_audio.gsc" if label.startswith("bo6") else ("t.csc" if "csc" in label else "t.gsc")
            open(os.path.join(d, "scripts", "zm", fname), "w").write(script + "\n")
            errors, _, _ = check(d)
            hit = [e for e in errors if expect and expect in e]
            good = (not errors) if expect is None else bool(hit)
            if not good:
                failures += 1
                print("  SELFTEST FAIL [%s]: expected %s, got %s" % (label, expect or "a pass", errors))
    print("SILENT SOUNDS SELFTEST %s: %d cases" % ("OK" if not failures else "FAILED", len(cases)))
    return failures == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="the build gate")
    ap.add_argument("--list", action="store_true", help="print every literal alias and where it is defined")
    ap.add_argument("--selftest", action="store_true", help="planted-error controls")
    ap.add_argument("--root", default=REPO, help="a tree laid out like the repo (default the repo)")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not (a.check or a.list):
        ap.print_help()
        sys.exit(2)
    root = os.path.abspath(a.root)
    errors, notes, stats = check(root, verbose=a.list)
    for n in notes:
        print("  note: " + n)
    print("  " + stats["steps"])
    for e in errors:
        print("  FAIL " + e)
    print("SILENT SOUNDS %s: %d tables / %d aliases loaded, %d sound calls (%d by name), %d stock names listed, "
          "%d BO6 source names, root=%s" % ("OK" if not errors else "FAILED", stats["tables"], stats["aliases"],
                                             stats["uses"], stats["literal"], stats["stock"], stats["bo6"], root))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
