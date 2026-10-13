// upgrade_damage_cb's "nothing modified -> return -1" guard, run as the
// SHIPPING TEXT rather than a copy of it.
//
// WHY THIS FILE EXISTS. Returning -1 tells the stock chain "I changed nothing",
// and stock then applies the RAW damage -- so every multiplier applied above
// the guard must also be TESTED by the guard, or it is silently discarded for
// any player who happens to have no other term active. That has now been the
// same bug several times: v13.7's sprinter_armor_frac, v16's
// slasher_sidearm_boss_mult (both fixed in v16.3), v18.59's script-paid
// PACK II/III, and every per-class multiplier since (the bow draw, the left
// hook, the class build cards).
//
// The negative control at the bottom is the point of the file: it strips the
// captured terms back out and requires each case to FAIL, so a future edit that
// quietly drops one cannot leave this test green.
const fs = require('fs'), assert = require('assert/strict');
const SRC = 'scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc';
const src = fs.readFileSync(SRC, 'utf8').replace(/\r/g, '');

// ---- the guard's own text, lifted from the file --------------------------
function guardText(text) {
  const ret = text.indexOf('return -1;   // nothing modified');
  assert.ok(ret > 0, 'the -1 fast path is gone from ' + SRC);
  // walk back to the `if (` that owns it
  const open = text.lastIndexOf('\tif (', ret);
  assert.ok(open > 0 && open < ret, 'could not find the guard condition');
  const cond = text.slice(open + '\tif ('.length, text.lastIndexOf(')', ret));
  return cond.replace(/\/\/[^\n]*/g, ' ').replace(/\s+/g, ' ').trim();
}

const cond = guardText(src);

// ---- the capture sites the guard depends on ------------------------------
// A guard term is only meaningful if the variable it reads is the SAME value
// that was multiplied in. Assert both halves at both sites.
assert.match(src, /pap_mult = tod_classes::pap_tier_mult\( attacker, weapon \);/,
  'PACK II/III is no longer captured into pap_mult');
assert.match(src, /damage = damage \* pap_mult;/,
  'pap_mult is captured but no longer applied to damage');

// ---- evaluate the real condition -----------------------------------------
// Every name below is either a local the callback computes or one of the four
// helper calls it makes; the condition is otherwise valid JS as written.
function evaluate(condText, s) {
  const fn = new Function(
    'dmult', 'balance', 'dmg_lvl', 'hs_lvl', 'headshot', 'umult', 'bmult',
    'pap_mult', 'draw_mult', 'hook_mult', 'cc_mult', 'attacker', 'self', 'weapon', 'is_melee',
    'melee_boss_mult', 'sprinter_armor_frac', 'slasher_sidearm_boss_mult', 'gunslinger_bonus',
    'return ( ' + condText + ' );');
  return fn(
    s.dmult, s.balance, s.dmg_lvl, s.hs_lvl, s.headshot, s.umult, s.bmult,
    s.pap_mult, s.draw_mult, s.hook_mult, s.cc_mult, {}, {}, {}, s.is_melee,
    () => s.melee_boss, () => s.sprinter_armor, () => s.slasher_sidearm, () => s.gunslinger);
}

// A player carrying nothing at all: no DAMAGE, no Insta-Kill, no class unique,
// ordinary victim, non-melee. This is the state the guard was written for.
const NEUTRAL = {
  dmult: 1, balance: 1.0, dmg_lvl: 0, hs_lvl: 0, headshot: false, umult: 0, bmult: 0,
  pap_mult: 1.0, draw_mult: 1.0, hook_mult: 1.0, cc_mult: 1.0, is_melee: false,
  melee_boss: 1.0, sprinter_armor: 1.0, slasher_sidearm: 1.0, gunslinger: 0.0,
};
const S = o => Object.assign({}, NEUTRAL, o);

// silent === the callback returns -1 and stock applies the raw damage.
const silent = o => evaluate(cond, S(o));

let checks = 0;
function want(label, opts, expected) {
  assert.equal(silent(opts), expected, label);
  checks++;
}

// The case the guard is FOR: nothing was modified, so say nothing.
want('a bare player with no terms stays silent', {}, true);

// PACK II / PACK III, on any class, with no DAMAGE level yet.
for (const p of [1.5, 2.25]) {
  want('a PACK re-pack of x' + p + ' must reach the victim', { pap_mult: p }, false);
}
want('tier 0/1 PaP returns 1.0 and stays silent', { pap_mult: 1.0 }, true);

