"""THE PRECACHE TABLE, READ FROM THE LINKED .FF (LT-meteor, 2026-10-05). Post-link, read-only, advisory until wired.

  python tools/verify_bgcache.py                       the deployed usermap's .ff against its deployed scripts
  python tools/verify_bgcache.py --ff F --usermap D    another build
  python tools/verify_bgcache.py --dump out.tsv        also write every table entry (index, type id, name)
  python tools/verify_bgcache.py --selftest            decode, then prove a planted miss and a planted empty name fail

WHY. A server PlayFX / PlayFXOnTag / SetModel resolves its name through the map's precache table, the one `bgcache`
asset the linker writes into the .ff from every compiled script's `#precache` directives (plus every zone `xmodel,`
line). A name that is not in it fails at RUNTIME ("effect X was not precached") even though its zone line, the asset
ledger (zone_source/all/assetinfo) and every source gate are green. From 2026-09-29 to 10-05 that was the Lucky
Meteor: a `#precache( "string", "" )` stood first in _tod_lucky.gsc, the table came out with 109 server effects and
NONE of that file's four, and every meteor flew with no trail. Nothing upstream of the linker can see the table, so
this tool decodes it: the .ff is a TAff0000 stream of zlib blocks (8 MB-aligned, with zero-length padding blocks);
the table is a run of 132-byte records [u32 type][char name[128]] after a u32 count, sorted by type then name.

TYPE IDS (measured on the 2026-10-05 15:10 build): 2 model/xmodel, 4 aitype, 5 character, 6 xmodelalias, 7 weapon,
9 rumble, 18 material, 19 string, 21 eventstring, 22 triggerstring (args joined by 0x15), 24 fx (server), 25 lui_menu,
27 client_fx. xanim directives have no table type and are not checked.

CHECK. Every `#precache` in every script the zone compiles (scriptparsetree lines, then their #using closure inside
the usermap's scripts/) must be in the table under its type; an empty-name directive with any directive after it in
the same file is an error in itself (the linker flattens the file's arguments, drops the empty name, and every later
directive of that file is misread and lost - the table even holds a bogus string "model", the next directive's
type). An empty name that is its file's LAST directive loses nothing and is printed as a note (the vendored Logical
power-ups' hint strings, resolved through their #insert'ed .gsh). Exit 1 on any miss.
"""
import argparse, os, re, struct, sys, zlib

DEFAULT_USERMAP = r'C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity'
MAP = 'zm_tod2_cybercity'
TYPE = {'model': 2, 'xmodel': 2, 'aitype': 4, 'character': 5, 'xmodelalias': 6, 'weapon': 7, 'rumble': 9,
        'material': 18, 'string': 19, 'eventstring': 21, 'triggerstring': 22, 'fx': 24, 'lui_menu': 25,
        'client_fx': 27}
REC = 132


def decompress(ff_path):
    data = open(ff_path, 'rb').read()
    if data[:4] != b'TAff':
        raise SystemExit('not a T7 fastfile: ' + ff_path)
    out = bytearray()
    pos, blocks = 0x248, 0
    while pos + 16 <= len(data):
        csize, dsize, bsize, off = struct.unpack_from('<IIII', data, pos)
        if csize == 0 and dsize == 0:
            break
        if off != pos:
            raise SystemExit('block header out of step at 0x%x (offset field 0x%x)' % (pos, off))
        if dsize == 0:                       # padding to the next 8 MB boundary
            pos = (pos + 0x800000) & ~0x7fffff
            continue
        out += zlib.decompress(data[pos + 16: pos + 16 + csize])
        pos += 16 + bsize
        blocks += 1
    return bytes(out), blocks


def rec_ok(d, p):
    if p < 0 or p + REC > len(d):
        return False
    t = struct.unpack_from('<I', d, p)[0]
    name = d[p + 4: p + REC]
    z = name.find(b'\x00')
    if t > 64 or z <= 0 or any(name[z:]):
        return False
    return all(c >= 0x20 or c in (0x14, 0x15) for c in name[:z])


def find_table(d):
    for m in re.finditer(re.escape(b'\x02\x00\x00\x00tag_origin\x00'), d):
        p = m.start()
        if not (rec_ok(d, p) and rec_ok(d, p + REC)):
            continue
        start = p
        while rec_ok(d, start - REC):
            start -= REC
        count = struct.unpack_from('<I', d, start - 8)[0]
        if d[start - 16: start - 8] == b'\xff' * 8 and count >= (p - start) // REC + 2:
            ents = []
            for i in range(count):
                q = start + i * REC
                t = struct.unpack_from('<I', d, q)[0]
                ents.append((i, t, d[q + 4: q + REC].split(b'\x00')[0].decode('latin1')))
            return start, ents
    raise SystemExit('no precache table found in the decoded .ff (the record layout may have changed)')


USING = re.compile(r'^[ \t]*#using\s+([\w\\/]+)\s*;', re.M)
PRECACHE = re.compile(r'^[ \t]*#precache\(\s*"(\w+)"\s*,\s*(.*?)\)\s*;', re.M)
DEFINE = re.compile(r'^[ \t]*#define\s+(\w+)\s+"([^"]*)"', re.M)
ARG_SEP = '\x15'   # a multi-argument directive (triggerstring "ZOMBIE_PERK_X", "500") is stored joined by 0x15


def strip_comments(s):
    s = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)


