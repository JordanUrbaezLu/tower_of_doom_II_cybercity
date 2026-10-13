// =============================================================================
// _tod_ability_fx.csc - THE ABILITY FEEDBACK, client half (docs/203, 2026-10-02).
//
// Draws every ability event _tod_ability_fx.gsc sends, in the right view:
//   * self == the local player: the FIRST-PERSON half (PlayViewmodelFX on the held
//     weapon, PlayFXOnCamera, nothing bright at the camera - the Soul Pulse's
//     caster flash whitened the view once, docs/necro_visibility_fix.md);
//   * otherwise: the BODY half on the caster (PlayFXOnTag on j_spine4 / tag_origin)
//     a teammate reads from across the hall. The local player's body half plays
//     too where it lights the world (a light on the floor around you).
// World bursts (the Bash shockwave, the Soul Pulse dome, the Fusion launch and
// landing) play at the caster's origin in the donor's own frame (forward X, up Z:
// PlayFX( org, ( 1, 0, 0 ), ( 0, 0, 1 ) ) = what PlayFXOnTag on an upright
// tag_origin gives the stock slam).
//
// Looping body states ride "tod_abfx_state" (bits): the DEMON aura + light, the
// FUSION air trail (re-triggered every 0.4 s while the bit holds, so a one-shot
// donor reads as a trail). Every handle is kept per local client and killed on
// the state's fall or the entity's shutdown.
//
// THE SECOND PASS (docs/206, 2026-10-03): the dive streak (a state) + the charged blade's
// glow on the sword hand (a state), the cloak / card / shield / charged one-shots on the BODY
// for the others (never sprites at the local camera: the 1p rule, twice earned), the full-draw
// viewmodel glow for the caster, and THE ACTOR HIT LANE (tod_abfx_hitk + tod_abfx_hit): the
// pierce flesh hit, the Retriever's impact and the Rune Prison's torso fire drawn on the zombie
// (a server PlayFXOnTag on an actor does not render here).
//
// LOCKSTEP _tod_ability_fx.gsc: the kind table, the state bits, the hit kinds, the six fields
// (same names / sizes / order). The effects: tools/ability_fx/gen_fx.py.
// LOGS: [TOD_ABFX_C] (TOD_ABFX_C_LOG 1 - zero before a publish).
// =============================================================================
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#precache( "client_fx", "tod/abfx/fx_abfx_dash_sword" );
#precache( "client_fx", "tod/abfx/fx_abfx_dash_gauntlet" );
#precache( "client_fx", "tod/abfx/fx_abfx_dash_punch" );
#precache( "client_fx", "tod/abfx/fx_abfx_dash_vm" );
#precache( "client_fx", "tod/abfx/fx_abfx_bash_impact" );
#precache( "client_fx", "tod/abfx/fx_abfx_bash_impact_lv9" );
#precache( "client_fx", "tod/abfx/fx_abfx_bash_1p" );
#precache( "client_fx", "tod/abfx/fx_abfx_pulse_dome0" );
#precache( "client_fx", "tod/abfx/fx_abfx_pulse_dome1" );
#precache( "client_fx", "tod/abfx/fx_abfx_pulse_dome2" );
#precache( "client_fx", "tod/abfx/fx_abfx_pulse_dome3" );
#precache( "client_fx", "tod/abfx/fx_abfx_pulse_1p" );
#precache( "client_fx", "tod/abfx/fx_abfx_fusion_launch" );
#precache( "client_fx", "tod/abfx/fx_abfx_fusion_trail" );
#precache( "client_fx", "tod/abfx/fx_abfx_fusion_land" );
#precache( "client_fx", "tod/abfx/fx_abfx_fusion_heal" );
#precache( "client_fx", "tod/abfx/fx_abfx_fusion_heal_1p" );
#precache( "client_fx", "tod/abfx/fx_abfx_demon_aura" );
#precache( "client_fx", "tod/abfx/fx_abfx_demon_light" );
#precache( "client_fx", "tod/abfx/fx_abfx_demon_on" );
#precache( "client_fx", "tod/abfx/fx_abfx_demon_on_1p" );
#precache( "client_fx", "tod/necro/fx_necro_soul_rip" );   // an elite struck by the Soul Pulse (the necro's own rip)
// docs/206
#precache( "client_fx", "tod/abfx/fx_abfx_dive_trail" );
#precache( "client_fx", "tod/abfx/fx_abfx_sword_glow" );
#precache( "client_fx", "tod/abfx/fx_abfx_sword_charged" );
#precache( "client_fx", "tod/abfx/fx_abfx_cloak_on" );
#precache( "client_fx", "tod/abfx/fx_abfx_cloak_off" );
#precache( "client_fx", "tod/abfx/fx_abfx_card_1" );
#precache( "client_fx", "tod/abfx/fx_abfx_card_2" );
#precache( "client_fx", "tod/abfx/fx_abfx_card_3" );
#precache( "client_fx", "tod/abfx/fx_abfx_card_4" );
#precache( "client_fx", "tod/abfx/fx_abfx_card_light" );
#precache( "client_fx", "tod/abfx/fx_abfx_shield_break" );
#precache( "client_fx", "tod/abfx/fx_abfx_shield_back" );
#precache( "client_fx", "tod/abfx/fx_abfx_draw_vm" );
#precache( "client_fx", "tod/abfx/fx_abfx_pierce" );
#precache( "client_fx", "tod/archer/fx_tod_archer_impact" );               // the Retriever's hit, on the zombie
#precache( "client_fx", "dlc1/zmb_weapon/fx_bow_rune_fire_torso_zmb" );   // the Rune Prison's torso fire, on the zombie

