// =============================================================================
// _tod_necro_skull.csc — the Necromancer skull's client FX (2026-09-26).
// LOCKSTEP with _tod_necro_skull.gsc: the three fields below must match it in
// name, type and bits or the map dies with "Clientfield Mismatch".
//   allplayers "tod_necro_fx"   3 bits int: 0 off / 1 beam start / 2 beam loop /
//                                            3 summon channel start / 4 channel loop /
//                                            5 PaP beam start / 6 PaP beam loop (the
//                                            Pack-a-Punched skull: recoloured violet-white
//                                            beam from make_soul_fx.py + the hum layer)
//   allplayers "tod_necro_burn" 1 bit counter: Burned Out burst (+ its fire sound)
//   allplayers "tod_necro_bomb" 1 bit counter: the Soul Bomb blast at the caster
//   actor      "tod_necro_soul" 3 bits int: 0 off / 1 soul torn out / 2 drained by the
//                                            beam / 3 being bound by the summon / 4 burned
//                                            out / 5 thrall / 6 soul hound / 7 Mangler (the
//                                            helper auras: blue-grey soul fx,
//                                            tools/necromancer/make_soul_fx.py)
// THE SOUL STREAM (2026-09-26, user: "you should see kind of some soul aura going from
// their AI body to your player. So you can see who you're damaging"): while an actor
// is in state 2 every client flies a soul wisp (fx_necro_soul_wisp, a stock soul trail
// recoloured) from its chest to the Necromancer beaming nearest it, one per
// TOD_STREAM_GAP; in state 3 (the bind) the wisps fly the other way, from the
// Necromancer channelling the torch INTO the lifted zombie. All client side: tag_origin
// client models homing on the player, no server entity, nothing networked but the one
// actor field. Which Necromancer is found by the player's own "tod_necro_fx" state
// (beam 1/2/5/6, torch 3/4) - nearest within TOD_STREAM_REACH.
// The skull's own effects are stock Zetsubou emitters (dlc2/zmb_weapon), the
// burst is Burned Out's own (zombie/fx_bgb_burned_out_*). First-person beam and
// torch play on the VIEWMODEL for the local shooter only; everyone else sees the
// 3p versions on the world model's tag_flash. Every stop is a KillFX of every
// handle the field started (map 1's port left the side loops running on stop).
// =============================================================================

#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_beam_start_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_beam_loop_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_beam_start_3p_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_beam_loop_3p_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_beam_side_start_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_beam_side_loop_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_torch_start_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_torch_loop_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_torch_side_start_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_torch_side_loop_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_torch_start_3p_island" );
#precache( "client_fx", "dlc2/zmb_weapon/fx_wpn_skull_torch_loop_3p_island" );
#precache( "client_fx", "zombie/fx_tesla_shock_eyes_zmb" );
#precache( "client_fx", "zombie/fx_glow_eye_white" );
#precache( "client_fx", "tod/necro/fx_necro_soul_rip" );
#precache( "client_fx", "tod/necro/fx_necro_thrall_aura" );
#precache( "client_fx", "tod/necro/fx_necro_hound_aura" );
#precache( "client_fx", "tod/necro/fx_necro_mangler_aura" );
#precache( "client_fx", "tod/necro/fx_necro_soul_bomb" );
#precache( "client_fx", "tod/necro/fx_necro_pulse_ring0" );   // the Soul Pulse ground ring, one per radius band (make_soul_fx.py RING_RADII)
#precache( "client_fx", "tod/necro/fx_necro_pulse_ring1" );
#precache( "client_fx", "tod/necro/fx_necro_pulse_ring2" );
#precache( "client_fx", "tod/necro/fx_necro_pulse_ring3" );
#precache( "client_fx", "tod/necro/fx_necro_summon" );
#precache( "client_fx", "tod/necro/fx_necro_soul_wisp" );
#precache( "client_fx", "tod/necro/fx_necro_pap_beam_start" );
#precache( "client_fx", "tod/necro/fx_necro_pap_beam_loop" );
#precache( "client_fx", "tod/necro/fx_necro_pap_beam_start_3p" );
#precache( "client_fx", "tod/necro/fx_necro_pap_beam_loop_3p" );
#precache( "client_fx", "tod/necro/fx_necro_pap_beam_side_start" );
#precache( "client_fx", "tod/necro/fx_necro_pap_beam_side_loop" );
#precache( "client_fx", "zombie/fx_bgb_burned_out_1p_zmb" );
#precache( "client_fx", "zombie/fx_bgb_burned_out_3p_zmb" );
#precache( "client_fx", "zombie/fx_bgb_burned_out_fire_torso_zmb" );

