// Four per-player AI companions. State belongs to the player, never a trigger.
// One level-owned manager owns every actor/proxy, including disconnect cleanup.
// THE DEALER'S GIFT (docs/209, user 2026-10-04: "This concept of finding your parts etc is a bit much to get into
// the black market situation. I think he should gift you a random AI companion on first use that doesnt use up your
// luck. Then you can continue to upgrade"): a companion comes from ONE place - the Black Market's dealer hands each
// player a random one, free, the first time he uses the counter (_tod_shop gift -> gift_companion below). The
// docs/159 collect-two-parts / build / equip flow is RETIRED: no parts at the Vault spawn, no workshop bench
// prompts (the four crafting tables stay in the wings as set dressing: the map's clips are cut round them).
#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\shared\ai_shared;
#using scripts\shared\ai\archetype_utility;
#using scripts\shared\ai\zombie_utility;
#using scripts\zm\_zm_spawner;
#using scripts\zm\_zm_score;
#using scripts\zm\zm_tod2_cybercity\_tod_luck;
#using scripts\zm\zm_tod2_cybercity\_tod_boss_fx;
#using scripts\zm\zm_tod2_cybercity\_tod_shop;          // the BLACK MARKET SPIN items (docs/188): item_mult / item_rarity / item_value / items_of
#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;   // GENERATED — the workshop tables' anchors (docs/158)
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;     // GENERATED — crown hall centre for the test benches
#using scripts\zm\zm_tod2_cybercity\_tod_teleport;       // discharge / fx_burst: a companion ARRIVES with the teleporter's own look
#using scripts\shared\ai\systems\animation_state_machine_mocomp;   // THE DROP: RegisterAnimationMocomp (register_drop_traversal)
#insert scripts\shared\shared.gsh;

// CROWN TEST BENCHES (user 2026-09-28: "add the benches in the crown for each
// one where i can equip and swap companions freely"). 1 = four extra benches in
// the crown hall's south nave: no rebuild wait, full health on every equip, and
// using the equipped partner's bench dismisses it. Players get their companion
// from the Black Market's dealer (docs/209); these are the tester's lane only.
// build_map.ps1 -Publish refuses to ship this armed.
#define TOD_PARTNER_TEST_BENCHES 0   // 2026-10-04: OFF for the first real playthrough - the companion comes from the Dealer's gift (docs/209)

#precache( "aitype", "spawner_tod_partner" );
#precache( "model", "tod_partner_protector" );
#precache( "model", "tod_partner_talon" );
#precache( "model", "tod_partner_raps" );
#precache( "model", "tod_partner_cerberus" );
// (the eight docs/159 part models stay in tod_partners.zpkg until tools/partner/install_assets.py retires them:
// its manifest + verify_assets.py pin all twelve. Nothing spawns them since the gift, docs/209.)
#precache( "model", "p8_zm_crafting_table" );
#precache( "model", "wm_t9_ak47_full" );
#precache( "model", "tag_origin" );
// Shot visuals (2026-09-28 playtest: "you cant see bullets or visuals"). Both
// LOOP on purpose: a server-played one-shot renders nothing in this map
// (_tod_rampage glow_set note), so the tracer is a looping trail on a flying
// tag_origin host (the Retriever's proven lane) and the hit is a looping spark
// on a host that lives TOD_PTN_HIT_SECS, then is deleted.
#precache( "fx", "tod/archer/fx_tod_archer_trail" );
#precache( "fx", "electric/fx_elec_spark_loop_sm" );
// THE BLAST (R.A.P.S.'s burst, the item-installed flash) was electric/fx_elec_burst_lg_z270_os until 2026-10-04: a
// gfx_debug_missing_fx STUB in the tools (memory stock-fx-can-be-a-stub) - it zoned, linked and drew NOTHING. Now
// Der Eisendrache's teleport flash, the teleporter's own "bright discharge" (_tod_teleport tod_tp_flash, real, zoned).
#precache( "fx", "dlc1/castle/fx_elec_teleport_flash_lg" );
// The companion loadout chips (TodSpinReel.lua): three packed item slots + companion.
#precache( "eventstring", "tod_ptn_items" );
// The pause menu / scoreboard AI COMPANION row (user 2026-09-29): which companion, its state,
// health or rebuild seconds, and the companions owned (push_state; TodSpinReel.lua records it).
#precache( "eventstring", "tod_ptn_state" );
// THE COMPANION STATUS PLATE (PK08, 2026-10-05, W2G): the live HUD readout (TodCompanionPlate.lua), sent by push_hud.
#precache( "eventstring", "tod_ptn_hud" );
#define TOD_PTN_TRACER_FX     "tod/archer/fx_tod_archer_trail"
#define TOD_PTN_HIT_FX        "electric/fx_elec_spark_loop_sm"
#define TOD_PTN_BLAST_FX      "dlc1/castle/fx_elec_teleport_flash_lg"
#define TOD_PTN_TRACER_SPEED  4500   // units / s the tracer host flies
#define TOD_PTN_HIT_SECS      0.3
#define TOD_PTN_TALON_HOVER   60     // zombie-swipe height: zombies clawing at it read as hitting it
#define TOD_PTN_MOVE_LOG_MS   2000   // MOVE heartbeat per partner
#define TOD_PTN_STALL_MS      1000   // no progress for this long while the goal is far = MOVE_STALL
// R.A.P.S. ROLLS AROUND (user 2026-09-28: "the raps should roll around. Like
// that's its functionality"). It never parks: it rams a zombie near its owner,
// and with nothing to hit it circles the owner at TOD_PTN_RAPS_ORBIT_R,
// stepping TOD_PTN_RAPS_ORBIT_STEP degrees each time it reaches the point (or
// every TOD_PTN_RAPS_ORBIT_MS), always on the companion's sprint locomotion.
// THE BOWLING BALL (user 2026-10-05: "I would expect it to hit things like by
// physically running them over or touching them ... too fast too. It was like
// almost like teleporting everywhere"). That run logged it at ~885 u/s (the
// sprint cycle x1.35 for everything), flipping charge <-> orbit 24 times in
// under a second each (targets crossing the 700 line, the nearest zombie
// changing every 0.2 s), and only its 5 s blast ever hurt anything. Now it
// LOCKS one zombie within TOD_PTN_RAPS_HUNT_R of its owner and rams it until
// that zombie dies, strays past TOD_PTN_RAPS_RELEASE_R or TOD_PTN_RAPS_LOCK_MS
// passes without a touch; it circles at TOD_PTN_RAPS_RATE_ORBIT and rams at
// TOD_PTN_RAPS_RATE_CHARGE; every zombie it rolls into takes a hit
// (raps_touch) and an ordinary one it kills is thrown along the roll
// (raps_fling). The 5 s blast stays its big hit.
#define TOD_PTN_RAPS_HUNT_R      700    // lock a zombie this close to the owner ...
#define TOD_PTN_RAPS_RELEASE_R   950    // ... and keep it until it strays this far (no flip-flop at the line)
#define TOD_PTN_RAPS_LOCK_MS     4000   // a lock with no touch for this long lets go (it cannot reach that one)
#define TOD_PTN_RAPS_ORBIT_R     200
#define TOD_PTN_RAPS_ORBIT_STEP  55
#define TOD_PTN_RAPS_ORBIT_MS    1500
#define TOD_PTN_RAPS_RATE_ORBIT  0.6    // ASM rate circling the owner, ~395 u/s (1.35 = ~885 u/s before, for everything)
#define TOD_PTN_RAPS_RATE_CHARGE 0.85   // ASM rate ramming its locked zombie, ~560 u/s
#define TOD_PTN_RAPS_TOUCH_R     52     // a zombie this close (flat, and within 56 up or down) is rolled into: the ball (r 18) + a zombie (r 15) + room for the carrier body ...
#define TOD_PTN_RAPS_TOUCH_MS    600    // ... once per this, per zombie
#define TOD_PTN_RAPS_TOUCH_FRAC  0.5    // a touch = half the blast's hit (deal_damage's frac)
// THE BLACK MARKET SPIN's items (docs/188; ids LOCKSTEP with _tod_shop.gsc).
#define TOD_ITEM_PLATING   1
#define TOD_ITEM_OVERCLOCK 2
#define TOD_ITEM_HOLLOW    3
#define TOD_ITEM_SIGHT     4
#define TOD_ITEM_NANO      5
#define TOD_ITEM_ARC       6
#define TOD_ITEM_SALVAGE   7
#define TOD_ITEM_REBOOT    8
#define TOD_ITEM_LUCKY     9
#define TOD_PTN_REBUILD_MS 45000
// PK22 (2026-10-05): THE COMPANIONS' SOUND. The Talon hovers, the R.A.P.S. rolls and Cerberus drives with a 3D loop
// on its visual (tod_partners.csv: the Talon's hum always while it is out, the roll / servo while it moves); a frozen
// companion (freeze_reason) is silent; Delete ends a loop on every exit (retire: destroyed, owner dead, gift, switch,
// end game, disconnect). A DESTROYED companion bursts where it fell (the blast flash + a shower of sparks) with a
// metal crunch and a dying whine there, and its owner hears a short "signal lost" wherever he is.
#define TOD_PTN_LOOP_FADE      0.25   // s: a loop fades in / out this fast
#define TOD_PTN_MOVE_ON        3      // units per 0.1 s tick that count as moving (30 u/s)
#define TOD_PTN_MOVE_HOLD_MS   400    // the roll / servo rides out a stop shorter than this
#define TOD_PTN_DEATH_SECS     1.2    // the sparks' host lives this long
// push_state's state codes. LOCKSTEP TodSpinReel.lua CoD.TodCompanionDescribe.
#define TOD_PTN_UI_NONE      0   // no companion held
#define TOD_PTN_UI_ACTIVE    1   // out and fighting: value = health percent, 5 % steps
#define TOD_PTN_UI_REBUILD   2   // destroyed: value = whole seconds until it is back
#define TOD_PTN_UI_DEPLOYING 3   // held, not out yet (on its way, or its owner is down / dead)
// push_hud's flags. LOCKSTEP TodCompanionPlate.lua CP.F_FROZEN / CP.F_OUT.
#define TOD_PTN_HUD_FROZEN   1   // it holds still with its owner (freeze_reason): the plate reads HOLDING
#define TOD_PTN_HUD_OUT      2   // its owner is dead or spectating: the plate hides
#define TOD_PTN_HUD_BEAT_MS  3000   // the plate's state is re-sent this often unchanged (a recreated HUD, a late joiner)
#define TOD_PTN_ARC_R      300
// THE DROP (LT-fix 2026-10-05, the user's 17:33 run): the stock mocomp the companion's selector table names for a
// traversal type it has no row for (zod_robot_companion.ai_ast, combat_traverse@traversal "*" row). See
// register_drop_traversal. Lower case: stock RegisterAnimationMocomp lower-cases the name it stores.
#define TOD_PTN_TRAV_MOCOMP    "mocomp_teleport_traversal@zombie"

#namespace tod_partners;

function init()
{
    level.tod_partner_records = [];
    level.tod_partner_defs = [];
    // id, name, model, health, shot interval, range, fraction of ROUND health.
    // W3E 2026-10-05: one name per companion - LOCKSTEP TodSpinReel.lua P3.COMPANIONS (partner_shop/test_spin.js),
    // and the HUD plate / gift tile already said PROTECTOR (the rig is the SoE Civil Protector; the player meets "PROTECTOR").
    define( 0, "PROTECTOR", "tod_partner_protector", 1800, 0.48, 750, 0.26 );
    define( 1, "TALON", "tod_partner_talon", 1000, 0.30, 850, 0.14 );
    define( 2, "R.A.P.S.", "tod_partner_raps", 1400, 5.0, 115, 1.10 );
    define( 3, "CERBERUS", "tod_partner_cerberus", 2200, 0.20, 650, 0.11 );
    callback::on_spawned( &player_spawned );
    zm_spawner::register_zombie_death_event_callback( &kill_credit );
    level thread workshop_tables();
    if ( TOD_PARTNER_TEST_BENCHES ) level thread test_benches();
    level thread manager();
    level thread end_cleanup();
    level.tod_partner_items_changed = &items_changed;   // _tod_shop calls this after a socket
    level.tod_partner_gift_fn = &gift_companion;        // THE DEALER'S GIFT (docs/209): _tod_shop hands one over
    register_drop_traversal();                          // THE DROP: the broken tower's drops (LT-fix)
    log( "INIT rev=2 types=4 source=dealer_gift parts=0 workshop_prompts=0 test_benches=" + TOD_PARTNER_TEST_BENCHES + " recharge_seconds=45 arrive=teleport" );
}

