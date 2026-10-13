// Run the actual CSC event dispatcher against simulated client clocks.
// Covers duplicate updates, pauses, frame jitter, loop wrap, and late joins.
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '../..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const client = read('scripts/zm/zm_tod2_cybercity/_tod_shop.csc');
const timing = read('scripts/zm/zm_tod2_cybercity/_tod_shop_timing.csc');
function body(source, name) {
    const s = source.split('function ' + name + '(')[1].split('\nfunction ')[0];
    return s.slice(s.indexOf('{'));
}
const generatedEvents = body(timing, 'events').replace(/= \( ([^)]+) \);/g, '= [$1];');
const animate = body(client, 'animate');
const dispatcher = animate.slice(animate.indexOf('if ( kind == 1 && tick'), animate.indexOf('last_tick = tick;'))
    .replaceAll('events.size', 'events.length')
    .replace('self PlaySound(', 'self.PlaySound(')
    .replaceAll('tod_shop_timing::', 'tod_shop_timing.');
const program = new vm.Script(dispatcher + '\nlast_tick = tick;');

function run(times, kind = 1, localClientNum = 0) {
    const calls = [], ctx = {
        kind, localClientNum, debug: false, reported: 0,
        SpawnStruct: () => ({}),
        local_to_world: (origin, yaw, p) => [...p],
        AnglesToForward: () => [1, 0, 0], AnglesToUp: () => [0, 0, 1],
        log: () => {}, tod_shop_timing: {},
        self: {origin: [0, 0, 0], angles: [0, 0, 0], shop_bursts: [[], []]}
    };
    const record = (type, clientNum, name, org) => {
        assert.equal(clientNum, localClientNum);
        calls.push({type, ms: ctx.ms, frame: ctx.f, name, org: [...org]});
        return calls.length;
    };
    ctx.PlayFX = (...args) => record('fx', ...args);
    ctx.self.PlaySound = (...args) => record('sound', ...args);
    vm.createContext(ctx);
    vm.runInContext('function events(){let a;' + generatedEvents + '}\n' +
        'function power_bus(frame){let v;' + body(timing, 'power_bus') + '}', ctx);
    ctx.tod_shop_timing.power_bus = ctx.power_bus;
    ctx.events = ctx.events();
    ctx.last_tick = Math.trunc(times[0] * .03);
    for (const ms of times) {
        ctx.ms = ms; ctx.tick = Math.trunc(ms * .03);
        program.runInContext(ctx);
    }
    // Every crackle must share its callback, authored frame and position with
    // a spark. A simultaneous multi-site cluster must emit exactly one crackle.
    for (let i = 0; i < calls.length; i++) {
        const c = calls[i];
        if (c.type !== 'sound') continue;
        const fx = calls[i - 1];
        assert.equal(fx.type, 'fx');
        assert.equal(c.ms, fx.ms); assert.equal(c.frame, fx.frame);
        assert.deepEqual(c.org, fx.org);
        assert.equal(calls.filter(x => x.type === 'sound' && x.ms === c.ms && x.frame === c.frame).length, 1);
        assert.equal(ctx.power_bus(c.frame), 0);
    }
    return calls;
}
const audio = calls => calls.filter(c => c.type === 'sound');
for (const step of [10, 16, 33, 50]) {
    const times = Array.from({length: Math.ceil(12000 / step) + 1}, (_, i) => i * step);
    const calls = run(times);
    assert.equal(calls.filter(c => c.type === 'fx').length, 20);
    assert.deepEqual(audio(calls).map(c => c.frame), [31, 91, 151, 31, 91, 151]);
    audio(calls).forEach((c, i) => {
        const due = 1000 + i * 2000;
        assert(c.ms >= due && c.ms - due < step, 'sound must fire on the first update crossing its animation frame');
    });
    assert.equal(run(times, 5).length, 0, 'independent mask must not own spark audio');
}
// Variable frame time crosses events without dropping or doubling them.
const jitter = [0], steps = [16, 17, 90, 1, 34, 16, 70];
for (let i = 0; jitter.at(-1) < 12000; i++) jitter.push(jitter.at(-1) + steps[i % steps.length]);
assert.equal(audio(run(jitter)).length, 6);
assert.deepEqual(audio(run([990, 1000, 1000, 1000, 1001])).map(c => c.frame), [31]);
assert.deepEqual(audio(run([4990, 5000, 5990, 6000, 6990, 7000])).map(c => c.frame), [151, 31]);
assert.equal(run([5000]).length, 0, 'late join must not replay an old spark');
assert.deepEqual(audio(run([5000, 5990, 6000, 6990, 7000])).map(c => c.frame), [31]);
assert.equal(run([0, 5000]).length, 0, 'large time jump must not replay missed audio');
assert.equal(run([5000, 1000]).length, 0, 'backwards time jump must not replay audio');
assert.equal(audio(run([990, 1000], 1, 1)).length, 1, 'second local client receives its own event');
console.log('SHOP CLIENT SYNC PASS: sound/FX callback pairing, no stacked crackles, frame jitter, pauses, loop wrap, late join and time jumps.');
