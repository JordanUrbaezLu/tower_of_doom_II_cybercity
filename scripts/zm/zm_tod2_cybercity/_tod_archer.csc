// Replicated hook host -> one native cable per local client, including co-op.
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#namespace tod_archer;
REGISTER_SYSTEM( "tod_archer_art", &__init__, undefined )
function __init__()
{
	clientfield::register( "scriptmover", "todArcherHook", VERSION_SHIP, 5, "int", &hook_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
}
function hook_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	self notify( "archer_hook_stop_" + localClientNum );
	if ( isdefined( self.archer_beams ) && isdefined( self.archer_beams[ localClientNum ] ) )
	{
		BeamKill( localClientNum, self.archer_beams[ localClientNum ] );
		self.archer_beams[ localClientNum ] = undefined;
	}
	if ( isdefined( newVal ) && newVal % 16 > 0 ) self thread hook_start( localClientNum, newVal );
}
function hook_start( localClientNum, value )
{
	self endon( "entityshutdown" );
	self endon( "archer_hook_stop_" + localClientNum );
	owner_id = ( value % 16 ) - 1;
	// A script mover's field can arrive before either entity's drawable model.
	for ( attempts = 0; attempts < 30; attempts++ )
	{
		wait 0.05;
		owner = GetEntByNum( localClientNum, owner_id );
		if ( isdefined( owner ) && self HasDObj( localClientNum ) && owner HasDObj( localClientNum ) ) break;
	}
	if ( !isdefined( owner ) || !self HasDObj( localClientNum ) || !owner HasDObj( localClientNum ) )
	{
		art_log( value >= 16, "CABLE_FAIL client=" + localClientNum + " owner=" + owner_id + " reason=model_timeout" );
		return;
	}
	beam = BeamLaunch( localClientNum, owner, "j_wrist_le", self, "tag_origin", "tod_archer_cable" );
	DEFAULT( self.archer_beams, [] );
	self.archer_beams[ localClientNum ] = beam;
	if ( isdefined( beam ) ) self thread hook_shutdown( localClientNum, beam, value >= 16 );
	art_log( value >= 16, "CABLE_ATTACH client=" + localClientNum + " owner=" + owner_id + " hook=" + self GetEntityNumber() + " valid=" + isdefined( beam ) );
}
function hook_shutdown( localClientNum, beam, debug )
{
	self endon( "archer_hook_stop_" + localClientNum );
	self waittill( "entityshutdown" );
	BeamKill( localClientNum, beam );
	art_log( debug, "CABLE_END client=" + localClientNum + " handle=" + beam );
}
function art_log( enabled, msg )
{
	if ( !enabled ) return;
	line = "[TOD_ARCHER_C] " + msg;
	/#
	PrintLn( line );
	#/
}
