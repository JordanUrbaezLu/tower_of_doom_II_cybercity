// =============================================================================
// _tod_class_cards.csc - client half of the class build cards (2026-09-28).
//
// THE INVISIBILITY CLOAK'S LOOK (user: "Invisible cloak should give the In Plain
// Sight gobblegum visual effects" + "it would be nice if the character ... can
// become opaque ... a visual for other players to know that they are in the cloak"):
//   * the cloaked player's own screen: In Plain Sight's vision set and post-FX
//     bundle, both retail assets in zm_common (vision/zm_bgb_in_plain_sight.vision,
//     pstfx_zm_bgb_in_plain_sight), under OUR visionset_mgr name "tod_cloak" -
//     the retail gum registers its own name in scripts this map never compiles,
//     and visionset_mgr resolves names by REGISTRATION (_tod_powerups.gsc's Zombie
//     Blood note: an unregistered activate kills the calling thread).
//   * everyone else: a blue-grey soul aura on the cloaked player's body (the
//     Necromancer's thrall aura, already zoned). BO3 has no per-player alpha, so
//     a translucent body would need a ghost-material model twin (art); the aura
//     is the cheap, readable tell.
// LOCKSTEP with _tod_class_cards.gsc: the visionset_mgr names and the
// "tod_cloak_fx" clientfield (allplayers, 1 bit).
// =============================================================================

#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\visionset_mgr_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#precache( "client_fx", "tod/necro/fx_necro_thrall_aura" );

#namespace tod_class_cards;

#define TOD_CLOAK_VSMGR         "tod_cloak"
#define TOD_CLOAK_VISION        "zm_bgb_in_plain_sight"
#define TOD_CLOAK_POSTFX        "pstfx_zm_bgb_in_plain_sight"
#define TOD_CLOAK_VS_LERP       16
#define TOD_CLOAK_AURA_FX       "tod/necro/fx_necro_thrall_aura"
#define TOD_CLOAK_AURA_TAG      "j_spine4"

REGISTER_SYSTEM( "tod_class_cards", &__init__, undefined )

function __init__()
{
	visionset_mgr::register_visionset_info( TOD_CLOAK_VSMGR, VERSION_SHIP, TOD_CLOAK_VS_LERP, undefined, TOD_CLOAK_VISION );
	visionset_mgr::register_overlay_info_style_postfx_bundle( TOD_CLOAK_VSMGR, VERSION_SHIP, 1, TOD_CLOAK_POSTFX );
	clientfield::register( "allplayers", "tod_cloak_fx", VERSION_SHIP, 1, "int", &cloak_fx_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	level._effect[ "tod_cloak_aura" ] = TOD_CLOAK_AURA_FX;
}

// self = a player entity. The aura is for OTHER players: the cloaked player's own
// client has the In Plain Sight screen instead.
function cloak_fx_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( !isdefined( self.tod_cloak_fx ) ) self.tod_cloak_fx = [];
	if ( isdefined( self.tod_cloak_fx[ localClientNum ] ) )
	{
		KillFX( localClientNum, self.tod_cloak_fx[ localClientNum ] );
		self.tod_cloak_fx[ localClientNum ] = undefined;
	}
	if ( newVal != 1 ) return;
	if ( self == GetLocalPlayer( localClientNum ) ) return;
	self.tod_cloak_fx[ localClientNum ] = PlayFXOnTag( localClientNum, level._effect[ "tod_cloak_aura" ], self, TOD_CLOAK_AURA_TAG );
}
