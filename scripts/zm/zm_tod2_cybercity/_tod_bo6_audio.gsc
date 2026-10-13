// Original BO6 enemy audio. Source notes drive timing, BO3 aliases drive layers.
#using scripts\shared\ai\systems\animation_state_machine_notetracks;
#insert scripts\shared\shared.gsh;
#namespace tod_bo6_audio;
#insert scripts\zm\zm_tod2_cybercity\_tod_bo6_audio_events.gsh;

// THE DOPPELGHAST'S APPROACH SCREECH (user 2026-09-20: "sfx we can make louder
// to make it obvious and anxiety building. The running sounds and screeching").
// The source clips only scream on their own notetracks, so a Doppelghast far
// from its target could close half a room in silence. While it is hunting —
// alive, not attacking, not juking, farther than TOD_DOPPEL_SCREECH_FAR from
// its target — it lets out one of its roars every 2.5-4.5 s through the same
// emit() lane (25 ms duplicate guard, per-actor counts, dev log). The alias is
// the pack's own vox_ai_ghoul_roar (3 variants), which nothing else fires, so
// it never doubles a notetrack scream. Set TOD_DOPPEL_SCREECH_MIN_S to 0 to
// turn the cadence off; the loudness itself lives in the alias CSV
// (tools/bo6_extraction/import_enemy_audio.py GHOUL_MIX).
#define TOD_DOPPEL_SCREECH_ALIAS  "vox_ai_ghoul_roar"
#define TOD_DOPPEL_SCREECH_MIN_S  2.5
#define TOD_DOPPEL_SCREECH_MAX_S  4.5
#define TOD_DOPPEL_SCREECH_FAR    320

// THE TIMED LANE (PK02, 2026-10-04). Every BO6 one-shot hung on an
// 'AudioOneShot@<alias>' clip note was SILENT: neither the ASM handlers nor the
// note_notify map in _tod_bo6_audio_events.gsh ever receive those mixed-case
// '@' names. The user's 2026-10-03 run (tmp/elite_tracking/runs/
// 20261003_154548_488_a1bee5db) logged 6 Doppelghast swings, a juke and 6
// cannon windups with ZERO of these events, while the private lowercase step
// notes on the SAME run clip fired every time. The elite modules now call the
// functions below the moment they start a clip, and each cue lands on the
// clip's own frame (the source XANIM_EXPORT notetracks, 30 fps), scaled by the
// rate the clip plays at. IF THE CLIP NOTES ARE EVER RENAMED TO PRIVATE NAMES
// (the steps' recipe), DELETE THE MATCHING CALLS IN THE SAME CHANGE, or every
// cue plays twice.
#define TOD_BO6_FPS                 30.0
#define TOD_DOPPEL_SWING_FOLEY_F    3     // hb_doppelghast_stn_melee_01: fly_ai_ghoul_melee (the hit is frame 18 = attacks()' 0.6 s)
#define TOD_DOPPEL_SWING_VOX_F      13    //   vox_ai_ghoul_attack
#define TOD_DOPPEL_JUKE_FOLEY_F     5     // hb_doppelghast_juke_l/r_short_01: fly_ai_ghoul_juke (its vox is the clip's last frame = the juke's end)
#define TOD_MANGLER_PRESHOT_F       1     // hb_mangler_cannon: fly_ai_mangler_cannon_preshot (the shot is frame 61 = attacks()' windup)
#define TOD_MANGLER_PULLBACK_F      10    //   fly_ai_mangler_cannon_pullback
#define TOD_MANGLER_CHARGE_F        27    //   fly_ai_mangler_cannon_charge (+ its secondary hb_bo6_48270a7a9846530e)
#define TOD_MANGLER_MELEE_MVMT_F    5     // hb_mangler_melee: fly_ai_mangler_mvmt_melee, under the existing hb_mangler_melee swing