#namespace tod_necro_skull;

#define TOD_STREAM_GAP       0.15     // one wisp per this, per streaming actor
#define TOD_STREAM_REACH     900      // the Necromancer must be this close (beam reach 650 x ~1.4)
#define TOD_STREAM_FLIGHT    0.40     // a wisp's flight time (s)
#define TOD_STREAM_STEPS     8        // homing steps in that flight

REGISTER_SYSTEM( "tod_necro_skull", &__init__, undefined )

function __init__()
{
	level._effect[ "tod_necro_beam_start" ]      = "dlc2/zmb_weapon/fx_wpn_skull_beam_start_island";
	level._effect[ "tod_necro_beam_loop" ]       = "dlc2/zmb_weapon/fx_wpn_skull_beam_loop_island";
	level._effect[ "tod_necro_beam_start_3p" ]   = "dlc2/zmb_weapon/fx_wpn_skull_beam_start_3p_island";
	level._effect[ "tod_necro_beam_loop_3p" ]    = "dlc2/zmb_weapon/fx_wpn_skull_beam_loop_3p_island";
	level._effect[ "tod_necro_beam_side_start" ] = "dlc2/zmb_weapon/fx_wpn_skull_beam_side_start_island";
	level._effect[ "tod_necro_beam_side_loop" ]  = "dlc2/zmb_weapon/fx_wpn_skull_beam_side_loop_island";
	level._effect[ "tod_necro_torch_start" ]      = "dlc2/zmb_weapon/fx_wpn_skull_torch_start_island";
	level._effect[ "tod_necro_torch_loop" ]       = "dlc2/zmb_weapon/fx_wpn_skull_torch_loop_island";
	level._effect[ "tod_necro_torch_side_start" ] = "dlc2/zmb_weapon/fx_wpn_skull_torch_side_start_island";
	level._effect[ "tod_necro_torch_side_loop" ]  = "dlc2/zmb_weapon/fx_wpn_skull_torch_side_loop_island";
	level._effect[ "tod_necro_torch_start_3p" ]   = "dlc2/zmb_weapon/fx_wpn_skull_torch_start_3p_island";
	level._effect[ "tod_necro_torch_loop_3p" ]    = "dlc2/zmb_weapon/fx_wpn_skull_torch_loop_3p_island";
	level._effect[ "tod_necro_drain_eyes" ]  = "zombie/fx_tesla_shock_eyes_zmb";
	level._effect[ "tod_necro_helper_eyes" ] = "zombie/fx_glow_eye_white";
	level._effect[ "tod_necro_soul_rip" ]    = "tod/necro/fx_necro_soul_rip";
	level._effect[ "tod_necro_aura_5" ]      = "tod/necro/fx_necro_thrall_aura";
	level._effect[ "tod_necro_aura_6" ]      = "tod/necro/fx_necro_hound_aura";
	level._effect[ "tod_necro_aura_7" ]      = "tod/necro/fx_necro_mangler_aura";
	level._effect[ "tod_necro_bomb" ]        = "tod/necro/fx_necro_soul_bomb";
	level._effect[ "tod_necro_ring_0" ]      = "tod/necro/fx_necro_pulse_ring0";   // 360
	level._effect[ "tod_necro_ring_1" ]      = "tod/necro/fx_necro_pulse_ring1";   // 440
	level._effect[ "tod_necro_ring_2" ]      = "tod/necro/fx_necro_pulse_ring2";   // 520
	level._effect[ "tod_necro_ring_3" ]      = "tod/necro/fx_necro_pulse_ring3";   // 600
	level._effect[ "tod_necro_summon" ]      = "tod/necro/fx_necro_summon";
	level._effect[ "tod_necro_wisp" ]        = "tod/necro/fx_necro_soul_wisp";
	level._effect[ "tod_necro_pap_beam_start" ]      = "tod/necro/fx_necro_pap_beam_start";
	level._effect[ "tod_necro_pap_beam_loop" ]       = "tod/necro/fx_necro_pap_beam_loop";
	level._effect[ "tod_necro_pap_beam_start_3p" ]   = "tod/necro/fx_necro_pap_beam_start_3p";
	level._effect[ "tod_necro_pap_beam_loop_3p" ]    = "tod/necro/fx_necro_pap_beam_loop_3p";
	level._effect[ "tod_necro_pap_beam_side_start" ] = "tod/necro/fx_necro_pap_beam_side_start";
	level._effect[ "tod_necro_pap_beam_side_loop" ]  = "tod/necro/fx_necro_pap_beam_side_loop";
	level._effect[ "tod_necro_burn_1p" ]     = "zombie/fx_bgb_burned_out_1p_zmb";
	level._effect[ "tod_necro_burn_3p" ]     = "zombie/fx_bgb_burned_out_3p_zmb";
	level._effect[ "tod_necro_burn_torso" ]  = "zombie/fx_bgb_burned_out_fire_torso_zmb";

	clientfield::register( "allplayers", "tod_necro_fx", VERSION_SHIP, 3, "int", &necro_fx_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "allplayers", "tod_necro_burn", VERSION_SHIP, 1, "counter", &necro_burn_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "allplayers", "tod_necro_bomb_band", VERSION_SHIP, 2, "int", undefined, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );   // read by necro_bomb_cb; registered BEFORE the counter (LOCKSTEP gsc) so it is applied first
	clientfield::register( "allplayers", "tod_necro_bomb", VERSION_SHIP, 1, "counter", &necro_bomb_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "actor", "tod_necro_soul", VERSION_SHIP, 3, "int", &necro_soul_cb, !CF_HOST_ONLY, CF_CALLBACK_ZERO_ON_NEW_ENT );
}