def compiled_scripts(usermap):
    zone = open(os.path.join(usermap, 'zone_source', MAP + '.zone'), encoding='latin1').read()
    todo = [l.split(',', 1)[1].strip() for l in zone.splitlines() if l.startswith('scriptparsetree,')]
    seen = set()
    while todo:
        rel = todo.pop().replace('\\', '/')
        if rel in seen:
            continue
        p = os.path.join(usermap, rel)
        if not os.path.isfile(p):
            continue                         # a stock script: its precaches live in the base game's table
        seen.add(rel)
        ext = os.path.splitext(rel)[1]
        for u in USING.findall(strip_comments(open(p, encoding='latin1').read())):
            todo.append(u.replace('\\', '/') + ext)
    return sorted(seen)


INSERT = re.compile(r'^[ \t]*#insert\s+([\w\\/]+\.gsh)\s*;', re.M)


def directives(usermap, rel):
    src = strip_comments(open(os.path.join(usermap, rel), encoding='latin1').read())
    defs = {}
    # LT-fix: an #insert'ed .gsh under the usermap (the Logical power-ups keep their hint strings there); a stock
    # .gsh is not in the usermap and resolves nothing, as before
    for inc in INSERT.findall(src):
        g = os.path.join(usermap, inc.replace('\\', '/'))
        if os.path.isfile(g):
            defs.update(DEFINE.findall(strip_comments(open(g, encoding='latin1').read())))
    defs.update(DEFINE.findall(src))
    for m in PRECACHE.finditer(src):
        typ, args = m.group(1), m.group(2)
        line = src.count('\n', 0, m.start(1)) + 1
        names = re.findall(r'"([^"]*)"', args)
        if not names:
            tok = args.strip()
            if tok in defs:
                names = [defs[tok]]
            else:
                yield line, typ, None
                continue
        yield line, typ, ARG_SEP.join(names)


def audit(usermap, ents, plant=None):
    have = {}
    for _, t, n in ents:
        have.setdefault(t, set()).add(n.lower())
    if plant == 'drop_trail':
        have.get(24, set()).discard('tod/luck/fx_luck_meteor_trail')
    miss, empty, unresolved, unchecked, total = [], [], 0, 0, 0
    trailing = []
    for rel in compiled_scripts(usermap):
        dirs = list(directives(usermap, rel))
        if plant == 'empty' and rel.endswith('_tod_lucky.gsc'):
            dirs.insert(0, (64, 'string', ''))
        for k, (line, typ, name) in enumerate(dirs):
            total += 1
            if name is None:
                unresolved += 1
                continue
            if name == '':
                # LT-fix: the linker drops the empty name and misreads every LATER directive of the file; one that is
                # the file's last directive loses nothing (the vendored Logical power-ups' hint strings) - a note
                if k == len(dirs) - 1:
                    trailing.append('%s:%d #precache( "%s", <empty> )' % (rel, line, typ))
                else:
                    empty.append('%s:%d #precache( "%s", "" ) with %d directive(s) after it' % (rel, line, typ, len(dirs) - 1 - k))
                continue
            t = TYPE.get(typ)
            if t is None:
                unchecked += 1
                continue
            if name.lower() not in have.get(t, ()):
                miss.append('%s:%d %s %s' % (rel, line, typ, name.replace(ARG_SEP, ',')))
    audit.trailing = trailing
    return miss, empty, unresolved, unchecked, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--usermap', default=DEFAULT_USERMAP)
    ap.add_argument('--ff')
    ap.add_argument('--dump')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    ff = a.ff or os.path.join(a.usermap, 'zone', MAP + '.ff')
    d, blocks = decompress(ff)
    start, ents = find_table(d)
    counts = {}
    for _, t, _n in ents:
        counts[t] = counts.get(t, 0) + 1
    print('BGCACHE: %s - %d blocks, %d MB decoded, table at 0x%x: %d entries %s'
          % (ff, blocks, len(d) >> 20, start, len(ents), dict(sorted(counts.items()))))
    if a.dump:
        with open(a.dump, 'w', encoding='utf-8', newline='\n') as f:
            for i, t, n in ents:
                f.write('%d\t%d\t%s\n' % (i, t, n))
    if a.selftest:
        bad = 0
        for plant in ('drop_trail', 'empty'):
            m, e, _, _, _ = audit(a.usermap, ents, plant)
            caught = bool(m) if plant == 'drop_trail' else bool(e)
            print('  selftest %-10s %s' % (plant, 'caught' if caught else 'NOT CAUGHT'))
            bad += 0 if caught else 1
        sys.exit(1 if bad else 0)
    miss, empty, unresolved, unchecked, total = audit(a.usermap, ents)
    for x in getattr(audit, 'trailing', []):
        print('  note: trailing empty name (last directive of its file, nothing after it to lose)  ' + x)
    for x in empty:
        print('  EMPTY NAME  ' + x + '  (the linker drops it - and this file\'s precaches after it)')
    for x in miss:
        print('  NOT IN THE TABLE  ' + x)
    print(('BGCACHE FAIL: %d missing, %d empty' % (len(miss), len(empty)) if (miss or empty) else 'BGCACHE OK')
          + ' - %d directives, %d via unresolved #define, %d of unchecked types (xanim)' % (total, unresolved, unchecked))
    sys.exit(1 if (miss or empty) else 0)


if __name__ == '__main__':
    main()