// THE GHOUL'S BREATH (PK02). The Doppelghast's run / sprint / idle clips carry
// vox_ai_ghoul_ambience notes (run 3 per cycle = one growl every ~1.1 s at the
// 1.5 walk rate, idle one every ~1.7 s); they were silent with the rest. A
// cadence plays them from the module instead, a touch sparser than the source
// (one growl per growl's length), never over this ghoul's own roar / attack
// scream / juke snarl / pain, never mid-attack or mid-juke, and the whole map
// starts at most one growl every TOD_DOPPEL_AMB_GLOBAL_MS so a pack of hunters
// never walls the mix. Set TOD_DOPPEL_AMB_MOVE_MIN_S to 0 to turn it off.
#define TOD_DOPPEL_AMB_ALIAS        "vox_ai_ghoul_ambience"
#define TOD_DOPPEL_AMB_MOVE_MIN_S   1.2
#define TOD_DOPPEL_AMB_MOVE_MAX_S   2.2
#define TOD_DOPPEL_AMB_IDLE_MIN_S   1.8
#define TOD_DOPPEL_AMB_IDLE_MAX_S   3.0
#define TOD_DOPPEL_AMB_MOVED_SQ     576   // 24 units since the last growl = it is moving (the run cadence), else the idle one
#define TOD_DOPPEL_AMB_VOX_GAP_MS   900
#define TOD_DOPPEL_AMB_GLOBAL_MS    350

// THE DEATH TAILS (PK02). PlaySoundAtPosition plays nothing audible for a
// custom alias in this map (v19.21c; the hoop sting, the riot shield break and
// the C4 blast all paid for it), so the death sounds that must outlive the
// corpse ride a script_origin carrier instead (_tod_perk_scatter's proven lane).
#define TOD_BO6_TAIL_SECS           10    // the longest tail: evt_ai_ghoul_death_oneshot is 8.1 s

// THE MANGLER'S VOICE (W2F, 2026-10-05: "the Mangler's VOICE ... spawn, pain, attack, death, idle growls"). It had
// none: watch_damage returned for it ("BO6 AIVox character lookup still open") and nothing else ever voiced it, so
// the elite fought in silence but for its armour. BO6 voices its Mangler through an AIVox character table whose
// takes are in no bank this PC's BO6 extraction dumped; the voice here is the creature BO6's Mangler is built on -
// Black Ops III's Gorod Krovi Mangler (vox_raz_exert_enrage / _melee / _pain, 24 takes) - plus two cues derived from
// those same takes (a slowed dying roar, a helmet-muffled growl). Rows: sound/aliases/tod_mangler_vox.csv, GENERATED
// by tools/original_rips/make_original_rips.py (never hand-edit). The moments are BO6's own: its clips' AIVox notes
// (vox_melee on the swing's frame 5, vox_shoot on frame 58, three frames before the frame-61 shot), the arrival roar,
// the vox_berserk roar the first time it is beaten to half health, pain grunts on a gap, a growl while it hunts.
// Logs ([TOD_BO6_AUDIO], dev / diag): EVENT source=vox_ai_mangler_* (the first two per voice per Mangler),
// MANGLER_BERSERK, and the BANK probe's ms for every new alias. Gate: tools/original_rips/test_original_rips.js.
#define TOD_MANGLER_VOX_MELEE_F     5     // hb_mangler_melee (BO6 ..._attack_mangler_swing_l_to_r): AIVox@vox_melee
#define TOD_MANGLER_VOX_SHOOT_F     58    // hb_mangler_cannon (BO6 ai_t9_zm_raz_attack_mangler_shoot_01): AIVox@vox_shoot
#define TOD_MANGLER_SPAWN_ROAR_F    10    // the arrival roar, 0.33 s after it appears (just behind the spawn foley's onset)
#define TOD_MANGLER_BERSERK_FRAC    0.5   // the first hit to half health draws the enrage roar (BO6 AIVox@vox_berserk)
#define TOD_MANGLER_PAIN_GAP_MIN_MS 1600  // pain grunts: one per 1.6-2.6 s at most, never mid-attack (it is a tank)
#define TOD_MANGLER_PAIN_GAP_MAX_MS 2600
#define TOD_MANGLER_VOX_GAP_MS      700   // no grunt or growl inside 0.7 s of its own last voice
#define TOD_MANGLER_AMB_MIN_S       4.0   // the hunting growl: one every 4-7 s (0 turns the cadence off)
#define TOD_MANGLER_AMB_MAX_S       7.0
#define TOD_MANGLER_AMB_GLOBAL_MS   900   // the whole map starts at most one Mangler growl per 0.9 s