// ---- the player's skull ------------------------------------------------------
function fx_stop_all( lc )
{
	if ( isdefined( self.tod_necro_pap_snd ) )
	{
		self StopLoopSound( self.tod_necro_pap_snd );   // the handle PlayLoopSound returned
		self.tod_necro_pap_snd = undefined;
	}
	if ( !isdefined( self.tod_necro_fx ) ) return;
	foreach ( h in self.tod_necro_fx )
		KillFX( lc, h );
	self.tod_necro_fx = undefined;
}

function fx_keep( h )
{
	if ( !isdefined( h ) ) return;
	if ( !isdefined( self.tod_necro_fx ) ) self.tod_necro_fx = [];
	self.tod_necro_fx[ self.tod_necro_fx.size ] = h;
}

function vm_fx( lc, fx, tag, keep )
{
	if ( !isdefined( self GetTagOrigin( tag ) ) ) return;
	h = PlayViewmodelFX( lc, level._effect[ fx ], tag );
	if ( keep ) self fx_keep( h );
}

function necro_fx_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( IsSpectating( lc ) ) return;
	self fx_stop_all( lc );
	if ( newVal <= 0 ) return;
	local = ( self == GetLocalPlayer( lc ) );
	pap = ( newVal >= 5 );
	beam = ( newVal <= 2 || pap );
	loop = ( newVal == 2 || newVal == 4 || newVal == 6 );
	b = ( pap ? "tod_necro_pap_beam" : "tod_necro_beam" );
	if ( pap )
	{
		// the PaP beam's layer: a charge accent, then a low hum under the stock loop
		if ( loop ) self.tod_necro_pap_snd = self PlayLoopSound( "hb_caliburn_idle", 0.2 );
		else self PlaySound( lc, "hb_caliburn_ready" );
	}
	if ( local )
	{
		if ( beam )
		{
			self vm_fx( lc, b + ( loop ? "_loop" : "_start" ), "tag_flash", loop );
			self vm_fx( lc, b + ( loop ? "_side_loop" : "_side_start" ), "tag_fx_left", loop );
			self vm_fx( lc, b + ( loop ? "_side_loop" : "_side_start" ), "tag_fx_right", loop );
		}
		else
		{
			self vm_fx( lc, ( loop ? "tod_necro_torch_loop" : "tod_necro_torch_start" ), "tag_fx_mouth", loop );
			self vm_fx( lc, ( loop ? "tod_necro_torch_side_loop" : "tod_necro_torch_side_start" ), "tag_fx_left", loop );
			self vm_fx( lc, ( loop ? "tod_necro_torch_side_loop" : "tod_necro_torch_side_start" ), "tag_fx_right", loop );
		}
		return;
	}
	if ( beam ) fx = b + ( loop ? "_loop_3p" : "_start_3p" );
	else        fx = ( loop ? "tod_necro_torch_loop_3p" : "tod_necro_torch_start_3p" );
	h = self tag_fx( lc, fx, "tag_flash" );
	if ( loop ) self fx_keep( h );
}