function define( id, title, model, hp, interval, range, fraction )
{
    d = SpawnStruct();
    d.title = title; d.model = model; d.hp = hp;
    d.interval = interval; d.range = range; d.fraction = fraction;
    level.tod_partner_defs[ id ] = d;
}

// ---- the spin's items on the HELD companion (docs/188). A companion that holds
// nothing reads 1.0 / -1 everywhere, so every line below is a no-op until a spin.
function item_mult( s, item ) { return tod_shop::item_mult( s.owner, s.chosen, item ); }
function max_hp( s, id ) { return int( level.tod_partner_defs[ id ].hp * tod_shop::item_mult( s.owner, id, TOD_ITEM_PLATING ) ); }
function rebuild_ms( s, id )
{
    r = tod_shop::item_rarity( s.owner, id, TOD_ITEM_REBOOT );
    if ( r < 0 ) return TOD_PTN_REBUILD_MS;
    return tod_shop::item_value( TOD_ITEM_REBOOT, r );
}
function start_rebuild( s, id, now )
{
    s.hp[ id ] = 0; s.ready_len[ id ] = rebuild_ms( s, id ); s.ready[ id ] = now + s.ready_len[ id ];
}

function ensure_state( p )
{
    if ( isdefined( p.tod_ptn ) ) return;
    s = SpawnStruct();
    s.owner = p;
    // built[ id ] = OWNED: the dealer gave it (docs/209) - the pause row's built mask still carries it
    s.built = []; s.hp = []; s.ready = []; s.ready_len = [];
    for ( i = 0; i < 4; i++ )
    {
        s.built[ i ] = false;
        s.hp[ i ] = level.tod_partner_defs[ i ].hp; s.ready[ i ] = 0; s.ready_len[ i ] = TOD_PTN_REBUILD_MS;
    }
    s.chosen = -1; s.busy = false; s.retry = 0;
    s.generation = 0;
    s.actor = undefined; s.visual = undefined;
    // Persistent non-AI attacker: the aggro carrier's allow_zombie_to_target_ai
    // flag would route stock hits through player GetCurrentWeapon/score calls.
    s.gun = Spawn( "script_origin", p.origin );
    s.gun.tod_is_partner = true;
    s.gun.tod_partner_owner = p; s.gun.tod_partner_state = s;
    s.next_shot = 0; s.next_goal = 0; s.next_log = 0; s.nano_acc = 0;
    s.last_origin = p.origin; s.stuck_since = GetTime();
    p.tod_ptn = s;
    level.tod_partner_records[ level.tod_partner_records.size ] = s;
    log( "PLAYER ent=" + p GetEntityNumber() + " state_created" );
}

function player_spawned()
{
    ensure_state( self );
    self.tod_ptn.busy = false;
    self.tod_ptn.ui_sig = undefined;   // a respawned HUD gets the companion row's state again
    self.tod_ptn.hud_sig = undefined;  // ... and the status plate its own, at once (no heartbeat wait)
    self thread push_items_later();
}

// THE DEALER'S GIFT (docs/209): _tod_shop gift() calls this (level.tod_partner_gift_fn) the moment its reel lands on
// companion `id`. He OWNS it and holds it at full health from now on; nothing spawns here - the manager deploys it the
// first tick nothing freezes him (freeze_reason "owner_spin" holds it until his Black Market screen closes), and the
// deploy is the teleporter's arrival (arrive_fx). Returns true when it took.
function gift_companion( p, id )
{
    if ( !isdefined( p ) || !isplayer( p ) || !isdefined( id ) || id < 0 || id >= level.tod_partner_defs.size ) return false;
    ensure_state( p );
    s = p.tod_ptn;
    previous = s.chosen;
    retire( s, "gift" );   // never two: a stale actor (a tester's bench pick) leaves before the gift arrives
    s.built[ id ] = true;
    s.chosen = id; s.retry = 0;
    s.hp[ id ] = max_hp( s, id ); s.ready[ id ] = 0;
    if ( !isdefined( s.gifts ) ) s.gifts = 0;
    s.gifts++;
    push_items( p );
    log( "GIFT owner=" + p GetEntityNumber() + " type=" + id + " name=" + level.tod_partner_defs[ id ].title + " hp=" + s.hp[ id ] + " previous=" + previous + " gifts=" + s.gifts );
    return true;
}

function usable( p )
{
    if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) ) return false;
    if ( p laststand::player_is_in_laststand() ) return false;
    if ( IS_TRUE( level.tod_upgrade_pause ) ) return false;
    if ( !IS_TRUE( level.tod_class_select_done ) ) return false;
    return true;
}

// docs/158 — EVERY ANCHOR IS GENERATED. A crafting table stands on the far wall of each workshop wing (N, E, S, W),
// at the generated tod_breather_data anchor that also cuts its collision clip into the map. Since the gift (docs/209)
// they are SET DRESSING: no prompt, no part, no scale model on top - a companion comes from the Black Market's dealer
// only. The table must stay: the clip is in the .map, and a clip with no table is an invisible wall.
function workshop_tables()
{
    level endon( "end_game" );
    level flag::wait_till( "initial_blackscreen_passed" );
    for ( id = 0; id < 4; id++ )
    {
        borg = tod_breather_data::partner_bench_org( id );
        byaw = tod_breather_data::partner_bench_yaw( id );
        bench = Spawn( "script_model", borg );
        if ( !isdefined( bench ) ) { log( "TABLE_FAIL id=" + id + " reason=spawn" ); continue; }
        bench SetModel( "p8_zm_crafting_table" );
        bench.angles = ( 0, byaw, 0 );
        log( "TABLE id=" + id + " room=" + tod_breather_data::partner_bench_room( id ) + " org=" + borg + " yaw=" + byaw );
    }
    log( "WORKSHOP ready tables=4 prompts=0 (companions come from the dealer, docs/209)" );
}

// Four benches in one row in the south nave, facing north toward the dais:
// y = hall centre - 308 (between the 8200 and 8424 pier rows), x 170 apart so
// the 48-unit trigger cylinders keep a 74-unit gap. Script models only, not
// solid: nothing is cut into the map, zombie paths are unchanged.
function test_benches()
{
    level endon( "end_game" );
    level flag::wait_till( "initial_blackscreen_passed" );
    c = tod_crown_data::hall_center();
    xs = array( -255, -85, 85, 255 );
    yaw = 90;
    fwd = AnglesToForward( ( 0, yaw, 0 ) );
    for ( id = 0; id < 4; id++ )
    {
        borg = ( xs[ id ], c[ 1 ] - 308, c[ 2 ] );
        bench = Spawn( "script_model", borg );
        if ( !isdefined( bench ) ) { log( "TEST_BENCH_FAIL id=" + id + " reason=bench_spawn" ); continue; }
        bench SetModel( "p8_zm_crafting_table" );
        bench.angles = ( 0, yaw, 0 );
        bench NotSolid();
        t = use_trigger( borg + fwd * 57 + ( 0, 0, 36 ), 48 );
        t.tod_type = id; t.tod_test = true;
        test_bench_hint( t, id );
        display = Spawn( "script_model", borg + fwd * 2 + ( 0, 0, 46 ) );
        if ( isdefined( display ) )
        {
            display SetModel( level.tod_partner_defs[ id ].model );
            display SetScale( 0.55 );
            display.angles = ( 0, yaw, 0 );
            display NotSolid();
            if ( id == 2 ) display.origin = display.origin + ( 0, 0, 10 );
        }
        t thread bench_loop();
        log( "TEST_BENCH id=" + id + " org=" + borg + " trig=" + t.origin + " yaw=" + yaw );
    }
    log( "TEST_BENCHES ready crown=4 free_equip=1 free_swap=1 dismiss=1" );
}

// Four more permanent strings (constant, never interpolated).
function test_bench_hint( t, id )
{
    switch ( id )
    {
        case 0: t SetHintString( "Hold ^3[{+activate}]^7 ^5PARTNER BENCH^7 - Protector test / Equip or swap freely" ); break;
        case 1: t SetHintString( "Hold ^3[{+activate}]^7 ^5PARTNER BENCH^7 - Talon test / Equip or swap freely" ); break;
        case 2: t SetHintString( "Hold ^3[{+activate}]^7 ^5PARTNER BENCH^7 - R.A.P.S. test / Equip or swap freely" ); break;
        case 3: t SetHintString( "Hold ^3[{+activate}]^7 ^5PARTNER BENCH^7 - Cerberus test / Equip or swap freely" ); break;
    }
}

// The test bench's whole action: equip (or swap to) this partner at full health
// with no rebuild wait; use it again while equipped to dismiss.
function test_bench_action( bench )
{
    self endon( "disconnect" );
    level endon( "end_game" );
    s = self.tod_ptn; id = bench.tod_type;
    d = level.tod_partner_defs[ id ];
    if ( s.chosen == id && isdefined( s.actor ) )
    {
        retire( s, "test_dismiss" );
        s.chosen = -1;
        s.hp[ id ] = max_hp( s, id ); s.ready[ id ] = 0;
        self IPrintLn( "^5" + d.title + "^7 dismissed." );
        push_items( self );
        log( "TEST_DISMISS owner=" + self GetEntityNumber() + " type=" + id );
    }
    else
    {
        previous = s.chosen;
        retire( s, "test_switch" );
        s.chosen = id; s.retry = 0;
        s.hp[ id ] = max_hp( s, id ); s.ready[ id ] = 0;
        push_items( self );
        self IPrintLn( "^5" + d.title + " equipped.^7 Use again to dismiss." );
        self PlaySound( "zmb_cha_ching" );
        log( "TEST_EQUIP owner=" + self GetEntityNumber() + " type=" + id + " previous=" + previous );
    }
    while ( isalive( self ) && self UseButtonPressed() ) wait 0.05;
    wait 0.2;
    s.busy = false;
}

function use_trigger( org, radius )
{
    t = Spawn( "trigger_radius_use", org, 0, radius, 64 );
    t TriggerIgnoreTeam();
    t SetCursorHint( "HINT_NOICON" );
    return t;
}

// The crown TEST benches only (TOD_PARTNER_TEST_BENCHES): the docs/159 part pickups and workshop build / equip
// prompts were retired with the gift (docs/209). The same held key may never equip / dismiss twice.
function bench_loop()
{
    level endon( "end_game" );
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !usable( p ) ) continue;
        ensure_state( p );
        if ( p.tod_ptn.busy ) continue;
        p.tod_ptn.busy = true;
        p thread test_bench_action( self );
    }
}

function manager()
{
    level endon( "end_game" );
    level flag::wait_till( "initial_blackscreen_passed" );
    for ( ;; )
    {
        compact = [];
        foreach ( s in level.tod_partner_records )
        {
            if ( !isdefined( s.owner ) )
            {
                retire( s, "disconnect" ); clear_hud( s );
                if ( isdefined( s.gun ) ) s.gun Delete();
                continue;
            }
            compact[ compact.size ] = s;
            tick( s );
            push_hud( s );
            push_state( s );
        }
        level.tod_partner_records = compact;
        wait 0.1;
    }
}

