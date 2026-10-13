// Persistent first-person staff auras follow the CLIENT weapon change, like
// stock _zm_weap_riotshield / _zm_weap_raygun_mark3. Replicated elements can
// arrive after the viewmodel changes. Never use them to choose the aura.
// KillFX removes existing particles too; StopFX lets the old aura linger.

#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

// v18.93: the Origins tip glows at 125% (tools/bo6_extraction/build_bo6_ice_fx.py, user:
// "enhance the frost, flame and electricity fx on each staff ... like 25% more").
#precache( "client_fx", "tod/bo6/fx_tod_staff_glow_elec" );
#precache( "client_fx", "tod/bo6/fx_tod_staff_glow_fire" );
#precache( "client_fx", "tod/bo6/fx_tod_staff_glow_ice" );
#precache( "client_fx", "tod/mage/fx_staff_lightning_chain_clean" );

#define TOD_STAFF_GLOW_FIELD   "tod_staff_glow"   // LOCKSTEP with _tod_mage_elements.gsc
#define TOD_STAFF_GLOW_TAG     "tag_upg"          // the Origins staff view model's tip tag (tod_staff_view: tag_weapon / tag_upg / tag_antennea_le4)
#define TOD_STAFF_GLOW_TAG_ICE "tag_bo6_glow"     // v18.89: the BO6 ice assembly (tod_bo6_ice_vm) has no tag_upg; this socket sits in its tip crystal

#namespace tod_mage_elements;

REGISTER_SYSTEM( "tod_mage_elements", &__init__, undefined )

function __init__()
{
	level._effect[ "tod_staff_glow_1" ] = "tod/bo6/fx_tod_staff_glow_elec";
	level._effect[ "tod_staff_glow_2" ] = "tod/bo6/fx_tod_staff_glow_fire";
	level._effect[ "tod_staff_glow_3" ] = "tod/bo6/fx_tod_staff_glow_ice";
	level._effect[ "tod_mage_chain" ] = "tod/mage/fx_staff_lightning_chain_clean";

	// Preserve the server/client field layout. Late snapshots must not
	// restart an old aura; the local weapon owns presentation now.
	callback::on_spawned( &glow_on_spawned );
	clientfield::register( "toplayer", TOD_STAFF_GLOW_FIELD, VERSION_SHIP, 2, "int", undefined, !CF_HOST_ONLY, CF_CALLBACK_ZERO_ON_NEW_ENT );
	clientfield::register( "actor", "tod_mage_chain_fx", VERSION_SHIP, 2, "int", &chain_fx_cb, !CF_HOST_ONLY, CF_CALLBACK_ZERO_ON_NEW_ENT );
}

function chain_fx_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	self notify( "tod_mage_chain_refresh_" + localClientNum );
	self chain_fx_stop( localClientNum );
	if ( newVal <= 0 || !IsAlive( self ) )
		return;
	if ( !isdefined( self.tod_chain_fx ) )
		self.tod_chain_fx = [];
	self.tod_chain_fx[ localClientNum ] = PlayFXOnTag( localClientNum, level._effect[ "tod_mage_chain" ], self, "j_spineupper" );
	self thread chain_fx_cleanup( localClientNum );
}

function chain_fx_cleanup( localClientNum )
{
	self endon( "tod_mage_chain_refresh_" + localClientNum );
	self util::waittill_any_timeout( 1.5, "death", "entityshutdown" );
	self chain_fx_stop( localClientNum );
}

function chain_fx_stop( localClientNum )
{
	if ( isdefined( self.tod_chain_fx ) && isdefined( self.tod_chain_fx[ localClientNum ] ) )
	{
		KillFX( localClientNum, self.tod_chain_fx[ localClientNum ] );
		self.tod_chain_fx[ localClientNum ] = undefined;
	}
}

function glow_on_spawned( localClientNum )
{
	if ( self != GetLocalPlayer( localClientNum ) )
		return;

	self notify( "tod_staff_glow_restart" );
	self glow_stop( localClientNum );
	self thread glow_watch( localClientNum );
	self thread glow_cleanup( localClientNum );
}

function glow_watch( localClientNum )
{
	self endon( "tod_staff_glow_restart" );
	self endon( "tod_staff_glow_stop" );
	self endon( "death" );
	self endon( "disconnect" );
	self endon( "entityshutdown" );

	self glow_replace( localClientNum, GetCurrentWeapon( localClientNum ) );
	for ( ;; )
	{
		self waittill( "weapon_change", weapon );
		// Replace even for q0 <-> q1 of the same element: the viewmodel changes.
		// No settle timer or delayed callback can restore the previous aura.
		self glow_replace( localClientNum, weapon );
	}
}

function glow_cleanup( localClientNum )
{
	self endon( "tod_staff_glow_restart" );
	self util::waittill_any( "death", "disconnect", "entityshutdown" );
	self notify( "tod_staff_glow_stop" );
	self glow_stop( localClientNum );
}

function glow_stop( localClientNum )
{
	if ( isdefined( self.tod_staff_glow_fx ) )
	{
		KillFX( localClientNum, self.tod_staff_glow_fx );
		self.tod_staff_glow_fx = undefined;
	}
}

function glow_replace( localClientNum, weapon )
{
	self glow_stop( localClientNum );
	if ( self != GetLocalPlayer( localClientNum ) )
		return;
	val = staff_glow_value( weapon );
	if ( val == 0 )
		return;
	tag = ( ( val == 3 ) ? TOD_STAFF_GLOW_TAG_ICE : TOD_STAFF_GLOW_TAG );
	self.tod_staff_glow_fx = PlayViewmodelFX( localClientNum, level._effect[ "tod_staff_glow_" + val ], tag );
}

// Match the server's staff_element naming, including generated variants.
function staff_glow_value( weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) || !IsSubStr( weapon.name, "tod_staff_" ) )
		return 0;
	if ( IsSubStr( weapon.name, "lightning" ) )
		return 1;
	if ( IsSubStr( weapon.name, "fire" ) )
		return 2;
	if ( IsSubStr( weapon.name, "ice" ) )
		return 3;
	return 0;
}
