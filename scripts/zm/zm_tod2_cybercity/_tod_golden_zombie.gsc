// =============================================================================
// _tod_golden_zombie.gsc — THE GOLDEN ZOMBIE (2026-09-29, docs/197).
//
// User: "I would like to add a golden zombie that has a 1% chance of spawning and give 3 bars to the killer. But we
// need a new model for this." Then (21:30, after the first build): "Golden zombie make one per round" + "It should have
// a golden glow" (tools/lucky/make_golden.py GLOW / GLOW_SCALE raised the same pass).
//
// ONE PER ROUND (TOD_GOLDEN_PER_ROUND): at each round's first ordinary spawn the round picks a TARGET: the Nth ordinary
//   spawn, N drawn from the first TOD_GOLDEN_SPAN of the round's zombies (stock's own count for the round and party),
//   so it always turns up with most of the round left to hunt it. The target spawn turns gold; if it is not an ordinary
//   horde zombie (or changes before the swap), the NEXT ordinary spawn takes the turn. A golden zombie still alive from
//   an earlier round does not cancel this round's. The hook is stock's zm_spawner::add_custom_zombie_spawn_logic, which
//   runs inside zombie_spawn_init AFTER is_zombie / health / the death event are set up (the on_ai_spawned dispatch runs
//   before those - _tod_sprinter's note); every round spawn passes through it (Battle Arena waves too).
// THE LOOK: its own xmodels, tod_golden_zombie_body / _head (tools/lucky/make_golden.py: the horde's mesh + skeleton
//   with GOLD twins of every material, a faint gold self-glow and gold eyes). The swap is the Necromancer thrall's
//   proven sequence (_tod_necro_summon::thrall_look: detach hat + head, SetModel, attach, mirror into gib_data), done
//   TOD_GOLDEN_SWAP_WAIT after the spawn (native character assignment lands after the dispatch) and while a riser is
//   still Ghost()ed, so nobody sees a charcoal zombie turn gold. Then a gold sparkle aura (a tag_origin host on its
//   spine: server effects on an actor do not render) with a soft shimmer loop, and a 2D chime for every player: one is
//   out there.
// IT KEEPS ITS LIMBS: no_gib (a limb gib swaps the body for the CHARCOAL gib models - there are no gold twins of those)
//   and guts_explosion (the close-explosive annihilate path ignores no_gib and would burst it into charcoal pieces).
//   It is never promoted to an armored sprinter (_tod_sprinter::eligible) and never bound as a Necromancer thrall
//   (_tod_necro_summon::is_elite treats it as an elite: helpers hurt it, the bind skips it).
// THE PAYOUT: its KILLER gets TOD_GOLDEN_BARS luck bars through tod_luck::add_bars (one segment at a time, the pip
//   ladder climbing, the LUCK card multiplying each step) + a 2D jackpot chime; everyone sees a gold burst and hears
//   the coins at the corpse. A companion's or a Necromancer helper's kill pays its owner (the map's rule). Its ordinary
//   kill luck / points ride the stock lanes as for any zombie.
// NEVER LOST: a golden zombie that dies to no player (a nuke, a trap, a script sweep) or is removed without dying is
//   OWED: the next ordinary spawn, in any round, turns gold in its place (level.tod_golden_owed, capped at
//   TOD_GOLDEN_OWED_MAX), so no round's chance is wasted by something the players did not do. A spawn that dies before
//   its swap gives the turn back the same way.
//
// Dev logs (level.tod_dev): [TOD_GOLDEN] READY / ROUND / ROLL / SKIP / SPAWN / KILL / LOST.
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\util_shared;
#using scripts\shared\ai\systems\gib;
#using scripts\shared\ai\zombie_utility;

#using scripts\zm\_zm;           // get_zombie_count_for_round (the round's size, as _tod_luck reads it)
#using scripts\zm\_zm_spawner;

#using scripts\zm\zm_tod2_cybercity\_tod_luck;            // add_bars (the killer's three bars)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;    // play_sound_at_origin (the map's proven 3D sound lane)

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#insert scripts\shared\ai\systems\gib.gsh;

