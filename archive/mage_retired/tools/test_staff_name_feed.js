// Exercise the actual server heartbeat and tier reader; emit its packets for Lua.
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const classes = fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_classes.gsc', 'utf8');
const gauge = fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_gauge.gsc', 'utf8');
function body(source, name) {
  const at = source.indexOf('function ' + name + '(');
  assert(at >= 0, name);
  const start = source.indexOf('{', at); let end = start + 1, depth = 1;
  while (depth) { if (source[end] === '{') depth++; if (source[end] === '}') depth--; end++; }
  return source.slice(start + 1, end - 1);
}
const stems = ['tod_staff_lightning', 'tod_staff_fire', 'tod_staff_ice'];
const packets = [];
const ctx = {isdefined: x => x !== undefined, IsSubStr: (s,k) => s.includes(k), IS_TRUE: x => x === true,
  TOD_PAP_TIER_MAX: +classes.match(/#define TOD_PAP_TIER_MAX\s+(\d+)/)[1], level: {weaponNone: 'none'},
  IsAlive: p => p.alive !== false, GetCurrentWeapon: p => p.weapon,
  pap_independent: (p,w) => p.tod_class === 'mage' && stems.some(s => w.name.startsWith(s)),
  pap_stem: (p,w) => stems.find(s => w.name.startsWith(s)) || w.name,
  is_class_primary: () => false,
  send: (p,t,id) => packets.push([t,id])};
vm.createContext(ctx);
for (const [name, args] of [['pap_staff_id','weapon'],['pap_tier','player, weapon']])
  vm.runInContext('function '+name+'('+args+') {'+body(classes,name)+'}',ctx);
const start = gauge.indexOf('\t\t\tpt = 0;');
assert(start >= 0);
const update = gauge.slice(start, gauge.indexOf('// THE FINALE OWNS THE BAR', start))
  .replace('p GetCurrentWeapon()', 'GetCurrentWeapon(p)').replaceAll('tod_classes::','')
  .replace('p LuiNotifyEvent( &"tod_pap_tier", 2, pt, staff_id );', 'send(p,pt,staff_id);');
vm.runInContext('function update(p) {'+update+'}',ctx);
const p = {tod_class:'mage', tod_pap_tier:{}};
for (let tier=0; tier<=3; tier++) for (let id=1; id<=3; id++) for (let q=0; q<=1; q++) {
  p.weapon = {name: stems[id-1]+'_q'+q}; p.tod_pap_tier[stems[id-1]] = tier;
  p.tod_pap_tier_shown = undefined; // same per-life re-arm used by player_lui_life
  const count = packets.length; ctx.update(p);
  assert.deepEqual(packets.at(-1), [tier,id]); assert.equal(packets.length,count+1);
  ctx.update(p); assert.equal(packets.length,count+1, 'unchanged state must not spam');
}
// Same-tier switches must change the displayed staff; previous all-owned mask did not.
for (let id=1; id<=3; id++) {
  p.weapon = {name:stems[id-1]+'_q0'}; p.tod_pap_tier[stems[id-1]]=3;
  const count=packets.length; ctx.update(p); assert.equal(packets.length,count+1);
  assert.deepEqual(packets.at(-1),[3,id]);
}
p.weapon={name:'pistol_standard'}; ctx.update(p); assert.deepEqual(packets.at(-1),[0,0]);
p.weapon=undefined; p.tod_pap_tier_shown=undefined; ctx.update(p); assert.deepEqual(packets.at(-1),[0,0]);
p.weapon={name:stems[0]+'_q1'}; p.alive=false; p.tod_pap_tier_shown=undefined;
ctx.update(p); assert.deepEqual(packets.at(-1),[0,0]);
fs.mkdirSync('tmp',{recursive:true});
fs.writeFileSync('tmp/staff_name_packets.lua', 'return {'+packets.map(p=>'{'+p.join(',')+'}').join(',')+'}\n');
console.log('Staff name feed passed: all six assets, base/PaP I-III, same-tier switches, life replay, nonstaff and death. '+packets.length+' real packets for Lua.');