#namespace tod_ability_fx;

#define TOD_ABFX_C_LOG             1   // 1 = log every event; 0 before a publish

// LOCKSTEP .gsc
#define TOD_ABFX_DASH_SWORD        1
#define TOD_ABFX_DASH_GAUNTLET     2
#define TOD_ABFX_DASH_PUNCH        3
#define TOD_ABFX_BASH_IMPACT       4
#define TOD_ABFX_BASH_IMPACT_LV9   5
#define TOD_ABFX_PULSE_0           6
#define TOD_ABFX_PULSE_3           9
#define TOD_ABFX_FUSION_HEAL      10
#define TOD_ABFX_FUSION_LAUNCH    11
#define TOD_ABFX_FUSION_LAND      12
#define TOD_ABFX_DEMON_ON         13
#define TOD_ABFX_DEMON_OFF        14
#define TOD_ABFX_CLOAK_ON         15
#define TOD_ABFX_CLOAK_OFF        16
#define TOD_ABFX_CARD_1           17
#define TOD_ABFX_CARD_4           20
#define TOD_ABFX_SHIELD_BREAK     21
#define TOD_ABFX_SHIELD_BACK      22
#define TOD_ABFX_SWORD_CHARGED    23
#define TOD_ABFX_DRAW_FULL        24
#define TOD_ABFX_KIND_BITS         5
#define TOD_ABFX_STATE_DEMON       1
#define TOD_ABFX_STATE_AIR         2
#define TOD_ABFX_STATE_DIVE        4
#define TOD_ABFX_STATE_SWORD       8
#define TOD_ABFX_STATE_BITS        4
#define TOD_ABFX_HIT_PIERCE        1
#define TOD_ABFX_HIT_AXE           2
#define TOD_ABFX_HIT_BURN          3
#define TOD_ABFX_HIT_BITS          2
#define TOD_ABFX_BURN_SECS         4.0

#define TOD_ABFX_DASH_SECS         0.55   // the streak outlives the 400 ms dash by a hair, then dies
#define TOD_ABFX_TRAIL_STEP        0.4    // the air trail is re-triggered this often while the bit holds
#define TOD_ABFX_BODY_TAG          "j_spine4"
#define TOD_ABFX_LIGHT_TAG         "j_spineupper"
#define TOD_ABFX_DIVE_STEP         0.3    // the dive streak is re-triggered this often while the bit holds (docs/206)
#define TOD_ABFX_SWORD_TAG         "tag_weapon_right"   // the blade hand (body_fx falls back to tag_origin)