function necro_burn_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( bNewEnt || bInitialSnap ) return;
	if ( self == GetLocalPlayer( lc ) )
		PlayViewmodelFX( lc, level._effect[ "tod_necro_burn_1p" ], "tag_origin" );
	else
		self body_fx( lc, "tod_necro_burn_3p", "j_spine4" );
	self PlaySound( lc, "hb_thermite_ignite" );   // the burst's fire whoosh (hb_thermite.csv)
}

// Soul Pulse: authored hollow white ground wave only. No caster burst, light or
// lens flare. Radius band is set before the counter; victims keep their soul rip.
function necro_bomb_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( bNewEnt || bInitialSnap ) return;
	self thread necro_bomb_play( lc, self.origin );
}

function necro_bomb_play( lc, origin )
{
	// Callbacks can precede the other field's application in the same snapshot.
	// The playtest's first max-radius cast read band 0. Finish that snapshot
	// before sampling its band; retain the actual cast origin during movement.
	wait 0.05;
	if ( !isdefined( self ) ) return;
	// No caster-centred blast: its lights, flare and shock sprites whitened the
	// first-person view. All emphasis belongs to the outward ground wave.
	band = self clientfield::get( "tod_necro_bomb_band" );
	if ( !isdefined( band ) || band < 0 || band > 3 ) band = 0;
	handle = PlayFX( lc, level._effect[ "tod_necro_ring_" + band ], origin + ( 0, 0, 12 ), ( 0, 0, 1 ), ( 1, 0, 0 ) );
	fx_log( "PULSE rev=outgoing_souls_3 ent=" + self GetEntityNumber() + " band=" + band + " org=" + origin + " allocated=" + isdefined( handle ) + " center=0 hdr=64 wisps=24 glyphs=12 life_ms=845" );
}

// ---- the zombie's soul -------------------------------------------------------
function soul_stop( lc )
{
	if ( isdefined( self.tod_necro_eye ) )
	{
		KillFX( lc, self.tod_necro_eye );
		self.tod_necro_eye = undefined;
	}
	if ( isdefined( self.tod_necro_aura ) )
	{
		KillFX( lc, self.tod_necro_aura );
		self.tod_necro_aura = undefined;
	}
}

// the helper's aura tag: a hound's spine, everyone else's upper torso
function aura_tag( state )
{
	if ( state == 6 ) return "j_spine2";       // the hellhound
	if ( state == 7 ) return "j_spineupper";   // the Mangler (BO6 skeleton: no j_spine4)
	return "j_spine4";
}