function tick( s )
{
    p = s.owner;
    if ( !isalive( p ) ) { retire( s, "owner_dead" ); return; }
    if ( s.chosen < 0 ) return;
    now = GetTime(); id = s.chosen;
    if ( isdefined( s.actor ) && !isalive( s.actor ) )
    {
        start_rebuild( s, id, now );
        retire( s, "destroyed" );
    }
    if ( !isdefined( s.actor ) )
    {
        // Native actor cleanup can run before this poll. Retire its visible
        // proxy even while the death notification's rebuild timer is running.
        if ( isdefined( s.visual ) ) s.visual Delete();
        s.visual = undefined; s.target = undefined; s.loop_on = undefined;
        // One due back while its owner's cards or spin are up waits for the
        // screen to close: it never materialises into a frozen scene. Nor beside
        // a JUMP-PAD FLYER (LT-fix 2026-10-05): a spawn anchor refuses a flyer
        // (CLAUDE.md); it deploys the tick he lands.
        if ( !usable( p ) || isdefined( freeze_reason( p ) ) || IS_TRUE( p.tod_jumppad_flying ) || now < s.ready[ id ] || now < s.retry ) return;
        if ( s.hp[ id ] <= 0 ) s.hp[ id ] = max_hp( s, id );
        s.retry = now + 2000;
        deploy( s );
        return;
    }
    a = s.actor;
    s.hp[ id ] = a.health;
    why = freeze_reason( p );
    paused = isdefined( why );
    if ( paused != IS_TRUE( s.paused ) )
    {
        s.paused = paused;
        if ( paused ) freeze( s, a, why );
        else thaw( s, a, now );
    }
    else if ( paused && why != s.frz_why )
    {
        log( "PAUSE_REASON owner=" + p GetEntityNumber() + " type=" + id + " from=" + s.frz_why + " to=" + why );
        s.frz_why = why;
    }
    if ( paused ) return;
    nano_tick( s, a );   // after the pause gate: a frozen world never heals it
    // Refresh living targets at 5 Hz. Reuse for movement, attacks and pressure.
    if ( now >= s.next_goal )
    {
        s.next_goal = now + 200;
        nav = GetClosestPointOnNavMesh( a.origin, 72 );
        if ( isdefined( nav ) && abs( nav[ 2 ] - a.origin[ 2 ] ) < 64 )
            a.last_valid_position = nav;
        else path_start_watch( s, a, nav, now );   // diag only: its own origin is off the mesh (PATH_START_OFF)
        // Goal on the navmesh: a jumping / mid-stair owner is often off it,
        // and an off-mesh goal leaves the actor with no path (HasPath false).
        // owner_ground (LT-fix 2026-10-05) also covers an AIRBORNE owner, and it
        // is computed FIRST: target_for and raps_goal measure from it.
        goal = owner_ground( s, p, now );
        s.anchor = goal;
        s.target = target_for( s );
        if ( id == 2 ) goal = raps_goal( s, goal, now );
        s.goal = goal;
        // The companion BT sprints while this point is > 512 away and walks
        // inside 384 (zodcompanionkeepscurrentmovementmode); stock moves it with
        // the leader, the partner gate skipped that, so feed it the goal: the
        // partner sprints to catch up and walks beside its owner. R.A.P.S. is
        // handed a far point so it always runs its sprint cycle.
        a.v_robot_land_position = goal;
        if ( id == 2 ) a.v_robot_land_position = a.origin + ( 4096, 0, 0 );
        if ( id == 2 || DistanceSquared( a.origin, goal ) > 105 * 105 ) a SetGoal( goal, true );
        else a SetGoal( a.origin, true );
        if ( DistanceSquared( a.origin, s.last_origin ) > 24 * 24 )
        { s.last_origin = a.origin; s.stuck_since = now; }
        if ( IS_TRUE( p.tod_jumppad_flying ) )
        {
            // A JUMP-PAD FLYER IS UNTOUCHABLE (CLAUDE.md; LT-fix 2026-10-05): no teleport is anchored on him mid-flight
            // (the 10-02 run RECOVERed one 150 ms before LAND). Time under a flight is not "stuck"; the far rule brings
            // it to him the tick he lands.
            s.last_origin = a.origin; s.stuck_since = now;
            if ( !IS_TRUE( s.flyer_hold ) )
            {
                s.flyer_hold = true;
                log( "RECOVER_HOLD owner=" + p GetEntityNumber() + " type=" + id + " reason=owner_flying at=" + a.origin );
            }
        }
        else
        {
            if ( IS_TRUE( s.flyer_hold ) )
            {
                s.flyer_hold = undefined;
                log( "RECOVER_HOLD released owner=" + p GetEntityNumber() + " type=" + id + " owner_dist=" + int( Distance( a.origin, p.origin ) ) );
            }
            far = DistanceSquared( a.origin, p.origin ) > 900 * 900;
            // NOT STUCK AT ITS GOAL (LT-fix 2026-10-05): a R.A.P.S. parked on the zombie it charges, blasting on its
            // recharge, is fighting, not stuck - the 17:33 run teleported it off two floor-40 guardians it was hitting
            // (RECOVER stuck=1, goal_dist 20-25). Stuck = not moving AND short of its goal AND away from its owner.
            stuck = ( now - s.stuck_since > 7000 && DistanceSquared( a.origin, p.origin ) > 220 * 220 && DistanceSquared( a.origin, goal ) > 64 * 64 );
            if ( far || stuck )
            {
                org = landing_point( p );
                if ( isdefined( org ) )
                {
                    gd = int( Distance( a.origin, goal ) );   // measured before the teleport moves it
                    a ForceTeleport( org ); a SetGoal( org, true );
                    // Snap the drone/tank with its body; a 0.1 s MoveTo would slide it across the map.
                    if ( isdefined( s.visual ) ) { s.visual.origin = org; s.visual_last = org; }
                    log( "RECOVER owner=" + p GetEntityNumber() + " type=" + id + " far=" + far + " stuck=" + stuck + " goal_dist=" + gd + " to=" + org );
                }
                s.last_origin = a.origin; s.stuck_since = now;
            }
        }
    }
    visual_tick( s );
    move_watch( s, now );
    if ( id == 2 ) raps_touch( s, now );   // THE BOWLING BALL: it hits what it rolls into
    if ( now >= s.next_shot && isdefined( s.target ) && isalive( s.target ) ) attack( s );
    if ( now >= s.next_log )
    {
        s.next_log = now + 10000;
        target_num = -1;
        if ( isdefined( s.target ) ) target_num = s.target GetEntityNumber();
        log( "STATUS owner=" + p GetEntityNumber() + " type=" + id + " hp=" + a.health + " distance=" + int( Distance( a.origin, p.origin ) ) + " target=" + target_num + " attacks=" + s.shots + " kills=" + s.kills );
    }
}

// THE COMPANION HOLDS STILL WHILE ITS OWNER IS OUT OF THE FIGHT (user 2026-09-29:
// "your AI partner companion should also freeze so we can't kill things while you
// are spinning or getting your cards"). The user's 15:32 run showed why: in every
// 10 s Black Market spin the zombies ignored the spinner and the Cerberus shot
// ~50 times, killed 2-8 of them and paid its owner for each. Why it is frozen:
//   world_pause  a round deal, a solo altar deal or the arena's win deal froze everything
//   owner_spin   its owner is spinning the Black Market (_tod_shop spin_lock), for
//                the WHOLE spin, including the gap while a card deal takes it over
//   owner_menu   its owner is menu-frozen by a card deal
//   owner_cards  its owner's co-op altar deal (tod_solo_upg_active): the same card
//                screen, which never calls menu_freeze; its status plate hides for
//                all three owner states already (the HUD veil, TodCompanionPlate.lua)
// A DOWNED owner releases it (9c review): a companion fights over a crawling owner.
// Returns undefined when it may fight.
function freeze_reason( p )
{
    if ( IS_TRUE( level.tod_upgrade_pause ) ) return "world_pause";
    if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) ) return undefined;
    if ( p laststand::player_is_in_laststand() ) return undefined;
    if ( IS_TRUE( p.tod_spin_locked ) ) return "owner_spin";
    if ( IS_TRUE( p.tod_menu_frozen ) ) return "owner_menu";
    if ( IS_TRUE( p.tod_solo_upg_active ) ) return "owner_cards";
    return undefined;
}

// Stops it where it stands and takes it out of the fight both ways: no shots
// (ignoreall; tick returns before attack and nano_tick), no zombie targets it
// (ignoreme; closest_target skips a paused partner) and nothing hurts it
// (incoming_damage). What it overwrites is snapshotted for thaw (9c review:
// hand back the companion's own state, never fixed values).
function freeze( s, a, why )
{
    p = s.owner;
    s.frz_ignoreall = a.ignoreall; s.frz_ignoreme = a.ignoreme;
    s.frz_why = why; s.frz_ms = GetTime();
    s.frz_shots = s.shots; s.frz_kills = s.kills; s.frz_blocked = 0;
    a.ignoreall = true; a.ignoreme = true;
    a ASMSetAnimationRate( 0.01 );
    a ClearPath(); a SetGoal( a.origin, true );
    s.target = undefined;
    loop_set( s, false );   // PK22: a frozen companion is a silent one (visual_tick starts it again after the thaw)
    log( "PAUSE value=1 owner=" + p GetEntityNumber() + " type=" + s.chosen + " why=" + why + " hp=" + a.health
       + " ignoreall_was=" + IS_TRUE( s.frz_ignoreall ) + " ignoreme_was=" + IS_TRUE( s.frz_ignoreme ) );
}

// Hands back what freeze took, re-goals it this tick and restarts the stuck and
// stall clocks: time spent frozen is not "stuck" (a 10 s spin would otherwise
// RECOVER-teleport it the moment the screen closed). The PAUSE value=0 line is
// the playtest proof: shots_during and kills_during must read 0.
function thaw( s, a, now )
{
    p = s.owner;
    a.ignoreall = s.frz_ignoreall; a.ignoreme = s.frz_ignoreme;
    a ASMSetAnimationRate( s.rate );
    s.next_goal = 0;
    s.last_origin = a.origin; s.stuck_since = now;
    s.move_ref = a.origin; s.move_ref_ms = now;
    log( "PAUSE value=0 owner=" + p GetEntityNumber() + " type=" + s.chosen + " why_was=" + s.frz_why + " held_ms=" + ( now - s.frz_ms )
       + " shots_during=" + ( s.shots - s.frz_shots ) + " kills_during=" + ( s.kills - s.frz_kills ) + " hits_blocked=" + s.frz_blocked
       + " ignoreall=" + IS_TRUE( a.ignoreall ) + " ignoreme=" + IS_TRUE( a.ignoreme ) + " rate=" + s.rate );
}

// THE OWNER'S GROUND (LT-fix 2026-10-05; the user's 17:33 run). The point on the navmesh a companion follows and
// fights around. A jumping, falling or flying owner is OFF the mesh, and the old fallback goaled the companion at his
// raw origin IN THE AIR: PATHFIND_FAILURE_INVALID_END to z 19741 (350 u over the crown floor) 250 ms after a jump-pad
// launch, and to the owner mid-fall through the lap-45 / lap-42 drops; target_for and raps_goal measured from that
// air point too, dropped every zombie (target=-1) and the companion stood idle until he landed. Now: the mesh under
// him, else stock's last_valid_position (player_shared keeps the last on-mesh point while he is off it), else his
// origin (the old behaviour, never worse). OWNER_OFF_MESH / OWNER_ON_MESH mark each off-mesh spell once.
function owner_ground( s, p, now )
{
    goal = GetClosestPointOnNavMesh( p.origin, 96, 24 );
    if ( isdefined( goal ) )
    {
        if ( isdefined( s.air_ms ) )
        {
            log( "OWNER_ON_MESH owner=" + p GetEntityNumber() + " type=" + s.chosen + " off_ms=" + ( now - s.air_ms ) + " at=" + goal );
            s.air_ms = undefined;
        }
        return goal;
    }
    how = "last_valid_position";
    goal = p.last_valid_position;
    if ( !isdefined( goal ) ) { goal = p.origin; how = "origin"; }
    if ( !isdefined( s.air_ms ) )
    {
        s.air_ms = now;
        log( "OWNER_OFF_MESH owner=" + p GetEntityNumber() + " type=" + s.chosen + " anchor=" + how + " flying=" + IS_TRUE( p.tod_jumppad_flying )
           + " owner_at=" + p.origin + " goal=" + goal );
    }
    return goal;
}