function init()
{
    if ( IS_TRUE( level.tod_bo6_audio_started ) ) return;
    level.tod_bo6_audio_started = true;
    level.tod_bo6_note_alias = [];
    register_source_events();
    level thread bank_probe();
}

// THE BANK PROBE (PK02; dev / diag only, once): every alias PK02 made audible with its length in the LOADED sound
// bank, so the first dev run proves they all resolve before anyone has to trigger them. ms=0 = not in the bank: the
// row did not build (a missing table in the zone config, a context column, a FileSpec the bank could not find).
function bank_probe()
{
    level endon( "end_game" );
    wait 1;
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
    probe = array( "zmb_no_purchase", "cw_mus_perks_packa_sting", "cw_mus_perks_packa_jingle",
                   "hb_bo6_fly_ai_ghoul_melee", "hb_bo6_vox_ai_ghoul_attack", "hb_bo6_fly_ai_ghoul_juke",
                   "hb_bo6_vox_ai_ghoul_juke", "hb_bo6_vox_ai_ghoul_ambience", "hb_bo6_fly_ai_mangler_cannon_preshot",
                   "hb_bo6_fly_ai_mangler_cannon_pullback", "hb_bo6_fly_ai_mangler_cannon_charge",
                   "hb_bo6_fly_ai_mangler_mvmt_melee", "hb_bo6_fly_ai_mangler_mvmt_heavystep_land",
                   "hb_bo6_vox_ai_ghoul_death", "hb_bo6_evt_ai_ghoul_death_oneshot", "hb_bo6_fly_ai_mangler_death_collapse" );
    // W2F: the Mangler's voice and the Death Perception / PhD Flopper machine music (tools/original_rips)
    more = array( "hb_bo6_vox_ai_mangler_roar", "hb_bo6_vox_ai_mangler_melee", "hb_bo6_vox_ai_mangler_shoot",
                  "hb_bo6_vox_ai_mangler_pain", "hb_bo6_vox_ai_mangler_death", "hb_bo6_vox_ai_mangler_ambience",
                  "mus_perk_deathperception_jingle", "mus_perk_deathperception_stinger", "mus_perk_phd_jingle", "mus_perk_phd_stinger" );
    foreach ( a in more )
    {
        probe[ probe.size ] = a;
    }
    missing = 0;
    foreach ( a in probe )
    {
        ms = SoundGetPlaybackTime( a );
        if ( !isdefined( ms ) ) ms = -1;
        if ( ms <= 0 ) missing++;
        dev_log( "BANK alias=" + a + " ms=" + ms );
    }
    dev_log( "BANK_SUMMARY probed=" + probe.size + " missing=" + missing + " (PK02: missing must be 0)" );
}

function dev_log( message )
{
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
    line = "[TOD_BO6_AUDIO] ms=" + GetTime() + " " + message;
    /# PrintLn( line ); #/
}

function emit( actor, source_alias, event )
{
    if ( !isdefined( actor ) || IS_TRUE( level.tod_upgrade_pause ) ) return;
    // The level-owned death burst places this sound at the frame-90 explosion.
    // The imported death clip's frame-198 tail must not fire it a second time.
    if ( source_alias == "evt_ai_ghoul_death_oneshot" && IS_TRUE( actor.tod_bo6_death_burst_started ) ) return;
    if ( !IS_TRUE( actor.tod_mangler ) && !isdefined( actor.tod_bo6_dev_kind ) ) return;
    if ( source_alias == "fly_ai_amalgam_grab_hit" && !IS_TRUE( actor.tod_bo6_grab_contact ) ) return;
    if ( !isdefined( actor.tod_bo6_audio_last ) ) actor.tod_bo6_audio_last = [];
    if ( !isdefined( actor.tod_bo6_audio_counts ) ) actor.tod_bo6_audio_counts = [];
    now = GetTime();
    last = actor.tod_bo6_audio_last[source_alias];
    // Some animation paths report a note through both ASM and note_notify.
    // Suppress only that same-frame duplicate, preserving source cadence.
    if ( isdefined( last ) && now - last < 25 ) return;
    actor.tod_bo6_audio_last[source_alias] = now;
    alias = "hb_bo6_" + source_alias;
    if ( source_alias == "evt_ai_amalgam_death" || source_alias == "vox_ai_ghoul_death" ||
         source_alias == "evt_ai_ghoul_death_oneshot" || source_alias == "fly_ai_mangler_death_collapse" ||
         source_alias == "vox_ai_mangler_death" )
        sound_at( alias, actor.origin, TOD_BO6_TAIL_SECS ); // retain the tail after corpse deletion (a carrier, never PlaySoundAtPosition)
    else actor PlaySound( alias );
    count = actor.tod_bo6_audio_counts[source_alias];
    if ( !isdefined( count ) ) count = 0;
    actor.tod_bo6_audio_counts[source_alias] = count + 1;
    if ( count < 2 ) dev_log( "EVENT entity=" + actor GetEntityNumber() + " source=" + source_alias + " alias=" + alias + " via=" + event + " count=" + ( count + 1 ) );
}

