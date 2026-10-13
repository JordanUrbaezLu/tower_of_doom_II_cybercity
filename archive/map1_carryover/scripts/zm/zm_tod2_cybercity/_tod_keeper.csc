// THE KEEPER, client half (docs/186). LOCKSTEP with _tod_keeper.gsc: the two
// actor clientfields below are registered in the same order with the same
// version and bit counts.
//
//  * His look: the pack's keeper script's own three effects (torso glow, mouth
//    glow, mist trail) on his archetype spawn, and the fade-in of his
//    "scriptVector" shader constants - his materials are the _script kind, and
//    with the constants at 0 the cloth/emission layers stay dark.
//  * tod_keeper_death (actor, 2): 2 = the dissolve body fades out (the pack's
//    callback). On shutdown the death burst plays where his chest was.
//  * tod_keeper_link (actor, 1, set on the LINKED ELITE): THE SOUL LINE. While
//    it is 1 every client streams soul wisps from the Keeper's chest into the
//    elite (one per TOD_KEEPER_LINE_GAP, the Necromancer's soul-stream recipe:
//    client tag_origin hosts homing on a moving target, nothing networked but
//    the one field) and wraps the elite in the Keeper's own torso glow.

#using scripts\codescripts\struct;
#using scripts\shared\ai_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#precache( "client_fx", "zombie/fx_keeper_ambient_torso_zod_zmb" );
#precache( "client_fx", "zombie/fx_keeper_glow_mouth_zod_zmb" );
#precache( "client_fx", "zombie/fx_keeper_mist_trail_zod_zmb" );
#precache( "client_fx", "zombie/fx_keeper_death_zod_zmb" );
#precache( "client_fx", "tod/necro/fx_necro_soul_wisp" );

#namespace tod_keeper;

#define TOD_KEEPER_LINE_GAP     0.08    // one wisp per this, per line (dense enough to read as a line)
#define TOD_KEEPER_LINE_FLIGHT  0.45    // a wisp's flight time (s)
#define TOD_KEEPER_LINE_STEPS   6       // homing steps in that flight
#define TOD_KEEPER_FADE_IN      1.0     // his materials fade up over this (the pack's value)

REGISTER_SYSTEM( "tod_keeper", &__init__, undefined )

function __init__()
{
	level._effect[ "tod_keeper_glow" ]  = "zombie/fx_keeper_ambient_torso_zod_zmb";
	level._effect[ "tod_keeper_mouth" ] = "zombie/fx_keeper_glow_mouth_zod_zmb";
	level._effect[ "tod_keeper_trail" ] = "zombie/fx_keeper_mist_trail_zod_zmb";
	level._effect[ "tod_keeper_death" ] = "zombie/fx_keeper_death_zod_zmb";
	level._effect[ "tod_keeper_wisp" ]  = "tod/necro/fx_necro_soul_wisp";
	level.tod_keeper_c = [];
	ai::add_archetype_spawn_function( "keeper", &keeper_spawned );
	clientfield::register( "actor", "tod_keeper_death", VERSION_SHIP, 2, "int", &keeper_death_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "actor", "tod_keeper_link", VERSION_SHIP, 1, "int", &keeper_link_cb, !CF_HOST_ONLY, CF_CALLBACK_ZERO_ON_NEW_ENT );
}

// a tag if the model has it, else a point off the origin (memory
// playfxontag-missing-bone-crashes: never PlayFXOnTag a bone we have not seen)
function tag_or( tag )
{
	if ( isdefined( self GetTagOrigin( tag ) ) )
		return tag;
	return undefined;
}

function point( tag, up )
{
	v = self GetTagOrigin( tag );
	if ( isdefined( v ) )
		return v;
	return self.origin + ( 0, 0, up );
}

function fx_on( lc, key, tag )
{
	if ( isdefined( self tag_or( tag ) ) )
		return PlayFXOnTag( lc, level._effect[ key ], self, tag );
	return undefined;
}

// ---- the Keeper ------------------------------------------------------------
function keeper_spawned( lc )
{
	self endon( "entityshutdown" );
	self util::waittill_dobj( lc );
	if ( !isdefined( self ) )
		return;
	level.tod_keeper_c[ lc ] = self;
	self.tod_keeper_fx = [];
	self.tod_keeper_fx[ self.tod_keeper_fx.size ] = self fx_on( lc, "tod_keeper_glow", "j_spineupper" );
	self.tod_keeper_fx[ self.tod_keeper_fx.size ] = self fx_on( lc, "tod_keeper_mouth", "j_head" );
	self.tod_keeper_fx[ self.tod_keeper_fx.size ] = self fx_on( lc, "tod_keeper_trail", "j_robe_front_03" );
	self callback::on_shutdown( &keeper_shutdown );
	// the fade-in of his _script materials (the pack: 0 -> 1 over a second)
	t = 0;
	while ( isdefined( self ) && t < TOD_KEEPER_FADE_IN )
	{
		wait 0.05;
		t += 0.05;
		k = t / TOD_KEEPER_FADE_IN;
		if ( k > 1 ) k = 1;
		self MapShaderConstant( lc, 0, "scriptVector2", k );
		self MapShaderConstant( lc, 0, "scriptVector0", k );
	}
}