// PATH_START_OFF (LT-fix 2026-10-05, diagnostics only - it changes nothing). The 17:33 run's R.A.P.S. logged nine
// PATHFIND_FAILURE_INVALID_START with its own origin 67-124 u ABOVE ordinary descending flights, while it travelled
// along them; why it rides that high is unproven (that run's always-sprint lane, ~885 u/s, is the leading suspect;
// THE BOWLING BALL's slower rates may already change it). Once a second while the companion's own origin is off the
// mesh: how high, over what floor, how fast, toward what.
function path_start_watch( s, a, nav, now )
{
    if ( isdefined( s.next_off_log ) && now < s.next_off_log ) return;
    s.next_off_log = now + 1000;
    nav_dz = -1;
    if ( isdefined( nav ) ) nav_dz = int( a.origin[ 2 ] - nav[ 2 ] );
    ground_hit = BulletTrace( a.origin + ( 0, 0, 8 ), a.origin - ( 0, 0, 400 ), false, a );
    ground_pos = ground_hit[ "position" ];
    log( "PATH_START_OFF owner=" + s.owner GetEntityNumber() + " type=" + s.chosen + " org=" + a.origin + " nav=" + isdefined( nav ) + " nav_dz=" + nav_dz
       + " floor_dz=" + int( a.origin[ 2 ] - ground_pos[ 2 ] ) + " speed=" + int( Length( a GetVelocity() ) ) + " haspath=" + ( a HasPath() )
       + " raps=" + s.raps_mode + " goal=" + s.goal );
}

// R.A.P.S.: ram its LOCKED zombie near the owner, else circle the owner.
// owner_goal = the owner's ground (owner_ground, LT-fix): the lock / release / orbit tests measure from it, never
// from an airborne origin.
function raps_goal( s, owner_goal, now )
{
    p = s.owner; a = s.actor;
    base = owner_goal;
    sight = item_mult( s, TOD_ITEM_SIGHT );
    z = s.raps_lock;
    if ( isdefined( z ) )
    {
        why = "";
        if ( !isalive( z ) || IS_TRUE( z.tod_dropping ) ) why = "dead";
        else if ( Distance( z.origin, base ) > TOD_PTN_RAPS_RELEASE_R * sight ) why = "far";
        else if ( isdefined( z.tod_necro_binder ) ) why = "bound";   // a Necromancer took it
        else if ( now - s.raps_lock_touch > TOD_PTN_RAPS_LOCK_MS ) why = "no_touch";
        if ( why != "" )
        {
            log( "RAPS_RELEASE owner=" + p GetEntityNumber() + " target=" + z GetEntityNumber() + " why=" + why + " held_ms=" + ( now - s.raps_lock_ms ) );
            if ( why == "no_touch" ) s.raps_skip = z;   // it could not reach that one: do not lock it straight back
            s.raps_lock = undefined;
            z = undefined;
        }
    }
    if ( !isdefined( z ) && isdefined( s.target ) && isalive( s.target ) && s.target !== s.raps_skip
         && Distance( s.target.origin, base ) < TOD_PTN_RAPS_HUNT_R * sight )
    {
        z = s.target;
        s.raps_lock = z; s.raps_lock_ms = now; s.raps_lock_touch = now;
    }
    if ( isdefined( z ) )
    {
        s.target = z;   // the blast follows the lock, not the nearest zombie of this instant
        goal = GetClosestPointOnNavMesh( z.origin, 64, 16 );
        if ( !isdefined( goal ) ) goal = z.origin;
        mode = "charge";
    }
    else
    {
        want = base + AnglesToForward( ( 0, s.orbit, 0 ) ) * TOD_PTN_RAPS_ORBIT_R;
        if ( now >= s.next_orbit || Distance2D( a.origin, want ) < 64 )
        {
            s.orbit = ( s.orbit + TOD_PTN_RAPS_ORBIT_STEP ) % 360;
            s.next_orbit = now + TOD_PTN_RAPS_ORBIT_MS;
            want = base + AnglesToForward( ( 0, s.orbit, 0 ) ) * TOD_PTN_RAPS_ORBIT_R;
        }
        goal = GetClosestPointOnNavMesh( want, 96, 16 );
        if ( !isdefined( goal ) || abs( goal[ 2 ] - base[ 2 ] ) > 48 ) goal = base;   // no floor there: roll to the owner
        mode = "orbit";
    }
    if ( mode != s.raps_mode )
    {
        s.raps_mode = mode;
        s.rate = ( ( mode == "charge" ) ? TOD_PTN_RAPS_RATE_CHARGE : TOD_PTN_RAPS_RATE_ORBIT );
        a ASMSetAnimationRate( s.rate );
        target_num = -1;
        if ( isdefined( z ) ) target_num = z GetEntityNumber();
        log( "RAPS_MODE " + mode + " owner=" + p GetEntityNumber() + " target=" + target_num + " rate=" + s.rate + " goal=" + goal );
    }
    return goal;
}

// THE BOWLING BALL: every zombie the R.A.P.S. rolls into takes a hit, once per
// TOD_PTN_RAPS_TOUCH_MS each; touching its locked zombie keeps the lock.
function raps_touch( s, now )
{
    a = s.actor;
    if ( !isdefined( a ) ) return;
    r2 = TOD_PTN_RAPS_TOUCH_R * TOD_PTN_RAPS_TOUCH_R;
    foreach ( z in GetAITeamArray( "axis" ) )
    {
        if ( !isdefined( z ) || !isalive( z ) || IS_TRUE( z.tod_is_partner ) || IS_TRUE( z.tod_dropping ) ) continue;
        if ( isdefined( z.tod_necro_binder ) ) continue;   // a Necromancer is binding it: leave it to the Necromancer
        if ( abs( z.origin[ 2 ] - a.origin[ 2 ] ) > 56 ) continue;
        dx = z.origin[ 0 ] - a.origin[ 0 ]; dy = z.origin[ 1 ] - a.origin[ 1 ];
        if ( dx * dx + dy * dy > r2 ) continue;
        if ( isdefined( z.tod_raps_touch_ms ) && now - z.tod_raps_touch_ms < TOD_PTN_RAPS_TOUCH_MS ) continue;
        z.tod_raps_touch_ms = now;   // raps_fling reads it: a kill from this touch is thrown
        if ( z === s.raps_lock ) s.raps_lock_touch = now;
        hp = z.health;
        dmg = deal_damage( s, z, TOD_PTN_RAPS_TOUCH_FRAC );
        s.raps_touches++;
        level thread fx_burst( TOD_PTN_HIT_FX, z.origin + ( 0, 0, 30 ), TOD_PTN_HIT_SECS );
        if ( s.raps_touches <= 5 || s.raps_touches % 10 == 0 )
            log( "RAPS_TOUCH owner=" + s.owner GetEntityNumber() + " target=" + z GetEntityNumber() + " n=" + s.raps_touches + " damage=" + dmg
               + " hp=" + hp + "->" + ( ( isdefined( z ) && isalive( z ) ) ? z.health : 0 ) + " locked=" + ( z === s.raps_lock ) );
    }
}

// THE BOWLING BALL'S THROW: an ordinary zombie the R.A.P.S. kills by rolling
// into it is thrown along the roll, with the stock punch's launch (the Warrior
// fling's numbers). Elites own their deaths; a body is thrown once (tod_bat_launched).
function raps_fling( s, z )
{
    if ( !isdefined( s ) || s.chosen != 2 || !isdefined( z ) || !isdefined( z.tod_raps_touch_ms ) ) return;
    if ( GetTime() - z.tod_raps_touch_ms > 100 ) return;   // the blast or anything else killed it: not a roll-over
    if ( IS_TRUE( z.is_boss ) || IS_TRUE( z.acc_is_boss ) || IS_TRUE( z.acc_is_mini_boss ) || isdefined( z.tod_boss_kind ) || IS_TRUE( z.tod_bat_launched ) ) return;
    if ( isdefined( level.ragdoll_limit_check ) && ![[ level.ragdoll_limit_check ]]() ) return;
    dir = AnglesToForward( ( 0, RandomInt( 360 ), 0 ) );
    if ( isdefined( s.actor ) )
    {
        v = s.actor GetVelocity();
        flat = ( v[ 0 ], v[ 1 ], 0 );
        if ( Length( flat ) < 60 ) flat = ( z.origin[ 0 ] - s.actor.origin[ 0 ], z.origin[ 1 ] - s.actor.origin[ 1 ], 0 );
        if ( Length( flat ) > 1 ) dir = VectorNormalize( flat );
    }
    impulse = dir * RandomIntRange( 125, 150 ) + ( 0, 0, RandomIntRange( 75, 150 ) );   // stock zombie_punch_death's
    z.tod_bat_launched = true;
    z StartRagdoll();
    z LaunchRagdoll( impulse );
    log( "RAPS_FLING owner=" + ( isdefined( s.owner ) ? s.owner GetEntityNumber() : -1 ) + " ent=" + z GetEntityNumber() + " impulse=" + impulse );
}

function landing_point( p )
{
    // Sample only the owner's current floor. Never teleport through a shut gate.
    for ( i = 0; i < 4; i++ )
    {
        yaw = p.angles[ 1 ] + 90 + i * 90;
        spot = p.origin + AnglesToForward( ( 0, yaw, 0 ) ) * 76;
        nav = GetClosestPointOnNavMesh( spot, 90 );
        if ( !isdefined( nav ) || abs( nav[ 2 ] - p.origin[ 2 ] ) > 48 ) continue;
        if ( !SightTracePassed( p.origin + ( 0, 0, 32 ), nav + ( 0, 0, 32 ), false, p ) ) continue;
        hit = BulletTrace( nav + ( 0, 0, 32 ), nav - ( 0, 0, 48 ), false, p );
        if ( hit[ "fraction" ] < 1 ) return hit[ "position" ] + ( 0, 0, 1 );
    }
    return undefined;
}