function attach( actor, kind )
{
    init();
    if ( IS_TRUE( actor.tod_bo6_audio_attached ) ) return;
    actor.tod_bo6_audio_attached = true;
    actor thread watch_scripted_notes();
    actor thread watch_damage( kind );
    if ( kind == "mangler" )
    {
        emit( actor, "fly_ai_mangler_spawn", "spawn" );
        actor thread timed( "vox_ai_mangler_roar", TOD_MANGLER_SPAWN_ROAR_F, 1, "spawn_roar" );   // THE MANGLER'S VOICE: its arrival
        if ( TOD_MANGLER_AMB_MIN_S > 0 ) actor thread mangler_ambience_cadence();
    }
    else if ( kind == "amalgam" ) emit( actor, "vox_ai_amalgam_spawn", "spawn" );
    else
    {
        emit( actor, "evt_ai_ghoul_spawn_novox", "spawn" );
        emit( actor, "vox_ai_ghoul_spawn", "spawn_voice" );
        if ( TOD_DOPPEL_SCREECH_MIN_S > 0 ) actor thread approach_screech();
        if ( TOD_DOPPEL_AMB_MOVE_MIN_S > 0 ) actor thread ambience_cadence();
    }
    dev_log( "ATTACH entity=" + actor GetEntityNumber() + " kind=" + kind );
}

// One cue at a source clip frame, counted from the moment the caller started
// the clip at `rate` (self = the actor). A death ends it unplayed; emit()
// refuses it under a world pause like every other lane.
function timed( source_alias, frame, rate, event )
{
    self endon( "death" );
    level endon( "end_game" );
    if ( !isdefined( rate ) || rate <= 0 ) rate = 1;
    delay = frame / ( TOD_BO6_FPS * rate );
    if ( delay > 0 ) wait delay;
    emit( self, source_alias, event );
}

// PUBLIC (_tod_doppelghast::attacks, right after its AnimScripted) — the
// swing's whoosh and the attack scream, on hb_doppelghast_stn_melee_01's frames.
function doppel_swing( actor )
{
    if ( !isdefined( actor ) ) return;
    actor thread timed( "fly_ai_ghoul_melee", TOD_DOPPEL_SWING_FOLEY_F, 1, "swing_timed" );
    actor thread timed( "vox_ai_ghoul_attack", TOD_DOPPEL_SWING_VOX_F, 1, "swing_timed" );
}

// PUBLIC (_tod_doppelghast::play_juke, right after its AnimScripted) — the
// side-dash's push-off whoosh.
function doppel_juke_start( actor )
{
    if ( !isdefined( actor ) ) return;
    actor thread timed( "fly_ai_ghoul_juke", TOD_DOPPEL_JUKE_FOLEY_F, 1, "juke_timed" );
}

// PUBLIC (_tod_doppelghast::play_juke, when the dash ends) — the snarl it lands
// on: the clip's last frame (38 / 39) when it runs out, the moment it breaks
// off for a swing or a lost path otherwise. Never on a world pause's cut.
function doppel_juke_end( actor, reason )
{
    if ( !isdefined( actor ) || ( isdefined( reason ) && reason == "pause" ) ) return;
    emit( actor, "vox_ai_ghoul_juke", "juke_end" );
}