REGISTER_SYSTEM( "tod_ability_fx", &__init__, undefined )
function __init__()
{
	level._effect[ "tod_abfx_dash_1" ]       = "tod/abfx/fx_abfx_dash_sword";
	level._effect[ "tod_abfx_dash_2" ]       = "tod/abfx/fx_abfx_dash_gauntlet";
	level._effect[ "tod_abfx_dash_3" ]       = "tod/abfx/fx_abfx_dash_punch";
	level._effect[ "tod_abfx_dash_vm" ]      = "tod/abfx/fx_abfx_dash_vm";
	level._effect[ "tod_abfx_impact_4" ]     = "tod/abfx/fx_abfx_bash_impact";
	level._effect[ "tod_abfx_impact_5" ]     = "tod/abfx/fx_abfx_bash_impact_lv9";
	level._effect[ "tod_abfx_bash_1p" ]      = "tod/abfx/fx_abfx_bash_1p";
	level._effect[ "tod_abfx_dome_0" ]       = "tod/abfx/fx_abfx_pulse_dome0";
	level._effect[ "tod_abfx_dome_1" ]       = "tod/abfx/fx_abfx_pulse_dome1";
	level._effect[ "tod_abfx_dome_2" ]       = "tod/abfx/fx_abfx_pulse_dome2";
	level._effect[ "tod_abfx_dome_3" ]       = "tod/abfx/fx_abfx_pulse_dome3";
	level._effect[ "tod_abfx_pulse_1p" ]     = "tod/abfx/fx_abfx_pulse_1p";
	level._effect[ "tod_abfx_launch" ]       = "tod/abfx/fx_abfx_fusion_launch";
	level._effect[ "tod_abfx_trail" ]        = "tod/abfx/fx_abfx_fusion_trail";
	level._effect[ "tod_abfx_land" ]         = "tod/abfx/fx_abfx_fusion_land";
	level._effect[ "tod_abfx_heal" ]         = "tod/abfx/fx_abfx_fusion_heal";
	level._effect[ "tod_abfx_heal_1p" ]      = "tod/abfx/fx_abfx_fusion_heal_1p";
	level._effect[ "tod_abfx_demon_aura" ]   = "tod/abfx/fx_abfx_demon_aura";
	level._effect[ "tod_abfx_demon_light" ]  = "tod/abfx/fx_abfx_demon_light";
	level._effect[ "tod_abfx_demon_on" ]     = "tod/abfx/fx_abfx_demon_on";
	level._effect[ "tod_abfx_demon_on_1p" ]  = "tod/abfx/fx_abfx_demon_on_1p";
	level._effect[ "tod_abfx_soul" ]         = "tod/necro/fx_necro_soul_rip";
	// docs/206
	level._effect[ "tod_abfx_dive_trail" ]   = "tod/abfx/fx_abfx_dive_trail";
	level._effect[ "tod_abfx_sword_glow" ]   = "tod/abfx/fx_abfx_sword_glow";
	level._effect[ "tod_abfx_sword_charged" ] = "tod/abfx/fx_abfx_sword_charged";
	level._effect[ "tod_abfx_cloak_on" ]     = "tod/abfx/fx_abfx_cloak_on";
	level._effect[ "tod_abfx_cloak_off" ]    = "tod/abfx/fx_abfx_cloak_off";
	level._effect[ "tod_abfx_card_1" ]       = "tod/abfx/fx_abfx_card_1";
	level._effect[ "tod_abfx_card_2" ]       = "tod/abfx/fx_abfx_card_2";
	level._effect[ "tod_abfx_card_3" ]       = "tod/abfx/fx_abfx_card_3";
	level._effect[ "tod_abfx_card_4" ]       = "tod/abfx/fx_abfx_card_4";
	level._effect[ "tod_abfx_card_light" ]   = "tod/abfx/fx_abfx_card_light";
	level._effect[ "tod_abfx_shield_break" ] = "tod/abfx/fx_abfx_shield_break";
	level._effect[ "tod_abfx_shield_back" ]  = "tod/abfx/fx_abfx_shield_back";
	level._effect[ "tod_abfx_draw_vm" ]      = "tod/abfx/fx_abfx_draw_vm";
	level._effect[ "tod_abfx_pierce" ]       = "tod/abfx/fx_abfx_pierce";
	level._effect[ "tod_abfx_hit_axe" ]      = "tod/archer/fx_tod_archer_impact";
	level._effect[ "tod_abfx_burn" ]         = "dlc1/zmb_weapon/fx_bow_rune_fire_torso_zmb";
	clientfield::register( "allplayers", "tod_abfx_kind", VERSION_SHIP, TOD_ABFX_KIND_BITS, "int", undefined, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );   // applied BEFORE the counter (LOCKSTEP gsc)
	clientfield::register( "allplayers", "tod_abfx", VERSION_SHIP, 1, "counter", &abfx_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "allplayers", "tod_abfx_state", VERSION_SHIP, TOD_ABFX_STATE_BITS, "int", &state_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "actor", "tod_abfx_soul", VERSION_SHIP, 1, "counter", &soul_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "actor", "tod_abfx_hitk", VERSION_SHIP, TOD_ABFX_HIT_BITS, "int", undefined, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );   // applied BEFORE the hit counter (LOCKSTEP gsc)
	clientfield::register( "actor", "tod_abfx_hit", VERSION_SHIP, 1, "counter", &hit_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
}

// =============================================================================
// THE EVENT
// =============================================================================
function abfx_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( bNewEnt || bInitialSnap ) return;
	self thread abfx_play( lc, self.origin );
}

