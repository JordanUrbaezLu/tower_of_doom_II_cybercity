// =============================================================================
// _tod_amb.csc - THE WORLD AMBIENCE (PK23, 2026-10-05). CLIENT ONLY, no server half, no clientfields.
//
// Before this the open-air descent had no air: no wind 19,000 units up, no city below, and the Undercity at the
// end of the run (the Vault, the Conduit, the four wings) and the plaza had no room tone at all - the only beds
// were the music and the war's local fires. Every player's own game now carries:
//   * THE WIND (2D, a seamless 48 s stereo bed): full from TOD_AMB_WIND_Z_FULL up (the crown, the upper tower),
//     thinning toward the ground to TOD_AMB_WIND_FLOOR. Gusts (3D one-shots) sweep past high up now and then.
//   * THE FAR CITY (2D, a seamless 45 s stereo bed): rises as the party descends below TOD_AMB_CITY_Z_TOP, full
//     at the plaza. The two cross-fade by altitude (SetSoundVolume + a slow SetSoundVolumeRate, the stock lane).
//   * THE UNDERCITY: inside its rooms both beds fall silent (walls, a ceiling) and the room tone takes over -
//     3D loops at GENERATED anchors (_tod_amb_data.csc, from the map's zone volumes) with drips and pipe knocks at
//     random points inside the room the player stands in. The PLAZA plays its own street bed from its anchors.
//   * THE QUIET ROOMS (the Battle Arena, the Dealer's House and parlour) carry their own scores: no world bed.
// Every bed sits ~20 dB under the music (tod_amb.csv volumes); nothing here plays a 2D loop that cannot stop
// (each bed is a loop on a client script_origin, faded by volume, stopped by handle).
// Logs: [TOD_AMB] INIT / ROOM (on change) / EMIT (on change). TOD_AMB_LOG 0 before a publish.
// =============================================================================

#using scripts\shared\audio_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\system_shared;

#using scripts\zm\zm_tod2_cybercity\_tod_amb_data;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#namespace tod_amb;

#define TOD_AMB_ENABLED       1
#define TOD_AMB_LOG           1        // [TOD_AMB] records for the first playtests; 0 before a publish
#define TOD_AMB_TICK          0.25     // real seconds between judgements
#define TOD_AMB_WIND_Z_FULL   12000    // the wind is full at and above this height (the upper tower, the crown)
#define TOD_AMB_WIND_Z_LOW    600      // ...thinning down to its floor level here
#define TOD_AMB_WIND_FLOOR    0.3      // the wind's level on the ground (the plaza still has a breeze)
#define TOD_AMB_CITY_Z_TOP    9000     // the far city starts to rise below this
#define TOD_AMB_CITY_Z_FULL   1500     // ...full at and below this
#define TOD_AMB_FADE_RATE     0.6      // SetSoundVolumeRate: volume units per second (a full swing in ~1.7 s)
#define TOD_AMB_ROOM_PAD      64       // a room box counts this much past its walls / floor / top
#define TOD_AMB_EMIT_ON       2600     // a room-tone anchor runs while the player is this close (its loop reaches 1600)
#define TOD_AMB_EMIT_OFF      3000     // ...and stops beyond this (hysteresis)
#define TOD_AMB_GUST_MIN      9        // s between gusts (high up only)
#define TOD_AMB_GUST_MAX      22
#define TOD_AMB_GUST_WIND     0.6      // gusts only where the wind is at least this strong
#define TOD_AMB_GUST_R        750      // a gust passes this far from the player
#define TOD_AMB_DRIP_MIN      2.5      // s between drips (Undercity only)
#define TOD_AMB_DRIP_MAX      7
#define TOD_AMB_PIPE_MIN      9        // s between pipe knocks (Undercity only)
#define TOD_AMB_PIPE_MAX      24

REGISTER_SYSTEM( "tod_amb", &__init__, undefined )

function __init__()
{
	if ( !TOD_AMB_ENABLED )
		return;
	level.tod_amb_emit_live = [];
	callback::on_localclient_connect( &on_local_connect );
}

function on_local_connect( localClientNum )
{
	level thread run( localClientNum );
}

