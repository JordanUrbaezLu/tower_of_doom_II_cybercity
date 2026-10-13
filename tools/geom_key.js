#!/usr/bin/env node
// geom_key.js - may a FULL build reuse the last full build's compiled map + lighting?
//
// WHY (user 2026-09-29: "Computer is freezing up while building"). The Radiant LED
// bake alone peaks at ~15.8 GB private memory on a 15.6 GB machine, so every full
// build pages the whole desktop out for ~8 minutes. Most full builds do not need
// it: a card-art or weapon GDT edit is a "full build" by the GDT rule, yet the map
// the bake lights has not changed at all. cod2map + the bake are pure functions
// of their inputs; when the inputs are byte-identical to the last full build, the
// compiled BSP / navmesh / LED on disk ARE the answer, and linking against them is
// exactly what -GscOnly has always done.
//
// THE RULE (docs/BO3_MAPMAKING_KB.md, "STALE LIGHTING BAKE"): the .led is indexed
// by surface, so linking a lighting bake against a BSP from a DIFFERENT .map draws
// every surface past the divergence black or not at all. Reuse is therefore
// refused unless ALL of these match the record written after the last full build:
//   * the deployed .map (byte hash) and every prefab .map it pulls in
//   * every GDT asset the .map names (brush/patch materials, sky model, ssi/wsi/fsi,
//     lut, prefab models), FOLLOWED TRANSITIVELY through every name and file path
//     inside those blocks (material -> image -> source PNG/TIF/EXR; skybox ->
//     material -> EXR). Block text and file bytes are hashed.
//   * the cod2map / Radiant command lines, the two exes, the navmesh settings files
//   * the compiled outputs themselves (BSP, portal file, metadata, navmesh,
//     navvolume, LED) are still the bytes that build wrote - a manual Radiant bake
//     or anything else touching them voids the record.
// Names that no GDT defines are stock assets compiled into the tools (clip, sky,
// caulk, lightmap_gray); they cannot change without the exes changing.
// Over-inclusion is deliberate: any string in the .map or a followed block that
// happens to name an asset is followed. The cost of a false match is one bake;
// the cost of a miss is a black map.
//
// KNOWN LIMIT: a model binary (.xmodel_bin) is LZ4-compressed, so material names
// inside it cannot be read; the model FILE is hashed, and when a .map-placed model
// is defined in a GDT the whole GDT file is followed. Today the only baked model
// is the stock power switch (no GDT).
//
// USAGE (build_map.ps1 calls it; nothing else needs to):
//   node tools/geom_key.js check --tools <root> --map <name> --args "<cod2map + radiant args>" [--write-pending]
//        exit 0 = reuse is valid, 3 = must compile + bake (reasons printed), 1 = error.
//        --write-pending (the FULL build only) also writes <map>.geomkey.pending.json for
//        `stamp` (the inputs cod2map saw); a plain check writes nothing.
//   node tools/geom_key.js stamp --tools <root> --map <name>
//        after a FRESH cod2map + LED: record the pending inputs + the output hashes.
//   node tools/geom_key.js clear --tools <root> --map <name>
//        before compiling: drop the record so a build dying mid-way cannot leave one.
//   node tools/geom_key.js show --tools <root> --map <name> --args "..."
//        read-only: print every input the key hashes (to see WHY a build re-bakes).
//   node tools/geom_key.js selftest
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const VERSION = 'geom-key-2';   // 2: permissive name scan, every path root, pending only on request
const OUT_EXTS = ['.d3dbsp', '.d3dprt', '_metadata.json', '_navmesh.hkt', '_navvolume.hkt', '.led'];

function sha1(buf) { return crypto.createHash('sha1').update(buf).digest('hex'); }
function fileHash(p) {
    try { return sha1(fs.readFileSync(p)); } catch (e) { return 'missing'; }
}
function exeId(p) {
    try { const s = fs.statSync(p); return 'size' + s.size + '@' + Math.round(s.mtimeMs); } catch (e) { return 'missing'; }
}

