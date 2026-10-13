// =============================================================================
// _tod_archer_rune.gsc - THE RUNE PRISON: the Fire Bow's charged shot
// (2026-09-26, user: "the last tier is a fire bow ... in Der Eisendrache ...
// there is like a fire charge up move. I wonder if we can get that in here").
//
// WHAT IT IS. Der Eisendrache's upgraded fire bow (Kreemasaleet lahm
// Ahmhogaroc, "Rune Prison"): a FULLY DRAWN arrow plants a burning rune where
// it lands; the rune glows for a moment, then ERUPTS - the zombies standing in
// the ring die in the fire and the rest are set ablaze. Every asset of that
// shot ships in the mod tools already (the dlc1/zmb_weapon "rune ... ug" effect
// set, the charged draw loop and the full-power release on
// elemental_bow_sounds.csv, the rune bow models this map fires); only the
// script did not, so this is that script, tuned to this map's numbers.
//
// HOW. `grenade_fire` on a Fire Bow (base or EX) hands the arrow over;
// _tod_archer_bow stamps its draw on it (`proj.tod_ab_charge`, 0..1, one
// frame later). At TOD_RUNE_ARM_FRAC or more, and off cooldown, the arrow is
// ARMED: the upgraded arrowhead burns on it, and where it dies (the Retriever's
// proven `waittill( "death" )` + origin) a rune is planted on the floor:
// ug_glow -> TOD_RUNE_DELAY_MS -> ug_fire + the aoe burst + the full-power
// explosion, the sweep (kill up to TOD_RUNE_KILL_CAP ordinary zombies outright,
// elites take TOD_RUNE_ELITE_HP round-zombie healths, everyone else in the
// ring burns for TOD_RUNE_TRAP_MS) -> TOD_RUNE_TRAP_MS of fire -> ug_end.
// Health-derived damage is marked `tod_ps_exempt` around each DoDamage so the
// power scale's front door passes it whole (memory tod2-power-scale). The draw
// loop the archer hears at full draw (TOD_RUNE_LOOP) is the "it is armed" tell.
//
// Logs `[TOD_RUNE]` (dev): INIT, ARM / SKIP reason=, LAND, ERUPT killed= elites=
// burned=, BURN_END. Knobs per symptom: too strong = KILL_CAP / RADIUS / CD_MS;
// too slow to feel = DELAY_MS; ring lingers = HOLD_MS.
// =============================================================================

#using scripts\shared\util_shared;
#using scripts\shared\callbacks_shared;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // docs/206: the one-shots on carriers, the torso fire on the client
#using scripts\zm\zm_tod2_cybercity\_tod_archer_bow;   // draw_window: the live full draw for the armed hum (a leaf: it imports no tod module)

#insert scripts\shared\shared.gsh;

#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_arrowhead_ug_zmb" );
#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_impact_ug_glow_zmb" );
#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_impact_ug_fire_zmb" );
#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_impact_ug_end_zmb" );
#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_impact_aoe_zmb" );
#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_fire_torso_zmb" );
#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_arrow_trail_zmb" );
#precache( "fx", "dlc1/zmb_weapon/fx_bow_rune_impact_ug_zmb" );

#namespace tod_archer_rune;