// PURE: the room kind at org ("undercity" / "plaza" / "quiet"), "" outside every room
function room_kind_at( org )
{
	kinds = tod_amb_data::room_kinds();
	mins = tod_amb_data::room_mins();
	maxs = tod_amb_data::room_maxs();
	for ( i = 0; i < kinds.size; i++ )
	{
		lo = mins[ i ];
		hi = maxs[ i ];
		if ( org[ 0 ] < lo[ 0 ] - TOD_AMB_ROOM_PAD || org[ 0 ] > hi[ 0 ] + TOD_AMB_ROOM_PAD ) continue;
		if ( org[ 1 ] < lo[ 1 ] - TOD_AMB_ROOM_PAD || org[ 1 ] > hi[ 1 ] + TOD_AMB_ROOM_PAD ) continue;
		if ( org[ 2 ] < lo[ 2 ] - TOD_AMB_ROOM_PAD || org[ 2 ] > hi[ 2 ] + TOD_AMB_ROOM_PAD ) continue;
		return kinds[ i ];
	}
	return "";
}

// PURE: the room index at org (the drips fall inside it), -1 outside
function room_index_at( org )
{
	mins = tod_amb_data::room_mins();
	maxs = tod_amb_data::room_maxs();
	for ( i = 0; i < mins.size; i++ )
	{
		lo = mins[ i ];
		hi = maxs[ i ];
		if ( org[ 0 ] >= lo[ 0 ] && org[ 0 ] <= hi[ 0 ] && org[ 1 ] >= lo[ 1 ] && org[ 1 ] <= hi[ 1 ] && org[ 2 ] >= lo[ 2 ] - TOD_AMB_ROOM_PAD && org[ 2 ] <= hi[ 2 ] + TOD_AMB_ROOM_PAD )
			return i;
	}
	return -1;
}

// PURE: ( wind, city, 0 ) - the two beds' levels (0..1) for a listener at org standing in a room of `kind`
function bed_levels( org, kind )
{
	if ( kind == "undercity" || kind == "quiet" )
		return ( 0, 0, 0 );
	z = org[ 2 ];
	u = ( z - TOD_AMB_WIND_Z_LOW ) / ( TOD_AMB_WIND_Z_FULL - TOD_AMB_WIND_Z_LOW );
	if ( u < 0 ) u = 0;
	if ( u > 1 ) u = 1;
	wind = TOD_AMB_WIND_FLOOR + ( 1 - TOD_AMB_WIND_FLOOR ) * u;
	c = ( TOD_AMB_CITY_Z_TOP - z ) / ( TOD_AMB_CITY_Z_TOP - TOD_AMB_CITY_Z_FULL );
	if ( c < 0 ) c = 0;
	if ( c > 1 ) c = 1;
	if ( kind == "plaza" )
	{
		wind = TOD_AMB_WIND_FLOOR;
		c = 1;
	}
	return ( wind, c, 0 );
}

