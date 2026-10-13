"""Builds source_data/tod_necro_skull.gdt from the stock Skull of Nan Sapwe.

The Necromancer's primary (2026-09-26). Source = the tools root's
wpn_t7_zmb_dlc2_keeper_head.gdt block "skull_gun_zm" (the HB21 pack's rip of
Zetsubou's hero weapon). Re-run this; never hand-edit the output.

Changes from stock, and why:
  inventoryType primary   it is the class gun, not a hero gadget
  gadget_type none        no power bar; _tod_necro_skull.gsc owns the soul meter
  altWeapon ""            a live altWeapon is the boot trap (docs/25 section 7)
  ammoName/clipName       its own pool, never the ray gun's
  weaponClass rocketlauncher  "pistol" would make it the last-stand weapon
  displayName             a literal, like the staffs
  maxAmmo 0               clip only; script tops the clip off
Two blocks: tod_necro_skull (base) and tod_necro_skull_up (PaP; the stock
upgraded block is the same weapon, the PaP difference is script-side).
"""
import os, re, sys

TOOLS = os.environ.get("TOD2_TOOLS", r"C:\BO3Tools\TOD2Cybercity")
SRC = os.path.join(TOOLS, "source_data", "wpn_t7_zmb_dlc2_keeper_head.gdt")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "source_data", "tod_necro_skull.gdt")

SET = {
    "inventoryType": "primary",
    "gadget_type": "none",
    "altWeapon": "",
    "ammoName": "tod_necro_skull",
    "clipName": "tod_necro_skull",
    "weaponClass": "rocketlauncher",
    "clipSize": "100",
    "startAmmo": "100",
    "maxAmmo": "0",
    "clipOnly": "1",
    "power_consume_on_ammo_use": "0",
    "parentWeaponName": "",
    # the stock block only names the 3p (npc) loop; the shooter gets the 1p
    # rows (all in sound/aliases/tod_necromancer.csv)
    "startFireSoundPlayer": "zmb_wpn_skullgun_start_plr",
    "loopFireSoundPlayer": "zmb_wpn_skullgun_loop_plr",
    "loopFireEndSoundPlayer": "zmb_wpn_skullgun_stop_plr",
    "raiseSound": "zmb_wpn_skullgun_raise_npc",
    "raiseSoundPlayer": "zmb_wpn_skullgun_raise_plr",
    "firstRaiseSoundPlayer": "fly_skull_first_raise",
    # PK27 (2026-10-05): the stock block names Der Eisendrache's fly_shoulder_* foley for putaway and the 3P first
    # raise, which no sheet this map loads defines (silent). Map-owned rows in sound/aliases/tod_necro_foley.csv
    # (tools/sfx/w2c_sounds): a bone-and-leather lower for both ears, and the stock first-raise WAV in 3D.
    "putawaySound": "tod_necro_skull_lower_npc",
    "putawaySoundPlayer": "tod_necro_skull_lower_plr",
    "firstRaiseSound": "tod_necro_first_raise_npc",
}
NAMES = {"tod_necro_skull": "Skull of Nan Sapwe", "tod_necro_skull_up": "Skull of the Damned"}

text = open(SRC, encoding="latin1").read()
m = re.search(r'^\t"skull_gun_zm" \( "projectileweapon\.gdf" \)\r?\n\t\{.*?^\t\}', text, re.S | re.M)
if not m:
    sys.exit("skull_gun_zm block not found in " + SRC)
block = m.group(0).replace("\r\n", "\n")

def emit(name):
    b = block.replace('"skull_gun_zm" (', '"%s" (' % name, 1)
    want = dict(SET, displayName=NAMES[name])
    for k, v in want.items():
        pat = re.compile(r'^(\t\t"%s" )"[^"]*"$' % re.escape(k), re.M)
        if pat.search(b):
            b = pat.sub(lambda mm: mm.group(1) + '"%s"' % v, b, count=1)
        else:
            b = b[: b.rfind("\t}")] + '\t\t"%s" "%s"\n\t}' % (k, v)
    return b

out = "{\n" + emit("tod_necro_skull") + "\n" + emit("tod_necro_skull_up") + "\n}\n"
open(OUT, "w", encoding="latin1", newline="\n").write(out)
for k in ("inventoryType", "altWeapon", "weaponClass", "displayName"):
    assert out.count('"%s" "' % k) == 2, k
print("wrote", OUT, len(out), "bytes")
