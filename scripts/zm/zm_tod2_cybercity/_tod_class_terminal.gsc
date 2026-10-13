// =============================================================================
// _tod_class_terminal.gsc - THE CROWN'S CLASS TERMINAL (tester kit, 2026-10-01).
//
// User 2026-10-01: "In the crown i want an option to switch between classes as
// well. I eventually want to push out a testing phase so testers have access to
// everything in the crown."
//
// WHAT THE PLAYER SEES. A data console stands against the crown hall's west wall,
// across the nave from the crown crate. Hold USE on it: the class draft's own four
// cards come up (the same panel, the same controls - tactical / lethal / d-pad /
// stick move, HOLD JUMP or USE locks) with the player's CURRENT class focused and
// tagged, under a SWITCH CLASS title. Lock another class and the confirm flash
// plays, the player's hands come back and the class changes in one server frame:
// the new class's gun at the SAME TIER (base form, full ammo - a promotion's rule),
// its lethal / tactical, its body, its speed, its health floor, a materialize burst
// at the player's feet. Lock the class they already are (or let the 32 s clock run
// out) and the panel just closes.
//
// WHAT CARRIES OVER. The tier, and EVERY upgrade card: a card of another class is
// kept and simply sleeps until the player is that class again
// (_tod_upgrades::class_live_level / domain_dormant; the pause menu hides the
// sleeping rows). The new gun arrives unpacked; Pack-a-Punch it again.
//
// WHAT THE OLD CLASS GIVES BACK, all in the switch's one frame (do_switch):
//   ARCHER       _tod_archer::cleanup( "class_changed" ): the grapple, the Retriever,
//                their HUD, the grenades the Archer had taken out of the slots
//   NECROMANCER  a bind in progress is dropped, every helper is dismissed
//   BREACHER     planted C4 is removed (its detonate lane leaves with the C4), the
//                riot shield and any recharge in flight are cleared
//   WARRIOR      the bowie leaves, the base knife comes back; the Cyber Sword's
//                glow goes out (kit_switch)
//   every class  every form of its guns, all tiers (the dev all-guns lane holds three)
//
// THE SESSION IS THE BLACK MARKET SPIN'S SHAPE (_tod_shop spin_lock): frozen (the
// card panel's soft freeze - button reads stay live), UNTARGETABLE (stock's ignoreme
// refcount) and unhurtable for the whole panel, then 1.5 s unhurtable after it
// closes so control never returns into a zombie's swing. The world does NOT pause:
// it is a tester's tool and co-op keeps playing.
//
// THE FIELDS ARE SHARED. The class panel's focus / clock / hold bar ride the upgrade
// panel's todUpgFocus / todUpgTime / todUpgHold (the 61-bit clientuimodel ceiling -
// _tod_class_select's header). The draft could never meet a card deal; the terminal
// can, so a round's deal TAKES the screen: on "tod_global_upg_takeover" the class
// panel closes in the same frame, the input dies, and the shared fields are left to
// the deal. A player the deal skipped is unfrozen when it ends. Re-open the terminal.
//
// REFUSED (one bottom-left line + the stock "no" sound, never a hint-string slot):
// before the draft ends, while down, while another menu owns the player (a card
// deal, the Black Market, a station pick), in the air (the jump pad, the grapple, a
// mantle, a jump), mid-ability (Bash, Gravity Smash, a soul pulse or a bind, the
// cloak), and with busy hands (a drink, a revive, a weapon swap in flight, the
// Death Machine).
//
// THE PROMPT is ONE constant hint string (one permanent triggerstring slot;
// lint_tod_hints counts it) and leads with the noun CLASS TERMINAL, claimed in
// ZMCursorHintNew.lua's TOD_NOUNS so it draws the default card.
//
// LOGS [TOD_CLASS_TERM] (TOD_CLS_TERM_LOG prints with dev OFF; console only):
//   INIT org= yaw= trig= / REFUSE why= / OPEN class= tier= focus= / CANCEL why=
//   (kept_class | timeout | takeover | downed | watchdog) / SWITCH from= to= tier=
//   old= new= swapped= guns_taken= kit= hp= c4_cleared= shield= asleep= / SWITCH_FAIL
//   / DONE why= class=
// Gate: tools/test_class_terminal.js (runs refuse_code, terminal_place and slot_of
// through the GSC interpreter, with negative controls) + tools/test_class_terminal_ui.lua.
// The switch: TOD_TESTER_KIT in _tod_tester.gsh.
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_classes;
#using scripts\zm\zm_tod2_cybercity\_tod_class_select;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;
#using scripts\zm\zm_tod2_cybercity\_tod_class_kit;
#using scripts\zm\zm_tod2_cybercity\_tod_archer;
#using scripts\zm\zm_tod2_cybercity\_tod_necro_summon;
#using scripts\zm\zm_tod2_cybercity\_tod_riotshield;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;   // play_sound_at_origin: the proven lane for a custom 3D alias

