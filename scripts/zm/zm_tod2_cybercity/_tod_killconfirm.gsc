// =============================================================================
// _tod_killconfirm.gsc — HIT MARKERS + KILL CONFIRM (2026-09-26 rewrite; user:
// "hit markers ... we have them on elites, but they should be added to all
// enemies ... the hit marker pulse on kill could be a little bit better ...
// ours is pretty bland ... more video game punchy").
//
// WHAT THE PLAYER GETS, in rank order (a higher rank always wins a frame):
//   HIT    every damaging hit on any enemy: a white marker, short.
//   HEAD   a headshot hit: gold, a touch bigger.
//   KILL   any enemy dies to your shot: a RED PUNCH — the marker lands BIG and
//          snaps down to size in 80 ms, then fades. That snap is the "punch".
//   ELITE  an elite dies (tod_luck::boss_kill's vocabulary): a bigger red
//          punch + the headshot ding in your ear (elites only, as before:
//          user 2026-09-13 "Zombies would get annoying" was about the SOUND).
//   BOSS   the biggest punch, longest hold. UNWORN since 2026-10-05: its wearers
//          (the Panzer, then the Keeper at arena level 10) retired whole; the
//          style stays defined for the next boss that is given it.
//
// THE HOOK FOR HITS: stock's actor damage wrapper (_zm.gsc
// actor_damage_override_wrapper) runs every registered
// `zombie_damage_override_callback` with `willBeKilled` already computed
// from the final damage, for EVERY actor that goes through the stock chain —
// the Aetherium HUD's damage numbers ride the same hook, which is the proof it
// fires for every hit. hit_cb() is ours: a HIT/HEAD marker on any damaging
// player hit on an enemy, and the KILL punch when willBeKilled — except for
// elites, whose death is owned by elite_kill() via boss_kill, so a Mangler
// never gets two pulses.
//
// THE LANE: stock allocates `self.hud_damagefeedback` for EVERY zombies player
// (_zm.gsc:6976, a `newdamageindicatorhudelem` on the crosshair) and in this
// map nothing draws it except the vendored Panzer's own per-hit marker. So the
// element is ours to fire: SetShader( "damage_feedback" ) + alpha + Fade /
// Scale / MoveOverTime (stock hudelem methods; _wager.gsc:793 pulses a hudelem
// with ScaleOverTime the same way), tinted through .color. The colour and
// stock size are put back after the fade so the Panzer's own marker is never
// left pink. No clientfield bits, no LUI, no new material, no new sound.
//
// THE ONE OWNER OF THE DING: `ding( player )` is the only place that alias is
// played now (the luck module's headshot lane calls it too), stamped per frame.
//
// LOGS (dev): `[TOD_KILLCONFIRM]` MARK kind= player= victim= dmg= hitloc=
// (every kill/elite/boss; the first TOD_KC_LOG_HITS hits), SKIP reason= when a
// marker is refused (lower rank in the frame / a punch still holding).
// =============================================================================
#using scripts\shared\util_shared;
#using scripts\zm\_zm;

#insert scripts\shared\shared.gsh;

#namespace tod_killconfirm;

// Marker sizes: stock's Panzer marker is 24x48 at (-12,-12) — the sprite's
// visible X lives in the top square of that tall quad, which is why the
// y-offset is half the WIDTH. Keep that rule and scale it.
#define TOD_KC_HIT_W        20
#define TOD_KC_HIT_HOLD     0.18
#define TOD_KC_HEAD_W       23
#define TOD_KC_HEAD_HOLD    0.22
#define TOD_KC_KILL_W       26
#define TOD_KC_KILL_HOLD    0.40
#define TOD_KC_ELITE_W      30
#define TOD_KC_ELITE_HOLD   0.55
#define TOD_KC_BOSS_W       42
#define TOD_KC_BOSS_HOLD    0.95
#define TOD_KC_PUNCH_SCALE  1.7    // a punch lands this much bigger than its size ...
#define TOD_KC_PUNCH_SECS   0.08   // ... and snaps down to size this fast
#define TOD_KC_STOCK_W      24     // put back for the Panzer's own per-hit marker
#define TOD_KC_DING         "tod_headshot_ding"
#define TOD_KC_LOG_HITS     20     // dev: log this many plain hits, then only kills