function deploy( s )
{
    // Stock get_current_actor_count counts AXIS actors + corpses. The zombie
    // cap (_tod_corpse_cleanup::ai_limit_watch) holds that under 60 minus one
    // slot per player minus every live ally, so the partner's slot is always
    // there below 60. The old 58 here refused a slot the cap had reserved and
    // left a partner "DEPLOYING" through every full round (review 2026-09-28).
    actors = GetAISpeciesArray( "all", "all" );
    corpses = GetCorpseArray();
    count = 0;
    if ( isdefined( actors ) ) count += actors.size;
    if ( isdefined( corpses ) ) count += corpses.size;
    if ( count >= 60 )
    { log( "SPAWN_RETRY actor_budget owner=" + s.owner GetEntityNumber() + " type=" + s.chosen + " count=" + count + " free=" + GetFreeActorCount() ); return; }
    p = s.owner; id = s.chosen;
    org = landing_point( p );
    if ( !isdefined( org ) ) { log( "SPAWN_RETRY no_owner_floor_nav owner=" + p GetEntityNumber() + " type=" + id + " org=" + p.origin ); return; }
    a = SpawnActor( "spawner_tod_partner", org, ( 0, p.angles[ 1 ], 0 ), "tod_partner", true );
    if ( !isdefined( a ) ) { log( "SPAWN_RETRY SpawnActor_undefined type=" + id ); return; }
    // 1 = archetype_zod_companion saw the targetname in its spawn setup and
    // skipped the stock follow / revive / powerup / gib threads. 0 = those
    // threads are running on this partner: the first thing to read in a log.
    pregated = IS_TRUE( a.tod_is_partner );
    a.tod_is_partner = true; a.tod_partner_owner = p; a.tod_partner_state = s;
    a.b_robot_finished = 1; a.reviving_a_player = 1;
    a.combatmode = "no_cover"; a.ignore_enemy_count = true; a.ignore_nuke = true;
    a.disableAmmoDrop = true; a.can_gib_zombies = 0; a.tod_boss_custom_speed = true;
    a.allow_zombie_to_target_ai = 1; a.ignoreme = false;
    // The drones never fire the body's native rifle (their shots are scripted
    // from the visual): no native enemy, so the BT's exposed shoot branch never
    // runs. The Civil Protector keeps its native aim/shoot animations.
    s.quiet = ( id != 0 );
    a.ignoreall = s.quiet;
    a.last_valid_position = org;
    a SetPlayerCollision( false ); a DisableAimAssist();
    a.maxhealth = max_hp( s, id );
    if ( s.hp[ id ] > a.maxhealth ) s.hp[ id ] = a.maxhealth;
    a.health = s.hp[ id ];
    a.goalRadius = 48; a SetGoal( org, true );
    AiUtility::AddAIOverrideDamageCallback( a, &incoming_damage );
    s.actor = a; s.paused = false; s.next_shot = GetTime() + 1000;
    s.generation++;
    a thread partner_death( s, id, s.generation );
    s.next_goal = 0; s.shots = 0; s.kills = 0;
    s.next_off_log = 0; s.air_ms = undefined; s.flyer_hold = undefined; s.anchor = undefined;   // LT-fix: the ground anchor + its diagnostics
    s.last_origin = org; s.stuck_since = GetTime(); s.roll = 0; s.visual_last = org;
    s.move_ref = org; s.move_ref_ms = GetTime(); s.next_move_log = GetTime() + TOD_PTN_MOVE_LOG_MS;
    s.next_stall_log = 0; s.goal = org; s.dmg_taken = 0; s.dmg_hits = 0; s.dmg_from = ""; s.next_dmg_log = 0;
    s.skip_logged = 0; s.hover_phase = RandomInt( 360 );
    s.rate = 1.0; s.orbit = RandomInt( 360 ); s.next_orbit = 0; s.raps_mode = ""; s.raps_lock = undefined; s.raps_skip = undefined; s.raps_touches = 0;
    if ( id == 2 ) { s.rate = TOD_PTN_RAPS_RATE_ORBIT; a ASMSetAnimationRate( s.rate ); }
    if ( id != 0 )
    {
        // NOT Hide(): a hidden entity is not sent to clients, and on the first
        // playtest (2026-09-28 11:28) every hidden walker stood still (Cerberus
        // 75 -> 297 from its owner, stuck=1; Talon 435) and none of its shot /
        // zap client FX drew. HidePart on j_mainroot (all 49,050 Protector
        // vertices hang under it) hides only the body mesh; the actor stays
        // networked and animating exactly like the Civil Protector.
        a DetachAll();
        a HidePart( "j_mainroot", "", true );
        // The body's own weapon model is attached to its hand, not part of the
        // mesh, so HidePart leaves it FLOATING under the drone (user 2026-09-28:
        // "why do these all have guns ... floating guns"). Stock's gun_remove
        // puts it nowhere; the partner's shots never used it.
        a ai::gun_remove();
        s.visual = Spawn( "script_model", org );
        s.visual SetModel( level.tod_partner_defs[ id ].model );
        s.visual.angles = a.angles;
        s.visual NotSolid();
        s.loop_on = undefined; s.moved_ms = undefined;   // PK22: a fresh visual starts silent; visual_tick starts its loop
    }
    else a Attach( "wm_t9_ak47_full", "tag_weapon_right", true );
    tod_boss_fx::attach( a, id + 3 ); // existing 3-bit actor field; no new pool bits
    arrive_fx( org );
    log( "SPAWN owner=" + p GetEntityNumber() + " type=" + id + " actor=" + a GetEntityNumber() + " hp=" + a.health + "/" + a.maxhealth + " pregated=" + pregated + " gun_removed=" + IS_TRUE( a.gun_removed ) + " rate=" + s.rate + " team=" + a.team + " visual=" + isdefined( s.visual ) + " org=" + org + " owner_dist=" + int( Distance( org, p.origin ) ) );
}

// THE ARRIVAL (docs/209): a companion never just pops in beside its owner - the dealer's gift, a rebuild coming back,
// a respawn or a tester's bench pick all MATERIALISE with the teleporter's own arrival (the look a recalled player
// gets, _tod_recall): the kino beam, the bright discharge + release field, the derez and the warp, all on host-based
// lanes that render in this map (_tod_teleport fx_burst / discharge -> tag_origin carriers, a script_origin sound).
function arrive_fx( org )
{
    level thread tod_teleport::fx_burst( "tod_tp_kino", org + ( 0, 0, 4 ), 2.0 );
    tod_teleport::discharge( org );
}

// THE DROP (LT-fix 2026-10-05, staged first as LT-mocomp; the user's 17:33 run, archive tmp/elite_tracking/runs/20261005_175358_367_fe125096).
// The broken tower's 24 drops are stock Giant negotiation pairs (animscript zm_jump_down_190, gen_tower_map.js). The
// companion's STOCK selector table (zod_robot_companion.ai_ast, combat_traverse@traversal) has rows for JUMP_DOWN_190
// but none for zm_jump_down_190, so a companion following its owner down a drop falls to the table's "*" row:
// ANIM_EXPOSED_IDLE + mocomp_teleport_traversal@zombie, a mocomp Shadows of Evil registers in its own level scripts
// and NOTHING in this map did. Stock RunAnimationMocomp indexed the missing entry on every frame of that traversal:
// two SCRIPTERRORs per server frame in animation_state_machine_mocomp.gsc ("undefined is not an array, string, or
// vector" + "undefined is not a function pointer"; 211 pairs in that run, ~58 per drop, the R.A.P.S.; the Protector
// did the same on 2026-09-28 and 10-02), while the companion stood at the lip for ~2.9 s (MOVE_STALL speed=0) and
// only then popped to the floor below. This registers that stock mocomp the way stock's own teleport traversals
// work (zombie_quad's quadTeleportTraversalMocompStart): at the traversal's start the actor steps to the drop's END
// node, and a companion MATERIALISES there with its own arrival (arrive_fx, the look every deploy wears) and its
// drone body snaps with it. Guarded: an existing registration is never replaced. What it cannot shorten: the "*"
// row still plays ANIM_EXPOSED_IDLE for the state's length at the landing (TRAVERSE_END held_ms measures it); a
// selector row for zm_jump_down_190 (a real robot jump-down) is the follow-up, tmp/logtriage/LT-fix/LAND.md part B.
function register_drop_traversal()
{
    if ( !isdefined( level._AnimationMocomps ) )
    {
        log( "TRAVERSE_MOCOMP skipped reason=no_mocomp_table name=" + TOD_PTN_TRAV_MOCOMP );
        return;
    }
    if ( isdefined( level._AnimationMocomps[ TOD_PTN_TRAV_MOCOMP ] ) )
    {
        log( "TRAVERSE_MOCOMP kept reason=already_registered name=" + TOD_PTN_TRAV_MOCOMP );
        return;
    }
    AnimationStateNetwork::RegisterAnimationMocomp( TOD_PTN_TRAV_MOCOMP, &drop_traverse_start, undefined, &drop_traverse_end );
    log( "TRAVERSE_MOCOMP registered name=" + TOD_PTN_TRAV_MOCOMP + " start=teleport_to_end_node end=log" );
}

// Mocomp START (runs inside the native ASM: no wait, no endon). zonly_physics, not zombie_quad's "normal": the idle
// that follows has no root motion, so the companion holds exactly at the landing instead of code-sliding in an idle
// pose (the 17:33 run's failed traversals drifted 290 u in one drop and sat at the lip in two others).
function drop_traverse_start( entity, mocompAnim, mocompAnimBlendOutTime, mocompAnimFlag, mocompDuration )
{
    if ( !isdefined( entity ) ) return;
    entity OrientMode( "face angle", entity.angles[ 1 ] );
    entity AnimMode( "zonly_physics" );
    entity.tod_drop_ms = GetTime();
    node = entity.traverseEndNode;
    kind = "none";
    if ( isdefined( entity.traverseStartNode ) && isdefined( entity.traverseStartNode.animscript ) ) kind = entity.traverseStartNode.animscript;
    if ( !isdefined( node ) )
    {
        log( "TRAVERSE_SKIP reason=no_end_node actor=" + entity GetEntityNumber() + " kind=" + kind + " at=" + entity.origin );
        return;
    }
    src = entity.origin;
    dst = node.origin;
    ang = entity.angles;
    if ( isdefined( node.angles ) ) ang = node.angles;
    entity ForceTeleport( dst, ang, false );
    s = entity.tod_partner_state;
    if ( !IS_TRUE( entity.tod_is_partner ) || !isdefined( s ) || !isdefined( s.actor ) || s.actor != entity )
    {
        log( "TRAVERSE_TELEPORT partner=0 actor=" + entity GetEntityNumber() + " kind=" + kind + " from=" + src + " to=" + dst );
        return;
    }
    now = GetTime();
    // The drone's visible body goes with it (RECOVER's idiom): a 0.1 s MoveTo would slide it down the drop face.
    if ( isdefined( s.visual ) ) { s.visual.origin = dst; s.visual_last = dst; }
    // A drop is progress: the stuck / stall clocks restart at the landing.
    s.last_origin = dst; s.stuck_since = now;
    s.move_ref = dst; s.move_ref_ms = now;
    level thread arrive_fx( dst );
    owner_num = -1; owner_dist = -1;
    if ( isdefined( s.owner ) && isplayer( s.owner ) ) { owner_num = s.owner GetEntityNumber(); owner_dist = int( Distance( dst, s.owner.origin ) ); }
    log( "TRAVERSE_TELEPORT partner=1 owner=" + owner_num + " type=" + s.chosen + " actor=" + entity GetEntityNumber() + " kind=" + kind
       + " from=" + src + " to=" + dst + " drop=" + int( src[ 2 ] - dst[ 2 ] ) + " owner_dist=" + owner_dist + " visual=" + isdefined( s.visual ) );
}

// Mocomp TERMINATE: the traversal state is over. held_ms is how long the "*" row's idle held it at the landing.
function drop_traverse_end( entity, mocompAnim, mocompAnimBlendOutTime, mocompAnimFlag, mocompDuration )
{
    if ( !isdefined( entity ) ) return;
    held = -1;
    if ( isdefined( entity.tod_drop_ms ) ) held = GetTime() - entity.tod_drop_ms;
    entity.tod_drop_ms = undefined;
    log( "TRAVERSE_END actor=" + entity GetEntityNumber() + " partner=" + IS_TRUE( entity.tod_is_partner ) + " held_ms=" + held + " at=" + entity.origin );
}

function partner_death( s, id, generation )
{
    level endon( "end_game" );
    org = self.origin;
    self waittill( "death" );
    // Capture before the archetype can delete its actor. Polling alone misses
    // short death lifetimes and would respawn with the last cached health.
    if ( s.generation != generation ) return;
    start_rebuild( s, id, GetTime() );
    log( "DEATH type=" + id + " generation=" + generation + " recharge_until=" + s.ready[ id ] + " rebuild_ms=" + s.ready_len[ id ] );
    // PK22: where it fell - the drone's visible body when it has one (the actor under it is hidden), else the robot
    if ( isdefined( self ) ) org = self.origin + ( 0, 0, 36 );
    if ( isdefined( s.visual ) ) org = s.visual.origin + ( 0, 0, 8 );
    level thread destroyed_fx( s, id, org, generation );
}

