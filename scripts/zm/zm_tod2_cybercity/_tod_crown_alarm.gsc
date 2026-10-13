// Authored physical beacons. The Fall owns the single activation/shutdown edge.
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_lights;
#using scripts\zm\zm_tod2_cybercity\_tod_power_conduits;
#insert scripts\shared\shared.gsh;
#precache( "model", "tod_crown_alarm_housing" );
#precache( "model", "tod_crown_alarm_rotor_off" );
#precache( "model", "tod_crown_alarm_rotor_on" );
#precache( "model", "tod_crown_alarm_rotor_high_on" );
#precache( "model", "tod_crown_alarm_housing_high" );
#precache( "model", "tod_crown_alarm_rotor_high_off" );
#namespace tod_crown_alarm;

function init()
{
    // Art bootstrap shared with surface details; their power watcher is independent
    // of the alarm trigger and seal, so conduits stay lit after the hall closes.
    tod_power_conduits::init();
    if ( isdefined( level.tod_crown_alarm_rotors ) )
        return;
    level.tod_crown_alarm_active = false;
    level.tod_crown_alarm_rotors = [];
    orgs = tod_crown_data::alarm_mount_orgs();
    angles = tod_crown_data::alarm_mount_angles();
    scales = tod_crown_data::alarm_mount_scales();
    kinds = tod_crown_data::alarm_mount_kinds();
    for ( i = 0; i < orgs.size; i++ )
    {
        housing = Spawn( "script_model", orgs[ i ] );
        housing SetModel( housing_model( kinds[ i ] ) );
        housing.angles = angles[ i ];
        housing SetScale( scales[ i ] );
        // Only the central pendant is inverted. Both models share the axis.
        dz = 26 * scales[ i ];
        if ( is_high( kinds[ i ] ) )
            dz = 48 * scales[ i ]; // doubled upper fixture; original mounting foot
        if ( kinds[ i ] == "pendant" )
            dz = 0 - dz;
        rotor = Spawn( "script_model", orgs[ i ] + ( 0, 0, dz ) );
        rotor SetModel( off_model( kinds[ i ] ) );
        // Choose once on the server: every client sees the same offset, and
        // repeated activation never resets the reflectors into formation.
        mount_angles = angles[ i ];
        rotor.tod_alarm_phase = RandomFloat( 360 );
        rotor.angles = ( mount_angles[ 0 ], mount_angles[ 1 ] + rotor.tod_alarm_phase, mount_angles[ 2 ] );
        rotor SetScale( scales[ i ] );
        rotor.tod_alarm_kind = kinds[ i ];
        rotor.tod_alarm_housing = housing;
        level.tod_crown_alarm_rotors[ i ] = rotor;
        alarm_log( "MOUNT id=" + i + " kind=" + kinds[ i ] + " origin=" + orgs[ i ] + " scale=" + scales[ i ] + " phase_degrees=" + rotor.tod_alarm_phase );
    }
    alarm_log( "READY fixtures=" + orgs.size + " state=off" );
}

function start()
{
    level endon( "end_game" );
    if ( IS_TRUE( level.tod_crown_alarm_active ) || IS_TRUE( level.tod_fall_sealed ) )
        return;
    init();
    level.tod_crown_alarm_active = true;
    rotors = level.tod_crown_alarm_rotors;
    for ( i = 0; i < rotors.size; i++ )
        rotors[ i ] SetModel( on_model( rotors[ i ].tod_alarm_kind ) );
    wait 0.1; // replicate the new dobj before the client resolves tag_origin
    if ( !IS_TRUE( level.tod_crown_alarm_active ) )
        return; // a seal during that snapshot cancels startup
    lights = 0;
    for ( i = 0; i < rotors.size; i++ )
    {
        rotor = rotors[ i ];
        rotor thread spin();
        if ( rotor.tod_alarm_kind == "pillar" || rotor.tod_alarm_kind == "pendant" )
        {
            tod_perk_lights::set_glow( rotor, 11 );
            lights++;
        }
        else if ( is_high( rotor.tod_alarm_kind ) )
            tod_perk_lights::set_glow( rotor, 12 );
    }
    alarm_log( "ON fixtures=" + rotors.size + " local_spots=" + lights + " turn_seconds=1.5 profile=red-sweep-2 reach=900 intensity=1800 lamp=36 high_lamp=576 high_lights=17 high_size=2 high_reach=2400 high_intensity=14400 revision=high_visibility_1 phase=random reason=alarm_trigger" );
}

function is_high( kind )
{
    return kind == "point" || kind == "apex";
}

function housing_model( kind )
{
    if ( is_high( kind ) )
        return "tod_crown_alarm_housing_high";
    return "tod_crown_alarm_housing";
}

function off_model( kind )
{
    if ( is_high( kind ) )
        return "tod_crown_alarm_rotor_high_off";
    return "tod_crown_alarm_rotor_off";
}

function on_model( kind )
{
    if ( kind == "point" || kind == "apex" )
        return "tod_crown_alarm_rotor_high_on";
    return "tod_crown_alarm_rotor_on";
}

function spin()
{
    self endon( "death" );
    self endon( "tod_alarm_stop" );
    level endon( "end_game" );
    while ( IS_TRUE( level.tod_crown_alarm_active ) )
    {
        self RotateYaw( 360, 1.5 );
        self waittill( "rotatedone" );
    }
}

function stop()
{
    if ( !IS_TRUE( level.tod_crown_alarm_active ) )
        return;
    level.tod_crown_alarm_active = false;
    rotors = level.tod_crown_alarm_rotors;
    for ( i = 0; i < rotors.size; i++ )
    {
        rotor = rotors[ i ];
        if ( !isdefined( rotor ) )
        {
            alarm_log( "STOP missing_rotor=" + i );
            continue;
        }
        rotor notify( "tod_alarm_stop" );
        tod_perk_lights::set_glow( rotor, 0 );
        rotor RotateTo( rotor.angles, 0.05 );
        rotor SetModel( off_model( rotor.tod_alarm_kind ) );
    }
    // Fixtures remain mounted, dark and stationary. Level teardown owns deletion.
    alarm_log( "OFF fixtures=" + rotors.size + " reason=crown_seal" );
}

function alarm_log( msg )
{
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
        return;
    line = "[TOD_CROWN_ALARM] ms=" + GetTime() + " " + msg;
    /#
    PrintLn( line );
    #/
}