#insert scripts\shared\shared.gsh;
#insert scripts\zm\zm_tod2_cybercity\_tod_class_count.gsh;     // TOD_CLS_COUNT
#insert scripts\zm\zm_tod2_cybercity\_tod_tester.gsh;   // TOD_TESTER_KIT

#precache( "model", "p7_zm_sta_dragon_network_data_terminal" );   // zoned for the finale's uplink (a stock Stalingrad console)
#precache( "model", "tag_origin" );
#precache( "fx", "dlc5/theater/fx_teleport_flashback_kino" );     // zoned for the teleporters' arrival

#define TOD_CLS_TERM_LOG        1      // [TOD_CLASS_TERM] prints with dev OFF too (a console line in a dev block: a player never sees it)
#define TOD_CLS_TERM_SECS       32     // the panel's clock. todUpgTime is QUARTERED (4 bits, _tod_class_select TOD_CLS_TIMEOUT): a multiple of 4, <= 60
#define TOD_CLS_TERM_WALL_X     700    // the console's centre this far off the hall's axis, on the wall OPPOSITE the crown crate (its back 6 off the 728 inner face)
#define TOD_CLS_TERM_TRIG_OUT   60     // the use trigger stands this far out from the console's centre, toward the hall
#define TOD_CLS_TERM_TRIG_Z     36     // and this high: every vendor trigger floats (v16.27; the partner benches' 36)
#define TOD_CLS_TERM_TRIG_R     56
#define TOD_CLS_TERM_TRIG_H     64
#define TOD_CLS_TERM_FLASH      1.4    // the picked card's confirm flash (the draft's 1.6)
#define TOD_CLS_TERM_KEEP_FLASH 0.6    // the shorter flash when the player locks the class they already are (= close)
#define TOD_CLS_TERM_GRACE      1.5    // unhurtable after the panel closes (the Black Market spin's TOD_SPIN_EXIT_GRACE)
#define TOD_CLS_TERM_SWAP_WAIT  30     // ticks (0.05 s) to wait out an in-flight twin swap (tier_up's own bound)
#define TOD_CLS_TERM_FX_SECS    2.5
#define TOD_CLS_SHOW_TERMINAL   3      // todClsShow 3 = the terminal's panel. LOCKSTEP ui/uieditor/menus/hud/tod_class_select.lua (show 3)
#define TOD_CLS_TERM_MODEL      "p7_zm_sta_dragon_network_data_terminal"
#define TOD_CLS_TERM_FX         "dlc5/theater/fx_teleport_flashback_kino"
#define TOD_CLS_TERM_SND_WARP   "tod_warp"

#namespace tod_class_terminal;

