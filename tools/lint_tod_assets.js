#!/usr/bin/env node
// =============================================================================
// lint_tod_assets.js — the two gates on UI ART: nothing missing, nothing dead.
//
// WHY THIS EXISTS (2026-09-03, docs/86 §9). Zoned art has two failure modes on
// this map and NEITHER is visible at build time. Both have shipped:
//
//   1. MISSING — the Lua asks for an image with no `image,` line. The linker
//      says nothing (Lua is an opaque rawfile to it) and the game draws a
//      WHITE SQUARE. Live 2026-08-23 (the Mule Kick shader; memory
//      `usermap-asset-traps`). Retiring a domain by deleting only its zone
//      lines, while its slug stays in CARD_SLUG, is exactly this bug.
//
//   2. DEAD — the zone line stays after the thing that drew it is gone. The
//      image is packed into the .ff and decompressed at load. Cards are
//      `uncompressed` 768x1152, so ONE dead card is 3.4 MB of load-time RAM.
//      Live until v16.86: FOUR retired domains (11 echo_rounds, 12 regen,
//      30 meat_grinder, 34 momentum) still shipped 12 cards no deal could
//      ever roll — 40.5 MB of RAM. v16.80 had already established the fix
//      (retire the slug AND the zone lines together) for a fifth domain;
//      nothing enforced it, so four were simply forgotten.
//
// THE RULE THIS ENFORCES: **a card slug and its zone lines are ONE unit.**
// Retire both or neither. Same for a domain and its pause plate.
//
// WHAT IT PROVES. Sources are PARSED, never copied here — the id map comes out
// of `_tod_upgrade_ui.gsc::domain_id`, the live domain set out of the
// `add_domain(` calls in `_tod_upgrades.gsc` (commented `// Was:` lines do NOT
// count), the slugs out of the Lua's own CARD_SLUG, the plate ceiling out of
// PAUSE_PLATE_MAX. Rename any of them and this lint follows.
//
//   GATE A — MISSING (HARD FAIL, always): an image a live path can name but
//   the zone does not carry. Three sources: literal "i_tod_*" strings in
//   ui/**/*.lua; every CARD_SLUG slug x {regular,super,ultimate}; every LIVE
//   domain id <= PAUSE_PLATE_MAX as i_tod_pause_rNN.
//
//   GATE B — DEAD (gated on REGRESSION against the baseline, like
//   lint_tod_geometry.js): a CARD_SLUG entry whose id has no live domain; a
//   zoned card whose slug nothing declares; a zoned pause plate for a dead id;
//   and zoned i_tod_* art no Lua literal names. The last bucket is ADVISORY —
//   art can be reached by a constructed name this lint does not model — so it
//   is counted, not itemised into a failure. Never edit the baseline to make
//   this green: fix the art, or record WHY in the entry you add.
//
// OUT OF SCOPE (documented so nobody reads more into a pass than is there):
// materials (`material,` lines and their colorMap images — a different lane,
// GSC SetShader names the MATERIAL), images referenced only from GSC, and
// anything a Lua builds from a table this file does not parse. A pass means
// the modelled lanes are consistent, not that every image is reachable.
//
//   node tools/lint_tod_assets.js            gate (build runs this)
//   node tools/lint_tod_assets.js --report   list every finding, exit 0
//   node tools/lint_tod_assets.js --update-baseline
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const ZONE = path.join(REPO, 'zone_source', 'zm_tod2_cybercity.zone');
const UPGRADES = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_upgrades.gsc');
const UPGRADE_UI = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_upgrade_ui.gsc');
const LUA_DIR = path.join(REPO, 'ui');
// --baseline <path>: the selftest hands a scratch copy (with a planted why.replatedIds
// entry) so the re-plate rule can be proven both ways without touching the real file.
const _bIdx = process.argv.indexOf('--baseline');
const BASELINE = _bIdx >= 0 ? process.argv[_bIdx + 1] : path.join(__dirname, 'lint_tod_assets.baseline.json');

const argv = process.argv.slice(2);
const REPORT = argv.includes('--report');
const UPDATE = argv.includes('--update-baseline');
// --root lets the selftest point every path at a scratch copy of the tree.
const rootIdx = argv.indexOf('--root');
const ROOT = rootIdx >= 0 ? argv[rootIdx + 1] : REPO;
const P = rel => path.join(ROOT, rel);

// ---- source readers ---------------------------------------------------------
const read = f => { try { return fs.readFileSync(f, 'utf8'); } catch (e) { return ''; } };

// Lua comments would otherwise make every retired name look live: a retirement
// note ("-- the three i_tod_card_mobility_* lines are gone") names the very
// images it says are gone. Strip block comments then line comments.
function stripLua(txt) {
  return txt.replace(/--\[\[[\s\S]*?\]\]/g, '').replace(/--[^\n]*/g, '');
}
// GSC/C-style for the .gsc sources.
function stripGsc(txt) {
  return txt.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
}
function luaFiles(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) luaFiles(p, out);
    else if (e.name.toLowerCase().endsWith('.lua')) out.push(p);
  }
  return out;
}

// ---- parse ------------------------------------------------------------------
const zoneTxt = read(P('zone_source/zm_tod2_cybercity.zone'));
const zoned = new Set([...zoneTxt.matchAll(/^image,(\S+)/gm)].map(m => m[1]));

