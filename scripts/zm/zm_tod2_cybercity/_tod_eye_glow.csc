// =============================================================================
// _tod_eye_glow.csc - THE HORDE'S EYES (PK04, 2026-10-04). Client only, no clientfields of its own.
//
// THE GAP. Every ordinary zombie runs stock zombie_spawn_init, which sets the actor clientfield
// "zombie_has_eyes" 0.5 s after the spawn (a riser: once it shows). The client's callback
// (_zm.csc zombie_eyes_clientfield_cb -> createZombieEyesInternal) then plays
// level._effect[ "eye_glow" ] on the bone j_eyeball_le, and zm_usermap.csc:72 sets that to
// "zombie/fx_glow_eye_orange". Nothing in the map overrode it, so ORANGE particles floated over
// the charcoal horde's pure-red HDR-16 eyes on every zombie (docs/cyber_elites/README.md: "red
// eyes and no orange"), and over the golden zombie's gold eyes too.
//
// THE FIX, the two stock hooks createZombieEyesInternal already reads:
//   level._override_eye_fx = TOD_EYE_FX_HORDE      every zombie that lights stock eyes: the horde,
//                                                  the armored sprinters, a thrall let go mid-bind
//   self._eyeglow_fx_override = TOD_EYE_FX_GOLDEN  per actor, the golden zombie only
// Hellhounds set their own override (zm_ai_dogs.csc) and the Necromancer's helpers put the
// stock eyes out at the bind and wear their own white ones (_tod_necro_skull.csc), so neither
// changes. Both effects are GENERATED (tools/fxgen/horde_eyes/make_fx.py): the stock orange's
// shape - a hot core, a faint halo and the forward light cones, made for these very heads - in
// pure red (hue 0 in every key) / in the golden eye's own gold.
//
// THE GOLDEN ZOMBIE is chosen in the stock "additional" eye callback (level.zombie_eyes_clientfield_cb_additional,
// chained - a previous owner still runs first): the server swaps its body to the gold twin 0.1 s after the spawn
// (_tod_golden_zombie.gsc golden_look), long before its eyes light, so by then the client sees the gold model. If the
// stock lane had already lit the red this frame, it is put out with DeleteFx( ..., true ) and re-lit gold in the same
// client frame: nobody sees red eyes on a golden zombie.
//
// Dev logs: [TOD_EYES_C] READY / EYES (the first TOD_EYES_C_LOG_FIRST lit) / GOLDEN (every one). Devblock only: a dev
// launch (developer 1 + scr_mod_enable_devblock 1, the user's own PLAY_NORMAL.bat) prints them, a release never.
// =============================================================================

#using scripts\zm\_zm;   // createZombieEyes / deleteZombieEyes: the stock eye lane this module steers

#insert scripts\shared\shared.gsh;
#insert scripts\zm\zm_tod2_cybercity\_tod_eye_glow.gsh;

#precache( "client_fx", TOD_EYE_FX_HORDE );
#precache( "client_fx", TOD_EYE_FX_GOLDEN );

#namespace tod_eye_glow;

#define TOD_EYES_C_LOG          1     // [TOD_EYES_C] lines (devblock-gated PrintLn)
#define TOD_EYES_C_LOG_FIRST    6     // the first N horde eyes lit are logged; every golden swap is

// Called from zm_tod2_cybercity.csc main(), right after zm_usermap::main() set the stock orange. Before any actor:
// createZombieEyesInternal reads the override at the moment it lights an eye.
function init()
{
	level._effect[ "tod_eye_horde" ] = TOD_EYE_FX_HORDE;
	level._effect[ "tod_eye_golden" ] = TOD_EYE_FX_GOLDEN;
	level._override_eye_fx = TOD_EYE_FX_HORDE;
	level.tod_eye_prev_cb = level.zombie_eyes_clientfield_cb_additional;
	level.zombie_eyes_clientfield_cb_additional = &eyes_cb;
	level.tod_eye_logged = 0;
	stock = "unset";
	if ( isdefined( level._effect[ "eye_glow" ] ) )
		stock = level._effect[ "eye_glow" ];
	c_log( "READY rev=1 horde=" + TOD_EYE_FX_HORDE + " golden=" + TOD_EYE_FX_GOLDEN + " golden_body=" + TOD_EYE_GOLDEN_BODY
		+ " stock=" + stock + " overridden=1 chained=" + isdefined( level.tod_eye_prev_cb ) );
}

// PURE (tools/fxgen/horde_eyes/test_eye_glow.js runs it through gsc_eval): the per-actor eye effect for a body model,
// or undefined = the level's own (TOD_EYE_FX_HORDE). Only the golden zombie differs.
function eye_fx_for_model( model )
{
	if ( !isdefined( model ) )
		return undefined;
	if ( model == TOD_EYE_GOLDEN_BODY )
		return TOD_EYE_FX_GOLDEN;
	return undefined;
}

// self = an actor. The stock "zombie_has_eyes" callback calls this AFTER it has lit (newVal 1) or put out (newVal 0)
// the eyes; every argument is passed straight through to the previous owner of the hook, if there was one.
function eyes_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( isdefined( level.tod_eye_prev_cb ) )
		self [[ level.tod_eye_prev_cb ]]( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump );
	if ( !isdefined( self ) || !isdefined( newVal ) || !newVal )
		return;
	fx = eye_fx_for_model( self.model );
	if ( !isdefined( fx ) )
	{
		if ( level.tod_eye_logged < TOD_EYES_C_LOG_FIRST )
		{
			level.tod_eye_logged++;
			c_log( "EYES ent=" + self GetEntityNumber() + " lc=" + localClientNum + " model=" + value( self.model )
				+ " fx=" + TOD_EYE_FX_HORDE + " n=" + level.tod_eye_logged + "/" + TOD_EYES_C_LOG_FIRST );
		}
		return;
	}
	if ( isdefined( self._eyeglow_fx_override ) && self._eyeglow_fx_override == fx )
		return;   // already gold: a second local client, or eyes lit again after a stop
	self._eyeglow_fx_override = fx;
	relit = 0;
	if ( isdefined( self._eyeArray ) && isdefined( self._eyeArray[ localClientNum ] ) )
	{
		self zm::deleteZombieEyes( localClientNum );   // the red lit a moment ago in this same callback (killed at once)
		self zm::createZombieEyes( localClientNum );   // re-lit: createZombieEyesInternal now reads the gold override
		relit = 1;
	}
	c_log( "GOLDEN ent=" + self GetEntityNumber() + " lc=" + localClientNum + " fx=" + fx + " relit=" + relit
		+ " (0 = the eye was still waiting for its model and lights gold first time)" );
}

function value( v )
{
	if ( !isdefined( v ) )
		return "unset";
	return "" + v;
}

function c_log( msg )
{
	if ( !TOD_EYES_C_LOG ) return;
	line = "[TOD_EYES_C] ms=" + GetRealTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
