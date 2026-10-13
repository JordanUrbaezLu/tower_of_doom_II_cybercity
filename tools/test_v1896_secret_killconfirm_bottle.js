// test_v1896_secret_killconfirm_bottle.js — v18.96's three script lanes, read
// from the ACTUAL sources: the teddy-bear song hunt (_tod_secret + the music
// channel's EE gate), the elite kill confirm (_tod_killconfirm + its two hooks
// in _tod_luck) and the elite perk-bottle roll (_tod_bosses + every caller).
// Structural: these are wiring facts a build cannot check (the linker is happy
// with a hook that nobody calls).
//   node tools/test_v1896_secret_killconfirm_bottle.js
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const root = path.join(__dirname, '..');
const read = f => fs.readFileSync(path.join(root, f), 'utf8').replace(/\r\n/g, '\n');
const G = f => read('scripts/zm/zm_tod2_cybercity/' + f);
const secret = G('_tod_secret.gsc'), kc = G('_tod_killconfirm.gsc'), luck = G('_tod_luck.gsc'),
      bosses = G('_tod_bosses.gsc'), atmos = G('_tod_atmosphere.gsc'), main = G('_tod_main.gsc'),
      mangler = G('_tod_mangler.gsc'), doppel = G('_tod_doppelghast.gsc'), dealer = G('_tod_dealer_finale.gsc');
const zone = read('zone_source/zm_tod2_cybercity.zone'), csv = read('sound/aliases/tod_ui.csv');
const num = (src, k) => Number((src.match(new RegExp('#define\\s+' + k + '\\s+([-\\d.]+)')) || [])[1]);
const str = (src, k) => (src.match(new RegExp('#define\\s+' + k + '\\s+"([^"]+)"')) || [])[1];

