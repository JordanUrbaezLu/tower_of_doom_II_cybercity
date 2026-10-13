// =============================================================================
// _tod_lucky.csc — client half of THE LUCKY CLOVER (docs/197; server: _tod_lucky.gsc).
// Stock contract (_tod_powerups.csc's header): register_powerup auto-includes the name on
// the SERVER only, so the client must include_zombie_powerup + add_zombie_powerup itself, or
// it never learns the power-up exists and the drop renders wrong. Instant, no HUD timer, so
// no clientfield to keep in lockstep — only the name (TOD_CLOVER_NAME in the .gsc).
// The meteor and the fragment are server script_models with server effects: nothing here.
// =============================================================================

#using scripts\shared\system_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#using scripts\zm\_zm_powerups;

#namespace tod_lucky;

REGISTER_SYSTEM( "tod_lucky", &__init__, undefined )

function __init__()
{
	zm_powerups::include_zombie_powerup( "tod_luck_clover" );
	zm_powerups::add_zombie_powerup( "tod_luck_clover" );
}
