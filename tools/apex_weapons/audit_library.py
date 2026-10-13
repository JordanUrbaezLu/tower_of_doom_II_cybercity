"""Validate the actual exports and build a hashed, searchable local catalog."""
from __future__ import annotations
import collections
import csv
import hashlib
import json
import re
import struct
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from extract_sources import APEX, LIBRARY, REPO, digest, write_json


def check_png(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature"
    pos, saw_data, ended = 8, False, False
    result = {}
    while pos < len(data):
        size, kind = struct.unpack_from(">I4s", data, pos)
        end = pos + 12 + size
        assert end <= len(data), "truncated PNG chunk"
        assert zlib.crc32(memoryview(data)[pos + 4:end - 4]) == struct.unpack_from(">I", data, end - 4)[0], "PNG CRC"
        if kind == b"IHDR":
            w, h, depth, color = struct.unpack_from(">IIBB", data, pos + 8)
            assert w and h
            result.update(width=w, height=h, depth=depth, color_type=color)
        saw_data |= kind == b"IDAT"
        pos = end
        if kind == b"IEND":
            ended = True
            break
    assert saw_data and ended and pos == len(data) and result, "incomplete PNG"
    return result


def check_wav(data):
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE", "WAV signature"
    assert struct.unpack_from("<I", data, 4)[0] + 8 == len(data), "RIFF size"
    pos, fmt, payload = 12, None, 0
    while pos + 8 <= len(data):
        kind, size = struct.unpack_from("<4sI", data, pos)
        end = pos + 8 + size
        assert end <= len(data), "truncated WAV chunk"
        if kind == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", data, pos + 8)
        if kind == b"data":
            payload += size
        pos = end + (size & 1)
    assert fmt and payload and fmt[1] and fmt[2] and fmt[3] and fmt[4], "empty WAV"
    assert payload % fmt[4] == 0, "partial audio frame"
    return dict(format=fmt[0], channels=fmt[1], sample_rate=fmt[2], bits=fmt[5],
                frames=payload // fmt[4], seconds=round(payload / fmt[3], 5), audio_bytes=payload)


def check_cast(data):
    assert len(data) >= 16
    magic, version, roots, flags = struct.unpack_from("<4I", data)
    assert magic == 0x74736163 and version == 1, "CAST header"
    counts = collections.Counter()
    files, models, animations, materials = [], [], [], []
    sizes = {"b": 1, "h": 2, "i": 4, "l": 8, "f": 4, "d": 8, "2v": 8, "3v": 12, "4v": 16}
    formats = {"b": "B", "h": "H", "i": "I", "l": "Q", "f": "f", "d": "d"}
    vertices, indices = 0, 0

    def node(pos, limit):
        nonlocal vertices, indices
        assert pos + 24 <= limit, "CAST node header"
        identifier, size, hash_value, props, children = struct.unpack_from("<IIQII", data, pos)
        end = pos + size
        assert size >= 24 and end <= limit, "CAST node length"
        tag = identifier.to_bytes(4, "little").decode("ascii")
        counts[tag] += 1
        pos += 24
        values = {}
        for _ in range(props):
            assert pos + 8 <= end
            typ, name_size, count = struct.unpack_from("<2sHI", data, pos)
            typ = typ.rstrip(b"\0").decode("ascii")
            pos += 8
            assert pos + name_size <= end
            key = data[pos:pos + name_size].decode("utf-8")
            pos += name_size
            if typ == "s":
                stop = data.index(b"\0", pos, end)
                values[key] = data[pos:stop].decode("utf-8")
                pos = stop + 1
            else:
                assert typ in sizes, f"unknown CAST property {typ}"
                finish = pos + count * sizes[typ]
                assert finish <= end, "CAST property length"
                if count == 1 and typ in formats:
                    values[key] = struct.unpack_from("<" + formats[typ], data, pos)[0]
                if tag == "mesh" and key == "vp":
                    vertices += count if typ == "3v" else count // 3
                if tag == "mesh" and key == "f":
                    indices += count
                pos = finish
        if tag == "file" and "p" in values:
            files.append(values["p"])
        if tag == "matl":
            materials.append(dict(guid=f"{hash_value:016x}", properties=values))
        if tag == "modl":
            models.append(dict(name=values.get("n"), guid=f"{hash_value:016x}"))
        if tag == "anim":
            animations.append(dict(name=values.get("n"), fps=values.get("fr"), looping=values.get("lo")))
        for _ in range(children):
            pos = node(pos, end)
        assert pos == end, "CAST trailing node data"
        return end

    pos = 16
    for _ in range(roots):
        pos = node(pos, len(data))
    assert pos == len(data), "CAST trailing file data"
    return dict(nodes=dict(counts), vertices=vertices, triangles=indices // 3,
                texture_references=files, models=models, animations=animations, materials=materials)


def read_asset(path):
    # Read independent files concurrently; antivirus/file-open latency otherwise
    # dominates this many-file archive. Large opaque RPaks need only a hash.
    if path.suffix == ".rpak":
        return path, None, digest(path), path.stat().st_size
    data = path.read_bytes()
    return path, data, hashlib.sha256(data).hexdigest(), len(data)


def main():
    records, errors, missing_refs = [], [], []
    cache = {}
    folders = ("assets", "audio", "source_paths", "standalone_materials", "native_packages")
    paths = sorted(p for folder in folders for p in (LIBRARY / folder).rglob("*") if p.is_file())
    pool = ThreadPoolExecutor(max_workers=8)
    for i, (path, data, sha, byte_count) in enumerate(pool.map(read_asset, paths, buffersize=16)):
        relative = path.relative_to(LIBRARY).as_posix()
        row = dict(path=relative, bytes=byte_count, sha256=sha, extension=path.suffix)
        try:
            if sha not in cache:
                parser = {".png": check_png, ".wav": check_wav, ".cast": check_cast}.get(path.suffix)
                cache[sha] = parser(data) if parser else {}
                if path.suffix == ".json":
                    json.loads(data)
            row.update(cache[sha])
            for ref in row.get("texture_references", []):
                if not (path.parent / ref.replace("\\", "/")).is_file():
                    missing_refs.append(dict(file=relative, reference=ref))
        except (AssertionError, ValueError, KeyError, struct.error, UnicodeError) as exc:
            errors.append(dict(path=relative, error=str(exc)))
        records.append(row)
        if i % 2000 == 0:
            print(f"Checked {i}/{len(paths)}", flush=True)
    pool.shutdown()
    selected = json.loads((LIBRARY / "evidence/common_weapon_assets.json").read_text())
    wanted_models = [r for r in selected if r["type"] == "mdl_"]
    missing_models = [r["asset_name"] for r in wanted_models if not any(
        (LIBRARY / "assets/mdl" / Path(r["asset_name"].replace("\\", "/")).stem).glob("*LOD0.cast"))]
    wanted_rigs = [r for r in selected if r["type"] == "arig"]
    missing_rigs = [r["asset_name"] for r in wanted_rigs if not any(
        (LIBRARY / "assets/animrig" / Path(r["asset_name"].replace("\\", "/")).stem).glob("*.cast"))]
    audio = json.loads((LIBRARY / "evidence/audio_events.json").read_text())
    pngs = [r for r in records if r["extension"] == ".png"]
    wavs = [r for r in records if r["extension"] == ".wav"]
    casts = [r for r in records if r["extension"] == ".cast"]
    icons = json.loads((LIBRARY / "evidence/icon_names.json").read_text())
    sequences = [r for r in selected if r["type"] == "aseq"]
    missing_sequences = []
    for row in sequences:
        p = Path(row["asset_name"].replace("\\", "/"))
        matches = list((LIBRARY / "source_paths" / p.parent).glob(p.stem + "*.cast"))
        if not matches:
            missing_sequences.append(row["asset_name"])
    summary = dict(created=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        apex_build=(APEX / "build.txt").read_text().strip(),
        apex_version=(APEX / "gameversion.txt").read_text().strip(),
        total_files=len(records), total_bytes=sum(r["bytes"] for r in records),
        unique_payloads=len(cache), unique_bytes=sum({r["sha256"]: r["bytes"] for r in records}.values()),
        extensions=dict(collections.Counter(r["extension"] for r in records)),
        selected_models=len(wanted_models), missing_models=missing_models,
        selected_rigs=len(wanted_rigs), missing_rigs=missing_rigs,
        selected_sequences=len(sequences), missing_sequences=missing_sequences,
        cast_files=len(casts), animation_files=sum(bool(r.get("animations")) for r in casts),
        cast_files_with_texture_references=sum(bool(r.get("texture_references")) for r in casts),
        texture_files=len(pngs), unique_textures=len({r["sha256"] for r in pngs}),
        texture_dimensions=dict(collections.Counter(f"{r.get('width')}x{r.get('height')}" for r in pngs)),
        native_4k_paths=[r["path"] for r in pngs if max(r.get("width", 0), r.get("height", 0)) >= 4096],
        wav_files=len(wavs), unique_wavs=len({r["sha256"] for r in wavs}),
        audio_events=audio["selected_events"], event_sources=audio["source_count"],
        audio_missing=audio["missing_wavs"], audio_errors=audio["parse_errors"], unresolved_audio_calls=audio["unresolved_calls"],
        resolved_icon_names=sum(bool(r["assets"]) for r in icons),
        icon_assets=len({a["guid"] for r in icons for a in r["assets"]}),
        unresolved_icon_names=[r["name"] for r in icons if not r["assets"]],
        validation_errors=errors, missing_texture_references=missing_refs)
    write_json(LIBRARY / "evidence/files.json", records)
    material_files = []
    for row in casts:
        if not row.get("materials"):
            continue
        folder = Path(row["path"]).parent.as_posix() + "/"
        images = [p for p in pngs if p["path"].startswith(folder)]
        slots = []
        for material in row["materials"]:
            name = material["properties"].get("n", "")
            matches = {Path(p["path"]).stem[len(name) + 1:]: p["path"] for p in images
                       if name and Path(p["path"]).stem.rsplit("_", 1)[0].lower() == name.lower()}
            slots.append(dict(name=name, guid=material["guid"], candidate_maps=matches))
        material_files.append(dict(model=row["path"], materials=slots))
    write_json(LIBRARY / "evidence/material_texture_candidates.json", dict(
        method="Inferred from RSX's exported material names and neighboring texture filenames. Not native shader bindings. CAST files retain material names but this RSX build omits texture File nodes.",
        suffixes={"col": "color", "nml": "normal", "spc": "specular", "gls": "gloss", "ao": "ambient occlusion", "cav": "cavity", "ilm": "illumination", "msk": "mask", "ehl": "retain native channel data", "ehm": "retain native channel data"},
        models=material_files))
    write_json(LIBRARY / "evidence/summary.json", summary)
    # Small evidence stays in git; bulky originals and the complete catalog do not.
    write_json(REPO / "docs/apex_weapon_evidence/summary.json", summary)
    build_catalog(summary, records, icons)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("native_4k_paths", "unresolved_icon_names", "texture_dimensions")}, indent=2))
    if errors or missing_models or missing_rigs or missing_sequences or missing_refs or audio["missing_wavs"] or audio["parse_errors"]:
        raise SystemExit("Audit found gaps; inspect evidence/summary.json")