function abfx_play( lc, origin )   // self = the caster
{
	self endon( "entityshutdown" );
	// A callback can precede the other field's application in the same snapshot (the
	// Soul Pulse band's lesson): finish the snapshot before reading the kind. The world
	// bursts keep the cast origin, never the caster's later position.
	wait 0.05;
	if ( !isdefined( self ) ) return;
	kind = self clientfield::get( "tod_abfx_kind" );
	if ( !isdefined( kind ) || kind <= 0 ) return;
	local = ( self == GetLocalPlayer( lc ) );
	if ( kind >= TOD_ABFX_DASH_SWORD && kind <= TOD_ABFX_DASH_PUNCH )
	{
		h = self body_fx( lc, "tod_abfx_dash_" + kind, TOD_ABFX_BODY_TAG );
		if ( isdefined( h ) ) self thread kill_after( lc, h, TOD_ABFX_DASH_SECS );
		if ( local ) PlayViewmodelFX( lc, level._effect[ "tod_abfx_dash_vm" ], "tag_weapon" );
	}
	else if ( kind == TOD_ABFX_BASH_IMPACT || kind == TOD_ABFX_BASH_IMPACT_LV9 )
	{
		PlayFX( lc, level._effect[ "tod_abfx_impact_" + kind ], origin + ( 0, 0, 2 ), ( 1, 0, 0 ), ( 0, 0, 1 ) );
		if ( local ) PlayFXOnCamera( lc, level._effect[ "tod_abfx_bash_1p" ] );
	}
	else if ( kind >= TOD_ABFX_PULSE_0 && kind <= TOD_ABFX_PULSE_3 )
	{
		PlayFX( lc, level._effect[ "tod_abfx_dome_" + ( kind - TOD_ABFX_PULSE_0 ) ], origin + ( 0, 0, 8 ), ( 1, 0, 0 ), ( 0, 0, 1 ) );
		if ( local ) PlayFXOnCamera( lc, level._effect[ "tod_abfx_pulse_1p" ] );
	}
	else if ( kind == TOD_ABFX_FUSION_HEAL )
	{
		self body_fx( lc, "tod_abfx_heal", TOD_ABFX_BODY_TAG );
		if ( local ) PlayViewmodelFX( lc, level._effect[ "tod_abfx_heal_1p" ], "tag_origin" );
	}
	else if ( kind == TOD_ABFX_FUSION_LAUNCH )
	{
		PlayFX( lc, level._effect[ "tod_abfx_launch" ], origin + ( 0, 0, 2 ), ( 1, 0, 0 ), ( 0, 0, 1 ) );
	}
	else if ( kind == TOD_ABFX_FUSION_LAND )
	{
		PlayFX( lc, level._effect[ "tod_abfx_land" ], origin + ( 0, 0, 2 ), ( 1, 0, 0 ), ( 0, 0, 1 ) );
	}
	else if ( kind == TOD_ABFX_DEMON_ON )
	{
		self body_fx( lc, "tod_abfx_demon_on", TOD_ABFX_BODY_TAG );
		if ( local ) PlayViewmodelFX( lc, level._effect[ "tod_abfx_demon_on_1p" ], "tag_origin" );
	}
	// ---- docs/206 ----
	// the one-shots on the BODY are for the others: a sprite burst at the chest sits inches from the local
	// camera (the 1p rule); the caster has the sound, the HUD, the vision set or the viewmodel half
	else if ( kind == TOD_ABFX_CLOAK_ON || kind == TOD_ABFX_CLOAK_OFF )
	{
		if ( !local ) self body_fx( lc, ( kind == TOD_ABFX_CLOAK_ON ? "tod_abfx_cloak_on" : "tod_abfx_cloak_off" ), TOD_ABFX_BODY_TAG );
	}
	else if ( kind >= TOD_ABFX_CARD_1 && kind <= TOD_ABFX_CARD_4 )
	{
		r = kind - TOD_ABFX_CARD_1 + 1;
		if ( !local ) self body_fx( lc, "tod_abfx_card_" + r, TOD_ABFX_BODY_TAG );
		if ( r == 4 ) self body_fx( lc, "tod_abfx_card_light", TOD_ABFX_LIGHT_TAG );   // the LEGENDARY's gold light reaches the floor round you too
	}
	else if ( kind == TOD_ABFX_SHIELD_BREAK )
	{
		if ( !local ) self body_fx( lc, "tod_abfx_shield_break", TOD_ABFX_BODY_TAG );
	}
	else if ( kind == TOD_ABFX_SHIELD_BACK )
	{
		if ( !local ) self body_fx( lc, "tod_abfx_shield_back", TOD_ABFX_BODY_TAG );
	}
	else if ( kind == TOD_ABFX_SWORD_CHARGED )
	{
		if ( !local ) self body_fx( lc, "tod_abfx_sword_charged", TOD_ABFX_SWORD_TAG );   // the caster's own blade brightens (_tod_cyber_sword.csc)
	}
	else if ( kind == TOD_ABFX_DRAW_FULL )
	{
		if ( local ) PlayViewmodelFX( lc, level._effect[ "tod_abfx_draw_vm" ], "tag_flash" );
	}
	// TOD_ABFX_DEMON_OFF: the aura's fall (state_cb) and the server's sound are the tell
	c_log( "EVENT kind=" + kind + " ent=" + self GetEntityNumber() + " local=" + local + " org=" + origin );
}