function log( msg )
{
	if ( !TOD_CLS_TERM_LOG && !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_CLASS_TERM] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function cls_name( v )
{
	if ( !isdefined( v ) )
		return "none";
	return v;
}

function init()
{
	if ( !TOD_TESTER_KIT )
		return;
	level thread spawn_terminal();
	level thread vis_watch();
}

// PURE (the gate runs it through tools/sky_ships/gsc_eval.js): where the console stands, from two
// GENERATED crown anchors, so the console moves with the hall if the crown's parity ever flips. The
// crate stands against one long wall; the console takes the OTHER wall at the crate's y, with its
// screen - the model's local -X, measured off the xmodel (the monitor faces (-1, 0, 0)) - facing in.
function terminal_place( hc, crate )
{
	s = SpawnStruct();
	s.side = -1;
	if ( crate[ 0 ] < hc[ 0 ] )
		s.side = 1;
	s.org = ( hc[ 0 ] + s.side * TOD_CLS_TERM_WALL_X, crate[ 1 ], hc[ 2 ] );
	s.yaw = 0;
	if ( s.side < 0 )
		s.yaw = 180;
	s.fwd = ( 0 - s.side, 0, 0 );
	s.trig = s.org + s.fwd * TOD_CLS_TERM_TRIG_OUT + ( 0, 0, TOD_CLS_TERM_TRIG_Z );
	return s;
}

function spawn_terminal()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );

	s = terminal_place( tod_crown_data::hall_center(), tod_crown_data::crown_crate_org() );
	m = Spawn( "script_model", s.org );
	if ( !isdefined( m ) )
	{
		log( "INIT_FAIL why=model_spawn org=" + s.org );
		return;
	}
	m SetModel( TOD_CLS_TERM_MODEL );
	m.angles = ( 0, s.yaw, 0 );
	m NotSolid();   // a prop, like the partner benches: nothing is cut into the map, zombie paths are unchanged

	t = Spawn( "trigger_radius_use", s.trig, 0, TOD_CLS_TERM_TRIG_R, TOD_CLS_TERM_TRIG_H );
	if ( !isdefined( t ) )
	{
		log( "INIT_FAIL why=trigger_spawn org=" + s.trig );
		return;
	}
	t TriggerIgnoreTeam();
	t SetCursorHint( "HINT_NOICON" );
	t SetHintString( "Hold ^3[{+activate}]^7 ^5CLASS TERMINAL^7 - Switch class / Your tier and cards stay" );
	level.tod_cls_term = t;
	level.tod_cls_term_model = m;
	log( "INIT org=" + s.org + " yaw=" + s.yaw + " trig=" + t.origin + " r=" + TOD_CLS_TERM_TRIG_R + " classes=" + TOD_CLS_COUNT + " secs=" + TOD_CLS_TERM_SECS );
	t thread trigger_loop();
}

function trigger_loop()   // self = the use trigger
{
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( "trigger", p );
		if ( !isdefined( p ) || !isplayer( p ) || IS_TRUE( p.tod_cls_term_busy ) )
			continue;
		p.tod_cls_term_busy = true;
		p thread session();
	}
}

// The prompt leaves a player's screen while their panel is up (the Black Market's
// spin_vis_apply_all shape). Re-applied every 0.5 s so a client that joins into a
// slot a disconnected player left invisible gets the prompt back.
function vis_watch()
{
	level endon( "end_game" );
	for ( ;; )
	{
		wait 0.5;
		foreach ( p in GetPlayers() )
			vis_apply( p );
	}
}

function vis_apply( p )
{
	t = level.tod_cls_term;
	if ( !isdefined( t ) || !isdefined( p ) || !isplayer( p ) )
		return;
	want = 1;
	if ( IS_TRUE( p.tod_cls_term_open ) )
		want = 0;
	if ( isdefined( p.tod_cls_term_vis ) && p.tod_cls_term_vis == want )
		return;
	p.tod_cls_term_vis = want;
	if ( want == 1 )
		t SetVisibleToPlayer( p );
	else
		t SetInvisibleToPlayer( p );
}

// ---------------------------------------------------------------------------
// WHO MAY OPEN IT. refuse_state reads the player; refuse_code is PURE, so the
// gate can run every case (and a negative control per case) without an engine.
// ---------------------------------------------------------------------------
function refuse_state()   // self = player
{
	st = SpawnStruct();
	st.drafted = ( IS_TRUE( level.tod_class_select_done ) && isdefined( self.tod_class ) );
	st.alive = IsAlive( self );
	st.downed = false;
	st.grounded = false;
	st.mantling = false;
	if ( st.alive )
	{
		st.downed = self laststand::player_is_in_laststand();
		st.grounded = self IsOnGround();
		st.mantling = self IsMantling();
	}
	st.world_paused = IS_TRUE( level.tod_upgrade_pause );
	st.in_menu = ( IS_TRUE( self.tod_menu_frozen ) || IS_TRUE( self.tod_solo_upg_active ) || IS_TRUE( self.tod_spin_locked ) || IS_TRUE( self.tod_spin_grace ) );
	st.flying = IS_TRUE( self.tod_jumppad_flying );
	st.grappling = IS_TRUE( self.tod_grappling );
	st.ability = ( IS_TRUE( self.tod_bash_busy ) || IS_TRUE( self.tod_gs_busy ) || IS_TRUE( self.tod_gs_diving ) || IS_TRUE( self.tod_necro_pulse_busy ) || isdefined( self.tod_necro_bind_t0 ) );
	st.cloaked = ( isdefined( self.tod_cloak_until ) && GetTime() < self.tod_cloak_until );
	st.drinking = ( isdefined( self.is_drinking ) && self.is_drinking > 0 );
	st.reviving = IS_TRUE( self.is_reviving_any );
	st.swapping = ( IS_TRUE( self.tod_tier_busy ) || IS_TRUE( self.tod_swap_busy ) );
	st.death_machine = ( isdefined( self.zombie_vars ) && ( IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( self.zombie_vars[ "zombie_powerup_tod_wunderstrahl_on" ] ) ) );   // the Gift of Death or the Wunderstrahl (docs/219)
	return st;
}

