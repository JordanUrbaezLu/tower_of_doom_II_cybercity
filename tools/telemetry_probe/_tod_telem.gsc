// _tod_telem.gsc - THE TELEMETRY PROBE (2026-10-05, rev 4). Landed by tools/telemetry_probe/land.js
// into scripts/zm/zm_tod2_cybercity/; the source of truth is the copy under tools/.
//
// WHY. The user wants per-run play data (class, guns, round, run length) stored where it can
// be analysed, and NOTHING may ever open outside the game (the old map's console flash cost
// player trust). The only silent persistence channel on retail BO3 is file IO from the UI
// Lua (proven by MACHIN[A]'s save and by the old map's board). This probe proves that channel
// on THIS build and on the CURRENT game patch before any feature is built on it, and records
// whether Engine.OpenUrl (a possible player-pressed "view my run" lane) still exists.
//
// HISTORY. Rev 1 (2026-10-04 22:33) and rev 2 (2026-10-05 17:33, three map loads) both came back
// NO_REPORT with no file: the menu opened every time (handle defined) but no report lane reached
// GSC, not even rev 2's top-level "file ran" marker. Rev 3 is a LANE CENSUS: the Lua reports on
// five lanes, each to its own dvar (tod_telem_l1..l4) plus a menuresponse (L5), using the
// controller the engine hands the menu, the shape of this map's proven Engine.Exec(controller,
// "map_restart"). This module logs every lane separately, so one run names the lane that works,
// or proves the file never executes at all (every lane empty, including the controller lane).
//
// REV 3 RESULT (2026-10-05 20:05 run): every lane empty including L1, no top-level marker, no
// SendMenuResponse: the menu's Lua NEVER EXECUTED. Root cause: the 4-file LUI contract needs a
// `LuiLoad( "ui.uieditor.menus.hud.<name>" )` in the CLIENT entry script (zm_tod2_cybercity.csc,
// beside tod_upgrade / tod_class_select); revs 1-3 had the Lua, the zone line and the precache but
// not the LuiLoad, so OpenLUIMenu returned a handle for a menu whose file was never loaded.
// Rev 4 adds the LuiLoad (land.js piece 6) and is console-only: no IPrintLnBold, no on-screen text.
//
// WHAT IT DOES (armed build only, TOD_TELEM_LOG 1):
//   * io probe x2 on the host (blackscreen + 2 s, then 40 s later): opens the tod_telem_probe
//     overlay in mode "io", polls every lane for 6 s keeping the last value per lane, closes the
//     overlay, logs a LANES census line + the verdict, prints a one-line verdict on screen.
//   * at end_game: the same overlay in mode "url" - the ONE place a page may open.
// Evidence after the run: console_mp.log lines tagged [TOD_TELEM], and the file
// <game>\players\tod2_telem_probe.txt (token line, "second", and the trace) when io works.
//
// RETIRE WHOLE after the test (node tools/telemetry_probe/land.js --remove): the module, the
// Lua rawfile, both zone lines and the two entry-script lines. The pre-publish grep for
// "#define TOD_\w*_LOG\s+1" lists TOD_TELEM_LOG while it is armed.

#using scripts\shared\flag_shared;
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#precache( "lui_menu", "tod_telem_probe" );
#namespace tod_telem;

#define TOD_TELEM_LOG 1          // 1 = probe ARMED (dev test build). 0 = inert (nothing threads).
#define TOD_TELEM_WAIT_MS 6000   // how long run_probe holds the overlay open and polls the lanes
#define TOD_TELEM_SECOND_WAIT 40 // seconds between the first and the second io probe

function init()
{
	if ( !TOD_TELEM_LOG ) return;
	telem_log( "init rev4 (LuiLoad'ed): probe ARMED (TOD_TELEM_LOG 1); lane census L1 ctrl / L2 c0 / L3 glcn / L4 setdvar / L5 menuresponse; io probe at blackscreen + 2 s and + " + ( 2 + TOD_TELEM_SECOND_WAIT ) + " s, url probe at end_game" );
	// never cleared: the Lua file's top-level code sets it when the FILE executes; a value present
	// already here means it ran earlier in this app session (the UI VM can outlive a map load)
	telem_log( "init: tod_telem_loaded='" + GetDvarString( "tod_telem_loaded", "" ) + "'" );
	level thread probe_at_boot();
	level thread probe_at_end_game();
}

