#!/usr/bin/env node
'use strict';
// =============================================================================
// tools/lint_tod_gdt.js - every repo GDT is a file gdtdb can parse, checked BEFORE the sync.
//
// WHY (2026-10-04): the Map One migration's FULL build died at `gdtdb /update` (the first native step after the
// sync) on `//` comment lines that two generators wrote INSIDE their GDTs' braces - gdtdb read the first as
// "Adding KVP to unnamed entity" and the rest as "Unknown token" and exited 1. Every gate had passed:
// run_build_gates.py never runs gdtdb, so "TREE SAFE" was said over a tree that killed every build on the root.
// An earlier build had already paid for the same rule at the file's FIRST line (memory npot-image-needs-nomipmaps).
// A GDT is the brace, the blocks, the brace - nothing else.
//
// THE GRAMMAR (read from the 500 stock GDTs in the tools install, which gdtdb accepts; zero hits there):
//   {
//       "name" ( "type.gdf" )      an asset              "name" [ "parent" ]   a derived asset
//       {
//           "key" "value"          zero or more pairs
//       }
//   }
// Tokens are the six brackets and double-quoted strings on one line; anything else outside a string (a // comment,
// a stray word) is an UNKNOWN TOKEN. Also refused: a string that runs off its line, a key with no value, a
// missing or extra brace, text after the closing brace, and one asset NAME + TYPE defined twice anywhere in the
// linted files (gdtdb refuses an asset in two GDTs - the Dealer's duplicate Keeper xanim stopped every build,
// 2026-10-01; memory gdt-duplicate-asset-across-gdts). The namespace is PER TYPE: a material and an xmodel may share
// a name (ours: zombie_blood, tod_archer_grapple_view; stock: 84 such pairs, e.g. a fog and an ssi both
// "mp_sector") and the 500 stock GDTs hold ZERO same-type repeats. A derived entry takes its parent's type.
//
// The planted-error fixtures below run on EVERY invocation first: a lint that cannot catch them fails the build
// rather than passing everything.
//
// Usage:  node tools/lint_tod_gdt.js                 every source_data/**/*.gdt in the repo (exit 1 on any hit)
//         node tools/lint_tod_gdt.js --dir <folder>  every *.gdt under another folder (read only; calibration)
//         node tools/lint_tod_gdt.js --selftest      the fixtures only
// =============================================================================
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');

// ---------------------------------------------------------------- the parser
function tokenize(text) {
    const toks = [];
    const errs = [];
    let line = 1;
    let i = 0;
    if (text.charCodeAt(0) === 0xfeff) i = 1;       // a UTF-8 BOM (read as one char) is tolerated
    const n = text.length;
    while (i < n) {
        const c = text[i];
        if (c === '\n') { line++; i++; continue; }
        if (c === ' ' || c === '\t' || c === '\r') { i++; continue; }
        if ('{}()[]'.includes(c)) { toks.push({ t: c, line }); i++; continue; }
        if (c === '"') {
            const j = text.indexOf('"', i + 1);
            const nl = text.indexOf('\n', i + 1);
            if (j < 0 || (nl >= 0 && nl < j)) {
                errs.push({ line, msg: 'a string runs off its line (no closing quote)' });
                i = nl < 0 ? n : nl;
                continue;
            }
            toks.push({ t: 'S', v: text.slice(i + 1, j), line });
            i = j + 1;
            continue;
        }
        // anything else is a token gdtdb does not know: report the whole rest of the line once
        let e = text.indexOf('\n', i);
        if (e < 0) e = n;
        const word = text.slice(i, e).replace(/\r$/, '').trim();
        errs.push({ line, msg: (word.startsWith('//') ? 'a // comment' : 'an unknown token') + ': ' + word.slice(0, 90) });
        i = e;
    }
    return { toks, errs };
}

