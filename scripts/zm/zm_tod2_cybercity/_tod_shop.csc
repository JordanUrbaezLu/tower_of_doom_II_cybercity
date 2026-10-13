// Client emission, native mesh sparks, positional audio and stock sky indication.
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;
#using scripts\zm\zm_tod2_cybercity\_tod_shop_timing;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#precache( "client_fx", "tod/shop/fx_tod_shop_spark" );
#precache( "client_fx", "zombie/fx_wonder_fizz_lightning_all" );
#namespace tod_shop;
REGISTER_SYSTEM( "tod_shop", &__init__, undefined )
function __init__()
{
    clientfield::register( "scriptmover", "todShopPart", VERSION_SHIP, 5, "int", &part_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
}
function part_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
    self notify( "shop_stop_" + localClientNum );
    // PK23: the hut's hum ends by its handle (StopSounds below does not own a loop)
    if ( isdefined( self.shop_hum ) && isdefined( self.shop_hum[ localClientNum ] ) )
    { self StopLoopSound( self.shop_hum[ localClientNum ] ); self.shop_hum[ localClientNum ] = undefined; }
    if ( isdefined( self.shop_sky ) && isdefined( self.shop_sky[ localClientNum ] ) )
    { StopFX( localClientNum, self.shop_sky[ localClientNum ] ); self.shop_sky[ localClientNum ] = undefined; }
    if ( isdefined( self.shop_bursts ) && isdefined( self.shop_bursts[ localClientNum ] ) )
        foreach ( fx in self.shop_bursts[ localClientNum ] ) if ( isdefined( fx ) ) StopFX( localClientNum, fx );
    self StopSounds();
    if ( !isdefined( newVal ) || newVal == 0 )
    {
        self MapShaderConstant( localClientNum, 0, "hdrScale", 0, 0, 0, 0 );
        if ( isdefined( oldVal ) && oldVal >= 16 && oldVal % 16 == 1 )
            log( true, "OFF client=" + localClientNum + " ent=" + self GetEntityNumber() + " marker_stopped=1 sounds_stopped=1" );
        return;
    }
    self thread animate( localClientNum, newVal % 16, newVal >= 16 );
}
function animate( localClientNum, kind, debug )
{
    self endon( "entityshutdown" ); self endon( "shop_stop_" + localClientNum );
    self util::waittill_dobj( localClientNum );
    if ( !isdefined( self ) ) return;
    self MapShaderConstant( localClientNum, 0, "hdrScale", 6, 0, 0, 0 );
    events = tod_shop_timing::events();
    hum = undefined; hum_bus = -1;
    if ( kind == 1 )
    {
        DEFAULT( self.shop_sky, [] ); DEFAULT( self.shop_bursts, [] ); self.shop_bursts[ localClientNum ] = [];
        sky = PlayFXOnTag( localClientNum, "zombie/fx_wonder_fizz_lightning_all", self, "tag_origin" );
        self.shop_sky[ localClientNum ] = sky;
        self thread sky_shutdown( localClientNum, sky );
        log( debug, "ACTIVE client=" + localClientNum + " ent=" + self GetEntityNumber() + " marker=" + isdefined( sky ) + " server_ms=" + GetServerTime( localClientNum ) );
        // PK23 (2026-10-05): THE HUT HUMS - its neon ballast's 60 Hz buzz with a faint tube sizzle (3D, tod_amb.csv),
        // the active marker only (one hum per live shop); it drops out with the sign on every supply fault below
        DEFAULT( self.shop_hum, [] );
        hum = self PlayLoopSound( "tod_shop_hum", 1 );
        self.shop_hum[ localClientNum ] = hum;
        if ( isdefined( hum ) ) SetSoundVolumeRate( hum, 6 );
    }
    last_tick = int( GetServerTime( localClientNum ) * 0.03 ); reported = 0;
    while ( true )
    {
        ms = GetServerTime( localClientNum ); tick = int( ms * 0.03 ); frame = ( tick % 180 ) + 1;
        value = brightness( kind, frame );
        self SetShaderConstant( localClientNum, 0, 6 * value, 0, 0, 0 );
        // PK23: the buzz cuts out with the light (the same power_bus frames that drop the sign)
        if ( isdefined( hum ) )
        {
            bus = tod_shop_timing::power_bus( frame );
            if ( bus != hum_bus ) { hum_bus = bus; SetSoundVolume( hum, ( bus == 1 ? 1 : 0.15 ) ); }
        }
        if ( kind == 1 && tick > last_tick && tick - last_tick < 8 )
        {
            // Crossed-frame test catches render jitter without replaying missed history.
            for ( t = last_tick + 1; t <= tick; t++ )
            {
                f = ( t % 180 ) + 1;
                for ( i = 0; i < events.size; i++ )
                {
                    if ( events[ i ].frame != f ) continue;
                    org = local_to_world( self.origin, self.angles[ 1 ], events[ i ].org );
                    fx = PlayFX( localClientNum, "tod/shop/fx_tod_shop_spark", org, AnglesToForward( self.angles ), AnglesToUp( self.angles ) );
                    self.shop_bursts[ localClientNum ][ i ] = fx;
                    // One sound per shared fault, not four stacked copies of the same transient.
                    if ( events[ i ].sound != "" ) self PlaySound( localClientNum, events[ i ].sound, org );
                    if ( reported < 10 ) { log( debug, "SYNC rev=2 client=" + localClientNum + " frame=" + f + " bus=" + tod_shop_timing::power_bus( f ) + " event=" + i + " site=" + events[ i ].site + " sound=" + events[ i ].sound + " org=" + org ); reported++; }
                }
            }
        }
        last_tick = tick;
        wait 0.0166667;
    }
}
function brightness( kind, frame )
{
    if ( kind >= 2 && kind <= 4 ) return tod_shop_timing::letter( kind, frame );
    // Supply faults happen together, regardless of the slower pulse/chase beneath them.
    if ( kind >= 6 && kind <= 12 && tod_shop_timing::power_bus( frame ) == 0 ) return 0;
    phase = ( frame - 1 ) * 360.0 / 180;
    if ( kind == 5 ) return ( 0.08 + 3.02 * ( 0.5 + 0.5 * Cos( phase ) ) ) / 3.1;
    if ( kind == 6 ) return ( 1.05 + 2.25 * ( 0.5 + 0.5 * Cos( 2 * phase ) ) ) / 3.3;
    if ( kind == 7 ) return ( 0.45 + 2.05 * ( 0.5 + 0.5 * Cos( 2 * phase ) ) ) / 2.5;
    if ( kind == 8 ) return ( 1.15 + 1.95 * ( 0.5 + 0.5 * Cos( 2 * phase ) ) ) / 3.1;
    if ( kind >= 9 && kind <= 12 ) return ( 0.15 + 2.85 * ( 0.5 + 0.5 * Cos( 2 * phase + ( kind - 9 ) * 72 ) ) ) / 3;
    return 1;
}
function local_to_world( origin, yaw, p )
{
    return origin + ( p[ 0 ] * Cos( yaw ) - p[ 1 ] * Sin( yaw ), p[ 0 ] * Sin( yaw ) + p[ 1 ] * Cos( yaw ), p[ 2 ] );
}
function sky_shutdown( localClientNum, fx )
{
    self endon( "shop_stop_" + localClientNum );
    self waittill( "entityshutdown" );
    if ( isdefined( fx ) ) StopFX( localClientNum, fx );
}
function log( enabled, msg )
{
    if ( !enabled ) return;
    line = "[TOD_SHOP_C] " + msg;
    /#
    PrintLn( line );
    #/
}
