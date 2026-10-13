// Exercise the shipping GSC predicate and the stock filter's removal order.
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const code = read('scripts/zm/zm_tod2_cybercity/_tod_cyber_zombies.gsc');
const body = code.match(/function ignore_spawner\( spawner \)\s*\{([\s\S]*?)\n\}/)[1];
const execute = new Function('spawner', 'level', 'isdefined', 'IS_TRUE', body);
const ignored = (spawner, dev) => execute(spawner, {tod_dev: dev}, x => x !== undefined, x => x !== undefined && !!x);
const stock = {script_string: 'tod_cyber_stock'};
const cyber = {script_string: 'tod_cyber_dev'};
for (const dev of [undefined, false, true]) {
  for (const order of [[stock, cyber], [cyber, stock]]) {
    const selected = [...order];
    // Stock _zm_spawner::init removes entries in a forward loop.
    for (let i = 0; i < selected.length; i++) {
      if (ignored(selected[i], dev)) selected.splice(i, 1);
    }
    assert.deepEqual(selected, [cyber]);
  }
  assert.equal(ignored({}, dev), false);
  assert.equal(ignored({script_string: 'unrelated_factory'}, dev), false);
}
const entry = read('scripts/zm/zm_tod2_cybercity.gsc');
const resolve = entry.indexOf('\ttod_resolve_dev_flags();');
const install = entry.indexOf('\ttod_cyber_zombies::install_spawn_filter();');
const bootstrap = entry.indexOf('\tzm_usermap::main();');
assert(resolve >= 0 && resolve < install && install < bootstrap);
assert.match(code, /level\.ignore_spawner_func = &ignore_spawner;/);
const map = read('map_source/zm/zm_tod2_cybercity.map');
const factories = map.split(/^\/\/ entity \d+.*$/m).filter(block => /"classname" "actor_(?:spawner_zm_factory_zombie|archetype_tod_charcoal_zombie)"/.test(block));
assert.equal(factories.length, 2);
for (const [name, marker] of [['spawner_zm_factory_zombie', 'tod_cyber_stock'], ['archetype_tod_charcoal_zombie', 'tod_cyber_dev']]) {
  const factory = factories.find(x => x.includes('actor_' + name + '"'));
  assert(factory.includes('"script_string" "' + marker + '"'));
  assert(factory.includes('"script_noteworthy" "zombie_spawner"'));
  assert(factory.includes('"origin" "470 470 208"'));
}
// Negative control: restore the old restriction; ordinary matches must fail.
const broken = new Function('spawner', 'level', 'isdefined', 'IS_TRUE', body.replace('return false; // Historical', 'return !IS_TRUE( level.tod_dev ); // Historical'));
assert.equal(broken(cyber, {tod_dev: false}, x => x !== undefined, x => !!x), true);
assert.equal(ignored(cyber, false), false);
// Appearance is universal, but diagnostic callbacks still cost nothing outside dev.
assert.match(code, /function init\(\)\s*\{\s*if \( !IS_TRUE\( level.tod_dev \) \)\s*return;/);
assert(!code.includes('restore_sprinter_head'));
// W2E (2026-10-05): THE ARMORED SPRINTER retired whole - its promotion module, the reference-three head kit it put on
// a promoted zombie, its body + heads (zone and roster GDT) - so nothing may still dress a zombie as one.
assert(!require('fs').existsSync(require('path').join(__dirname, '..', 'scripts/zm/zm_tod2_cybercity/_tod_sprinter.gsc')), 'the sprinter module stays retired');
for (const gone of ['function armored_head_for(', 'function apply_sprinter_equipment(', 'function log_sprinter_promotion(', 'tod_cyber_sprinter_head'])
  assert(!code.includes(gone), '_tod_cyber_zombies no longer carries ' + gone);
assert(!/^xmodel,tod_cyber_sprinter/m.test(read('zone_source/zm_tod2_cybercity.zone')), 'no sprinter model is zoned');
console.log('Charcoal spawn selection PASS: every mode uses charcoal; exactly one factory in either order; bootstrap timing, generated map and dev-only diagnostics verified.');
