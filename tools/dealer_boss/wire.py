#!/usr/bin/env python3
"""wire.py -- put the Dealer boss into the SHARED files in ONE step, right before a build (WIRE LAST).

  zone_source/zm_tod2_cybercity.zone   the aitype, the five models, the authored clips, the scripts, his effects (every
                                       share/raw/fx/tod/dealer/*.efx tools/dealer_fx/gen_fx.py writes, W2B / PK11)
  tools/sync_to_modtools.ps1           Copy-Tree rows for model_export/tod_dealer and xanim_export/tod_dealer
  tools/build_map.ps1                  the two gates: install.py --check and test_dealer.js, and the publish
                                       refusal while TOD_DEALER_TEST_SPAWN / TOD_DEALER_LOG are armed
  scripts/zm/zm_tod2_cybercity/_tod_main.gsc   the #using + the init call (after the Keeper's)

Idempotent: every line is guarded by a marker comment and re-running changes nothing.
`--check` reports what is still missing without writing (the test gate uses it).
"""
import os, re, sys, json
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ZONE = os.path.join(REPO, 'zone_source', 'zm_tod2_cybercity.zone')
SYNC = os.path.join(REPO, 'tools', 'sync_to_modtools.ps1')
BUILD = os.path.join(REPO, 'tools', 'build_map.ps1')
MAIN = os.path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_main.gsc')
MANIFEST = os.path.join(REPO, 'model_export', 'tod_dealer', 'install_manifest.json')
MARK = '// THE DEALER (docs/199): the final boss - tools/dealer_boss/wire.py writes this block; never hand-edit it.'
SCRIPTS = ['scripts/zm/zm_tod2_cybercity/_tod_dealer_finale.gsc', 'scripts/zm/zm_tod2_cybercity/_tod_dealer_finale.csc']
FX_DIR = os.path.join(REPO, 'share', 'raw', 'fx', 'tod', 'dealer')   # his effects (GENERATED: tools/dealer_fx/gen_fx.py)

# the -Publish refusal while the test spawn / the dev-off log are armed (the partner benches' pattern)
PUBLISH_GATE = r"""# THE DEALER TEST SPAWN + LOG (docs/199). TOD_DEALER_TEST_SPAWN in _tod_dealer_finale.gsc spawns the
# final boss in the crown hall after the opening for the playtest; TOD_DEALER_LOG prints with dev OFF.
$DealerGsc = Join-Path $RepoRoot 'scripts\zm\zm_tod2_cybercity\_tod_dealer_finale.gsc'
if (Test-Path $DealerGsc) {
    $armedDealer = @(Select-String -Path $DealerGsc -Pattern '^\s*#define\s+TOD_DEALER_(TEST_SPAWN|LOG)\s+1\b' |
                    ForEach-Object { $_.Line.Trim() })
    if ($armedDealer.Count -gt 0) {
        if ($Publish) {
            Die ("PUBLISH GATE: {0} is ARMED in {1} -> set it to 0, rebuild, then publish" -f ($armedDealer -join '; '), $DealerGsc)
        }
        Warn ("THE DEALER test state ARMED ({0}) - he spawns in the crown hall / logs with dev off; NEVER publish this .ff" -f ($armedDealer -join '; '))
    }
}
"""

BUILD_GATE = """    & python (Join-Path $PSScriptRoot "dealer_boss/install.py") --check
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER boss assets are stale - re-run tools/dealer_boss/export_native.py + install.py (docs/199)." }
    & node (Join-Path $PSScriptRoot "dealer_boss/test_dealer.js")
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER boss contract failed - see test_dealer.js output." }
"""

MAIN_USING = '#using scripts\\zm\\zm_tod2_cybercity\\_tod_dealer_finale;   // THE DEALER (docs/199): the final boss'
MAIN_CALL = '\ttod_dealer_finale::init();   // docs/199: THE DEALER, the final boss (the crown-hall test spawn while TOD_DEALER_TEST_SPAWN is 1)'


def read(path):
    text = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in text else '\n'
    return text, nl


def write(path, text):
    open(path, 'w', encoding='utf-8', newline='').write(text)