// live domains: add_domain( "key", ... ) with the call NOT commented out
const upgradesTxt = stripGsc(read(P('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc')));
const liveKeys = new Set([...upgradesTxt.matchAll(/\badd_domain\s*\(\s*"([a-z_0-9]+)"/g)].map(m => m[1]));

// id map: domain_id()'s switch cases
const uiTxt = stripGsc(read(P('scripts/zm/zm_tod2_cybercity/_tod_upgrade_ui.gsc')));
const idBlock = (uiTxt.match(/function\s+domain_id[\s\S]*?\n\}/) || [''])[0];
const keyToId = new Map();
for (const m of idBlock.matchAll(/case\s+"([a-z_0-9]+)"\s*:\s*return\s+(\d+)/g)) keyToId.set(m[1], +m[2]);
const liveIds = new Set([...liveKeys].map(k => keyToId.get(k)).filter(v => v !== undefined));
// REUSED IDS (2026-09-26): the field is 6 bits and 1..63 are all taken, so a new
// domain takes a RETIRED domain's number (docs/upgrade_ids.md). The old `case`
// line stays in domain_id() as history, so one id can have two keys: the LIVE
// key names it. Two LIVE keys on one id is a real collision (hard fail below).
const idToKey = new Map([...keyToId].map(([k, v]) => [v, k]));
for (const [k, v] of keyToId) if (liveKeys.has(k)) idToKey.set(v, k);
const idCollisions = [], reusedIds = new Map();   // id -> [live key, retired keys...]
{
  const byId = new Map();
  for (const [k, v] of keyToId) { if (!byId.has(v)) byId.set(v, []); byId.get(v).push(k); }
  for (const [id, keys] of byId) {
    if (keys.length < 2) continue;
    const live = keys.filter(k => liveKeys.has(k));
    if (live.length > 1) idCollisions.push(`domain_id() gives id ${id} to ${live.length} LIVE domains (${live.join(', ')}) - the HUD cannot tell them apart`);
    else if (live.length === 1) reusedIds.set(id, [live[0], ...keys.filter(k => k !== live[0])]);
  }
}
// 24 = the TIER card: dealt by tier_card_roll, never registered via add_domain.
const TIER_ID = keyToId.get('tier');
if (TIER_ID !== undefined) liveIds.add(TIER_ID);

// Lua sources
const luaPaths = luaFiles(P('ui'));
const luaClean = new Map();      // path -> comment-stripped text
for (const f of luaPaths) luaClean.set(f, stripLua(read(f)));

// CARD_SLUG: [id] = "slug"
const cardLuaPath = luaPaths.find(f => f.toLowerCase().endsWith(path.join('hud', 'tod_upgrade.lua').toLowerCase()))
  || luaPaths.find(f => /tod_upgrade\.lua$/i.test(f));
const cardLua = cardLuaPath ? luaClean.get(cardLuaPath) : '';
const slugBlock = (cardLua.match(/CARD_SLUG\s*=\s*\{[\s\S]*?\n\s*\}/) || [''])[0];
const cardSlug = new Map();
for (const m of slugBlock.matchAll(/\[(\d+)\]\s*=\s*"([a-z_0-9]+)"/g)) cardSlug.set(+m[1], m[2]);

// PAUSE_PLATE_MAX (declared in the start menu Lua)
let plateMax = 0;
for (const [, t] of luaClean) {
  const m = t.match(/PAUSE_PLATE_MAX\s*=\s*(\d+)/);
  if (m) plateMax = Math.max(plateMax, +m[1]);
}
// ...AND THE SCOREBOARD'S COPY (2026-09-10). AetheriumScoreboard.lua draws the
// same rows off its own TOD_UPG_PLATE_MAX, commented "LOCKSTEP" since v15 and
// never checked: it sat at 47 while the pause menu went to 56, so every row
// above 47 was a text label on the scoreboard with no red dark plate, for as
// long as those rows existed. A lockstep pair nothing
// checks is a pair that drifts. GATE D below fails the build on a mismatch.
let sbPlateMax = null;
for (const [f, t] of luaClean) {
  if (!/AetheriumScoreboard\.lua$/i.test(f)) continue;
  const m = t.match(/TOD_UPG_PLATE_MAX\s*=\s*(\d+)/);
  if (m) sbPlateMax = +m[1];
}