// ranks: a marker only replaces a lower or equal rank in the same frame, and a
// PUNCH (kill+) is never overwritten by a plain hit while it holds.
#define TOD_KC_RANK_HIT     1
#define TOD_KC_RANK_HEAD    2
#define TOD_KC_RANK_KILL    3
#define TOD_KC_RANK_ELITE   4
#define TOD_KC_RANK_BOSS    5

function init()
{
	level.tod_killconfirm_on = true;
	level.tod_kc_logged_hits = 0;
	zm::register_zombie_damage_override_callback( &hit_cb );
	dev_log( "init hook=zombie_damage_override_callback" );
}

// self = the damaged actor. Stock threads this for every actor damage with
// the kill verdict already made (see the header).
function hit_cb( willBeKilled, inflictor, attacker, damage, flags, meansofdeath, weapon, vpoint, vdir, sHitLoc, psOffsetTime, boneIndex, surfaceType )
{
	if ( !isdefined( self ) || !isdefined( attacker ) || !isplayer( attacker ) )
		return;
	if ( !isdefined( damage ) || damage <= 0 )
		return;
	if ( !isdefined( self.team ) || self.team == attacker.team || IS_TRUE( self.tod_is_partner ) )
		return;   // helpers, partners, friendlies: no marker
	if ( IS_TRUE( willBeKilled ) )
	{
		if ( is_elite( self ) )
			return;   // elite_kill() owns it (ding + big punch) via boss_kill
		if ( IS_TRUE( self.tod_kc_dead ) )
			return;   // two lethal hits in one frame: one pulse
		self.tod_kc_dead = true;
		attacker show_marker( "kill", self, damage, sHitLoc );
		return;
	}
	if ( isdefined( sHitLoc ) && ( sHitLoc == "head" || sHitLoc == "helmet" || sHitLoc == "neck" ) )
		attacker show_marker( "head", self, damage, sHitLoc );
	else
		attacker show_marker( "hit", self, damage, sHitLoc );
}

function is_elite( actor )
{
	if ( isdefined( actor.tod_boss_kind ) ) return true;
	if ( isdefined( actor.archetype ) && actor.archetype != "zombie" ) return true;
	return false;
}

// PUBLIC — an elite died to `player`. kind = "mangler" | "doppelghast" |
// "dealer" (tod_luck::boss_kill's vocabulary). Every one is the ELITE punch: the
// BOSS tier's two wearers (kind "panzer", kind "keeper") retired whole 2026-10-05.
function elite_kill( player, kind )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return;
	player show_marker( "elite", undefined, undefined, kind );
	ding( player );
}

// PUBLIC — the headshot/elite ding, ONCE PER FRAME per player.
function ding( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return;
	if ( isdefined( player.tod_kc_ding_ms ) && player.tod_kc_ding_ms == GetTime() )
		return;
	player.tod_kc_ding_ms = GetTime();
	player PlayLocalSound( TOD_KC_DING );
}

function rank_of( kind )
{
	switch ( kind )
	{
		case "boss":  return TOD_KC_RANK_BOSS;
		case "elite": return TOD_KC_RANK_ELITE;
		case "kill":  return TOD_KC_RANK_KILL;
		case "head":  return TOD_KC_RANK_HEAD;
	}
	return TOD_KC_RANK_HIT;
}

