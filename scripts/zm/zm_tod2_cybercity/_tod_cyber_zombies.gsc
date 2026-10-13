// Cyber appearance is owned by the character asset, including every gib model.
// Select its factory in every mode, before stock spawn initialization.
#using scripts\shared\callbacks_shared;
#using scripts\shared\ai\systems\gib;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\ai\systems\gib.gsh;
#insert scripts\zm\zm_tod2_cybercity\_tod_eye_glow.gsh;   // the eye-glow effect names (PK04): the START line reports them

#precache( "xmodel", "c_zom_der_zombie_head1" );

#namespace tod_cyber_zombies;

function install_spawn_filter()
{
	// _zm_spawner::init consumes this during zm_usermap::main, before it
	// registers spawn functions. Both factories retain native character/gibs.
	level.ignore_spawner_func = &ignore_spawner;
}

function ignore_spawner( spawner )
{
	if ( !isdefined( spawner.script_string ) )
		return false;
	if ( spawner.script_string == "tod_cyber_dev" )
		return false; // Historical map marker; appearance is now enabled in all modes.
	if ( spawner.script_string == "tod_cyber_stock" )
		return true;
	return false;
}

function init()
{
	if ( !IS_TRUE( level.tod_dev ) )
		return;
	level.tod_cyber_dev_seen = 0;
	level.tod_cyber_dev_tracked = 0;
	// eyes=red is the eye MATERIAL; the eye-glow PARTICLES were the stock orange until PK04 (2026-10-04). The client
	// sets them (_tod_eye_glow.csc) and proves it in its own log: [TOD_EYES_C] READY ... overridden=1.
	dev_log( "START rev=8 roster=charcoal palette=gray_black_red eyes=red eye_fx=" + TOD_EYE_FX_HORDE + " golden_eye_fx=" + TOD_EYE_FX_GOLDEN
		+ " orange=0 (client proof: [TOD_EYES_C] READY) dev_only=0 native_character=1 native_gibs=1 factories=" + level.zombie_spawners.size );
	callback::on_ai_spawned( &on_spawned );
}

// Cosmetic roster detection; no gameplay or dismemberment decisions live here.
function is_cyber_body( model )
{
	return model == "tod_charcoal_c_zom_dlc3_zombie_sentinel_body";
}

function on_spawned()
{
	self thread inspect_spawn();
}

function inspect_spawn()
{
	self endon( "death" );
	// Native character assignment runs after on_ai_spawned dispatch.
	wait 0.1;
	if ( !isdefined( self.archetype ) || self.archetype != "zombie" )
		return;
	level.tod_cyber_dev_seen++;
	if ( !is_cyber_body( self.model ) )
	{
		if ( level.tod_cyber_dev_seen <= 8 )
			dev_log( "STOCK ent=" + self GetEntityNumber() + " body=" + value( self.model ) + " hp=" + self.health );
		return;
	}
	if ( level.tod_cyber_dev_tracked >= 24 )
		return;
	level.tod_cyber_dev_tracked++;
	dev_log( "SPAWN ent=" + self GetEntityNumber() + " body=" + self.model
		+ " head=" + value( self.head ) + " hp=" + self.health
		+ " gibdef=" + value( self.gibdef ) + " no_gib=" + value( self.no_gib ) );
	self thread inspect_death();
	previous = "";
	while ( isdefined( self ) )
	{
		state = value( self.model ) + "/" + value( self.gib_state ) + "/" + value( self.head_gibbed );
		if ( state != previous )
		{
			dev_log( "STATE ent=" + self GetEntityNumber() + " body/gib/headgone=" + state );
			previous = state;
		}
		wait 0.25;
	}
}

function inspect_death()
{
	num = self GetEntityNumber();
	self waittill( "death" );
	if ( isdefined( self ) )
		dev_log( "DEATH ent=" + num + " body=" + value( self.model )
			+ " gib=" + value( self.gib_state ) + " headgone=" + value( self.head_gibbed ) );
}

function value( v )
{
	if ( !isdefined( v ) )
		return "unset";
	return "" + v;
}

function dev_log( text )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	msg = "[TOD_CHARCOAL] t=" + GetTime() + " " + text;
	/# PrintLn( msg ); #/
}
