// THE BLACK MARKET SPIN (docs/188): runs the shipping roll / item / timing GSC
// with stubbed randomness, and proves the server and TodSpinReel.lua agree on
// every item name, effect number, odds line, event name and the price.
// Does not claim to emulate native LUI or input; the user's match does that.
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict'), path = require('path');
const root = path.resolve(__dirname, '../..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const gsc = read('scripts/zm/zm_tod2_cybercity/_tod_shop.gsc');
const lua = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodSpinReel.lua');
const ptn = read('scripts/zm/zm_tod2_cybercity/_tod_partners.gsc');
let checks = 0; const ok = (v, m) => { assert.ok(v, m); checks++; };

function body(name) {
  const clean = gsc.replace(/\/\/[^\n]*/g, '');
  const start = clean.indexOf('function ' + name + '(');
  assert(start >= 0, name);
  const a = clean.indexOf('{', start); let b = a + 1, depth = 1;
  while (depth) { if (clean[b] === '{') depth++; if (clean[b] === '}') depth--; b++; }
  return clean.slice(a + 1, b - 1);
}
const translate = c => c
  .replace(/foreach \( (\w+) in ([^)]+) \)/g, 'for (const $1 of $2)')
  .replace(/\.size\b/g, '.length')
  .replace(/\bint\(/g, 'Math.trunc(')
  .replace(/\btod_luck::/g, '');   // THE HOT STREAK (docs/201): heat_mult is mirrored below from _tod_luck.gsc's own table
const defs = {};
for (const m of gsc.matchAll(/#define (TOD_SPIN_\w+)\s+([-\d.]+)/g)) defs[m[1]] = Number(m[2]);
// THE HOT STREAK's one table (docs/201), read from _tod_luck.gsc init(): the shop's roll multiplies by it
const luckGsc = read('scripts/zm/zm_tod2_cybercity/_tod_luck.gsc');
const HEAT_MULT = (luckGsc.match(/level\.tod_heat_mult = array\(([^)]*)\);/) || ['', ''])[1].split(',').map(Number);
// RandomInt: a constant (env.ri) for the exact sweeps, or a seeded stream (env.rng) for the near-miss rates
const env = Object.assign({ array: (...a) => a, self: {}, rf: 0, ri: 0, rng: null,
  RandomFloat: n => env.rf, RandomInt: n => (env.rng ? Math.floor(env.rng() * n) : env.ri), isdefined: x => x !== undefined && x !== null,
  heat_mult: p => { const h = (p && p.tod_luck_heat) || 0; return HEAT_MULT[Math.max(0, Math.min(HEAT_MULT.length - 1, h))]; } }, defs);
vm.createContext(env);
for (const [n, args, locals] of [['tile_item', 'v', ''], ['tile_rar', 'v', ''], ['item_value', 'item,rar', 'v'],
  ['arc_frac', 'rar', 'v'], ['roll_rarity', 'luck', 'c,r,e,hm,l,roll,rar'], ['roll_item', 'slots,rar', 'pool,i,held'],
  ['step_ms', 'k,rar,nkind', 't,ms'], ['item_rarity', 'p,comp,item', ''], ['near_plan', 'rar,slots', 'x,kind,trar,titem']]) {
  vm.runInContext(`function ${n}(${args}){${locals ? 'let ' + locals + ';' : ''}${translate(body(n))}}`, env);
}

// ---- odds: sweep the roll across 0..100 and count (docs/187 table)
function dist(luck, ri) {
  const c = [0, 0, 0, 0]; env.ri = ri;
  for (let i = 0; i < 10000; i++) { env.rf = i / 100; c[env.roll_rarity(luck)]++; }
  return c.map(x => x / 100);
}
const near = (a, b) => Math.abs(a - b) < 0.02;
let d = dist(0, 99);
ok(near(d[0], 56) && near(d[1], 27) && near(d[2], 13) && near(d[3], 4), 'empty bar = 56/27/13/4, got ' + d);
d = dist(49, 99); ok(d[0] > 0, 'below half a bar Common can land');
d = dist(50, 99); ok(d[0] === 0, 'half a bar guarantees Rare or better');
d = dist(100, 99); ok(d[0] === 0 && d[1] === 0, 'a full bar guarantees Epic or better');
ok(near(d[3], 8), 'a full bar keeps its natural 8 Legendary when the guarantee does not roll it, got ' + d[3]);
d = dist(100, 0); ok(near(d[3], 8 + 36 + 36), 'the forced Epic becomes Legendary on the 25 percent roll (every forced one here)');
ok(defs.TOD_SPIN_GUAR_LEG_PCT === 25, 'GUAR_LEG_SHARE 25 (docs/187)');

// ---- no dead spins
env.ri = 0;
const held = [3 * 4 + 2, 1 * 4 + 3, 6 * 4 + 0];   // HOLLOW EPIC, PLATING LEGENDARY, ARC COMMON
for (let rar = 0; rar < 4; rar++) {
  for (let pick = 0; pick < 9; pick++) {
    env.ri = pick;
    const item = env.roll_item(held, rar);
    if (item === 0) continue;
    const h = env.item_rarity({ tod_spin_items: [held] }, 0, item);
    ok(h < rar, `rar ${rar}: prize item ${item} is new or an upgrade (held ${h})`);
  }
}
ok(env.roll_item(held, 3) !== 1, 'a Legendary item is never offered again at Legendary');

// ---- the reel's timing
let total = 0, last = 0, mono = true;
for (let k = 1; k <= defs.TOD_SPIN_STEPS; k++) {
  const ms = env.step_ms(k, 0, 0); total += ms; ok(ms % 50 === 0 && ms >= 50, 'step on a server frame');
  if (ms < last) mono = false; last = ms;
}
ok(mono, 'the reel only ever slows down');
ok(total >= 5000 && total <= 8000, 'a spin reads in 5..8 s, got ' + total);
ok(env.step_ms(defs.TOD_SPIN_STEPS, 3, 0) - env.step_ms(defs.TOD_SPIN_STEPS, 2, 0) >= 800, 'a Legendary crawls onto the needle');

// ---- lockstep: names, effect numbers, odds, price, events, routing
const luaNames = [...lua.matchAll(/\[ (\d) \] = \{ name = "([^"]+)",\s+chip =/g)].map(m => m[2]);
const gscNames = body('item_name').match(/array\(([^)]*)\)/)[1].split(',').map(s => s.trim().replace(/"/g, '')).slice(1);
ok(JSON.stringify(luaNames) === JSON.stringify(gscNames), 'item names match: ' + luaNames);
const glyph = /^[A-Z0-9 \-'.]+$/;
for (const m of lua.matchAll(/"([^"]+)"/g)) if (/^[A-Z][A-Z0-9 .'-]+$/.test(m[1]) || m[1].includes(' X')) ok(glyph.test(m[1]), 'typeface can draw: ' + m[1]);
const fxLines = {};
for (const m of lua.matchAll(/\[ (\d) \] = \{ name = "[^"]+",\s+chip = "[^"]+",\s+fx = \{ ([^}]+) \}/g)) fxLines[+m[1]] = m[2].split('",').map(s => s.replace(/"/g, '').trim());
ok(Object.keys(fxLines).length === 9, 'nine effect rows');
const numIn = s => (s.match(/[\d.]+/g) || []).map(Number);
for (let r = 0; r < 4; r++) {
  for (const it of [1, 2, 3, 4, 9]) ok(numIn(fxLines[it][r]).includes(env.item_value(it, r)), `item ${it} r${r} x${env.item_value(it, r)} in "${fxLines[it][r]}"`);
  ok(numIn(fxLines[5][r])[0] === Math.round(env.item_value(5, r) * 100), 'NANO percent r' + r);
  ok(numIn(fxLines[6][r])[0] === env.item_value(6, r) && numIn(fxLines[6][r])[1] === Math.round(env.arc_frac(r) * 100), 'ARC count + percent r' + r);
  ok(numIn(fxLines[7][r])[0] === env.item_value(7, r), 'SALVAGE points r' + r);
  ok(numIn(fxLines[8][r])[0] === env.item_value(8, r) / 1000, 'QUICK REBOOT seconds r' + r);
  ok(env.item_value(8, r) < 45000, 'QUICK REBOOT always beats the 45 s rebuild');
}
ok(/56 - 0\.20 \* luck/.test(lua) && /27 \+ 0\.09 \* luck/.test(lua) && /13 \+ 0\.07 \* luck/.test(lua), 'the reel filler uses the server odds line');
ok(gsc.includes('[Cost: ' + defs.TOD_SPIN_COST + ']'), 'the hint price is TOD_SPIN_COST');
for (const m of (gsc + ptn).matchAll(/LuiNotifyEvent\( &"(tod_spin_\w+|tod_ptn_items)"/g))
  ok((gsc + ptn).includes(`#precache( "eventstring", "${m[1]}" )`), 'precached eventstring ' + m[1]);
for (const ev of ['tod_spin_open', 'tod_spin_step', 'tod_spin_land', 'tod_spin_slots', 'tod_spin_end', 'tod_ptn_items'])
  ok(lua.includes(`"${ev}"`) && (gsc + ptn).includes(`&"${ev}"`), 'both sides speak ' + ev);
ok(read('ui/uieditor/widgets/HUD/ZM_CursorHint/ZMCursorHintNew.lua').includes('"black market",'), 'the BLACK MARKET prompt routes to the default card');
// ONE NAME (user 2026-09-29): nothing a player reads may still say "item shop".
ok(!/"item shop"/.test(read('ui/uieditor/widgets/HUD/ZM_CursorHint/ZMCursorHintNew.lua')) && !/SetHintString\([^)]*ITEM SHOP/i.test(gsc), 'the old ITEM SHOP name is gone from the prompt noun and the hints');
ok(gsc.includes('buy SetHintString( "Hold ^3[{+activate}]^7 ^5BLACK MARKET^7 - Spin for a companion item / Your luck sets the odds ^2[Cost: 2500]" );'), 'the buy prompt is titled BLACK MARKET');
ok(read('zone_source/zm_tod2_cybercity.zone').includes('rawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodSpinReel.lua'), 'the reel is zoned');
ok(read('ui/uieditor/menus/hud/tod_upgrade.lua').includes('CoD.TodSpinReel.new( Hud, Instance )'), 'the always-open HUD builds the reel');

// ---- the lock is symmetric and the user's two rules hold
const lock = body('spin_lock');
ok((lock.match(/increment_ignoreme/g) || []).length === 1 && (lock.match(/decrement_ignoreme/g) || []).length === 1, 'untargetable: ignoreme refcount paired');
ok(lock.includes('menu_freeze( true )') && lock.includes('menu_freeze( false )') && lock.includes('EnableInvulnerability') && body('spin_exit_grace').includes('DisableInvulnerability'), 'frozen + unhurtable, both released (protection ends after the exit grace)');
ok(body('spin_exit_grace').includes('tod_pause_invuln') && body('spin_exit_grace').includes('pause_invuln_held_elsewhere'), 'never strips a world-pause or zombie-blood invulnerability');
const spin = body('spin');
ok(spin.indexOf('spin_lock( true )') < spin.indexOf('spin_open(') && spin.lastIndexOf('spin_lock( false )') > spin.lastIndexOf('tod_spin_end'), 'untargetable for the whole spin');
ok(spin.includes('tod_luck::spend( self )'), 'the spin spends the luck bar');
ok(body('item_rarity').includes('return -1') && body('choose_slot').includes('return -1;'), 'timeout / SCRAP never overwrites a held item');
ok(body('near_plan').includes('if ( rar >= 3 ) return 0;'), 'a LEGENDARY prize is never teased (the near miss only dresses a lesser prize)');
ok(gsc.includes('if ( IS_TRUE( level.tod_dev ) ) powered = true;'), 'dev: the crown shop is live without power (user)');


// ---- THE SECOND PASS (user 2026-09-29: "Double check for bad player experiences
// or UI issues. Also the HUD should not show while this is happening")
// 1. the prompt: two constant hints, per-player visibility, none while spinning
// THE DEALER'S GIFT (docs/209): a player with no companion sees the GIFT prompt (free, no luck), never a locked
// "companion required / Build one at a partner bench" card (the parts and benches are retired)
const GIFT_HINT = 'need SetHintString( "Hold ^3[{+activate}]^7 ^5BLACK MARKET^7 - A free AI companion / No points or luck - on the house" );';
ok(gsc.includes(GIFT_HINT), 'a player with no companion sees THE DEALER\'S GIFT prompt (a key, no price, no lock word)');
{
  const gh = GIFT_HINT.match(/"([^"]+)"/)[1].toLowerCase();
  const lockWords = (read('ui/uieditor/widgets/HUD/ZM_CursorHint/Prompts/TodPromptCard.lua').match(/LOCK_WORDS = \{([^}]*)\}/) || ['', ''])[1].split(',').map(s => s.trim().replace(/"/g, '')).filter(Boolean);
  ok(lockWords.length >= 5 && lockWords.every(w => !gh.includes(w)), 'the gift prompt carries no lock word (a live card, not the locked chassis)');
  ok(!/\[cost:/.test(gh) && !gh.includes('$'), 'the gift prompt carries no price (it is free)');
  ok(gh.includes('free ai companion') && read('ui/uieditor/widgets/HUD/ZM_CursorHint/Prompts/PromptDefault.lua').includes('string.find( string.lower( t ), "free ai companion", 1, true )') && read('ui/uieditor/widgets/HUD/ZM_CursorHint/Prompts/PromptDefault.lua').includes('SetFooter( self, "TAKE" )'), 'the gift card says HOLD <key> TO TAKE');
  const d = GIFT_HINT.match(/\^7 - ([^"]+)"/)[1].split(' / ');
  ok(d.length === 2 && d.every(x => x.length <= 40), 'both gift detail lines fit the card\'s 40-cell glyph pool: ' + d.map(x => x.length));
  ok(!/Build one at a partner bench|companion required/.test(gsc), 'the old locked NEED card is gone');
}
{
  const vis = body('spin_vis_apply_all');
  ok(vis.includes('IS_TRUE( p.tod_spin_locked ) ) want = 0') && vis.includes('p.tod_ptn.chosen < 0 ) want = 2'), 'visibility: spinning = no prompt, no companion = the GIFT prompt');
  ok(body('spin_lock').split('spin_vis_apply_all();').length === 3, 'the prompt leaves / returns the same frame the spin locks / unlocks');
}
// 2. every wait inside a spin gives way to a card deal; never unfreeze under a deal
{
  const sp = body('spin');
  const bare = sp.split('\n').filter(l => /\bwait\b/.test(l) && !/spin_wait|wait_world|spin_release_use/.test(l));
  ok(bare.length === 1 && /while \( IS_TRUE\( level\.tod_upgrade_pause \) \) wait 0\.1;/.test(bare[0]), 'the only bare wait in spin() is the deal wait before the unlock: ' + JSON.stringify(bare));
  ok(sp.indexOf('while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.1;') < sp.lastIndexOf('self spin_lock( false );'), 'a deal that began in the last frame keeps its freeze');
  ok(sp.indexOf('tod_luck::spend( self )') < sp.indexOf('self spin_wait_world()'), 'the luck is paid at the purchase, before any wait');
  ok(sp.indexOf('self spin_wait_world()') < sp.indexOf('self spin_open('), 'a deal at the purchase takes the screen before the reel opens');
  ok((sp.match(/spin_show_result\(/g) || []).length === 2, 'the prize is repainted after a hold at the landing and at the read');
}
// 3. the choice cannot lose an item by accident (executed with simulated input)
{
  const src = body('choose_slot')
    .replace(/foreach \( (\w+) in ([^)]+) \)/g, 'for (const $1 of $2)')
    .replace(/\bint\(/g, 'Math.trunc(')
    .replace(/&"/g, '"')
    .replace(/\bself (\w+)\(/g, 'self.$1(')
    .replace(/wait ([^;]+);/g, 'yield $1;');
  const cenv = Object.assign({ log: () => {}, tile_rar: v => v - Math.trunc(v / 4) * 4, Math }, defs);
  vm.createContext(cenv);
  vm.runInContext('function* choose_slot(slots,prize,seed,tease,luck){let weakest,i,focus,held,jump_armed,use_armed,grace,last_sec,last_frg,last_d3,last_d4,left,sent,want,sec,frg,d3,d4,b_jump,b_use,packed;' + src + '}', cenv);
  function play(slots, prize, input) {
    let t = 0; const events = [];
    const self = { SecondaryOffhandButtonPressed: () => !!input(t).sec, FragButtonPressed: () => !!input(t).frg,
      ActionSlotThreeButtonPressed: () => false, ActionSlotFourButtonPressed: () => false,
      JumpButtonPressed: () => !!input(t).jump, UseButtonPressed: () => !!input(t).use,
      LuiNotifyEvent: (...a) => events.push(a), PlayLocalSound: () => {}, spin_hold_for_pause: () => false, GetEntityNumber: () => 0 };
    cenv.self = self;
    const g = cenv.choose_slot(slots, prize, 1, 0, 0);
    let r;
    while (!(r = g.next()).done) { t += r.value; if (t > 60) throw Error('choice never ended'); }
    return { idx: r.value, t, events };
  }
  const allCommon = [1 * 4 + 0, 2 * 4 + 0, 3 * 4 + 0];
  // mashing USE from the very first frame: nothing may be replaced before the grace ends
  let r = play(allCommon, 7 * 4 + 1, () => ({ use: true }));
  ok(r.idx === -1, 'USE held from the start never confirms (it must be released first) -> timeout scrap, got ' + r.idx);
  // THE PLAYTEST CASE: USE pressed a frame AFTER the choice appeared and held (the
  // 23:40 run replaced HOLLOW POINT 0.65 s in). The grace swallows the press, and a
  // button still down when the grace ends must be released before it can confirm.
  r = play(allCommon, 7 * 4 + 1, t => ({ use: t >= 0.05 }));
  ok(r.idx === -1 && r.t > 10, 'a press that starts inside the grace never confirms while held, got ' + r.idx + ' at ' + r.t.toFixed(2) + ' s');
  r = play(allCommon, 7 * 4 + 1, t => ({ use: Math.floor(t * 10) % 2 === 0 }));
  ok(r.idx === -1, 'mashing USE never confirms (a confirm is a steady hold), got ' + r.idx);
  r = play(allCommon, 7 * 4 + 1, t => ({ jump: t >= 0.7 }));
  ok(r.idx === 0 && r.t >= defs.TOD_SPIN_CHOICE_GRACE + defs.TOD_SPIN_HOLD_SECS - 0.06, 'a deliberate hold after the grace confirms, at ' + r.t.toFixed(2) + ' s');
  // default focus: the weakest slot only when the prize beats it
  r = play(allCommon, 7 * 4 + 1, t => ({ jump: t > 0.8 }));
  ok(r.idx === 0, 'a RARE prize over three COMMONs defaults to the weakest slot, got ' + r.idx);
  r = play(allCommon, 7 * 4 + 0, t => ({ jump: t > 0.8 }));
  ok(r.idx === -1, 'a COMMON prize over three COMMONs defaults to SCRAP (an equal item is never thrown away by default), got ' + r.idx);
  r = play([1 * 4 + 3, 2 * 4 + 2, 3 * 4 + 3], 7 * 4 + 3, t => ({ jump: t > 0.8 }));
  ok(r.idx === 1, 'a LEGENDARY prize targets the EPIC slot, got ' + r.idx);
  // navigation: tactical steps left (wraps to SCRAP), lethal steps right
  r = play(allCommon, 7 * 4 + 1, t => ({ sec: t > 0.2 && t < 0.3, jump: t > 1.0 }));
  ok(r.idx === -1, 'tactical from slot 1 wraps to SCRAP, got ' + r.idx);
  r = play(allCommon, 7 * 4 + 1, t => ({ frg: (t > 0.2 && t < 0.3) || (t > 0.5 && t < 0.6), jump: t > 1.0 }));
  ok(r.idx === 2, 'lethal twice from slot 1 lands on slot 3, got ' + r.idx);
  r = play(allCommon, 7 * 4 + 1, () => ({}));
  ok(r.idx === -1 && Math.abs(r.t - defs.TOD_SPIN_CHOICE_SECS) < 0.2, 'doing nothing times out to SCRAP at ' + defs.TOD_SPIN_CHOICE_SECS + ' s');
  ok(r.events.some(e => e[0] === 'tod_spin_slots' && e[5] % 10 === 1), 'the choice paints the slot row in choosing mode');
}
// 4. sound + announce speak the card reveal's language; the reel does not buzz
{
  const lf = body('land_feedback');
  ok(lf.includes('"tod_pull_legendary"') && lf.includes('"tod_super_sting"') && lf.includes('"tod_card_land"'), 'landing sounds = the card reveal (land / sting / legendary)');
  // RT 2026-10-05: the announcement is THE TOAST (kind 2, our typeface), no longer a stock-font IPrintLnBold
  ok(lf.includes('if ( rar < 3 ) return;') && lf.includes('self tod_upgrade_ui::team_toast( 2, item, "tod_pull_alert" );') && !lf.includes('IPrintLnBold'), 'only a LEGENDARY is announced to teammates, like a Legendary card (THE TOAST, never the stock font)');
  ok(defs.TOD_SPIN_TICK_MIN_MS >= 100 && body('spin').includes('GetTime() - last_tick >= TOD_SPIN_TICK_MIN_MS'), 'the reel ticks at most every 100 ms');
  ok(body('spin').includes('"tod_pull_beat"'), 'a Legendary gets the heartbeat in the crawl');
  const ui = read('sound/aliases/tod_ui.csv');
  for (const a of ['tod_card_land', 'tod_super_sting', 'tod_pull_legendary', 'tod_pull_beat', 'tod_pull_alert'])
    ok(new RegExp('^' + a + ',', 'm').test(ui), 'alias exists: ' + a);
  // PASS 3 SOUND (docs/194): the machine's own kit + the dealer. Every alias the spin can
  // play exists (the concatenated names expanded), and the spin plays each family.
  const shop = gsc.replace(/\/\/[^\n]*/g, '');
  const kit = { tod_spin_coin: 1, tod_spin_open: 1, tod_spin_luck: 1, tod_spin_start: 1, tod_spin_stop: 1,
    tod_spin_socket: 1, tod_spin_upgrade: 1, tod_spin_scrap: 1, tod_spin_close: 1, tod_spin_vo_close: 1,
    tod_spin_tick_: 3, tod_spin_crawl_: 5, tod_spin_vo_buy_: 3, tod_spin_vo_common_: 2, tod_spin_vo_epic_: 2, tod_spin_vo_legendary_: 2,
    // THE DEALER'S VOICE (2026-09-30, tools/black_market_vo): every new hook's aliases
    tod_spin_vo_approach_: 4, tod_spin_vo_no_points_: 2, tod_spin_vo_busy: 1,
    // THE DEALER'S GIFT (docs/209): his offer as a companion-less player walks up, his word as the gift reel starts and as it lands
    tod_spin_vo_gift_offer_: 2, tod_spin_vo_gift_spin_: 2, tod_spin_vo_gift_land_: 2,
    tod_spin_vo_luck_low: 1, tod_spin_vo_luck_full: 1, tod_spin_vo_rare_: 2, tod_spin_vo_socket_: 2, tod_spin_vo_upgrade_: 2,
    tod_spin_vo_scrap_: 2, tod_spin_vo_full_1: 1, tod_spin_vo_regular_: 2, tod_spin_vo_item_: 0,
    // THE NEAR MISS + THE HOT STREAK (docs/201): the "so close" after a near miss, the hot greeting at the pour
    tod_spin_vo_near_: 4, tod_spin_vo_hot_: 3 };
  // THE MOUTH (user 2026-09-30): every dealer line is a 3D row in tod_shop.csv, played FROM a script_origin at
  // the mask TO one player (PlaySoundToPlayer); the kit's old 2D voice rows must be gone from tod_ui.csv
  const shopCsv = read('sound/aliases/tod_shop.csv');
  const voTable = a => a.startsWith('tod_spin_vo_') ? shopCsv : ui;
  for (const [base, n] of Object.entries(kit)) {
    ok(shop.includes('"' + base + '"'), 'the spin plays ' + base + (n > 1 ? '1..' + n : ''));
    if (n === 0) continue;   // the nine item lines are named by item_slug(): checked below
    const names = n === 1 ? [base] : Array.from({ length: n }, (_, i) => base + (i + 1));
    for (const a of names) {
      ok(new RegExp('^' + a + ',', 'm').test(voTable(a)), 'alias exists: ' + a);
      if (a.startsWith('tod_spin_vo_')) {
        ok(new RegExp('^' + a + ',.*,3d,', 'm').test(shopCsv), 'dealer alias is 3D: ' + a);
        ok(!new RegExp('^' + a + ',', 'm').test(ui), 'no 2D copy of ' + a + ' left in tod_ui.csv');
      }
    }
  }
  // the item lines: one per slug in item_slug(), the same nine items as item_name()
  const slugs = (body('item_slug').match(/array\(([^)]*)\)/) || ['', ''])[1].split(',').map(s => s.trim().replace(/"/g, '')).filter(Boolean);
  ok(slugs.length === 9, 'item_slug names nine items');
  for (const s of slugs) ok(new RegExp('^tod_spin_vo_item_' + s + ',.*,3d,', 'm').test(shopCsv), 'alias exists (3D): tod_spin_vo_item_' + s);
  // the idle mutters are 3D rows in the shop's own table (played at the counter, not on the player)
  for (let i = 1; i <= 6; i++) ok(new RegExp('^tod_spin_vo_idle_' + i + ',.*,3d,', 'm').test(shopCsv), 'alias exists (3D): tod_spin_vo_idle_' + i);
  ok(body('vo_idle_watch').includes('"tod_spin_vo_idle_"') && body('vo_idle_watch').includes('p vo_say( alias )') && body('vo_idle_watch').includes('TOD_SPIN_VO_IDLE_R'), 'the mutters go to each player in earshot on his own lane');
  ok(body('vo_say').includes('mouth PlaySoundToPlayer( alias, self )') && !body('vo_say').includes('PlayLocalSound'), 'a line is played on the mouth entity to ONE player (3D + private)');
  ok(body('spin_init').includes('level.tod_spin_vo_mouth = Spawn( "script_origin"') && body('spin_trigger_place').includes('level.tod_spin_vo_mouth.origin = local_to_world( s.origin, s.yaw, TOD_SPIN_VO_MOUTH_OFS )'), 'the mouth follows the lit counter');
  ok(!/PlaySoundToPlayer\( *"tod_spin_vo_/.test(shop.replace(body('vo_say'), '')), 'no dealer line bypasses vo_say via PlaySoundToPlayer');
  // ONE VOICE LANE PER PLAYER: every dealer line goes through vo_say(), which drops a line while
  // another is still speaking, using the GENERATED length table
  ok(body('vo_say').includes('tod_shop_vo::secs') && body('vo_say').includes('tod_spin_vo_until') && body('vo_say').includes('VO_DROP'), 'vo_say keeps one lane per player from the generated lengths');
  ok(!/PlayLocalSound\( *"tod_spin_vo_/.test(shop.replace(body('vo_say'), '')), 'no dealer line bypasses vo_say');
  ok(shop.includes('vo_approach_watch();') && shop.includes('vo_idle_watch();'), 'the greeting and the mutters are threaded from spin_init');
  // THE CLASSES (user 2026-10-01): six class lines per class (approach x2, buy x2, close, socket), 3D rows in the
  // shop table, in the length table, and the four hooks route through vo_cls() with the generic line as the fallback
  const clsSlugs = ['archer', 'breacher', 'warrior', 'necro'];
  const clsHooks = { approach: 2, buy: 2, close: 1, socket: 1, near: 1 };
  const voGscCls = read('scripts/zm/zm_tod2_cybercity/_tod_shop_vo.gsc');
  for (const s of clsSlugs) for (const [h, n] of Object.entries(clsHooks)) for (let i = 1; i <= n; i++) {
    const a = 'tod_spin_vo_cls_' + s + '_' + h + '_' + i;
    ok(new RegExp('^' + a + ',.*,3d,', 'm').test(shopCsv), 'class line exists (3D): ' + a);
    ok(new RegExp('case "' + a + '": return [0-9.]+;').test(voGscCls), 'the length table knows ' + a);
  }
  const vcs = body('vo_cls_slug');
  for (const [key, slug] of [['assault', 'archer'], ['heavy', 'breacher'], ['slasher', 'warrior'], ['necromancer', 'necro']])
    ok(new RegExp('case "' + key + '":\\s*return "' + slug + '";').test(vcs), 'vo_cls_slug maps ' + key + ' -> ' + slug);
  ok(vcs.includes('if ( !isdefined( self.tod_class ) ) return "";'), 'a player with no class yet hears the generic line');
  const vc = body('vo_cls');
  ok(vc.includes('RandomInt( 100 ) >= TOD_SPIN_VO_CLASS_PCT ) return generic;') && vc.includes('"tod_spin_vo_cls_" + slug + "_" + hook + "_" + ( RandomInt( n_cls ) + 1 )'), 'vo_cls rolls the class share then names the class line');
  ok(defs.TOD_SPIN_VO_CLASS_PCT >= 40 && defs.TOD_SPIN_VO_CLASS_PCT <= 80, 'the class share leaves the generic lines in play (40..80)');
  ok(body('vo_approach_watch').includes('p vo_cls( "approach", 2, "tod_spin_vo_approach_"'), 'the greeting routes through vo_cls');
  ok(body('spin').includes('self vo_cls( "buy", 2, "tod_spin_vo_buy_"') && body('spin').includes('self vo_cls( "close", 1, "tod_spin_vo_close" )') && body('spin').includes('self vo_cls( "socket", 1, "tod_spin_vo_socket_"'), 'the buy, close and socket lines route through vo_cls');
  ok(!/"tod_spin_vo_cls_[a-z]+_/.test(shop.replace(body('vo_cls'), '')), 'no class line is named outside vo_cls (the slug + hook build it)');
  const voGsc = read('scripts/zm/zm_tod2_cybercity/_tod_shop_vo.gsc');
  for (const a of ['tod_spin_vo_buy_1', 'tod_spin_vo_legendary_2', 'tod_spin_vo_item_lucky_charm', 'tod_spin_vo_idle_6', 'tod_spin_vo_approach_4'])
    ok(new RegExp('case "' + a + '": return [0-9.]+;').test(voGsc), 'the length table knows ' + a);
  // the crawl climbs: five rows on one wav, pitch rising (cents)
  const crawl = [1, 2, 3, 4, 5].map(i => (ui.match(new RegExp('^tod_spin_crawl_' + i + ',.*$', 'm')) || [''])[0]);
  ok(crawl.every(r => r.includes('tod_spin_crawl.wav')), 'the five crawl rows share tod_spin_crawl.wav');
  ok(!/tod_ui_tick|tod_luck_pip0|tod_ui_lock|zmb_cha_ching/.test(body('spin')), 'the spin no longer borrows the glass cling, the luck pips or the stock cha-ching');
}
// 5. control returns fairly: a grace after the panel closes
{
  const lock = body('spin_lock');
  ok(!/DisableInvulnerability/.test(lock) && lock.includes('self thread spin_exit_grace();'), 'unlocking hands over to the exit grace instead of dropping protection at once');
  const g = body('spin_exit_grace');
  ok(g.includes('wait TOD_SPIN_EXIT_GRACE;') && g.includes('IS_TRUE( self.tod_spin_locked ) ) return;') && g.includes('pause_invuln_held_elsewhere'), 'the grace never strips a new spin or a world pause');
  ok(defs.TOD_SPIN_EXIT_GRACE >= 1 && defs.TOD_SPIN_EXIT_GRACE <= 2, 'grace 1..2 s');
}
// 6. the whole HUD is veiled: LUI (the shared veil) + the server hudelems
{
  ok(lua.includes('CoD.TodHudVeil.Set( "spin", on )') && lua.includes('pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodHudVeil" )'), 'the reel owns the "spin" veil key');
  ok(read('zone_source/zm_tod2_cybercity.zone').includes('rawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodHudVeil.lua'), 'the veil is zoned');
  // PK08 (W2G 2026-10-05): the companion's status is a LUI plate now (TodCompanionPlate.lua), built inside
  // tod_upgrade.lua's HudOnly - the layer the veil hides - so it goes with the rest of the HUD. (The server hudelem
  // bar it replaced tested the owner's tod_menu_frozen / tod_solo_upg_active itself; none is left to test.)
  ok(read('ui/uieditor/menus/hud/tod_upgrade.lua').includes('HudOnly:addElement( CompanionPlate )') && !/NewClientHudElem/.test(ptn), 'the companion status plate hides under the veil (built in HudOnly; no server hudelem left)');
  ok(read('scripts/zm/zm_tod2_cybercity/_tod_elite_hp.gsc').includes('IS_TRUE( p.tod_menu_frozen ) || IS_TRUE( p.tod_solo_upg_active )'), 'the elite health bars hide for a veiled player');
}

// 7. PASS 3 (docs/188, 2026-09-29): the machine comes alive - the lockstep pairs it added
{
  const pour = defs.TOD_SPIN_POUR_SECS;
  const pourMs = Number((lua.match(/POUR_MS = (\d+)/) || [])[1]);
  const slamMs = Number((lua.match(/SLAM_MS = (\d+)/) || [])[1]);
  ok(pour && pourMs && slamMs && Math.abs(pour * 1000 - (pourMs + 350)) < 1, 'the reel waits for the slam (0.35 s) + the luck pour: TOD_SPIN_POUR_SECS ' + pour + ' vs POUR_MS ' + pourMs);
  ok(slamMs <= 350, 'the slam lands inside the open beat');
  ok(spin.includes('spin_wait( TOD_SPIN_POUR_SECS'), 'the server waits for the pour before the first step');
  const defNames = [...ptn.matchAll(/define\( (\d), "([^"]+)"/g)].sort((a, b) => a[1] - b[1]).map(m => m[2]);
  const luaComp = ((lua.match(/COMPANIONS = \{([^}]*)\}/) || [])[1] || '').split(',').map(x => x.trim().replace(/"/g, '')).filter(Boolean);
  ok(defNames.length === 4 && JSON.stringify(defNames) === JSON.stringify(luaComp), 'FOR YOUR <companion> names in _tod_partners order: ' + luaComp);
  ok(luaComp.every(n => glyph.test(n)), 'every companion name is drawable in the typeface');
  ok(/elseif luck >= 50 then/.test(lua) && /if luck >= 100 then/.test(lua) && /\( c \+ r \) \* 0\.25/.test(lua), 'the odds bar carries the half-bar / full-bar guarantees and the 25 in 100 Legendary share');
  ok(body('spin_open').includes('self.tod_spin_slots_shown') && spin.includes('self.tod_spin_slots_shown = slots;') && spin.includes('self.tod_spin_slots_shown = undefined;'), 'the companion slots show from the open (and on a resume), and the field is cleared at the end');
}

// ---- THE AI COMPANION ROW (user 2026-09-29: "there is an upgrade in the pause menu. That shows AI
// companion ... wire it all up. Make sure the upgrades are there as well"). The server pushes the held
// companion's state on change; the always-open HUD reel records it and the items; the pause menu and the
// scoreboard draw it from ONE describe (TodSpinReel.lua). tools/ui_mockup/render_menus.py renders the worst cases.
{
  const pm = read('ui/uieditor/menus/StartMenu/AetheriumStartMenu.lua');
  const sb = read('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumScoreboard.lua');
  const ps = ptn.split('function push_state(')[1].split('\nfunction ')[0];
  ok(ptn.includes('#precache( "eventstring", "tod_ptn_state" );') && ps.includes('LuiNotifyEvent( &"tod_ptn_state", 4, comp + 1, state, value, built )'), 'the companion state is a precached int event: companion, state, value, built mask');
  ok(ps.includes('if ( isdefined( s.ui_sig ) && s.ui_sig == sig ) return;') && /tick\( s \);\s*push_hud\( s \);\s*push_state\( s \);/.test(ptn), 'pushed from the manager tick, only when what the row says changes (after the PK08 status plate\'s push_hud)');
  ok(ptn.split('function push_items(')[1].split('\nfunction ')[0].includes('p.tod_ptn.ui_sig = undefined;') && ptn.split('function player_spawned(')[1].split('\nfunction ')[0].includes('ui_sig = undefined'), 'an equip / swap / dismiss / socket / respawn re-sends it (never a stale partner)');
  ok(/#define TOD_PTN_UI_NONE\s+0/.test(ptn) && /#define TOD_PTN_UI_ACTIVE\s+1/.test(ptn) && /#define TOD_PTN_UI_REBUILD\s+2/.test(ptn) && /#define TOD_PTN_UI_DEPLOYING\s+3/.test(ptn), 'state codes 0..3 (LOCKSTEP the Lua describe)');
  ok(lua.includes('name ~= "tod_ptn_state"') && lua.includes('rec.value, rec.built = tonumber( d[ 3 ] ) or 0, tonumber( d[ 4 ] ) or 0') && lua.includes('rec.items[ comp ] = {'), 'the HUD reel records the state and each companion\'s items');
  ok(lua.includes('function CoD.TodCompanionDescribe()') && lua.includes('state == 1') && lua.includes('state == 2') && lua.includes('state == 3') && lua.includes('" sec"'), 'one describe says the row: active + health, destroyed + seconds (" sec"), on its way');
  ok(lua.includes('while #table.concat( names, ", " ) > 35 do'), 'the item line always fits the pause row (long names give way to chip labels)');
  ok(pm.includes('TOD_PARTNER_ROW.view()') && pm.includes('cd.portrait') && pm.includes('info.chip') && !pm.includes('COMING SOON'), 'the pause menu draws the live row: portrait, rarity chips, items, state (no placeholder)');
  ok(sb.includes('TOD_PARTNER_SB.view()') && sb.includes('cd.portrait') && sb.includes('info.chip') && !sb.includes('COMING SOON'), 'the scoreboard draws the same live row');
  ok(read('tools/ui_mockup/render_menus.py').includes('state = 2, value = 45'), 'the menu render gate covers the worst companion row');
}

// ---- EXECUTED: the shipping push_state() (translated) through every companion state, the health /
// rebuild encodings, the change gate, the re-send and the transition-only log.
{
  const ptnBody = name => {
    const clean = ptn.replace(/\/\/[^\n]*/g, '');
    const start = clean.indexOf('function ' + name + '(');
    assert(start >= 0, name);
    const a = clean.indexOf('{', start); let b = a + 1, depth = 1;
    while (depth) { if (clean[b] === '{') depth++; if (clean[b] === '}') depth--; b++; }
    return clean.slice(a + 1, b - 1);
  };
  const ui = {};
  for (const m of ptn.matchAll(/#define (TOD_PTN_UI_\w+)\s+(\d+)/g)) ui[m[1]] = Number(m[2]);
  const js = ptnBody('push_state')
    .replace(/\bp LuiNotifyEvent\( &"tod_ptn_state",/g, 'p.LuiNotifyEvent("tod_ptn_state",')
    .replace(/\bp GetEntityNumber\(\)/g, 'p.GetEntityNumber()')
    .replace(/\bint\(/g, 'Math.trunc(');
  const cenv = Object.assign({ array: (...a) => a, isdefined: x => x !== undefined && x !== null, isplayer: x => !!(x && x.player),
    isalive: x => !!(x && x.alive), IS_TRUE: x => x === true, now: 0, GetTime: () => cenv.now,
    logs: [], log: m => cenv.logs.push(m), max_hp: (s, id) => s.max[id] }, ui);
  vm.createContext(cenv);
  vm.runInContext('function push_state(s){let p,comp,state,value,bits,built,i,now,top,sig,moment;' + js + '}', cenv);
  const fresh = chosen => {
    const sent = [];
    const p = { player: true, LuiNotifyEvent: (...a) => sent.push(a.slice(2)), GetEntityNumber: () => 0 };
    return { sent, s: { owner: p, chosen, built: [false, false, false, false], hp: [1800, 1000, 1400, 2200], max: [1800, 1000, 1400, 2200], ready: [0, 0, 0, 0] } };
  };
  const J = JSON.stringify;
  ok(Object.keys(ui).length === 4, 'four companion-row state codes');
  let t = fresh(-1); t.s.built = [true, false, false, true]; cenv.push_state(t.s);
  ok(J(t.sent) === J([[0, 0, 0, 9]]), 'none held: companion 0, state 0, built mask 9 ' + J(t.sent));
  cenv.push_state(t.s); ok(t.sent.length === 1, 'unchanged = no second event');
  t = fresh(3); t.s.actor = { alive: true }; cenv.push_state(t.s);
  ok(J(t.sent[0]) === J([4, ui.TOD_PTN_UI_ACTIVE, 100, 0]), 'active at full health = 100 ' + J(t.sent));
  t.s.hp[3] = 2190; cenv.push_state(t.s); ok(t.sent.length === 1, 'a scratch inside the top 5 % step sends nothing');
  t.s.hp[3] = 2080; cenv.push_state(t.s); ok(t.sent[1][2] === 95, '94.5 % reads 95');
  t.s.hp[3] = 1; cenv.push_state(t.s); ok(t.sent[2][2] === 5, 'a living companion never reads 0 (1 hp = 5)');
  t = fresh(0); cenv.now = 1000; t.s.ready[0] = 1000 + 44001; cenv.push_state(t.s);
  ok(J(t.sent[0]) === J([1, ui.TOD_PTN_UI_REBUILD, 45, 0]), '44.001 s to rebuild reads 45 ' + J(t.sent));
  cenv.now = 1000 + 44000; cenv.push_state(t.s); ok(t.sent[1][2] === 1, 'the last millisecond reads 1');
  cenv.now += 1; cenv.push_state(t.s); ok(t.sent[2][1] === ui.TOD_PTN_UI_DEPLOYING, 'rebuilt but not out = on its way');
  t.s.actor = { alive: true }; cenv.push_state(t.s); ok(t.sent[3][1] === ui.TOD_PTN_UI_ACTIVE, 'out = active');
  const n0 = t.sent.length; t.s.ui_sig = undefined; cenv.push_state(t.s);
  ok(t.sent.length === n0 + 1 && J(t.sent[n0]) === J(t.sent[n0 - 1]), 'a cleared signature re-sends the same state');
  cenv.logs = []; t = fresh(2); t.s.actor = { alive: true };
  for (const hp of [1400, 1300, 1200, 1100, 1000]) { t.s.hp[2] = hp; cenv.push_state(t.s); }
  ok(t.sent.length === 5 && cenv.logs.length === 1, 'health steps send, the log keeps transitions only (' + t.sent.length + ' / ' + cenv.logs.length + ')');
  cenv.push_state({ owner: undefined, chosen: 0, built: [], hp: [], ready: [] }); ok(true, 'no owner: no call, no throw');
}

// ---- THE NEAR MISS + THE HOT STREAK (docs/201, user 2026-10-02): the shipping near_plan / roll_rarity / step_ms,
// executed. THE LINE: the prize is rolled first at the shown odds, the near miss only dresses it, never shows what
// could not have come, and heat is a real, displayed odds change.
{
  let seed = 4242;   // mulberry32, so the rates below are exact run to run
  env.rng = () => { seed = (seed + 0x6D2B79F5) | 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const heldSlots = [3 * 4 + 2, 1 * 4 + 3, 6 * 4 + 0];   // HOLLOW EPIC, PLATING LEGENDARY, ARC COMMON
  const N = 60000;
  let short = 0, past = 0, shortLegLow = 0, shortLow = 0, shortEpicLeg = 0, shortEpic = 0;
  for (let i = 0; i < N; i++) {
    const rar = i % 3;                                 // COMMON / RARE / EPIC prizes in equal measure
    const near = env.near_plan(rar, heldSlots);
    if (near === 0) continue;
    const kind = Math.trunc(near / 64), tile = near - kind * 64;
    const titem = Math.trunc(tile / 4), trar = tile - titem * 4;
    assert.ok(kind === 1 || kind === 2, 'a near miss is STOPPED SHORT or SLIPPED PAST, got ' + kind);
    assert.ok(trar > rar, 'the teased tile is better than the prize (' + trar + ' over ' + rar + ')');
    assert.ok(titem >= 1 && titem <= 9, 'the teased tile is a real item');
    assert.ok(env.item_rarity({ tod_spin_items: [heldSlots] }, 0, titem) < trar, 'the teased item would really have been new or an upgrade (never what could not have come)');
    if (kind === 2) { past++; assert.ok(trar === 3, 'SLIPPED PAST always slips past a LEGENDARY'); }
    else {
      short++;
      if (rar === 2) { shortEpic++; if (trar === 3) shortEpicLeg++; }
      else { shortLow++; if (trar === 3) shortLegLow++; }
    }
  }
  const pct = x => 100 * x / N;
  ok(Math.abs(pct(short) - defs.TOD_SPIN_NEAR_SHORT_PCT) < 1.0, 'STOPPED SHORT on ' + pct(short).toFixed(1) + ' in 100 non-Legendary spins (the knob says ' + defs.TOD_SPIN_NEAR_SHORT_PCT + ')');
  ok(Math.abs(pct(past) - defs.TOD_SPIN_NEAR_PAST_PCT) < 1.0, 'SLIPPED PAST on ' + pct(past).toFixed(1) + ' in 100 (the knob says ' + defs.TOD_SPIN_NEAR_PAST_PCT + ')');
  ok(Math.abs(pct(short + past) - 30) < 1.5, 'about 30 in 100 non-Legendary spins carry a near miss (Kassinove & Schare 2001), got ' + pct(short + past).toFixed(1));
  ok(shortEpic > 0 && shortEpicLeg === shortEpic, 'an EPIC prize stopped short always teases a LEGENDARY');
  ok(Math.abs(100 * shortLegLow / shortLow - defs.TOD_SPIN_NEAR_LEG_PCT) < 2.5, 'a lesser prize stopped short teases a LEGENDARY ' + (100 * shortLegLow / shortLow).toFixed(1) + ' in 100 (the knob says ' + defs.TOD_SPIN_NEAR_LEG_PCT + ')');
  let legTeased = 0;
  for (let i = 0; i < 2000; i++) if (env.near_plan(3, heldSlots) !== 0) legTeased++;
  ok(legTeased === 0, 'a LEGENDARY prize is never dressed as a near miss');
  env.rng = null;
  // the wire: heat * 256 + kind * 64 + tile never outgrows the smallest int the open already carries
  ok(3 * 256 + 2 * 64 + 39 === 935 && 935 < 100 * 64 + 30, 'the packed tease (max 935) is smaller than the open\'s own luck * 64 + land');
  // the step timing: only the LAST step of a near miss grows, by the hang or the hold; a Legendary's crawl is its own
  for (let k = 1; k < defs.TOD_SPIN_STEPS; k++) ok(env.step_ms(k, 1, 1) === env.step_ms(k, 1, 0) && env.step_ms(k, 1, 2) === env.step_ms(k, 1, 0), 'step ' + k + ' is untouched by a near miss');
  const S = defs.TOD_SPIN_STEPS;
  ok(env.step_ms(S, 1, 1) - env.step_ms(S, 1, 0) === defs.TOD_SPIN_NEAR_HANG_MS, 'STOPPED SHORT adds the hang to the last step');
  ok(env.step_ms(S, 0, 2) - env.step_ms(S, 0, 0) === defs.TOD_SPIN_PAST_HOLD_MS, 'SLIPPED PAST adds the creep across the jackpot');
  ok(env.step_ms(S, 3, 1) === env.step_ms(S, 3, 0), 'a Legendary prize keeps its own crawl (it is never a near miss)');
  // LOCKSTEP with the reel
  const luaNum = k => Number((lua.match(new RegExp('\\b' + k + ' = (\\d+)')) || [])[1]);
  ok(luaNum('NEAR_HANG_MS') === defs.TOD_SPIN_NEAR_HANG_MS && luaNum('PAST_HOLD_MS') === defs.TOD_SPIN_PAST_HOLD_MS && luaNum('SETTLE_MS') === defs.TOD_SPIN_SETTLE_MS,
    'the reel draws the hang / creep / settle the server waits (' + luaNum('NEAR_HANG_MS') + ' / ' + luaNum('PAST_HOLD_MS') + ' / ' + luaNum('SETTLE_MS') + ')');
  const luaHeat = ((lua.match(/HEAT_MULT = \{ \[ 0 \] = ([^}]*)\}/) || ['', ''])[1]).split(',').map(x => Number(x.trim())).filter(x => !isNaN(x));
  ok(HEAT_MULT.length === 4 && JSON.stringify(luaHeat) === JSON.stringify(HEAT_MULT), 'the reel heats its odds by the server\'s table: ' + HEAT_MULT + ' vs ' + luaHeat);
  // THE HOT STREAK in the spin's roll: sweep the roll at every heat and compare with an independent mirror
  const mirror = (L, hm) => {   // _tod_shop roll_rarity's line, heated, then the guarantees (no 25 in 100 roll: ri 99)
    let c = 56 - 0.20 * L, r = 27 + 0.09 * L, e = 13 + 0.07 * L, l = 100 - c - r - e;
    c -= (e * hm - e) + (l * hm - l); e *= hm; l *= hm;
    if (L >= 100) return [0, 0, e + c + r, l];
    if (L >= 50) return [0, r + c, e, l];
    return [c, r, e, l];
  };
  for (let h = 0; h <= 3; h++) for (const L of [0, 30, 49, 50, 80, 100]) {
    env.self = { tod_luck_heat: h };
    const got = dist(L, 99), want = mirror(L, HEAT_MULT[h]);
    ok(got.every((x, i) => Math.abs(x - want[i]) < 0.02), `heat ${h} luck ${L}: the roll is ${got.map(x => x.toFixed(2))} (mirror ${want.map(x => x.toFixed(2))})`);
    ok(want[0] >= 0, 'COMMON never goes below 0');
  }
  env.self = {};
  // the order inside spin(): the prize first, the near miss after it from what it is, the streak after the land
  const sp = body('spin');
  ok(sp.indexOf('rar = self roll_rarity( luck );') < sp.indexOf('near = near_plan( rar, slots );') && sp.indexOf('prize = item * 4 + rar;') < sp.indexOf('near = near_plan( rar, slots );'), 'the near miss is planned AFTER the prize is rolled');
  ok((sp.match(/\bprize = /g) || []).length === 1, 'nothing after the roll ever rewrites the prize');
  ok(sp.includes('tease = hot * 256 + near;') && sp.includes('hot = tod_luck::heat( self );'), 'the open carries the heat the spin rolled with');
  ok(sp.indexOf('&"tod_spin_land"') < sp.indexOf('tod_luck::streak_result( self, rar + 1, "spin", TOD_SPIN_STREAK_FB_SECS );'), 'the spin reports its prize to the streak after the reel shows it');
  ok(sp.includes('if ( nkind > 0 ) self thread spin_near_after( nkind, ntile );') && sp.includes('else self thread spin_vo_land( rar );'), 'a near miss takes the landing line\'s place');
  const na = body('spin_near_after');
  ok(na.includes('"tod_spin_near"') && na.includes('vo_cls( "near", 1, "tod_spin_vo_near_"'), 'the "so close" and the dealer\'s word (through vo_cls) follow a near miss');
  ok(sp.includes('"tod_spin_teeter"') && sp.includes('tile_rar( ntile ) >= 3 ) self PlayLocalSound( "tod_pull_beat" )'), 'a LEGENDARY on the seam gets the jackpot heartbeat, a lesser one the teeter');
  ok(sp.includes('if ( hot >= 2 ) self.tod_spin_vo_pour = self vo_say( "tod_spin_vo_hot_"'), 'a player HEATING UP or ON FIRE hears the dealer notice it');
  ok(luckGsc.includes('#precache( "eventstring", "tod_luck_heat" );') && lua.includes('"tod_luck_heat"'), 'the heat event is precached and the reel hears it');
  const nearCsv = read('sound/aliases/tod_near.csv');
  for (const a of ['tod_spin_teeter', 'tod_spin_near']) ok(new RegExp('^' + a + ',.*,2d,', 'm').test(nearCsv), 'alias exists (2D, tod_near.csv): ' + a);
}


// ---- THE DEALER'S GIFT (docs/209, user 2026-10-04: "This concept of finding your parts etc is a bit much to get into
// the black market situation. I think he should gift you a random AI companion on first use that doesnt use up your
// luck. Then you can continue to upgrade"). A player with no companion is GIVEN one at the counter: a short reel of the
// four companions, free, his luck shown and NEVER spent. Executed: the dispatcher's rule, the pick, the reel timing and
// the whole gift() against stubbed engine calls (the event sequence, the hand-off at the landing, nothing paid).
{
  for (const m of gsc.matchAll(/#define (TOD_GIFT_\w+)\s+([-\d.]+)/g)) env[m[1]] = defs[m[1]] = Number(m[2]);
  for (const m of gsc.matchAll(/#define (TOD_SPIN_CODE_GIFT)\s+([-\d.]+)/g)) env[m[1]] = defs[m[1]] = Number(m[2]);
  ok(defs.TOD_GIFT_TILE_BASE === 44 && defs.TOD_SPIN_CODE_GIFT === 8 && defs.TOD_GIFT_SLOTS_MODE === 4, 'the gift tile base / code / slots mode are defined');
  // the gift's tiles can never be read as anything else: items are item * 4 + rarity <= 39, CURSED is 60, a tease < 64
  const giftTiles = [1, 2, 3, 4].map(c => defs.TOD_GIFT_TILE_BASE + c);
  ok(giftTiles.every(v => v > 9 * 4 + 3 && v !== defs.TOD_SPIN_CURSED_TILE && v < 64), 'gift tiles 45..48 never collide with an item tile, CURSED or the packed tease');
  // LOCKSTEP with the reel (TodSpinReel.lua P3.GIFT) and with the companions _tod_partners defines
  const G = (lua.match(/GIFT = \{ base = (\d+), code = (\d+), slotsMode = (\d+), n = (\d+),/) || []).slice(1).map(Number);
  ok(G.length === 4 && G[0] === defs.TOD_GIFT_TILE_BASE && G[1] === defs.TOD_SPIN_CODE_GIFT && G[2] === defs.TOD_GIFT_SLOTS_MODE && G[3] === defs.TOD_GIFT_COMPANIONS, 'LOCKSTEP the reel: ' + G);
  ok([...ptn.matchAll(/^\s*define\( \d, "/gm)].length === defs.TOD_GIFT_COMPANIONS, 'TOD_GIFT_COMPANIONS = the companions _tod_partners defines');
  for (const k of ['short', 'role']) {
    const arr = (lua.match(new RegExp(k + ' = \\{([^}]*)\\}')) || ['', ''])[1].split('",').filter(s => s.trim());
    ok(arr.length === defs.TOD_GIFT_COMPANIONS, 'P3.GIFT.' + k + ' names all ' + defs.TOD_GIFT_COMPANIONS + ' companions');
  }
  // the dispatcher: the trigger gives a companion-less player the gift, everyone else the spin
  ok(/if \( gift_wanted\( p \) \) p thread gift\( self\.tod_shop \);\s*else p thread spin\( self\.tod_shop \);/.test(body('spin_trigger_loop')), 'the trigger gives a companion-less player the gift, everyone else the spin');
  ok(body('gift_wanted').includes('p.tod_ptn.chosen < 0'), 'gift_wanted = the prompts\' own rule (no companion)');
  ok(body('spin_refusal').includes('if ( gift_wanted( p ) ) return "no_companion";') && !/tod_spin_vo_no_companion|Equip a companion first/.test(gsc), 'nothing refuses a companion-less player out loud any more: the gift answers him');
  // the greeting: a companion-less player hears the gift offer (no chance roll, a cooldown against pacing)
  const ap = body('vo_approach_watch');
  ok(ap.includes('if ( gift_wanted( p ) )') && ap.includes('"tod_spin_vo_gift_offer_"') && ap.includes('TOD_GIFT_VO_OFFER_CD'), 'the walk-up offers the gift to a player with no companion');
  // THE LATCH SURVIVES A SPIN (LT-rest 2026-10-05, the 17:33 run: GIFT_END at ms=368450, a class greeting 150 ms later):
  // mid-spin the walk-up latch is kept, so a spin or a gift ending at the counter is never a fresh walk-up.
  {
    const keepsLatch = /if \( IS_TRUE\( p\.tod_spin_locked \) \|\| IS_TRUE\( p\.tod_spin_busy \) \)\s*\{\s*p\.tod_spin_vo_held = true;\s*continue;\s*\}/;
    const clearsLatch = /IS_TRUE\( p\.tod_spin_locked \)[^{]*\{\s*p\.tod_spin_vo_near = false;/;
    ok(keepsLatch.test(ap) && !clearsLatch.test(ap), 'mid-spin the walk-up latch is kept: the end of a spin or gift is not a walk-up');
    ok(ap.includes('VO_GREET_HOLD'), 'the kept latch is logged as the spin ends ([TOD_SHOP] VO_GREET_HOLD)');
    // NEGATIVE CONTROL: the 17:33 build's guard cleared the latch while the player was locked in a spin
    const old = 'if ( !isdefined( counter ) || !isalive( p ) || IS_TRUE( p.tod_spin_locked ) || IS_TRUE( p.tod_spin_busy ) )\r\n            {\r\n                p.tod_spin_vo_near = false;\r\n                continue;\r\n            }';
    ok(clearsLatch.test(old) && !keepsLatch.test(old), 'negative control: the old mid-spin latch reset is caught');
  }

  // THE PICK, executed: random, and in co-op a companion nobody else holds while one is left
  const genv = Object.assign({ array: (...a) => a, isdefined: x => x !== undefined && x !== null, ri: 0, players: [],
    RandomInt: n => Math.min(n - 1, genv.ri), GetPlayers: () => genv.players }, defs);
  vm.createContext(genv);
  const callEach = c => c.replace(/foreach \( (\w+) in (\w+)\(\) \)/g, 'for (const $1 of $2())');   // foreach over a call: the shared translate stops at its )
  const tr = c => translate(callEach(c)).replace(/\bself\b/g, 'me');
  vm.runInContext(`function gift_pick(p){let held,i,o,c,pool;${tr(body('gift_pick'))}}`, genv);
  vm.runInContext(`function gift_step_ms(k){let t,ms;${tr(body('gift_step_ms'))}}`, genv);
  const pl = c => ({ tod_ptn: { chosen: c } });
  const sweep = (me, n) => { const got = new Set(); for (let r = 0; r < n; r++) { genv.ri = r; got.add(genv.gift_pick(me)); } return [...got].sort(); };
  let me = pl(-1); genv.players = [me];
  ok(JSON.stringify(sweep(me, 4)) === '[0,1,2,3]', 'solo: any of the four (' + sweep(me, 4) + ')');
  genv.players = [me, pl(1), pl(3)];
  ok(JSON.stringify(sweep(me, 4)) === '[0,2]', 'co-op: never a companion a teammate holds while one is free (' + sweep(me, 4) + ')');
  genv.players = [me, pl(0), pl(1), pl(2)];
  ok(JSON.stringify(sweep(me, 4)) === '[3]', 'three teammates with three companions: the fourth');
  genv.players = [me, pl(0), pl(1), pl(2), pl(3)];
  ok(JSON.stringify(sweep(me, 4)) === '[0,1,2,3]', 'all four taken: any of them (never an empty pick)');
  genv.players = [me, pl(-1), pl(undefined), { }];
  ok(JSON.stringify(sweep(me, 4)) === '[0,1,2,3]', 'teammates with no companion (or no state) take nothing out of the pool');
  me.tod_ptn.chosen = 2; genv.players = [me, pl(0)];
  ok(JSON.stringify(sweep(me, 4)) === '[1,2,3]', 'his own (a dismissed test pick) never counts against him');

  // THE REEL'S TIMING, executed: the spin's curve over the same 30 tiles, never slower than a spin, ~4.6 s
  let tot = 0, prev = 0, mono = true, slower = false;
  for (let k = 1; k <= defs.TOD_SPIN_STEPS; k++) {
    const ms = genv.gift_step_ms(k); tot += ms;
    if (ms < prev || ms % 50 || ms < 50) mono = false;
    if (ms > env.step_ms(k, 0, 0)) slower = true;
    prev = ms;
  }
  ok(mono && !slower, 'the gift reel only slows, on server frames, never slower than a spin at the same tile');
  ok(tot >= 3500 && tot <= 5500, 'the gift reel reads in 3.5..5.5 s, got ' + tot);
  ok(genv.gift_step_ms(defs.TOD_SPIN_STEPS) === defs.TOD_GIFT_STEP_MAX_MS, 'its last tile crawls at TOD_GIFT_STEP_MAX_MS');
  const rs = read('tools/ui_mockup/render_spin.py');
  ok(new RegExp('GIFT_MAX\\s*=\\s*' + defs.TOD_GIFT_STEP_MAX_MS + '\\b').test(rs) && rs.includes('def gift_step_ms('), 'render_spin.py mirrors the gift reel (LOCKSTEP TOD_GIFT_STEP_MAX_MS)');

  // THE WHOLE GIFT, executed against stubbed engine calls: what the player's screen and ears get, in order
  const ev = [];
  const fenv = Object.assign({ array: (...a) => a, isdefined: x => x !== undefined && x !== null, IS_TRUE: x => x === true,
    isalive: x => !!x && x.alive !== false, isplayer: x => !!x && x.player === true, Math, t: 0,
    level: { tod_upgrade_pause: false }, RandomInt: n => 0, RandomIntRange: (a, b) => 4242,
    GetPlayers: () => fenv.players, players: [], log: m => ev.push(['log', m.split(' ')[0]]),
    local_to_world: () => [0, 0, 0], GetTime: () => Math.round(fenv.t * 1000),
    tod_luck_get: p => p.luck, play_sound_at_origin: (o, a) => ev.push(['snd3d', a]), fx_burst: () => ev.push(['fx']),
    TOD_SPIN_SPARK_FX: 'spark' }, defs);
  vm.createContext(fenv);
  const ftr = c => callEach(c)
    .replace(/(?:self|level) endon\([^;]+;/g, '')
    .replace(/\bp laststand::player_is_in_laststand\(\)/g, 'p.down')
    .replace(/\[\[ level\.tod_partner_gift_fn \]\]\(/g, 'level.tod_partner_gift_fn(')
    .replace(/\btod_luck::get\(/g, 'tod_luck_get(')
    .replace(/\btod_perk_scatter::play_sound_at_origin\(/g, 'play_sound_at_origin(')
    .replace(/\blevel thread (\w+)\(/g, '$1(')
    .replace(/\bself thread (\w+)\(/g, 'self.$1(')
    .replace(/\bself (\w+)\(/g, 'self.$1(')
    .replace(/&"/g, '"')
    .replace(/foreach \( (\w+) in ([^)]+) \)/g, 'for (const $1 of $2)')
    .replace(/\.size\b/g, '.length')
    .replace(/\bint\(/g, 'Math.trunc(')
    .replace(/wait ([^;]+);/g, 't += $1;');
  for (const [n, args, locals] of [['gift_wanted', 'p', ''], ['gift_refusal', 'p', ''], ['gift_pick', 'p', 'held,i,o,c,pool'], ['gift_step_ms', 'k', 't,ms'],
    ['gift', 'shop', 'num,reason,comp,luck,seed,prize,counter,last_tick,k,ms,given']])
    vm.runInContext(`function ${n}(${args}){${locals ? 'let ' + locals + ';' : ''}${ftr(body(n))}}`, fenv);
  const mkPlayer = (luck, chosen) => {
    const self = { player: true, alive: true, down: false, luck, tod_ptn: { chosen }, tod_spin_busy: true,
      GetEntityNumber: () => 0, LuiNotifyEvent: (n, c, ...a) => ev.push([n, ...a]), PlayLocalSound: a => ev.push(['snd', a]),
      spin_lock: on => ev.push(['lock', on]), spin_wait_world: () => ev.push(['wait_world']),
      spin_open: (seed, prize, tease, l, at) => ev.push(['open', prize, tease, l, at]),
      vo_say: a => (ev.push(['vo', a]), true), vo_say_later: a => ev.push(['vo_later', a]), gift_vo_land: a => ev.push(['vo_land', a]),
      spin_wait: (secs) => { fenv.t += secs; return false; }, spin_release_use: () => ev.push(['release']), gift_show_result: () => ev.push(['repaint']) };
    return self;
  };
  let handed = null;
  fenv.level.tod_partner_gift_fn = (p, c) => { handed = [p, c]; ev.push(['handed', c]); p.tod_ptn.chosen = c; return true; };
  const self = mkPlayer(64, -1); fenv.self = self; fenv.players = [self];
  fenv.gift({ origin: [0, 0, 0], yaw: 0 });
  const names = ev.map(e => e[0]);
  const at = n => names.indexOf(n);
  ok(handed && handed[0] === self && handed[1] === 0, 'the gift hands HIS companion to _tod_partners (RandomInt 0 = the first free one)');
  ok(at('lock') >= 0 && ev[at('lock')][1] === true && at('lock') < at('open'), 'locked (frozen, untargetable) before the machine opens');
  const open = ev[at('open')];
  ok(open[1] === defs.TOD_GIFT_TILE_BASE + 0 + 1 && open[2] === 0 && open[3] === 64 && open[4] === 0, 'the reel opens on his companion tile with no tease and HIS luck (64) for the box: ' + open);
  const steps = ev.filter(e => e[0] === 'tod_spin_step');
  ok(steps.length === defs.TOD_SPIN_STEPS && steps.every((s, i) => s[1] === i + 1 && s[2] === genv.gift_step_ms(i + 1)), 'thirty steps on the gift curve');
  const land = ev.findIndex(e => e[0] === 'tod_spin_land');
  ok(land > 0 && ev[land][1] === open[1] && ev[land][2] === defs.TOD_SPIN_CODE_GIFT, 'it lands on his companion with the gift code');
  ok(at('handed') > land, 'the companion is his the moment the reel SHOWS it (never before)');
  const slots = ev.findIndex(e => e[0] === 'tod_spin_slots');
  ok(slots > at('handed') && ev[slots].slice(1).join(',') === '0,0,0,' + defs.TOD_GIFT_SLOTS_MODE, 'then its three empty slots in the gift mode (SPIN TO FILL)');
  const end = ev.findIndex(e => e[0] === 'tod_spin_end');
  const unlock = ev.findIndex(e => e[0] === 'lock' && e[1] === false);
  ok(end > slots && unlock > end && self.tod_spin_busy === false, 'the panel drops, THEN control returns (the companion deploys on the next manager tick)');
  ok(ev.some(e => e[0] === 'vo' && /^tod_spin_vo_gift_spin_/.test(e[1])) && ev.some(e => e[0] === 'vo_land' && /^tod_spin_vo_gift_land_/.test(e[1])), 'his two gift lines play');
  const gl = body('gift_vo_land');
  ok(gl.includes('wait TOD_GIFT_VO_LAND_AT;') && gl.includes('i < TOD_GIFT_VO_LAND_WAIT * 20 && isdefined( self.tod_spin_vo_until ) && GetTime() < self.tod_spin_vo_until') && gl.includes('self vo_say( alias )'), 'the landing line WAITS for his reel line (never dropped by it, never over it)');
  ok(defs.TOD_GIFT_VO_LAND_WAIT >= 1.5 && defs.TOD_GIFT_VO_LAND_WAIT <= 4, 'the wait is bounded (1.5..4 s)');
  ok(!names.includes('snd') || !ev.some(e => e[0] === 'snd' && e[1] === 'tod_spin_coin'), 'no coin: nothing is paid');
  ok(Math.abs(fenv.t - (defs.TOD_GIFT_OPEN_SECS + steps.reduce((a, s) => a + s[2], 0) / 1000 + defs.TOD_GIFT_READ_SECS)) < 0.01, 'the whole gift lasts the open + the reel + the read (' + fenv.t.toFixed(2) + ' s)');
  // THE USER'S RULE, structurally: the gift body never spends luck, points or the streak, never counts as a spin
  const gb = body('gift');
  for (const bad of ['tod_luck::spend', 'minus_to_player_score', 'streak_result', 'tod_spin_count', 'tod_spin_coin', 'roll_rarity'])
    ok(!gb.includes(bad), 'the gift never touches ' + bad);
  ok(body('spin').includes('tod_luck::spend( self )'), 'control: the ordinary spin still spends the luck (so the check above can fail)');
  // THE POOL: while the reel runs the slot row shows the four companions; spin_open sends it (and on every resume)
  ok(body('spin_open').includes('if ( IS_TRUE( self.tod_gift_pool ) ) self LuiNotifyEvent( &"tod_spin_slots", 4, 0, 0, 0, TOD_GIFT_POOL_MODE );'), 'spin_open sends THE POOL while a gift reel runs (and so on a resume after a card deal)');
  ok(gb.indexOf('self.tod_gift_pool = true;') < gb.indexOf('self spin_open( seed, prize, 0, luck, 0 );') && gb.indexOf('self.tod_gift_pool = undefined;') < gb.indexOf('&"tod_spin_land", 2, prize, TOD_SPIN_CODE_GIFT'), 'the pool is up from the open until the landing');
  ok(/poolMode = (\d+)/.test(lua) && Number(lua.match(/poolMode = (\d+)/)[1]) === defs.TOD_GIFT_POOL_MODE && new Set([0, 1, 2, 3, defs.TOD_GIFT_SLOTS_MODE, defs.TOD_GIFT_POOL_MODE]).size === 6, 'LOCKSTEP the pool mode, distinct from every other slot-row mode');
  ok(/GIFT_POOL = 44, 8, 4, 5|GIFT_SLOTS, GIFT_POOL = 44, 8, 4, 5/.test(rs) && rs.includes("(0.0, 'tod_spin_slots', [0, 0, 0, GIFT_POOL])"), 'render_spin.py sends the pool with the open');
  ok(gb.split('\n').filter(l => /\bwait\b/.test(l) && !/spin_wait|wait_world|spin_release_use/.test(l)).every(l => /while \( IS_TRUE\( level\.tod_upgrade_pause \) \) wait 0\.1;/.test(l)), 'every wait in the gift gives way to a card deal (spin_wait), except the deal wait before the unlock');
  // the refusals, executed: down / menu / flying / already has one / no partner module
  const refuse = (mut) => { ev.length = 0; handed = null; const s2 = mkPlayer(30, -1); mut(s2); fenv.self = s2; fenv.players = [s2]; fenv.gift({ origin: [0, 0, 0], yaw: 0 }); return { s2, opened: ev.some(e => e[0] === 'open') }; };
  for (const [why, mut] of [['down', s => { s.down = true; }], ['menu', s => { s.tod_menu_frozen = true; }], ['flying', s => { s.tod_jumppad_flying = true; }], ['has_companion', s => { s.tod_ptn.chosen = 2; }]]) {
    const r = refuse(mut);
    ok(!r.opened && !handed && r.s2.tod_spin_busy === false && ev.some(e => e[0] === 'log' && e[1] === 'GIFT_REFUSED'), 'refused (' + why + '): no reel, nothing handed, the busy flag released');
  }
  const gf = fenv.level.tod_partner_gift_fn; fenv.level.tod_partner_gift_fn = undefined;
  ok(!refuse(() => {}).opened, 'refused when the companion module is not there');
  fenv.level.tod_partner_gift_fn = gf;
  // a card deal on screen when he presses: "wait your turn", like a spin
  ok(/if \( reason == "menu" \) self vo_say\( "tod_spin_vo_busy" \);/.test(gb), 'a card deal on screen: his "wait your turn"');
  // THE NUDGE: once per match, a moment after the counter first lights, to every player with no companion
  const nd = body('gift_nudge');
  ok(body('spin_trigger_place').includes('if ( !IS_TRUE( level.tod_gift_nudge_armed ) ) { level.tod_gift_nudge_armed = true; level thread gift_nudge(); }') && !body('activate').includes('gift_nudge'), 'the nudge is armed once, the first time a counter lights (outside activate: test_shop.js runs that body)');
  ok(nd.includes('wait TOD_GIFT_NUDGE_SECS;') && nd.includes('while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.5;') && nd.includes('!gift_wanted( p ) || IS_TRUE( p.tod_gift_nudged )') && nd.includes('IPrintLnBold'), 'it waits for the power moment and any card deal, then tells each companion-less player once');
  // NO STUB EFFECTS: the counter's blast was a gfx_debug_missing_fx stub until 2026-10-04 (drew nothing)
  const MT = 'C:/BO3Tools/TOD2Cybercity/share/raw/fx/';
  if (fs.existsSync(MT)) {
    const stub = f => { const q = MT + f + '.efx'; return fs.existsSync(q) && fs.readFileSync(q, 'utf8').includes('gfx_debug_missing_fx'); };
    ok(stub('electric/fx_elec_burst_lg_z270_os'), 'control: the retired blast IS a stub, so the check below can fail');
    for (const m of gsc.matchAll(/#define TOD_SPIN_\w+_FX\s+"([^"]+)"/g)) ok(!stub(m[1]), 'not a stub: ' + m[1]);
  }
  for (const m of gsc.matchAll(/#define TOD_SPIN_\w+_FX\s+"([^"]+)"/g)) {
    ok(gsc.includes('#precache( "fx", "' + m[1] + '" )'), 'precached: ' + m[1]);
    ok(new RegExp('^fx,' + m[1].replace(/\//g, '\\/') + '\\s*$', 'm').test(read('zone_source/zm_tod2_cybercity.zone')), 'zoned: ' + m[1]);
  }
}

console.log(`SPIN PASS: ${checks} checks; odds + guarantees, no dead spins, reel timing, server/reel lockstep (names, effects, odds, price, events), routing, zone, symmetric untargetable lock, dev-live shop; pass 2: per-player prompts, pause-aware waits, accident-proof choice (executed), card-reveal sounds, exit grace, HUD veil; pass 3: pour lockstep, companion names, odds guarantees, slots from the open; the pause menu / scoreboard AI COMPANION row (lanes + push_state executed); THE NEAR MISS + THE HOT STREAK (docs/201): near_plan, step timing, the packed open, the heated roll, the near / hot dealer lines; THE DEALER'S GIFT (docs/209): the dispatcher, the prompt, the pick (executed), the reel timing, free + no luck + no streak, the hand-off at the landing, LOCKSTEP with the reel.`);