// self = player. Draw one marker. A newer marker takes over an older one's
// fade (sequence stamp) and the reset only runs for the newest; a lower rank
// never replaces a higher rank in the same frame, and a plain hit never
// interrupts a punch that is still holding.
function show_marker( kind, victim, damage, extra )
{
	e = self.hud_damagefeedback;
	if ( !isdefined( e ) )
		return;
	rank = rank_of( kind );
	now = GetTime();
	if ( isdefined( self.tod_kc_ms ) && self.tod_kc_ms == now && isdefined( self.tod_kc_rank ) && self.tod_kc_rank >= rank )
	{
		if ( rank >= TOD_KC_RANK_KILL ) log_skip( "same_frame_rank", kind, victim );
		return;
	}
	if ( rank < TOD_KC_RANK_KILL && isdefined( self.tod_kc_hold_until ) && now < self.tod_kc_hold_until )
		return;   // a punch is on screen; a hit under it would only shrink it
	self.tod_kc_ms = now;
	self.tod_kc_rank = rank;

	w = TOD_KC_HIT_W;  hold = TOD_KC_HIT_HOLD;  color = ( 1, 1, 1 );      punch = false;
	switch ( kind )
	{
		case "head":  w = TOD_KC_HEAD_W;  hold = TOD_KC_HEAD_HOLD;  color = ( 1, 0.85, 0.3 );  break;
		case "kill":  w = TOD_KC_KILL_W;  hold = TOD_KC_KILL_HOLD;  color = ( 1, 0.18, 0.18 ); punch = true; break;
		case "elite": w = TOD_KC_ELITE_W; hold = TOD_KC_ELITE_HOLD; color = ( 1, 0.18, 0.18 ); punch = true; break;
		case "boss":  w = TOD_KC_BOSS_W;  hold = TOD_KC_BOSS_HOLD;  color = ( 1, 0.12, 0.12 ); punch = true; break;
	}
	if ( !isdefined( self.tod_kc_seq ) )
		self.tod_kc_seq = 0;
	self.tod_kc_seq++;
	seq = self.tod_kc_seq;

	e.color = color;
	e.alpha = 1;
	if ( punch )
	{
		// THE PUNCH: land big and centred, snap down to size, then fade.
		bw = int( w * TOD_KC_PUNCH_SCALE );
		e SetShader( "damage_feedback", bw, bw * 2 );
		e.x = -( bw / 2 );
		e.y = -( bw / 2 );
		e ScaleOverTime( TOD_KC_PUNCH_SECS, w, w * 2 );
		e MoveOverTime( TOD_KC_PUNCH_SECS );
		e.x = -( w / 2 );
		e.y = -( w / 2 );
		self.tod_kc_hold_until = now + int( hold * 1000 );
	}
	else
	{
		e SetShader( "damage_feedback", w, w * 2 );
		e.x = -( w / 2 );
		e.y = -( w / 2 );
	}
	e FadeOverTime( hold );
	e.alpha = 0;
	self thread marker_reset( seq, hold );
	log_mark( kind, victim, damage, extra );
}

// self = player. After the fade, hand the element back in stock's shape.
function marker_reset( seq, hold )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	wait hold + 0.05;
	if ( !isdefined( self ) || !isdefined( self.tod_kc_seq ) || self.tod_kc_seq != seq )
		return;   // a newer marker owns the element
	e = self.hud_damagefeedback;
	if ( !isdefined( e ) )
		return;
	e.alpha = 0;
	e.color = ( 1, 1, 1 );
	e SetShader( "damage_feedback", TOD_KC_STOCK_W, TOD_KC_STOCK_W * 2 );
	e.x = -( TOD_KC_STOCK_W / 2 );
	e.y = -( TOD_KC_STOCK_W / 2 );
}

// self = player
function log_mark( kind, victim, damage, extra )
{
	if ( !IS_TRUE( level.tod_dev ) ) return;
	if ( kind == "hit" || kind == "head" )
	{
		if ( level.tod_kc_logged_hits >= TOD_KC_LOG_HITS ) return;
		level.tod_kc_logged_hits++;
	}
	dev_log( "MARK kind=" + kind + " player=" + self GetEntityNumber()
	       + " victim=" + ( isdefined( victim ) ? victim GetEntityNumber() : "-" )
	       + " dmg=" + ( isdefined( damage ) ? int( damage ) : -1 )
	       + " extra=" + ( isdefined( extra ) ? extra : "-" ) );
}

function log_skip( reason, kind, victim )
{
	if ( !IS_TRUE( level.tod_dev ) ) return;
	dev_log( "SKIP reason=" + reason + " kind=" + kind + " player=" + self GetEntityNumber() + " victim=" + ( isdefined( victim ) ? victim GetEntityNumber() : "-" ) );
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_KILLCONFIRM] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
