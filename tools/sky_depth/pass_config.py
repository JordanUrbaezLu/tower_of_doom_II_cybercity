"""Paths and source provenance for v13; importing this module writes nothing."""
import ast
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = ROOT / 'tmp/sky_depth'
REVIEW = ROOT / 'art/sky3d/depth_review'
SKY_SOURCE_DIR = ROOT / 'tools/sky3d'
SOURCE_OVERRIDES = {'cyber_architecture': pathlib.Path(__file__).parent / 'staged_sources/cyber_architecture.py'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def resolve_sky_source(module_name):
    """Mirror author.py's explicit override; other local imports remain shared.

    The staged directory is never added to sys.path. Its candidate dependencies
    resolve against tools/sky3d exactly as they do when the generator executes.
    An absent explicit candidate is an error, never a fallback to shipping art.
    """
    name = module_name.split('.')[0]
    path = SOURCE_OVERRIDES.get(name, SKY_SOURCE_DIR / (name + '.py'))
    if name in SOURCE_OVERRIDES and not path.is_file():
        raise FileNotFoundError('Missing isolated depth source: ' + str(path))
    return path if path.is_file() else None


def sky_sources():
    """Hash actual imported source paths, including isolated replacements."""
    todo = [SKY_SOURCE_DIR / 'build_city.py']
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
                local = resolve_sky_source(name)
                if local is not None:
                    todo.append(local)
    return sorted(seen)


def source_hashes():
    # Finishing and preview code may change without reauthoring geometry. Those
    # are captured by the final build snapshot, not this master-source contract.
    paths = sky_sources() + [pathlib.Path(__file__)] + [pathlib.Path(__file__).with_name(name)
             for name in ('author.py', 'quality_profile.py', 'quality_profile.json')]
    config = STAGE / 'author_config.json'
    if config.is_file():
        paths.append(config)
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths))}
