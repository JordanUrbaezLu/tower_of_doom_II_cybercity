// THE BREACHER'S GUNS CARRY NO OPTIC, AND STILL HAVE SOMETHING TO AIM DOWN
// (docs/208; map 1's v19.22 gate, retargeted to TOD II's roster).
//
// Map 1's user: "remove sights from all ... primary guns base and pap ... make
// sure we dont break the ADS. Sometimes that happens." TOD II's rule is the same
// (no dots on packed forms, user 2026-09-15), and a sight removal is THREE edits
// per gun - see the noOptic() block in gen_tod_twins.js. Until docs/208 TOD II's
// noOptic() did only two of them and the packed Skye 870 aimed onto iron sights
// its own hideTags hid (`tag_sights`): "ADS onto bare metal", invisible in a hip
// screenshot. This gate pins all three on EVERY emitted variant of the Breacher's
// three guns, base and PaP:
//
//   A. no attachment slot references an optic model or mounts on an optic tag
//   B. no ADS animation is an optic animation
//   C. the PaP form's sight tags equal the base form's
//
// C is the one that catches a BROKEN ADS rather than a visible dot. It compares
// against the BASE FORM, never a hardcoded tag list, so a port update that
// legitimately renames a tag moves both halves together and stays green.
//
// The second half pairs EVERY packed form the generator emits with its base and
// holds the rules true for any gun whatever its optic policy (see below).
//   node tools/test_no_optics.js
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const ROOT = path.join(__dirname, '..');

// "sight" catches optic names like ..._sight_reflex; IRON sights are the one
// "sight" a no-optic gun is supposed to carry, so they are excluded.
const OPTIC = /reflex|reddot|red_dot|aimpoint|quickdot|snappoint|microflex|holo|acog|scope|elbit|susat|kobra|otero|(?<!iron_)sight/i;

// Tags a PaP form may hide that its base does not, with the reason. These are
// NOT sights - they are geometry a PaP-only attachment covers. None yet here.
const ATTACHMENT_TAGS = {};

// The Breacher's three primaries (the map's only guns with sights; the Archer's
// bows, the Warrior's blades and the Necromancer's staffs have none).
const GUNS = [
  { cls: 'breacher', tier: 1, stem: 'cc_mozambique' },
  { cls: 'breacher', tier: 2, stem: 'cc_rem870' },
  { cls: 'breacher', tier: 3, stem: 'cc_peacekeeper' },
];

const src = fs.readFileSync(path.join(ROOT, 'source_data/tod_weapon_twins.gdt'), 'latin1');
const blocks = new Map(
  [...src.matchAll(/"([^"\n]+)" \( "(?:bullet|projectile)weapon.gdf" \)\s*\{([\s\S]*?)\n\t\}/g)].map(
    m => [m[1], Object.fromEntries(
      [...m[2].matchAll(/"([^"\n]+)" "([^"\n]*)"/g)].map(f => [f[1], f[2]]))]));

const sightTags = f => new Set(
  (f.hideTags || '').split(/\\r\\n|\\n|\\r/).map(s => s.trim())
    .filter(Boolean).filter(t => !(t in ATTACHMENT_TAGS)));

let checked = 0, forms = 0;

