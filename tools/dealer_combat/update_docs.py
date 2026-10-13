"""Record completed native delivery, keeping shared document line endings and peer notes."""
import datetime
import json
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]


def replace(rel,before,after):
    p=ROOT/rel;raw=p.read_bytes();nl='\r\n' if b'\r\n' in raw else '\n'
    text=raw.decode('utf-8');before=before.replace('\n',nl);after=after.replace('\n',nl)
    assert text.count(before)==1,(rel,before[:60])
    p.write_bytes(text.replace(before,after).encode('utf-8'))


def main():
    proof=json.loads((ROOT/'art/dealer_combat/build.json').read_text())
    stamp=datetime.datetime.fromtimestamp(proof['ff']['mtime_ns']/1e9).strftime('%Y-%m-%d %H:%M')
    replace('docs/207_dealer_house.md',
        'The fight is the docs/199 first pass (the scythe float, the cracked-mask gun run): no Wunderwaffe shock, no Dingo\nbursts, no adds. (W2B, 2026-10-05:',
        'The fight now includes warned fixed-position Wunderwaffe shocks and six-round Dingo bursts with native two-hand\ngun clips (docs/dealer_combat/README.md). Guarded FULL delivery is art/dealer_combat/build.json; native fight unplayed.\nAdds are not implemented. (W2B, 2026-10-05:')
    replace('docs/199_dealer_boss.md',
        '- Still to do: the Wunderwaffe shock, the machine-gun bursts and its two-hand hold, the adds (section 4). The aura,',
        '- The Wunderwaffe shock and Dingo bursts/two-hand attack holds are now implemented and built (docs/dealer_combat/README.md); native fight unplayed. Adds remain a design item (section 4). The aura,')
    p=ROOT/'docs/status_log.md';raw=p.read_bytes();nl=b'\r\n' if b'\r\n' in raw else b'\n'
    cut=raw.index(nl+nl)+len(nl+nl)
    note=(f'**{stamp} - DEALER WEAPON PASS: GUARDED FULL BUILD OK; USER FIGHT UNPLAYED.** '
        f'Dealer\'s House has fixed-position Wunderwaffe shocks and warned six-round Dingo bursts, '
        f'two dedicated native two-hand clips, five bounded carrier effects and four measured sound cues. '
        f'Cover, the marked footprint, co-op overlap and every pause/hold/stun/phase/death exit are guarded. '
        f'The final death line finishes before arena cards. Independent code/art review passed; '
        f'60 combat checks plus three planted regressions and the complete guarded build gates passed. '
        f'FF {proof["ff"]["bytes"]:,} bytes, SHA256 {proof["ff"]["sha256"][:16]}...; '
        f'{len(proof["source_parity"])} deployed inputs match, both new xanims/all five FX/three modules are linked, '
        f'four native aliases and loaded-bank entries verified. Geometry/lighting '
        f'{"reused by byte-identity gate" if proof["geometry_reused"] else "processed by guarded FULL pipeline"}. '
        f'No game launched. Evidence: art/dealer_combat/build.json, review/review.html; '
        f'docs/dealer_combat/README.md. Correct Rendered preview: tools/dealer_combat/open_preview.ps1. '
        f'The earlier reported-OK build omitted the charge effect after duplicate curve times; '
        f'it was rejected by the delivery audit and is archived under deliveries/20261007_charge_rejected/. '
        f'The curve is repaired; source negative controls and a mandatory five-effect compiled gate now pass. '
        f'The character master/core 45 clips/material pins are preserved; no retired voice/finale restored.\n\n')
    p.write_bytes(raw[:cut]+note.replace('\n',nl.decode()).encode('utf-8')+raw[cut:])
    print('DEALER COMBAT DOCS: delivered behavior and fresh FF proof recorded; user playtest pending')


if __name__=='__main__':main()
