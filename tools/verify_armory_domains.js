#!/usr/bin/env node
// =============================================================================
// verify_armory_domains.js — audit docs/armory.html's DOMAINS array against the
// SHIPPING GSC, field by field.
//
// WHY THIS EXISTS. tools/verify_armory_constants.js already checks the `tune:`
// strings against #defines, and it earns its keep — but it only sees values
// spelled as `NAME 0.05` inside that one field. It cannot see a stale `max:`, a
// domain that changed class, a scope that flipped, a gun binding that moved, or
// a domain that was added or retired. Every one of those has drifted here.
//
// The page is STATIC — every number is transcribed, not read at view time — and
// the user balances off it. So a wrong `max:` is not a cosmetic docs bug; it is
// a wrong input to a design decision.
//
// WHAT IT CHECKS (mechanically, no judgement):
//   * the SET of domains: anything in the code but not the page, or vice versa
//   * max            vs add_domain's 4th arg
//   * class list     vs add_domain's class_keys
//   * band           vs add_domain's tier arg (TOD_TIER_S/A/B)
//   * scope          vs set_scope (default is "class" since v15)
//   * gun binding    vs set_guns
//   * bonusMax       vs add_domain's bonus_max
//
// WHAT IT CANNOT CHECK, and you still have to read: the `eff` and `note` prose,
// and whether `lad:` matches the real ladder function. A sentence can become
// false without any number moving — that is the failure mode this tool does NOT
// cover, and the reason the page still needs a human pass.
// =============================================================================

const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const ARMORY = path.join(REPO, 'docs', 'armory.html');
const GSC = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_upgrades.gsc');

// ---- 1. the page's view -----------------------------------------------------
const html = fs.readFileSync(ARMORY, 'utf8');
const src = html.match(/<script[^>]*>([\s\S]*?)<\/script>/)[1];
const cut = src.indexOf('const CLASS_NOTES');
let PAGE;
try {
  PAGE = new Function(src.slice(0, cut) + '; return DOMAINS;')();
} catch (e) {
  console.error('FATAL: could not evaluate the page DOMAINS array —', e.message);
  process.exit(1);
}

// ---- 2. the code's view -----------------------------------------------------
const gsc = fs.readFileSync(GSC, 'utf8');

// Strip // comments so a commented-out add_domain (retired domains are kept as
// comments on purpose) is never counted as live.
const live = gsc.split('\n').filter(l => !l.trim().startsWith('//')).join('\n');

const CODE = {};
// add_domain( "key", "DISPLAY", "desc", max, class_keys, tier, bonus_class, bonus_max )
//
// ⚠️ A CALL IS FOUND BY BALANCED PARENTHESES, NEVER BY THE FIRST ");" (2026-09-26).
// The first version matched /add_domain\(([\s\S]*?)\);/ - a lazy match that ends
// at the first ");" ANYWHERE, including inside a description string. SUMMONING
// POWER's text "(a 2nd Mangler at Lv8); they ..." cut its call short, the tier
// argument never parsed and the domain silently dropped out of the code count
// (code 31 against 32 live). A checker that undercounts without saying so is worse
// than none, so the scanner walks the call honouring strings ("..." with \"
// escapes) and parenthesis depth, and selfCheck() below proves it on a planted
// ");" every run, beside the old regex failing on the same text.
function addDomainCalls(text) {
  const out = [];
  const re = /\badd_domain\s*\(/g;
  let m;
  while ((m = re.exec(text))) {
    let i = m.index + m[0].length, depth = 1, inStr = false;
    const start = i;
    for (; i < text.length && depth > 0; i++) {
      const c = text[i];
      if (inStr) {
        if (c === '\\') { i++; continue; }
        if (c === '"') inStr = false;
        continue;
      }
      if (c === '"') inStr = true;
      else if (c === '(') depth++;
      else if (c === ')') depth--;
    }
    if (depth !== 0) { console.error('FATAL: unbalanced add_domain( call at offset ' + m.index); process.exit(1); }
    out.push(text.slice(start, i - 1));
    re.lastIndex = i;
  }
  return out;
}

// negative control, every run: a description carrying ");" and "(" must parse whole
(function selfCheck() {
  const planted = 'add_domain( "ctl", "CONTROL", "more at Lv3 (a 2nd at Lv8); then \\"quoted\\" )", 8, array( "necromancer" ), TOD_TIER_A );\n'
                + 'add_domain( "ctl2", "CONTROL 2", "plain", 5, undefined, TOD_TIER_B );';
  const calls = addDomainCalls(planted);
  const a = calls.length === 2 ? splitArgs(calls[0]) : [];
  const ok = calls.length === 2 && a.length === 6 && /TOD_TIER_A/.test(a[5]) && a[3] === '8'
          && /"necromancer"/.test(a[4]) && /TOD_TIER_B/.test(splitArgs(calls[1])[5]);
  const oldRegexBroke = !/TOD_TIER_A/.test(([...planted.matchAll(/add_domain\(([\s\S]*?)\);/g)][0] || [])[1] || '');
  if (!ok || !oldRegexBroke) {
    console.error('FATAL: add_domain scanner self-check failed (ok=' + ok + ' old_regex_broke=' + oldRegexBroke + ')');
    process.exit(1);
  }
})();

// ⚠️ ARGUMENTS ARE SPLIT ON *TOP-LEVEL* COMMAS, not by a regex per argument.
// A naive /([^,]+?)/ for class_keys silently fails on the only two domains that
// take more than one class — SPRINT array("skirmisher","slasher") and SCAVENGER
// array("skirmisher","assault","heavy") — because the array's own comma ends the
// match early. The first version of this tool did exactly that and reported both
// as "not in code", i.e. it produced two false alarms about the page while the
// page was right. A checker that cries wolf is worse than none.
function splitArgs(s) {
  const out = []; let depth = 0, cur = '', inStr = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (inStr) { cur += c; if (c === '\\') { cur += s[++i] || ''; continue; } if (c === '"') inStr = false; continue; }
    if (c === '"') { inStr = true; cur += c; continue; }
    if (c === '(') depth++;
    if (c === ')') depth--;
    if (c === ',' && depth === 0) { out.push(cur.trim()); cur = ''; continue; }
    cur += c;
  }
  if (cur.trim()) out.push(cur.trim());
  return out;
}