function telem_log( msg )
{
	line = "[TOD_TELEM] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// The listen-server host is players[0]; the probe runs there and nowhere else.
function host_player()
{
	players = GetPlayers();
	if ( !isdefined( players ) || players.size < 1 ) return undefined;
	return players[ 0 ];
}

function probe_at_boot()
{
	level endon( "end_game" );
	flag::wait_till( "initial_blackscreen_passed" );
	wait 2;
	io_probe_once( "first" );
	wait TOD_TELEM_SECOND_WAIT;
	io_probe_once( "second" );
}

function io_probe_once( which )
{
	host = host_player();
	if ( !isdefined( host ) )
	{
		telem_log( which + " io probe: no player, skipped" );
		return;
	}
	tr = host run_probe( "io" );
	v = verdict_io( tr );
	// console only (rev 4): nothing on screen in a dev-off build (CLAUDE.md; -13's triage 2026-10-05)
	telem_log( which + " io probe VERDICT=" + v + " trace=" + tr );
}

function probe_at_end_game()
{
	level waittill( "end_game" );
	wait 1;
	host = host_player();
	if ( !isdefined( host ) )
	{
		telem_log( "url probe: no player, skipped" );
		return;
	}
	tr = host run_probe( "url" );
	telem_log( "end_game url probe trace=" + tr );
}

// L5: every menuresponse the host sends while the probe window is open. Logged raw (menu +
// response), the last tod_telem_probe response kept for the census. Ends on the stop notify.
function menuresponse_watch( mode )
{
	self endon( "disconnect" );
	self endon( "tod_telem_mr_stop" );
	while ( true )
	{
		self waittill( "menuresponse", menu, response );
		m = ( isdefined( menu ) ? menu : "undefined" );
		r = ( isdefined( response ) ? response : "undefined" );
		telem_log( "run_probe mode=" + mode + " L5 menuresponse menu=" + m + " response=" + r );
		if ( m == "tod_telem_probe" )
			self.tod_telem_l5 = r;
	}
}

// self = the host player. Clears every lane, opens the overlay (the Lua runs synchronously in
// createMenu and reports on all five lanes), polls the dvar lanes for the whole window keeping the
// LAST value of each, closes the overlay, logs the census and returns the best trace.
function run_probe( mode )
{
	SetDvar( "tod_telem_cmd", mode );
	SetDvar( "tod_telem_l1", "" );
	SetDvar( "tod_telem_l2", "" );
	SetDvar( "tod_telem_l3", "" );
	SetDvar( "tod_telem_l4", "" );
	self.tod_telem_l5 = "";
	self thread menuresponse_watch( mode );
	wait 0.2;   // let the mode dvar land client-side before createMenu reads it
	loaded_before = GetDvarString( "tod_telem_loaded", "" );
	m = self OpenLUIMenu( "tod_telem_probe" );
	telem_log( "run_probe mode=" + mode + " OpenLUIMenu handle defined=" + ( isdefined( m ) ? 1 : 0 ) + " tod_telem_loaded before open='" + loaded_before + "'" );

	l1 = ""; l2 = ""; l3 = ""; l4 = "";
	end_ms = GetTime() + TOD_TELEM_WAIT_MS;
	while ( GetTime() < end_ms )
	{
		c1 = GetDvarString( "tod_telem_l1", "" );
		c2 = GetDvarString( "tod_telem_l2", "" );
		c3 = GetDvarString( "tod_telem_l3", "" );
		c4 = GetDvarString( "tod_telem_l4", "" );
		if ( c1 != l1 ) { l1 = c1; telem_log( "run_probe mode=" + mode + " L1 ctrl: " + l1 ); }
		if ( c2 != l2 ) { l2 = c2; telem_log( "run_probe mode=" + mode + " L2 c0: " + l2 ); }
		if ( c3 != l3 ) { l3 = c3; telem_log( "run_probe mode=" + mode + " L3 glcn: " + l3 ); }
		if ( c4 != l4 ) { l4 = c4; telem_log( "run_probe mode=" + mode + " L4 setdvar: " + l4 ); }
		if ( IsSubStr( l1, "|done" ) || IsSubStr( l2, "|done" ) || IsSubStr( l3, "|done" ) || IsSubStr( l4, "|done" ) || IsSubStr( self.tod_telem_l5, "|done" ) )
			break;
		wait 0.1;
	}
	if ( isdefined( m ) )
		self CloseLUIMenu( m );
	self notify( "tod_telem_mr_stop" );
	l5 = self.tod_telem_l5;

	telem_log( "run_probe mode=" + mode + " LANES L1=" + lane_flag( l1 ) + " L2=" + lane_flag( l2 ) + " L3=" + lane_flag( l3 ) + " L4=" + lane_flag( l4 ) + " L5=" + lane_flag( l5 ) + " loaded_after='" + GetDvarString( "tod_telem_loaded", "" ) + "'" );

	tr = best_trace( l1, l2, l3, l4, l5 );
	telem_log( "run_probe mode=" + mode + " final trace=" + tr );
	return tr;
}

function lane_flag( v )
{
	if ( v == "" ) return "0";
	return "1";
}

// the first lane carrying the finished trace wins; otherwise the longest partial; otherwise NO_REPORT
function best_trace( l1, l2, l3, l4, l5 )
{
	lanes = array( l1, l2, l3, l4, l5 );
	foreach ( v in lanes )
	{
		if ( IsSubStr( v, "|done" ) )
			return v;
	}
	best = "";
	foreach ( v in lanes )
	{
		if ( v.size > best.size )
			best = v;
	}
	if ( best == "" )
		best = "NO_REPORT";
	return best;
}

function verdict_io( tr )
{
	if ( IsSubStr( tr, "rd_true_MATCH" ) ) return "GO";
	if ( tr == "NO_REPORT" ) return "NO REPORT";
	if ( IsSubStr( tr, "outer_nochunk" ) || IsSubStr( tr, "outer_chunk_error" ) ) return "CHUNK FAILED";
	if ( tr == "outer_open" ) return "MENU RAN, CHUNK SILENT";
	if ( tr == "outer_create" ) return "MENU ENTERED, MENU OBJECT FAILED";
	if ( IsSubStr( tr, "io_nil" ) ) return "NO IO LIBRARY";
	return "NO";
}