// NEVER BOLT AN EFFECT TO A BONE THE MODEL DOES NOT HAVE (2026-09-26, the user's
// build-6 crash: "the game crashed on one of the necromancer's summoning ability").
// The dump was an access violation inside the FX system on
// fx_necro_mangler_aura, 50 ms after a Mangler rose from a bound zombie: the aura
// was bolted to "j_spine4", and the Mangler is Hellbound's BO6 model, whose
// skeleton names its spine j_spineupper / j_spinelower (Hellbound guards every
// j_spine4 lookup for exactly that reason). A missing bone does not fail quietly
// in PlayFXOnTag - it crashes the game. So EVERY actor/player effect in this
// file goes through body_fx(): the wanted bone if the model has it, else the
// first of a fallback chain that it does have, else no effect at all.
function body_tag( want )
{
	if ( isdefined( want ) && isdefined( self GetTagOrigin( want ) ) ) return want;
	if ( isdefined( self GetTagOrigin( "j_spine4" ) ) ) return "j_spine4";          // stock zombies, players
	if ( isdefined( self GetTagOrigin( "j_spineupper" ) ) ) return "j_spineupper";  // BO6 skeletons (the Mangler)
	if ( isdefined( self GetTagOrigin( "j_spine2" ) ) ) return "j_spine2";          // the hellhound
	if ( isdefined( self GetTagOrigin( "j_spinelower" ) ) ) return "j_spinelower";
	if ( isdefined( self GetTagOrigin( "tag_origin" ) ) ) return "tag_origin";
	return undefined;   // no model / bones yet: skip, never guess
}

function body_fx( lc, fx, want )
{
	tag = self body_tag( want );
	if ( !isdefined( want ) || tag !== want )
		fx_log( "TAG_FALLBACK ent=" + self GetEntityNumber() + " fx=" + fx + " want=" + ( isdefined( want ) ? want : "-" ) + " got=" + ( isdefined( tag ) ? tag : "none(skipped)" ) );
	if ( !isdefined( tag ) ) return undefined;
	return PlayFXOnTag( lc, level._effect[ fx ], self, tag );
}

// an effect on a tag the actor may not have: skipped, never moved, when the
// bone is missing
function tag_fx( lc, fx, tag )
{
	if ( !isdefined( self GetTagOrigin( tag ) ) ) return undefined;
	return PlayFXOnTag( lc, level._effect[ fx ], self, tag );
}

// WHITE EYES ON EVERY HELPER (user 2026-09-26: "the Hound, the Mangler, and the
// Zombie all need to have white eyes"): the white glow on the first eye bone the
// model has - j_eyeball_le (zombies AND the hellhound: stock createZombieEyes
// links a dog's eyes there too), tag_eye (the BO6 Mangler, where its red eye
// light used to ride - the helper no longer gets that one), then j_head. A model
// with none of them gets no glow (never a guessed bone - the build-6 lesson). The
// thrall's baked-red eye material is swapped server-side (thrall_head).
function helper_eyes( lc, state )
{
	tags = array( "j_eyeball_le", "tag_eye", "j_head" );
	foreach ( t in tags )
	{
		if ( !isdefined( self GetTagOrigin( t ) ) ) continue;
		fx_log( "EYES ent=" + self GetEntityNumber() + " state=" + state + " tag=" + t );
		return PlayFXOnTag( lc, level._effect[ "tod_necro_helper_eyes" ], self, t );
	}
	fx_log( "EYES ent=" + self GetEntityNumber() + " state=" + state + " tag=none(skipped)" );
	return undefined;
}

function fx_log( msg )
{
	line = "[TOD_NECRO_C] " + msg;
	/#
	PrintLn( line );
	#/
}

function necro_soul_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	self soul_stop( lc );
	self.tod_necro_state = newVal;   // the soul stream reads this to know when to stop
	if ( newVal == 1 )
	{
		// a soul torn out: the beam's last bite, hound bites, Soul Bomb victims, a helper leaving
		self body_fx( lc, "tod_necro_soul_rip", "j_spine4" );
		self PlaySound( lc, "evt_zombie_skull_breathe" );
	}
	else if ( newVal >= 5 )
	{
		// a helper arriving: the summon burst where it stands, then its aura
		if ( oldVal < 5 )
			PlayFX( lc, level._effect[ "tod_necro_summon" ], self.origin );
		self.tod_necro_aura = self body_fx( lc, "tod_necro_aura_" + newVal, aura_tag( newVal ) );
		self.tod_necro_eye = self helper_eyes( lc, newVal );   // EVERY helper has white eyes (user 2026-09-26)
		if ( newVal == 7 ) fx_log( "MANGLER_AURA rev=wisps_no_flames_1 ent=" + self GetEntityNumber() );
	}
	else if ( newVal == 2 )
	{
		// drained: shock eyes + the soul stream out of it to the beam
		self.tod_necro_eye = self tag_fx( lc, "tod_necro_drain_eyes", "j_eyeball_le" );
		self thread soul_stream( lc, false );
	}
	else if ( newVal == 3 )
	{
		// bound: the lift (the scene is the server's), a soul body forming, souls flowing in
		self.tod_necro_eye = self tag_fx( lc, "tod_necro_drain_eyes", "j_eyeball_le" );
		self.tod_necro_aura = self body_fx( lc, "tod_necro_aura_5", "j_spine4" );
		self thread soul_stream( lc, true );
	}
	else if ( newVal == 4 )
		self body_fx( lc, "tod_necro_burn_torso", "j_spine4" );
}