// =============================================================================
// THE BODY STATES
// =============================================================================
function state_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( !isdefined( oldVal ) ) oldVal = 0;
	demon_was = ( ( oldVal & TOD_ABFX_STATE_DEMON ) != 0 );
	demon_now = ( ( newVal & TOD_ABFX_STATE_DEMON ) != 0 );
	air_was = ( ( oldVal & TOD_ABFX_STATE_AIR ) != 0 );
	air_now = ( ( newVal & TOD_ABFX_STATE_AIR ) != 0 );
	if ( demon_now && !demon_was ) self demon_start( lc );
	else if ( !demon_now && demon_was ) self demon_stop( lc );
	if ( air_now && !air_was ) self thread trail_run( lc );
	else if ( !air_now && air_was ) self trail_stop( lc );
	// docs/206
	dive_was = ( ( oldVal & TOD_ABFX_STATE_DIVE ) != 0 );
	dive_now = ( ( newVal & TOD_ABFX_STATE_DIVE ) != 0 );
	sword_was = ( ( oldVal & TOD_ABFX_STATE_SWORD ) != 0 );
	sword_now = ( ( newVal & TOD_ABFX_STATE_SWORD ) != 0 );
	if ( dive_now && !dive_was ) self thread dive_run( lc );
	else if ( !dive_now && dive_was ) self dive_stop( lc );
	if ( sword_now && !sword_was ) self sword_start( lc );
	else if ( !sword_now && sword_was ) self sword_stop( lc );
	c_log( "STATE ent=" + self GetEntityNumber() + " value=" + newVal + " demon=" + demon_now + " air=" + air_now + " dive=" + dive_now + " sword=" + sword_now + " snap=" + bInitialSnap );
}