#define TOD_RUNE_REV        "rune_prison_v2b"
#define TOD_RUNE_ARM_FRAC   0.98    // the draw fraction that arms the rune (= _tod_archer_bow's TOD_AB_FULL: a full draw; every HELD arrow of the auto-release bow is one)
// THE ARMED HUM (2026-10-05, the automatic bow): the bow releases itself at full draw, so there is no "held at full"
// any more. The hum plays through the LAST part of every draw while a rune is ready - the next arrow plants it - and
// never at an automatic cadence. The window is the live one (_tod_archer_bow::draw_window: PaP + QUICK DRAW).
#define TOD_RUNE_LOOP_FROM  0.5     // ... from this fraction of the draw
#define TOD_RUNE_LOOP_MIN_MS 250    // ... and only on a draw at least this long
#define TOD_RUNE_CD_MS      5000    // one rune per archer per this long; a full draw inside it is an ordinary arrow
#define TOD_RUNE_MAX_LIVE   3       // runes on the ground per archer at once
#define TOD_RUNE_DELAY_MS   900     // the rune glows this long before it erupts
#define TOD_RUNE_RADIUS     240     // eruption reach (u, on the floor)
#define TOD_RUNE_HEIGHT     160     // ... and this far above / below it
#define TOD_RUNE_KILL_CAP   12      // ordinary zombies killed outright per eruption (nearest first)
#define TOD_RUNE_ELITE_HP   4.0     // an elite / boss takes this many round-zombie healths
#define TOD_RUNE_BURN_HP    0.5     // a trapped ordinary zombie burns this many round-zombie healths per second
#define TOD_RUNE_TRAP_MS    4000    // THE PRISON: the fire holds and burns what it catches this long, then consumes it
#define TOD_RUNE_TRACK_SECS 6.0     // an armed arrow that never lands (sky) is forgotten after this
#define TOD_RUNE_LOOP       "wpn_rune_prison_bow_fire_loop_upg_plr"   // heard by the archer at full draw while armed
#define TOD_RUNE_ERUPT_SND  "exp_elemental_bow_full"                  // the eruption, 3D at the rune
#define TOD_RUNE_FX_ARROW   "dlc1/zmb_weapon/fx_bow_rune_arrowhead_ug_zmb"
#define TOD_RUNE_FX_GLOW    "dlc1/zmb_weapon/fx_bow_rune_impact_ug_glow_zmb"
#define TOD_RUNE_FX_FIRE    "dlc1/zmb_weapon/fx_bow_rune_impact_ug_fire_zmb"
#define TOD_RUNE_FX_END     "dlc1/zmb_weapon/fx_bow_rune_impact_ug_end_zmb"
#define TOD_RUNE_FX_AOE     "dlc1/zmb_weapon/fx_bow_rune_impact_aoe_zmb"
#define TOD_RUNE_FX_TORSO   "dlc1/zmb_weapon/fx_bow_rune_fire_torso_zmb"
#define TOD_RUNE_FX_TRAIL   "dlc1/zmb_weapon/fx_bow_rune_arrow_trail_zmb"      // the armed arrow's trail (dies with the arrow)
#define TOD_RUNE_FX_IMPACT  "dlc1/zmb_weapon/fx_bow_rune_impact_ug_zmb"        // the landing burst (one-shot)
#define TOD_RUNE_SND_IMPACT "wpn_rune_prison_proj_impact_upgraded"
#define TOD_RUNE_SND_RISE   "wpn_rune_prison_mound_appear"
#define TOD_RUNE_SND_END    "wpn_rune_prison_mound_disappear"

function rune_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_RUNE] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function init()
{
	callback::on_spawned( &on_spawned );
	rune_log( "INIT rev=" + TOD_RUNE_REV + " arm_frac=" + TOD_RUNE_ARM_FRAC + " cd_ms=" + TOD_RUNE_CD_MS + " delay_ms=" + TOD_RUNE_DELAY_MS +
	          " radius=" + TOD_RUNE_RADIUS + " kill_cap=" + TOD_RUNE_KILL_CAP + " elite_hp=" + TOD_RUNE_ELITE_HP + " trap_ms=" + TOD_RUNE_TRAP_MS + " burn_hp_per_s=" + TOD_RUNE_BURN_HP );
}

// self = player. One watcher set per player for the whole game.
function on_spawned()
{
	if ( IS_TRUE( self.tod_rune_watch_on ) ) return;
	self.tod_rune_watch_on = true;
	self.tod_rune_next_ms = 0;
	self.tod_rune_live = 0;
	self thread arm_watch();
	self thread loop_watch();
}

function is_fire_bow( weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) ) return false;
	return IsSubStr( weapon.name, "cc_fire_bow" );
}

function ready( now )
{
	return ( now >= self.tod_rune_next_ms && self.tod_rune_live < TOD_RUNE_MAX_LIVE );
}

// self = player. Every Fire Bow arrow: armed at a full draw, off cooldown.
// THE ARROW IS A MISSILE (build-11 test, 2026-09-26: the user's log had FIRE
// frac=1 and HIT lane=player but not one ARM/SKIP - "grenade_fire" is raised for
// grenades only; a bow's arrow raises stock's "missile_fire" (missile, weapon),
// the notify every rocket/bow script in the tools root waits on). Both are
// listened to now, one handler.
function arm_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	self thread arm_watch_notify( "missile_fire" );
	self thread arm_watch_notify( "grenade_fire" );
}