// PUBLIC (_tod_mangler::attacks, right after the cannon's AnimScripted) — the
// windup: the pre-shot click, the arm's pull-back and the charge whine (+ its
// secondary layer), on hb_mangler_cannon's frames at the clip's playback rate.
function mangler_cannon_windup( actor, rate )
{
    if ( !isdefined( actor ) ) return;
    actor thread timed( "fly_ai_mangler_cannon_preshot", TOD_MANGLER_PRESHOT_F, rate, "cannon_timed" );
    actor thread timed( "fly_ai_mangler_cannon_pullback", TOD_MANGLER_PULLBACK_F, rate, "cannon_timed" );
    actor thread timed( "fly_ai_mangler_cannon_charge", TOD_MANGLER_CHARGE_F, rate, "cannon_timed" );
    actor thread timed( "vox_ai_mangler_shoot", TOD_MANGLER_VOX_SHOOT_F, rate, "cannon_timed" );   // THE MANGLER'S VOICE: the bellow as it fires
}

// PUBLIC (_tod_mangler::attacks) — a windup that never fires (a world pause, a
// lost target) cuts its charge whine instead of letting it ring on.
function mangler_cannon_cancel( actor )
{
    if ( !isdefined( actor ) ) return;
    actor StopSound( "hb_bo6_fly_ai_mangler_cannon_charge" );
    actor StopSound( "hb_bo6_48270a7a9846530e" );   // the charge row's Secondary
}

// PUBLIC (_tod_mangler::attacks) — the armour's lunge, under the swing.
function mangler_melee( actor )
{
    if ( !isdefined( actor ) ) return;
    actor thread timed( "fly_ai_mangler_mvmt_melee", TOD_MANGLER_MELEE_MVMT_F, 1, "melee_timed" );
    actor thread timed( "vox_ai_mangler_melee", TOD_MANGLER_VOX_MELEE_F, 1, "melee_timed" );   // THE MANGLER'S VOICE: the swing's grunt
}

// PUBLIC (_tod_mangler::step_watch) — one heavy footfall: the BO6 land and its
// armour-rattle Secondary (hb_bo6_6ecdcdac2e4c9955).
function mangler_step( actor, via )
{
    emit( actor, "fly_ai_mangler_mvmt_heavystep_land", via );
}

// THE GHOUL'S BREATH (self = the Doppelghast; the defines above).
function ambience_cadence()
{
    self endon( "death" );
    level endon( "end_game" );
    last = self.origin;
    moving = true;
    wait RandomFloatRange( 0.4, 1.2 );
    while ( isdefined( self ) && isalive( self ) )
    {
        if ( moving )
            wait RandomFloatRange( TOD_DOPPEL_AMB_MOVE_MIN_S, TOD_DOPPEL_AMB_MOVE_MAX_S );
        else
            wait RandomFloatRange( TOD_DOPPEL_AMB_IDLE_MIN_S, TOD_DOPPEL_AMB_IDLE_MAX_S );
        if ( !isdefined( self ) || !isalive( self ) ) return;
        moving = ( DistanceSquared( self.origin, last ) > TOD_DOPPEL_AMB_MOVED_SQ );
        last = self.origin;
        if ( IS_TRUE( self.tod_bo6_attacking ) || IS_TRUE( self.tod_bo6_juking ) ) continue;
        if ( self vox_recent( TOD_DOPPEL_AMB_VOX_GAP_MS ) ) continue;
        now = GetTime();
        if ( isdefined( level.tod_bo6_amb_next_ms ) && now < level.tod_bo6_amb_next_ms ) continue;
        level.tod_bo6_amb_next_ms = now + TOD_DOPPEL_AMB_GLOBAL_MS;
        emit( self, TOD_DOPPEL_AMB_ALIAS, "ambience_cadence" );
    }
}

// True when this ghoul voiced anything in the last gap_ms (self = the actor).
function vox_recent( gap_ms )
{
    if ( !isdefined( self.tod_bo6_audio_last ) ) return false;
    now = GetTime();
    voices = array( TOD_DOPPEL_SCREECH_ALIAS, "vox_ai_ghoul_attack", "vox_ai_ghoul_juke", "vox_ai_ghoul_pain", "vox_ai_ghoul_spawn", TOD_DOPPEL_AMB_ALIAS );
    foreach ( voice in voices )
    {
        t = self.tod_bo6_audio_last[voice];
        if ( isdefined( t ) && now - t < gap_ms ) return true;
    }
    return false;
}