function parseArgs(argv) {
    const o = { cmd: argv[0], tools: '', map: '', args: '', note: '', writePending: false };
    for (let i = 1; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--tools') o.tools = argv[++i];
        else if (a === '--map') o.map = argv[++i];
        else if (a === '--args') o.args = argv[++i];
        else if (a === '--note') o.note = argv[++i];
        else if (a === '--write-pending') o.writePending = true;
        else throw new Error('unknown argument ' + a);
    }
    return o;
}

// ---- .map tokens --------------------------------------------------------------
// Every token (quoted or bare) that is not a number is a candidate asset name, and the
// GDT index decides. Deliberately permissive: a material name may carry '/', '#', '~'
// and so on, and a token that names nothing costs one failed lookup, never a miss.
const NUM_RE = /^[-+]?[0-9.]+(e[+-]?[0-9]+)?$/i;
function mapTokens(text, into) {
    const parts = text.split(/[\s"(){}\[\]]+/);
    for (const t of parts) {
        if (t.length < 2 || NUM_RE.test(t)) continue;
        into.add(t.toLowerCase());
    }
}
function prefabRefs(text) {
    const out = [];
    const re = /"([^"\r\n]+\.map)"/gi;
    let m;
    while ((m = re.exec(text))) out.push(m[1]);
    return out;
}

// ---- GDT index -----------------------------------------------------------------
function listGdts(dir, out) {
    let ents;
    try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return out; }
    for (const e of ents) {
        const p = path.join(dir, e.name);
        if (e.isDirectory()) listGdts(p, out);
        else if (e.name.toLowerCase().endsWith('.gdt')) out.push(p);
    }
    return out;
}
// header:  "name" ( "type.gdf" )   or derived:  "name" [ "parent" ]
const HDR_RE = /^[ \t]*"([^"\r\n]+)"[ \t]*(?:\([ \t]*"([^"\r\n]+)"[ \t]*\)|\[[ \t]*"([^"\r\n]+)"[ \t]*\])/gm;
function indexGdts(files) {
    const idx = new Map();   // lower name -> [{file, hdrStart, bodyFrom, gdf, parent}]
    for (const f of files) {
        let text;
        try { text = fs.readFileSync(f, 'latin1'); } catch (e) { continue; }
        HDR_RE.lastIndex = 0;
        let m;
        while ((m = HDR_RE.exec(text))) {
            const key = m[1].toLowerCase();
            let list = idx.get(key);
            if (!list) { list = []; idx.set(key, list); }
            list.push({ file: f, hdrStart: m.index, bodyFrom: HDR_RE.lastIndex, gdf: m[2] || '', parent: m[3] || '' });
        }
    }
    return idx;
}
function blockText(text, def) {
    const open = text.indexOf('{', def.bodyFrom);
    if (open < 0) return text.slice(def.hdrStart, def.bodyFrom);
    let depth = 0;
    for (let i = open; i < text.length; i++) {
        const c = text.charCodeAt(i);
        if (c === 123) depth++;
        else if (c === 125) { depth--; if (depth === 0) return text.slice(def.hdrStart, i + 1); }
    }
    return text.slice(def.hdrStart);
}
const PATH_EXT_RE = /\.[A-Za-z0-9_]{2,14}$/;
// GDT file paths are relative to different roots by field: images to the tools root
// ("model_export\\...\\x.png", "texture_assets\\..."), xmodel filenames to model_export,
// xanim filenames to xanim_export, effects to share/raw. EVERY root is tried and EVERY
// existing candidate is hashed - guessing one root could hash the wrong copy of a file
// and miss a change to the one the converter reads.
const PATH_ROOTS = ['', 'model_export', 'xanim_export', 'texture_assets', path.join('share', 'raw')];
function resolveAssetPaths(v, tools, gdtFile) {
    const clean = v.replace(/\\\\/g, '\\').trim();
    if (!/[\\/]/.test(clean) || !PATH_EXT_RE.test(clean)) return [];
    const tries = path.isAbsolute(clean) ? [clean]
        : PATH_ROOTS.map(r => path.join(tools, r, clean)).concat([path.join(path.dirname(gdtFile), clean)]);
    const found = [];
    for (const t of tries) {
        try { if (fs.statSync(t).isFile()) { const r = path.resolve(t); if (!found.includes(r)) found.push(r); } } catch (e) { /* next */ }
    }
    return found.length ? found : ['missing:' + clean.toLowerCase()];
}

