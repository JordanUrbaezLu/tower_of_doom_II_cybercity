"""Install THE SKY FLEET's staged GDT into source_data (docs/192).

06_export.py writes art/sky_ships/staging/tod_sky_ships.gdt, NOT source_data: a half-written GDT in
source_data breaks every session's build at the gdtdb step. Run this only when no build is running.
  python tools/sky_ships/install.py
"""
import hashlib, json, pathlib, shutil
ROOT = pathlib.Path(__file__).resolve().parents[2]
m = json.loads((ROOT / 'art/sky_ships/manifest.json').read_text(encoding='utf-8'))
src = ROOT / m['gdt']
dst = ROOT / 'source_data/tod_sky_ships.gdt'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src) == m['gdt_sha256'], 'staged GDT does not match the export manifest'
shutil.copyfile(src, dst)
assert sha(dst) == m['gdt_sha256']
print('SKY GDT INSTALLED', dst.relative_to(ROOT).as_posix(), m['gdt_sha256'][:12])