function arm_watch_notify( note )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( note, proj, w );
		if ( !isdefined( proj ) || !is_fire_bow( w ) ) continue;
		wait 0.05;   // _tod_archer_bow::projectile_watch stamps the draw on the same notify
		frac = 0;
		if ( isdefined( proj ) && isdefined( proj.tod_ab_charge ) ) frac = proj.tod_ab_charge;
		else if ( isdefined( self.tod_ab_charge ) ) frac = self.tod_ab_charge;
		now = GetTime();
		if ( frac < TOD_RUNE_ARM_FRAC )
		{
			if ( frac >= 0.5 ) rune_log( "SKIP player=" + self GetEntityNumber() + " reason=not_full frac=" + frac );
			continue;
		}
		if ( now < self.tod_rune_next_ms ) { rune_log( "SKIP player=" + self GetEntityNumber() + " reason=cooldown left_ms=" + ( self.tod_rune_next_ms - now ) ); continue; }
		if ( self.tod_rune_live >= TOD_RUNE_MAX_LIVE ) { rune_log( "SKIP player=" + self GetEntityNumber() + " reason=max_live live=" + self.tod_rune_live ); continue; }
		if ( !isdefined( proj ) ) { rune_log( "SKIP player=" + self GetEntityNumber() + " reason=arrow_gone" ); continue; }
		self.tod_rune_next_ms = now + TOD_RUNE_CD_MS;
		rune_log( "ARM player=" + self GetEntityNumber() + " weapon=" + w.name + " frac=" + frac + " live=" + self.tod_rune_live );
		self thread rune_arrow( proj, w );
	}
}

// self = player. Follows one armed arrow to the ground. The arrow wears the
// upgraded arrowhead AND the rune bow's arrow trail; both end with the arrow (the
// missile is deleted at impact - an attached effect dies with its host).
function rune_arrow( proj, w )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	PlayFXOnTag( TOD_RUNE_FX_ARROW, proj, "tag_origin" );
	PlayFXOnTag( TOD_RUNE_FX_TRAIL, proj, "tag_origin" );
	s = SpawnStruct();
	s.dead = false;
	s.pos = proj.origin;
	proj thread death_note( s );
	t = 0;
	while ( !s.dead && t < TOD_RUNE_TRACK_SECS )
	{
		if ( isdefined( proj ) ) s.pos = proj.origin;
		wait 0.05;
		t += 0.05;
		if ( !isdefined( proj ) ) break;
	}
	if ( !s.dead && isdefined( proj ) ) { rune_log( "LOST player=" + self GetEntityNumber() + " reason=never_landed" ); return; }
	if ( !isdefined( s.pos ) ) { rune_log( "LOST player=" + self GetEntityNumber() + " reason=no_landing_pos" ); return; }
	// The rune lies on the floor under the arrow (a wall hit still plants it at the wall's foot).
	tr = BulletTrace( s.pos + ( 0, 0, 16 ), s.pos - ( 0, 0, 320 ), false, undefined );
	ground = s.pos;
	if ( tr[ "fraction" ] < 1 ) ground = tr[ "position" ] + ( 0, 0, 2 );
	tod_ability_fx::burst_at( TOD_RUNE_FX_IMPACT, ground, ( -90, 0, 0 ), 2.0 );   // the upgraded impact burst (one-shot; on a carrier since docs/206 - a bare PlayFX drew nothing)
	tod_perk_scatter::play_sound_at_origin( ground, TOD_RUNE_SND_IMPACT, 2 );
	level thread rune_erupt( self, ground, w );   // on LEVEL: the archer leaving must never strand a burning rune
}

// self = the arrow. Its death is the landing.
function death_note( s )
{
	self waittill( "death" );
	// A missile deleted at impact has NO origin by the time this wakes (build-14 log:
	// 122 script errors, every one from this undefined pos - and each one broke the
	// rune thread before its fire host was deleted = the "effects staying the whole
	// game"). Keep the last tracked position unless a real one is still readable.
	if ( isdefined( self ) && isdefined( self.origin ) ) s.pos = self.origin;
	s.dead = true;
}