#precache( "model", "tod_golden_zombie_body" );
#precache( "model", "tod_golden_zombie_head" );
#precache( "model", "tag_origin" );
#precache( "fx", "tod/luck/fx_luck_golden_aura" );
#precache( "fx", "tod/luck/fx_luck_golden_burst" );

#namespace tod_golden_zombie;

#define TOD_GOLDEN_PER_ROUND      1        // user: "Golden zombie make one per round" (was a 1% chance per spawn)
#define TOD_GOLDEN_SPAN           0.6      // the target is one of the round's first 60% of ordinary spawns
#define TOD_GOLDEN_OWED_MAX       2        // lost goldens re-issued to the next ordinary spawns (at most two waiting)
#define TOD_GOLDEN_BARS           3        // user: "give 3 bars to the killer"
#define TOD_GOLDEN_MODEL_BODY     "tod_golden_zombie_body"   // LOCKSTEP tools/lucky/make_golden.py MODELS
#define TOD_GOLDEN_MODEL_HEAD     "tod_golden_zombie_head"
#define TOD_GOLDEN_DONOR_BODY     "tod_charcoal_c_zom_dlc3_zombie_sentinel_body"   // the horde it is made from
#define TOD_GOLDEN_DONOR_HEAD     "tod_charcoal_c_zom_dlc4_zombie_charred_head"
#define TOD_GOLDEN_FX_AURA        "tod/luck/fx_luck_golden_aura"    // LOOPING, on the spine host
#define TOD_GOLDEN_FX_BURST       "tod/luck/fx_luck_golden_burst"   // one-shot at the death
#define TOD_GOLDEN_SND_SPAWN      "tod_luck_golden_spawn"     // 2D, every player: one is out there
#define TOD_GOLDEN_SND_LOOP       "tod_luck_golden_loop"      // 3D loop on the host: find it by ear
#define TOD_GOLDEN_SND_DEATH      "tod_luck_golden_death"     // 3D at the corpse: the coins
#define TOD_GOLDEN_SND_JACKPOT    "tod_luck_golden_jackpot"   // 2D, the killer
#define TOD_GOLDEN_SWAP_WAIT      0.1      // native character assignment lands after the spawn dispatch
#define TOD_GOLDEN_SHOW_WAIT      0.7      // a riser is Ghost()ed ~0.6 s; the aura and the chime wait for it
#define TOD_GOLDEN_TAG            "j_spine4"
#define TOD_GOLDEN_LOG            1

function init()
{
	level.tod_golden_round = -1;
	level.tod_golden_owed = 0;
	zm_spawner::add_custom_zombie_spawn_logic( &golden_roll );
	log( "READY per_round=" + TOD_GOLDEN_PER_ROUND + " span=" + TOD_GOLDEN_SPAN + " bars=" + TOD_GOLDEN_BARS );
}

// PURE (tools/lucky/test_lucky.js runs it): the round's target, 1..max(1, floor(total x span)), from a 0..1 draw.
function golden_target( total, span, draw )
{
	top = int( total * span );
	if ( top < 1 )
		top = 1;
	t = 1 + int( draw * top );
	if ( t > top )
		t = top;
	return t;
}

// The round bookkeeping: a new round resets the count and draws its target.
function golden_round_tick()
{
	r = level.round_number;
	if ( !isdefined( r ) )
		r = 0;
	if ( level.tod_golden_round == r )
		return;
	level.tod_golden_round = r;
	level.tod_golden_count = 0;
	level.tod_golden_made = 0;
	p = GetPlayers().size;
	if ( p < 1 )
		p = 1;
	total = zm::get_zombie_count_for_round( r, p );
	if ( !isdefined( total ) || total < 1 )
		total = 6;
	level.tod_golden_target = golden_target( total, TOD_GOLDEN_SPAN, RandomFloat( 1 ) );
	log( "ROUND " + r + " zombies=" + total + " golden_at_spawn=" + level.tod_golden_target );
}