// PURE. "" = the terminal opens. The order is the order a player would want to
// hear it: the draft, down, a menu that already owns the screen, the body (in the
// air), what they are doing (an ability), then their hands.
function refuse_code( st )
{
	if ( !IS_TRUE( st.drafted ) )
		return "draft";
	if ( !IS_TRUE( st.alive ) || IS_TRUE( st.downed ) )
		return "downed";
	if ( IS_TRUE( st.world_paused ) || IS_TRUE( st.in_menu ) )
		return "menu";
	if ( !IS_TRUE( st.grounded ) || IS_TRUE( st.flying ) || IS_TRUE( st.grappling ) || IS_TRUE( st.mantling ) )
		return "airborne";
	if ( IS_TRUE( st.ability ) || IS_TRUE( st.cloaked ) )
		return "ability";
	if ( IS_TRUE( st.drinking ) || IS_TRUE( st.reviving ) || IS_TRUE( st.swapping ) || IS_TRUE( st.death_machine ) )
		return "hands";
	return "";
}

// PURE. The one line a refusal prints (IPrintLn: a free lane, never a hint-string slot).
function refuse_message( code )
{
	if ( code == "draft" )
		return "Class terminal: opens after the class draft";
	if ( code == "downed" )
		return "Class terminal: get back up first";
	if ( code == "menu" )
		return "Class terminal: finish the open menu first";
	if ( code == "airborne" )
		return "Class terminal: land first";
	if ( code == "ability" )
		return "Class terminal: let your ability finish first";
	if ( code == "hands" )
		return "Class terminal: finish what you are doing first";
	return "Class terminal: not right now";
}

// PURE (given _tod_class_select::class_key). The draft slot a class sits in, so
// the panel opens on the player's own class.
function slot_of( key )
{
	for ( id = 1; id <= TOD_CLS_COUNT; id++ )
	{
		if ( tod_class_select::class_key( id ) == key )
			return id;
	}
	return tod_class_select::default_focus();
}