for (const { cls, tier, stem } of GUNS) {
  const mine = [...blocks].filter(([n]) => n === stem || n.startsWith(stem + '_'));
  assert(mine.length > 0, `${cls} T${tier}: no emitted forms for ${stem} - did the ladder rename it?`);
  for (const [name, f] of mine) {
    forms++;
    const where = `${cls} T${tier} ${name}`;
    // A. no optic model, and no attachment mounted on an optic tag.
    for (const [key, val] of Object.entries(f)) {
      if (!/^attach(View|World)Model(Tag)?\d+$/.test(key) || !val) continue;
      assert(!OPTIC.test(val),
        `${where}: attachment ${key}="${val}" is an optic. Clear it through noOptic() in the generator.`);
    }
    // B. no optic ADS animation (it raises the gun to the optic's eye height).
    for (const key of ['adsUpAnim', 'adsDownAnim', 'adsFireAnim', 'adsLastShotAnim', 'adsUpOtherScopeAnim']) {
      const val = f[key];
      if (!val) continue;
      assert(!OPTIC.test(val),
        `${where}: ${key}="${val}" is an optic ADS animation - the ADS pose would aim above the irons.`);
    }
    // ADS itself must still work ("make sure we dont break the ADS").
    assert.equal(f.aimDownSight, '1', `${where}: aimDownSight is off - the gun cannot ADS at all.`);
    assert(f.adsUpAnim && f.adsDownAnim, `${where}: missing an ADS transition animation.`);
    // C. PaP sight tags == base sight tags, rung by rung.
    if (!name.includes('_up')) continue;
    let baseName = name.replace('_up', '');
    let base = blocks.get(baseName);
    if (!base) {
      const first = mine.find(([n]) => !n.includes('_up'));
      assert(first, `${where}: ${stem} emits no base form at all to compare sight tags against.`);
      [baseName, base] = first;
    }
    // An optic carries its own zoom; aiming down the base's irons, the PaP zooms like the base.
    for (const key of ['adsZoom1_focalLength', 'adsZoom1_fStop', 'adsZoom2_focalLength',
                       'adsZoom3_focalLength', 'adsZoomInFrac', 'adsZoomOutFrac', 'adsOverlayShader']) {
      assert.equal(f[key], base[key],
        `${where}: ${key}="${f[key]}" but ${baseName} has "${base[key]}" - that is an optic's ADS view on a gun with iron sights.`);
    }
    const up = sightTags(f), bs = sightTags(base);
    const hidden = [...up].filter(t => !bs.has(t));   // PaP hides a sight the base shows
    const shown = [...bs].filter(t => !up.has(t));    // PaP shows a sight the base hides
    assert.equal(hidden.length, 0,
      `${where}: hides ${hidden.join(', ')} but ${baseName} does not. ` +
      `The PaP borrows the base's ADS pose, so a sight the base aims down must be drawn here too. ` +
      `Pass the base's hideTags to noOptic(), or add the tag to ATTACHMENT_TAGS if a PaP attachment covers it.`);
    assert.equal(shown.length, 0,
      `${where}: shows ${shown.join(', ')} but ${baseName} hides it. With the optic gone that is bare mounting hardware.`);
    checked++;
  }
}
assert(forms >= 24, `only ${forms} Breacher forms matched - the stem names look stale against the ladder.`);