// Every literal i_tod_* the Lua names — but a literal followed by `..` is a
// PREFIX for a constructed name ("i_tod_badge_luck_" .. i * 10), not an image,
// and demanding a zone line for it would fail on art that is perfectly fine.
// Those constructed families are covered by the card/plate lanes below and by
// the advisory bucket, never by GATE A.
const luaLiterals = new Map();   // image -> [files]
const luaPrefixes = new Set();
for (const [f, t] of luaClean) {
  for (const m of t.matchAll(/["'](i_tod_[a-z0-9_]+)["'](\s*\.\.)?/g)) {
    // `..` right after it, or a trailing underscore (no image is named that
    // way; `cellImg( "i_tod_gauge_", "c", f )` concatenates inside the callee).
    if (m[2] || m[1].endsWith('_')) { luaPrefixes.add(m[1]); continue; }
    if (!luaLiterals.has(m[1])) luaLiterals.set(m[1], []);
    const arr = luaLiterals.get(m[1]);
    const rel = path.relative(ROOT, f).replace(/\\/g, '/');
    if (!arr.includes(rel)) arr.push(rel);
  }
}

// ONE-IMAGE DOMAINS: a domain locked to a single rarity ships ONE card file and
// the Lua fills all three slots with it (CARD_ONE_IMAGE, v16.67 DEADSHOT).
// Demanding _regular/_super for those would be a false failure.
const oneImage = new Map();      // id -> rarity
const oneBlock = (cardLua.match(/CARD_ONE_IMAGE\s*=\s*\{[\s\S]*?\n\s*\}/) || [''])[0];
for (const m of oneBlock.matchAll(/\[(\d+)\]\s*=\s*"([a-z]+)"/g)) oneImage.set(+m[1], m[2]);

// THE 8 TIER CARDS are built from a table, so no literal names them:
//   art.tier[c][t] = RegisterImage( "i_tod_card_tier_" .. TCLS[c] .. "_" .. t )
// They are LIVE — a player sees one on every tier promotion. Without this the
// lint would leave them in the advisory bucket, uncovered: a deleted zone line
// would be a white square nothing caught (raised by a peer session 2026-09-03
// before the baseline set, and it was right). Parsed, not hardcoded, and only
// required when the flag that registers them is on.
const tierCards = [];
{
  const on = /USE_TIER_CARD_ART\s*=\s*true/.test(cardLua);
  const tblM = cardLua.match(/TCLS\s*=\s*\{([^}]*)\}/);
  const loopM = cardLua.match(/for\s+t\s*=\s*(\d+)\s*,\s*(\d+)\s*do[\s\S]{0,400}?i_tod_card_tier_/);   // 400: R5's card-v2 guard lengthened the loop body
  // R5 (2026-10-04): a class listed in TodCardArt.lua `classes` deals layered card v2 (THE PULL draws its
  // tier card), so tod_upgrade.lua no longer registers its old baked tier cards and they left the zone.
  const v2 = new Set();
  const artLua = luaPaths.find(f => /TodCardArt\.lua$/i.test(f));
  if (artLua) {
    const cm = luaClean.get(artLua).match(/classes\s*=\s*\{([^}]*)\}/);
    if (cm) for (const k of cm[1].matchAll(/([a-z_0-9]+)\s*=\s*true/g)) v2.add(k[1]);
  }
  if (on && tblM && loopM) {
    const classes = [...tblM[1].matchAll(/"([a-z_0-9]+)"/g)].map(m => m[1]).filter(c => !v2.has(c));
    for (const c of classes)
      for (let t = +loopM[1]; t <= +loopM[2]; t++) tierCards.push(`i_tod_card_tier_${c}_${t}`);
  }
}

// THE GUN-HUD GLYPH SET (v17.9, docs/91) — the same blind spot as the tier
// cards, one size larger. AetheriumLoadout.lua builds every one of these names
// by concatenation: "i_tod_hud_d" .. c for a numeral, "i_tod_hud_l" .. lower(c)
// for a letter, "i_tod_hud_gun_" .. category for the weapon silhouette. A
// Lua-LITERAL scan cannot see any of them, so without this they sit in the
// advisory bucket and a deleted zone line is a WHITE SQUARE in the middle of the
// ammo counter that nothing catches.
//
// The list is READ FROM GENERATED DATA, not hardcoded here: tools/
// slice_hud_sheets.js writes tod_hud_glyphs.generated.json from the same SHEETS
// table it cuts the cells with, so adding a cell covers itself and a skipped
// cell (the ampersand) is absent from both at once.
//
// Read from __dirname, NOT from ROOT. The manifest is a toolchain artifact that
// lives beside this lint, not map content — and --root points the selftest at a
// scratch COPY of the map tree that has no tools/ directory at all. Resolving it
// against ROOT made three selftest shapes fail with a phantom unnamed 209 -> 257
// regression, which is the lint reporting on its own missing file rather than on
// anything the shape changed.
const hudGlyphs = [];
{
  const p = path.join(__dirname, 'tod_hud_glyphs.generated.json');
  if (fs.existsSync(p)) {
    try { hudGlyphs.push(...(JSON.parse(fs.readFileSync(p, 'utf8')).images || [])); } catch (e) {}
  }
}

