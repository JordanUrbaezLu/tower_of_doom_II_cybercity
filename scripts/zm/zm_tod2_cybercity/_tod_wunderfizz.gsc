// STAGED: exact-model machine spawning and authored BO6 presentation are root
// integration tasks. This module accepts generated/live machine descriptors;
// it never copies layout coordinates or substitutes a machine model/sound.
#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_perks;
#using scripts\zm\_zm_pers_upgrades_functions;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_weapons;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_roster;
#insert scripts\shared\shared.gsh;
#precache( "lui_menu", "tod_wunderfizz" );
#precache( "eventstring", "tod_wf_state" );
#precache( "eventstring", "tod_wf_close" );
#precache( "eventstring", "tod_wf_result" );
#define TOD_WF_BASE_COST 2000
#define TOD_WF_STEP_COST 500
#define TOD_WF_MENU_MS 20000
#define TOD_WF_DRINK_MS 8000
#define TOD_WF_HEARTBEAT_MS 500
#namespace tod_wunderfizz;

function init()
{
    if ( IS_TRUE( level.tod_wf_init ) ) return;
    level.tod_wf_init = true;
    level.tod_wf_seq = 0;
    level.tod_wf_sessions = [];
    callback::on_connect( &on_connect );
    callback::on_spawned( &on_spawned );
    foreach ( p in GetPlayers() ) p on_connect();
    level thread end_game_watch();
    dev_log( "INIT rev=1 roster=9 base=2000 step=500 player_sessions=separate" );
}

function on_connect()
{
    if ( IS_TRUE( self.tod_wf_response_watch ) ) return;
    self.tod_wf_response_watch = true;
    self thread response_watch();
}

function on_spawned()
{
    if ( isdefined( self.tod_wf_tx ) ) finish( self.tod_wf_tx, "spawned" );
}

function next_seq()
{
    level.tod_wf_seq++;
    return level.tod_wf_seq;
}

// Pure functions are executed verbatim by the candidate gate.
function price_from_count( n )
{
    return TOD_WF_BASE_COST + TOD_WF_STEP_COST * n;
}

function qr_paid_allowed( solo, lives )
{
    if ( solo && isdefined( lives ) && lives >= 3 ) return false;
    return true;
}

function offer_allowed( owned, registered, power, solo, lives, id )
{
    if ( owned || !registered ) return false;
    if ( id == 3 && !qr_paid_allowed( solo, lives ) ) return false;
    if ( !power && !( id == 3 && solo ) ) return false;
    return true;
}

function refusal_from_state( s, own_drink )
{
    if ( !s.alive || s.downed ) return "down";
    if ( !s.drafted ) return "draft";
    if ( s.intermission ) return "end_game";
    if ( s.menu || s.world_pause ) return "menu";
    if ( s.flying || s.grappling || s.mantling || !s.grounded ) return "airborne";
    if ( s.ability || s.cloaked ) return "ability";
    if ( s.reviving || s.swapping || s.powerup_weapon ) return "hands";
    if ( s.drinking && !own_drink ) return "drink";
    if ( s.haven_locked ) return "haven";
    if ( !s.machine_live ) return "machine";
    if ( !s.in_range ) return "range";
    return "";
}

function response_id( token )
{
    for ( i = 1; i <= 9; i++ ) if ( token == "" + i ) return i;
    return 0;
}

// UI result IDs: 1 points, 2 quote changed, 3 perk unavailable, 4 busy,
// 5 interrupted purchase, 6 internal/source failure. No clientfield bits.
function result_code( reason )
{
    if ( reason == "points" ) return 1;
    if ( reason == "stale" || reason == "quote" ) return 2;
    if ( reason == "perk" || reason == "owned" || reason == "offer" || reason == "offer_changed" ) return 3;
    if ( reason == "grant_failed" || reason == "menu_failed" ) return 6;
    return 4;
}

function refund_due( tx )
{
    if ( IS_TRUE( tx.granted ) || IS_TRUE( tx.refunded ) || !isdefined( tx.debit ) || tx.debit <= 0 ) return 0;
    return tx.debit;
}

function cancel_allowed( tx, seq )
{
    if ( !isdefined( tx ) || IS_TRUE( tx.finished ) ) return false;
    return ( tx.seq == seq || ( seq == 0 && tx.phase == "menu" ) );
}

