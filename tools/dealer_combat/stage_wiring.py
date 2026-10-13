"""Stage shared-file edits; keep every unrelated byte/hunk and detect later edits."""
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from prepare import ROOT, STAGE, change


def main():
    pins=json.loads((STAGE/'inputs.json').read_text())
    def edit(rel, edits, tail=''):
        pins[rel]=change(rel,edits,tail)
    edit('tools/dealer_boss/install.py',[
        ("    'anim_dealer_channel_loop': F('revive_loop'),",
         "    'anim_dealer_channel_loop': F('revive_loop'),\n    # Dedicated gun holds live in the independently generated combat sidecar GDT.\n    'anim_dealer_weapon_shock': 'tod_dealer_c_shock',\n    'anim_dealer_weapon_burst': 'tod_dealer_c_burst',")])
    edit('tools/dealer_boss/test_dealer.js',[
        ("const keeperGdt = R('source_data/tod_keeper.gdt');",
         "const keeperGdt = R('source_data/tod_keeper.gdt');\nconst combatGdt = R('source_data/tod_dealer_combat.gdt');"),
        ("const shipped = new Set([...keeperGdt.matchAll", "const shipped = new Set([...(keeperGdt + combatGdt).matchAll"),
        ("for (const m of installPy.matchAll(",
         "const noteAliasesBlock = (installPy.match(/NOTE_ALIASES = \\{([\\s\\S]*?)\\n\\}/) || [])[1];\nok(!!noteAliasesBlock, '9 the sound-note mapping dictionary exists');\nfor (const m of noteAliasesBlock.matchAll(")
    ])
    # Generate the AM from the real installer (no pack extraction, copying or master writes).
    sys.path.insert(0,str(ROOT/'tools/keeper'))
    spec=importlib.util.spec_from_file_location('dc_installer',STAGE/'tools/dealer_boss/install.py')
    inst=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inst)
    am=inst.am_text((ROOT/'animtables/tod_keeper.ai_am').read_text())
    rel='animtables/tod_dealer.ai_am'
    raw=(ROOT/rel).read_bytes()
    data=am.replace('\r\n','\n').replace('\n','\r\n').encode()
    dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    pins[rel]={'before':hashlib.sha256(raw).hexdigest(),'after':hashlib.sha256(data).hexdigest()}
    rel='model_export/tod_dealer/install_manifest.json'
    raw=(ROOT/rel).read_bytes();man=json.loads(raw)
    man['script_aliases']=inst.SCRIPT_ALIASES
    man['texts']['animtables/tod_dealer.ai_am']=hashlib.sha256(data).hexdigest()
    data=(json.dumps(man,indent=1,sort_keys=True)+'\n').encode()
    dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    pins[rel]={'before':hashlib.sha256(raw).hexdigest(),'after':hashlib.sha256(data).hexdigest()}
    zone='\n// DEALER COMBAT: tools/dealer_combat; dedicated native holds and bounded weapon effects.\n'
    zone+=''.join('xanim,tod_dealer_c_'+k+'\n' for k in ('shock','burst'))
    zone+=''.join('fx,tod/dealer_combat/fx_dc_'+k+'\n' for k in ('warning','charge','shock','muzzle','tracer'))
    zone+='// end DEALER COMBAT\n'
    edit('zone_source/zm_tod2_cybercity.zone',[],zone)
    rel='sound/zoneconfig/zm_tod2_cybercity.szc'
    text=(ROOT/rel).read_text()
    tpl=re.search(r'([ \t]*)(\{[^{}]*"Filename"\s*:\s*"tod_dealer\.csv"[^{}]*\})',text)
    assert tpl and not 'tod_dealer_combat.csv' in text
    clone=tpl.group(2).replace('"tod_dealer.csv"','"tod_dealer_combat.csv"').replace('"tod_dealer"','"tod_dealer_combat"')
    edit(rel,[(tpl.group(2),tpl.group(2)+',\n'+tpl.group(1)+clone)])
    json.loads((STAGE/rel).read_text())
    gate='''    # Dealer weapon pass: lifecycle/footprint, native clips and authored sound/FX pins.
    & node (Join-Path $PSScriptRoot "dealer_combat/test_combat.js")
    if ($LASTEXITCODE -ne 0) { Die "Dealer weapon lifecycle / fairness contract failed." }
    & python -B (Join-Path $PSScriptRoot "dealer_combat/check_assets.py")
    if ($LASTEXITCODE -ne 0) { Die "Dealer gun animation sources or native registration are stale." }
    & python -B (Join-Path $PSScriptRoot "dealer_combat/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Dealer weapon sound cues are stale or invalid." }
    & python -B (Join-Path $PSScriptRoot "dealer_combat/gen_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Dealer weapon effects are stale or invalid." }
'''
    postgate='''    # Dealer effects can be rejected without an ERROR: prefix; require all native definitions.
    & python -B (Join-Path $PSScriptRoot 'dealer_combat/gen_fx.py') --check --compiled-ledger $partnerLedger
    if ($LASTEXITCODE -ne 0) { Die "Dealer weapon effects are missing or rejected by the native linker." }
'''
    marker="    $partnerLedger = $cyberLedger -replace '_xmodel\\.csv$', '.csv'"
    edit('tools/build_map.ps1',[
        ("    # THE RETIREMENT PIN (W2E, 2026-10-05):",gate+"    # THE RETIREMENT PIN (W2E, 2026-10-05):"),
        (marker,marker+'\n'+postgate.rstrip('\n'))])
    (STAGE/'inputs.json').write_text(json.dumps(pins,indent=2))
    print('DEALER COMBAT WIRING STAGED: shared originals pinned; no live edits')


if __name__=='__main__':main()