// ONE FACE PER UPGRADE (docs/187, 2026-09-28): the rarity (COMMON / RARE / EPIC /
// LEGENDARY) is drawn LIVE by TodPull.lua over one image per upgrade, so a card
// owes ONE file. Until the rarity-neutral faces land, that file is the old
// _regular art. A zoned _super/_ultimate card is dead load RAM (GATE R below).
const RARITIES = ['regular'];
// DARK UPGRADES ARE RETIRED (docs/187) while TOD_DARK_ENABLED is 0. Every dark
// check below is gated on these; with them off, a zoned _dark card or red pause
// plate is dead load RAM and GATE R fails it.
const darkDealt = /#define\s+TOD_DARK_ENABLED\s+1(?!\d)/.test(upgradesTxt);
const darkCardsOn = darkDealt && /USE_DARK_CARD_ART\s*=\s*true/.test(cardLua);
const darkPlatesOn = darkDealt && /USE_DARK_PLATE_ART\s*=\s*true/.test(cardLua);
// DARK UPGRADES (v17.10): a FOURTH rarity, but only for the domains that can be
// dealt one. set_no_dark( "key" ) in _tod_upgrades.gsc is the exception list and
// is parsed here rather than copied, exactly like add_domain above -- a hand-kept
// mirror of it is the thing that goes stale and then passes while lying.
const noDarkKeys = new Set([...upgradesTxt.matchAll(/^\s*set_no_dark\s*\(\s*"([a-z_0-9]+)"/gm)].map(m => m[1]));
const noDarkIds = new Set([...noDarkKeys].map(k => keyToId.get(k)).filter(v => v !== undefined));
// Enabled text-only Dark cards neither register an image nor reuse Ultimate
// art. Honor this exception only while both routing guards are present.
const darkTextBlock = (cardLua.match(/DARK_TEXT_ONLY\s*=\s*\{([^}]*)\}/) || [,''])[1];
const darkTextIds = new Set([...darkTextBlock.matchAll(/\[\s*(\d+)\s*\]\s*=\s*true/g)].map(m => +m[1]));
const darkTextSafe = /not DARK_NONE\[ id \] and not DARK_TEXT_ONLY\[ id \]/.test(cardLua)
  && /if isDark and not darkImg then\s+set = nil/.test(cardLua);
// THE V1 OWNED-UPGRADES PLATE LISTS LEFT (R5, 2026-10-04): the pause menu (USE_PAUSE_V2) and the scoreboard
// V2 draw the rows from i_tod_pm_* art, so PAUSE_PLATE_MAX / TOD_UPG_PLATE_MAX, CoD.TodTextPlate and
// DARK_PLATE_NONE left the Lua with the i_tod_pause_rNN plates. plateMax now reads 0, which leaves the
// plate lanes below (GATE A plates, GATE D, the re-plate check) dormant; the deadPlates bucket stays as the
// guard against a retired plate coming back into the zone.
const darkPlateNone = new Set();
const pad2 = n => String(n).padStart(2, '0');
const textPlate = new Set();

// ---- GATE A: missing (hard fail) --------------------------------------------
const missing = [];
for (const [img, files] of luaLiterals)
  if (!zoned.has(img)) missing.push(`${img} — named in ${files.join(', ')} but NO zone line (draws a WHITE SQUARE)`);
for (const [id, slug] of cardSlug) {
  const rars = oneImage.has(id) ? [oneImage.get(id)] : RARITIES;
  for (const r of rars) {
    const img = `i_tod_card_${slug}_${r}`;
    if (!zoned.has(img)) missing.push(`${img} — CARD_SLUG[${id}] = "${slug}"${oneImage.has(id) ? ' (one-image, ' + oneImage.get(id) + ')' : ''} but NO zone line (white square when that card is dealt)`);
  }
}
for (const [id, slug] of cardSlug) {
  if (!darkCardsOn) break;
  if (!liveIds.has(id) || noDarkIds.has(id) || (darkTextSafe && darkTextIds.has(id))) continue;
  const img = `i_tod_card_${slug}_dark`;
  if (!zoned.has(img)) missing.push(`${img} — domain "${idToKey.get(id)}" (id ${id}) is live and has no set_no_dark(), so a DARK card can be dealt for it, but there is NO zone line (white square on that dark deal)`);
}
// DARK_NONE IS THE LUA MIRROR OF set_no_dark() (2026-09-26, the user's build-6
// log: "Could not find image i_tod_card_retriever_dark / pellets_dark /
// sticky_c4_dark / cluster_dark"). tod_upgrade.lua RegisterImage()s
// i_tod_card_<slug>_dark for EVERY CARD_SLUG id that is not in DARK_NONE (or a
// guarded DARK_TEXT_ONLY). The check above skips set_no_dark ids - right about the
// DEAL, blind to the REGISTRATION - so four no-dark cards missing from DARK_NONE
// asked the .ff for images it never had, and nothing failed. Both directions:
//   (a) set_no_dark + CARD_SLUG but NOT in DARK_NONE -> the Lua registers a dark
//       card that is not zoned (and can never be dealt);
//   (b) in DARK_NONE but its _dark card IS zoned -> ~3.4 MB of load RAM nothing
//       will ever draw (the v18.42 lesson: a retired card id 52 paid for one).
const darkNone = new Set();
{
  const m = cardLua.match(/DARK_NONE\s*=\s*\{([^}]*)\}/);
  if (m) for (const k of m[1].matchAll(/\[\s*(\d+)\s*\]\s*=\s*true/g)) darkNone.add(Number(k[1]));
  else console.error('lint_tod_assets: WARN - no DARK_NONE table in tod_upgrade.lua; the set_no_dark mirror check is skipped.');
}
for (const [id, slug] of cardSlug) {
  if (!darkCardsOn) break;
  const img = `i_tod_card_${slug}_dark`;
  const textOnly = darkTextSafe && darkTextIds.has(id);
  if (noDarkIds.has(id) && !darkNone.has(id) && !textOnly && !zoned.has(img))
    missing.push(`${img} — "${idToKey.get(id)}" (id ${id}) is set_no_dark() but NOT in tod_upgrade.lua DARK_NONE, so the Lua RegisterImage()s a dark card the .ff does not carry ("Could not find image" at load). Add [${id}] = true to DARK_NONE`);
  if (darkNone.has(id) && zoned.has(img))
    missing.push(`${img} — id ${id} is in DARK_NONE (never registered, never drawn) but its dark card is ZONED: ~3.4 MB of load RAM for nothing. Unzone it, or take [${id}] out of DARK_NONE if the card is real`);
}
for (const img of tierCards)
  if (!zoned.has(img)) missing.push(`${img} — built by tod_upgrade.lua's TCLS loop under USE_TIER_CARD_ART, but NO zone line (white square on that tier promotion)`);
