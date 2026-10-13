// =============================================================================
// _tod_deadshot.gsc — DEADSHOT, the assault's perma aim-bot upgrade (domain 47)
//
// v16.64 (user 2026-09-02): "we would need a deadshot upgrade now. Basically
// its perma deadshot. Itll show up in your perk bar as well and only way to
// pull it is an Ultimate card ... Name on top will be Deadshot. Aim bot will be
// the description."
//
// WHAT IT IS. One level of the `deadshot` domain (registered in
// _tod_upgrades::register_domains — assault only, max 1, band S, always dealt
// as an ULTIMATE via set_rarity_lock) switches on the ENGINE's Deadshot: the
// head-snap aim assist that the retired Deadshot Daiquiri machine used to
// sell. The perk was one line — `UseAlternateAimParams()` on the client, see
// memory `deadshot-aim-params-unauthorable` — so the upgrade is that one line,
// driven by a 1-bit toplayer field of our own, plus the engine perk flag and
// the perk-bar crest. Gamepad only: aim assist does not exist on M+KB, and the
// card copy says so.
//
// WHY NOT zm_perks::give_perk / the stock _zm_perk_deadshot module:
//   * give_perk increments num_perks and lands in perks_active, so the upgrade
//     would EAT a perk slot and be STRIPPED by stock on every down. The user
//     asked for a permanent upgrade that merely shows in the bar.
//   * the stock module registers a machine, a bottle weapon, a triggerstring
//     pair and a 2-bit clientuimodel field. The machine is retired (v14.16),
//     the triggerstring budget is a standing constraint, and the clientuimodel
//     pool sits at 60 of the PROVEN 61 bits — a 2-bit field would not boot.
//     So: raw SetPerk (HasPerk reads true for any stock consumer; num_perks
//     untouched, so the perk cap never sees it), a 1-bit TOPLAYER field (that
//     pool holds 2 bits today), and the .csc writes the perk bar's UI model
//     itself. See _tod_deadshot.csc.
//
// HOW IT LANDS. No hook in the deal: a per-player RECONCILE LOOP (1 s) reads
// tod_upgrades::get_level and makes the world match — the perk flag, the
// field, the on/off latch. That covers every grant lane the map has (the
// event deal, the station, level.tod_dev's grant-all) and every life:
// on_spawned resets the latch and the field so a new
// player ENTITY (whose client zeroed its copy, CF_CALLBACK_ZERO_ON_NEW_ENT)
// receives a fresh 0 -> 1 edge, and a revive pulses the field so the client
// re-asserts the aim params after stock's last-stand weapon shuffle.
// PERMA: the level lives on the player object, so nothing here ever removes
// it; a level of 0 (never rolled) keeps the field at 0 and does nothing.
//
// LOCKSTEP: TOD_DEADSHOT_FIELD here == the register in _tod_deadshot.csc
// (clientfield names are the wire format). TOD_DEADSHOT_KEY == the add_domain
// key in _tod_upgrades.gsc.
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;   // get_level — the ONE truth for "does this player own DEADSHOT"

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#define TOD_DEADSHOT_KEY      "deadshot"            // add_domain key (_tod_upgrades.gsc)
#define TOD_DEADSHOT_PERK     "specialty_deadshot"  // the engine perk flag (stock PERK_DEAD_SHOT)
#define TOD_DEADSHOT_FIELD    "tod_deadshot"        // toplayer, 1 bit — LOCKSTEP with _tod_deadshot.csc
#define TOD_DEADSHOT_POLL     1.0                   // reconcile cadence, seconds

#namespace tod_deadshot;

// THE CLIENTFIELD MUST BE REGISTERED HERE, AT SYSTEM-INIT TIME — NOT IN init().
// v16.67 shipped the register inside init(), which _tod_main::init() calls
// AFTER zm_usermap::main() has closed the engine's registration window, and
// the map aborted at load: "Com_ERROR: Attempt to register ClientField
// tod_deadshot post finalization of ClientField registration period failed."
// (2026-09-03, the user's first failed load in weeks; session 26 read the
// console line.) REGISTER_SYSTEM's __init__ runs in the load phase where the
// window is still open — the _tod_upgrade_ui.gsc:143 / _tod_perk_electric_cherry
// pattern, and the .csc half already did it this way. Every clientfield in
// BOTH VMs goes through a REGISTER_SYSTEM __init__; nothing else is early
// enough. init() keeps only the spawn callback.
REGISTER_SYSTEM( "tod_deadshot", &__init__, undefined )

function __init__()
{
	clientfield::register( "toplayer", TOD_DEADSHOT_FIELD, VERSION_SHIP, 1, "int" );
}

function init()
{
	callback::on_spawned( &on_player_spawned );
}

// self = player. Every life: clear the server's copy of the field so the next
// 1 is a CHANGE the client sees (its own copy was zeroed with the new entity),
// drop the latch so reconcile re-asserts, and start the keeper ONCE.
//
// RESPAWN LATCH in the function, not at the registration site (the shipped
// idiom — _tod_riotshield, _tod_distraction): callback::callback THREADS every
// registered func on every dispatch, so an unlatched thread here would stack
// one keeper per life.
function on_player_spawned()
{
	self clientfield::set_to_player( TOD_DEADSHOT_FIELD, 0 );
	self.tod_deadshot_on = false;
	if ( IS_TRUE( self.tod_deadshot_watch_on ) )
		return;
	self.tod_deadshot_watch_on = true;
	self thread reconcile_loop();
	self thread revive_watch();
}

// THE KEEPER. self = player; one per player for the match (no endon "death" —
// the level survives the life, so the loop does too; on_spawned only resets).
function reconcile_loop()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	for ( ;; )
	{
		self reconcile();
		wait TOD_DEADSHOT_POLL;
	}
}

// Make the world match the level. Idempotent; cheap (one get_level, one
// HasPerk); safe while downed (SetPerk on a last-stand player is a no-op for
// the engine's aim path and the client handler is what actually matters).
function reconcile()
{
	if ( !isdefined( self ) )
		return;
	want = ( tod_upgrades::get_level( self, TOD_DEADSHOT_KEY ) > 0 );
	if ( want && !( self HasPerk( TOD_DEADSHOT_PERK ) ) )
		self SetPerk( TOD_DEADSHOT_PERK );
	if ( want != IS_TRUE( self.tod_deadshot_on ) )
	{
		self.tod_deadshot_on = want;
		self clientfield::set_to_player( TOD_DEADSHOT_FIELD, ( ( want ) ? 1 : 0 ) );
	}
}

// A revive: stock re-runs its perk bookkeeping (UnsetPerk on everything in
// perks_active — ours is not in it, but the ENGINE may still drop the flag
// with the last-stand state) and the client may have shed its aim params with
// the weapon shuffle. Pulse the field 1 -> 0 and drop the latch: the keeper
// re-sets the perk and drives a fresh 0 -> 1 edge within a second. Idempotent.
function revive_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( "player_revived" );
		wait 0.5;   // let stock's revive settle (health, weapons) first
		if ( !isdefined( self ) || !IS_TRUE( self.tod_deadshot_on ) )
			continue;
		self clientfield::set_to_player( TOD_DEADSHOT_FIELD, 0 );
		self.tod_deadshot_on = false;
	}
}