function demon_start( lc )
{
	self demon_stop( lc );
	DEFAULT( self.tod_abfx_demon_fx, [] );
	DEFAULT( self.tod_abfx_demon_lt, [] );
	self.tod_abfx_demon_fx[ lc ] = self body_fx( lc, "tod_abfx_demon_aura", TOD_ABFX_BODY_TAG );
	self.tod_abfx_demon_lt[ lc ] = self body_fx( lc, "tod_abfx_demon_light", TOD_ABFX_LIGHT_TAG );
}

function demon_stop( lc )
{
	if ( isdefined( self.tod_abfx_demon_fx ) && isdefined( self.tod_abfx_demon_fx[ lc ] ) )
	{
		KillFX( lc, self.tod_abfx_demon_fx[ lc ] );
		self.tod_abfx_demon_fx[ lc ] = undefined;
	}
	if ( isdefined( self.tod_abfx_demon_lt ) && isdefined( self.tod_abfx_demon_lt[ lc ] ) )
	{
		KillFX( lc, self.tod_abfx_demon_lt[ lc ] );
		self.tod_abfx_demon_lt[ lc ] = undefined;
	}
}

function trail_run( lc )   // self = the flying Breacher
{
	self notify( "tod_abfx_trail_" + lc );
	self endon( "tod_abfx_trail_" + lc );
	self endon( "entityshutdown" );
	DEFAULT( self.tod_abfx_trail, [] );
	for ( ;; )
	{
		self trail_kill( lc );
		self.tod_abfx_trail[ lc ] = self body_fx( lc, "tod_abfx_trail", TOD_ABFX_BODY_TAG );
		wait TOD_ABFX_TRAIL_STEP;
	}
}

function trail_stop( lc )
{
	self notify( "tod_abfx_trail_" + lc );
	self trail_kill( lc );
}

function trail_kill( lc )
{
	if ( isdefined( self.tod_abfx_trail ) && isdefined( self.tod_abfx_trail[ lc ] ) )
	{
		KillFX( lc, self.tod_abfx_trail[ lc ] );
		self.tod_abfx_trail[ lc ] = undefined;
	}
}

// docs/206: THE DIVE STREAK (the Fusion trail's shape in the Warrior's cyan) while the dive bit holds
function dive_run( lc )   // self = the diving Warrior
{
	self notify( "tod_abfx_dive_" + lc );
	self endon( "tod_abfx_dive_" + lc );
	self endon( "entityshutdown" );
	DEFAULT( self.tod_abfx_dive, [] );
	for ( ;; )
	{
		self dive_kill( lc );
		self.tod_abfx_dive[ lc ] = self body_fx( lc, "tod_abfx_dive_trail", TOD_ABFX_BODY_TAG );
		wait TOD_ABFX_DIVE_STEP;
	}
}