// PUBLIC — a 3D one-shot at a point that outlives whatever made it: a spawned
// script_origin plays it and is deleted after life_secs (the THE DEATH TAILS
// note above). An empty entity pool drops the sound, never throws.
function sound_at( alias, org, life_secs )
{
    if ( !isdefined( alias ) || !isdefined( org ) ) return;
    if ( !isdefined( life_secs ) ) life_secs = TOD_BO6_TAIL_SECS;
    e = Spawn( "script_origin", org );
    if ( !isdefined( e ) )
    {
        dev_log( "TAIL_DROPPED alias=" + alias + " reason=entity_pool" );
        return;
    }
    e PlaySound( alias );
    e thread carrier_cleanup( life_secs );
    dev_log( "TAIL alias=" + alias + " carrier=" + e GetEntityNumber() + " secs=" + life_secs );
}

function carrier_cleanup( life_secs )   // self = the carrier
{
    level endon( "end_game" );
    wait life_secs;
    if ( isdefined( self ) ) self Delete();
}

function approach_screech()
{
    self endon( "death" );
    level endon( "end_game" );
    wait RandomFloatRange( 1.0, 2.0 );
    while ( isdefined( self ) && isalive( self ) )
    {
        wait RandomFloatRange( TOD_DOPPEL_SCREECH_MIN_S, TOD_DOPPEL_SCREECH_MAX_S );
        if ( !isdefined( self ) || !isalive( self ) ) return;
        if ( IS_TRUE( self.tod_bo6_attacking ) || IS_TRUE( self.tod_bo6_juking ) ) continue;
        target = self.favoriteenemy;
        if ( isdefined( target ) && isdefined( target.origin ) &&
             DistanceSquared( self.origin, target.origin ) < TOD_DOPPEL_SCREECH_FAR * TOD_DOPPEL_SCREECH_FAR ) continue;
        emit( self, TOD_DOPPEL_SCREECH_ALIAS, "approach_screech" );
    }
}

function watch_scripted_notes()
{
    // Continue through death so the original death clip can deliver its tail;
    // entity deletion ends this thread. No extra entity or loop sound is owned.
    level endon( "end_game" );
    while ( 1 )
    {
        self waittill( "note_notify", note );
        if ( !isdefined( note ) ) continue;
        alias = level.tod_bo6_note_alias[note];
        if ( isdefined( alias ) ) emit( self, alias, "scripted_notetrack" );
    }
}

function watch_damage( kind )
{
    self endon( "death" );
    level endon( "end_game" );
    if ( kind == "mangler" )
    {
        self mangler_pain_watch();   // THE MANGLER'S VOICE: pain grunts on a gap + the berserk roar
        return;
    }
    next_voice = 0;
    while ( 1 )
    {
        self waittill( "damage", amount );
        if ( !isdefined( amount ) || amount <= 0 || GetTime() < next_voice ) continue;
        if ( kind == "amalgam" ) emit( self, "vox_ai_amalgam_pain", "damage" );
        else emit( self, "vox_ai_ghoul_pain", "damage" );
        next_voice = GetTime() + 1200;
    }
}

function death( actor, kind )
{
    if ( kind == "amalgam" ) emit( actor, "evt_ai_amalgam_death", "death" ); // source Secondary supplies voice
    else if ( kind == "doppelghast" ) emit( actor, "vox_ai_ghoul_death", "death" );
    else
    {
        emit( actor, "fly_ai_mangler_death_collapse", "death" );
        emit( actor, "vox_ai_mangler_death", "death_voice" );   // THE MANGLER'S VOICE: the dying roar, on a carrier (outlives the corpse)
    }
}