// PK22: THE DESTRUCTION. The blast flash + a shower of sparks on host carriers (the lanes that render here: never a
// bare PlayFX), the crunch and the dying whine from a script_origin at the spot (a custom 3D alias plays from an
// entity; PlaySoundAtPosition is silent for it), and the owner's 2D "signal lost". The drone's visual stops its loop
// the moment it dies (the manager deletes it within the 0.1 s tick; Delete ends the loop).
function destroyed_fx( s, id, org, generation )
{
    if ( isdefined( s.visual ) ) { s.visual StopLoopSound( 0.05 ); s.loop_on = false; }
    level thread fx_burst( TOD_PTN_BLAST_FX, org, 0.6 );
    level thread fx_burst( TOD_PTN_HIT_FX, org, TOD_PTN_DEATH_SECS );
    e = Spawn( "script_origin", org );
    if ( isdefined( e ) )
    {
        e PlaySound( "tod_ptn_destroyed" );
        e thread delete_after( 4 );
    }
    p = s.owner;
    if ( isdefined( p ) && IsPlayer( p ) ) p PlayLocalSound( "tod_ptn_destroyed_plr" );
    log( "DESTROYED_FX type=" + id + " generation=" + generation + " org=" + org + " sound_host=" + isdefined( e ) + " owner_cue=" + ( isdefined( p ) && IsPlayer( p ) ) );
}

function delete_after( secs )   // self = a temp sound host
{
    wait secs;
    if ( isdefined( self ) ) self Delete();
}

// PK22: the movement loop on the visual (Talon / R.A.P.S. / Cerberus; the Civil Protector walks on its own feet).
// Change-gated: the call costs nothing when nothing changed.
function loop_set( s, on )
{
    if ( !isdefined( s.visual ) ) return;
    if ( IS_TRUE( on ) == IS_TRUE( s.loop_on ) ) return;
    s.loop_on = IS_TRUE( on );
    if ( !s.loop_on ) { s.visual StopLoopSound( TOD_PTN_LOOP_FADE ); return; }
    if ( s.chosen == 1 ) s.visual PlayLoopSound( "tod_ptn_talon_hover_lp", TOD_PTN_LOOP_FADE );
    else if ( s.chosen == 2 ) s.visual PlayLoopSound( "tod_ptn_raps_roll_lp", TOD_PTN_LOOP_FADE );
    else if ( s.chosen == 3 ) s.visual PlayLoopSound( "tod_ptn_cerberus_servo_lp", TOD_PTN_LOOP_FADE );
}

function retire( s, reason )
{
    if ( isdefined( s.actor ) )
    {
        if ( isalive( s.actor ) && s.chosen >= 0 ) s.hp[ s.chosen ] = s.actor.health;
        else if ( s.chosen >= 0 && s.hp[ s.chosen ] > 0 )
        {
            // A bench press can arrive between death and the manager tick.
            start_rebuild( s, s.chosen, GetTime() );
        }
        // Stale the death watcher BEFORE the delete: if deleting the actor
        // raises its "death" notify, partner_death would otherwise book a
        // swapped-out or dismissed partner as destroyed (health 0 + the 45 s
        // rebuild) - breaking "health persists through switches".
        s.generation++;
        s.actor Delete();
        log( "RETIRE type=" + s.chosen + " reason=" + reason );
    }
    if ( isdefined( s.visual ) ) s.visual Delete();   // (Delete ends its movement loop too - PK22)
    s.actor = undefined; s.visual = undefined; s.target = undefined; s.loop_on = undefined;
}

function end_cleanup()
{
    level waittill( "end_game" );
    foreach ( s in level.tod_partner_records )
    {
        retire( s, "end_game" ); clear_hud( s );
        if ( isdefined( s.gun ) ) s.gun Delete();
    }
}

// THE COMPANION STATUS PLATE (PK08, 2026-10-05, W2G). The companion's HUD readout was three server hudelems here
// (status_hud: a stock-font "TALON - REBUILDING" label over two plain white quads) - the one stock-font, flat-box
// piece on the HUD. It is a LUI plate now (TodCompanionPlate.lua, art by tools/artgen/packs/w2g_companion_plate.py):
// the portrait in a neon ring that says the state, the name and state in the map's typeface, the player's own
// health-bar art. The server owns the state and sends ONE int event to the OWNER (never a teammate):
//   tod_ptn_hud ( companion + 1, state, value, len, flags )
//     state  TOD_PTN_UI_* (push_state's codes)
//     value  active / deploying: health percent in 5 % steps (a living one never reads 0; one on its way after a
//            rebuild reads 100, the health it comes back with); rebuilding: whole seconds until it is back
//     len    rebuilding: the rebuild's whole length in seconds (QUICK REBOOT, even mid-rebuild), else 0
//     flags  TOD_PTN_HUD_FROZEN (it holds still with its owner) + TOD_PTN_HUD_OUT (its owner is dead / spectating)
// Sent when that tuple changes, and re-sent unchanged every TOD_PTN_HUD_BEAT_MS: an eventstring reaches only a HUD
// alive when it fires, so a recreated HUD (or a late joiner's) is right within 3 s; the plate draws nothing for a
// same-tuple re-send. The HUD VEIL hides the plate with the rest of the HUD (it lives in tod_upgrade.lua's HudOnly),
// which is what status_hud's own veil test (tod_upgrade_pause / tod_menu_frozen / tod_solo_upg_active) did here.
// clear_hud hides it (the end of the match) and forgets the signature.
function clear_hud( s )
{
    s.hud_sig = undefined;
    if ( !isdefined( s.owner ) || !isplayer( s.owner ) ) return;
    s.owner LuiNotifyEvent( &"tod_ptn_hud", 5, 0, TOD_PTN_UI_NONE, 0, 0, 0 );
}

// the health percent the plate reads: 5 % steps, rounded up, a living companion never 0 (LOCKSTEP push_state's)
function hud_percent( s, comp )
{
    top = max_hp( s, comp ); hp = s.hp[ comp ];
    if ( top <= 0 || hp <= 0 ) return 100;   // nothing booked (back from a rebuild): it returns at full health
    value = int( ( hp * 100 + top - 1 ) / top );
    value = int( ( value + 4 ) / 5 ) * 5;
    if ( value > 100 ) value = 100;
    if ( value < 5 ) value = 5;
    return value;
}

function push_hud( s )
{
    p = s.owner;
    if ( !isdefined( p ) || !isplayer( p ) ) return;
    now = GetTime();
    comp = s.chosen; state = TOD_PTN_UI_NONE; value = 0; whole = 0; flags = 0;
    if ( comp >= 0 )
    {
        if ( !isalive( p ) ) flags += TOD_PTN_HUD_OUT;
        else if ( isdefined( freeze_reason( p ) ) ) flags += TOD_PTN_HUD_FROZEN;
        if ( now < s.ready[ comp ] )
        {
            state = TOD_PTN_UI_REBUILD;
            value = int( ( s.ready[ comp ] - now + 999 ) / 1000 );   // whole seconds, rounded up
            whole = int( ( s.ready_len[ comp ] + 999 ) / 1000 );   // the rebuild's whole length
            if ( whole < value ) whole = value;
        }
        else if ( isdefined( s.actor ) && isalive( s.actor ) )
        {
            state = TOD_PTN_UI_ACTIVE;
            value = hud_percent( s, comp );
        }
        else
        {
            state = TOD_PTN_UI_DEPLOYING;
            value = hud_percent( s, comp );
        }
    }
    sig = ( comp + 1 ) + "/" + state + "/" + value + "/" + whole + "/" + flags;
    if ( isdefined( s.hud_sig ) && s.hud_sig == sig && isdefined( s.hud_beat ) && now < s.hud_beat ) return;
    s.hud_beat = now + TOD_PTN_HUD_BEAT_MS;
    s.hud_sig = sig;
    p LuiNotifyEvent( &"tod_ptn_hud", 5, comp + 1, state, value, whole, flags );
    // Log the transitions (companion, state, flags), not every health step, rebuild second or heartbeat.
    moment = ( comp + 1 ) + "/" + state + "/" + flags;
    if ( !isdefined( s.hud_log ) || s.hud_log != moment )
    {
        s.hud_log = moment;
        log( "HUD owner=" + p GetEntityNumber() + " type=" + comp + " state=" + state + " value=" + value + " len=" + whole + " flags=" + flags );
    }
}

function visual_tick( s )
{
    if ( !isdefined( s.visual ) ) return;
    a = s.actor; id = s.chosen;
    org = a.origin;
    step = a.origin - s.visual_last;
    moved = Length( ( step[ 0 ], step[ 1 ], 0 ) );
    // Heading: the way it is travelling, or its target while fighting.
    yaw = a.angles[ 1 ];
    if ( moved > 2 ) yaw = VectorToAngles( ( step[ 0 ], step[ 1 ], 0 ) )[ 1 ];
    if ( id != 2 && isdefined( s.target ) && isalive( s.target ) ) yaw = VectorToAngles( s.target.origin - org )[ 1 ];
    ang = ( 0, yaw, 0 );
    if ( id == 1 )
    {
        // TALON: hovers at zombie-swipe height, bobs, leans into its travel.
        ceiling = BulletTrace( org + ( 0, 0, 24 ), org + ( 0, 0, TOD_PTN_TALON_HOVER + 40 ), false, a );
        lift = TOD_PTN_TALON_HOVER;
        if ( ceiling[ "fraction" ] < 1 )
        {
            ceiling_pos = ceiling[ "position" ];
            lift = ceiling_pos[ 2 ] - org[ 2 ] - 20;
        }
        if ( lift < 30 ) lift = 30;
        s.hover_phase = ( s.hover_phase + 18 ) % 360;
        lift = lift + 4 * Sin( s.hover_phase );
        lean = moved * 1.2;           // ~11 degrees at a walking 90 u/s
        if ( lean > 16 ) lean = 16;
        ang = ( lean, yaw, 3 * Sin( s.hover_phase * 0.5 ) );
        org = org + ( 0, 0, lift );
    }
    else if ( id == 2 )
    {
        // R.A.P.S. (Gorod Krovi body, axle along its Y, radius 18.2, centre
        // pivot): rolls exactly as far as it travels, 360 / (2 pi 18.2) = 3.15
        // degrees per unit, and sits on the floor at +18.
        if ( moved < 100 ) s.roll = int( s.roll + moved * 3.15 ) % 360;
        ang = ( s.roll, yaw, 0 );
        org = org + ( 0, 0, 18 );
    }
    s.visual_last = a.origin;
    s.visual MoveTo( org, 0.1 );
    s.visual RotateTo( ang, 0.1 );
    // PK22: the Talon's rotors hum the whole time it is out; the R.A.P.S.'s roll and Cerberus's servos run while it moves
    if ( id == 1 ) loop_set( s, true );
    else
    {
        if ( moved > TOD_PTN_MOVE_ON ) s.moved_ms = GetTime();
        loop_set( s, isdefined( s.moved_ms ) && GetTime() - s.moved_ms < TOD_PTN_MOVE_HOLD_MS );
    }
}

// Movement evidence. MOVE every TOD_PTN_MOVE_LOG_MS; MOVE_STALL the moment the
// actor makes no progress for TOD_PTN_STALL_MS while its goal is more than 150
// away (the exact failure of the first playtest), with the path state.
function move_watch( s, now )
{
    a = s.actor; p = s.owner;
    goal_dist = Distance( a.origin, s.goal );
    progressed = Distance( a.origin, s.move_ref );
    if ( progressed > 24 || goal_dist < 150 ) { s.move_ref = a.origin; s.move_ref_ms = now; }
    else if ( now - s.move_ref_ms >= TOD_PTN_STALL_MS && now >= s.next_stall_log )
    {
        s.next_stall_log = now + 1000;
        nav = GetClosestPointOnNavMesh( a.origin, 48 );
        log( "MOVE_STALL owner=" + p GetEntityNumber() + " type=" + s.chosen + " for_ms=" + ( now - s.move_ref_ms )
           + " org=" + a.origin + " goal=" + s.goal + " goal_dist=" + int( goal_dist ) + " owner_dist=" + int( Distance( a.origin, p.origin ) )
           + " haspath=" + ( a HasPath() ) + " on_nav=" + isdefined( nav ) + " paused=" + IS_TRUE( s.paused ) + " ignoreall=" + IS_TRUE( a.ignoreall ) );
    }
    if ( now >= s.next_move_log )
    {
        s.next_move_log = now + TOD_PTN_MOVE_LOG_MS;
        vgap = -1;
        if ( isdefined( s.visual ) ) vgap = int( Distance2D( s.visual.origin, a.origin ) );
        log( "MOVE owner=" + p GetEntityNumber() + " type=" + s.chosen + " owner_dist=" + int( Distance( a.origin, p.origin ) )
           + " goal_dist=" + int( goal_dist ) + " haspath=" + ( a HasPath() ) + " visual_gap=" + vgap + " roll=" + s.roll
           + " speed=" + int( Length( a GetVelocity() ) ) + " raps=" + s.raps_mode );
    }
}