def build_catalog(summary, records, icons):
    names = {a["guid"].lower(): row["name"] for row in icons for a in row["assets"]}
    primary_hashes = {r["sha256"] for r in records if not r["path"].startswith("standalone_materials/")}
    standalone_seen = set()
    items = []
    for row in records:
        if row["path"].startswith("native_packages/"):
            continue
        if row["path"].startswith("standalone_materials/"):
            if row["sha256"] in primary_hashes or row["sha256"] in standalone_seen:
                continue
            standalone_seen.add(row["sha256"])
        if row["extension"] not in (".png", ".wav", ".cast", ".json", ".txt"):
            continue
        name = row["path"]
        for guid_value in re.findall(r"0x([0-9A-Fa-f]{16})", name):
            name = names.get(guid_value.lower(), name)
        info = (f"{row['width']} x {row['height']}" if "width" in row else
                f"{row['seconds']} s | {row['channels']} channels | {row['sample_rate']} Hz" if "seconds" in row else
                f"{row.get('vertices', 0)} vertices | {row.get('triangles', 0)} triangles" if row.get("vertices") else "")
        items.append(dict(path=row["path"], name=name, type=row["extension"][1:], info=info))
    payload = json.dumps(items).replace("<", "\\u003c")
    html = r'''<!doctype html><meta charset="utf-8"><title>Apex R-99 / Peacekeeper source library</title>
<style>body{font:16px system-ui;background:#10151b;color:#e6edf3;margin:32px;max-width:1300px}a{color:#70caff}input,select,button{font:inherit;padding:10px;background:#1b2530;color:inherit;border:1px solid #435365;border-radius:5px}input{width:50%}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #33404e;overflow-wrap:anywhere}small{color:#9aafc1}img{max-width:400px;max-height:330px;object-fit:contain;background:repeating-conic-gradient(#444 0% 25%,#555 0% 50%) 0/20px 20px}#preview{padding:14px;min-height:35px}p{line-height:1.55}button{cursor:pointer}</style>
<h1>R-99 &amp; Peacekeeper</h1><p>Original assets from the installed Apex build, collected 24 September 2026. Native resolutions; no upscaling or audio remixing. <a href="README.md">Scope and limitations</a> · <a href="evidence/summary.json">Validation</a> · <a href="evidence/files.json">SHA-256 manifest</a> · <a href="evidence/audio_events.json">Sound event mappings</a></p>
<p>COUNTS</p><p>Base weapon main textures: 2048 × 2048. R-99 Vampire Hunter includes native 4096 × 4096 maps. Original Apex particle/shader metadata is archived; it still needs conversion for BO3.</p>
<label>Find assets <input id="q" placeholder="r99_base, peacekeeper, reload, vampirehunter..."></label> <select id="type"><option value="">All types</option><option>png</option><option>wav</option><option>cast</option><option>txt</option><option>json</option></select>
<div id="preview">Choose Preview to inspect a texture or play a sound.</div><p id="count"></p><table><thead><tr><th>Asset</th><th>Details</th><th></th></tr></thead><tbody id="rows"></tbody></table><button id="more">Show more</button>
<script>const items=PAYLOAD;let limit=100;const q=document.querySelector('#q'),type=document.querySelector('#type'),rows=document.querySelector('#rows');function draw(){const words=q.value.toLowerCase().split(/\s+/).filter(Boolean),matches=items.filter(x=>(!type.value||x.type===type.value)&&words.every(w=>(x.name+' '+x.path).toLowerCase().includes(w)));rows.replaceChildren();document.querySelector('#count').textContent=matches.length+' matching files (showing '+Math.min(limit,matches.length)+')';for(const x of matches.slice(0,limit)){const tr=document.createElement('tr'),a=document.createElement('a'),td=document.createElement('td'),details=document.createElement('td'),actions=document.createElement('td');a.textContent=x.name;a.href=x.path;td.append(a);details.textContent=x.info;tr.append(td,details,actions);if(['png','wav'].includes(x.type)){const b=document.createElement('button');b.textContent='Preview';b.onclick=()=>{const p=document.querySelector('#preview');p.replaceChildren();const el=document.createElement(x.type==='png'?'img':'audio');el.src=x.path;if(x.type==='wav'){el.controls=true;el.play().catch(()=>{});}else el.alt=x.name;p.append(el);};actions.append(b);}rows.append(tr);}document.querySelector('#more').hidden=limit>=matches.length;}q.oninput=type.onchange=()=>{limit=100;draw();};document.querySelector('#more').onclick=()=>{limit+=100;draw();};draw();</script>'''
    html = html.replace("COUNTS", f"{summary['selected_models']} named model assets · {summary['cast_files']:,} CAST files · {summary['texture_files']:,} PNG files · {summary['wav_files']:,} WAV files · {summary['audio_events']} sound events")
    (LIBRARY / "index.html").write_text(html.replace("PAYLOAD", payload), encoding="utf-8")


if __name__ == "__main__":
    main()
