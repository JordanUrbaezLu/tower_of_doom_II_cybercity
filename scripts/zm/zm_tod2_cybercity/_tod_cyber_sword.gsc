// Presentation only. The class kit supplies its existing HUD readiness result.
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#namespace tod_cyber_sword;
REGISTER_SYSTEM( "tod_cyber_sword", &__init__, undefined )

function __init__()
{
	clientfield::register( "toplayer", "todCyberSwordReady", VERSION_SHIP, 1, "int" );
	callback::on_spawned( &on_spawned );
}

function on_spawned()
{
	self.tod_cyber_sword_ready = undefined;
	self update( false, "spawn" );
}

function update( ready, reason )
{
	value = ( ready && IsAlive( self ) ? 1 : 0 );
	if ( isdefined( self.tod_cyber_sword_ready ) && self.tod_cyber_sword_ready == value ) return;
	self.tod_cyber_sword_ready = value;
	self clientfield::set_to_player( "todCyberSwordReady", value );
	if ( !IS_TRUE( level.tod_dev ) ) return;
	line = "[TOD_CYBER_SWORD] ms=" + GetTime() + " player=" + self GetEntityNumber() + " ready=" + value + " reason=" + reason;
	/#
	PrintLn( line );
	#/
}