function parse(text) {
    const { toks, errs } = tokenize(text);
    const assets = [];          // { name, line, type } or { name, line, parent } for a derived entry
    let k = 0;
    const peek = () => toks[k];
    const fail = (msg) => {
        const t = toks[k];
        errs.push({ line: t ? t.line : 'EOF', msg });
    };
    const want = (t, what) => {
        const x = toks[k];
        if (!x || x.t !== t) {
            fail('expected ' + what + (x ? ', found ' + (x.t === 'S' ? '"' + x.v.slice(0, 40) + '"' : x.t) : ', found the end of the file'));
            return null;
        }
        k++;
        return x;
    };
    if (errs.length) return { errs, assets };          // token errors first: the structure is unreliable after one
    if (!want('{', 'the opening { as the first thing in the file')) return { errs, assets };
    while (peek() && peek().t !== '}') {
        const nm = want('S', 'an asset name');
        if (!nm) return { errs, assets };
        const p = peek();
        const entry = { name: nm.v, line: nm.line };
        if (p && p.t === '(') {
            k++;
            const ty = want('S', 'the asset type ( "type.gdf" )');
            if (!ty) return { errs, assets };
            if (!/\.gdf$/i.test(ty.v)) { k--; fail('the asset type must name a .gdf: "' + ty.v + '"'); return { errs, assets }; }
            if (!want(')', ')')) return { errs, assets };
            entry.type = ty.v.toLowerCase();
        } else if (p && p.t === '[') {
            k++;
            const par = want('S', 'the parent asset name [ "parent" ]');
            if (!par) return { errs, assets };
            if (!want(']', ']')) return { errs, assets };
            entry.parent = par.v;
        } else {
            fail('expected ( "type.gdf" ) or [ "parent" ] after the asset name "' + nm.v + '"');
            return { errs, assets };
        }
        if (!want('{', 'the { that opens "' + nm.v + '"')) return { errs, assets };
        while (peek() && peek().t === 'S') {
            const key = toks[k++];
            const val = peek();
            if (!val || val.t !== 'S' || val.line !== key.line) {
                fail('the key "' + key.v + '" has no value on its line');
                return { errs, assets };
            }
            k++;
        }
        if (!want('}', 'the } that closes "' + nm.v + '"')) return { errs, assets };
        assets.push(entry);
    }
    if (!want('}', 'the closing } of the file')) return { errs, assets };
    if (k < toks.length) fail('text after the closing } of the file');
    return { errs, assets };
}

// ---------------------------------------------------------------- the planted errors (run every time)
const FIX_OK = [
    ['plain', '{\n\t"a" ( "image.gdf" )\n\t{\n\t\t"k" "v"\n\t}\n}\n'],
    ['crlf + derived + empty', '{\r\n\t"a" ( "xmodel.gdf" )\r\n\t{\r\n\t}\r\n\t"b" [ "a" ]\r\n\t{\r\n\t\t"k" ""\r\n\t}\r\n}\r\n'],
    ['mixed endings + paths', '{\r\n\t"a" ( "material.gdf" )\n\t{\n\t\t"colorMap" "model_export\\\\x\\\\y.tif"\r\n\t}\r\n}'],
    ['no assets', '{\n}\n'],
    ['one name, two types (a material + an xmodel, like zombie_blood)',
        '{\n\t"z" ( "material.gdf" )\n\t{\n\t}\n\t"z" ( "xmodel.gdf" )\n\t{\n\t}\n}\n'],
];
const FIX_BAD = [
    ['comment before the brace', '// note\n{\n}\n'],
    ['comment inside the braces (the 2026-10-04 build)', '{\n\t// ---- GENERATED ----\n\t"a" ( "image.gdf" )\n\t{\n\t}\n}\n'],
    ['comment after the last asset', '{\n\t"a" ( "image.gdf" )\n\t{\n\t}\n\t// ---- END GENERATED ----\n}\n'],
    ['comment inside an asset', '{\n\t"a" ( "image.gdf" )\n\t{\n\t\t// x\n\t\t"k" "v"\n\t}\n}\n'],
    ['missing closing brace', '{\n\t"a" ( "image.gdf" )\n\t{\n\t}\n'],
    ['text after the closing brace', '{\n}\n}\n'],
    ['key with no value', '{\n\t"a" ( "image.gdf" )\n\t{\n\t\t"k"\n\t\t"v" "w"\n\t}\n}\n'],
    ['string off its line', '{\n\t"a ( "image.gdf" )\n\t{\n\t}\n}\n'],
    ['type not a .gdf', '{\n\t"a" ( "image" )\n\t{\n\t}\n}\n'],
    ['stray word', '{\n\tasset\n}\n'],
];

const FIX_DUP = [
    // [label, files, must be caught]
    ['the same xanim in two GDTs (the Dealer, 2026-10-01)',
        [['x.gdt', '{\n\t"a" ( "xanim.gdf" )\n\t{\n\t}\n}\n'], ['y.gdt', '{\n\t"a" ( "xanim.gdf" )\n\t{\n\t}\n}\n']], true],
    ['the same image twice in one GDT',
        [['x.gdt', '{\n\t"a" ( "image.gdf" )\n\t{\n\t}\n\t"a" ( "image.gdf" )\n\t{\n\t}\n}\n']], true],
    ['a derived entry repeating its type under a used name',
        [['x.gdt', '{\n\t"p" ( "aitype.gdf" )\n\t{\n\t}\n\t"a" ( "aitype.gdf" )\n\t{\n\t}\n}\n'], ['y.gdt', '{\n\t"a" [ "p" ]\n\t{\n\t}\n}\n']], true],
    ['a fog and an ssi sharing a name (stock fog.gdt + ssi.gdt)',
        [['fog.gdt', '{\n\t"m" ( "fog.gdf" )\n\t{\n\t}\n}\n'], ['ssi.gdt', '{\n\t"m" ( "ssi.gdf" )\n\t{\n\t}\n}\n']], false],
];