// The nearest visible zombie near the companion and its owner, measured from the owner's GROUND (s.anchor, set by
// tick from owner_ground; LT-fix 2026-10-05): an airborne owner's origin dropped every zombie (target=-1).
function target_for( s )
{
    sight = item_mult( s, TOD_ITEM_SIGHT );
    best = undefined; nearest = 900 * 900 * sight * sight;
    anchor = s.owner.origin;
    if ( isdefined( s.anchor ) ) anchor = s.anchor;
    foreach ( z in GetAITeamArray( "axis" ) )
    {
        if ( !isdefined( z ) || !isalive( z ) || IS_TRUE( z.tod_is_partner ) || IS_TRUE( z.tod_dropping ) ) continue;
        if ( isdefined( z.tod_necro_binder ) ) continue;   // a Necromancer is binding it: leave it to the Necromancer
        if ( abs( z.origin[ 2 ] - anchor[ 2 ] ) > 150 ) continue;
        dist = DistanceSquared( z.origin, s.actor.origin );
        if ( dist >= nearest || DistanceSquared( z.origin, anchor ) > 950 * 950 * sight * sight ) continue;
        from = s.actor.origin + ( 0, 0, 40 );
        if ( s.chosen == 1 ) from = from + ( 0, 0, 30 );
        if ( !SightTracePassed( from, z.origin + ( 0, 0, 35 ), false, s.actor ) ) continue;
        nearest = dist; best = z;
    }
    return best;
}

function attack( s )
{
    a = s.actor; d = level.tod_partner_defs[ s.chosen ]; z = s.target;
    if ( isdefined( z.tod_necro_binder ) ) return;   // bound since the 5 Hz pick: the next pick skips it (target_for)
    reach_r = d.range * item_mult( s, TOD_ITEM_SIGHT );
    if ( DistanceSquared( a.origin, z.origin ) > reach_r * reach_r )
    {
        // Target seen but out of reach: say so (throttled) - "it never shoots".
        if ( GetTime() >= s.skip_logged )
        {
            s.skip_logged = GetTime() + 3000;
            log( "SHOT_SKIP out_of_range type=" + s.chosen + " target=" + z GetEntityNumber() + " dist=" + int( Distance( a.origin, z.origin ) ) + " range=" + int( reach_r ) );
        }
        return;
    }
    s.next_shot = GetTime() + int( d.interval * 1000 / item_mult( s, TOD_ITEM_OVERCLOCK ) );
    s.shots++;
    if ( s.chosen == 2 )
    {
        tod_boss_fx::zap_pulse( a );
        level thread fx_burst( TOD_PTN_BLAST_FX, a.origin + ( 0, 0, 16 ), 0.5 );
        hits = 0;
        blast = 170 * item_mult( s, TOD_ITEM_SIGHT );
        foreach ( target in GetAITeamArray( "axis" ) )
        {
            if ( !isdefined( target ) || !isalive( target ) || IS_TRUE( target.tod_dropping ) ) continue;
            if ( isdefined( target.tod_necro_binder ) ) continue;   // a Necromancer is binding it
            if ( DistanceSquared( target.origin, a.origin ) > blast * blast ) continue;
            if ( !SightTracePassed( a.origin + ( 0, 0, 24 ), target.origin + ( 0, 0, 30 ), false, a ) ) continue;
            deal_damage( s, target ); hits++;
        }
        arcs = arc_chain( s, a.origin, blast );
        log( "RAPS_BLAST owner=" + s.owner GetEntityNumber() + " targets=" + hits + " arcs=" + arcs + " radius=" + int( blast ) + " recharge_ms=" + int( d.interval * 1000 / item_mult( s, TOD_ITEM_OVERCLOCK ) ) );
    }
    else
    {
        tod_boss_fx::shot_pulse( a );
        from = muzzle( s );
        hp_before = z.health;
        dmg = deal_damage( s, z );
        tracer( from, z.origin + ( 0, 0, 44 ), s );
        if ( isdefined( z ) ) arc_chain( s, z.origin, 0, z );
        if ( s.shots <= 3 || s.shots % 10 == 0 )
        {
            after = -1;
            if ( isdefined( z ) && isalive( z ) ) after = z.health;
            log( "SHOT owner=" + s.owner GetEntityNumber() + " type=" + s.chosen + " n=" + s.shots + " target=" + z GetEntityNumber()
               + " dist=" + int( Distance( from, z.origin ) ) + " damage=" + dmg + " hp=" + hp_before + "->" + after + " from=" + from );
        }
    }
}

// Where the shot leaves: the Protector's gun hand, the Talon's belly, the
// Cerberus turret (the visual models are what players see).
function muzzle( s )
{
    if ( s.chosen == 0 || !isdefined( s.visual ) )
        return s.actor GetTagOrigin( "tag_weapon_right" ) + AnglesToForward( s.actor.angles ) * 18;
    fwd = AnglesToForward( ( 0, s.visual.angles[ 1 ], 0 ) );
    if ( s.chosen == 1 ) return s.visual.origin + fwd * 14 + ( 0, 0, -4 );
    return s.visual.origin + fwd * 26 + ( 0, 0, 30 );
}

// A visible bullet: a tag_origin host carrying the looping trail flies from
// the gun to the zombie, then a looping spark marks the hit and the host is
// deleted. One host per shot, alive ~0.4 s (Cerberus at 5 shots/s = ~2 live).
function tracer( from, to, s )
{
    h = Spawn( "script_model", from );
    if ( !isdefined( h ) ) { log( "FX_FAIL tracer_spawn type=" + s.chosen ); return; }
    h SetModel( "tag_origin" );
    h.angles = VectorToAngles( to - from );
    h thread tracer_fly( to );
}

function tracer_fly( to )
{
    self endon( "death" );
    WAIT_SERVER_FRAME;   // the host's DObj must exist before an effect binds to its tag
    PlayFXOnTag( TOD_PTN_TRACER_FX, self, "tag_origin" );
    t = Distance( self.origin, to ) / TOD_PTN_TRACER_SPEED;
    if ( t < 0.05 ) t = 0.05;
    self MoveTo( to, t );
    wait t;
    PlayFXOnTag( TOD_PTN_HIT_FX, self, "tag_origin" );
    wait TOD_PTN_HIT_SECS;
    self Delete();
}

// A looping effect shown for `secs` on its own host, then removed.
function fx_burst( fx, org, secs )
{
    h = Spawn( "script_model", org );
    if ( !isdefined( h ) ) return;
    h SetModel( "tag_origin" );
    WAIT_SERVER_FRAME;
    PlayFXOnTag( fx, h, "tag_origin" );
    wait secs;
    h Delete();
}

function deal_damage( s, target, frac )
{
    if ( !isdefined( frac ) ) frac = 1.0;
    hp = 15;   // map 1: 150 (power scale / 10, 2026-09-25)
    if ( isdefined( level.zombie_health ) ) hp = level.zombie_health;
    damage = int( hp * level.tod_partner_defs[ s.chosen ].fraction + 0.5 );
    if ( damage < 3 ) damage = 3;       // map 1: 25
    if ( damage > 350 ) damage = 350;   // map 1: 3500
    // HOLLOW POINT scales the capped hit; ARC CHAIN passes its fraction.
    damage = int( damage * item_mult( s, TOD_ITEM_HOLLOW ) * frac + 0.5 );
    if ( damage < 1 ) damage = 1;
    // The gun proxy intentionally has NO allow_zombie_to_target_ai. That flag
    // belongs only to the body; stock treats flagged attackers as players.
    s.gun.origin = s.actor.origin + ( 0, 0, 45 );
    target.damagehit_origin = s.gun.origin; // stock must not GetWeaponMuzzlePoint on a script_origin
    w = s.actor.weapon;
    if ( !isdefined( w ) ) w = level.weaponNone;
    target DoDamage( damage, target.origin + ( 0, 0, 35 ), s.gun, s.gun, undefined, "MOD_RIFLE_BULLET", 0, w );
    return damage;
}

function incoming_damage( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, offset, bone, model )
{
    s = self.tod_partner_state;
    // Nothing lands while the world or its owner's cards / spin hold it
    // (freeze_reason), including a swing that started before the freeze.
    if ( IS_TRUE( level.tod_upgrade_pause ) || ( isdefined( s ) && IS_TRUE( s.paused ) ) )
    {
        if ( isdefined( s ) && isdefined( s.frz_blocked ) ) s.frz_blocked++;
        return 0;
    }
    if ( !isdefined( attacker ) || isplayer( attacker ) || IS_TRUE( attacker.tod_is_partner ) ) return 0;
    // Different enemy attacks share a bounded integrity hit, so late-round
    // melee cannot delete a companion in one frame. No friendly-fire damage.
    if ( damage <= 0 ) return 0;
    if ( damage > 180 ) damage = 180;
    // DAMAGE: one line per 2 s while it is being hit - who hurts it and how fast.
    if ( isdefined( s ) && isdefined( s.dmg_taken ) )
    {
        s.dmg_taken += damage; s.dmg_hits++;
        if ( isdefined( attacker.archetype ) ) s.dmg_from = attacker.archetype;
        if ( GetTime() >= s.next_dmg_log )
        {
            s.next_dmg_log = GetTime() + 2000;
            log( "DAMAGE type=" + s.chosen + " taken=" + s.dmg_taken + " hits=" + s.dmg_hits + " hp=" + ( self.health - damage ) + " last_from=" + s.dmg_from + " mod=" + mod );
            s.dmg_taken = 0; s.dmg_hits = 0;
        }
    }
    return damage;
}

function kill_credit( attacker )
{
    if ( !isdefined( attacker ) || !IS_TRUE( attacker.tod_is_partner ) ) return;
    raps_fling( attacker.tod_partner_state, self );   // THE BOWLING BALL: a zombie the R.A.P.S. rolled into and killed is thrown
    p = attacker.tod_partner_owner;
    if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) ) return;
    attacker.tod_partner_state.kills++;
    // Elites have their own reward paths; the standard zombie event pays once.
    if ( IS_TRUE( self.is_boss ) || IS_TRUE( self.acc_is_boss ) || IS_TRUE( self.acc_is_mini_boss ) ) return;
    s = attacker.tod_partner_state;
    bonus = 0;
    r = tod_shop::item_rarity( p, s.chosen, TOD_ITEM_SALVAGE );
    if ( r >= 0 ) bonus = tod_shop::item_value( TOD_ITEM_SALVAGE, r );
    kill_pts = 50 + bonus;
    // THE HAVENS (docs/202): an owner standing inside a safe-zone field is paid a quarter
    if ( isdefined( level.tod_haven_kill_pay_fn ) ) kill_pts = [[ level.tod_haven_kill_pay_fn ]]( p, kill_pts );
    p zm_score::add_to_player_score( kill_pts );
    tod_luck::on_zombie_kill( p, false );
    lucky = tod_shop::item_mult( p, s.chosen, TOD_ITEM_LUCKY );
    if ( lucky > 1 && isdefined( level.tod_luck_per_kill ) ) tod_luck::add( p, level.tod_luck_per_kill * ( lucky - 1 ) );
    // Stock death_points exits for a non-player attacker before its drop roll.
    // Restore exactly that eligibility/roll without replaying player rewards.
    if ( zm_spawner::zombie_can_drop_powerups( self ) )
        level thread zm_spawner::zombie_delay_powerup_drop( self.origin );
}

