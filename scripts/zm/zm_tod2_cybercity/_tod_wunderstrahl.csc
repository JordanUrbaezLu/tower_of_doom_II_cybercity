// =============================================================================
// _tod_wunderstrahl.csc - THE WUNDERSTRAHL, client half (docs/219, 2026-10-05).
// Stock contract (_tod_powerups.csc header): the client must include + add the power-up
// ITSELF, with the SAME clientfield name as the server's add_zombie_powerup ("tod_wunderstrahl",
// VERSION_SHIP, 2-bit "toplayer"), or the registration mismatches at load. The add enrolls the
// field in stock's code-callback pass, which is what the Aetherium tray row
// (AetheriumPowerupsContainer.lua, clientFieldName "tod_wunderstrahl") reads.
// The beam and its effects are the ENGINE's (the gas weapon's flameBeamFirstPerson / ThirdPerson),
// so nothing else runs here.
// =============================================================================

#using scripts\shared\system_shared;
#using scripts\zm\_zm_powerups;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#namespace tod_wunderstrahl;

REGISTER_SYSTEM( "tod_wunderstrahl", &__init__, undefined )

function __init__()
{
	zm_powerups::include_zombie_powerup( "tod_wunderstrahl" );
	zm_powerups::add_zombie_powerup( "tod_wunderstrahl", "tod_wunderstrahl" );
}