// THE MANGLER'S VOICE (the defines above). self = the Mangler. Every hit asks mangler_pain_pick what it earns.
function mangler_pain_watch()
{
    self endon( "death" );
    level endon( "end_game" );
    next_pain = 0;
    while ( 1 )
    {
        self waittill( "damage", amount );
        if ( !isdefined( amount ) || amount <= 0 ) continue;
        now = GetTime();
        pick = mangler_pain_pick( self.health, self.maxhealth, IS_TRUE( self.tod_bo6_mangler_berserk ),
                                  IS_TRUE( self.tod_mangler_attacking ), now, next_pain, mangler_last_vox( self ) );
        if ( pick == "roar" )
        {
            self.tod_bo6_mangler_berserk = true;
            next_pain = now + TOD_MANGLER_PAIN_GAP_MAX_MS;
            emit( self, "vox_ai_mangler_roar", "berserk" );
            dev_log( "MANGLER_BERSERK entity=" + self GetEntityNumber() + " health=" + self.health + " max=" + self.maxhealth );
        }
        else if ( pick == "pain" )
        {
            next_pain = now + RandomIntRange( TOD_MANGLER_PAIN_GAP_MIN_MS, TOD_MANGLER_PAIN_GAP_MAX_MS );
            emit( self, "vox_ai_mangler_pain", "damage" );
        }
    }
}

// PURE (tools/original_rips/test_original_rips.js runs it through gsc_eval): the voice one Mangler hit earns.
// "roar" once, on the first hit that leaves it at or under TOD_MANGLER_BERSERK_FRAC of its health (even mid-attack:
// it is the moment the player's damage lands); "pain" when the gap has passed, it is not attacking and it has not
// voiced for TOD_MANGLER_VOX_GAP_MS; "" otherwise (and on the killing blow: the death voice owns that).
function mangler_pain_pick( health, maxhealth, berserked, attacking, now, next_pain_ms, last_vox_ms )
{
    if ( !isdefined( health ) || !isdefined( maxhealth ) || maxhealth <= 0 || health <= 0 ) return "";
    if ( !berserked && health <= maxhealth * TOD_MANGLER_BERSERK_FRAC ) return "roar";
    if ( attacking ) return "";
    if ( now < next_pain_ms ) return "";
    if ( isdefined( last_vox_ms ) && now - last_vox_ms < TOD_MANGLER_VOX_GAP_MS ) return "";
    return "pain";
}

// PURE: may this Mangler growl now? Not mid-attack, not on top of its own last voice, and the map's growls apart.
function mangler_amb_ready( attacking, now, last_vox_ms, global_next_ms )
{
    if ( attacking ) return false;
    if ( isdefined( last_vox_ms ) && now - last_vox_ms < TOD_MANGLER_VOX_GAP_MS ) return false;
    if ( isdefined( global_next_ms ) && now < global_next_ms ) return false;
    return true;
}

// PURE: when this Mangler last voiced anything (undefined = never).
function mangler_last_vox( actor )
{
    if ( !isdefined( actor ) || !isdefined( actor.tod_bo6_audio_last ) ) return undefined;
    last = undefined;
    voices = array( "vox_ai_mangler_roar", "vox_ai_mangler_melee", "vox_ai_mangler_shoot", "vox_ai_mangler_pain", "vox_ai_mangler_ambience" );
    foreach ( voice in voices )
    {
        t = actor.tod_bo6_audio_last[voice];
        if ( isdefined( t ) && ( !isdefined( last ) || t > last ) ) last = t;
    }
    return last;
}

// THE HUNTING GROWL (self = the Mangler): a muffled growl every TOD_MANGLER_AMB_MIN_S..MAX_S while it lives, never
// mid-attack or on top of its own voice; emit() refuses it under a world pause like every other lane.
function mangler_ambience_cadence()
{
    self endon( "death" );
    level endon( "end_game" );
    while ( isdefined( self ) && isalive( self ) )
    {
        wait RandomFloatRange( TOD_MANGLER_AMB_MIN_S, TOD_MANGLER_AMB_MAX_S );
        if ( !isdefined( self ) || !isalive( self ) ) return;
        now = GetTime();
        if ( !mangler_amb_ready( IS_TRUE( self.tod_mangler_attacking ), now, mangler_last_vox( self ), level.tod_bo6_mangler_amb_next_ms ) ) continue;
        level.tod_bo6_mangler_amb_next_ms = now + TOD_MANGLER_AMB_GLOBAL_MS;
        emit( self, "vox_ai_mangler_ambience", "ambience_cadence" );
    }
}