// ---- THE SECRET -------------------------------------------------------------
assert.equal(num(secret, 'TOD_SECRET_COUNT'), 3, 'three bears');
assert.equal((secret.match(/spots\[ \d \] = spot\(/g) || []).length, 3, 'three placed spots');
// docs/208: the fan's Cyber Teddy (map 1's v19.64) replaced the stock p7_zm_teddybear; the
// size chain + the file hashes are tools/cyber_teddy/verify.py's, the numbers its manifest's.
const teddyMan = JSON.parse(read('art/cyber_teddy/manifest.json'));
assert.equal(str(secret, 'TOD_SECRET_MODEL'), 'tod_cyber_teddy');
assert.ok(secret.includes('#precache( "model", "tod_cyber_teddy" );'), 'model precached');
assert.ok(zone.includes('\nxmodel,tod_cyber_teddy\n'), 'model zoned');
assert.ok(!/^xmodel,p7_zm_teddybear\s*$/m.test(zone) && !/p7_zm_teddybear" \);|"p7_zm_teddybear"\s*$/m.test(secret), 'the stock bear is retired whole (no zone line, no precache, no define)');
assert.equal(str(secret, 'TOD_SECRET_REVISION'), teddyMan.revision, 'the INIT log names the built revision');
assert.equal(num(secret, 'TOD_SECRET_HALF_DEPTH'), teddyMan.half_depth, 'HALF_DEPTH = its back extent (manifest)');
assert.ok(secret.includes('self thread melee_watch( note );') && secret.includes('function melee_hits_bear()'), 'a blade swing counts (the melee lane)');
assert.ok(zone.includes('scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_secret.gsc') && zone.includes('scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_killconfirm.gsc'), 'both modules zoned');
assert.ok(secret.includes('self SetCanDamage( true );') && secret.includes('self waittill( "damage", amount, attacker, dir, point, mod );'), 'shoot detection');
assert.ok(secret.includes('if ( !isdefined( attacker ) || !isplayer( attacker ) )'), 'only a player counts');
assert.equal(str(secret, 'TOD_SECRET_LAUGH'), 'tod_secret_laugh', 'OUR laugh alias (the stock one is in a CSV this map never loads)');
assert.ok(csv.split('\n').some(l => l.startsWith('tod_secret_laugh,') && l.includes('tod\\sfx\\tod_secret_laugh.wav') && l.includes('3d')), 'laugh alias row, 3D');
assert.ok(fs.existsSync(path.join(root, 'sound_assets/tod/sfx/tod_secret_laugh.wav')), 'laugh wav present');
// v18.96b: centre pivot -> every spot lifted; view-ray detection on every shot; the 3 s gap before the song
assert.equal(num(secret, 'TOD_SECRET_LIFT'), teddyMan.lift, 'the pivot lift = the mesh min z (manifest)');
// 2026-10-02 THE HAVENS (docs/202): the floor-10 and floor-20 bears ride GENERATED anchors
// (tools/haven_layout.js BEARS -> _tod_breather_data.gsc secret_bear_org), and the lift is in them
assert.equal((secret.match(/\+ TOD_SECRET_LIFT \)/g) || []).length, 1, 'the base spot is lifted by the define');
{
  const data = fs.readFileSync(path.join(root, 'scripts/zm/zm_tod2_cybercity/_tod_breather_data.gsc'), 'utf8');
  const bo = data.match(/function secret_bear_org\( i, z \) \{ if \( i == 1 \) return \( (-?[\d.]+), (-?[\d.]+), z \+ ([\d.]+) \); return \( (-?[\d.]+), (-?[\d.]+), z \+ ([\d.]+) \); \}/);
  assert.ok(bo, 'the generated haven bear anchors');
  const lift = num(secret, 'TOD_SECRET_LIFT');
  assert.ok(Math.abs(+bo[3] - lift) < 1e-6 && Math.abs(+bo[6] - lift) < 1e-6,
    'both haven bears carry the lift (docs/202 v2): floor 10 on the hall floor, floor 20 on the loggia floor');
}
assert.ok(secret.includes('callback::on_spawned( &shot_watch );') && secret.includes('self waittill( "weapon_fired" );') && secret.includes('BulletTracePassed( eye, bear.origin, false, self )'), 'view-ray lane');
assert.ok(secret.includes('if ( IS_TRUE( self.tod_secret_hit ) )\n\t\treturn;\n\tself.tod_secret_hit = true;'), 'both lanes latch once');
assert.equal(num(atmos, 'TOD_MUSIC_EE_GAP'), 3, '3 s of silence');
assert.ok(/channel_stop\(\);\s*level thread ee_song_run\(\);/.test(atmos) && /wait TOD_MUSIC_EE_GAP;\s*channel_play\( "tod_music_ee" \);\s*wait TOD_MUSIC_EE_SECS;/.test(atmos), 'stop, gap, song, length');
assert.ok(secret.includes('tod_perk_scatter::play_sound_at_origin( org, TOD_SECRET_LAUGH, TOD_SECRET_LAUGH_SECS );'), 'laugh at the bear');
assert.ok(secret.includes('tod_atmosphere::ee_song_start( TOD_SECRET_RISE_SECS + TOD_SECRET_FLY_SECS )'), 'the third bear arms the song with the flight as its lead');
// v18.96c: the rise-and-flight is paced inside the laugh, and the lead runs before the gap
assert.ok(num(secret, 'TOD_SECRET_RISE_SECS') + num(secret, 'TOD_SECRET_FLY_SECS') <= num(secret, 'TOD_SECRET_LAUGH_SECS'), 'flight fits inside the laugh emitter life');
assert.ok(secret.includes('function bear_fly_away( bear, last )') && secret.includes('bear MoveTo( dest, TOD_SECRET_FLY_SECS') && secret.includes('bear RotateYaw( TOD_SECRET_SPIN_DEG, TOD_SECRET_RISE_SECS + TOD_SECRET_FLY_SECS, TOD_SECRET_RISE_SECS + TOD_SECRET_FLY_SECS, 0 );'), 'one accelerating spin over the whole exit');
assert.ok(secret.includes('spot( ( 1620 - TOD_SECRET_HALF_DEPTH, -520, 0 + TOD_SECRET_LIFT ), ( 0, 270, 0 )'), 'base bear: back to the east wall, facing west');
assert.ok(secret.includes('spots[ 1 ] = spot( tod_breather_data::secret_bear_org( 1, zs[ 0 ] ), ( 0, tod_breather_data::secret_bear_yaw( 1 ), 0 )'), 'floor-10 bear: the generated haven hall anchor (docs/202)');
assert.ok(secret.includes('spots[ 2 ] = spot( tod_breather_data::secret_bear_org( 2, zs[ 1 ] ), ( 0, tod_breather_data::secret_bear_yaw( 2 ), 0 )'), 'floor-20 bear: the generated haven loggia anchor (docs/202)');
assert.ok(/wait level\.tod_music_ee_lead;\s*wait TOD_MUSIC_EE_GAP;/.test(atmos), 'lead then gap');
{ const lw = path.join(root, 'sound_assets/tod/sfx/tod_secret_laugh.wav'); const lh = fs.readFileSync(lw).subarray(0, 44); const lsecs = (fs.statSync(lw).size - 44) / (48000 * 2 * 2); assert.ok(lh.readUInt32LE(24) === 48000 && lsecs > 8 && lsecs < 9, 'the Samantha laugh wav (8.30 s, cut before the bye-bye) is the one banked'); }
assert.ok(!/IPrintLnBold|SetHintString|iprintln/i.test(secret), 'no on-screen text, no triggerstrings');
assert.ok(main.includes('tod_secret::init();') && main.includes('tod_killconfirm::init();'), 'both inits threaded from _tod_main');
// the song: alias row + wav on the bank contract + the measured length in the define
const row = csv.split('\n').find(l => l.startsWith('tod_music_ee,'));
assert.ok(row, 'tod_music_ee alias row');
assert.ok(row.includes('tod\\music\\tod_music_ee.wav') && row.includes('STREAMED') && row.includes('LOOPING') && row.includes('2d'), 'row shape = the band rows');
const wavPath = path.join(root, 'sound_assets/tod/music/tod_music_ee.wav');
assert.ok(fs.existsSync(wavPath), 'the song wav exists');
const hdr = fs.readFileSync(wavPath).subarray(0, 44);
assert.equal(hdr.readUInt32LE(24), 48000, 'wav 48 kHz');
assert.equal(hdr.readUInt16LE(22), 2, 'wav stereo');
assert.equal(hdr.readUInt16LE(34), 16, 'wav 16-bit');
const secs = num(atmos, 'TOD_MUSIC_EE_SECS');
const dataBytes = fs.statSync(wavPath).size - 44, wavSecs = dataBytes / (48000 * 2 * 2);
assert.ok(Math.abs(wavSecs - secs) < 1.0, `TOD_MUSIC_EE_SECS ${secs} vs wav ${wavSecs.toFixed(2)} s`);
// NO MUSIC CAN OVERTAKE IT: the gate is in channel_play itself, and the resume replays the parked request.
assert.ok(/function channel_play\( alias \)\s*\{\s*if \( IS_TRUE\( level\.tod_music_ee \) && isdefined\( alias \) && alias != "tod_music_ee" \)\s*\{\s*level\.tod_music_ee_pending = alias;[^\n]*\n\s*return;/.test(atmos), 'channel_play parks every other request while the song holds');
assert.ok(atmos.includes('next = level.tod_music_ee_pending;'), 'the parked request resumes');
assert.ok(atmos.includes('level.tod_music_ee_played = true;'), 'once per match');
// W2E (2026-10-05): the Panzer's music refcount (boss_track_start/end + boss_music_blocked) retired with him; the arena's
// boss track is parked under the song by channel_play's own gate (asserted above).
assert.ok(atmos.includes('IS_TRUE( level.tod_music_ee )') && !/function boss_track_start\(/.test(atmos), 'the Panzer refcount stays retired; the song still holds the channel');

// ---- THE KILL CONFIRM ---------------------------------------------------------
// (the partner-owner redirect may sit between the brace and the player guard since the partner feature)
assert.ok(/function boss_kill\( killer, kind \)\s*\{[\s\S]*?if \( !isdefined\( killer \) \|\| !isplayer\( killer \) \)\s*return;[\s\S]*?tod_killconfirm::elite_kill\( killer, kind \);/.test(luck), 'elite_kill hangs on boss_kill');
assert.ok(!luck.includes('PlayLocalSound( "tod_headshot_ding" )'), 'luck no longer plays the ding itself');
assert.ok(luck.includes('tod_killconfirm::ding( attacker );'), 'the headshot ding routes through the one owner');
assert.equal((kc.match(/PlayLocalSound\( TOD_KC_DING \)/g) || []).length, 1, 'one ding site');
assert.ok(kc.includes('player.tod_kc_ding_ms == GetTime()'), 'once per frame');
// 2026-09-26: hit markers on EVERY enemy + a punch on kills (user). The stock element is still the one lane.
assert.ok(kc.includes('e SetShader( "damage_feedback", w, w * 2 );') && kc.includes('color = ( 1, 0.18, 0.18 );') && kc.includes('e FadeOverTime( hold );'), 'the red snap on the stock element');
assert.ok(kc.includes('zm::register_zombie_damage_override_callback( &hit_cb );'), 'hits ride stock\'s damage-override hook (the Aetherium HUD\'s lane)');
assert.ok(kc.includes('function hit_cb( willBeKilled, inflictor, attacker, damage,'), 'the hook signature is stock\'s');
assert.ok(kc.includes('e ScaleOverTime( TOD_KC_PUNCH_SECS, w, w * 2 );') && kc.includes('e MoveOverTime( TOD_KC_PUNCH_SECS );'), 'a kill lands big and snaps down, centred (the punch)');
assert.ok(num(kc, 'TOD_KC_PUNCH_SCALE') > 1 && num(kc, 'TOD_KC_PUNCH_SECS') <= 0.15, 'punch is bigger than its size and fast');
assert.ok(kc.includes('if ( is_elite( self ) )') && kc.includes('return;   // elite_kill() owns it'), 'an elite death is pulsed once, by elite_kill via boss_kill');
assert.ok(kc.includes('self.team == attacker.team || IS_TRUE( self.tod_is_partner )'), 'no marker on helpers or partners');
assert.ok(kc.includes('if ( !isdefined( self ) || !isdefined( attacker ) || !isplayer( attacker ) )'), 'a disconnected owner never crashes the hook');
assert.ok(num(kc, 'TOD_KC_RANK_BOSS') > num(kc, 'TOD_KC_RANK_ELITE') && num(kc, 'TOD_KC_RANK_ELITE') > num(kc, 'TOD_KC_RANK_KILL') && num(kc, 'TOD_KC_RANK_KILL') > num(kc, 'TOD_KC_RANK_HEAD') && num(kc, 'TOD_KC_RANK_HEAD') > num(kc, 'TOD_KC_RANK_HIT'), 'rank ladder hit < head < kill < elite < boss');
assert.ok(kc.includes('e.color = ( 1, 1, 1 );'), 'colour handed back to white');
assert.ok(num(kc, 'TOD_KC_BOSS_W') > num(kc, 'TOD_KC_ELITE_W') && num(kc, 'TOD_KC_BOSS_HOLD') > num(kc, 'TOD_KC_ELITE_HOLD'), 'the boss marker is bigger and longer');
// no per-hit / ordinary-zombie marker anywhere in the map's own scripts
for (const f of fs.readdirSync(path.join(root, 'scripts/zm/zm_tod2_cybercity')).filter(f => f.endsWith('.gsc') && f !== '_tod_killconfirm.gsc'))
  assert.ok(!G(f).includes('hud_damagefeedback'), f + ' must not drive the marker (elites only, one owner)');

// ---- THE PERK BOTTLE ----------------------------------------------------------
assert.equal(num(bosses, 'TOD_ELITE_BOTTLE_PCT'), 10, '10%');
assert.ok(bosses.includes('function grant_elite_reward( name, attacker, org )'), 'org param');
assert.ok(bosses.includes('elite_bottle_roll( name, attacker, org );'), 'roll called from the one payout');
const roll = bosses.slice(bosses.indexOf('function elite_bottle_roll('));
assert.ok(roll.includes('flag::get( "power_on" )'), 'power on (the Endless Spire guard left with the spire, 2026-09-29)');
assert.ok(roll.includes('if ( roll >= TOD_ELITE_BOTTLE_PCT )') && roll.includes('zm_powerups::specific_powerup_drop( "tod_free_pap", org )'), 'the bottle is the map\'s own perk-bottle powerup');
// every elite death site hands its origin over, guarded against the same-frame reap. W2E (2026-10-05): the Map One
// sites (the Rogue Protector in _tod_bosses, _tod_hellhounds, _tod_reaver, _tod_sprinter) retired whole; the live
// elites are the sites now.
for (const [name, src, call, guard] of [['mangler', mangler, 'tod_bosses::grant_elite_reward( "MANGLER", attacker, org )', /if \( isdefined\( self \) \)\s*org = self\.origin;/],
                                        ['doppelghast', doppel, 'tod_bosses::grant_elite_reward( "DOPPELGHAST", attacker, org )', /if \( isdefined\( self \) \)\s*org = self\.origin;/],
                                        ['dealer', dealer, 'tod_bosses::grant_elite_reward( "DEALER", attacker, org )', /org = \( isdefined\( self \) \? self\.origin : undefined \);/]]) {
  assert.ok(src.includes(call), name + ' passes org');
  assert.ok(guard.test(src), name + ' guards the corpse read');
}
assert.equal((bosses.match(/grant_elite_reward\( "[A-Z ]+", \w+ \);/g) || []).length, 0, 'no two-arg elite reward call left in _tod_bosses');
assert.equal(((mangler + doppel + dealer).match(/grant_elite_reward\( "[A-Z ]+", attacker \);/g) || []).length, 0, 'no two-arg call left in the elite modules');

console.log('v18.96: 3 bears (shoot-detect, laugh 3D, once-per-match song that NOTHING overtakes; wav 48k/16/stereo, ' + wavSecs.toFixed(1) + 's), elite kill confirm (red snap + one ding owner, elites only), 10% perk bottle from every elite death site (tower, power on). PASS');