function dive_stop( lc )
{
	self notify( "tod_abfx_dive_" + lc );
	self dive_kill( lc );
}

function dive_kill( lc )
{
	if ( isdefined( self.tod_abfx_dive ) && isdefined( self.tod_abfx_dive[ lc ] ) )
	{
		KillFX( lc, self.tod_abfx_dive[ lc ] );
		self.tod_abfx_dive[ lc ] = undefined;
	}
}

// docs/206: THE CHARGED BLADE's glow on the sword hand, for the others (the caster's blade brightens through
// _tod_cyber_sword.csc; a glow at the local hand would sit in the camera's corner)
function sword_start( lc )
{
	self sword_stop( lc );
	if ( self == GetLocalPlayer( lc ) ) return;
	DEFAULT( self.tod_abfx_sword, [] );
	self.tod_abfx_sword[ lc ] = self body_fx( lc, "tod_abfx_sword_glow", TOD_ABFX_SWORD_TAG );
}

function sword_stop( lc )
{
	if ( isdefined( self.tod_abfx_sword ) && isdefined( self.tod_abfx_sword[ lc ] ) )
	{
		KillFX( lc, self.tod_abfx_sword[ lc ] );
		self.tod_abfx_sword[ lc ] = undefined;
	}
}

// =============================================================================
// AN ELITE STRUCK BY THE SOUL PULSE: the soul-rip flash at the chest and the head
// =============================================================================
function soul_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( bNewEnt || bInitialSnap ) return;
	self body_fx( lc, "tod_abfx_soul", "j_spine4" );
	self body_fx( lc, "tod_abfx_soul", "j_head" );
	self PlaySound( lc, "evt_zombie_skull_breathe" );
}

// =============================================================================
// docs/206: A ZOMBIE STRUCK (the actor hit lane): the kind field is read after the snapshot settles
// =============================================================================
function hit_cb( lc, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( bNewEnt || bInitialSnap ) return;
	self thread hit_play( lc );
}

function hit_play( lc )   // self = the struck zombie
{
	self endon( "entityshutdown" );
	wait 0.05;   // abfx_play's rule: the kind field settles with the snapshot
	if ( !isdefined( self ) ) return;
	kind = self clientfield::get( "tod_abfx_hitk" );
	if ( !isdefined( kind ) || kind <= 0 ) return;
	if ( kind == TOD_ABFX_HIT_PIERCE ) self body_fx( lc, "tod_abfx_pierce", TOD_ABFX_BODY_TAG );
	else if ( kind == TOD_ABFX_HIT_AXE ) self body_fx( lc, "tod_abfx_hit_axe", TOD_ABFX_BODY_TAG );
	else if ( kind == TOD_ABFX_HIT_BURN )
	{
		h = self body_fx( lc, "tod_abfx_burn", TOD_ABFX_LIGHT_TAG );   // the torso; the fire ends with the prison
		if ( isdefined( h ) ) self thread kill_after( lc, h, TOD_ABFX_BURN_SECS );
	}
	c_log( "HIT kind=" + kind + " ent=" + self GetEntityNumber() );
}

// =============================================================================
// helpers
// =============================================================================
// a one-shot / looping effect on a bone of self, with the tag guard (a missing bone
// would be a script error on a model without it); -> the handle or undefined
function body_fx( lc, key, tag )
{
	if ( !isdefined( self ) ) return undefined;
	if ( !isdefined( self GetTagOrigin( tag ) ) ) tag = "tag_origin";
	if ( !isdefined( self GetTagOrigin( tag ) ) ) return undefined;
	return PlayFXOnTag( lc, level._effect[ key ], self, tag );
}

function kill_after( lc, h, secs )
{
	self endon( "entityshutdown" );
	wait secs;
	if ( isdefined( h ) ) KillFX( lc, h );
}

function c_log( msg )
{
	if ( !TOD_ABFX_C_LOG ) return;
	line = "[TOD_ABFX_C] " + msg;
	/#
	PrintLn( line );
	#/
}
