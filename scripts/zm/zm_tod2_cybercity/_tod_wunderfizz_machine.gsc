// STAGED. Exact BO6Overhaul/WetEgg machine presentation; no substitute assets.
// Root lands this with its CSC, generated data, native art and sound receipts.
#using scripts\shared\animation_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_audio;
#using scripts\zm\_zm_perks;
#using scripts\zm\_zm_unitrigger;
#using scripts\zm\zm_tod2_cybercity\_tod_wunderfizz;
#using scripts\zm\zm_tod2_cybercity\_tod_wunderfizz_data;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#using_animtree( "generic" );
#precache( "model", "t10_zm_machine_wunderfizz_fxanim" );
#precache( "model", "t10_zm_machine_wunderfizz_fxanim_on" );
#define TOD_WF_HUM_LIMIT 6
#define TOD_WF_HUM_DIST 600
#define TOD_WF_QUEUE_LIMIT 36
#define TOD_WF_TRIG_HEIGHT 80
#namespace tod_wunderfizz_machine;

REGISTER_SYSTEM( "tod_wunderfizz_machine", &__init__, undefined )

function __init__()
{
    // One late-join-replayed bit; exactly mirrored by the matching CSC.
    clientfield::register( "scriptmover", "todWunderfizzIdle", VERSION_SHIP, 1, "int" );
}

function init()
{
    if ( IS_TRUE( level.tod_wf_machine_init ) ) return;
    level.tod_wf_machine_init = true;
    level.tod_wf_machine_shutdown = false;
    level.tod_wf_present_fn = &present;
    ensure_perk_precache();
    // Register per-player responses/refund watchers before any trigger opens.
    tod_wunderfizz::init();
    level.tod_wf_machines = tod_wunderfizz_data::nodes();
    foreach ( m in level.tod_wf_machines )
    {
        m.live = false;
        m.buyers = 0;
        m.powered = false;
        m.model_power = false;
        m.hum = false;
        m.queue = [];
        m.anim_busy = false;
        m.rekicked = false;
        m.rekick_pending = false;
        m.next_jingle = GetTime() + RandomIntRange( 30000, 60000 );
        m.host = spawn_host( m, false );
        if ( !isdefined( m.host ) )
        {
            dev_log( "SPAWN_FAILED floor=" + m.floor + " reason=model_entity" );
            continue;
        }
        m.live = true;
        m.stub = SpawnStruct();
        // Native look checks target the original model hint, not the buyer's
        // standing point. Keep m.trig unchanged for backend range and nav.
        m.stub.origin = m.host GetTagOrigin( "tag_hint" );
        m.stub.angles = ( 0, m.yaw, 0 );
        m.stub.machine = m;
        m.stub.radius = m.r;
        m.stub.script_height = TOD_WF_TRIG_HEIGHT;
        m.stub.script_unitrigger_type = "unitrigger_radius_use";
        m.stub.cursor_hint = "HINT_NOICON";
        m.stub.require_look_at = true;
        m.stub.hint_string = hint_for_state( "ready" );
        m.stub.prompt_and_visibility_func = &prompt_and_visibility;
        zm_unitrigger::unitrigger_force_per_player_triggers( m.stub, true );
        zm_unitrigger::register_static_unitrigger( m.stub, &use_loop );
        dev_log( "SPAWN floor=" + m.floor + " id=" + m.id + " org=" + m.org + " trig=" + m.trig + " hint=" + m.stub.origin + " r=" + m.r + " yaw=" + m.yaw + " scale=1" );
    }
    level thread world_watch();
    level thread end_game_watch();
    dev_log( "INIT counters=" + level.tod_wf_machines.size + " native_notes=1 hum_limit=6 serial_art_only=1" );
}

function ensure_perk_precache()
{
    // Stock perk init returns before precaching when no zombie_vending
    // entities exist. Player effects (including Widow's Wine wrap) still
    // require those callbacks. Mirror only that skipped native step; never
    // respawn a vendor or restart any individual-machine/power threads.
    if ( isdefined( level.machine_assets ) ) return false;
    level.machine_assets = [];
    custom = isdefined( level.custom_vending_precaching );
    if ( custom ) [[ level.custom_vending_precaching ]]();
    else zm_perks::default_vending_precaching();
    dev_log( "PERK_PRECACHE vendors=0 native_custom=" + custom );
    return true;
}

