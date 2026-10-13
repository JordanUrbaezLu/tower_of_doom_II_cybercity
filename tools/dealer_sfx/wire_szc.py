"""Register sound/aliases/tod_dealer.csv in the sound zone config (W2B / PK10): a text copy of the tod_house entry, placed
right after it (the battle arena / dealer house generators' szc_register pattern). Idempotent; --check reports only.

  python tools/dealer_sfx/wire_szc.py [--root DIR] [--check]

The lander runs it (or pastes the entry by hand: see tmp/wave2/W2B-dealer-av/LAND.md WIRING); never while a build runs.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(sys.argv[sys.argv.index('--root') + 1]) if '--root' in sys.argv else pathlib.Path(__file__).resolve().parents[2]
SZC = ROOT / 'sound' / 'zoneconfig' / 'zm_tod2_cybercity.szc'


def loads(text):
    try:
        data = json.loads(text)
    except ValueError:
        return False
    return any(isinstance(s, dict) and s.get('Type') == 'ALIAS' and str(s.get('Filename', '')).lower() == 'tod_dealer.csv'
               for s in data.get('Sources', []))


def main():
    raw = SZC.read_bytes()
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text = raw[len(bom):].decode('utf-8')
    if loads(text):
        print('DEALER SZC OK: tod_dealer.csv is loaded by', SZC.name)
        return 0
    if '--check' in sys.argv:
        print('DEALER SZC: tod_dealer.csv is NOT loaded by %s - run tools/dealer_sfx/wire_szc.py' % SZC)
        return 1
    tpl = re.search(r'([ \t]*)(\{[^{}]*"Filename"\s*:\s*"tod_house\.csv"[^{}]*\})', text)
    if not tpl:
        sys.exit('DEALER SZC: no tod_house entry in %s to copy - add the tod_dealer ALIAS source by hand' % SZC)
    nl = '\r\n' if '\r\n' in text else '\n'
    clone = tpl.group(2).replace('"tod_house.csv"', '"tod_dealer.csv"').replace('"tod_house"', '"tod_dealer"')
    new = text[:tpl.end()] + ',' + nl + tpl.group(1) + clone + text[tpl.end():]
    if not loads(new):
        sys.exit('DEALER SZC: %s would not parse with tod_dealer added - left untouched' % SZC)
    SZC.write_bytes(bom + new.encode('utf-8'))
    print('DEALER SZC: registered tod_dealer.csv in', SZC)
    return 0


if __name__ == '__main__':
    sys.exit(main())