function keeper_shutdown( lc )
{
	if ( isdefined( self.tod_keeper_fx ) )
		foreach ( fx in self.tod_keeper_fx )
			if ( isdefined( fx ) )
				StopFX( lc, fx );
	self.tod_keeper_fx = undefined;
	v = self GetTagOrigin( "j_spineupper" );
	if ( isdefined( v ) )
		PlayFX( lc, level._effect[ "tod_keeper_death" ], v, ( 0, 0, 0 ) );
	if ( isdefined( level.tod_keeper_c[ lc ] ) && level.tod_keeper_c[ lc ] == self )
		level.tod_keeper_c[ lc ] = undefined;
}

// 2 = the dissolve body fades out (the pack's callback, value 2)
function keeper_death_cb( lc, oldval, newval, bnewent, binitialsnap, fieldname, bwastimejump )
{
	self endon( "entityshutdown" );
	if ( newval != 2 )
		return;
	self util::waittill_dobj( lc );
	t = 0;
	while ( isdefined( self ) && t < 0.3 )
	{
		wait 0.05;
		t += 0.05;
		self MapShaderConstant( lc, 0, "scriptVector0", 1 - ( t / 0.3 ) );
	}
	if ( isdefined( self ) )
		self MapShaderConstant( lc, 0, "scriptVector0", 0 );
}

// ---- the soul line (self = the linked elite) -------------------------------
function keeper_link_cb( lc, oldval, newval, bnewent, binitialsnap, fieldname, bwastimejump )
{
	self notify( "tod_keeper_line" );
	if ( isdefined( self.tod_keeper_line_fx ) )
	{
		KillFX( lc, self.tod_keeper_line_fx );
		self.tod_keeper_line_fx = undefined;
	}
	if ( newval != 1 )
		return;
	self thread line_stream( lc );
}

function line_stream( lc )
{
	self notify( "tod_keeper_line" );
	self endon( "tod_keeper_line" );
	self endon( "entityshutdown" );
	self util::waittill_dobj( lc );
	if ( !isdefined( self ) )
		return;
	self.tod_keeper_line_fx = self fx_on( lc, "tod_keeper_glow", "j_spine4" );
	if ( !IS_TRUE( self.tod_keeper_line_cb ) )
	{
		self.tod_keeper_line_cb = true;   // one shutdown hook per elite, however many times it is linked
		self callback::on_shutdown( &line_shutdown );
	}
	while ( isdefined( self ) )
	{
		keeper = level.tod_keeper_c[ lc ];
		if ( isdefined( keeper ) )
			level thread line_wisp( lc, keeper, self );
		wait TOD_KEEPER_LINE_GAP;
	}
}

function line_shutdown( lc )
{
	if ( isdefined( self.tod_keeper_line_fx ) )
		KillFX( lc, self.tod_keeper_line_fx );
	self.tod_keeper_line_fx = undefined;
}

// one wisp: a client tag_origin carrying the soul trail from the Keeper's
// chest into the elite's, re-aimed each step (both move), gone on arrival
function line_wisp( lc, keeper, elite )
{
	from = keeper point( "j_spineupper", 56 );
	host = util::spawn_model( lc, "tag_origin", from, ( 0, 0, 0 ) );
	if ( !isdefined( host ) )
		return;
	fx = PlayFXOnTag( lc, level._effect[ "tod_keeper_wisp" ], host, "tag_origin" );
	step = TOD_KEEPER_LINE_FLIGHT / TOD_KEEPER_LINE_STEPS;
	for ( i = 1; i <= TOD_KEEPER_LINE_STEPS; i++ )
	{
		if ( !isdefined( host ) || !isdefined( keeper ) || !isdefined( elite ) )
			break;
		from = keeper point( "j_spineupper", 56 );
		to = elite point( "j_spine4", 48 );
		host MoveTo( from + ( to - from ) * ( i / TOD_KEEPER_LINE_STEPS ), step );
		wait step;
	}
	if ( isdefined( fx ) )
		KillFX( lc, fx );
	if ( isdefined( host ) )
		host Delete();
}