// ---------------------------------------------------------------------------
// ONE VISIT, from the USE press to the prompt coming back. self = player.
// ---------------------------------------------------------------------------
function session()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	code = refuse_code( self refuse_state() );
	if ( code != "" )
	{
		self PlaySound( "zmb_no_purchase" );
		self IPrintLn( refuse_message( code ) );
		log( "REFUSE player=" + self GetEntityNumber() + " class=" + cls_name( self.tod_class ) + " why=" + code );
		self release_use();
		self.tod_cls_term_busy = undefined;
		return;
	}

	from = self.tod_class;
	focus = slot_of( from );
	self.tod_cls_term_open = true;
	self.tod_cls_term_taken = undefined;
	vis_apply( self );
	self lock();
	self thread takeover_watch();
	self menu_open();
	if ( IS_TRUE( self.tod_cls_term_taken ) || IS_TRUE( level.tod_upgrade_pause ) )
	{
		self close_session( "takeover" );   // a deal landed while the menu was opening: its fields, not ours
		return;
	}
	self tod_class_select::set_field( "todUpgFocus", focus );
	self tod_class_select::set_field( "todUpgTime", int( ( TOD_CLS_TERM_SECS + 3 ) / 4 ) );   // QUARTERED, as the draft (the Lua x4)
	self tod_class_select::set_field( "todUpgHold", 0 );
	self tod_class_select::set_field( "todClsShow", TOD_CLS_SHOW_TERMINAL );   // last: the Lua paints with the full state
	self PlayLocalSound( "tod_ui_tick" );
	log( "OPEN player=" + self GetEntityNumber() + " class=" + from + " tier=" + tod_classes::tier( self ) + " focus=" + focus + " secs=" + TOD_CLS_TERM_SECS );

	self.tod_cls_term_pick = undefined;
	self thread input_run( focus );
	why = "";
	waited = 0;
	for ( ;; )
	{
		wait 0.05;
		waited += 0.05;
		if ( IS_TRUE( self.tod_cls_term_taken ) || IS_TRUE( level.tod_upgrade_pause ) )
		{
			why = "takeover";
			break;
		}
		if ( isdefined( self.tod_cls_term_pick ) )
			break;
		if ( !IsAlive( self ) || self laststand::player_is_in_laststand() )
		{
			why = "downed";
			break;
		}
		if ( waited > TOD_CLS_TERM_SECS + 3 )
		{
			why = "watchdog";   // run_select_input returns at its own clock; this is the belt and braces
			break;
		}
	}
	self notify( "tod_cls_term_input_end" );
	sel = 0;
	if ( isdefined( self.tod_cls_term_pick ) )
		sel = self.tod_cls_term_pick;
	self.tod_cls_term_pick = undefined;
	if ( why != "" )
	{
		log( "CANCEL player=" + self GetEntityNumber() + " why=" + why + " class=" + from );
		self close_session( why );
		return;
	}

	to = undefined;
	if ( sel > 0 )
		to = tod_class_select::class_key( sel );
	if ( !isdefined( to ) || to == from )
	{
		if ( isdefined( to ) )
		{
			// KEPT: the lock lands on their own card - a short flash, then the panel closes
			self tod_class_select::set_field( "todUpgFocus", sel );
			self tod_class_select::set_field( "todUpgTime", 0 );
			self tod_class_select::set_field( "todClsShow", 2 );
			self PlayLocalSound( "tod_ui_tick" );
			wait TOD_CLS_TERM_KEEP_FLASH;
		}
		why = "timeout";
		if ( isdefined( to ) )
			why = "kept_class";
		log( "CANCEL player=" + self GetEntityNumber() + " why=" + why + " class=" + from );
		self close_session( why );
		return;
	}

	// THE SWITCH. The confirm flash goes up first; then the player's hands come back
	// (the swap RAISES the new gun, and a raise needs enabled weapons - tier_up runs
	// after the card panel's unfreeze for the same reason); then the class changes.
	self tod_class_select::set_field( "todUpgFocus", sel );
	self tod_class_select::set_field( "todUpgTime", 0 );
	self tod_class_select::set_field( "todClsShow", 2 );
	self PlayLocalSound( "tod_class_jackin" );
	self tod_upgrades::menu_freeze( false );
	ok = self do_switch( from, to );
	if ( ok )
	{
		level thread fx_burst( TOD_CLS_TERM_FX, self.origin + ( 0, 0, 4 ), TOD_CLS_TERM_FX_SECS );
		tod_perk_scatter::play_sound_at_origin( self.origin, TOD_CLS_TERM_SND_WARP, 4 );
		// dev's "maxed out class ... this should apply to all the classes" (_tod_main dev_maxed_harness):
		// the class a tester switches INTO is maxed like the one they drafted
		if ( IS_TRUE( level.tod_dev_maxed ) )
			self thread tod_upgrades::dev_grant_maxed( self );
	}
	else
	{
		self PlaySound( "zmb_no_purchase" );
		self IPrintLn( "Class terminal: the switch did not go through - try again" );
	}
	wait TOD_CLS_TERM_FLASH;
	why = "switch_failed";
	if ( ok )
		why = "switched";
	self close_session( why );
}

// The draft's own input loop (run_select_input: every lane, both release gates,
// the hold bar), opened on the player's class. Killed by a card deal's takeover
// (synchronously, before the deal touches the shared fields) or by the session.
function input_run( focus )   // self = player
{
	self endon( "disconnect" );
	self endon( "tod_cls_term_input_end" );
	level endon( "end_game" );
	level endon( "tod_global_upg_takeover" );
	sel = self tod_class_select::run_select_input( TOD_CLS_TERM_SECS, focus );
	self.tod_cls_term_pick = sel;
}

// A CARD DEAL TAKES THE SCREEN (run_upgrade_event notifies before it writes a
// field): the class panel goes in the SAME frame, so the two never share one.
function takeover_watch()   // self = player
{
	self endon( "disconnect" );
	self endon( "tod_cls_term_closed" );
	level waittill( "tod_global_upg_takeover" );
	self.tod_cls_term_taken = true;
	self tod_class_select::set_field( "todClsShow", 0 );
}