// A host for a LOOPING effect at a point: the loop ends when the host is deleted
// (build-14 test, user: "the effects ... staying there the whole game" - PlayFX at a
// point has nothing to delete; there is no server StopFX for it).
function fx_host( pos )
{
	h = Spawn( "script_model", pos );
	h SetModel( "tag_origin" );
	h thread host_failsafe();
	return h;
}

// self = an fx host. Belt and braces: whatever happens to the rune's thread, the
// host (and its looping fire) is gone a little after the prison could have ended.
function host_failsafe()
{
	self endon( "death" );
	wait ( ( TOD_RUNE_DELAY_MS + TOD_RUNE_TRAP_MS ) / 1000.0 ) + 2;
	rune_log( "FAILSAFE host deleted at=" + self.origin );
	self Delete();
}

// self = level. One rune: the glow (hosted), the eruption, THE PRISON, out.
function rune_erupt( attacker, pos, w )
{
	level endon( "end_game" );
	if ( !isdefined( pos ) ) return;
	if ( isdefined( attacker ) ) attacker.tod_rune_live++;
	glow = fx_host( pos );
	PlayFXOnTag( TOD_RUNE_FX_GLOW, glow, "tag_origin" );
	tod_perk_scatter::play_sound_at_origin( pos, TOD_RUNE_SND_RISE, 2 );
	rune_log( "LAND player=" + ( isdefined( attacker ) ? attacker GetEntityNumber() : -1 ) + " pos=" + pos + " live=" + ( isdefined( attacker ) ? attacker.tod_rune_live : -1 ) );
	wait ( TOD_RUNE_DELAY_MS / 1000.0 );
	if ( isdefined( glow ) ) glow Delete();
	fire = fx_host( pos );
	PlayFXOnTag( TOD_RUNE_FX_FIRE, fire, "tag_origin" );
	tod_ability_fx::burst_at( TOD_RUNE_FX_AOE, pos, ( -90, 0, 0 ), 2.5 );   // docs/206
	tod_perk_scatter::play_sound_at_origin( pos, TOD_RUNE_ERUPT_SND, 3 );
	prison( attacker, pos, w );
	if ( isdefined( fire ) ) fire Delete();
	tod_ability_fx::burst_at( TOD_RUNE_FX_END, pos, ( -90, 0, 0 ), 2.5 );   // docs/206
	tod_perk_scatter::play_sound_at_origin( pos, TOD_RUNE_SND_END, 2 );
	if ( isdefined( attacker ) ) attacker.tod_rune_live--;
	rune_log( "END player=" + ( isdefined( attacker ) ? attacker GetEntityNumber() : -1 ) + " pos=" + pos );
}

function zombie_hp()
{
	if ( isdefined( level.zombie_health ) && level.zombie_health > 0 ) return level.zombie_health;
	return 100;
}

function is_elite( actor )
{
	if ( isdefined( actor.tod_boss_kind ) ) return true;
	if ( isdefined( actor.archetype ) && actor.archetype != "zombie" ) return true;
	return false;
}

// A bone the victim has for the burning-torso effect (never a guessed one: a
// missing bone in PlayFXOnTag is a crash - memory playfxontag-missing-bone-crashes).
function torso_tag( z )
{
	if ( isdefined( z GetTagOrigin( "j_spine4" ) ) ) return "j_spine4";
	if ( isdefined( z GetTagOrigin( "j_spineupper" ) ) ) return "j_spineupper";
	if ( isdefined( z GetTagOrigin( "j_spine2" ) ) ) return "j_spine2";
	return undefined;
}

// Health-derived damage, passed whole by the power scale's front door.
function exempt_damage( z, dmg, pos, attacker, w )
{
	if ( !isdefined( z ) || !IsAlive( z ) ) return;
	z.tod_ps_exempt = true;
	z DoDamage( int( dmg ), pos, attacker, undefined, "none", "MOD_BURNED", 0, w );
	if ( isdefined( z ) ) z.tod_ps_exempt = undefined;
}