function spawn_host( m, powered )
{
    name = "t10_zm_machine_wunderfizz_fxanim";
    if ( powered ) name = "t10_zm_machine_wunderfizz_fxanim_on";
    host = Spawn( "script_model", m.org, 0 );
    if ( !isdefined( host ) ) return undefined;
    host SetModel( name );
    host.angles = ( 0, m.yaw, 0 );
    // Exact original hulls are generated world clip, never movable blockers.
    host NotSolid();
    host.scale = 1;
    host useanimtree( #animtree );
    host.sndJingleCooldown = false;
    idle = 0;
    if ( powered ) idle = 1;
    host clientfield::set( "todWunderfizzIdle", idle );
    return host;
}

// Four permanent hint strings for all haven counters. Costs live in the menu,
// never in the engine's finite hint table. TodPromptCard strips the leading
// native USE binding into its footer, leaving the noun first in its title.
function hint_for_state( kind )
{
    if ( kind == "power" ) return "^5WUNDERFIZZ^7 - ^1Power required";
    if ( kind == "owned" ) return "^5WUNDERFIZZ^7 - All perks owned";
    if ( kind == "busy" ) return "^5WUNDERFIZZ^7 - Finish your current action";
    return "Hold ^3[{+activate}]^7 ^5WUNDERFIZZ^7 - Choose a perk";
}

// self = one player's native trigger. Engine/unitrigger owns its deletion.
function prompt_and_visibility( p )
{
    if ( !isdefined( p ) || !IsPlayer( p ) || !isdefined( self.stub ) ) return false;
    m = self.stub.machine;
    if ( !isdefined( m ) || !IS_TRUE( m.live ) || !isdefined( m.host ) ) return false;
    if ( IS_TRUE( p.tod_wf_menu_active ) ) return false;
    s = tod_wunderfizz::state( p, m );
    if ( !s.alive || s.downed || !s.drafted || s.menu || s.reviving ) return false;
    kind = "ready";
    q = tod_wunderfizz::snapshot( p, m );
    if ( q.owned == 511 ) kind = "owned";
    else if ( q.available == 0 && !s.power ) kind = "power";
    else if ( tod_wunderfizz::refusal_from_state( s, false ) != "" ) kind = "busy";
    if ( !isdefined( self.tod_wf_hint_kind ) || self.tod_wf_hint_kind != kind )
    {
        self.tod_wf_hint_kind = kind;
        self SetHintString( hint_for_state( kind ) );
    }
    return true;
}

function use_loop()
{
    self endon( "kill_trigger" );
    while ( true )
    {
        self waittill( "trigger", p );
        if ( !isdefined( p ) || !IsPlayer( p ) || IS_TRUE( p.tod_wf_use_latched ) ) continue;
        p.tod_wf_use_latched = true;
        p thread release_use();
        m = self.stub.machine;
        reason = tod_wunderfizz::open( p, m );
        if ( reason != "" )
        {
            // State refusals already call present(); early API exits do not.
            if ( reason == "session" || reason == "all_owned" || reason == "player" ) present( p, m, "refuse", undefined );
            dev_log( "USE_REFUSED client=" + p GetEntityNumber() + " floor=" + m.floor + " reason=" + reason );
        }
    }
}

function release_use()
{
    self endon( "disconnect" );
    self endon( "end_game" );
    while ( self UseButtonPressed() ) wait 0.05;
    self.tod_wf_use_latched = undefined;
}

// This hook never waits. Queueing native art cannot hold up a player's debit,
// drink, refund, another player's selector, or a purchase on another floor.
function present( p, m, kind, perk )
{
    if ( kind == "refuse" || kind == "interrupt" )
    {
        if ( isdefined( p ) )
        {
            p PlaySound( "zmb_no_purchase" );
            // A selector is already closed when its bottle is interrupted.
            // This free HUD text lane survives that close, without adding a
            // hint-table entry or claiming an unverified native refund.
            if ( kind == "interrupt" ) p IPrintLn( "^1WUNDERFIZZ^7 - Purchase cancelled" );
            else p IPrintLn( "^1WUNDERFIZZ^7 - Cannot buy right now" );
        }
        return;
    }
    if ( kind != "purchase" ) return;
    if ( isdefined( p ) ) p PlaySound( "zmb_cha_ching" );
    if ( !isdefined( m ) || !IS_TRUE( m.live ) || !isdefined( m.host ) ) return;
    q = SpawnStruct();
    q.tx = p.tod_wf_tx;
    q.client = p GetEntityNumber();
    q.perk = perk;
    q.enqueued = GetTime();
    // Nine identities x four co-op players. Finished/interrupted records are
    // pruned before capacity is checked; this is presentation, never a lock.
    prune_queue( m );
    if ( m.queue.size >= TOD_WF_QUEUE_LIMIT )
    {
        dev_log( "QUEUE_FULL floor=" + m.floor + " client=" + q.client + " perk=" + perk + " art_only=1" );
        return;
    }
    m.queue[ m.queue.size ] = q;
    dev_log( "QUEUE floor=" + m.floor + " client=" + q.client + " perk=" + perk + " depth=" + m.queue.size );
}

function queued_valid( q )
{
    if ( !isdefined( q ) || !isdefined( q.tx ) || !isdefined( q.tx.p ) ) return false;
    return ( !IS_TRUE( q.tx.finished ) || IS_TRUE( q.tx.granted ) );
}

function prune_queue( m )
{
    kept = [];
    foreach ( q in m.queue ) if ( queued_valid( q ) ) kept[ kept.size ] = q;
    m.queue = kept;
}

function shift_queue( m )
{
    q = m.queue[ 0 ];
    tail = [];
    for ( i = 1; i < m.queue.size; i++ ) tail[ tail.size ] = m.queue[ i ];
    m.queue = tail;
    return q;
}

function presentation_tick( m, now )
{
    if ( !IS_TRUE( m.live ) || !isdefined( m.host ) ) return;
    if ( IS_TRUE( m.anim_busy ) )
    {
        if ( now < m.anim_end ) return;
        m.host animation::stop( 0 );
        m.host.origin = m.org;
        m.host.angles = ( 0, m.yaw, 0 );
        m.anim_busy = false;
        m.active = undefined;
        if ( m.model_power != m.powered )
        {
            name = "t10_zm_machine_wunderfizz_fxanim";
            if ( IS_TRUE( m.powered ) ) name = "t10_zm_machine_wunderfizz_fxanim_on";
            m.host SetModel( name );
            m.model_power = m.powered;
        }
        dev_log( "ACTIVATE_END floor=" + m.floor + " native_final_note=120" );
    }
    prune_queue( m );
    if ( m.queue.size == 0 ) return;
    q = shift_queue( m );
    m.active = q;
    m.anim_busy = true;
    // Stock play() waits for scriptedanim notifications. Launch it on the
    // host so one counter cannot suspend this level-owned world watcher.
    // Keep frame120's native Stop Fx note: no early blend-out. Sound, its
    // electricity secondary, and spark emitters are authored asset notes.
    m.anim_end = now + int( GetAnimLength( "t10_zm_machine_wunderfizz_fxanim_activate" ) * 1000 ) + 100;
    m.host thread animation::play( "t10_zm_machine_wunderfizz_fxanim_activate", m.org, ( 0, m.yaw, 0 ), 1, 0, 0 );
    dev_log( "ACTIVATE floor=" + m.floor + " client=" + q.client + " perk=" + q.perk + " lag_ms=" + ( now - q.enqueued ) + " duration_ms=" + ( m.anim_end - now ) + " powered=" + m.powered );
}

// Stable nearest-six arbitration preserves the original alias global cap.
// Eager distant PlayLoopSound requests could consume it before nearby hosts.
function audible_indices( distances )
{
    picked = [];
    used = [];
    for ( rank = 0; rank < TOD_WF_HUM_LIMIT; rank++ )
    {
        best = -1;
        best_dist = TOD_WF_HUM_DIST * TOD_WF_HUM_DIST + 1;
        for ( i = 0; i < distances.size; i++ )
        {
            if ( IS_TRUE( used[ i ] ) || distances[ i ] > TOD_WF_HUM_DIST * TOD_WF_HUM_DIST ) continue;
            if ( distances[ i ] < best_dist ) { best = i; best_dist = distances[ i ]; }
        }
        if ( best < 0 ) break;
        used[ best ] = true;
        picked[ picked.size ] = best;
    }
    return picked;
}

function nearest_distance( m, players )
{
    nearest = 2147483647;
    foreach ( p in players )
        if ( isdefined( p ) && IsAlive( p ) ) nearest = min( nearest, DistanceSquared( p.origin, m.org ) );
    return nearest;
}

function sound_tick( nodes, players, now )
{
    distances = [];
    foreach ( m in nodes )
    {
        m.want_hum = false;
        dist = 2147483647;
        if ( IS_TRUE( m.live ) && IS_TRUE( m.powered ) && isdefined( m.host ) ) dist = nearest_distance( m, players );
        distances[ distances.size ] = dist;
        if ( dist <= 700 * 700 && !IS_TRUE( m.rekicked ) && IS_TRUE( m.powered ) && isdefined( m.host ) )
        {
            m.rekicked = true;
            m.rekick_pending = true;
            m.host clientfield::set( "todWunderfizzIdle", 0 );
            dev_log( "IDLE_REKICK floor=" + m.floor );
        }
    }
    selected = audible_indices( distances );
    foreach ( i in selected ) nodes[ i ].want_hum = true;
    // Release losing voices before requesting new ones under the native cap.
    foreach ( m in nodes )
        if ( IS_TRUE( m.hum ) && !IS_TRUE( m.want_hum ) ) hum_set( m, false );
    foreach ( m in nodes )
    {
        if ( !IS_TRUE( m.hum ) && IS_TRUE( m.want_hum ) ) hum_set( m, true );
        if ( now >= m.next_jingle )
        {
            m.next_jingle = now + RandomIntRange( 30000, 60000 );
            if ( IS_TRUE( m.hum ) && !IS_TRUE( m.anim_busy ) && !IS_TRUE( m.host.sndJingleCooldown ) && !IS_TRUE( level.tod_music_ee ) && !IS_TRUE( level.tod_music_victory ) && RandomInt( 100 ) < 10 )
            {
                m.host.script_sound = jingle_alias( RandomIntRange( 1, 10 ) );
                m.host thread zm_audio::sndPerksJingles_Player( 0 );
                dev_log( "JINGLE floor=" + m.floor + " alias=" + m.host.script_sound );
            }
        }
    }
}

function jingle_alias( id )
{
    all = array( "mus_perks_jugganog_jingle", "mus_perks_speed_jingle", "mus_perks_revive_jingle",
        "mus_perks_stamin_jingle", "mus_perks_widow_jingle", "mus_perk_deathperception_jingle",
        "mus_perks_doubletap_jingle", "mus_perk_wisptea_jingle", "mus_perk_phd_jingle" );
    return all[ id - 1 ];
}

function hum_set( m, on )
{
    if ( !isdefined( m.host ) ) { m.hum = false; return; }
    if ( on ) m.host PlayLoopSound( "evt_wunderfizz_humming_loop" );
    else m.host StopLoopSound();
    m.hum = on;
    dev_log( "HUM floor=" + m.floor + " on=" + on );
}

function cancel_machine_sessions( m, why )
{
    if ( !isdefined( level.tod_wf_sessions ) ) return;
    foreach ( tx in level.tod_wf_sessions )
        if ( isdefined( tx ) && tx.machine == m && isdefined( tx.p ) )
            tod_wunderfizz::cancel( tx.p, tx.seq, why );
}

function remove_host( m )
{
    if ( isdefined( m.host ) )
    {
        m.host clientfield::set( "todWunderfizzIdle", 0 );
        if ( IS_TRUE( m.hum ) ) m.host StopLoopSound();
        if ( IS_TRUE( m.anim_busy ) )
        {
            m.host notify( "new_scripted_anim" );
            m.host animation::stop( 0 );
        }
        // Authored engine Play Fx notes attach to this native model host.
        // Deleting it also owns forced cleanup before the frame120 Stop Fx.
        m.host Delete();
    }
    m.host = undefined;
    m.hum = false;
    m.anim_busy = false;
    m.active = undefined;
}

function apply_power( m, on )
{
    if ( !IS_TRUE( m.live ) || !isdefined( m.host ) || m.powered == on ) return;
    m.powered = on;
    m.rekicked = false;
    m.rekick_pending = false;
    if ( on )
    {
        // Power can arrive during the solo pre-power QR activation. Do not
        // rebuild its DObj mid-clip and lose the authored final FX note.
        if ( !IS_TRUE( m.anim_busy ) )
        {
            m.host SetModel( "t10_zm_machine_wunderfizz_fxanim_on" );
            m.model_power = true;
        }
        m.host clientfield::set( "todWunderfizzIdle", 1 );
    }
    else
    {
        cancel_machine_sessions( m, "power" );
        m.queue = [];
        remove_host( m );
        m.host = spawn_host( m, false );
        m.model_power = false;
        if ( !isdefined( m.host ) ) retire( m, "power_host_failed" );
    }
    dev_log( "POWER floor=" + m.floor + " on=" + on );
}

// One cheap level owner for power, proximity, queues and unexpected host loss.
// It has no endon that could skip cleanup; end_game_watch also calls shutdown.
function world_watch()
{
    next_sound = 0;
    while ( !IS_TRUE( level.tod_wf_machine_shutdown ) )
    {
        if ( IS_TRUE( level.intermission ) ) { shutdown( "intermission" ); return; }
        now = GetTime();
        power = level flag::get( "power_on" );
        foreach ( m in level.tod_wf_machines )
        {
            if ( !IS_TRUE( m.live ) ) continue;
            if ( !isdefined( m.host ) ) { retire( m, "host_lost" ); continue; }
            if ( IS_TRUE( m.rekick_pending ) )
            {
                m.rekick_pending = false;
                if ( IS_TRUE( m.powered ) ) m.host clientfield::set( "todWunderfizzIdle", 1 );
            }
            apply_power( m, power );
            presentation_tick( m, now );
        }
        if ( now >= next_sound )
        {
            sound_tick( level.tod_wf_machines, GetPlayers(), now );
            next_sound = now + 500;
        }
        wait 0.1;
    }
}

function retire( m, why )
{
    if ( !isdefined( m ) || !IS_TRUE( m.live ) ) return;
    m.live = false;
    cancel_machine_sessions( m, why );
    m.queue = [];
    if ( isdefined( m.stub ) )
    {
        // Stock playertrigger slots may contain undefined disconnect holes;
        // prune them before native unregister notifies each owned trigger.
        if ( isdefined( m.stub.playertrigger ) )
        {
            kept = [];
            foreach ( key in GetArrayKeys( m.stub.playertrigger ) )
                if ( isdefined( m.stub.playertrigger[ key ] ) ) kept[ key ] = m.stub.playertrigger[ key ];
            m.stub.playertrigger = kept;
        }
        zm_unitrigger::unregister_unitrigger( m.stub );
        m.stub = undefined;
    }
    remove_host( m );
    dev_log( "RETIRE floor=" + m.floor + " reason=" + why + " buyers=" + m.buyers );
}

function shutdown( why )
{
    if ( IS_TRUE( level.tod_wf_machine_shutdown ) ) return;
    level.tod_wf_machine_shutdown = true;
    foreach ( m in level.tod_wf_machines ) retire( m, why );
    dev_log( "SHUTDOWN reason=" + why );
}

function end_game_watch()
{
    level waittill( "end_game" );
    shutdown( "end_game" );
}

function dev_log( detail )
{
    out = "[TOD_WF_MACHINE] " + detail;
    if ( !IS_TRUE( level.tod_dev ) && !IS_TRUE( level.tod_diag ) ) return;
    /# PrintLn( out ); #/
}
