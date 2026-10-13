// Same shader channel used by stock Tesla/Thundergun and the donor sword.
// Only our held view material reads it. The slam has a separate always-lit skin.
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#define TOD_SWORD_C_LOG 1   // 1 = log the end-of-match cleanup ([TOD_SWORD_C]); 0 before a publish
#namespace tod_cyber_sword;
REGISTER_SYSTEM( "tod_cyber_sword", &__init__, undefined )

function __init__()
{
	clientfield::register( "toplayer", "todCyberSwordReady", VERSION_SHIP, 1, "int", &ready_cb, !CF_HOST_ONLY, CF_CALLBACK_ZERO_ON_NEW_ENT );
	callback::on_spawned( &on_spawned );
}

function ready_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( self != GetLocalPlayer( localClientNum ) ) return;
	self.tod_cyber_sword_ready = newVal;
}

function is_sword( weapon )
{
	return isdefined( weapon ) && isdefined( weapon.name ) &&
		( IsSubStr( weapon.name, "cc_gold_sword" ) || IsSubStr( weapon.name, "tod_cyber_sword_bash" ) || IsSubStr( weapon.name, "tod_bash_sword" ) );
}

function on_spawned( localClientNum )
{
	if ( self != GetLocalPlayer( localClientNum ) ) return;
	self notify( "tod_cyber_sword_restart" );
	self thread glow_watch( localClientNum );
	self thread cleanup( localClientNum );
}

function glow_watch( localClientNum )
{
	self endon( "tod_cyber_sword_restart" );
	self endon( "tod_cyber_sword_stop" );
	self endon( "death" );
	self endon( "disconnect" );
	self endon( "entityshutdown" );
	last_weapon = undefined;
	brightness = 0;
	for ( ;; )
	{
		weapon = GetCurrentWeapon( localClientNum );
		if ( is_sword( weapon ) )
		{
			if ( !isdefined( last_weapon ) || last_weapon != weapon ) brightness = 0;
			target = ( IS_TRUE( self.tod_cyber_sword_ready ) ? 1 : 0 );
			// 300 ms rise; immediate dark when spent. No independent charge timer.
			if ( target == 0 ) brightness = 0;
			else brightness = Min( 1, brightness + 0.166667 );
			self MapShaderConstant( localClientNum, 0, "scriptVector2", 0, brightness, 0, 0 );
			last_weapon = weapon;
		}
		else
		{
			// No writes on another weapon: its own shader initialization owns it.
			last_weapon = undefined;
			brightness = 0;
		}
		wait 0.05;
	}
}

function cleanup( localClientNum )
{
	self endon( "tod_cyber_sword_restart" );
	self util::waittill_any( "death", "disconnect", "entityshutdown" );
	self notify( "tod_cyber_sword_stop" );
	// THE GAME OVER (LT-fix 2026-10-05): stock _zm.gsc player_intermission switches every player to "intermission"
	// ~6.15 s after end_game (wait 5 + a 1 s fade), and by the time this thread resumes from the "death" it waited on
	// (util waittill_any waits on its FIRST notify; the other two only end it) the local player's client entity is
	// already removed: the field write below threw "cannot set field of removed entity" once per game over, for every
	// class (the 17:33 run at log ms 692966 and 878913; the 2026-10-04 22:33 run too). glow_watch ends on its own
	// endons, so a removed entity has nothing left to clear.
	if ( !isdefined( self ) )
	{
		c_log( "CLEANUP client=" + localClientNum + " removed=1 (the player entity left before its death notify; nothing to clear)" );
		return;
	}
	self.tod_cyber_sword_ready = 0;
}

// [TOD_SWORD_C] client log (LT-fix 2026-10-05). TEMPORARY like the other TOD_*_LOG switches: 0 before a publish.
function c_log( msg )
{
	if ( !TOD_SWORD_C_LOG ) return;
	line = "[TOD_SWORD_C] " + msg;
	/#
	PrintLn( line );
	#/
}
