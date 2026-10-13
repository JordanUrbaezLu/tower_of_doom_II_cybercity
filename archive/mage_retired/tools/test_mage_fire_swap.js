// Exercise the actual fire-only cooldown controller; native input/animation
// behavior still needs BO3. No Take/Give or forced weapon swap is involved.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '../scripts/zm/zm_tod2_cybercity/_tod_mage_elements.gsc'), 'utf8');
function body(name) {
    const start = src.indexOf('{', src.indexOf('function ' + name + '('));
    let end = start + 1, depth = 1;
    while (depth) { if (src[end] === '{') depth++; if (src[end] === '}') depth--; end++; }
    return src.slice(start + 1, end - 1)
        .replace(/self laststand::player_is_in_laststand\(\)/g, 'isDown()')
        .replace(/self\s+(\w+)\s*\(/g, '$1(');
}
const env = { IS_TRUE: v => v === true, isdefined: v => v !== undefined,
    IsAlive: p => p.alive, isDown: () => env.down,
    GetTime: () => env.time, GetCurrentWeapon: () => env.weapon,
    staff_element: w => w && w.element,
    DisableWeaponFire: () => {env.disabled++; env.nativeBlocked = true;},
    EnableWeaponFire: () => {env.enabled++; env.nativeBlocked = false;},
};
vm.createContext(env);
vm.runInContext(`function update() { let element, blocked; ${body('fire_recovery_update')} }`, env);
const cooldown = Number(src.match(/#define\s+TOD_MAGE_FIRE_RECOVERY_MS\s+(\d+)/)[1]);
assert.equal(cooldown, 1573);
function begin() {
    Object.assign(env, {self: {tod_mage_armed:true, alive:true, tod_mage_fire_ready_ms:1573},
        weapon:{element:'fire'}, time:0, down:false, disabled:0, enabled:0, nativeBlocked:false});
    env.update(); assert.equal(env.nativeBlocked, true);
}
begin(); env.time=1572; env.update(); assert.equal(env.nativeBlocked,true);
env.time=1573; env.update(); assert.equal(env.nativeBlocked,false);
env.update(); assert.equal(env.disabled,1); assert.equal(env.enabled,1);
for(const destination of ['lightning','ice',undefined]) {
    begin(); env.time=200; env.weapon={element:destination}; env.update();
    assert.equal(env.nativeBlocked,false,'other weapons can fire');
    env.time=800; env.weapon={element:'fire'}; env.update();
    assert.equal(env.nativeBlocked,true,'swap back does not reset cooldown');
    env.time=1600; env.update(); assert.equal(env.nativeBlocked,false);
}
for(const state of ['dead','down','disarmed']) {
    begin();
    if(state==='dead') env.self.alive=false;
    if(state==='down') env.down=true;
    if(state==='disarmed') env.self.tod_mage_armed=false;
    env.update(); assert.equal(env.nativeBlocked,false,state+' releases our firing flag');
}
begin(); env.self.tod_menu_frozen=true; env.time=1700; env.update();
assert.equal(env.self.tod_menu_frozen,true,'menu ownership untouched');
assert.equal(env.nativeBlocked,false);
begin(); env.self.tod_mage_fire_ready_ms=undefined; env.update();
assert.equal(env.nativeBlocked,false,'undefined deadline releases stale flag');
// v18.99c: ICE IS OFF THIS CONTROLLER. v18.94 put it here to free the weapon
// switch and the staff then fired as fast as the trigger could be clicked —
// fire is `Charge Shot` (the engine fires on release, so the flag is read on
// the next press), ice is `Single Shot` and the flag did not hold it. Ice's
// cadence is its native fireTime again (0.8 s since v18.99d); this controller
// is fire's alone.
assert(!/TOD_MAGE_ICE_RECOVERY_MS/.test(src), 'ice must not ride the script fire cooldown again');
assert(!/tod_mage_ice_ready_ms/.test(src), 'no ice deadline left behind');
begin(); env.self.tod_mage_fire_ready_ms=1573; env.weapon={element:'ice'}; env.update();
assert.equal(env.nativeBlocked,false,'ice is never blocked by this controller, even mid-fire-cooldown');
env.weapon={element:'lightning'}; env.update(); assert.equal(env.nativeBlocked,false,'lightning never blocked');
const controller = src.slice(src.indexOf('function fire_recovery_watch('),src.indexOf('// Time the trigger hold'));
assert(!/\b(DisableWeapons|EnableWeapons|SwitchToWeaponImmediate|TakeWeapon|GiveWeapon|FreezeControls)\(/.test(controller));
assert(!/endon\( "(death|tod_mage_disarm)" \)/.test(controller),'cleanup must survive death/disarm');
assert(controller.includes('GetTime() + TOD_MAGE_FIRE_RECOVERY_MS'));
console.log('Fire cooldown passed: 1.573s cadence, ice and lightning never gated by it, swap-back deadline, death/disarm cleanup, menu ownership. Ice cadence is native fireTime 0.8. Native playtest required.');
