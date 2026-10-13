// Execute the actual GSC host lifetime with a mocked server-frame scheduler.
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const source = fs.readFileSync(require('path').join(__dirname, '../scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc'), 'utf8');
const fn = source.split('function fx_burst(')[1].split('\nfunction ')[0];
const body = fn.slice(fn.indexOf('{'))
    .replace(/WAIT_SERVER_FRAME;/g, 'yield "frame";')
    .replace(/wait secs;/g, 'yield secs;')
    .replace(/\bh (SetModel|Delete)\(/g, 'h.$1(');
function scenario(options = {}) {
    const env = {level: {_effect: {base: 'electricity', overlay: 'rings'}}, logs: [], effects: [], hosts: [],
        GetTime: () => 1234, isdefined: x => x !== undefined && !x?.deleted,
        fx_dev_log: (...row) => env.logs.push(row),
        PlayFxOnTag: (fx, host) => env.effects.push({fx, host}),
        Spawn: () => {
            if (options.failSpawn) return undefined;
            const h = {SetModel(m) {this.model = m;}, Delete() {this.deleted = true;}};
            env.hosts.push(h); return h;
        }};
    if (options.missingBase) delete env.level._effect.base;
    if (options.missingOverlay) delete env.level._effect.overlay;
    vm.createContext(env);
    vm.runInContext(`function* run(key, origin, secs, overlay_key) {let h, op;${body}}`, env);
    const run = env.run('base', [0, 0, 4], 2, options.noOverlay ? undefined : 'overlay');
    return {env, run};
}
for (const options of [{}, {noOverlay: true}, {missingOverlay: true}]) {
    const {env, run} = scenario(options);
    assert.equal(run.next().value, 'frame'); assert.equal(run.next().value, 'frame');
    assert.equal(env.effects.length, 0, 'replicate host before emitting');
    assert.equal(run.next().value, 2);
    assert.equal(env.hosts.length, 1, 'layers share one host');
    assert.equal(env.effects.length, options.noOverlay || options.missingOverlay ? 1 : 2);
    assert(env.effects.every(f => f.host === env.hosts[0]));
    assert.equal(run.next().done, true); assert(env.hosts[0].deleted);
    assert(env.logs.some(r => r[1] === 'finished' && r[3] === 1234));
}
for (const options of [{failSpawn: true}, {missingBase: true}]) {
    const {env, run} = scenario(options); assert(run.next().done); assert.equal(env.effects.length, 0);
    assert.equal(env.hosts.length, 0); assert(env.logs.length);
}
const {env, run} = scenario(); run.next(); env.hosts[0].Delete(); run.next();
assert(run.next().done); assert.equal(env.effects.length, 0);
assert(env.logs.some(r => r[1] === 'host_lost'));
console.log('Teleporter FX: replication delay, shared host, timed cleanup and missing/deleted-host paths pass.');