// ---- the key -------------------------------------------------------------------
function computeParts(tools, map, args) {
    const t0 = Date.now();
    const parts = {};
    const zmRaw = path.join(tools, 'share', 'raw', 'maps', 'zm');
    const bin = path.join(tools, 'bin');
    parts['version'] = VERSION;
    parts['args'] = sha1(Buffer.from(args || '', 'utf8'));
    parts['exe:cod2map64'] = exeId(path.join(bin, 'cod2map64.exe'));
    parts['exe:radiant'] = exeId(path.join(bin, 'Radiant_modtools.exe'));
    parts['tool:default_navmesh_settings.json'] = fileHash(path.join(bin, 'default_navmesh_settings.json'));
    parts['tool:map_navmesh_settings.json'] = fileHash(path.join(zmRaw, map + '_navmesh_settings.json'));

    const mapFile = path.join(tools, 'map_source', 'zm', map + '.map');
    if (!fs.existsSync(mapFile)) throw new Error('no deployed map at ' + mapFile);
    const names = new Set();
    const seenMaps = new Set();
    const mapQueue = [mapFile];
    while (mapQueue.length) {
        const mf = mapQueue.shift();
        const key = path.resolve(mf).toLowerCase();
        if (seenMaps.has(key)) continue;
        seenMaps.add(key);
        let buf;
        try { buf = fs.readFileSync(mf); } catch (e) { parts['map:' + path.relative(tools, mf).toLowerCase()] = 'missing'; continue; }
        parts['map:' + path.relative(tools, mf).toLowerCase()] = sha1(buf);
        const text = buf.toString('latin1');
        mapTokens(text, names);
        for (const ref of prefabRefs(text)) {
            if (path.resolve(ref).toLowerCase() === key) continue;
            mapQueue.push(path.join(tools, 'map_source', ref.replace(/\//g, path.sep)));
        }
    }

    const gdts = listGdts(path.join(tools, 'source_data'), []);
    const idx = indexGdts(gdts);
    const tIndex = Date.now();

    const texts = new Map();
    const getText = (f) => { if (!texts.has(f)) texts.set(f, fs.readFileSync(f, 'latin1')); return texts.get(f); };
    const done = new Set();
    const wholeGdt = new Set();
    const files = new Set();
    let unresolved = 0;
    const queue = [];
    for (const n of names) { if (idx.has(n)) queue.push(n); else unresolved++; }
    const follow = (value, gdtFile) => {
        for (const tok of value.split(/[\s,]+/)) {
            if (!tok) continue;
            const low = tok.toLowerCase();
            if (idx.has(low) && !done.has(low)) queue.push(low);
        }
        for (const p of resolveAssetPaths(value, tools, gdtFile)) files.add(p);
    };
    while (queue.length) {
        const n = queue.shift();
        if (done.has(n)) continue;
        done.add(n);
        for (const def of idx.get(n)) {
            const text = getText(def.file);
            const body = blockText(text, def);
            parts['asset:' + n + '@' + path.relative(tools, def.file).toLowerCase()] = sha1(Buffer.from(body, 'latin1'));
            if (def.parent) follow(def.parent, def.file);
            // a model placed in the map carries its materials inside an LZ4 binary we
            // cannot read: follow its whole GDT file instead (see KNOWN LIMIT above)
            if (/xmodel\.gdf/i.test(def.gdf) && names.has(n)) wholeGdt.add(def.file);
            const kv = /"([^"\r\n]*)"[ \t]+"([^"]*)"/g;
            let m;
            while ((m = kv.exec(body))) follow(m[2], def.file);
        }
    }
    for (const f of wholeGdt) {
        parts['gdt:' + path.relative(tools, f).toLowerCase()] = fileHash(f);
        const text = getText(f);
        const kv = /"([^"\r\n]*)"[ \t]+"([^"]*)"/g;
        let m;
        while ((m = kv.exec(text))) { for (const p of resolveAssetPaths(m[2], tools, f)) files.add(p); }
    }
    let bytes = 0;
    for (const f of files) {
        if (f.startsWith('missing:')) { parts['file:' + f] = 'missing'; continue; }
        const h = fileHash(f);
        try { bytes += fs.statSync(f).size; } catch (e) { /* counted as missing */ }
        parts['file:' + path.relative(tools, f).toLowerCase()] = h;
    }
    const stats = {
        gdt_files: gdts.length, map_files: seenMaps.size, names: names.size, assets: done.size,
        whole_gdts: wholeGdt.size, files: files.size, file_mb: Math.round(bytes / 1e6), stock_or_other_names: unresolved,
        index_s: +((tIndex - t0) / 1000).toFixed(1), total_s: +((Date.now() - t0) / 1000).toFixed(1),
    };
    return { parts, stats };
}
function keyOf(parts) {
    const keys = Object.keys(parts).sort();
    return sha1(Buffer.from(keys.map(k => k + '=' + parts[k]).join('\n'), 'utf8'));
}
function outputHashes(tools, map) {
    const zmRaw = path.join(tools, 'share', 'raw', 'maps', 'zm');
    const o = {};
    for (const ext of OUT_EXTS) o[map + ext] = fileHash(path.join(zmRaw, map + ext));
    return o;
}
function recordPaths(tools, map) {
    const zmRaw = path.join(tools, 'share', 'raw', 'maps', 'zm');
    return { stamp: path.join(zmRaw, map + '.geomkey.json'), pending: path.join(zmRaw, map + '.geomkey.pending.json') };
}
function diffParts(a, b, limit) {
    const lines = [];
    const all = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const k of [...all].sort()) {
        if (a[k] === b[k]) continue;
        lines.push(!(k in a) ? '  added   ' + k : !(k in b) ? '  removed ' + k : '  changed ' + k);
    }
    const n = lines.length;
    return { n, lines: lines.slice(0, limit).concat(n > limit ? ['  ... and ' + (n - limit) + ' more'] : []) };
}

// ---- commands ------------------------------------------------------------------
function cmdCheck(o) {
    const rp = recordPaths(o.tools, o.map);
    // ONLY the FULL build's own check (--write-pending) touches the pending record: the
    // -GscOnly advisory check, or anyone running `check` by hand, must never replace the
    // inputs a running full build recorded before its cod2map and will stamp after its bake.
    // An older pending record must never be stamped for this build if computing fails.
    if (o.writePending) { try { fs.unlinkSync(rp.pending); } catch (e) { /* none */ } }
    const { parts, stats } = computeParts(o.tools, o.map, o.args);
    const key = keyOf(parts);
    if (o.writePending) fs.writeFileSync(rp.pending, JSON.stringify({ version: VERSION, map: o.map, key, parts, stats, computed_at: new Date().toISOString() }));
    console.log('[geom_key] inputs: ' + stats.map_files + ' map file(s), ' + stats.assets + ' GDT assets from ' + stats.gdt_files +
        ' GDTs, ' + stats.files + ' source files (' + stats.file_mb + ' MB) in ' + stats.total_s + ' s; key ' + key.slice(0, 12));
    let rec;
    try { rec = JSON.parse(fs.readFileSync(rp.stamp, 'utf8')); } catch (e) {
        console.log('[geom_key] REBUILD: no record of a completed full build (first run, or the last one did not finish)');
        return 3;
    }
    if (rec.version !== VERSION) { console.log('[geom_key] REBUILD: record is from ' + rec.version + ', tool is ' + VERSION); return 3; }
    if (rec.key !== key) {
        const d = diffParts(rec.parts || {}, parts, 15);
        console.log('[geom_key] REBUILD: ' + d.n + ' lighting/geometry input(s) changed since the full build recorded ' + rec.stamped_at + ':');
        for (const l of d.lines) console.log(l);
        return 3;
    }
    const now = outputHashes(o.tools, o.map);
    const bad = Object.keys(rec.outputs || {}).filter(k => rec.outputs[k] !== now[k]);
    if (bad.length) {
        console.log('[geom_key] REBUILD: compiled file(s) differ from what the full build recorded ' + rec.stamped_at + ' wrote: ' + bad.join(', '));
        return 3;
    }
    if (now[o.map + '.led'] === 'missing' || now[o.map + '.d3dbsp'] === 'missing') {
        console.log('[geom_key] REBUILD: compiled map or lighting is missing');
        return 3;
    }
    console.log('[geom_key] REUSE: map, materials, textures and sky are byte-identical to the full build recorded ' + rec.stamped_at + (rec.note ? ' (' + rec.note.split(';')[0] + ')' : '') +
        '; its BSP, navmesh and lighting are unchanged on disk');
    return 0;
}
function cmdStamp(o) {
    const rp = recordPaths(o.tools, o.map);
    let pend;
    try { pend = JSON.parse(fs.readFileSync(rp.pending, 'utf8')); } catch (e) {
        console.log('[geom_key] no pending input record (run check before compiling); nothing stamped');
        return 1;
    }
    const outputs = outputHashes(o.tools, o.map);
    const missing = Object.keys(outputs).filter(k => outputs[k] === 'missing' && !k.endsWith('_navvolume.hkt'));
    if (missing.length) { console.log('[geom_key] outputs missing, not stamping: ' + missing.join(', ')); return 1; }
    const rec = { version: VERSION, map: o.map, key: pend.key, parts: pend.parts, stats: pend.stats, outputs, stamped_at: new Date().toString() };
    if (o.note) rec.note = o.note;
    fs.writeFileSync(rp.stamp, JSON.stringify(rec));
    fs.unlinkSync(rp.pending);
    console.log('[geom_key] recorded this full build (key ' + pend.key.slice(0, 12) + '); the next full build with the same inputs skips cod2map + the bake');
    return 0;
}
function cmdClear(o) {
    const rp = recordPaths(o.tools, o.map);
    try { fs.unlinkSync(rp.stamp); console.log('[geom_key] cleared the previous full-build record'); } catch (e) { /* none */ }
    return 0;
}

// ---- selftest: a throwaway tools root, broken every way that must force a rebuild
function cmdSelftest() {
    const os = require('os');
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'geomkey-'));
    const w = (rel, s) => { const p = path.join(root, rel); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, s); return p; };
    const map = 'zm_t';
    w('bin/cod2map64.exe', 'x'); w('bin/Radiant_modtools.exe', 'y'); w('bin/default_navmesh_settings.json', '{}');
    const mapText = '{\n"classname" "worldspawn"\n"skyboxmodel" "sky_m"\n{\n ( 0 0 0 ) ( 1 0 0 ) ( 0 1 0 ) mat_floor 128 128 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0\n ( 0 0 0 ) ( 0 0 1 ) ( 0 1 0 ) mat_wall 128 128 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0\n ( 0 0 0 ) ( 1 0 1 ) ( 0 1 1 ) wc/mat_slash 128 128 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0\n}\n}\n{\n"classname" "misc_prefab"\n"model" "_prefabs/p.map"\n}\n{\n"classname" "misc_model"\n"model" "prop2_m"\n}\n';
    w('map_source/zm/' + map + '.map', mapText);
    w('map_source/_prefabs/p.map', '{\n"classname" "misc_model"\n"model" "prop_m"\n}\n');
    w('source_data/world.gdt', '{\n\t"mat_floor" ( "material.gdf" )\n\t{\n\t\t"colorMap" "i_floor"\n\t}\n\t"i_floor" ( "image.gdf" )\n\t{\n\t\t"baseImage" "tex\\\\floor.png"\n\t}\n\t"sky_m" ( "xmodel.gdf" )\n\t{\n\t\t"skinOverride" "a sky_mat"\n\t}\n\t"sky_mat" [ "sky_base" ]\n\t{\n\t}\n\t"sky_base" ( "material.gdf" )\n\t{\n\t\t"colorMap" "i_sky"\n\t}\n\t"i_sky" ( "image.gdf" )\n\t{\n\t\t"baseImage" "tex\\\\sky.exr"\n\t}\n}\n');
    w('source_data/props.gdt', '{\n\t"prop_m" ( "xmodel.gdf" )\n\t{\n\t\t"filename" "model\\\\prop.xmodel_bin"\n\t}\n\t"prop_mat" ( "material.gdf" )\n\t{\n\t\t"colorMap" "i_prop"\n\t}\n}\n');
    // a derived material in a GDT the map names no model from: only the [ "parent" ] link reaches the texture
    w('source_data/derived.gdt', '{\n\t"mat_wall" [ "wall_base" ]\n\t{\n\t}\n\t"wall_base" ( "material.gdf" )\n\t{\n\t\t"colorMap" "i_wall"\n\t}\n\t"i_wall" ( "image.gdf" )\n\t{\n\t\t"baseImage" "tex\\\\wall.png"\n\t}\n}\n');
    // a material name with a '/' (the name scan must not drop it)
    w('source_data/slash.gdt', '{\n\t"wc/mat_slash" ( "material.gdf" )\n\t{\n\t\t"colorMap" "i_slash"\n\t}\n\t"i_slash" ( "image.gdf" )\n\t{\n\t\t"baseImage" "tex\\\\slash.png"\n\t}\n}\n');
    // an xmodel whose filename is relative to model_export, not the tools root
    w('source_data/props2.gdt', '{\n\t"prop2_m" ( "xmodel.gdf" )\n\t{\n\t\t"filename" "props\\\\prop2.xmodel_bin"\n\t}\n}\n');
    w('source_data/ui.gdt', '{\n\t"i_card" ( "image.gdf" )\n\t{\n\t\t"baseImage" "ui\\\\card.png"\n\t}\n}\n');
    w('tex/floor.png', 'F1'); w('tex/wall.png', 'W1'); w('tex/slash.png', 'L1'); w('model_export/props/prop2.xmodel_bin', 'P1'); w('tex/sky.exr', 'S1'); w('model/prop.xmodel_bin', 'M1'); w('ui/card.png', 'C1');
    const outs = OUT_EXTS.map(e => w('share/raw/maps/zm/' + map + e, 'out' + e));
    const o = { tools: root, map, args: 'a b c' };
    const quiet = (fn) => { const log = console.log; console.log = () => {}; try { return fn(); } finally { console.log = log; } };
    // a FULL build: check --write-pending before cod2map, stamp after the bake
    const build = () => quiet(() => { cmdCheck(Object.assign({}, o, { writePending: true })); return cmdStamp(o); });
    const check = (args) => quiet(() => cmdCheck(Object.assign({}, o, args || {})));
    let fails = 0;
    const expect = (label, got, want) => { const ok = got === want; if (!ok) fails++; console.log((ok ? 'ok   ' : 'FAIL ') + label + ' (exit ' + got + ', want ' + want + ')'); };

    expect('no record -> rebuild', check(), 3);
    build();
    expect('unchanged -> reuse', check(), 0);
    w('ui/card.png', 'C2');
    expect('UI-only image edit -> still reuse', check(), 0);
    const cases = [
        ['map edit', () => w('map_source/zm/' + map + '.map', mapText + '// x\n')],
        ['prefab edit', () => w('map_source/_prefabs/p.map', '{\n"classname" "misc_model"\n"model" "prop_m"\n"angles" "0 90 0"\n}\n')],
        ['floor texture pixels', () => w('tex/floor.png', 'F2')],
        ['derived material -> parent -> texture pixels', () => w('tex/wall.png', 'W2')],
        ['sky EXR pixels (the map names the sky model)', () => w('tex/sky.exr', 'S2')],
        ['prop model binary', () => w('model/prop.xmodel_bin', 'M2')],
        ['material name with a slash -> its texture', () => w('tex/slash.png', 'L2')],
        ['model file relative to model_export', () => w('model_export/props/prop2.xmodel_bin', 'P2')],
        ['material block in the prop GDT (whole-GDT follow)', () => w('source_data/props.gdt', fs.readFileSync(path.join(root, 'source_data/props.gdt'), 'latin1').replace('i_prop', 'i_prop2'))],
        ['material tint', () => w('source_data/world.gdt', fs.readFileSync(path.join(root, 'source_data/world.gdt'), 'latin1').replace('"colorMap" "i_floor"', '"colorMap" "i_floor"\n\t\t"colorTint" "1 0 0 1"'))],
        ['LED touched after the bake', () => w('share/raw/maps/zm/' + map + '.led', 'manual bake')],
        ['BSP touched after the bake', () => w('share/raw/maps/zm/' + map + '.d3dbsp', 'other')],
        ['Radiant exe replaced', () => w('bin/Radiant_modtools.exe', 'y2')],
        ['navmesh settings', () => w('bin/default_navmesh_settings.json', '{"a":1}')],
    ];
    for (const [label, mutate] of cases) {
        for (const e of OUT_EXTS) w('share/raw/maps/zm/' + map + e, 'out' + e);
        build();
        if (check() !== 0) { fails++; console.log('FAIL baseline before: ' + label); continue; }
        mutate();
        expect(label + ' -> rebuild', check(), 3);
    }
    for (const e of OUT_EXTS) w('share/raw/maps/zm/' + map + e, 'out' + e);
    build();
    expect('different bake arguments -> rebuild', check({ args: 'a b +high' }), 3);
    // the pending record belongs to the running FULL build: a plain (-GscOnly or manual)
    // check in the middle of it - even after an input changed - must not replace it
    const pendingPath = recordPaths(root, map).pending;
    const pendKey = () => { try { return JSON.parse(fs.readFileSync(pendingPath, 'utf8')).key; } catch (e) { return 'none'; } };
    quiet(() => cmdCheck(Object.assign({}, o, { writePending: true })));
    const k1 = pendKey();
    w('tex/floor.png', 'F9');
    check();
    const kept = k1 !== 'none' && pendKey() === k1;
    if (!kept) fails++;
    console.log((kept ? 'ok   ' : 'FAIL ') + 'a plain check mid-build leaves the full build pending record alone');
    fs.unlinkSync(pendingPath);
    check();
    const none = !fs.existsSync(pendingPath);
    if (!none) fails++;
    console.log((none ? 'ok   ' : 'FAIL ') + 'a plain check writes no pending record');
    quiet(() => cmdClear(o));
    expect('cleared record -> rebuild', check(), 3);
    fs.rmSync(root, { recursive: true, force: true });
    console.log(fails ? 'geom_key selftest: ' + fails + ' FAILED' : 'geom_key selftest: all passed');
    return fails ? 1 : 0;
}

function main() {
    const argv = process.argv.slice(2);
    if (argv[0] === 'selftest') return cmdSelftest();
    const o = parseArgs(argv);
    if (!o.tools || !o.map) throw new Error('need --tools <root> --map <name>');
    if (o.cmd === 'check') return cmdCheck(o);
    if (o.cmd === 'show') { const r = computeParts(o.tools, o.map, o.args); console.log(JSON.stringify({ key: keyOf(r.parts), stats: r.stats, parts: r.parts }, null, 1)); return 0; }
    if (o.cmd === 'stamp') return cmdStamp(o);
    if (o.cmd === 'clear') return cmdClear(o);
    throw new Error('command must be check | show | stamp | clear | selftest');
}
try { process.exitCode = main(); } catch (e) { console.log('[geom_key] ERROR: ' + (e && e.stack || e)); process.exitCode = 1; }
