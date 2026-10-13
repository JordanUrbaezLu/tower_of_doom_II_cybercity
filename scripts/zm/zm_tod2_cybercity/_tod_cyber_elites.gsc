// The normal-round elite mix. One owner, bounded per-round budget, no death debt.
#using scripts\shared\flag_shared;
#using scripts\zm\zm_tod2_cybercity\_tod_bosses;
#using scripts\zm\zm_tod2_cybercity\_tod_doppelghast;
#using scripts\zm\zm_tod2_cybercity\_tod_mangler;
#insert scripts\shared\shared.gsh;
#namespace tod_cyber_elites;

function init()
{
    if ( IS_TRUE( level.tod_cyber_elites_started ) ) return;
    level.tod_cyber_elites_started = true;
    tod_mangler::init();
    level thread director();
}

function dev_log( message )
{
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
    line = "[TOD_ELITES] ms=" + GetTime() + " " + message;
    /# PrintLn( line ); #/
}

// First introductions on rounds 3 and 5. Thereafter 1/round, 2 at 14, 3 at 22.
function round_budget( round )
{
    if ( round < 3 || round == 4 ) return 0;
    if ( round < 14 ) return 1;
    if ( round < 22 ) return 2;
    return 3;
}

function hold_reason()
{
    if ( IS_TRUE( level.tod_upgrade_pause ) ) return "upgrade_pause";
    if ( level flag::exists( "world_is_paused" ) && level flag::get( "world_is_paused" ) ) return "world_pause";
    if ( !( level flag::exists( "spawn_zombies" ) ) || !( level flag::get( "spawn_zombies" ) ) ) return "spawns_held";
    if ( isdefined( level.tod_trial_box ) ) return "arena";   // the Battle Arena fight owns the elites (_tod_arena sets the box)
    if ( GetFreeActorCount() < 3 ) return "actor_reserve";
    if ( tod_bosses::elites_over_roof() ) return "shared_elite_roof";
    if ( tod_doppelghast::alive_count() + tod_mangler::live_manglers().size >= 2 ) return "mix_cap";
    return "";
}

function director()
{
    level endon( "end_game" );
    level flag::wait_till( "initial_blackscreen_passed" );
    dev_log( "INIT rev=1 doppel_round=3 mangler_round=5 budget=1,2_at_14,3_at_22 live_cap=2 gap=25 actor_reserve=2" );
    seen_round = -1;
    left = 0;
    clock = 0;
    sequence = 0;
    previous_reason = "";
    while ( 1 )
    {
        wait 0.5;
        if ( !isdefined( level.round_number ) ) continue;
        round = level.round_number;
        if ( seen_round != round )
        {
            dev_log( "ROUND round=" + round + " expired_budget=" + left + " budget=" + round_budget( round ) );
            seen_round = round;
            left = round_budget( round );
            clock = 0;
            previous_reason = "";
        }
        if ( left <= 0 ) continue;
        reason = hold_reason();
        if ( reason != "" )
        {
            if ( reason != previous_reason ) dev_log( "HOLD round=" + round + " reason=" + reason + " left=" + left );
            previous_reason = reason;
            continue;
        }
        clock += 0.5;
        if ( clock < 25 ) continue;
        target = tod_doppelghast::target_player();
        if ( !isdefined( target ) ) reason = "no_target";
        else
        {
            org = tod_doppelghast::reloc_point( target );
            if ( !isdefined( org ) ) reason = "no_clear_position";
        }
        if ( reason != "" )
        {
            if ( reason != previous_reason ) dev_log( "HOLD round=" + round + " reason=" + reason );
            previous_reason = reason;
            continue;
        }
        kind = "doppelgast";
        if ( round == 5 || ( round > 5 && sequence % 2 == 1 ) ) kind = "mangler";
        if ( kind == "mangler" )
        {
            facing = VectorToAngles( target.origin - org );
            actor = tod_mangler::spawn_at( org, target, ( 0, facing[1], 0 ) );
        }
        else actor = tod_doppelghast::spawn_hunter( org, target, 5 );
        if ( !isdefined( actor ) )
        {
            dev_log( "DENIED round=" + round + " kind=" + kind + " reason=spawnactor" );
            clock = 20;
            continue;
        }
        left--;
        sequence++;
        clock = 0;
        previous_reason = "";
        dev_log( "SPAWN round=" + round + " kind=" + kind + " entity=" + actor GetEntityNumber() + " target=" + target GetEntityNumber() + " hp=" + actor.health + " origin=" + org + " left=" + left );
    }
}
