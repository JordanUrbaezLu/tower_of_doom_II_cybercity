"""Retain native RPak metadata that RSX cannot translate (FX/shaders/etc.).

This is not a complete game backup: external StarPak streams remain in Apex.
Usable exported meshes, clips, textures and WAVs are stored separately.
"""
import shutil
from extract_sources import APEX, COMMON, UI, PAKS, REPO, TOOL, LIBRARY, digest, write_json

if __name__ == "__main__":
    dest = LIBRARY / "native_packages"
    dest.mkdir(parents=True, exist_ok=True)
    sources = set(COMMON + UI + list(PAKS.glob("patch_master*.rpak")))
    for base in COMMON + UI:
        sources.update(PAKS.glob(base.stem + "(*).rpak"))
    records = []
    for source in sorted(sources):
        target = dest / source.name
        if not target.exists():
            shutil.copy2(source, target)
        source_hash, target_hash = digest(source), digest(target)
        assert source_hash == target_hash, source
        records.append(dict(source=str(source), archive=str(target.relative_to(LIBRARY)),
                            bytes=target.stat().st_size, sha256=target_hash))
        print(source.name, target.stat().st_size, flush=True)
    for name in ("build.txt", "gameversion.txt"):
        shutil.copy2(APEX / name, dest / name)
    write_json(LIBRARY / "evidence/native_packages.json", dict(packages=records,
        limitation="Native RPak metadata retained. External StarPak stream files are read-only in the original Apex installation; this is not a standalone Apex backup."))
    # First model export predates the per-run fallback handling.
    old = TOOL / "exported_files"
    target = LIBRARY / "standalone_materials/extract_models"
    if old.exists():
        if not all(p.resolve().is_relative_to(REPO.resolve()) for p in (old, target)):
            raise RuntimeError("Unsafe archive move")
        if target.exists():
            raise FileExistsError(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        old.rename(target)
