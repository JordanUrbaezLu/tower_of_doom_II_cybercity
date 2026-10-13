// Tower-wide recessed wire details. Regional batches conserve server entities.
#using scripts\shared\flag_shared;
#using scripts\zm\zm_tod2_cybercity\_tod_conduit_data;
#insert scripts\shared\shared.gsh;
#precache( "model", "tod_power_conduit_off" );
#precache( "model", "tod_power_conduit_on" );
#namespace tod_power_conduits;

function init()
{
    if ( isdefined( level.tod_conduit_hosts ) )
        return;
    level.tod_conduit_hosts = [];
    orgs = tod_conduit_data::origins();
    angles = tod_conduit_data::angles();
    kinds = tod_conduit_data::kinds();
    models = tod_conduit_data::models();
    counts = tod_conduit_data::counts();
    channels = 0;
    powered = level flag::exists( "power_on" ) && level flag::get( "power_on" );
    for ( i = 0; i < orgs.size; i++ )
    {
        host = Spawn( "script_model", orgs[ i ] );
        if ( !isdefined( host ) )
        {
            conduit_log( "SPAWN_FAILED id=" + i + " kind=" + kinds[ i ] + " origin=" + orgs[ i ] );
            continue;
        }
        host.tod_conduit_model = models[ i ];
        host.tod_conduit_count = counts[ i ];
        host SetModel( model_for_power( host.tod_conduit_model, powered ) );
        host.angles = angles[ i ];
        host NotSolid();
        level.tod_conduit_hosts[ level.tod_conduit_hosts.size ] = host;
        channels += counts[ i ];
    }
    conduit_log( "READY revision=tower_wide_v2 hosts=" + level.tod_conduit_hosts.size + " expected=" + orgs.size + " channels=" + channels + " tower_floors=50 powered=" + powered );
    level thread power_watch();
}

function model_for_power( model, powered )
{
    if ( powered )
        return model + "_on";
    return model + "_off";
}

function power_watch()
{
    level endon( "end_game" );
    level flag::wait_till( "power_on" );
    // Server SetModel replicates the current twin to late joiners too.
    live = 0;
    channels = 0;
    foreach ( host in level.tod_conduit_hosts )
    {
        if ( !isdefined( host ) )
            continue;
        host SetModel( model_for_power( host.tod_conduit_model, true ) );
        live++;
        channels += host.tod_conduit_count;
    }
    conduit_log( "ON hosts=" + live + " channels=" + channels + " reason=power_on" );
}

function conduit_log( msg )
{
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
        return;
    line = "[TOD_CONDUIT] ms=" + GetTime() + " " + msg;
    /#
    PrintLn( line );
    #/
}