// The spin's lock (_tod_shop spin_lock): frozen, untargetable, unhurtable - the
// invulnerability re-asserted every tick so a world pause ending mid-panel cannot
// strip it (_tod_upgrades::pause_invuln_held_elsewhere reads tod_cls_term_locked).
function lock()   // self = player
{
	self.tod_cls_term_locked = true;
	self tod_upgrades::menu_freeze( true );
	if ( !IS_TRUE( self.tod_cls_term_ignored ) )
	{
		self.tod_cls_term_ignored = true;
		self zm_utility::increment_ignoreme();
	}
	self EnableInvulnerability();
	self thread invuln_hold();
}

function unlock()   // self = player
{
	self.tod_cls_term_locked = undefined;
	self notify( "tod_cls_term_unlock" );
	if ( IS_TRUE( self.tod_cls_term_ignored ) )
	{
		self.tod_cls_term_ignored = undefined;
		self zm_utility::decrement_ignoreme();
	}
}

function invuln_hold()   // self = player
{
	self endon( "disconnect" );
	self endon( "tod_cls_term_unlock" );
	while ( IS_TRUE( self.tod_cls_term_locked ) )
	{
		self EnableInvulnerability();
		wait 0.1;
	}
}

// EXIT GRACE: zombies that idled next to an untargetable player re-acquire the
// frame the panel closes; for TOD_CLS_TERM_GRACE they cannot hurt (the spin's rule).
function exit_grace()   // self = player
{
	self endon( "disconnect" );
	self notify( "tod_cls_term_grace" );
	self endon( "tod_cls_term_grace" );
	self.tod_cls_term_grace = true;
	self EnableInvulnerability();
	wait TOD_CLS_TERM_GRACE;
	self.tod_cls_term_grace = undefined;
	if ( IS_TRUE( self.tod_cls_term_locked ) )
		return;   // a new visit owns it now
	if ( IS_TRUE( self.tod_pause_invuln ) || ( self tod_upgrades::pause_invuln_held_elsewhere() ) )
		return;
	self DisableInvulnerability();
}

// THE ONE WAY OUT, for every ending (switched, kept, timed out, taken over, down).
function close_session( why )   // self = player
{
	self notify( "tod_cls_term_input_end" );
	self tod_class_select::set_field( "todClsShow", 0 );
	taken = ( IS_TRUE( self.tod_cls_term_taken ) || IS_TRUE( level.tod_upgrade_pause ) );
	if ( !taken )
	{
		self tod_class_select::set_field( "todUpgFocus", 0 );
		self tod_class_select::set_field( "todUpgTime", 0 );
		self tod_class_select::set_field( "todUpgHold", 0 );
	}
	self unlock();
	self.tod_cls_term_grace = true;   // held through a card deal below; exit_grace times it out
	if ( taken )
	{
		// A CARD DEAL HAS THE SCREEN (and the shared fields). Its own flow freezes and
		// unfreezes a participant; a player it skipped is still frozen by us. Wait it out,
		// then hand back only a freeze no other menu owns.
		while ( IS_TRUE( level.tod_upgrade_pause ) )
			wait 0.1;
		wait 0.1;
		if ( IS_TRUE( self.tod_menu_frozen ) && !IS_TRUE( self.tod_spin_locked ) && !IS_TRUE( self.tod_solo_upg_active ) )
			self tod_upgrades::menu_freeze( false );
	}
	else
		self tod_upgrades::menu_freeze( false );
	wait 0.3;   // the panel's 250 ms fade, then the menu goes
	self menu_close();
	self thread exit_grace();
	self notify( "tod_cls_term_closed" );
	self.tod_cls_term_taken = undefined;
	self.tod_cls_term_open = undefined;
	vis_apply( self );
	log( "DONE player=" + self GetEntityNumber() + " why=" + why + " class=" + cls_name( self.tod_class ) );
	self release_use();
	self.tod_cls_term_busy = undefined;
}

// The draft's panel, reopened for this visit and closed after it. The draft's own
// handle is closed first: the engine closes a player's OpenLUIMenu menus on a
// death, so it may already be stale (the upgrade overlay's per-life rule).
function menu_open()   // self = player
{
	if ( isdefined( self.tod_cls_menu ) )
		self CloseLUIMenu( self.tod_cls_menu );
	self.tod_cls_menu = self OpenLUIMenu( "tod_class_select" );
	wait 0.1;   // let the menu build client-side before its fields land
}