// ---- the soul stream -------------------------------------------------------------
// the chest a wisp leaves from / flies into
function soul_point()
{
	p = self GetTagOrigin( "j_spine4" );
	if ( !isdefined( p ) ) p = self.origin + ( 0, 0, 40 );
	return p;
}

// the skull a wisp flies into / out of: a little in front of the Necromancer's chest,
// where the skull is held (first person: just under the view)
function skull_point()
{
	// Staff heads sit beyond the old handheld-skull chest point. Prefer the
	// native weapon tag so wisps follow the held world model and casting pose.
	p = self GetTagOrigin( "tag_fx_mouth" );
	if ( isdefined( p ) ) return p;
	f = AnglesToForward( ( 0, self.angles[ 1 ], 0 ) );
	return self.origin + ( 0, 0, 46 ) + f * 22;
}

// the nearest Necromancer beaming (drain) or holding the torch (bind)
function stream_partner( lc, inward )
{
	best = undefined;
	bd = TOD_STREAM_REACH * TOD_STREAM_REACH;
	foreach ( p in GetPlayers( lc ) )
	{
		if ( !isdefined( p ) ) continue;
		v = p clientfield::get( "tod_necro_fx" );
		if ( !isdefined( v ) || v <= 0 ) continue;
		torch = ( v == 3 || v == 4 );
		if ( torch != inward ) continue;
		d = DistanceSquared( p.origin, self.origin );
		if ( d >= bd ) continue;
		best = p;
		bd = d;
	}
	return best;
}

function soul_stream( lc, inward )
{
	self notify( "tod_necro_stream" );
	self endon( "tod_necro_stream" );
	self endon( "entityshutdown" );
	want = self.tod_necro_state;
	while ( isdefined( self ) && self.tod_necro_state === want )
	{
		p = self stream_partner( lc, inward );
		if ( isdefined( p ) )
			level thread soul_wisp( lc, self, p, inward );
		wait TOD_STREAM_GAP;
	}
}

// one wisp: a client tag_origin carrying the soul trail, homing on its target
// (the target moves, so it re-aims every step) and gone when it arrives
function soul_wisp( lc, actor, player, inward )
{
	if ( inward ) from = player skull_point();
	else          from = actor soul_point();
	host = util::spawn_model( lc, "tag_origin", from, ( 0, 0, 0 ) );
	if ( !isdefined( host ) ) return;
	fx = PlayFXOnTag( lc, level._effect[ "tod_necro_wisp" ], host, "tag_origin" );
	step = TOD_STREAM_FLIGHT / TOD_STREAM_STEPS;
	for ( i = 1; i <= TOD_STREAM_STEPS; i++ )
	{
		if ( !isdefined( host ) || !isdefined( actor ) || !isdefined( player ) ) break;
		if ( inward ) to = actor soul_point();
		else          to = player skull_point();
		// a slight arc: the soul rises off the body, then falls into its target
		k = i / TOD_STREAM_STEPS;
		lift = ( 0, 0, 14 * sin( 180 * k ) );
		host MoveTo( from + ( to - from ) * k + lift, step );
		wait step;
	}
	if ( isdefined( fx ) ) KillFX( lc, fx );
	if ( isdefined( host ) ) host Delete();
}