// THE PRISON (build-14 test, user: "the charge up shot ... doesn't look right ...
// missing stuff"): Der Eisendrache's rune holds what it catches. For TOD_RUNE_TRAP_MS
// every ordinary zombie that steps into the ring is TRAPPED (the Electric Cherry stun
// recipe, _tod_class_kit::stun_stock: zombie_tesla_hit + ignoreall) and burns
// (TOD_RUNE_BURN_HP round-zombie healths per second); elites are never held, they
// take TOD_RUNE_ELITE_HP healths spread over the hold. When the prison ends the
// trapped ordinary zombies are consumed (first caught first, up to TOD_RUNE_KILL_CAP)
// and everyone else is let go.
function prison( attacker, pos, w )
{
	ticks = int( TOD_RUNE_TRAP_MS / 250 );
	if ( ticks < 1 ) ticks = 1;
	trapped = [];
	elite_tick = TOD_RUNE_ELITE_HP * zombie_hp() / ticks;
	burn_tick = TOD_RUNE_BURN_HP * zombie_hp() / 4;   // per quarter second
	for ( i = 0; i < ticks; i++ )
	{
		zombies = GetAITeamArray( level.zombie_team );
		near = util::get_array_of_closest( pos, zombies, undefined, undefined, TOD_RUNE_RADIUS );
		if ( !isdefined( near ) ) near = [];
		foreach ( z in near )
		{
			if ( !isdefined( z ) || !IsAlive( z ) ) continue;
			if ( Abs( z.origin[ 2 ] - pos[ 2 ] ) > TOD_RUNE_HEIGHT ) continue;
			if ( !IS_TRUE( z.tod_rune_trapped ) )
			{
				z.tod_rune_trapped = true;
				trapped[ trapped.size ] = z;
				tod_ability_fx::burn( z );   // docs/206: the torso fire on the client for TOD_RUNE_TRAP_MS (a server PlayFXOnTag on an actor does not render here)
				if ( !is_elite( z ) ) trap( z );
			}
			exempt_damage( z, ( is_elite( z ) ? elite_tick : burn_tick ), pos, attacker, w );
		}
		wait 0.25;
	}
	killed = 0; elites = 0; freed = 0;
	foreach ( z in trapped )
	{
		if ( !isdefined( z ) ) continue;
		release( z );
		if ( !IsAlive( z ) ) continue;
		if ( is_elite( z ) ) { elites++; continue; }
		if ( killed < TOD_RUNE_KILL_CAP ) { killed++; exempt_damage( z, z.health + 1, pos, attacker, w ); }
		else freed++;
	}
	rune_log( "ERUPT player=" + ( isdefined( attacker ) ? attacker GetEntityNumber() : -1 ) + " pos=" + pos + " trapped=" + trapped.size + " killed=" + killed + " elites=" + elites + " freed=" + freed + " zombie_hp=" + zombie_hp() );
}

// The hold: the stun recipe, without its own timer - release() ends it.
function trap( z )
{
	z.zombie_tesla_hit = true;
	z.ignoreall = true;
}

function release( z )
{
	z.tod_rune_trapped = undefined;
	if ( !isdefined( z ) || !IsAlive( z ) ) return;
	if ( isdefined( z.tod_stun_until ) && z.tod_stun_until > GetTime() ) return;   // a Bash stun still owns it
	z.zombie_tesla_hit = false;
	if ( !IS_TRUE( z.tod_frozen ) && !IS_TRUE( level.tod_upgrade_pause ) ) z.ignoreall = false;
}

// self = player. The armed-draw tell: the upgraded draw loop while a Fire Bow
// is held at full draw and the rune is ready; stopped on release / swap / cooldown.
function loop_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	on = false;
	for ( ;; )
	{
		wait 0.05;
		w = self GetCurrentWeapon();
		want = false;
		if ( is_fire_bow( w ) && isdefined( self.tod_ab_press_ms ) && self AttackButtonPressed() && self ready( GetTime() ) )
		{
			win_ms = Int( self tod_archer_bow::draw_window( w ) * 1000 );
			into = GetTime() - self.tod_ab_press_ms;   // negative while a held chain's release plays
			want = ( win_ms >= TOD_RUNE_LOOP_MIN_MS && into >= Int( win_ms * TOD_RUNE_LOOP_FROM ) );
		}
		if ( want && !on ) { self PlayLocalSound( TOD_RUNE_LOOP ); on = true; }
		else if ( !want && on ) { self StopLocalSound( TOD_RUNE_LOOP ); on = false; }
	}
}
