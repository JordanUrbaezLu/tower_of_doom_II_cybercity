#!/usr/bin/env node
// =============================================================================
// lint_tod_assets_selftest.js — break the map, require a catch.
//
// A lint nobody has watched FAIL is not a gate (CLAUDE.md: "a guard nobody has
// watched fire is not a guard"; memory `check-passes-wrong-question`). This
// copies the four sources lint_tod_assets.js reads into a scratch tree, injures
// one thing per case, and requires the lint to catch exactly that — plus a
// clean control that must stay green, and two SHAPE cases that must NOT fire
// (the false positives the lint shipped with for ten minutes on 2026-09-03:
// a concatenation prefix, and a one-image card).
//
//   node tools/lint_tod_assets_selftest.js
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

const REPO = path.resolve(__dirname, '..');
const LINT = path.join(__dirname, 'lint_tod_assets.js');
const SRC = {
  zone: 'zone_source/zm_tod2_cybercity.zone',
  upgrades: 'scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc',
  ui: 'scripts/zm/zm_tod2_cybercity/_tod_upgrade_ui.gsc',
  lua: 'ui/uieditor/menus/hud/tod_upgrade.lua',
  menu: 'ui/uieditor/menus/StartMenu/AetheriumStartMenu.lua',
  scoreboard: 'ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumScoreboard.lua',
};

// The whole ui/ tree is copied, not just the two Lua files the cases mutate:
// the lint's "unnamed" count is over EVERY Lua literal, so a partial copy makes
// images look unreferenced and every case regresses on that bucket alone.
function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, e.name), d = path.join(dst, e.name);
    if (e.isDirectory()) copyDir(s, d); else fs.copyFileSync(s, d);
  }
}
function freshTree() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tod_assets_selftest_'));
  for (const rel of [SRC.zone, SRC.upgrades, SRC.ui]) {
    const dst = path.join(root, rel);
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.copyFileSync(path.join(REPO, rel), dst);
  }
  copyDir(path.join(REPO, 'ui'), path.join(root, 'ui'));
  // 2026-09-09: the working-copy zone is CRLF (git normalises it to LF on
  // commit, so `git show HEAD:` hides that). Every zone mutation below deletes
  // "<line>\n", which never matched a CRLF line -- five "expected a catch"
  // failures that were the SELFTEST's, not the lint's. Normalise the scratch
  // copy; the lint's own ^image,(\S+) parse is line-ending agnostic.
  const zp = path.join(root, SRC.zone);
  fs.writeFileSync(zp, fs.readFileSync(zp, 'utf8').replace(/\r\n/g, '\n'));
  return root;
}
const rd = (root, key) => fs.readFileSync(path.join(root, SRC[key]), 'utf8');
const wr = (root, key, txt) => fs.writeFileSync(path.join(root, SRC[key]), txt);

// The lint gates GATE B on a baseline; the scratch tree has the same counts as
// the repo, so a case that ADDS a dead thing regresses and must fail.
function runLint(root) {
  // a case may plant a scratch baseline (root/_baseline.json) - the re-plate cases
  const sb = path.join(root, '_baseline.json');
  const args = [LINT, '--root', root].concat(fs.existsSync(sb) ? ['--baseline', sb] : []);
  const r = spawnSync(process.execPath, args, { encoding: 'utf8' });
  return { code: r.status, out: (r.stdout || '') + (r.stderr || '') };
}

const cases = [];
const add = (name, mustCatch, mutate, expect) => cases.push({ name, mustCatch, mutate, expect });

// ---- control ----------------------------------------------------------------
add('CONTROL: untouched tree', false, () => {}, null);

// 2026-09-28 (docs/187): DARK UPGRADES ARE RETIRED and a card has ONE face. The
// v17.10 text-only-Dark and DARK_NONE shapes tested a feature that can no longer
// be dealt; GATE R replaced them: any zoned card in a retired rarity, or a red
// pause plate while dark is off, is dead load RAM and fails.
add('GATE R: a zoned _super card (a retired rarity) fires', true, root => {
  wr(root, 'zone', rd(root, 'zone') + 'image,i_tod_card_luck_super\n');
}, /i_tod_card_luck_super[\s\S]*retired/);
add('GATE R: a zoned _dark card fires while dark upgrades are off', true, root => {
  wr(root, 'zone', rd(root, 'zone') + 'image,i_tod_card_bash_dark\n');
}, /i_tod_card_bash_dark[\s\S]*retired/);
add('GATE R: a zoned red pause plate fires while dark upgrades are off', true, root => {
  wr(root, 'zone', rd(root, 'zone') + 'image,i_tod_pause_r02_dark\n');
}, /i_tod_pause_r02_dark[\s\S]*retired/);