function run( localClientNum )
{
	// the two 2D beds ride their own client script_origins (one loop each), faded by volume, never stopped by a
	// wait: a bed that should be silent is held at volume 0
	wind_host = Spawn( localClientNum, ( 0, 0, 0 ), "script_origin" );
	city_host = Spawn( localClientNum, ( 0, 0, 0 ), "script_origin" );
	wind = undefined;
	city = undefined;
	if ( isdefined( wind_host ) )
	{
		wind = wind_host PlayLoopSound( "tod_amb_tower_wind", 3 );
		if ( isdefined( wind ) ) SetSoundVolumeRate( wind, TOD_AMB_FADE_RATE );
	}
	if ( isdefined( city_host ) )
	{
		city = city_host PlayLoopSound( "tod_amb_city_far", 3 );
		if ( isdefined( city ) ) SetSoundVolumeRate( city, TOD_AMB_FADE_RATE );
	}
	amb_log( "INIT local=" + localClientNum + " rooms=" + tod_amb_data::room_count() + " anchors=" + tod_amb_data::emitter_count()
		+ " wind=" + isdefined( wind ) + " city=" + isdefined( city ) + " wind_full_z=" + TOD_AMB_WIND_Z_FULL + " city_full_z=" + TOD_AMB_CITY_Z_FULL );
	last_kind = "-";
	next_gust = GetRealTime() + 1000 * RandomFloatRange( TOD_AMB_GUST_MIN, TOD_AMB_GUST_MAX );
	next_drip = 0;
	next_pipe = 0;
	for ( ;; )
	{
		waitrealtime( TOD_AMB_TICK );   // a client `wait` counts frames: real time
		player = GetLocalPlayer( localClientNum );
		if ( !isdefined( player ) )
			continue;
		org = player.origin;
		kind = room_kind_at( org );
		lv = bed_levels( org, kind );
		if ( isdefined( wind ) ) SetSoundVolume( wind, lv[ 0 ] );
		if ( isdefined( city ) ) SetSoundVolume( city, lv[ 1 ] );
		if ( kind != last_kind )
		{
			amb_log( "ROOM local=" + localClientNum + " kind=" + ( kind == "" ? "open" : kind ) + " z=" + int( org[ 2 ] ) + " wind=" + lv[ 0 ] + " city=" + lv[ 1 ] );
			last_kind = kind;
		}
		if ( localClientNum == 0 )
			emitters( org );
		now = GetRealTime();
		// the gusts: high up, now and then, sweeping past
		if ( now >= next_gust )
		{
			next_gust = now + 1000 * RandomFloatRange( TOD_AMB_GUST_MIN, TOD_AMB_GUST_MAX );
			if ( lv[ 0 ] >= TOD_AMB_GUST_WIND )
			{
				yaw = RandomFloat( 360 );
				PlaySound( localClientNum, "tod_amb_gust", org + ( Cos( yaw ) * TOD_AMB_GUST_R, Sin( yaw ) * TOD_AMB_GUST_R, 120 ) );
			}
		}
		// the Undercity: drips and pipe knocks at random points inside the room the player stands in
		if ( kind == "undercity" )
		{
			i = room_index_at( org );
			if ( i >= 0 && now >= next_drip )
			{
				next_drip = now + 1000 * RandomFloatRange( TOD_AMB_DRIP_MIN, TOD_AMB_DRIP_MAX );
				PlaySound( localClientNum, "tod_amb_drip", room_point( i, 40, 260 ) );
			}
			if ( i >= 0 && now >= next_pipe )
			{
				next_pipe = now + 1000 * RandomFloatRange( TOD_AMB_PIPE_MIN, TOD_AMB_PIPE_MAX );
				PlaySound( localClientNum, "tod_amb_pipe", room_point( i, 120, 340 ) );
			}
		}
		else
		{
			next_drip = 0;   // the first drip comes soon after walking in
			next_pipe = now + 1000 * TOD_AMB_PIPE_MIN * 0.5;
		}
	}
}

// a random point inside room i, z between lo and hi above its floor (never above its top)
function room_point( i, z_lo, z_hi )
{
	mins = tod_amb_data::room_mins();
	maxs = tod_amb_data::room_maxs();
	lo = mins[ i ];
	hi = maxs[ i ];
	z = lo[ 2 ] + RandomFloatRange( z_lo, z_hi );
	if ( z > hi[ 2 ] - 16 ) z = hi[ 2 ] - 16;
	return ( RandomFloatRange( lo[ 0 ] + 48, hi[ 0 ] - 48 ), RandomFloatRange( lo[ 1 ] + 48, hi[ 1 ] - 48 ), z );
}

// the room-tone anchors: a 3D loop at a position (the war damage's proven lane), run only near the player
function emitters( org )
{
	kinds = tod_amb_data::emitter_kinds();
	orgs = tod_amb_data::emitter_orgs();
	changed = 0;
	for ( i = 0; i < kinds.size; i++ )
	{
		d = Distance( org, orgs[ i ] );
		on = IS_TRUE( level.tod_amb_emit_live[ i ] );
		if ( !on && d <= TOD_AMB_EMIT_ON )
		{
			if ( kinds[ i ] == "undercity" )
				audio::playloopat( "tod_amb_undercity_lp", orgs[ i ] );
			else
				audio::playloopat( "tod_amb_plaza_lp", orgs[ i ] );
			level.tod_amb_emit_live[ i ] = true;
			changed++;
		}
		else if ( on && d > TOD_AMB_EMIT_OFF )
		{
			if ( kinds[ i ] == "undercity" )
				audio::stoploopat( "tod_amb_undercity_lp", orgs[ i ] );
			else
				audio::stoploopat( "tod_amb_plaza_lp", orgs[ i ] );
			level.tod_amb_emit_live[ i ] = false;
			changed++;
		}
	}
	if ( changed )
	{
		live = 0;
		for ( i = 0; i < kinds.size; i++ )
			if ( IS_TRUE( level.tod_amb_emit_live[ i ] ) )
				live++;
		amb_log( "EMIT changed=" + changed + " live=" + live + "/" + kinds.size + " z=" + int( org[ 2 ] ) );
	}
}

function amb_log( msg )
{
	if ( !TOD_AMB_LOG )
		return;
	line = "[TOD_AMB] ms=" + GetRealTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
