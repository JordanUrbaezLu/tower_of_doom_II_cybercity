// THE BOUND SOUL IS HIS (LT-fix 2026-10-05). The user's 17:33 run lost 5 of 15 Necromancer binds as
// "BIND_CANCEL why=lost alive=0": his own thrall killed the zombie he was lifting (thrall HELPER_KILL 0-200 ms
// before each cancel; the thrall's engine enemy WAS the bound zombie), and older runs show the hounds' bites and the
// Mangler's sweep / cannon doing the same. Executes the shipping bind_unshield / soul_kill against stubs and pins
// the order of the shield in bind_start / bind_drop / bind_finish, the helper_target skip and the stock contract
// the shield relies on. NEGATIVE CONTROL: the 15:10 soul_kill (a verbatim fixture) marks a bound zombie.
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const root = require('path').resolve(__dirname, '../..');
const src = fs.readFileSync(root + '/scripts/zm/zm_tod2_cybercity/_tod_necro_summon.gsc', 'utf8');
function body(name, text) {
  const clean = (text || src).replace(/\/\/[^\n]*/g, '');
  const start = clean.indexOf('function ' + name + '(');
  assert(start >= 0, 'function ' + name);
  const a = clean.indexOf('{', start); let b = a + 1, depth = 1;
  while (depth) { if (clean[b] === '{') depth++; if (clean[b] === '}') depth--; b++; }
  return clean.slice(a + 1, b - 1);
}
let checks = 0; const ok = (v, m) => { assert.ok(v, m); checks++; };