// Called only by the map's stock closest-player seam after its POI guard. self = the asking zombie: stock
// get_closest_valid_player runs level.closest_player_override on it (zm_tod2_cybercity::tod_closest_player).
// ELITES HUNT PLAYERS ONLY (LT-fix 2026-10-05; the user's 17:33 run). The Mangler and the Doppelghast choose their
// prey in script (hunt_target -> valid_target: players only), but stock's find-flesh service asks THIS seam every
// behaviour tick, and a companion within 230 u won it: favoriteenemy flipped companion -> player -> companion
// (160 [TOD_MANGLER] RETARGET lines, only while the R.A.P.S. was out). The Mangler now keeps its own pick in
// tod_hunt_player (_tod_mangler, 2026-10-05); the Doppelghast still reads favoriteenemy in its hunt and its swing
// (attacks: is_player_valid refuses a companion, so it never swung), and the stock behaviour tree reads it for every
// elite. An elite (is_boss or tod_boss_kind) keeps the nearest player here; ordinary zombies still divert to a
// companion. AGGRO_SKIP once per elite.
function closest_target( origin, players )
{
    nearest = ArrayGetClosest( origin, players );
    if ( !isdefined( nearest ) ) return undefined;
    elite = ( isdefined( self ) && !isplayer( self ) && ( IS_TRUE( self.is_boss ) || isdefined( self.tod_boss_kind ) ) );
    dist = DistanceSquared( origin, nearest.origin );
    foreach ( s in level.tod_partner_records )
    {
        if ( !isdefined( s.owner ) || !isalive( s.owner ) || !isdefined( s.actor ) || !isalive( s.actor ) ) continue;
        if ( IS_TRUE( s.paused ) ) continue;
        d = DistanceSquared( origin, s.actor.origin );
        // Only nearby zombies divert; an ally never drags the whole tower away.
        if ( d < 230 * 230 && d < dist && abs( origin[ 2 ] - s.actor.origin[ 2 ] ) < 80 )
        {
            if ( elite )
            {
                if ( !IS_TRUE( self.tod_ptn_aggro_logged ) )
                {
                    self.tod_ptn_aggro_logged = true;
                    kind = "boss";
                    if ( isdefined( self.tod_boss_kind ) ) kind = self.tod_boss_kind;
                    log( "AGGRO_SKIP elite=" + self GetEntityNumber() + " kind=" + kind + " companion=" + s.actor GetEntityNumber() + " type=" + s.chosen
                       + " companion_dist=" + int( Distance( origin, s.actor.origin ) ) + " player_dist=" + int( Distance( origin, nearest.origin ) ) + " (keeps the player)" );
                }
                continue;
            }
            dist = d; nearest = s.actor;
        }
    }
    return nearest;
}

// ARC CHAIN: after a hit, jump to up to N more zombies near `origin` for a
// fraction of the damage, each with its own tracer. `skip_r` skips zombies the
// R.A.P.S. blast already hit; `skip` skips the shot's own target. Returns arcs.
function arc_chain( s, origin, skip_r, skip )
{
    r = tod_shop::item_rarity( s.owner, s.chosen, TOD_ITEM_ARC );
    if ( r < 0 ) return 0;
    count = tod_shop::item_value( TOD_ITEM_ARC, r );
    frac = tod_shop::arc_frac( r );
    reach = TOD_PTN_ARC_R + skip_r;
    arcs = 0;
    foreach ( z in GetAITeamArray( "axis" ) )
    {
        if ( arcs >= count ) break;
        if ( !isdefined( z ) || !isalive( z ) || IS_TRUE( z.tod_is_partner ) || IS_TRUE( z.tod_dropping ) ) continue;
        if ( isdefined( z.tod_necro_binder ) ) continue;   // a Necromancer is binding it: leave it to the Necromancer
        if ( isdefined( skip ) && z == skip ) continue;
        d2 = DistanceSquared( z.origin, origin );
        if ( d2 > reach * reach || ( skip_r > 0 && d2 <= skip_r * skip_r ) ) continue;
        deal_damage( s, z, frac );
        tracer( origin + ( 0, 0, 44 ), z.origin + ( 0, 0, 44 ), s );
        arcs++;
    }
    return arcs;
}

// NANO REPAIR: heals a share of max health per second, carried in fractions.
function nano_tick( s, a )
{
    r = tod_shop::item_rarity( s.owner, s.chosen, TOD_ITEM_NANO );
    if ( r < 0 || a.health >= a.maxhealth ) { s.nano_acc = 0; return; }
    s.nano_acc += a.maxhealth * tod_shop::item_value( TOD_ITEM_NANO, r ) * 0.1;   // the manager ticks at 10 Hz
    heal = int( s.nano_acc );
    if ( heal < 1 ) return;
    s.nano_acc -= heal;
    a.health = a.health + heal;
    if ( a.health > a.maxhealth ) a.health = a.maxhealth;
}

// The three loadout chips beside the companion health bar (TodSpinReel.lua).
function push_items( p )
{
    if ( !isdefined( p ) || !isplayer( p ) || !isdefined( p.tod_ptn ) ) return;
    // Every equip, swap, dismiss, socket and spawn comes through here: the companion row's
    // state goes out again on the next manager tick, so it can never show a stale partner.
    p.tod_ptn.ui_sig = undefined;
    comp = p.tod_ptn.chosen;
    if ( comp < 0 ) { p LuiNotifyEvent( &"tod_ptn_items", 4, 0, 0, 0, 0 ); return; }
    slots = tod_shop::items_of( p, comp );
    p LuiNotifyEvent( &"tod_ptn_items", 4, slots[ 0 ], slots[ 1 ], slots[ 2 ], comp + 1 );
}

function push_items_later()   // self = player; the HUD must exist first
{
    self endon( "disconnect" );
    wait 1;
    push_items( self );
}

// THE PAUSE MENU'S AI COMPANION ROW (user 2026-09-29: "there is an upgrade in the pause menu.
// That shows AI companion. I don't think it's wired up yet, to the actual companion that the
// player has. So we need to wire it all up"). One int event whenever what the row would say
// changes: the companion held, its state, its health in 5 % steps or the whole seconds until
// it is rebuilt, and which companions are owned (the dealer's gift, docs/209). The manager calls this every tick; the
// signature keeps it to a handful of events a minute (one a second while rebuilding), and
// push_items clears the signature so an equip, swap, dismiss or socket re-sends at once.
// The items themselves ride tod_ptn_items. The row is a snapshot when the menu opens.
function push_state( s )
{
    p = s.owner;
    if ( !isdefined( p ) || !isplayer( p ) ) return;
    comp = s.chosen; state = TOD_PTN_UI_NONE; value = 0;
    bits = array( 1, 2, 4, 8 ); built = 0;
    for ( i = 0; i < 4; i++ ) if ( IS_TRUE( s.built[ i ] ) ) built += bits[ i ];
    if ( comp >= 0 )
    {
        now = GetTime();
        if ( now < s.ready[ comp ] )
        {
            state = TOD_PTN_UI_REBUILD;
            value = int( ( s.ready[ comp ] - now + 999 ) / 1000 );   // whole seconds, rounded up
        }
        else if ( isdefined( s.actor ) && isalive( s.actor ) )
        {
            state = TOD_PTN_UI_ACTIVE;
            top = max_hp( s, comp ); value = 100;
            if ( top > 0 ) value = int( ( s.hp[ comp ] * 100 + top - 1 ) / top );   // percent, rounded up
            value = int( ( value + 4 ) / 5 ) * 5;   // 5 % steps; a living companion never reads 0
            if ( value > 100 ) value = 100;
            if ( value < 5 ) value = 5;
        }
        else state = TOD_PTN_UI_DEPLOYING;
    }
    sig = ( comp + 1 ) + "/" + state + "/" + value + "/" + built;
    if ( isdefined( s.ui_sig ) && s.ui_sig == sig ) return;
    s.ui_sig = sig;
    p LuiNotifyEvent( &"tod_ptn_state", 4, comp + 1, state, value, built );
    // Log the transitions, not every health step or rebuild second.
    moment = ( comp + 1 ) + "/" + state + "/" + built;
    if ( !isdefined( s.ui_log ) || s.ui_log != moment )
    {
        s.ui_log = moment;
        log( "UI_STATE owner=" + p GetEntityNumber() + " type=" + comp + " state=" + state + " value=" + value + " built=" + built );
    }
}

// _tod_shop calls this after a spin (level.tod_partner_items_changed): re-scale
// the live companion's health to the new PLATING, flash it, refresh the chips.
function items_changed( p, comp, installed )
{
    if ( !isdefined( p ) || !isdefined( p.tod_ptn ) ) return;
    s = p.tod_ptn;
    if ( s.chosen == comp && isdefined( s.actor ) && isalive( s.actor ) )
    {
        a = s.actor;
        old = a.maxhealth; now = max_hp( s, comp );
        if ( old > 0 && now != old )
        {
            a.maxhealth = now;
            a.health = int( a.health * now / old );
            if ( a.health > now ) a.health = now;
            if ( a.health < 1 ) a.health = 1;
        }
        if ( IS_TRUE( installed ) )
        {
            org = a.origin + ( 0, 0, 40 );
            if ( isdefined( s.visual ) ) org = s.visual.origin + ( 0, 0, 20 );
            level thread fx_burst( TOD_PTN_BLAST_FX, org, 0.6 );
        }
        s.hp[ comp ] = a.health;
    }
    // QUICK REBOOT socketed while the companion is rebuilding: the running timer
    // shrinks too (the time already served counts), not only the next one.
    now = GetTime();
    if ( now < s.ready[ comp ] )
    {
        want = rebuild_ms( s, comp );
        if ( want < s.ready_len[ comp ] )
        {
            served = s.ready_len[ comp ] - ( s.ready[ comp ] - now );
            left = want - served;
            if ( left < 0 ) left = 0;
            s.ready[ comp ] = now + left;
            s.ready_len[ comp ] = want;
            log( "REBOOT_SHORTENED owner=" + p GetEntityNumber() + " type=" + comp + " left_ms=" + left + " len_ms=" + want );
        }
    }
    push_items( p );
    log( "ITEMS owner=" + p GetEntityNumber() + " type=" + comp + " installed=" + IS_TRUE( installed )
       + " hp_x=" + tod_shop::item_mult( p, comp, TOD_ITEM_PLATING ) + " rate_x=" + tod_shop::item_mult( p, comp, TOD_ITEM_OVERCLOCK )
       + " dmg_x=" + tod_shop::item_mult( p, comp, TOD_ITEM_HOLLOW ) + " range_x=" + tod_shop::item_mult( p, comp, TOD_ITEM_SIGHT )
       + " nano=" + tod_shop::item_rarity( p, comp, TOD_ITEM_NANO ) + " arc=" + tod_shop::item_rarity( p, comp, TOD_ITEM_ARC )
       + " salvage=" + tod_shop::item_rarity( p, comp, TOD_ITEM_SALVAGE ) + " reboot=" + tod_shop::item_rarity( p, comp, TOD_ITEM_REBOOT )
       + " lucky=" + tod_shop::item_rarity( p, comp, TOD_ITEM_LUCKY ) );
}


function log( message )
{
    // Bring-up evidence also runs in the user's normal (tod_dev=false) match.
    // Restore the standard dev-only gate after the first native acceptance;
    // no gameplay/dev cheats or extra user-facing debug toggle are enabled.
    line = "[TOD_PARTNER] ms=" + GetTime() + " " + message;
    /# PrintLn( line ); #/
}
