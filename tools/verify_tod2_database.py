"""Reject a private-looking database whose definitions still belong to Map One."""
from pathlib import Path
import sqlite3

ROOT = Path('C:/BO3Tools/TOD2Cybercity')
db = sqlite3.connect((ROOT / 'gdtdb/gdt.db').as_uri() + '?mode=ro', uri=True)
db.execute('pragma writable_schema=ON')
rows = db.execute('select * from _gdt').fetchall()
assert rows, 'Private GDT database is empty'
prefix = str(ROOT).replace('/', '\\').lower() + '\\'
foreign = [row[1] for row in rows if not row[1].lower().startswith(prefix)]
assert not foreign, ('Foreign source paths in Tower II asset database', foreign[:10])
for name in ('tod_teleporter', 'tod_heavenly_altar'):
    assert db.execute('select 1 from xmodel where _name=?', (name,)).fetchone(), name
print(f'TOD II DATABASE PASS: {len(rows)} definitions files, all under the private tools root.')