// self = a zombie inside stock zombie_spawn_init (threaded). Every ordinary spawn counts; the round's target turns gold.
// An OWED golden (a lost one, golden_owe) goes to the very next ordinary spawn first.
// NO endon( "death" ) BEFORE THE SWAP: a spawn killed inside the swap wait must give its claim back, not take it along.
function golden_roll()
{
	golden_round_tick();
	owed = ( level.tod_golden_owed > 0 );
	if ( !owed )
	{
		if ( level.tod_golden_made >= TOD_GOLDEN_PER_ROUND )
			return;
		level.tod_golden_count++;
		if ( level.tod_golden_count < level.tod_golden_target )
			return;
	}
	ent = self GetEntityNumber();
	if ( !eligible( self ) )
	{
		log( "SKIP ent=" + ent + " reason=not_ordinary owed=" + owed + " (the next ordinary spawn takes the turn)" );
		return;
	}
	r = level.tod_golden_round;
	if ( owed )
		level.tod_golden_owed--;
	else
		level.tod_golden_made++;   // claimed now: the spawns of this same frame do not also turn
	wait TOD_GOLDEN_SWAP_WAIT;
	if ( !isdefined( self ) || !eligible( self ) || self.model !== TOD_GOLDEN_DONOR_BODY )
	{
		if ( owed )
			level.tod_golden_owed++;
		else if ( level.tod_golden_round == r )
			level.tod_golden_made--;   // give the turn back: the next ordinary spawn of this round takes it
		body = "gone";
		if ( isdefined( self ) && isdefined( self.model ) )
			body = self.model;
		log( "SKIP ent=" + ent + " reason=changed_or_dead body=" + body + " owed=" + owed + " (the turn goes back)" );
		return;
	}
	self golden_look();
	self thread golden_death_watch();
	log( "ROLL ent=" + ent + " round=" + ( isdefined( level.round_number ) ? level.round_number : 0 ) + " owed=" + owed + " at=" + self.origin + " arena=" + IS_TRUE( self.tod_arena ) );

	self endon( "death" );   // from here it is gold: golden_death_watch owns its end
	wait TOD_GOLDEN_SHOW_WAIT;
	if ( !isdefined( self ) || !IsAlive( self ) )
		return;
	host = Spawn( "script_model", self.origin );
	if ( !isdefined( host ) )
	{
		log( "SPAWN ent=" + ent + " aura=dropped (entity pool full)" );
		return;
	}
	host SetModel( "tag_origin" );
	if ( isdefined( self GetTagOrigin( TOD_GOLDEN_TAG ) ) )
		host LinkTo( self, TOD_GOLDEN_TAG, ( 0, 0, 0 ), ( 0, 0, 0 ) );
	else
	{
		host.origin = self.origin + ( 0, 0, 48 );   // no spine bone (never seen): ride the body at chest height
		host LinkTo( self );
	}
	host thread aura_run( self );
	foreach ( p in GetPlayers() )
		p PlayLocalSound( TOD_GOLDEN_SND_SPAWN );
	log( "SPAWN ent=" + ent + " aura=on" );
}

// An ordinary horde zombie, not any special AI the map owns.
function eligible( z )
{
	if ( !isdefined( z ) || !IsAlive( z ) )
		return false;
	if ( !isdefined( z.archetype ) || z.archetype != "zombie" )
		return false;
	if ( isdefined( z.team ) && isdefined( level.zombie_team ) && z.team != level.zombie_team )
		return false;   // a Necromancer thrall is on the players' team
	if ( IS_TRUE( z.is_boss ) || IS_TRUE( z.acc_is_boss ) || IS_TRUE( z.acc_is_mini_boss ) )
		return false;
	if ( isdefined( z.tod_boss_kind ) || IS_TRUE( z.tod_golden ) )
		return false;
	if ( isdefined( z.tod_necro_kind ) || isdefined( z.tod_necro_owner ) || IS_TRUE( z.tod_is_partner ) )
		return false;
	if ( IS_TRUE( z.head_gibbed ) || IS_TRUE( z.gibbed ) )
		return false;
	return true;
}

