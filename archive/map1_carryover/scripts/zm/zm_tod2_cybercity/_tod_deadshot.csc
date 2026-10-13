// =============================================================================
// _tod_deadshot.csc — DEADSHOT upgrade, client half (domain 47, v16.64)
//
// The whole of the retired Deadshot Daiquiri perk was this client call:
// `UseAlternateAimParams()` on, `ClearAlternateAimParams()` off (stock
// _zm_perk_deadshot.csc::player_deadshot_perk_handler; memory
// `deadshot-aim-params-unauthorable`). This module is that handler bound to
// OUR 1-bit toplayer field instead of the perk's clientuimodel field, plus
// the perk-bar crest: the Aetherium perks container draws whatever
// `hudItems.perks.<clientFieldName>` models read > 0 (AetheriumPerksContainer
// .lua HandlePerksList), and stock fills those from a 2-bit CLIENTUIMODEL
// field per perk. That pool sits at 60 of the PROVEN 61 bits (the
// _tod_upgrade_ui.gsc BUDGET note), so instead the handler WRITES the model
// itself — SetUIModelValue( CreateUIModel( ... ) ), the exact idiom stock's
// _zm_utility.csc:155 uses for zmInventory — and spends nothing. The Lua
// entry (AetheriumPerks.lua, clientFieldName "dead_shot") is what makes the
// container subscribe to that model.
//
// THE LOCAL GUARD IS LOAD-BEARING (memory `registered-perk-is-not-sellable`;
// live 2026-08-30: an unguarded toplayer callback lit Death Perception's
// outlines for EVERY player). Toplayer fires for the spectated player and for
// every player on the host's client VM; only the local player's own value may
// touch this machine's aim params and HUD.
//
// LOCKSTEP: the register here == "tod_deadshot" 1-bit in _tod_deadshot.gsc.
// CF_CALLBACK_ZERO_ON_NEW_ENT like stock's deadshot_perk field: a new player
// entity (respawn) starts clear, and the server re-drives 0 -> 1.
// =============================================================================

#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#define TOD_DEADSHOT_FIELD    "tod_deadshot"              // LOCKSTEP with _tod_deadshot.gsc
#define TOD_DEADSHOT_UIMODEL  "hudItems.perks.dead_shot"  // == AetheriumPerks.lua clientFieldName "dead_shot" under hudItems.perks (stock's PERK_CLIENTFIELD_DEAD_SHOT leaf)

#namespace tod_deadshot;

REGISTER_SYSTEM( "tod_deadshot", &__init__, undefined )

function __init__()
{
	clientfield::register( "toplayer", TOD_DEADSHOT_FIELD, VERSION_SHIP, 1, "int", &deadshot_cb, !CF_HOST_ONLY, CF_CALLBACK_ZERO_ON_NEW_ENT );
}

// self = the player whose field changed — NOT necessarily the local player.
function deadshot_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( self != GetLocalPlayer( localClientNum ) )
		return;
	on = ( isdefined( newVal ) && newVal > 0 );
	if ( on )
		self UseAlternateAimParams();
	else
		self ClearAlternateAimParams();
	// The perk bar: 1 = PERK_STATE_OWNED, 0 = gone. CreateUIModel is
	// idempotent on an existing model (stock calls it on every write).
	SetUIModelValue( CreateUIModel( GetUIModelForController( localClientNum ), TOD_DEADSHOT_UIMODEL ), ( ( on ) ? 1 : 0 ) );
}