// ---------------------------------------------------------------------------
// THE WHOLE ROSTER: every packed form the generator emits, paired with its base:
//   1. the packed form can aim down sights whenever its base can (melee exempt);
//   2. an optic ADS animation needs an optic MODEL in an attachment slot;
//   3. a sight tag the base draws may be hidden by the packed form ONLY when an
//      optic model replaces it (map 1's MP7 / Mk 48 / HK21 bug, TOD II's 870);
//   4. a rail or mount tag the base hides may be shown by the packed form ONLY
//      when an optic model sits on it (map 1's MP5 bare rail);
//   5. without an optic, the packed form's ADS zoom and overlay equal the base's;
//   6. the packed form uses the base's first-person model (or its own _up twin,
//      or a listed packed model - MODEL_EXCEPT).
const OPTIC_ANIM  = /reflex|reddot|red_dot|aimpoint|quickdot|snappoint|microflex|holo|acog|scope|_elo_|otero|kobra|elbit|susat/i;
const OPTIC_MODEL = /reflex|reddot|aimpoint|quickdot|snappoint|microflex|holo|acog|scope|_elo$|_elo_|otero|kobra|elbit|susat/i;
const SIGHT_TAG   = /sight|iron|reticle/i;
const MOUNT_TAG   = /rail|mount|scope/i;
// The Breacher's packed forms wear their own PaP view models by design (docs/157), never an optic:
// the Mozambique its private PaP skin (tools install_breacher_apex.py), the Peacekeeper Hellbound's
// own packed model on its own packed ADS clips. Anything else that differs fails.
const MODEL_EXCEPT = {
  cc_mozambique: 'tod_bra_moz_pap_view',
  cc_peacekeeper: 'hb_am_peacekeeper_view',
};
const gen = fs.readFileSync(path.join(ROOT, 'tools/gen_tod_twins.js'), 'utf8');
const MELEE = new Set([...gen.matchAll(/stem: '([^']+)'[^\n]*melee: true/g)].map(m => m[1]));
for (const s of ['cc_punch', 'cc_gauntlet', 'cc_gold_sword']) MELEE.add(s);   // the Warrior's blades swing, they never aim
const tagSet = f => new Set((f.hideTags || '').split(/\\r\\n|\\n|\\r/).map(s => s.trim()).filter(Boolean));

let pairs = 0, withOptic = 0, exempt = 0;
const stemsPaired = new Set();
for (const [name, f] of blocks) {
  if (!name.includes('_up')) continue;
  const stem = name.slice(0, name.indexOf('_up'));
  const baseForms = [...blocks].filter(([n]) => (n === stem || n.startsWith(stem + '_')) && !n.includes('_up'));
  assert(baseForms.length > 0, `${name}: no base form for stem ${stem} - a packed gun with nothing to compare against.`);
  const same = baseForms.find(([n]) => n === name.replace('_up', ''));
  const [baseName, base] = same || baseForms[0];
  stemsPaired.add(stem);
  const where = `${stem}: ${name} vs ${baseName}`;
  const akimbo = f.dualWield === '1';
  const melee = MELEE.has(stem);
  const opticModels = Object.entries(f).filter(([k, v]) => /^attachViewModel\d+$/.test(k) && v && OPTIC_MODEL.test(v)).map(([, v]) => v);
  const hasOptic = opticModels.length > 0;
  const opticAnims = ['adsUpAnim', 'adsDownAnim', 'adsFireAnim', 'adsLastShotAnim'].filter(k => OPTIC_ANIM.test(f[k] || ''));
  if (akimbo || melee) {
    exempt++;
  } else {
    if (base.aimDownSight === '1') {
      assert.equal(f.aimDownSight, '1', `${where}: the packed form cannot aim down sights and its base can (rule 1).`);
      assert(f.adsUpAnim && f.adsDownAnim, `${where}: missing an ADS transition animation (rule 1).`);
    }
    assert(!opticAnims.length || hasOptic,
      `${where}: ${opticAnims.map(k => k + '="' + f[k] + '"').join(', ')} raise to an optic but no optic model is attached (rule 2).`);
    assert(f.gunModel === base.gunModel || f.gunModel === base.gunModel + '_up' || MODEL_EXCEPT[stem] === f.gunModel,
      `${where}: first-person model "${f.gunModel}" is neither the base's "${base.gunModel}" nor its _up twin (rule 6).`);
  }
  const up = tagSet(f), bs = tagSet(base);
  const hiddenSights = [...up].filter(t => !bs.has(t) && SIGHT_TAG.test(t));
  const shownMounts = [...bs].filter(t => !up.has(t) && MOUNT_TAG.test(t));
  assert(!hiddenSights.length || hasOptic,
    `${where}: hides ${hiddenSights.join(', ')} that the base draws, with no optic model replacing it (rule 3 - TOD II's packed 870 until docs/208).`);
  assert(!shownMounts.length || hasOptic,
    `${where}: shows ${shownMounts.join(', ')} that the base hides, with no optic sitting on it (rule 4).`);
  if (!hasOptic && !akimbo && !melee) {
    for (const key of ['adsZoom1_focalLength', 'adsZoom1_fStop', 'adsZoom2_focalLength',
                       'adsZoom3_focalLength', 'adsZoomInFrac', 'adsZoomOutFrac', 'adsOverlayShader']) {
      assert.equal(f[key], base[key],
        `${where}: ${key}="${f[key]}" but the base has "${base[key]}" - an optic's ADS view on a gun without one (rule 5).`);
    }
  }
  pairs++;
  if (hasOptic) withOptic++;
}
assert(pairs >= 40, `only ${pairs} packed forms paired - the generated GDT looks truncated.`);

console.log(`No-optic gate: ${forms} Breacher forms (Mozambique, 870, Peacekeeper) carry no optic model or optic ADS anim, ` +
            `all can ADS, and ${checked} PaP forms match their base form's sight picture. ` +
            `Roster: ${pairs} packed forms over ${stemsPaired.size} weapons paired with their base (${withOptic} carry an optic model, ` +
            `${exempt} melee/akimbo exempt from the ADS rules): no hidden sight without an optic, no bare rail, no optic pose without an optic. PASS.`);