function reserve_allowed( tx, seq, id, reason, owned, offered, can_pay, cost )
{
    if ( !isdefined( tx ) || tx.phase != "menu" ) return "session";
    if ( tx.seq != seq ) return "stale";
    if ( id < 1 || id > 9 || int( id ) != id ) return "perk";
    if ( reason != "" ) return reason;
    if ( owned ) return "owned";
    if ( !offered ) return "offer";
    if ( cost != tx.cost ) return "quote";
    if ( !can_pay ) return "points";
    return "";
}

function state( p, m )
{
    s = SpawnStruct();
    s.alive = IsAlive( p );
    s.downed = false;
    s.grounded = false;
    s.mantling = false;
    if ( s.alive )
    {
        s.downed = p laststand::player_is_in_laststand();
        s.grounded = p IsOnGround();
        s.mantling = p IsMantling();
    }
    s.drafted = ( IS_TRUE( level.tod_class_select_done ) && isdefined( p.tod_class ) );
    s.intermission = ( IS_TRUE( level.intermission ) || IS_TRUE( p.intermission ) );
    s.world_pause = IS_TRUE( level.tod_upgrade_pause );
    s.menu = ( IS_TRUE( p.tod_menu_frozen ) || IS_TRUE( p.tod_solo_upg_active ) || IS_TRUE( p.tod_spin_locked ) || IS_TRUE( p.tod_spin_grace ) || IS_TRUE( p.tod_cls_term_busy ) );
    s.flying = IS_TRUE( p.tod_jumppad_flying );
    s.grappling = IS_TRUE( p.tod_grappling );
    s.ability = ( IS_TRUE( p.tod_bash_busy ) || IS_TRUE( p.tod_gs_busy ) || IS_TRUE( p.tod_gs_diving ) || IS_TRUE( p.tod_necro_pulse_busy ) || isdefined( p.tod_necro_bind_t0 ) );
    s.cloaked = ( isdefined( p.tod_cloak_until ) && GetTime() < p.tod_cloak_until );
    s.drinking = ( isdefined( p.is_drinking ) && p.is_drinking > 0 );
    s.reviving = ( IS_TRUE( p.is_reviving_any ) || p zm_utility::in_revive_trigger() );
    s.swapping = ( IS_TRUE( p.tod_tier_busy ) || IS_TRUE( p.tod_swap_busy ) );
    s.powerup_weapon = ( isdefined( p.zombie_vars ) && ( IS_TRUE( p.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( p.zombie_vars[ "zombie_powerup_tod_wunderstrahl_on" ] ) ) );
    s.haven_locked = false;
    if ( isdefined( m ) && isdefined( level.tod_haven_locked_fn ) ) s.haven_locked = [[ level.tod_haven_locked_fn ]]( m.org );
    s.machine_live = ( isdefined( m ) && IS_TRUE( m.live ) && isdefined( m.host ) );
    s.in_range = false;
    if ( s.machine_live ) s.in_range = DistanceSquared( p.origin, m.trig ) <= ( m.r + 64 ) * ( m.r + 64 );
    s.power = level flag::get( "power_on" );
    s.solo = zm_perks::use_solo_revive();
    s.lives = undefined;
    if ( isdefined( level.solo_lives_given ) ) s.lives = level.solo_lives_given;
    return s;
}

function available_mask( p, s )
{
    mask = 0;
    bit = 1;
    all = tod_perk_roster::keys();
    for ( i = 0; i < all.size; i++ )
    {
        perk = all[ i ];
        registered = tod_perk_roster::registered( perk );
        if ( registered ) registered = isdefined( level._custom_perks[ perk ].perk_bottle_weapon );
        if ( offer_allowed( tod_perk_roster::owns( p, perk ), registered, s.power, s.solo, s.lives, i + 1 ) ) mask += bit;
        bit *= 2;
    }
    return mask;
}

function snapshot( p, m )
{
    q = SpawnStruct();
    q.cost = price_from_count( tod_perk_roster::owned_count( p ) );
    q.owned = tod_perk_roster::owned_mask( p );
    q.available = available_mask( p, state( p, m ) );
    return q;
}

function owns_session( tx )
{
    return ( isdefined( tx ) && !IS_TRUE( tx.finished ) && isdefined( tx.p ) && isdefined( tx.p.tod_wf_tx ) && tx.p.tod_wf_tx.op == tx.op );
}

function push_state( tx, force )
{
    if ( !owns_session( tx ) || tx.phase != "menu" ) return;
    q = snapshot( tx.p, tx.machine );
    changed = ( q.cost != tx.cost || q.owned != tx.owned || q.available != tx.available );
    if ( changed ) tx.seq = next_seq(); // stale displayed quotes cannot charge
    tx.cost = q.cost;
    tx.owned = q.owned;
    tx.available = q.available;
    if ( changed || force )
        tx.p LuiNotifyEvent( &"tod_wf_state", 5, tx.seq, tx.machine.floor, tx.cost, tx.owned, tx.available );
}

function open( p, m )
{
    if ( !isdefined( p ) || !IsPlayer( p ) || !isdefined( m ) ) return "player";
    if ( isdefined( p.tod_wf_tx ) ) return "session";
    reason = refusal_from_state( state( p, m ), false );
    if ( reason != "" )
    {
        dev_log( "OPEN_REFUSED client=" + p GetEntityNumber() + " floor=" + m.floor + " reason=" + reason );
        cue( p, m, "refuse", undefined );
        return reason;
    }
    if ( tod_perk_roster::owned_count( p ) >= 9 ) return "all_owned";
    tx = SpawnStruct();
    tx.p = p;
    tx.machine = m;
    tx.op = next_seq();
    tx.seq = tx.op;
    tx.client = p GetEntityNumber();
    tx.phase = "menu";
    tx.deadline = GetTime() + TOD_WF_MENU_MS;
    tx.finished = false;
    tx.granted = false;
    tx.refunded = false;
    tx.debit = 0;
    q = snapshot( p, m );
    tx.cost = q.cost;
    tx.owned = q.owned;
    tx.available = q.available;
    p.tod_wf_tx = tx;
    p.tod_wf_menu_active = true;
    level.tod_wf_sessions[ tx.client ] = tx;
    if ( !isdefined( m.buyers ) ) m.buyers = 0;
    m.buyers++;
    tx.menu = p OpenLUIMenu( "tod_wunderfizz" );
    if ( !isdefined( tx.menu ) )
    {
        finish( tx, "menu_failed" );
        return "menu";
    }
    cue( p, m, "open", undefined );
    dev_log( "OPEN op=" + tx.op + " client=" + tx.client + " floor=" + m.floor + " owned=" + tod_perk_roster::owned_count( p ) + " cost=" + tx.cost + " available=" + tx.available );
    level thread session_watch( tx );
    return "";
}

function respond( p, seq, id )
{
    if ( !isdefined( p ) || !isdefined( p.tod_wf_tx ) ) return "session";
    tx = p.tod_wf_tx;
    if ( !owns_session( tx ) || tx.phase != "menu" ) return "session";
    if ( !isdefined( id ) || id < 1 || id > 9 || int( id ) != id ) return "perk";
    perk = tod_perk_roster::perk_for_id( id );
    s = state( p, tx.machine );
    cost = price_from_count( tod_perk_roster::owned_count( p ) );
    registered = tod_perk_roster::registered( perk );
    if ( registered ) registered = isdefined( level._custom_perks[ perk ].perk_bottle_weapon );
    offered = offer_allowed( tod_perk_roster::owns( p, perk ), registered, s.power, s.solo, s.lives, id );
    reason = reserve_allowed( tx, seq, id, refusal_from_state( s, false ),
        tod_perk_roster::owns( p, perk ), offered, p zm_score::can_player_purchase( cost ), cost );
    if ( reason != "" )
    {
        cue( p, tx.machine, "refuse", perk );
        dev_log( "BUY_REFUSED op=" + tx.op + " client=" + tx.client + " floor=" + tx.machine.floor + " perk=" + perk + " reason=" + reason + " cost=" + cost );
        push_state( tx, true );
        p LuiNotifyEvent( &"tod_wf_result", 2, tx.seq, result_code( reason ) );
        return reason;
    }
    // FINAL VALIDATION -> RESERVATION -> ACTUAL DEBIT: no wait/thread/callback
    // between these writes. Shopping Free may debit zero; never refund cost.
    tx.phase = "drink";
    tx.perk = perk;
    tx.deadline = GetTime() + TOD_WF_DRINK_MS;
    tx.before = p.score;
    p zm_score::minus_to_player_score( cost );
    tx.after = p.score;
    tx.debit = tx.before - tx.after;
    if ( tx.debit < 0 ) tx.debit = 0;
    p.perk_purchased = perk;
    p notify( "perk_purchased", perk );
    close_menu( tx );
    cue( p, tx.machine, "purchase", perk );
    dev_log( "BUY op=" + tx.op + " client=" + tx.client + " floor=" + tx.machine.floor + " perk=" + perk + " owned=" + tod_perk_roster::owned_count( p ) + " quote=" + cost + " debit=" + tx.debit + " before=" + tx.before + " after=" + tx.after );
    p thread drink_worker( tx );
    return "";
}

function response_watch()
{
    self endon( "disconnect" );
    self endon( "end_game" );
    while ( true )
    {
        self waittill( "menuresponse", menu, response );
        if ( !isdefined( menu ) || menu != "tod_wunderfizz" || !isdefined( response ) || !isdefined( self.tod_wf_tx ) ) continue;
        tx = self.tod_wf_tx;
        parts = StrTok( response, "." );
        // Escape before the first hydration may close this player's own menu
        // with seq=0. It cannot cancel or alter a reserved/charged drink.
        if ( parts.size == 2 && parts[ 0 ] == "close" && parts[ 1 ] == "0" && cancel_allowed( tx, 0 ) )
        { finish( tx, "close_initial" ); continue; }
        if ( parts.size < 2 || parts[ 1 ] != "" + tx.seq ) { push_state( tx, true ); continue; }
        if ( parts.size == 2 && parts[ 0 ] == "close" ) { finish( tx, "close" ); continue; }
        if ( parts.size != 3 || parts[ 0 ] != "buy" ) continue;
        id = response_id( parts[ 2 ] );
        if ( id > 0 ) respond( self, tx.seq, id );
    }
}

// This level-owned watchdog survives player-worker endons. No actor/level
// lifetime termination can strand a charged purchase, pending perk or menu.
function session_watch( tx )
{
    last_push = 0;
    while ( !IS_TRUE( tx.finished ) )
    {
        wait 0.1;
        if ( !owns_session( tx ) ) { finish( tx, "disconnect" ); return; }
        now = GetTime();
        if ( now >= tx.deadline ) { finish( tx, "timeout" ); return; }
        own_drink = ( tx.phase == "drink" && IS_TRUE( tx.drink_started ) );
        reason = refusal_from_state( state( tx.p, tx.machine ), own_drink );
        if ( reason != "" ) { finish( tx, reason ); return; }
        if ( tx.phase == "menu" && now - last_push >= TOD_WF_HEARTBEAT_MS )
        {
            push_state( tx, true );
            last_push = now;
        }
    }
}

function drink_worker( tx )
{
    self endon( "disconnect" );
    self endon( "end_game" );
    self endon( "tod_wf_abort" );
    if ( !owns_session( tx ) ) return;
    tx.drinking_before = 0;
    if ( isdefined( self.is_drinking ) ) tx.drinking_before = self.is_drinking;
    tx.original = self GetCurrentWeapon();
    tx.can = level._custom_perks[ tx.perk ].perk_bottle_weapon;
    tx.drink_started = true;
    self zm_perks::perk_give_bottle_begin( tx.perk );
    event = self util::waittill_any_return( "weapon_change_complete", "player_downed", "fake_death", "death", "perk_abort_drinking" );
    if ( event != "weapon_change_complete" ) { finish( tx, event ); return; }
    self zm_perks::perk_give_bottle_end( tx.original, tx.perk );
    // The stock end helper can await weapon_change_complete forever. The
    // separate watchdog owns the timeout and forces our idempotent cleanup.
    if ( !owns_session( tx ) ) return;
    reason = refusal_from_state( state( self, tx.machine ), true );
    id = 0;
    all = tod_perk_roster::keys();
    for ( i = 0; i < all.size; i++ ) if ( all[ i ] == tx.perk ) id = i + 1;
    s = state( self, tx.machine );
    if ( reason == "" && !offer_allowed( tod_perk_roster::owns( self, tx.perk ), tod_perk_roster::registered( tx.perk ), s.power, s.solo, s.lives, id ) ) reason = "offer_changed";
    if ( reason != "" ) { finish( tx, reason ); return; }
    self zm_perks::give_perk( tx.perk, true );
    tx.granted = tod_perk_roster::owns( self, tx.perk );
    if ( !tx.granted ) { finish( tx, "grant_failed" ); return; }
    self notify( "burp" );
    if ( IS_TRUE( level.pers_upgrade_cash_back ) ) self zm_pers_upgrades_functions::cash_back_player_drinks_perk();
    if ( IS_TRUE( level.pers_upgrade_perk_lose ) ) self thread zm_pers_upgrades_functions::pers_upgrade_perk_lose_bought();
    if ( isdefined( level.perk_bought_func ) ) self [[ level.perk_bought_func ]]( tx.perk );
    cue( self, tx.machine, "grant", tx.perk );
    dev_log( "GRANT op=" + tx.op + " client=" + tx.client + " floor=" + tx.machine.floor + " perk=" + tx.perk + " owned=" + tod_perk_roster::owned_count( self ) + " debit=" + tx.debit );
    finish( tx, "granted" );
}

function close_menu( tx )
{
    if ( !isdefined( tx.p ) ) return;
    if ( isdefined( tx.menu ) ) tx.p CloseLUIMenu( tx.menu );
    tx.menu = undefined;
    tx.p.tod_wf_menu_active = undefined;
    tx.p LuiNotifyEvent( &"tod_wf_close", 1, tx.seq );
}

function cancel( p, seq, why )
{
    if ( !isdefined( p ) || !isdefined( p.tod_wf_tx ) || !cancel_allowed( p.tod_wf_tx, seq ) ) return false;
    finish( p.tod_wf_tx, why );
    return true;
}

function finish( tx, why )
{
    if ( !isdefined( tx ) || IS_TRUE( tx.finished ) ) return;
    tx.finished = true; // synchronous claim prevents a late worker grant
    // Cleanup must NEVER run in the bottle worker: notifying its endon would
    // kill that thread before refund/control restoration. This detached level
    // thread owns every exit, including a worker's successful completion.
    level thread finish_cleanup( tx, why );
}

function finish_cleanup( tx, why )
{
    p = tx.p;
    close_menu( tx );
    if ( isdefined( p ) )
    {
        p notify( "tod_wf_abort" );
        if ( IS_TRUE( tx.drink_started ) )
        {
            // Own one drink increment only. Stock down/abort may have already
            // consumed it; never underflow or unwind another owner's drink.
            if ( isdefined( p.is_drinking ) && p.is_drinking > tx.drinking_before )
                p zm_perks::perk_abort_drinking();
            if ( isdefined( tx.can ) && p HasWeapon( tx.can ) ) p TakeWeapon( tx.can );
            if ( !IS_TRUE( tx.granted ) && IsAlive( p ) && !( p laststand::player_is_in_laststand() ) && !IS_TRUE( p.intermission ) )
                p zm_weapons::switch_back_primary_weapon( tx.original, true );
        }
        if ( isdefined( tx.perk ) && isdefined( p.perk_purchased ) && p.perk_purchased == tx.perk ) p.perk_purchased = undefined;
        refund = refund_due( tx );
        tx.refunded = true;
        if ( refund > 0 )
        {
            before_refund = p.score;
            p zm_score::add_to_player_score( refund, false );
            dev_log( "REFUND op=" + tx.op + " client=" + tx.client + " floor=" + tx.machine.floor + " perk=" + tx.perk + " reason=" + why + " actual_debit=" + refund + " credited=" + ( p.score - before_refund ) );
        }
        if ( isdefined( p.tod_wf_tx ) && p.tod_wf_tx.op == tx.op ) p.tod_wf_tx = undefined;
        if ( tx.phase == "drink" && !IS_TRUE( tx.granted ) )
        {
            code = 5;
            if ( why == "grant_failed" ) code = 6;
            p LuiNotifyEvent( &"tod_wf_result", 2, tx.seq, code );
            cue( p, tx.machine, "interrupt", tx.perk );
        }
    }
    else if ( tx.debit > 0 && !IS_TRUE( tx.granted ) )
        dev_log( "REFUND_SKIPPED op=" + tx.op + " client=" + tx.client + " reason=player_entity_gone actual_debit=" + tx.debit );
    if ( isdefined( tx.machine.buyers ) && tx.machine.buyers > 0 ) tx.machine.buyers--;
    if ( isdefined( level.tod_wf_sessions[ tx.client ] ) && level.tod_wf_sessions[ tx.client ].op == tx.op ) level.tod_wf_sessions[ tx.client ] = undefined;
    dev_log( "CLOSE op=" + tx.op + " client=" + tx.client + " floor=" + tx.machine.floor + " reason=" + why + " granted=" + tx.granted + " debit=" + tx.debit );
}

function end_game_watch()
{
    level waittill( "end_game" );
    foreach ( tx in level.tod_wf_sessions ) if ( isdefined( tx ) ) finish( tx, "end_game" );
}

// Root supplies the exact imported BO6 alias/animation presentation callback.
function cue( p, m, kind, perk )
{
    if ( isdefined( level.tod_wf_present_fn ) ) [[ level.tod_wf_present_fn ]]( p, m, kind, perk );
}

function dev_log( msg )
{
    if ( !IS_TRUE( level.tod_dev ) && !IS_TRUE( level.tod_diag ) ) return;
    line = "[TOD_WUNDERFIZZ] ms=" + GetTime() + " " + msg;
    /#
    PrintLn( line );
    #/
}