// ---- GATE D: retired with the V1 plate lists (R5, 2026-10-04) -----------------
// PAUSE_PLATE_MAX / TOD_UPG_PLATE_MAX left both screens with the i_tod_pause_rNN plates; nothing to drift.

// ---- GATE A: missing art ----------------------------------------------------
add('a zoned card image is deleted while its slug stays (WHITE SQUARE)', true, root => {
  const slug = [...rd(root, 'lua').matchAll(/\[(\d+)\]\s*=\s*"([a-z_0-9]+)"/g)]
    .map(m => m[2]).find(s => rd(root, 'zone').includes(`image,i_tod_card_${s}_regular`));
  wr(root, 'zone', rd(root, 'zone').replace(`image,i_tod_card_${slug}_regular\n`, ''));
}, /GATE A/);

add('a Lua literal names an image with no zone line', true, root => {
  wr(root, 'lua', rd(root, 'lua').replace(
    /(local CARD_SLUG\s*=\s*\{)/,
    'local NOPE = RegisterImage( "i_tod_totally_invented_image" )\n        $1'));
}, /i_tod_totally_invented_image/);

// The 8 TIER cards are built from TCLS, so NO literal names them. Before
// 2026-09-03 they were invisible to this lint entirely — not even in the
// advisory bucket — so deleting one was a white square nothing caught.
// R5 (2026-10-04): a class with layered card v2 (TodCardArt.lua `classes`) no longer registers its old
// tier cards. Take one class OUT of that table and the lint must demand its two baked tier cards again.
add('a class leaves card v2, so its old TIER cards are demanded (no literal names them)', true, root => {
  const p = path.join(root, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodCardArt.lua');
  fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replace(/heavy = true, /, ''));
}, /i_tod_card_tier_heavy_3/);

// THE GUN-HUD GLYPH SET, same blind spot one size larger (v17.9, docs/91).
// AetheriumLoadout.lua builds these names by concatenation — "i_tod_hud_d" .. c —
// so no Lua literal names them and a literal scan leaves them uncovered. The
// coverage reads tools/tod_hud_glyphs.generated.json, and the only honest way to
// know that coverage works is to DELETE one and require the lint to notice
// (memory: constructed-names-evade-inventory). Two shapes, because the set has
// two different constructions behind it: a typeface cell and a category cell.
add('a DIGIT glyph loses its zone line (built by concatenation)', true, root => {
  wr(root, 'zone', rd(root, 'zone').replace(/image,i_tod_hud_d7\n/, ''));
}, /i_tod_hud_d7/);

add('a GUN silhouette loses its zone line (built by concatenation)', true, root => {
  wr(root, 'zone', rd(root, 'zone').replace(/image,i_tod_hud_gun_mr6\n/, ''));
}, /i_tod_hud_gun_mr6/);

// ---- GATE B: dead weight (the v16.86 bug class) ------------------------------
add('a domain is retired but its CARD_SLUG slug stays (the v16.86 bug)', true, root => {
  // retire "luck" (id 4, universal, carded) by commenting out its add_domain,
  // leaving the slug. (Was "leech" until 2026-09-26, when leech was retired for
  // real by the Warrior card cut and the mutation became a no-op.)
  wr(root, 'upgrades', rd(root, 'upgrades').replace(/^(\s*)(add_domain\(\s*"luck")/m, '$1// Was: $2'));
}, /deadSlugs 0 -> 1|GATE B REGRESSION/);

add('a card is zoned that no slug declares', true, root => {
  wr(root, 'zone', rd(root, 'zone').replace(/^image,i_tod_card_bounty_regular$/m,
    'image,i_tod_card_bounty_regular\nimage,i_tod_card_ghostdomain_regular'));   // bounty: the damage card lines went with DAMAGE (2026-09-27)
}, /deadCards 0 -> 1|GATE B REGRESSION/);

// ---- GATE C: pause/scoreboard row capacity + the one-owner dark rule --------
// The bug this gate exists for (2026-09-04): the pause panel drew 2 x 7 = 14
// rows while every class could hold 15 or 16, so RIOT SHIELD was invisible on
// all four and the only complaint on screen was a "+N MORE" nobody reads. Both
// halves of the comparison are parsed, so the way to prove the gate works is to
// move either half — here the panel's own ROWS_MAX, back to what shipped.
const MENU = 'ui/uieditor/menus/StartMenu/AetheriumStartMenu.lua';
const SCORE = 'ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumScoreboard.lua';
const rdf = (root, rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const wrf = (root, rel, t) => fs.writeFileSync(path.join(root, rel), t);

add('the pause panel loses a row of capacity (the v17.10 riot-shield bug)', true, root => {
  // 2026-09-26: 7 rows (14 slots) no longer overflows any class after the Warrior
  // card cut (the biggest class holds 14); 5 rows (10 slots) does.
  // The lint takes the MAX over both presets (7 and 9), so both must drop.
  // 2026-09-26 (pause menu V2): the capacity is TOD_PAUSE_ROWS_CAP (12, the
  // user's per-class cap) while USE_PAUSE_V2 is on; 8 catches the Warrior's 9 (2026-09-27: DAMAGE /
  // PERK SLOTS / MELEE SPEED left, so the biggest class holds 9 rows).
  wrf(root, MENU, rdf(root, MENU).replace(/ROWS_MAX = (7|9)/g, 'ROWS_MAX = 4')
    .replace(/TOD_PAUSE_ROWS_CAP = \d+/, 'TOD_PAUSE_ROWS_CAP = 8'));   // 2026-09-28: the cap is 10 now; match any value
}, /GATE C/);

add('the SCOREBOARD loses a column of capacity', true, root => {
  // 2026-09-26: the gated-off Mage (14) no longer fails the gate, so losing ONE
  // column (18 -> 12) is caught by nobody; losing two (-> 6) is caught by every class.
  // Forces ONE column whatever the shipped value is (3 until 2026-09-26, 2 since), so the case never silently stops mutating.
  wrf(root, SCORE, rdf(root, SCORE).replace(/TOD_UPG_COLS\s*=\s*\d+/, 'TOD_UPG_COLS       = 1'));
}, /GATE C.*|SCOREBOARD/);

// A NEW DOMAIN IS THE OTHER HALF OF THE SAME COMPARISON, and the more likely
// one: nobody edits ROWS_MAX by accident, but add_domain gets called every few
// days. This is the case that will actually fire in anger one day.
add('a new universal domain pushes a class past the panel capacity', true, root => {
  let u = rd(root, 'upgrades');
  // Two extra universal domains take the 16-row classes to 18, one past the 18
  // the compact preset draws... so add three, and keep them off the art lanes
  // by reusing ids the lint already knows are dead (no CARD_SLUG is added).
  // 2026-09-26: the biggest class holds 14 rows after the Warrior card cut, so
  // it takes FIVE extras to pass 18.
  const extra = ['zz_one', 'zz_two', 'zz_three', 'zz_four', 'zz_five'].map(k =>
    `\tadd_domain( "${k}", "TEST ${k}", "test", 5, undefined, TOD_TIER_A );`).join('\n');
  u = u.replace(/^(\s*add_domain\(\s*"luck".*)$/m, `$1\n${extra}`);
  wr(root, 'upgrades', u);
}, /GATE C/);

add('a second Lua file builds an i_tod_pause_rNN_dark name itself', true, root => {
  wrf(root, SCORE, rdf(root, SCORE).replace(
    /(local TOD_UPG_COLS)/,
    'local BAD = string.format( "i_tod_pause_r%02d_dark", 1 )\n$1'));
}, /TodDarkPlate|GATE C/);

// ---- REUSED IDS (2026-09-26, docs/upgrade_ids.md) ---------------------------
// Ids 1..63 are all taken, so a new card reuses a retired number. 11 = ECHO
// ROUNDS (retired, its r11 plate still zoned; was 37 FORCED MARCH until 2026-09-27, when 37 became
// DEMOLITIONIST). The fixture card is PARKED so it never pushes a class past the 12-row cap. doReuse() performs the checklist; each case
// then forgets exactly one step.
const doReuse = (root, { textPlate = true, row = true, slug = false } = {}) => {
  wr(root, 'upgrades', rd(root, 'upgrades').replace(/(\n\tset_no_dark\( "retriever" \);)/,
    '\n\tadd_domain( "zz_reuse",   "ZZ REUSE", "selftest", 3, array( "parked" ), TOD_TIER_A );$1'));
  wr(root, 'ui', rd(root, 'ui').replace(/(\t\tcase "echo":)/, '\t\tcase "zz_reuse":    return 11;\n$1'));
  let lua = rd(root, 'lua');
  if (row) lua = lua.replace('[11] = { name = "ECHO ROUNDS"', '[11] = { name = "ZZ REUSE"');
  if (textPlate) lua = lua.replace(/CoD\.TodTextPlate = \{ /, 'CoD.TodTextPlate = { [11] = true, ');
  if (slug) lua = lua.replace(/(local CARD_SLUG\s*=\s*\{)/, '$1\n            [11] = "echo",');
  wr(root, 'lua', lua);
};
add('CONTROL: a retired id reused by the checklist is clean', false, root => doReuse(root), null);
add('a reused id keeps the old card slug (old card art)', true, root => doReuse(root, { slug: true }), /CARD_SLUG\[11\][\s\S]*REUSED/);
add('a reused id keeps the old Lua name row', true, root => doReuse(root, { row: false }), /DOMAIN\[11\]\.name/);
// WHEN THE NEW ART LANDS (2026-09-26): a NEW slug + a re-baked plate on a reused id is
// legal once DECLARED in the baseline's why.replatedIds (slug + drop zip + why).
const plantReplated = (root, decl) => {
  const bf = JSON.parse(fs.readFileSync(path.join(__dirname, 'lint_tod_assets.baseline.json'), 'utf8'));
  bf.why = bf.why || {};
  bf.why.replatedIds = Object.assign({}, bf.why.replatedIds || {}, decl);
  fs.writeFileSync(path.join(root, '_baseline.json'), JSON.stringify(bf, null, 2));
};
const newSlug = root => wr(root, 'lua', rd(root, 'lua').replace(/(local CARD_SLUG\s*=\s*\{)/, '$1\n            [11] = "zz_new_art",'));
add('CONTROL: a reused id with a NEW slug and a declared re-plate is clean', false, root => {
  doReuse(root, { textPlate: false }); newSlug(root);
  // the install itself: the new cards + the re-baked plate zoned, no dark rung
  wr(root, 'zone', rd(root, 'zone') + 'image,i_tod_card_zz_new_art_regular\n' + 'image,i_tod_pause_r37\n');   // docs/187: one face per upgrade
  wr(root, 'upgrades', rd(root, 'upgrades').replace(/(\n\tset_no_dark\( "retriever" \);)/, '$1\n\tset_no_dark( "zz_reuse" );'));
  wr(root, 'lua', rd(root, 'lua').replace(/(local DARK_NONE\s*=\s*\{)/, '$1\n            [11] = true,'));   // ...and its Lua mirror (the DARK_NONE rule)
  plantReplated(root, { "11": { slug: "zz_new_art", drop: "files - selftest.zip", why: "selftest: the new art landed" } });
}, null);
add('a reused id with a NEW slug but NO declaration still fires (card + plate)', true, root => {
  doReuse(root, { textPlate: false }); newSlug(root);
}, /CARD_SLUG\[11\][\s\S]*why\.replatedIds/);   // (the OLD-plate half went with the V1 plate lists, R5)
add('a declaration cannot launder a retired key\'s slug', true, root => {
  doReuse(root, { textPlate: false, slug: true });
  plantReplated(root, { "11": { slug: "echo", drop: "files - selftest.zip", why: "selftest: laundering attempt" } });
}, /CARD_SLUG\[11\] = "echo"[\s\S]*retired "echo"/);
add('two LIVE domains share one id', true, root => {
  wr(root, 'ui', rd(root, 'ui').replace(/case "bounty":\s*return 3;/, 'case "bounty":     return 2;'));   // collide with DMG REDUCTION (id 1 went dead with DAMAGE, 2026-09-27)
}, /2 LIVE domains/);

// ---- SHAPE: things that must NOT fire ---------------------------------------
add('SHAPE: a concatenation prefix is not an image name', false, root => {
  wr(root, 'lua', rd(root, 'lua').replace(
    /(local CARD_SLUG\s*=\s*\{)/,
    'local PFX = RegisterImage( "i_tod_made_up_prefix_" .. 7 )\n        $1'));
}, null);

add('SHAPE: a one-image card needs only its one rarity', false, root => {
  // add a one-image domain whose _regular/_super deliberately do not exist
  // (luck, id 4, since 2026-09-26; leech's lines are retired comments now)
  let lua = rd(root, 'lua');
  lua = lua.replace(/(local CARD_ONE_IMAGE\s*=\s*\{)/, '$1\n            [4] = "ultimate",');
  wr(root, 'lua', lua);
  let zone = rd(root, 'zone');
  zone = zone.replace(/^image,i_tod_card_luck_regular$/m, '')
             .replace(/^image,i_tod_card_luck_super$/m, '') + 'image,i_tod_card_luck_ultimate\n';   // docs/187 unzoned it; the one-image card brings it back
  wr(root, 'zone', zone);
}, null);

// ---- run --------------------------------------------------------------------
let pass = 0, fail = 0;
for (const c of cases) {
  const root = freshTree();
  c.mutate(root);
  const { code, out } = runLint(root);
  const caught = code !== 0;
  let ok = caught === c.mustCatch;
  if (ok && c.mustCatch && c.expect) ok = c.expect.test(out);
  if (ok) { pass++; console.log('  ok   ' + c.name); }
  else {
    fail++;
    console.log('  FAIL ' + c.name + `  (expected ${c.mustCatch ? 'a catch' : 'clean'}, exit ${code})`);
    console.log(out.split('\n').filter(l => l.trim()).slice(-6).map(l => '         ' + l).join('\n'));
  }
  fs.rmSync(root, { recursive: true, force: true });
}
console.log(`\nlint_tod_assets_selftest: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
