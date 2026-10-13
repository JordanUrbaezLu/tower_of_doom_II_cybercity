"""Compare protected Map One/shared-install file metadata against a pre-work snapshot.

Junctions are deliberately not traversed: the sole new shared entry is the unique
Tower II game-folder junction, whose destination is validated independently.
This reports size/mtime evidence, not a claim that every stock byte was hashed.
"""
import argparse
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / 'tmp/tod2_isolation'
ROOTS = {
    'map_one_shared': Path('C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops III 455130'),
    'map_one_repo': REPO.parent / 'tower_of_doom_cybercity',
}


def scan(root):
    files = {}
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [n for n in dirs if not (Path(base) / n).is_junction()]
        for name in names:
            p = Path(base) / name
            st = p.stat()
            files[p.relative_to(root).as_posix()] = [st.st_size, st.st_mtime_ns]
    return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name, root in ROOTS.items():
        snapshot = OUT / (name + '_before.json')
        current = scan(root)
        if args.snapshot:
            # Never destroy original before-work evidence.
            with snapshot.open('x') as f:
                json.dump(current, f)
        else:
            before = json.loads(snapshot.read_text())
            changed = [p for p in before.keys() | current.keys() if before.get(p) != current.get(p)]
            reports[name] = {'files': len(before), 'size_or_mtime_changes': changed}
            print(name, len(before), 'files;', len(changed), 'changes', flush=True)
    if not args.snapshot:
        (OUT / 'protected_paths_verification.json').write_text(json.dumps(reports, indent=2) + '\n')
        assert all(not row['size_or_mtime_changes'] for row in reports.values()), reports