function menu_close()   // self = player
{
	if ( !isdefined( self.tod_cls_menu ) )
		return;
	self CloseLUIMenu( self.tod_cls_menu );
	self.tod_cls_menu = undefined;
}

// The same held USE never opens the terminal twice.
function release_use()   // self = player
{
	self endon( "disconnect" );
	for ( i = 0; i < 60 && self UseButtonPressed(); i++ )
		wait 0.05;
	wait 0.25;
}

// ---------------------------------------------------------------------------
// THE SWITCH. self = player. true = the class changed. Everything from the
// assign to the weapon swap runs in ONE server frame, so no other thread ever
// sees the new class with the old kit, or the old class with the new gun.
// ---------------------------------------------------------------------------
function do_switch( from, to )
{
	for ( i = 0; i < TOD_CLS_TERM_SWAP_WAIT && IS_TRUE( self.tod_swap_busy ); i++ )
		wait 0.05;
	if ( IS_TRUE( self.tod_swap_busy ) || !IsAlive( self ) || self laststand::player_is_in_laststand() )
	{
		why = "down";
		if ( IS_TRUE( self.tod_swap_busy ) )
			why = "swap_busy";
		log( "SWITCH_FAIL player=" + self GetEntityNumber() + " from=" + from + " to=" + to + " why=" + why );
		return false;
	}
	self.tod_tier_busy = true;   // the body loop's twin reconcile holds off until the new gun has landed (tier_up's latch)
	tier = tod_classes::tier( self );
	g_old = tod_classes::gun( self );
	old_w = self tod_upgrades::class_primary_in_inventory();
	old_name = "none";
	if ( isdefined( old_w ) )
		old_name = old_w.name;
	kit_from = tod_class_kit::kit_of( self );
	hp_from = self.maxhealth;

	// 1. THE OLD CLASS GIVES BACK WHAT IT OWNED
	archer = false;
	if ( isdefined( self.tod_archer_state ) && IS_TRUE( self.tod_archer_state.armed ) )
	{
		self tod_archer::cleanup( "class_changed" );   // grapple, Retriever, their HUD; the grenades it took out come back
		archer = true;
	}
	if ( from == "necromancer" )
	{
		self tod_necro_summon::bind_cancel( "class_change" );
		self tod_necro_summon::dismiss_all( "class_change" );
	}
	c4 = 0;
	shield = 0;
	if ( from == "heavy" )
	{
		c4 = self tod_class_kit::clear_planted_c4();
		shield = self clear_shield();
	}

	// 2. THE NEW CLASS
	self.tod_pap_owned = undefined;   // the new gun arrives unpacked (tier_up step 3: reconcile would otherwise pull its _up form)
	if ( isdefined( g_old ) )
		tod_classes::pap_tier_forget( self, g_old.stem );
	self.tod_upg_maxed_told = undefined;
	tod_classes::assign_class( self, to );   // tod_class + the class body
	kit_to = tod_class_kit::kit_of( self );
	given = 0;
	if ( isdefined( self.tod_kit_given ) )
		given = self.tod_kit_given;
	if ( kit_to != given )
		self tod_class_kit::kit_switch( given, kit_to );   // the lethal / tactical slots now (kit_loop would a tick later)

	// 3. THE WEAPON: the new class's gun at the player's tier, base form, full ammo
	g_new = tod_classes::gun( self );
	want = tod_classes::base_weapon( g_new );
	swapped = false;
	if ( isdefined( want ) && isdefined( old_w ) && old_w != want )
		swapped = self tod_upgrades::swap_primary( old_w, want, true );
	if ( isdefined( want ) && !( self HasWeapon( want ) ) )
	{
		self tod_classes::give_camo_weapon( want );
		self GiveStartAmmo( want );
		self SwitchToWeapon( want );
	}
	taken = self take_class_guns( from, want );
	if ( isdefined( g_old ) && isdefined( g_old.alt ) && ( !isdefined( g_new ) || !isdefined( g_new.alt ) || g_new.alt != g_old.alt ) )
	{
		// the Warrior's bowie leaves with him; the base knife comes back
		a = GetWeapon( g_old.alt );
		if ( isdefined( a ) && a != level.weaponNone && self HasWeapon( a ) )
			self TakeWeapon( a );
		if ( isdefined( level.weaponBaseMelee ) && level.weaponBaseMelee != level.weaponNone && !( self HasWeapon( level.weaponBaseMelee ) ) )
			self GiveWeapon( level.weaponBaseMelee );
	}
	if ( isdefined( g_new ) && isdefined( g_new.alt ) )
	{
		a = GetWeapon( g_new.alt );
		if ( isdefined( a ) && a != level.weaponNone && !( self HasWeapon( a ) ) )
			self GiveWeapon( a );
	}
	self tod_classes::give_secondary( to, tier );   // no secondaries since 2026-09-26: reaps any sidearm, grants nothing

	// 4. THE BODY: health to the new class's floor (VITALITY is the Warrior's and the
	// summon bank the Necromancer's - both sleep in another class), speed, sprint fire
	hp = self tod_upgrades::max_hp_floor();
	if ( self.maxhealth != hp )
	{
		self.maxhealth = hp;
		self SetMaxHealth( hp );
	}
	if ( self.health > hp )
		self.health = hp;
	self.tod_tier_busy = undefined;
	self tod_upgrades::apply_move_speed();
	self tod_upgrades::apply_sprint_fire();
	self tod_upgrades::refresh_upgrade_list();   // the pause menu: this class's cards live, the others' asleep
	if ( isdefined( level.tod_shield_reconcile ) )
		self [[ level.tod_shield_reconcile ]]();   // a Breacher holding the card gets his shield back
	self thread tod_classes::give_class_loadout();   // the respawn path's own top-up; a no-op when all of the above landed
	self notify( "tod_class_switched", from, to );

	asleep = 0;
	foreach ( d in level.tod_domains )
	{
		if ( tod_upgrades::get_level( self, d.key ) > 0 && tod_upgrades::domain_dormant( self, d ) )
			asleep++;
	}
	new_name = "none";
	if ( isdefined( want ) )
		new_name = want.name;
	log( "SWITCH player=" + self GetEntityNumber() + " from=" + from + " to=" + to + " tier=" + tier + " old=" + old_name + " new=" + new_name
		+ " swapped=" + swapped + " guns_taken=" + taken + " kit=" + kit_from + ">" + kit_to + " archer_cleanup=" + archer
		+ " c4_cleared=" + c4 + " shield=" + shield + " hp=" + hp_from + ">" + hp + " asleep=" + asleep );
	return true;
}