// The swap: _tod_necro_summon::thrall_look's sequence with the gold twins.
function golden_look()
{
	head_old = GIB_HEAD_MODEL( self );
	has_head = ( !IS_TRUE( self.head_gibbed ) && isdefined( head_old ) && head_old != "" );
	hat = GIB_HAT_MODEL( self );
	if ( has_head )
	{
		if ( isdefined( hat ) && hat != "" ) self Detach( hat, "" );
		self Detach( head_old, "" );
	}
	self SetModel( TOD_GOLDEN_MODEL_BODY );
	if ( has_head )
	{
		head_new = ( head_old == TOD_GOLDEN_DONOR_HEAD ? TOD_GOLDEN_MODEL_HEAD : head_old );
		self Attach( head_new, "" );
		self.head = head_new;
		self.hatmodel = undefined;
		if ( isdefined( self.gib_data ) )
		{
			self.gib_data.head = head_new;
			self.gib_data.hatmodel = undefined;
		}
	}
	self.tod_golden = true;
	self.no_gib = true;           // no limb gibs (they would be charcoal)
	self.guts_explosion = true;   // the close-explosive annihilate ignores no_gib: mark it already done
}

// self = the aura host. One server frame before the effect binds (the host's DObj must exist on the client), then it
// lives exactly as long as its zombie - a poll, so a zombie Delete()d without dying (an arena wipe, the crown hall
// clear) still takes its aura with it.
function aura_run( owner )
{
	self endon( "death" );
	wait 0.05;
	PlayFXOnTag( TOD_GOLDEN_FX_AURA, self, "tag_origin" );
	self PlayLoopSound( TOD_GOLDEN_SND_LOOP, 0.3 );
	while ( isdefined( owner ) && IsAlive( owner ) )
		wait 0.2;
	self StopLoopSound( 0.2 );
	self StopSounds();
	wait 0.05;
	self Delete();
}

// self = the golden zombie.
function golden_death_watch()
{
	ent = self GetEntityNumber();
	self waittill( "death", attacker );
	if ( !isdefined( self ) )
	{
		golden_owe( ent, "removed" );
		return;
	}
	org = self.origin + ( 0, 0, 48 );
	tag = self GetTagOrigin( TOD_GOLDEN_TAG );
	if ( isdefined( tag ) )
		org = tag;
	fx_at( TOD_GOLDEN_FX_BURST, org, 3 );
	tod_perk_scatter::play_sound_at_origin( org, TOD_GOLDEN_SND_DEATH, 4 );

	killer = golden_killer( attacker );
	if ( !isdefined( killer ) )
	{
		golden_owe( ent, "no_player_killer" );   // a nuke, a trap, a sweep: the players never had their shot
		return;
	}
	killer PlayLocalSound( TOD_GOLDEN_SND_JACKPOT );
	level thread tod_luck::add_bars( killer, TOD_GOLDEN_BARS );
	log( "KILL ent=" + ent + " killer=" + killer GetEntityNumber() + " bars=" + TOD_GOLDEN_BARS + " bar_before=" + tod_luck::get( killer ) );
}

// A golden zombie the players did not get to kill: the next ordinary spawn (any round) turns gold in its place.
function golden_owe( ent, why )
{
	if ( level.tod_golden_owed < TOD_GOLDEN_OWED_MAX )
		level.tod_golden_owed++;
	log( "LOST ent=" + ent + " why=" + why + " owed=" + level.tod_golden_owed + " (the next ordinary spawn turns gold)" );
}

// The player a kill belongs to: a companion (its gun proxy carries the same fields) or a Necromancer helper pays its
// owner, as every other reward in the map does.
function golden_killer( attacker )
{
	if ( !isdefined( attacker ) )
		return undefined;
	if ( IS_TRUE( attacker.tod_is_partner ) )
		attacker = attacker.tod_partner_owner;
	else if ( isdefined( attacker.tod_necro_owner ) )
		attacker = attacker.tod_necro_owner;
	if ( isdefined( attacker ) && isplayer( attacker ) )
		return attacker;
	return undefined;
}

// A ONE-SHOT effect rides a short-lived tag_origin carrier, played one server frame after it spawns
// (_tod_class_kit::fx_at: a bare server PlayFX of a one-shot does not render in this map).
function fx_at( effect, org, life )
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) )
	{
		log( "FX_DROPPED effect=" + effect + " at=" + org + " (entity pool full)" );
		return;
	}
	host SetModel( "tag_origin" );
	host thread fx_at_play( effect, life );
}

function fx_at_play( effect, life )   // self = the carrier
{
	self endon( "death" );
	wait 0.05;
	PlayFXOnTag( effect, self, "tag_origin" );
	wait life;
	self Delete();
}

function log( msg )
{
	if ( !TOD_GOLDEN_LOG || !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_GOLDEN] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
