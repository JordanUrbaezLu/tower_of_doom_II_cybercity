# SPDX-License-Identifier: AGPL-3.0-or-later
"""Archive v49 Miles weapon events and resolve their authored source choices.

Format / LZB decoding derived from r-ex/rsx 2.3.0 (AGPL-3.0), specifically
src/game/audio/{miles,event}.{h,cpp} and thirdparty/rad_lzb_simple; also follows
the existing Hellbound trace_apex_fire_events.py investigation. This is an
offline dependency reader, not a simulation of Apex's controller/mixer state.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import struct

from extract_sources import APEX, LIBRARY, write_json


def u(data, offset, fmt="I"):
    return struct.unpack_from("<" + fmt, data, offset)[0]


def lzb(data, size):
    if len(data) == size:
        return data
    result = bytearray()
    pos = 0

    def excess():
        nonlocal pos
        byte = data[pos]
        pos += 1
        value = byte
        if byte >= 192:
            for shift in (6, 13, 20, 27):
                byte = data[pos]
                pos += 1
                value += byte << shift
                if byte < 128:
                    break
        return value

    while len(result) < size:
        control = data[pos]
        pos += 1
        literals, match = control & 15, control >> 4
        if literals == 15:
            literals += excess()
        if literals == 9 and len(result) + literals >= size:
            literals = size - len(result)
        result.extend(data[pos:pos + literals])
        pos += literals
        if len(result) == size:
            break
        length = match + 4
        if match < 15:
            offset = u(data, pos, "H")
            pos += 2
        else:
            value = data[pos]
            pos += 1
            if value & 128:
                offset = value & 7
                length = ((value & 127) >> 3) + 4
                if length == 19:
                    length += excess()
            else:
                offset = u(data, pos, "H")
                pos += 2
                length += value
                if value == 127:
                    length += excess()
        if not 0 < offset <= len(result):
            raise ValueError("Invalid LZB back-reference")
        for _ in range(length):
            result.append(result[-offset])
    if len(result) != size or pos != len(data):
        raise ValueError("LZB size/consumption mismatch")
    return bytes(result)


def main(keywords=("r97", "r99", "peacekeeper", "energy_shotgun")):
    bank_path = APEX / "audio/ship/general.mbnk"
    bank = bank_path.read_bytes()
    if u(bank, 4) != 49:
        raise ValueError("This reader only supports Miles bank version 49")
    strings, names, action_base, source_base = (u(bank, p, f) for p, f in
                                               ((0x70, "Q"), (0x68, "Q"), (0x2C, "I"), (0x34, "I")))

    def string(offset):
        return bank[strings + offset:bank.index(b"\0", strings + offset)].decode("utf-8")

    events = {}
    for i in range(u(bank, 0x1C)):
        name_offset, data_offset = struct.unpack_from("<II", bank, names + i * 8)
        events[string(name_offset)] = action_base + data_offset
    canonical = {n.lower(): n for n in events}

    def resolve_event(name):
        # Execute-event actions can qualify names with a /general/ bank path.
        return canonical.get(name.replace("\\", "/").rsplit("/", 1)[-1].lower())
    write_json(LIBRARY / "evidence/audio_event_names.json", sorted(events))
    wanted = {n for n in events if any(k in n.lower() for k in keywords)}
    # Also follow the event strings in the actual weapon definitions.
    for path in (LIBRARY / "assets/weapon").glob("*.txt"):
        if any(k in path.name for k in ("r97", "energy_shotgun")):
            for name in re.findall(r'"[^"\n]+"\s+"([^"\n]+)"', path.read_text()):
                resolved = resolve_event(name)
                if resolved:
                    wanted.add(resolved)
    initial = set(wanted)
    queue = sorted(wanted)
    records = {}
    errors = []
    raw_dir = LIBRARY / "audio/event_data"
    raw_dir.mkdir(parents=True, exist_ok=True)
    while queue:
        name = queue.pop(0)
        if name in records:
            continue
        offset = events[name]
        decompressed, compressed = struct.unpack_from("<HH", bank, offset)
        packed = bank[offset + 4:offset + 4 + compressed]
        raw = lzb(packed, decompressed)
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
        (raw_dir / (safe + ".bin")).write_bytes(raw)
        row = dict(name=name, bank_offset=offset, compressed_bytes=compressed, bytes=len(raw),
                   sha256=hashlib.sha256(raw).hexdigest(), raw_file=f"audio/event_data/{safe}.bin",
                   selection="weapon_name_or_definition" if name in initial else "called_event", actions=[],
                   sources=[], calls=[])
        at = 0
        try:
            while at < len(raw):
                kind = raw[at] & 15
                size = u(raw, at + 2, "H") * 4
                if size < 4 or at + size > len(raw):
                    raise ValueError("Invalid action size")
                data = raw[at:at + size]
                action = dict(type=kind, offset=at, bytes=size)
                if kind == 8:
                    action["calls"] = [string(u(data, 12 + j * 4)) for j in range(u(data, 4))]
                    row["calls"].extend(action["calls"])
                if kind == 0:
                    state = u(data, 0x76, "H") * 4
                    links = u(data, 0x78, "H") * 4
                    selectors = u(data, 0x7A, "H") * 4
                    action["states"] = []

                    def selector(pos, base, seen=frozenset()):
                        if pos in seen:
                            raise ValueError("Cyclic source selector")
                        typ = data[pos] & 7
                        item = dict(type=typ, weight=data[pos + 1])
                        if typ == 0:
                            index = u(data, pos + 4, "i")
                            item["source_index"] = index
                            if index >= 0:
                                item["source"] = string(u(bank, source_base + index * 80, "Q"))
                                row["sources"].append(item["source"])
                        else:
                            item["children"] = [selector(base + u(data, pos + 12 + j * 2, "H") * 4,
                                                         base, seen | {pos})
                                                for j in range(u(data, pos + 2, "H"))]
                        return item

                    for _ in range(data[1]):
                        current = dict(name=string(u(data, state)), selectors=[])
                        for j in range(data[state + 4]):
                            index = u(data, links + data[state + 6] * 4 + j * 36, "i")
                            if index != -1:
                                root = selectors + index * 4
                                current["selectors"].append(selector(root, root))
                        action["states"].append(current)
                        state += (104 if u(data, state + 14, "H") & 256 else 80) + 36 * (data[state + 8] + data[state + 9])
                row["actions"].append(action)
                at += size
                if data[0] & 16:
                    break
        except (ValueError, IndexError, struct.error, UnicodeDecodeError) as e:
            row["parse_error"] = str(e)
            errors.append(dict(event=name, error=str(e)))
        row["sources"] = sorted(set(row["sources"]))
        row["calls"] = sorted(set(row["calls"]))
        for called in row["calls"]:
            resolved = resolve_event(called)
            if resolved and resolved not in records:
                queue.append(resolved)
        records[name] = row

    # Preserve the complete small metadata bank/project: unknown action fields and
    # graph/string offsets can still be interpreted later without a lost dependency.
    shared = LIBRARY / "audio/bank_metadata"
    shared.mkdir(exist_ok=True)
    for stem in ("general.mbnk", "general.mbnk_digest", "audio.mprj"):
        src = bank_path.parent / stem
        if src.exists() and not (shared / stem).exists():
            shutil.copy2(src, shared / stem)
    sources = sorted({s for r in records.values() for s in r["sources"]})
    wavs = {p.stem.lower() for p in (LIBRARY / "audio/audio").glob("*.wav")}
    missing = [s for s in sources if s.lower() not in wavs]
    result = dict(bank_version=49, bank_sha256=hashlib.sha256(bank).hexdigest(),
                  bank_events=len(events), selected_events=len(records), source_count=len(sources),
                  sources=sources, missing_wavs=missing, parse_errors=errors,
                  unresolved_calls=sorted({s for r in records.values() for s in r["calls"] if not resolve_event(s)}),
                  events=[records[n] for n in sorted(records)],
                  interpretation="All authored selector branches; runtime conditions are not evaluated.")
    write_json(LIBRARY / "evidence/audio_events.json", result)
    print(json.dumps({k: len(result[k]) if isinstance(result[k], list) else result[k]
                      for k in ("bank_events", "selected_events", "source_count", "parse_errors", "missing_wavs", "unresolved_calls")}, indent=2))


if __name__ == "__main__":
    main()