for (const img of hudGlyphs)
  if (!zoned.has(img)) missing.push(`${img} — gun-HUD art (tools/tod_hud_glyphs.generated.json), named by concatenation in AetheriumLoadout.lua, but NO zone line (white square in the bottom-right readout)`);
// REUSE + NAME CHECKS (2026-09-26). A reused id must not inherit the old
// domain's art: no CARD_SLUG (the old card), a text plate (the old plate names
// the old card), and the Lua DOMAIN row must carry the NEW name. The name
// check runs for every live domain: the add_domain display and DOMAIN[id].name
// are one fact in two files, and a reuse that forgets the Lua row shows the
// retired card's name on the new card.
for (const c of idCollisions) missing.push(c);
// WHEN THE NEW ART LANDS (2026-09-26, the Necromancer's 38 / 39). A reused id may
// carry a CARD_SLUG and a real rNN plate once the NEW domain's art is installed:
// the new cards under a NEW slug, the plate FILE overwritten with the new art under
// the same name. The plate name cannot tell old art from new, so that state is
// DECLARED - dated, reasoned, naming the drop zip - in the baseline's why block:
//   why.replatedIds = { "<id>": { "slug": "<new slug>", "drop": "<zip>", "why": "..." } }
// Two things the declaration can never launder: a slug that matches a RETIRED key of
// that id (derived from domain_id()'s history lines, never hand-typed) is the old
// card's art whatever is declared, and a declaration missing slug / drop / why counts
// as none. (`why` is carried forward by --update-baseline, so the entry survives it.)
let REPLATED = {};
try { const bf = JSON.parse(fs.readFileSync(BASELINE, 'utf8')); REPLATED = (bf.why && bf.why.replatedIds) || {}; } catch (e) {}
const replatedDecl = id => {
  const d = REPLATED[String(id)];
  return ( d && typeof d === 'object' && d.slug && d.drop && d.why ) ? d : null;
};
for (const [id, keys] of reusedIds) {
  const retired = keys.slice(1);
  const decl = replatedDecl(id);
  if (cardSlug.has(id)) {
    const slug = cardSlug.get(id);
    const oldKey = retired.find(k => slug === k || slug.startsWith(k + '_') || k.startsWith(slug));
    if (oldKey) missing.push(`CARD_SLUG[${id}] = "${slug}" - id ${id} is REUSED by "${keys[0]}" (was ${retired.join(', ')}): "${slug}" is the retired "${oldKey}" card's art. Remove it until the new card art lands`);
    else if (!decl || decl.slug !== slug) missing.push(`CARD_SLUG[${id}] = "${slug}" - id ${id} is REUSED by "${keys[0]}" (was ${retired.join(', ')}): a new slug on a reused id must be declared in the baseline's why.replatedIds (slug + drop zip + why) when its art lands`);
  }
  if (plateMax && id <= plateMax && !textPlate.has(id) && !decl) missing.push(`id ${id} is REUSED by "${keys[0]}" (was ${retired.join(', ')}) but is not in CoD.TodTextPlate: the pause menu / scoreboard would draw the OLD plate i_tod_pause_r${pad2(id)} (or declare the re-baked plate in the baseline's why.replatedIds)`);
}
{
  const domBlock = (cardLua.match(/\nlocal DOMAIN\s*=\s*\{[\s\S]*?\n\}/) || [''])[0];
  const luaNames = new Map();
  for (const m of domBlock.matchAll(/^\s*\[(\d+)\]\s*=\s*\{\s*name\s*=\s*"([^"]*)"/gm)) luaNames.set(+m[1], m[2]);
  for (const m of upgradesTxt.matchAll(/\badd_domain\s*\(\s*"([a-z_0-9]+)"\s*,\s*"([^"]*)"/g)) {
    const id = keyToId.get(m[1]);
    if (id === undefined) { console.error(`lint_tod_assets: WARN - add_domain "${m[1]}" has no case in domain_id() (the HUD would receive id 0)`); continue; }
    if (domBlock && luaNames.get(id) !== m[2]) missing.push(`DOMAIN[${id}].name in tod_upgrade.lua is "${luaNames.get(id)}" but add_domain "${m[1]}" says "${m[2]}" - the card shows the wrong name`);
  }
}
for (const id of [...liveIds].sort((a, b) => a - b)) {
  if (!plateMax || id > plateMax || textPlate.has(id)) continue;
  const img = `i_tod_pause_r${pad2(id)}`;
  if (!zoned.has(img)) missing.push(`${img} — domain "${idToKey.get(id)}" (id ${id}) is LIVE and <= PAUSE_PLATE_MAX ${plateMax}, but NO zone line`);
  // DARK UPGRADES (v17.10): a dark-capable domain also owes its RED plate. The
  // name is built by concatenation in AetheriumStartMenu.lua under
  // USE_DARK_PLATE_ART, so no Lua literal exists for the literal lane to find.
  // DARK_PLATE_NONE in AetheriumStartMenu.lua lists the ids that deliberately
  // fall back to the runtime tint because no red plate was baked for them.
  // PARSED, not copied — same rule as every other fact in this file.
  if (!darkPlatesOn || noDarkIds.has(id) || id === TIER_ID || darkPlateNone.has(id)) continue;
  const dimg = `i_tod_pause_r${pad2(id)}_dark`;
  if (!zoned.has(dimg)) missing.push(`${dimg} — domain "${idToKey.get(id)}" (id ${id}) can hold a DARK upgrade, so the pause menu asks for its red plate, but there is NO zone line (white square in the pause list)`);
}

// ---- GATE R: retired rarities (HARD FAIL) -------------------------------------
// docs/187: a card has ONE face, and dark upgrades are retired. Any zoned card in
// a retired rarity, or a red pause plate while dark is off, is load RAM that
// nothing can draw. (CARD_ONE_IMAGE domains keep the one file they name.)
for (const img of zoned) {
  let m = img.match(/^i_tod_card_(.+)_(super|ultimate|dark)$/);
  if (m) {
    const slug = m[1], r = m[2];
    if (/^(tier|class)(_|$)/.test(slug)) continue;
    if (r === 'dark' && darkCardsOn) continue;
    let keep = false;
    for (const [id, sl] of cardSlug) if (sl === slug && oneImage.get(id) === r) keep = true;
    if (!keep) missing.push(`${img} — rarity "${r}" is retired (docs/187: one face per upgrade${r === 'dark' ? ', dark upgrades off' : ''}); unzone it`);
    continue;
  }
  m = img.match(/^i_tod_pause_r\d+_dark$/);
  if (m && !darkPlatesOn) missing.push(`${img} — dark upgrades are retired (docs/187); the red pause plate can never draw. Unzone it`);
}

// ---- GATE C: pause-menu row capacity (HARD FAIL, always) --------------------
//
// The pause menu's YOUR UPGRADES panel draws a fixed number of rows and
// SILENTLY DROPS the rest behind a "+N MORE" line. Rows render in ascending
// domain id, so overflow always eats the NEWEST domains — which is how RIOT
// SHIELD (id 45) was invisible for every class from 2026-09-02 to 2026-09-04,
// and FULL STEAM for the heavy on top of it. Nobody reads "+2 MORE".
//
// A ROW BUDGET IS NOT A COMMENT. It moves every time add_domain is called, and
// the comment that claimed "the true ceiling is 14 rows" had been stale for two
// days before a player noticed. Both halves are PARSED here: the reachable set
// per class off add_domain's own class_keys argument, and the panel's capacity
// off its ROWS_MAX declarations (the base preset and the compact one; the
// larger wins, since the panel picks it for exactly this case).
const CLASSES = ['necromancer', 'assault', 'heavy', 'slasher'];   // the four drafted classes (2026-10-04)
const perClass = new Map(CLASSES.map(c => [c, []]));
// add_domain( key, display, desc, max, class_keys, ... ) — the 5th argument is
// either `undefined` (universal) or `array( "cls", ... )`.
for (const m of upgradesTxt.matchAll(
  /\badd_domain\s*\(\s*"([a-z_0-9]+)"\s*,\s*"([^"]*)"\s*,\s*"(?:[^"\\]|\\.)*"\s*,\s*\d+\s*,\s*(undefined|array\s*\([^)]*\))/g)) {
  const [, key, display, scope] = m;
  for (const c of CLASSES)
    if (scope === 'undefined' || scope.includes('"' + c + '"'))
      perClass.get(c).push({ id: keyToId.get(key), key, display });
}
// BOTH SCREENS, not just the pause menu. The scoreboard (AetheriumScoreboard)
// draws the same CoD.TodOwned on its own grid and DROPS ID 24, so its budget is
// one lower and its capacity is a different pair of numbers. Checking only the
// one that broke first is how the second one gets found by a player.
let rowsMax = 0;
for (const [, t] of luaClean)
  for (const m of t.matchAll(/ROWS_MAX\s*=\s*(\d+)/g)) rowsMax = Math.max(rowsMax, +m[1]);
// [2026-09-26, pause menu V2] THE CAP IS THE USER'S NUMBER, NOT A LAYOUT ACCIDENT
// ("a class can only have 12 upgrades max. That needs to be defined"). When the
// pause menu declares TOD_PAUSE_ROWS_CAP (and USE_PAUSE_V2 is on), THAT is the
// capacity: the V2 panel draws one fixed 2 x 6 grid and no compact preset, so the
// old ROWS_MAX declarations (7 / 9) describe the flag-off layout only.
let pauseCap = 0;
{
  const pm = [...luaClean].find(([f]) => /AetheriumStartMenu\.lua$/i.test(f));
  if (pm && /USE_PAUSE_V2\s*=\s*true/.test(pm[1])) {
    const m = pm[1].match(/TOD_PAUSE_ROWS_CAP\s*=\s*(\d+)/);
    if (m) pauseCap = +m[1];
  }
}
const sbTxt = [...luaClean].find(([f]) => /AetheriumScoreboard\.lua$/i.test(f));
const sbNum = (re) => { const m = sbTxt && sbTxt[1].match(re); return m ? +m[1] : 0; };
const sbCap = sbNum(/TOD_UPG_ROWS_COL\s*=\s*(\d+)/) * sbNum(/TOD_UPG_COLS\s*=\s*(\d+)/);
const PANELS = [
  { name: 'pause menu', cap: pauseCap || rowsMax * 2, tier: true,
    how: pauseCap ? `TOD_PAUSE_ROWS_CAP ${pauseCap}, the user's 12-upgrade class cap` : `2 columns x ROWS_MAX ${rowsMax}`,
    where: 'ui/uieditor/menus/StartMenu/AetheriumStartMenu.lua' },
  { name: 'scoreboard', cap: sbCap, tier: false,
    how: 'TOD_UPG_COLS x TOD_UPG_ROWS_COL', where: 'ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumScoreboard.lua' },
];
const overCap = [];
const classRowCounts = [];
for (const panel of PANELS) {
  if (!panel.cap) continue;
  for (const c of CLASSES) {
    // +1 for the CLASS TIER row (id 24), which refresh_upgrade_list sends for
    // every drafted player and which add_domain therefore never declares. The
    // scoreboard skips that row, so it is added only where it is drawn.
    const rows = (panel.tier
      ? perClass.get(c).concat([{ id: TIER_ID, key: 'tier', display: 'CLASS TIER' }])
      : perClass.get(c).slice())
      .sort((a, b) => (a.id || 0) - (b.id || 0));
    if (panel.tier) classRowCounts.push(`${c} ${rows.length}`);
    if (rows.length > panel.cap)
      overCap.push(`${panel.name.toUpperCase()} / ${c.toUpperCase()}: ${rows.length} rows but the panel draws ${panel.cap} ` +
        `(${panel.how}) — DROPPED: ` +
        rows.slice(panel.cap).map(r => `${r.id}:${r.display}`).join(', ') + ` [${panel.where}]`);
  }
}

// ONE OWNER FOR THE DARK PLATE RULE. The name i_tod_pause_rNN_dark may only be
// built inside CoD.TodDarkPlate (tod_upgrade.lua). The scoreboard printed dark
// VALUES under an ordinary blue plate for a whole version because the pause
// menu's copy of the rule was a local — a rule written down twice is a rule one
// screen will be a version behind on, and nothing failed to say so.
for (const [f, t] of luaClean) {
  if (/tod_upgrade\.lua$/i.test(f)) continue;
  if (/_dark"/.test(t) || /_dark'/.test(t))
    overCap.push(`${path.relative(P('.'), f)} builds an i_tod_pause_rNN_dark name itself — ` +
      `call CoD.TodDarkPlate( id, plateMax ) instead; it owns the art flag AND the not-yet-baked list`);
}

// ---- GATE B: dead (baseline-gated) ------------------------------------------
const deadSlugs = [];
for (const [id, slug] of cardSlug)
  if (!liveIds.has(id))
    deadSlugs.push(`CARD_SLUG[${id}] = "${slug}" — no live add_domain for id ${id} (key "${idToKey.get(id) || '?'}"), so no deal can roll it; its 3 cards are dead weight in the .ff`);

// zoned cards whose slug nothing declares. tier_/class_ are built from their own
// tables (art.tier, tod_class_select) and are covered by the literal lane.
const declaredSlugs = new Set(cardSlug.values());
const deadCards = [];
for (const img of zoned) {
  const m = img.match(/^i_tod_card_(.+)_(regular|super|ultimate|dark)$/);
  if (!m) continue;
  const slug = m[1];
  if (declaredSlugs.has(slug)) continue;
  if (/^(tier|class)(_|$)/.test(slug)) continue;
  if (luaLiterals.has(img)) continue;
  deadCards.push(`${img} — no CARD_SLUG entry declares slug "${slug}"`);
}
const deadPlates = [];
for (const img of zoned) {
  const m = img.match(/^i_tod_pause_r(\d+)$/);
  if (!m) continue;
  const id = +m[1];
  if (liveIds.has(id) || luaLiterals.has(img)) continue;
  deadPlates.push(`${img} — no live domain has id ${id} (key "${idToKey.get(id) || 'unmapped'}")`);
}
// advisory bucket: zoned art no Lua literal names and no family above explains
const unnamed = [];
const tierSet = new Set(tierCards);
const hudSet = new Set(hudGlyphs);
for (const img of zoned) {
  if (luaLiterals.has(img)) continue;
  if (tierSet.has(img)) continue;          // covered by GATE A above, not advisory
  if (hudSet.has(img)) continue;           // ditto — the gun-HUD glyph set
  if (/^i_tod_card_/.test(img) || /^i_tod_pause_r\d+(_dark)?$/.test(img)) continue;
  // The over-head health bars (docs/174) are server HUDELEM materials drawn from GSC
  // (_tod_elite_hp.gsc SetShader), never named in Lua: e/b = the RED elite + boss
  // bars, s = the WHITE Necromancer-helper bars (2026-10-01). Their whole lane —
  // precache list = GDT = zone = PNGs — is gated by tools/test_elite_hp.js, so
  // they are covered, not advisory.
  if (/^i_tod_hpbar_[ebs]_\d\d(_h[12])?$/.test(img)) continue;
  unnamed.push(img);
}

// ---- report / gate ----------------------------------------------------------
const counts = { deadSlugs: deadSlugs.length, deadCards: deadCards.length, deadPlates: deadPlates.length, unnamed: unnamed.length };
let baseFile = {};
if (fs.existsSync(BASELINE)) { try { baseFile = JSON.parse(fs.readFileSync(BASELINE, 'utf8')); } catch (e) {} }
const base = baseFile.counts || { deadSlugs: 0, deadCards: 0, deadPlates: 0, unnamed: 0 };

if (UPDATE) {
  // The `why` block is the whole discipline of this baseline — it says which
  // numbers are ACCEPTED and on what grounds. An update that silently wiped it
  // would turn the next reader's "just re-baseline" into exactly the unrecorded
  // bump this file exists to prevent, so it is CARRIED FORWARD. Numbers that
  // went UP are called out for you to justify.
  const raised = Object.keys(counts).filter(k => counts[k] > (base[k] ?? 0));
  fs.writeFileSync(BASELINE, JSON.stringify({
    note: baseFile.note || 'Regression baseline for lint_tod_assets.js GATE B. Lower is better. NEVER raise a number to make the lint green - fix the art, or replace this note with the reason the new number is correct. GATE A (missing art) has no baseline: it is always a hard fail.',
    updated: new Date().toISOString().slice(0, 10),
    why: baseFile.why || undefined,
    counts,
  }, null, 2) + '\n');
  console.log('baseline updated: ' + JSON.stringify(counts));
  if (baseFile.why) console.log('  (the "why" block was carried forward — update the entries for any number that moved)');
  if (raised.length) console.log('  RAISED: ' + raised.map(k => `${k} ${base[k]} -> ${counts[k]}`).join(', ') + ' — record WHY in the baseline, or this is dead weight nobody will question again.');
  process.exit(0);
}

const show = (label, arr) => { if (!arr.length) return; console.log(`\n${label} (${arr.length}):`); for (const f of arr) console.log('  * ' + f); };

if (missing.length) {
  console.error('\nlint_tod_assets: GATE A — MISSING ART (' + missing.length + ')');
  for (const f of missing) console.error('  * ' + f);
}
const plateDrift = [];
if (sbPlateMax !== null && plateMax && sbPlateMax !== plateMax)
  plateDrift.push(`AetheriumScoreboard.lua TOD_UPG_PLATE_MAX ${sbPlateMax} != AetheriumStartMenu.lua PAUSE_PLATE_MAX ${plateMax} — rows ${Math.min(sbPlateMax, plateMax) + 1}..${Math.max(sbPlateMax, plateMax)} draw a plate on one screen and a text label on the other`);
if (plateDrift.length) {
  console.error('\nlint_tod_assets: GATE D — PLATE CEILING DRIFT BETWEEN THE TWO OWNED-UPGRADES SCREENS');
  for (const f of plateDrift) console.error('  * ' + f);
  console.error('  The pause menu and the scoreboard read one CoD.TodOwned and must agree on which ids have baked plates.');
}
if (overCap.length) {
  console.error('\nlint_tod_assets: GATE C — PAUSE ROWS OVER CAPACITY (' + overCap.length + ')');
  for (const f of overCap) console.error('  * ' + f);
  console.error('  Raise ROWS_MAX (and the row metrics that make the rows fit) in');
  console.error('  ui/uieditor/menus/StartMenu/AetheriumStartMenu.lua. Do NOT let it ride on "+N MORE".');
}
if (REPORT) {
  show('GATE B — dead CARD_SLUG entries', deadSlugs);
  show('GATE B — dead zoned cards', deadCards);
  show('GATE B — dead zoned pause plates', deadPlates);
  console.log(`\nadvisory — zoned i_tod_* no Lua literal names (${unnamed.length}); a constructed name may still reach these:`);
  for (const i of unnamed.sort()) console.log('    ' + i);
}

const regressed = Object.keys(counts).filter(k => counts[k] > base[k]);
if (regressed.length && !REPORT) {
  console.error('\nlint_tod_assets: GATE B REGRESSION — ' +
    regressed.map(k => `${k} ${base[k]} -> ${counts[k]}`).join(', '));
  console.error('  Retiring a domain? Remove its CARD_SLUG slug AND its zone lines together (the v16.80/v16.86 pattern).');
  console.error('  Run with --report to see them. Fix the art; do not raise the baseline to hide it.');
}

console.log(`\nassets: ${zoned.size} zoned image(s), ${cardSlug.size} card slug(s), ` +
  `${liveIds.size} live domain id(s), plate ceiling ${plateMax}; ` +
  `dead slugs ${counts.deadSlugs}/${base.deadSlugs}, dead cards ${counts.deadCards}/${base.deadCards}, ` +
  `dead plates ${counts.deadPlates}/${base.deadPlates}, unnamed ${counts.unnamed}/${base.unnamed} (now/baseline); ` +
  `pause rows ${classRowCounts.join(' / ')} vs capacity ${pauseCap || rowsMax * 2} (scoreboard ${sbCap}, tier row excluded)`);

process.exit((missing.length || overCap.length || plateDrift.length || (regressed.length && !REPORT)) ? 1 : 0);