// THE BOW DRAW (2026-09-25): a charged arrow, no other term.
for (const d of [2.0, 3.0]) want('a bow draw of x' + d + ' must reach the victim', { draw_mult: d }, false);
want('a tap (x1.0) stays silent', { draw_mult: 1.0 }, true);
assert.match(src, /draw_mult = tod_archer_bow::charge_mult\( attacker, inflictor, weapon, meansofdeath \);\n\tdamage = damage \* draw_mult;/, 'the bow draw is no longer captured + applied');

// THE WARRIOR'S LEFT HOOK (2026-09-26): x0.5 on the gauntlet's left hand (x0.75 until 2026-09-27), no other term.
want('a left hook (x0.5) must reach the victim', { hook_mult: 0.5, is_melee: true }, false);
want('a right hook (x1.0) stays silent', { hook_mult: 1.0, is_melee: true }, true);
assert.match(src, /hook_mult = \[\[ level\.tod_wm_hit_mult_fn \]\]\( attacker, weapon, meansofdeath \);\n\tdamage = damage \* hook_mult;/, 'the left hook is no longer captured + applied');
assert.match(src, /\thook_mult = 1\.0;/, 'hook_mult must default to 1.0 so the guard is valid without the Warrior module');

// THE CLASS BUILD CARDS (2026-09-27): HUNTER'S MARK / POINT BLANK / EXECUTIONER, one multiplier.
want('a class build card (x1.36) must reach the victim', { cc_mult: 1.36 }, false);
want('no build card (x1.0) stays silent', { cc_mult: 1.0 }, true);
assert.match(src, /cc_mult = \[\[ level\.tod_cc_damage_fn \]\]\( attacker, self, weapon, meansofdeath, draw_mult \);\n\tdamage = damage \* cc_mult;/, 'the build cards are no longer captured + applied');
assert.match(src, /\tcc_mult = 1\.0;/, 'cc_mult must default to 1.0 so the guard is valid without _tod_class_cards');

// Both at once -- a packed, fully drawn arrow.
want('a packed charged arrow is not silent', { pap_mult: 2.25, draw_mult: 3.0 }, false);

// The terms that were ALREADY tested must still break it (v16.3 regression).
want('DAMAGE level breaks silence', { dmg_lvl: 1 }, false);
want('Insta-Kill breaks silence', { dmult: 2 }, false);
// W2E (2026-10-05): the armored sprinter retired whole, and its armor term left the guard with its lane - no victim
// carries it, so the term would be a dead read. The guard must not name it again without the lane coming back.
assert.ok(!/sprinter_armor_frac\s*\(/.test(src.replace(/\/\/[^\n]*/g, '')), 'the retired sprinter armor lane stays out of the damage chain (code; comments are history)');
want('the retired sprinter armor is no longer a guard term', { sprinter_armor: 0.34 }, true);
want('melee-vs-boss halving breaks silence', { melee_boss: 0.5, is_melee: true }, false);
want('the slasher sidearm boss lane breaks silence', { slasher_sidearm: 2.25 }, false);
want('GUNSLINGER breaks silence', { gunslinger: 0.4 }, false);
want('a headshot with a HEADSHOT level breaks silence', { hs_lvl: 3, headshot: true }, false);
want('a HEADSHOT level without a headshot stays silent', { hs_lvl: 3, headshot: false }, true);
want('gun balance breaks silence', { balance: 7.2 }, false);

// ---- NEGATIVE CONTROL ----------------------------------------------------
// Strip the captured terms and require each case to regress. If this block
// ever passes, the test above is measuring nothing.
const stripped = cond.replace(/&& pap_mult == 1\.0 /, '').replace(/&& draw_mult == 1\.0 /, '').replace(/&& hook_mult == 1\.0 /, '').replace(/&& cc_mult == 1\.0 /, '');
assert.notEqual(stripped, cond, 'negative control could not find the terms to strip');
assert.equal(evaluate(stripped, S({ pap_mult: 2.25 })), true,
  'negative control: without the term, a PACK III holder SHOULD be wrongly silent');
assert.equal(evaluate(stripped, S({ draw_mult: 3.0 })), true,
  'negative control: without the term, a full-draw arrow SHOULD be wrongly silent');
assert.equal(evaluate(stripped, S({ hook_mult: 0.75 })), true,
  'negative control: without the term, a left hook SHOULD be wrongly silent (landing at full damage)');
assert.equal(evaluate(stripped, S({ cc_mult: 1.36 })), true,
  'negative control: without the term, a build-card hit SHOULD be wrongly silent');

console.log('upgrade_damage_cb guard passed: ' + checks +
  ' scenarios over the shipping condition, both capture sites wired, negative control fires.');