def zone_block():
    man = json.load(open(MANIFEST))
    lines = [MARK]
    for s in SCRIPTS:
        if os.path.exists(os.path.join(REPO, s)):
            lines.append('scriptparsetree,' + s)
    lines += ['aitype,spawner_tod_dealer', 'xmodel,tod_dealer_body', 'xmodel,tod_dealer_body_cracked', 'xmodel,tod_dealer_scythe']
    lines += ['xmodel,' + v for v in man['weapon_models'].values()]
    lines += ['xanim,' + c for c in man['clips']]
    if os.path.isdir(FX_DIR):   # W2B / PK11: his aura, trail, arrival, mask shatter, eye, death and dissolve (one line each)
        lines += ['fx,tod/dealer/' + f[:-4] for f in sorted(os.listdir(FX_DIR)) if f.endswith('.efx')]
    lines.append('// end THE DEALER')
    return '\n'.join(lines) + '\n'


def wire_zone(check):
    text, nl = read(ZONE)
    block = zone_block().replace('\n', nl)
    if MARK in text:
        start = text.index(MARK); end = text.index('// end THE DEALER', start) + len('// end THE DEALER') + len(nl)
        if text[start:end] == block:
            return False
        if check:
            return True
        text = text[:start] + block + text[end:]
    else:
        if check:
            return True
        text = text.rstrip(nl) + nl + nl + block
    write(ZONE, text)
    return True


def wire_sync(check):
    text, nl = read(SYNC)
    rows = ['    Copy-Tree (Join-Path $RepoRoot "model_export\\tod_dealer") (Join-Path $ModTools "model_export\\tod_dealer") "THE DEALER boss: body, cracked-mask body, scythe, weapons, atlases (docs/199)" $false',
            '    Copy-Tree (Join-Path $RepoRoot "xanim_export\\tod_dealer") (Join-Path $ModTools "xanim_export\\tod_dealer") "THE DEALER boss: his authored clips (docs/199)" $false']
    missing = [r for r in rows if r not in text]
    if not missing:
        return False
    if check:
        return True
    anchor = '    Copy-Tree (Join-Path $RepoRoot "model_export\\tod_crown_alarm")'
    i = text.index(anchor); j = text.index(nl, i) + len(nl)
    text = text[:j] + nl.join(missing) + nl + text[j:]
    write(SYNC, text)
    return True


def wire_build(check):
    text, nl = read(BUILD)
    changed = False
    if 'dealer_boss/install.py' not in text:
        if check:
            return True
        anchor = '    & node (Join-Path $PSScriptRoot "keeper/test_keeper.js")'
        i = text.index(anchor); j = text.index(nl, text.index('Die "Keeper boss / soul line', i)) + len(nl)
        text = text[:j] + BUILD_GATE.replace('\n', nl) + text[j:]
        changed = True
    if 'TOD_DEALER_(TEST_SPAWN|LOG)' not in text:
        if check:
            return True
        anchor = 'Warn ("TOD_PARTNER_TEST_BENCHES ARMED'
        i = text.index(anchor)
        j = text.index('}' + nl + '}' + nl, i) + len('}' + nl + '}' + nl)
        text = text[:j] + nl + PUBLISH_GATE.replace('\n', nl) + text[j:]
        changed = True
    if changed:
        write(BUILD, text)
    return changed


def wire_main(check):
    """the module's #using beside the Keeper's and its init() right after the Keeper's (he spawns through nothing
    but his own test thread for now; the finale wiring is a later pass)"""
    text, nl = read(MAIN)
    changed = False
    if MAIN_USING not in text:
        if check:
            return True
        a = '#using scripts\\zm\\zm_tod2_cybercity\\_tod_keeper;'
        i = text.index(a); j = text.index(nl, i) + len(nl)
        text = text[:j] + MAIN_USING + nl + text[j:]
        changed = True
    if 'tod_dealer_finale::init();' not in text:
        if check:
            return True
        a = '\ttod_keeper::init();'
        i = text.index(a); j = text.index(nl, i) + len(nl)
        text = text[:j] + MAIN_CALL + nl + text[j:]
        changed = True
    if changed:
        write(MAIN, text)
    return changed


def main():
    check = '--check' in sys.argv
    if not os.path.exists(MANIFEST):
        raise SystemExit('no install manifest: run install.py first')
    changed = {'zone': wire_zone(check), 'sync': wire_sync(check), 'build': wire_build(check), 'main': wire_main(check)}
    if check:
        pending = [k for k, v in changed.items() if v]
        if pending:
            raise SystemExit('dealer wire --check: NOT WIRED: ' + ', '.join(pending))
        print('dealer wire --check OK')
    else:
        print('dealer wire:', {k: ('written' if v else 'already wired') for k, v in changed.items()})


if __name__ == '__main__':
    main()