function selftest() {
    const bad = [];
    for (const [nm, t] of FIX_OK) if (parse(t).errs.length) bad.push('a clean fixture was refused: ' + nm + ' (' + parse(t).errs[0].msg + ')');
    for (const [nm, t] of FIX_BAD) if (!parse(t).errs.length) bad.push('a planted error was NOT caught: ' + nm);
    for (const [nm, files, caught] of FIX_DUP) {
        const hit = lintTexts(files).some((h) => /defined twice/.test(h));
        if (hit !== caught) bad.push((caught ? 'a planted duplicate was NOT caught: ' : 'a legal same-name pair was refused: ') + nm);
    }
    return bad;
}

// ---------------------------------------------------------------- the files
function lintTexts(list) {
    const hits = [];
    const parsed = list.map(([file, text]) => [file, parse(text)]);
    // a derived entry's type = its parent's, resolved through every linted file (an unresolved parent is stock)
    const typeOf = new Map();
    for (const [, r] of parsed) for (const a of r.assets) if (a.type && !typeOf.has(a.name)) typeOf.set(a.name, a.type);
    const resolve = (a) => {
        let p = a.parent;
        for (let hop = 0; hop < 16; hop++) {
            const own = parsed.flatMap(([, r]) => r.assets).find((x) => x.name === p && x.type);
            if (own) return own.type;
            const der = parsed.flatMap(([, r]) => r.assets).find((x) => x.name === p && x.parent);
            if (!der) break;
            p = der.parent;
        }
        return '[' + a.parent + ']';
    };
    const seen = new Map();     // type + ' ' + name -> 'file:line'
    for (const [file, r] of parsed) {
        for (const e of r.errs) hits.push(file + ':' + e.line + '  ' + e.msg);
        for (const a of r.assets) {
            const type = a.type || resolve(a);
            const key = type + ' ' + a.name;
            const here = file + ':' + a.line;
            if (seen.has(key)) hits.push(here + '  ' + type + ' "' + a.name + '" defined twice (first at ' + seen.get(key) + ') - gdtdb refuses one asset in two places');
            else seen.set(key, here);
        }
    }
    return hits;
}

function gdtFiles(dir) {
    const out = [];
    const walk = (d) => {
        for (const e of fs.readdirSync(d, { withFileTypes: true })) {
            const p = path.join(d, e.name);
            if (e.isDirectory()) walk(p);
            else if (/\.gdt$/i.test(e.name)) out.push(p);
        }
    };
    walk(dir);
    return out.sort();
}

function main() {
    const argv = process.argv.slice(2);
    const st = selftest();
    if (st.length) {
        for (const s of st) console.log('GDT LINT SELFTEST FAILED: ' + s);
        process.exit(1);
    }
    if (argv[0] === '--selftest') {
        console.log('GDT LINT SELFTEST OK (' + FIX_BAD.length + ' planted syntax errors + ' + FIX_DUP.filter((d) => d[2]).length +
            ' planted duplicates caught; ' + FIX_OK.length + ' clean fixtures + ' + FIX_DUP.filter((d) => !d[2]).length + ' legal same-name pair clean)');
        return;
    }
    let root = path.join(REPO, 'source_data');
    if (argv[0] === '--dir') root = path.resolve(argv[1]);
    const files = gdtFiles(root);
    const list = files.map((f) => [path.relative(argv[0] === '--dir' ? root : REPO, f), fs.readFileSync(f, 'utf8')]);
    const hits = lintTexts(list);
    if (hits.length) {
        for (const h of hits.slice(0, 40)) console.log('  ' + h);
        if (hits.length > 40) console.log('  ... and ' + (hits.length - 40) + ' more');
        console.log('GDT LINT FAILED: ' + hits.length + ' problem(s) in ' + files.length + ' GDT(s) - gdtdb /update would refuse them. A GDT is the brace, the blocks, the brace: no // comments anywhere.');
        process.exit(1);
    }
    console.log('GDT LINT OK (' + files.length + ' GDTs, ' + list.reduce((s, [, t]) => s + parse(t).assets.length, 0) + ' assets; selftest ' + FIX_BAD.length + '/' + FIX_BAD.length + ' planted errors caught)');
}

if (require.main === module) main();
module.exports = { parse, lintTexts };