// Every form of a class's guns, all tiers, except `keep`. Returns how many went.
function take_class_guns( key, keep )   // self = player
{
	c = level.tod_classes[ key ];
	if ( !isdefined( c ) )
		return 0;
	n = 0;
	weapons = self GetWeaponsListPrimaries();
	foreach ( w in weapons )
	{
		if ( !isdefined( w ) || !isdefined( w.name ) )
			continue;
		if ( isdefined( keep ) && w == keep )
			continue;
		for ( t = 1; t <= tod_classes::tier_max(); t++ )
		{
			if ( isdefined( c.tiers[ t ] ) && IsSubStr( w.name, c.tiers[ t ].stem ) )
			{
				self TakeWeapon( w );
				n++;
				break;
			}
		}
	}
	return n;
}

// The Breacher's riot shield is his card's: it leaves with the class, with any
// recharge in flight (recharge_loop endon's tod_shield_recharge_loop). 1 = a shield
// was taken, 2 = a recharge was stopped, 3 = both.
function clear_shield()   // self = player
{
	n = 0;
	held = self tod_riotshield::held_shield();
	if ( isdefined( held ) )
	{
		self tod_riotshield::clear_shield( held );
		n += 1;
	}
	if ( isdefined( self.tod_shield_recharge_until ) )
	{
		self.tod_shield_recharge_until = undefined;
		self.tod_shield_broke_at = undefined;
		self notify( "tod_shield_recharge_loop" );
		n += 2;
	}
	return n;
}

// A throwaway FX host. NO endon: a thread killed mid-wait would orphan the host.
function fx_burst( fx, org, secs )
{
	h = Spawn( "script_model", org );
	if ( !isdefined( h ) )
		return;
	h SetModel( "tag_origin" );
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;   // let the host replicate before its one-shot (the teleporter's rule)
	if ( !isdefined( h ) )
		return;
	PlayFXOnTag( fx, h, "tag_origin" );
	wait secs;
	if ( isdefined( h ) )
		h Delete();
}
