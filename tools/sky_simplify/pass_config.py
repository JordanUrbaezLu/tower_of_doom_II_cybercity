"""Paths and source provenance for v9; importing this module writes nothing."""
import ast
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = ROOT / 'tmp/sky_simplify'
REVIEW = ROOT / 'art/sky3d/simplify_review'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def sky_sources():
    """Include local imports of the sky generator without importing bpy."""
    todo = [ROOT / 'tools/sky3d/build_city.py']
    seen = set()
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for name in names:
                local = path.parent / (name.split('.')[0] + '.py')
                if local.is_file():
                    todo.append(local)
    return sorted(seen)


def source_hashes():
    # Finishing and preview code may change without reauthoring geometry. Those
    # are captured by the final build snapshot, not this master-source contract.
    paths = sky_sources() + [pathlib.Path(__file__), pathlib.Path(__file__).with_name('author.py')]
    config = STAGE / 'author_config.json'
    if config.is_file():
        paths.append(config)
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths))}
