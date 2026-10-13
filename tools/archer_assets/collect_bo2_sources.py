"""Read BO2/MOTD fastfiles with OAT; all outputs stay in this repository.

Start with `--action list`. Dumping includes the selected asset types for the
whole zone; inspect the retained list for tomahawk assets before converting.
This tool never starts a game, modifies a game install, or installs a mod.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'tmp/archer_assets/oat_0.33.0/Unlinker.exe'
OUTPUT = ROOT / 'source_library/archer_equipment/bo2_motd'
DEFAULT_ZONES = ('common_zm', 'common_patch_zm', 'zm_prison', 'zm_prison_patch')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, required=True)
    parser.add_argument('--action', choices=('list', 'dump'), default='list')
    parser.add_argument('--zone', action='append', help='Exact zone basename; repeatable')
    parser.add_argument('--asset-types', default='xmodel,xanim,material,image,weapon,soundbank,script,rawfile')
    parser.add_argument('--preload-zone', action='append', default=[], help='Load a dependency zone before dumping')
    args = parser.parse_args()
    game = args.game_root.resolve()
    if not game.is_dir():
        parser.error('BO2 game root does not exist. Supply the installed game/data folder.')
    if not TOOL.is_file():
        parser.error('OAT 0.33.0 is missing; see tools/archer_assets/README.md.')
    search = [game/p for p in ('main', 'sounds', 'zone/all', 'zone/english') if (game/p).is_dir()]
    zones, missing = [], []
    for name in args.zone or DEFAULT_ZONES:
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
            parser.error('Zone names must be basenames without paths or extensions.')
        found = [p/(name+'.ff') for p in search if (p/(name+'.ff')).is_file()]
        if found:
            zones.append(found[0])
        else:
            missing.append(name)
    if not zones:
        parser.error('No requested BO2 fastfiles found. Mob of the Dead is zm_prison.')
    preloads=[]
    for name in args.preload_zone:
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
            parser.error('Preload zone names must be basenames.')
        found=next((p/(name+'.ff') for p in search if (p/(name+'.ff')).is_file()),None)
        if not found:parser.error('Missing preload zone: '+name)
        preloads.append(found)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    out = OUTPUT/(stamp+'_'+args.action)
    out.mkdir(parents=True, exist_ok=False)
    # Steam's Zombies-only depot names this DLC IPAK dlczm2, while the original
    # Alcatraz fastfile requests dlc2. Alias a private COPY; never rename or
    # write a file in the installed game. Search this copy first.
    aliases = []
    if any('prison' in z.stem for z in zones):
        original = game/'zone/all/dlczm2.ipak'
        if original.is_file() and not any((p/'dlc2.ipak').is_file() for p in search):
            alias_dir = out/'input_aliases'; alias_dir.mkdir()
            destination = alias_dir/'dlc2.ipak'
            shutil.copy2(original, destination)
            aliases.append({'source': str(original), 'copy': str(destination), 'sha256': sha(original)})
            search.insert(0, alias_dir)
    report = {'action': args.action, 'game_root': str(game), 'tool': str(TOOL),
              'tool_sha256': sha(TOOL), 'missing_zones': missing, 'zones': [],
              'input_aliases': aliases, 'game_started': False, 'conversion_to_bo3': False}
    failures = []
    for zone in zones:
        command = [str(TOOL), '--no-color', '--verbose', '--search-path', ';'.join(map(str, search))]
        for preload in preloads:
            command.extend(['--load',str(preload)])
        if args.action == 'list':
            command.append('--list')
        else:
            command.extend(['--output-folder', str(out/'dump'/'?zone?'), '--model-format',
                            'XMODEL_BIN', '--image-format', 'DDS', '--gdt', '--include-assets',
                            args.asset_types])
        command.append(str(zone))
        log = out/(zone.stem+'.log')
        with log.open('wb') as stream:
            result = subprocess.run(command, cwd=out, stdout=stream, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        # OAT can exit zero after reporting missing image payloads.
        text = log.read_text(encoding='utf8', errors='replace')
        errors = len(re.findall(r'^ERROR:', text, re.MULTILINE))
        summary = re.search(r'Finished with (\d+) warnings, (\d+) errors', text)
        if summary:
            errors = max(errors, int(summary[2]))
        report['zones'].append({'file': str(zone), 'sha256': sha(zone), 'bytes': zone.stat().st_size,
                                'command': command, 'returncode': result.returncode, 'errors': errors, 'log': log.name})
        if result.returncode or errors:
            failures.append(zone.name)
        print(zone.name, 'exit', result.returncode, 'errors', errors, '->', log, flush=True)
        (out/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print('Evidence:', out)
    if missing:
        print('Not present:', ', '.join(missing))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
