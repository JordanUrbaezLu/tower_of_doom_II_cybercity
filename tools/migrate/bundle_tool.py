"""Machine-migration helper for TOWER II (2026-10-12, docs/220). Stdlib only, Python 3.10+.

Adapted from Map One's tools/migrate/bundle_tool.py (docs/174 there), which moved the SHARED Steam
Mod Tools root by diffing it against Steam's depot manifest. Tower II never writes that root (CLAUDE.md
hard rule 1): it builds in its own PRIVATE root, C:\\BO3Tools\\TOD2Cybercity, made once by
tools/setup_tod2_workspace.ps1 as a physical copy of the 2026-09-22 Steam root plus 123 junctions
into its read-only model/texture libraries. Re-running setup on a new machine would copy TODAY's
Steam root, which is not the root Tower II has been building in since. So this tool moves the private
root itself:

  every PHYSICAL file (stock copies included: tod2_workspace.ps1 refuses a root without its private
  stock shader binaries and sw4 textures) - sha1 of each in root_manifest.json;
  every junction as (path, target) - recreated on the new machine, never followed or copied;
  every directory, so empty ones (zone\\, temp_assets\\, usermaps\\...\\snd) come back too.

  root-export  --dest <bundle>/tod2_root [--dry-run] [--skip-build-output]
               Resumable: re-running skips finished files.
  root-import  --src <bundle>/tod2_root [--root C:\\BO3Tools\\TOD2Cybercity] [--force]
               copy every file in (sha1 checked on the way; a mismatch is refused), recreate the
               directories and junctions. Never replaces a file that is newer here unless --force.
  root-verify  --manifest <root_manifest.json> [--quick]
               re-check a root against the manifest (size, sha1 unless --quick, junction targets).
  copylist     --src <root> --dest <dir> --list <file> | --git-untracked
               copy a NUL/newline list of relative paths (git ls-files --others -z).
  du <path>... sizes, for dry runs.

Left out on purpose (they regenerate on the first build): share/assetconvert EXCEPT its shaders,
ToolsGfx and preshader folders (the converter cannot rebuild those - setup_tod2_workspace.ps1), and
bin/crash_reports.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

MAP = 'zm_tod2_cybercity'
DEFAULT_ROOT = r'C:\BO3Tools\TOD2Cybercity'
# lowercase, '/'-separated, trailing '/'. KEEP_UNDER wins over EXCLUDE_DIRS.
EXCLUDE_DIRS = ('share/assetconvert/', 'bin/crash_reports/')
KEEP_UNDER = ('share/assetconvert/shaders/', 'share/assetconvert/toolsgfx/', 'share/assetconvert/preshader/')
BUILD_OUTPUT = 'usermaps/%s/' % MAP
CHUNK = 1 << 20


def lp(p):
    """Long-path-safe absolute path (\\\\?\\ prefix on Windows): tool trees exceed 260 chars."""
    p = os.path.abspath(p)
    if os.name == 'nt' and not p.startswith('\\\\?\\'):
        if p.startswith('\\\\'):
            return '\\\\?\\UNC\\' + p[2:]
        return '\\\\?\\' + p
    return p


def gb(n):
    return '%.2f GB' % (n / 1e9)


def fold(path):
    """Windows file names are case-insensitive: compare paths case-folded there."""
    return path.lower() if os.name == 'nt' else path


def sha1_file(path):
    h = hashlib.sha1()
    with open(lp(path), 'rb') as f:
        for chunk in iter(lambda: f.read(CHUNK), b''):
            h.update(chunk)
    return h.hexdigest()


def is_link(p):
    """Junction or symlink: never followed (os.walk follows junctions on Windows)."""
    return os.path.islink(p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(p))


def link_target(p):
    t = os.readlink(lp(p))
    if t.startswith('\\\\?\\UNC\\'):
        t = '\\\\' + t[8:]
    elif t.startswith('\\\\?\\') or t.startswith('\\??\\'):
        t = t[4:]
    return t


# ------------------------------------------------------------------ selection rules
def keep_dir(reldir, skip_build_output=False):
    """reldir: lowercase, '/'-separated, trailing '/', '' for the root."""
    if any(reldir.startswith(k) or k.startswith(reldir) for k in KEEP_UNDER):
        return True
    if any(reldir.startswith(e) for e in EXCLUDE_DIRS):
        return False
    if skip_build_output and reldir.startswith(BUILD_OUTPUT):
        return False
    return True


def keep_file(rel_low, skip_build_output=False):
    d = rel_low.rsplit('/', 1)[0] + '/' if '/' in rel_low else ''
    if d and not keep_dir(d, skip_build_output):
        return False
    if d == 'share/assetconvert/':
        return False      # loose cache files in share/assetconvert itself (datasignature.db ...); walked only for KEEP_UNDER
    return True


def classify_root(root, skip_build_output=False, log=print):
    """Return (sel, dirs, links, errors). sel = [(rel, size, mtime)] for every physical file kept;
    dirs = every kept directory (rel, '/'-separated); links = [(rel, target)] for every junction or
    symlink met (never followed); errors = unreadable paths (the export FAILS on any - a silent skip
    is a missed file)."""
    t0 = time.time()
    base = lp(root)
    sel, dirs, links, errors = [], [], [], []
    onerr = lambda e: errors.append('%s: %s' % (e.filename, e.strerror))
    for dp, dns, fns in os.walk(base, onerror=onerr):
        reldir = os.path.relpath(dp, base).replace(chr(92), '/')
        reldir = '' if reldir == '.' else reldir + '/'
        keep = []
        for d in dns:
            rd = reldir + d + '/'
            full = os.path.join(dp, d)
            if is_link(full):
                if keep_dir(rd.lower(), skip_build_output):
                    try:
                        links.append((rd.rstrip('/'), link_target(full)))
                    except OSError as e:
                        errors.append('%s: %s' % (rd, e.strerror))
                continue
            if not keep_dir(rd.lower(), skip_build_output):
                continue
            keep.append(d)
            dirs.append(rd.rstrip('/'))
        dns[:] = keep
        for fn in fns:
            rel = reldir + fn
            if not keep_file(rel.lower(), skip_build_output):
                continue
            full = os.path.join(dp, fn)
            if is_link(full):
                try:
                    links.append((rel, link_target(full)))
                except OSError as e:
                    errors.append('%s: %s' % (rel, e.strerror))
                continue
            try:
                st = os.stat(full)
            except OSError as e:
                errors.append('%s: %s' % (rel, e.strerror))
                continue
            sel.append((rel, st.st_size, st.st_mtime))
    log('scanned %s in %.0fs: %d files (%s), %d folders, %d junctions (not followed)'
        % (root, time.time() - t0, len(sel), gb(sum(s for _, s, _ in sel)), len(dirs), len(links)))
    return sorted(sel), sorted(dirs), sorted(links), errors


def summary(sel, depth=2, limit=30):
    g = collections.defaultdict(lambda: [0, 0])
    for rel, size, _ in sel:
        p = rel.split('/')
        k = '/'.join(p[:depth]) if len(p) > depth else '/'.join(p[:-1]) or '(root)'
        g[k][0] += 1
        g[k][1] += size
    for k, (n, s) in sorted(g.items(), key=lambda x: -x[1][1])[:limit]:
        print('  %10s %7d files  %s' % (gb(s), n, k))
    if len(g) > limit:
        rest = sorted(g.items(), key=lambda x: -x[1][1])[limit:]
        print('  %10s %7d files  (%d more folders)' % (gb(sum(v[1] for _, v in rest)),
                                                     sum(v[0] for _, v in rest), len(rest)))


def tree_sizes(root):
    """{'a/b/c.ext': (size, mtime)} for every file under root, from ONE directory listing per folder.
    On a network share a per-file isfile+getsize is two round trips each (Map One, 2026-10-08: the
    resume check of 16.5k files stalled ~25 min over Wi-Fi). DirEntry.stat() reuses the listing."""
    out = {}
    base = lp(root)
    stack = ['']
    while stack:
        rel = stack.pop()
        here = os.path.join(base, rel.replace('/', chr(92))) if rel else base
        try:
            with os.scandir(here) as it:
                for e in it:
                    r = rel + '/' + e.name if rel else e.name
                    if e.is_dir(follow_symlinks=False):
                        stack.append(r)
                    else:
                        st = e.stat(follow_symlinks=False)
                        out[fold(r)] = (st.st_size, st.st_mtime)
        except FileNotFoundError:
            pass
    return out


def copy_direct(src, dst):
    """Export-side copy: straight to the final name, hashing on the way. Over SMB every extra step is
    more round trips per file; an interrupted file has no progress record (so the resume recopies it),
    the import re-hashes every file against the manifest and sets the real mtime."""
    os.makedirs(lp(os.path.dirname(dst)), exist_ok=True)
    h = hashlib.sha1()
    with open(lp(src), 'rb') as fi, open(lp(dst), 'wb') as fo:
        for chunk in iter(lambda: fi.read(CHUNK), b''):
            h.update(chunk)
            fo.write(chunk)
    return h.hexdigest()


def copy_hash(src, dst, mtime, expect=None):
    """Copy src -> dst through a .part file, hashing on the way. With `expect`, a mismatch deletes the
    .part and leaves dst untouched. Returns the sha1 hex of what was read."""
    os.makedirs(lp(os.path.dirname(dst)), exist_ok=True)
    part = dst + '.part'
    h = hashlib.sha1()
    with open(lp(src), 'rb') as fi, open(lp(part), 'wb') as fo:
        for chunk in iter(lambda: fi.read(CHUNK), b''):
            h.update(chunk)
            fo.write(chunk)
    sha = h.hexdigest()
    if expect is not None and sha != expect:
        os.remove(lp(part))
        return sha
    os.replace(lp(part), lp(dst))
    os.utime(lp(dst), (mtime, mtime))
    return sha


class Progress:
    def __init__(self, total_files, total_bytes, label):
        self.n = self.b = 0
        self.tf, self.tb, self.label = total_files, total_bytes, label
        self.t0 = self.last = time.time()

    def step(self, size):
        self.n += 1
        self.b += size
        now = time.time()
        if now - self.last > 15 or self.n == self.tf:
            self.last = now
            rate = self.b / max(now - self.t0, 0.001) / 1e6
            print('  %s: %d/%d files, %s/%s (%.0f MB/s)' % (self.label, self.n, self.tf, gb(self.b),
                                                          gb(self.tb), rate), flush=True)


# ------------------------------------------------------------------ subcommands
def root_export(a):
    root = a.root
    if not os.path.isfile(os.path.join(root, '.tod2-workspace.json')):
        print('ROOT EXPORT FAIL: %s has no .tod2-workspace.json - not the Tower II private root' % root)
        return 1
    sel, dirs, links, errors = classify_root(root, a.skip_build_output)
    total = sum(r[1] for r in sel)
    print('private root: %d files, %s' % (len(sel), gb(total)))
    summary(sel)
    print('BYTES=%d FILES=%d' % (total, len(sel)))
    if errors:
        print('ROOT EXPORT FAIL: %d path(s) could not be read - close BO3 / the mod tools / any build and re-run:' % len(errors))
        for e in errors[:25]:
            print('   ', e)
        return 1
    if a.dry_run:
        for rel, tgt in links[:5]:
            print('  junction: %s -> %s' % (rel, tgt))
        if len(links) > 5:
            print('  ... %d more junctions' % (len(links) - 5))
        return 0
    os.makedirs(lp(a.dest), exist_ok=True)
    # The progress record lives on THIS machine's disk (Map One 2026-10-08: written to the share, 32
    # copy workers outran the one recorder and a Wi-Fi drop lost the backlog), keyed by an id stored IN
    # the bundle, so a wiped bundle can never be "resumed" from a stale local record.
    tok_path = os.path.join(a.dest, 'bundle_id.txt')
    if os.path.isfile(lp(tok_path)):
        key = open(lp(tok_path), encoding='utf-8').read().strip()
    else:
        import uuid
        key = uuid.uuid4().hex[:16]
        open(lp(tok_path), 'w', encoding='utf-8').write(key)
    local_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'tod2_migrate')
    os.makedirs(local_dir, exist_ok=True)
    prog_path = os.path.join(local_dir, key + '_root_progress.jsonl')
    legacy = os.path.join(a.dest, 'root_progress.jsonl')
    done = {}
    for path in (legacy, prog_path):
        if os.path.isfile(lp(path)):
            for line in open(lp(path), encoding='utf-8'):
                try:
                    r = json.loads(line)
                    done[r['p']] = r
                except ValueError:
                    pass
    print('  progress record: %s (%d files recorded)' % (prog_path, len(done)))
    finished, todo = {}, []
    pr = Progress(len(sel), total, 'export')
    for rel, size, mtime in sel:
        r = done.get(rel)
        if r and r['size'] == size and abs(r['mtime'] - mtime) < 2:
            finished[rel] = r
            pr.step(size)
        else:
            todo.append((rel, size, mtime))
    if finished:
        print('  resuming: %d files already in the bundle, %d to copy' % (len(finished), len(todo)))

    def work(item):
        rel, size, mtime = item
        sha = copy_direct(os.path.join(root, rel), os.path.join(a.dest, 'files', rel))
        return {'p': rel, 'size': size, 'mtime': mtime, 'sha1': sha}

    with open(prog_path, 'a', encoding='utf-8') as prog:
        ex = ThreadPoolExecutor(max_workers=max(1, a.workers))
        try:
            for fut in as_completed([ex.submit(work, it) for it in todo]):
                r = fut.result()
                prog.write(json.dumps(r) + '\n')
                prog.flush()
                finished[r['p']] = r
                pr.step(r['size'])
        except BaseException:
            ex.shutdown(wait=True, cancel_futures=True)
            raise
        ex.shutdown(wait=True)
    records = [finished[rel] for rel, _, _ in sel]
    # Final safety net (Map One 2026-10-09): a run stopped mid-copy truncates the file it was rewriting;
    # if that file's earlier record survives, a resume trusts it. List the bundle once and re-copy any
    # file whose size disagrees with its record. Up to 3 passes, then fail loudly.
    for attempt in range(3):
        on_disk = tree_sizes(os.path.join(a.dest, 'files'))
        short = [r for r in records if (on_disk.get(fold(r['p'])) or (None,))[0] != r['size']]
        if not short:
            print('  size check: all %d files in the bundle match their records' % len(records))
            break
        print('  size check: %d file(s) short or missing - re-copying (pass %d)' % (len(short), attempt + 1))
        for r in short:
            copy_hash(os.path.join(root, r['p']), os.path.join(a.dest, 'files', r['p']), r['mtime'], expect=r['sha1'])
    else:
        print('ROOT EXPORT FAIL: files still short after 3 passes: %s' % ', '.join(r['p'] for r in short[:10]))
        return 1
    out = {'created': datetime.datetime.now().isoformat(timespec='seconds'),
           'source_root': root, 'map': MAP, 'skip_build_output': a.skip_build_output,
           'excluded_dirs': [d for d in EXCLUDE_DIRS] + (['%s (build output)' % BUILD_OUTPUT] if a.skip_build_output else []),
           'kept_under_excluded': list(KEEP_UNDER),
           'dirs': dirs, 'links': [{'p': p, 'target': t} for p, t in links],
           'file_count': len(records), 'total_bytes': sum(r['size'] for r in records), 'files': records}
    with open(lp(os.path.join(a.dest, 'root_manifest.json')), 'w', encoding='utf-8') as f:
        json.dump(out, f)
    for path in (prog_path, legacy):
        tmp = path + '.new'
        with open(lp(tmp), 'w', encoding='utf-8') as f:
            for r in records:
                f.write(json.dumps(r) + '\n')
        os.replace(lp(tmp), lp(path))
    print('ROOT EXPORT OK: %d files, %s, %d folders, %d junctions -> %s'
          % (len(records), gb(out['total_bytes']), len(dirs), len(links), a.dest))
    return 0


def make_junction(link, target):
    """Create a directory junction (what setup_tod2_workspace.ps1 makes with New-Item -ItemType Junction)."""
    import _winapi
    _winapi.CreateJunction(target, link)


def root_import(a):
    man = json.load(open(lp(os.path.join(a.src, 'root_manifest.json')), encoding='utf-8'))
    root = a.root
    os.makedirs(lp(root), exist_ok=True)
    files = man['files']
    present = copied = 0
    bad, missing, newer = [], [], []
    pr = Progress(len(files), man['total_bytes'], 'import')
    for r in files:
        src = os.path.join(a.src, 'files', r['p'])
        dst = os.path.join(root, r['p'])
        if os.path.isfile(lp(dst)):
            st = os.stat(lp(dst))
            if st.st_size == r['size'] and abs(st.st_mtime - r['mtime']) < 2:
                present += 1
                pr.step(r['size'])
                continue
            if st.st_size == r['size'] and sha1_file(dst) == r['sha1']:
                os.utime(lp(dst), (r['mtime'], r['mtime']))   # same bytes, only the date differs
                present += 1
                pr.step(r['size'])
                continue
            if st.st_mtime > r['mtime'] + 2 and not a.force:
                newer.append(r['p'])            # changed on this machine (a build, a sync, an edit)
                pr.step(r['size'])
                continue
        if not os.path.isfile(lp(src)):
            missing.append(r['p'])
        elif copy_hash(src, dst, r['mtime'], expect=r['sha1']) != r['sha1']:
            bad.append(r['p'])
        else:
            copied += 1
        pr.step(r['size'])
    for d in man.get('dirs', []):
        os.makedirs(lp(os.path.join(root, d)), exist_ok=True)
    made = had = 0
    link_probs = []
    for l in man.get('links', []):
        p, tgt = os.path.join(root, l['p']), l['target']
        if is_link(p):
            cur = link_target(p)
            if fold(cur.rstrip('\\/')) == fold(tgt.rstrip('\\/')):
                had += 1
            else:
                link_probs.append('%s points at %s, expected %s (left alone)' % (l['p'], cur, tgt))
            continue
        if os.path.exists(lp(p)):
            link_probs.append('%s exists as a real folder/file, expected a junction to %s (left alone)' % (l['p'], tgt))
            continue
        if not os.path.isdir(tgt):
            link_probs.append('%s: junction target missing on this machine: %s' % (l['p'], tgt))
            continue
        os.makedirs(lp(os.path.dirname(p)), exist_ok=True)
        make_junction(p, tgt)
        made += 1
    print('root import: %d copied, %d already present, %d kept (newer on this machine), %d missing from bundle, %d failed sha1'
          % (copied, present, len(newer), len(missing), len(bad)))
    print('junctions: %d created, %d already right, %d problem(s); %d folders ensured'
          % (made, had, len(link_probs), len(man.get('dirs', []))))
    if newer:
        print('   kept because the local copy is newer than the bundle (use --force to take the bundle copy):')
        for p in newer[:10]:
            print('     ', p)
    for p in (missing + bad)[:25]:
        print('   PROBLEM:', p)
    for p in link_probs[:25]:
        print('   JUNCTION PROBLEM:', p)
    if missing or bad or link_probs:
        print('ROOT IMPORT INCOMPLETE - fix the problems above (re-copy the bundle from the old laptop / restore the Mod Tools folders) and run again')
        return 1
    print('ROOT IMPORT OK -> %s' % root)
    return 0


def root_verify(a):
    man = json.load(open(lp(a.manifest), encoding='utf-8'))
    root = a.root
    # the build output (usermaps/<map>) and the GDT database are rewritten by every build/sync: only
    # their presence matters after the first build here
    volatile = (BUILD_OUTPUT, 'gdtdb/')
    probs = collections.defaultdict(list)
    changed = []
    files = man['files']
    pr = Progress(len(files), sum(r['size'] for r in files), 'verify')
    for r in files:
        dst = os.path.join(root, r['p'])
        pr.step(r['size'])
        low = r['p'].lower()
        if not os.path.isfile(lp(dst)):
            if not low.startswith(volatile):
                probs['missing'].append(r['p'])
            continue
        st = os.stat(lp(dst))
        differs = st.st_size != r['size'] or (not a.quick and sha1_file(dst) != r['sha1'])
        if not differs:
            continue
        if st.st_mtime > r['mtime'] + 2 or low.startswith(volatile):
            changed.append(r['p'])          # edited / rebuilt here after the import: fine
        else:
            probs['size' if st.st_size != r['size'] else 'sha1'].append(r['p'])
    for l in man.get('links', []):
        p = os.path.join(root, l['p'])
        if not is_link(p):
            probs['junction missing'].append(l['p'])
        elif fold(link_target(p).rstrip('\\/')) != fold(l['target'].rstrip('\\/')):
            probs['junction points elsewhere'].append(l['p'])
        elif not os.path.isdir(lp(p)):
            probs['junction target missing'].append('%s -> %s' % (l['p'], l['target']))
    note = ''
    if changed:
        note = ' (%d changed on this machine since the import - normal after builds or edits)' % len(changed)
    if not probs:
        print('ROOT VERIFY OK: %d files present%s, %d junctions resolve, in %s%s'
              % (len(files), '' if a.quick else ' and sha1-identical', len(man.get('links', [])), root, note))
        return 0
    for k, v in probs.items():
        print('ROOT VERIFY FAIL: %d %s' % (len(v), k if k.startswith('junction') or k == 'missing' else 'differ from the bundle (' + k + ')'))
        for p in v[:15]:
            print('   ', p)
    if note:
        print('   ' + note.strip())
    return 1


def copylist(a):
    if a.git_untracked:
        # every path git does not track (ignored or not); --directory folds a wholly-untracked folder
        # (tmp/, source_library/) into one entry. Read as bytes: -z paths are raw UTF-8, unquoted.
        import subprocess
        raw = subprocess.run(['git', '-C', a.src, 'ls-files', '--others', '--directory', '-z'],
                             check=True, capture_output=True).stdout.decode('utf-8')
        if a.save_list:
            os.makedirs(lp(os.path.dirname(os.path.abspath(a.save_list))), exist_ok=True)
            open(a.save_list, 'w', encoding='utf-8').write(raw.replace('\0', '\n'))
    else:
        raw = open(a.list, 'rb').read().decode('utf-8')
    items = [x.rstrip('\r') for x in re.split('[\0\n]', raw) if x.strip()]
    n = b = skipped = kept = 0
    errors, links, absent, jobs = [], [], [], []
    onerr = lambda e: errors.append('%s: %s' % (e.filename, e.strerror))
    existing = {} if a.dry_run else tree_sizes(a.dest)
    for rel in items:
        src = os.path.join(a.src, rel)
        srcs = []
        if is_link(src.rstrip('/\\')):
            links.append(rel)
        elif os.path.isdir(lp(src)):
            for dp, dns, fns in os.walk(lp(src), onerror=onerr):
                for d in list(dns):
                    if is_link(os.path.join(dp, d)):
                        links.append(os.path.relpath(os.path.join(dp, d), lp(a.src)))
                        dns.remove(d)
                for fn in fns:
                    full = os.path.join(dp, fn)
                    srcs.append(os.path.relpath(full, lp(a.src)))
        elif os.path.isfile(lp(src)):
            srcs.append(rel.rstrip('/'))
        else:
            absent.append(rel)
        for r in srcs:
            s, d = os.path.join(a.src, r), os.path.join(a.dest, r)
            try:
                st = os.stat(lp(s))
            except OSError as e:
                errors.append('%s: %s' % (r, e.strerror))
                continue
            if a.dry_run:
                n += 1
                b += st.st_size
                continue
            cur = existing.get(fold(r.replace(chr(92), '/')))
            if cur is not None:
                if a.no_overwrite:
                    kept += 1          # import: a file the clone (or the user) already has wins
                    continue
                if cur[0] == st.st_size and abs(cur[1] - st.st_mtime) < 2:
                    skipped += 1
                    continue
            jobs.append((r, s, d, st.st_size))
    lock = threading.Lock()

    def one(job):
        r, s, d, size = job
        try:
            os.makedirs(lp(os.path.dirname(d)), exist_ok=True)
            shutil.copy2(lp(s), lp(d))
            return size
        except OSError as e:
            with lock:
                errors.append('%s: %s' % (r, e.strerror))
            return None
    if jobs:
        with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
            for size in ex.map(one, jobs):
                if size is not None:
                    n += 1
                    b += size
    for l in links:
        print('  not followed (junction/symlink): %s' % l)
    if absent:
        print('  %d list entr%s no longer exist at the source (skipped): %s'
              % (len(absent), 'y' if len(absent) == 1 else 'ies', ', '.join(absent[:5])))
    if a.dry_run:
        print('copylist (dry run): %d files, %s from %d list entries' % (n, gb(b), len(items)))
    else:
        print('copylist: %d copied (%s), %d already current, %d kept (already at the destination), from %d list entries'
              % (n, gb(b), skipped, kept, len(items)))
    print('BYTES=%d FILES=%d' % (b, n))
    if errors:
        print('COPYLIST FAIL: %d file(s) could not be read/written:' % len(errors))
        for e in errors[:25]:
            print('   ', e)
        return 1
    if not a.dry_run:
        print('COPYLIST OK')
    return 0


def du(a):
    out = []
    for p in a.paths:
        n = s = 0
        if os.path.isfile(lp(p)):
            n, s = 1, os.path.getsize(lp(p))
        elif os.path.isdir(lp(p)):
            sizes = tree_sizes(p)
            n, s = len(sizes), sum(v[0] for v in sizes.values())
        out.append({'path': p, 'files': n, 'bytes': s, 'exists': os.path.exists(lp(p))})
    if a.json:
        print(json.dumps(out))
    else:
        for o in out:
            print('%10s %8d files  %s' % (gb(o['bytes']), o['files'], o['path']))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('root-export')
    e.add_argument('--dest', required=True)
    e.add_argument('--root', default=DEFAULT_ROOT)
    e.add_argument('--dry-run', action='store_true')
    e.add_argument('--skip-build-output', action='store_true', help='leave usermaps/%s (the last build, ~17 GB) behind' % MAP)
    e.add_argument('--workers', type=int, default=32, help='files copied at once (default 32: Wi-Fi SMB is latency-bound)')
    i = sub.add_parser('root-import')
    i.add_argument('--src', required=True)
    i.add_argument('--root', default=DEFAULT_ROOT)
    i.add_argument('--force', action='store_true', help='also replace files that are newer on this machine')
    v = sub.add_parser('root-verify')
    v.add_argument('--manifest', required=True)
    v.add_argument('--root', default=DEFAULT_ROOT)
    v.add_argument('--quick', action='store_true', help='sizes only, no sha1')
    c = sub.add_parser('copylist')
    c.add_argument('--src', required=True)
    c.add_argument('--dest', required=True)
    g = c.add_mutually_exclusive_group(required=True)
    g.add_argument('--list', help='NUL- or newline-separated relative paths')
    g.add_argument('--git-untracked', action='store_true', help='copy every path git does not track in --src')
    c.add_argument('--save-list', help='with --git-untracked: also write the list here')
    c.add_argument('--no-overwrite', action='store_true', help='never replace a file already at the destination')
    c.add_argument('--workers', type=int, default=32, help='files copied at once (default 32)')
    c.add_argument('--dry-run', action='store_true')
    d = sub.add_parser('du')
    d.add_argument('paths', nargs='+')
    d.add_argument('--json', action='store_true')
    a = ap.parse_args()
    fn = {'root-export': root_export, 'root-import': root_import, 'root-verify': root_verify,
          'copylist': copylist, 'du': du}[a.cmd]
    return fn(a)


if __name__ == '__main__':
    sys.exit(main())