// 1. bind_start takes the shield AFTER it snapshots allowDeath, and names it in the BIND line
{
  const b = body('bind_start');
  const snap = b.indexOf('z.tod_necro_bind_allowdeath = z.allowDeath;'), off = b.indexOf('z.allowDeath = false;');
  ok(snap > 0 && off > snap && b.indexOf('z.tod_necro_shielded = true;') > 0, 'bind_start snapshots allowDeath, marks the shield, then sets it false');
  ok(b.indexOf('z.tod_necro_binder = self;') < off, 'the binder is stamped before the shield (one owner of the bound state)');
  ok(b.indexOf('z.allowDeath = false;') < b.indexOf('self bind_lift( z );'), 'the shield is up before the lift (the hold is the exposed moment)');
  ok(/" shield=1"/.test(b), 'the BIND log line carries shield=1 (the next user log proves the fixed build)');
}
// 2. bind_unshield, executed
{
  const env = { IS_TRUE: x => x === true, isdefined: x => x !== undefined && x !== null };
  vm.createContext(env);
  vm.runInContext(`function bind_unshield(){let was;${body('bind_unshield')}}`, env);
  const run = z => { env.self = z; return env.bind_unshield(); };
  let z = { allowDeath: false, tod_necro_shielded: true, tod_necro_bind_allowdeath: true };
  ok(run(z) === true && z.allowDeath === true && z.tod_necro_shielded === undefined && z.tod_necro_bind_allowdeath === undefined, 'unshield hands back the snapshot and clears the marks');
  ok(run(z) === -1 && z.allowDeath === true, 'a second unshield changes nothing (idempotent: bind_drop then bind_finish can never both write)');
  z = { allowDeath: false, tod_necro_shielded: true, tod_necro_bind_allowdeath: false };
  ok(run(z) === false && z.allowDeath === false, 'a zombie that could not die before the bind still cannot (the snapshot, never a fixed value)');
  z = { allowDeath: false, tod_necro_shielded: true };
  ok(run(z) === true && z.allowDeath === true, 'no snapshot recorded: it can die again (never left immortal)');
  z = { allowDeath: false };
  ok(run(z) === -1 && z.allowDeath === false, 'a zombie this module never shielded (a thrall: thrall_make) is left alone');
}
// 3. every exit hands it back, before anything that needs it mortal
{
  const d = body('bind_drop');
  ok(d.indexOf('self bind_unshield();') > 0 && d.indexOf('self bind_unshield();') < d.indexOf('if ( !IsAlive( self ) )'), 'bind_drop (every cancel, the owner_gone guard) unshields first');
  const f = body('bind_finish');
  const clr = f.indexOf('z.tod_necro_binder = undefined;'), un = f.indexOf('z bind_unshield();'), sk = f.indexOf('soul_kill( z, self, undefined, "bind", 0 );'), th = f.indexOf('self thrall_make( z );');
  ok(clr > 0 && un > clr && un < sk && un < th, 'bind_finish unshields after it clears the binder and before soul_kill / thrall_make');
  ok(/self bind_cancel\(/.test(f.slice(0, clr)), 'bind_finish\'s meter / slots refusal goes through bind_cancel -> bind_drop (unshielded)');
  ok(body('thrall_make').includes('guy.allowDeath = false;'), 'a thrall stays deathless after the conversion (stock Turned\'s own rule)');
}
// 4. soul_kill, executed: the helpers' and the bomb's one kill lane spares a bound zombie and does not MARK it
{
  const env = { IS_TRUE: x => x === true, isdefined: x => x !== undefined && x !== null, logs: [], threads: [] };
  env.soul_kill_run = (...args) => env.threads.push(args);   // the threaded kill, recorded (one entry per call)
  env.dev_log = m => env.logs.push(m);
  vm.createContext(env);
  const tr = t => t.replace(/\bz thread soul_kill_run\(/g, 'soul_kill_run(').replace(/\bz\.tod_necro_binder GetEntityNumber\(\)/g, 'z.tod_necro_binder.n')
    .replace(/\bz GetEntityNumber\(\)/g, 'z.n');
  vm.runInContext(`function soul_kill(z,owner,helper,why,delay){${tr(body('soul_kill'))}}`, env);
  const owner = { n: 0 };
  const bound = { n: 31, tod_necro_binder: owner }, plain = { n: 32 };
  env.soul_kill(bound, owner, { n: 30 }, 'mangler_sweep', 0);
  ok(bound.marked_for_death === undefined && env.threads.length === 0, 'a bound zombie is neither marked nor killed by a helper / the bomb');
  ok(env.logs.length === 1 && /^SOUL_SPARED target=31 why=mangler_sweep binder=0$/.test(env.logs[0]), 'SOUL_SPARED names the victim, the lane and the binder: ' + env.logs[0]);
  env.soul_kill(plain, owner, undefined, 'soul_bomb', 0.2);
  ok(plain.marked_for_death === true && env.threads.length === 1, 'an unbound zombie still dies the same way');
  bound.tod_necro_binder = undefined; env.soul_kill(bound, owner, undefined, 'bind', 0);
  ok(bound.marked_for_death === true && env.threads.length === 2, 'bind_finish (binder cleared) still tears the soul out for a hound / Mangler');
  // NEGATIVE CONTROL: the 15:10 soul_kill (verbatim) marked the bound zombie - which also made bind_finish's own
  // soul_kill skip it later and leave it alive under the new helper
  const OLD = 'function soul_kill( z, owner, helper, why, delay )\n{\n\tif ( !isdefined( z ) || IS_TRUE( z.marked_for_death ) ) return;\n\tz.marked_for_death = true;\n\tz thread soul_kill_run( owner, helper, why, delay );\n}\n';
  vm.runInContext(`function soul_kill_old(z,owner,helper,why,delay){${tr(body('soul_kill', OLD))}}`, env);
  const b2 = { n: 33, tod_necro_binder: owner }; env.soul_kill_old(b2, owner, undefined, 'hound_bite', 0);
  ok(b2.marked_for_death === true, 'negative control: the 15:10 soul_kill marks (and kills) a zombie mid-bind');
}
// 5. the helpers never pick a bound zombie; the companions do not either (_tod_partners)
{
  const h = body('helper_target');
  ok(/if \( isdefined\( z\.tod_necro_binder \) \) continue;/.test(h) && h.includes('!isdefined( helper.tod_necro_target.tod_necro_binder )'), 'helper_target (hounds, the Mangler) never picks or keeps a bound zombie');
  ok(/isdefined\( z\.tod_necro_binder \)/.test(body('bind_pick')), 'bind_pick still refuses a zombie already being bound');
  const ptn = fs.readFileSync(root + '/scripts/zm/zm_tod2_cybercity/_tod_partners.gsc', 'utf8');
  for (const fn of ['target_for', 'arc_chain', 'raps_touch'])
    ok(body(fn, ptn).includes('if ( isdefined( z.tod_necro_binder ) ) continue;'), 'the companions\' ' + fn + ' skips a bound zombie');
  ok(body('attack', ptn).includes('if ( isdefined( target.tod_necro_binder ) ) continue;'), 'the R.A.P.S. blast spares a bound zombie');
}
// 6. the stock contract the shield relies on (read from the private tools root when it is on this machine)
{
  const RAW = 'C:/BO3Tools/TOD2Cybercity/share/raw/scripts/';
  if (fs.existsSync(RAW + 'zm/_zm_behavior.gsc')) {
    const beh = fs.readFileSync(RAW + 'zm/_zm_behavior.gsc', 'utf8'), utl = fs.readFileSync(RAW + 'zm/_zm_utility.gsc', 'utf8'), zb = fs.readFileSync(RAW + 'shared/ai/zombie.gsc', 'utf8');
    const fze = beh.slice(beh.indexOf('function findZombieEnemy()'), beh.indexOf('function zombieBlackHoleBombPullStart'));
    ok(/!zm_utility::is_magic_bullet_shield_enabled\( zombie \)/.test(fze), 'stock findZombieEnemy (a thrall\'s prey) skips a zombie with the shield');
    ok(/function is_magic_bullet_shield_enabled\( ent \)[^]*?return !IS_TRUE\( ent\.allowDeath \);/.test(utl), 'stock is_magic_bullet_shield_enabled = !allowDeath');
    ok(/entity\.enemy\.archetype == ARCHETYPE_ZOMBIE && IS_TRUE\( entity\.enemy\.allowDeath \)\)[^]*?entity\.enemy Kill\(\);/.test(zb), 'stock turned-zombie swing Kill()s only an enemy whose allowDeath is true');
  }
}
console.log(`NECRO BIND GUARD PASS: ${checks} checks - the shield (snapshot, every exit hands it back), soul_kill spares a bound zombie (negative control: the 15:10 one marked it), helpers and companions skip it, the stock contract.`);
