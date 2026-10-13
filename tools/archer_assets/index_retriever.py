"""Gather exact Retriever dependencies from the retained OAT source dumps."""
from pathlib import Path
import csv
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT/'source_library/archer_equipment'
DATA = LIB/'bo2_motd/20260925_042053_156865_dump/dump/zm_prison'
IMAGES = LIB/'bo2_motd/20260925_042222_883023_dump/dump/zm_prison'
AUDIO = LIB/'bo2_motd/20260925_042929_363375_dump/dump/zm_prison'
OUT = LIB/'retriever'


def main():
    paths = {}
    for source in (DATA, IMAGES, AUDIO):
        for file in source.rglob('*'):
            if file.is_file() and any(x in file.name.lower() for x in ('tomahawk', 'hatchet')):
                paths[file.relative_to(source)] = file
    materials = list((DATA/'materials/mc').glob('*tomahawk*.json'))
    for mat in materials:
        for texture in json.loads(mat.read_text())['textures']:
            relative = Path('images')/(texture['image']+'.dds')
            file = IMAGES/relative
            if not file.is_file():
                raise RuntimeError('Missing Retriever image: '+str(relative))
            paths[relative] = file
    with (AUDIO/'soundbank/zmb_alcatraz.all.aliases.csv').open(newline='') as file:
        all_rows = list(csv.DictReader(file))
    aliases = [r for r in all_rows if 'tomahawk' in r['Name']]
    secondaries = {r['Secondary'] for r in aliases if r['Secondary']}
    aliases += [r for r in all_rows if r['Name'] in secondaries and r not in aliases]
    missing_audio = []
    for row in aliases:
        rel = Path(row['FileSource'].replace('\\', '/').removeprefix('raw/'))
        found = next((AUDIO/p for p in (rel, Path(str(rel)+'.wav'), Path(str(rel)+'.flac')) if (AUDIO/p).is_file()), None)
        if not found:
            missing_audio.append({'alias': row['Name'], 'source': str(rel)})
            continue
        paths[found.relative_to(AUDIO)] = found
    paths[Path('source_data/zm_prison.gdt')] = DATA/'source_data/zm_prison.gdt'
    records = []
    for relative, source in sorted(paths.items()):
        destination = OUT/relative; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        records.append({'path': relative.as_posix(), 'source': source.relative_to(ROOT).as_posix(),
                        'bytes': source.stat().st_size, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    report = {'game': 'BO2 Mob of the Dead', 'extractor': 'OpenAssetTools 0.33.0',
              'files': records, 'audio_aliases': aliases, 'game_started_by_agent': False,
              'image_errors_after_private_dlc_alias': 0, 'missing_audio': missing_audio,
              'native_bo3_animations': False}
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print('RETRIEVER_SOURCES', len(records), 'files;', len(aliases), 'audio alias rows;', len(missing_audio), 'unresolved secondary samples')


if __name__ == '__main__':
    main()
