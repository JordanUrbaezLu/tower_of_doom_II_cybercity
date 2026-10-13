// STAGED. Matching native idle field; exact imported BO6 FX, not a recolor.
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#precache( "client_fx", "_t10/vending/fizz_idle" );
#namespace tod_wunderfizz_machine;

REGISTER_SYSTEM( "tod_wunderfizz_machine", &__init__, undefined )

function __init__()
{
    level._effect[ "tod_wunderfizz_idle" ] = "_t10/vending/fizz_idle";
    clientfield::register( "scriptmover", "todWunderfizzIdle", VERSION_SHIP, 1, "int", &idle_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
}

function idle_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
    self endon( "entityshutdown" );
    if ( !isdefined( self.tod_wf_idle_states ) ) self.tod_wf_idle_states = [];
    if ( !isdefined( self.tod_wf_idle_states[ localClientNum ] ) )
    {
        s = SpawnStruct();
        s.generation = 0;
        s.handle = undefined;
        self.tod_wf_idle_states[ localClientNum ] = s;
        // Detached state lets cleanup retain the handle after host loss.
        level thread idle_shutdown_watch( self, s, localClientNum );
    }
    s = self.tod_wf_idle_states[ localClientNum ];
    s.generation++;
    generation = s.generation;
    stop_idle( s, localClientNum );
    if ( !isdefined( newVal ) || newVal == 0 ) return;
    self util::waittill_dobj( localClientNum );
    // A power-off/rekick callback may arrive while the first one waits for
    // the model. It owns a newer generation; an old wait cannot relight it.
    if ( generation != s.generation ) return;
    s.handle = PlayFXOnTag( localClientNum, level._effect[ "tod_wunderfizz_idle" ], self, "body_jnt" );
}

function stop_idle( s, localClientNum )
{
    if ( !isdefined( s.handle ) ) return;
    StopFX( localClientNum, s.handle );
    s.handle = undefined;
}

function idle_shutdown_watch( host, s, localClientNum )
{
    host waittill( "entityshutdown" );
    s.generation++;
    stop_idle( s, localClientNum );
}