for (const inner of addDomainCalls(live)) {
  const a = splitArgs(inner);
  if (a.length < 6) continue;
  const key = (a[0].match(/"([a-z0-9_]+)"/) || [])[1];
  if (!key) continue;
  const bandM = a[5].match(/TOD_TIER_([SAB])/);
  CODE[key] = {
    key,
    display: (a[1].match(/"([^"]*)"/) || [])[1],
    desc: (a[2].match(/"([^"]*)"/) || [])[1],
    max: parseInt(a[3], 10),
    classes: a[4] === 'undefined' ? null : [...a[4].matchAll(/"([a-z]+)"/g)].map(x => x[1]),
    band: bandM ? bandM[1] : '?',
    bonusMax: a.length >= 8 ? parseInt(a[7], 10) : undefined,
  };
}

// set_scope( "key", "scope" [, "class"] ) — default since v15 is "class"
for (const d of Object.values(CODE)) d.scope = 'class';
for (const mm of live.matchAll(/set_scope\(\s*"([a-z0-9_]+)"\s*,\s*"(gun|class)"/g)) {
  if (CODE[mm[1]]) CODE[mm[1]].scope = mm[2];
}
// set_guns( "key", array( "a", "b" ) )
for (const mm of live.matchAll(/set_guns\(\s*"([a-z0-9_]+)"\s*,\s*array\(([^)]*)\)/g)) {
  if (CODE[mm[1]]) CODE[mm[1]].guns = [...mm[2].matchAll(/"([a-z0-9_]+)"/g)].map(x => x[1]);
}

// ---- 3. compare -------------------------------------------------------------
const problems = [];
const eq = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
const norm = a => (a && a.length ? [...a].sort() : null);

const pageByKey = {};
for (const p of PAGE) pageByKey[p.key] = p;

for (const k of Object.keys(CODE)) {
  if (!pageByKey[k]) problems.push(`MISSING FROM PAGE   ${k} — live in code (${CODE[k].display}, max ${CODE[k].max}) but no row`);
}
for (const p of PAGE) {
  if (!CODE[p.key]) problems.push(`NOT IN CODE         ${p.key} — page has a row but no live add_domain (retired?)`);
}

for (const k of Object.keys(CODE)) {
  const c = CODE[k], p = pageByKey[k];
  if (!p) continue;
  if (c.max !== p.max) problems.push(`max                 ${k}: page ${p.max}  code ${c.max}`);
  if (c.band !== p.band) problems.push(`band                ${k}: page ${p.band}  code ${c.band}`);
  if (c.scope !== p.scope) problems.push(`scope               ${k}: page ${p.scope}  code ${c.scope}`);
  if (!eq(norm(c.classes), norm(p.cls))) problems.push(`class list          ${k}: page ${JSON.stringify(p.cls)}  code ${JSON.stringify(c.classes)}`);
  if (!eq(norm(c.guns), norm(p.guns))) problems.push(`gun binding         ${k}: page ${JSON.stringify(p.guns)}  code ${JSON.stringify(c.guns)}`);
  if ((c.bonusMax ?? null) !== (p.bonusMax ?? null)) problems.push(`bonusMax            ${k}: page ${p.bonusMax}  code ${c.bonusMax}`);
}

// ---- 4. the derived header/tile counts the page hand-maintains --------------
const N = PAGE.length;
const PERSIST = PAGE.filter(d => d.scope === 'class').length;
const HI = Math.max(...PAGE.map(d => d.id));
const derived = [
  [`<span>${N} domains`, `masthead "${N} domains"`],
  [`>All ${N}</button>`, `tab "All ${N}"`],
  [`["${N}","Live domains"]`, `tile "Live domains" = ${N}`],
  [`["${PERSIST}","Survive a tier-up"]`, `tile "Survive a tier-up" = ${PERSIST}`],
  [`domain id (1..${HI})`, `UIFIELDS "domain id (1..${HI})"`],
  [`"${63 - HI} values"`, `UIFIELDS spare "${63 - HI} values"`],
];
for (const [needle, label] of derived) {
  if (!html.includes(needle)) problems.push(`HAND-MAINTAINED     ${label} — not found; measured says it should be there`);
}

// ---- 5. report --------------------------------------------------------------
console.log(`domains: code ${Object.keys(CODE).length}, page ${PAGE.length}`);
console.log(`persist (scope class): page ${PERSIST}   highest id: ${HI}`);
if (!problems.length) {
  console.log('ARMORY DOMAINS OK — every structural field matches the shipping GSC');
  console.log('(prose in eff:/note: is NOT checked — read it)');
  process.exit(0);
}
console.log('');
for (const p of problems) console.log('  ' + p);
console.log(`\n${problems.length} problem(s)`);
process.exit(1);
