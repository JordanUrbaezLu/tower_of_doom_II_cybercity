// Crown-room native art/state test. Upgrade inventory and prices are separate design.
#using scripts\shared\clientfield_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\system_shared;
#using scripts\shared\laststand_shared;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_luck;          // get / spend / add: the spin spends the bar, a scrap refunds it
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;      // menu_freeze + pause_invuln_held_elsewhere (the card panel's own lanes)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;  // play_sound_at_origin (the proven 3D lane)
#using scripts\zm\zm_tod2_cybercity\_tod_shop_vo;       // GENERATED: the length of every dealer line (tools/black_market_vo/pick.py)
#using scripts\zm\zm_tod2_cybercity\_tod_upgrade_ui;    // team_toast: THE TOAST (imports only shared: no cycle)
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#namespace tod_shop;
// ONE SHOP IN THE CROWN (user 2026-09-25: "the crown has two item shops inside
// of it. It should only have one"). The generator emits the hall's shop as
// index 0 and the balcony's display hut as index 1; the ACTIVE shop cycles over
// the first TOD_SHOP_CYCLE anchors only, so the hall's is always the live one
// and the balcony's stays the dark, silent display by construction.
#define TOD_SHOP_CYCLE 1
#define TOD_SHOP_LOG 1 // Bring-up records in a normal user match; zero after acceptance.
#precache( "model", "tod_shop_off" );
#precache( "model", "tod_shop_solid" );
#precache( "model", "tod_shop_vendor" );
#precache( "model", "tod_shop_steady" );
#precache( "model", "tod_shop_letter_t" );
#precache( "model", "tod_shop_letter_e" );
#precache( "model", "tod_shop_letter_c" );   // BLACK MARKET sign: C / E / T blink (2026-09-29; was H)
#precache( "model", "tod_shop_mask" );
#precache( "model", "tod_shop_core_left" );
#precache( "model", "tod_shop_core_counter" );
#precache( "model", "tod_shop_core_right" );
#precache( "model", "tod_shop_scan_0" );
#precache( "model", "tod_shop_scan_1" );
#precache( "model", "tod_shop_scan_2" );
#precache( "model", "tod_shop_scan_3" );
#precache( "model", "tod_shop_valve" );
#precache( "model", "tod_shop_needle" );
#precache( "model", "tag_origin" );
#precache( "fx", "electric/fx_elec_spark_loop_sm" );
#precache( "fx", "dlc1/castle/fx_elec_teleport_flash_lg" );   // TOD_SPIN_BLAST_FX (was a stub until 2026-10-04, see below)
// THE BLACK MARKET SPIN's HUD channel (TodSpinReel.lua). A LuiNotifyEvent name
// must be a precached eventstring or the event silently never fires.
#precache( "eventstring", "tod_spin_open" );
#precache( "eventstring", "tod_spin_step" );
#precache( "eventstring", "tod_spin_land" );
#precache( "eventstring", "tod_spin_slots" );
#precache( "eventstring", "tod_spin_end" );

// =============================================================================
// THE BLACK MARKET SPIN (docs/188, user 2026-09-28): the ACTIVE shop sells a
// spin for a companion item. Hold USE, pay, your LUCK BAR is spent into the
// odds, a reel of item tiles spins to an item + rarity, and it sockets into the
// held companion's three item slots (no duplicates; a lower-rarity copy is
// upgraded in place; three full slots = choose one or SCRAP it back to luck).
// While the spin runs the player is frozen, UNTARGETABLE and cannot be hurt.
// ITEMS + RARITY + ODDS are LOCKSTEP with TodSpinReel.lua; the rarity ladder
// and odds are docs/187's (the card session's constants, confirmed equal).
// =============================================================================
#define TOD_SPIN_COST          2500   // LOCKSTEP with the literal in the hint below
#define TOD_SPIN_STEPS         30     // reel steps to the prize; the prize is tile TOD_SPIN_STEPS
#define TOD_SPIN_STEP_MIN_MS   50     // the fastest step (one server frame per tile)
#define TOD_SPIN_STEP_MAX_MS   700    // the last step, on a cubic slow-down
#define TOD_SPIN_LEG_HITCH_MS  850    // the reel all but stops on the tile before a LEGENDARY
// THE NEAR MISS (docs/201 section 3, user 2026-10-02: "the concept of near miss and almost hit that sports companies
// and gambling companies use"). It replaces the silent 45 % tease (a better tile next to the needle that nothing
// pointed at). The prize is rolled FIRST, at the odds the screen shows; a near miss only decides what is drawn around
// it (near_plan), so it never changes what the player gets - tools/partner_shop/test_spin.js proves it. Two kinds,
// on about 30 % of non-Legendary spins (the rate that kept players going longest, Kassinove & Schare 2001):
//   STOPPED SHORT - the reel runs past the prize until the needle sits on the seam with the NEXT tile, a better one
//                   (one rarity up, or a LEGENDARY), hangs there, and falls back onto the prize;
//   SLIPPED PAST  - the reel creeps across a LEGENDARY with the jackpot's heartbeat, never locking on it (no stop
//                   clunk, no flare: a prize is never shown and taken back), and creeps off onto the real prize.
// The teased tile is always an item this companion would really gain (roll_item), never one that could not have come.
// Side effect, wanted: the heartbeat stops being a certain Legendary, so a real one finally has suspense.
#define TOD_SPIN_NEAR_SHORT_PCT  22    // STOPPED SHORT, of the non-Legendary spins
#define TOD_SPIN_NEAR_PAST_PCT   8     // SLIPPED PAST, of the non-Legendary spins (always a LEGENDARY tile)
#define TOD_SPIN_NEAR_LEG_PCT    50    // a STOPPED SHORT tile is a LEGENDARY this often, else one rarity up (an EPIC prize: always LEGENDARY)
#define TOD_SPIN_NEAR_HANG_MS    400   // the needle on the seam                 - LOCKSTEP TodSpinReel.lua P3.NEAR_HANG_MS
#define TOD_SPIN_PAST_HOLD_MS    850   // the reel creeping across the jackpot   - LOCKSTEP P3.PAST_HOLD_MS
#define TOD_SPIN_SETTLE_MS       150   // the settle back onto the prize         - LOCKSTEP P3.SETTLE_MS
#define TOD_SPIN_NEAR_SND_AT     0.3   // the "so close" lands this long after the stop
#define TOD_SPIN_VO_NEAR_AT      0.7   // ... and the dealer's word after it (it takes the landing line's place)
#define TOD_SPIN_VO_NEAR_PCT     70
#define TOD_SPIN_VO_HOT_PCT      70    // THE HOT STREAK (docs/201 section 5): a player HEATING UP or ON FIRE hears him notice it at the pour
#define TOD_SPIN_STREAK_FB_SECS  1.3   // the streak's sound waits for the landing sting and the dealer's word
#define TOD_SPIN_CHOICE_SECS   15     // full slots: time to choose; timeout = SCRAP (never loses a held item)
#define TOD_SPIN_HOLD_SECS     0.5    // hold JUMP/USE to confirm (the card panel's lock)
#define TOD_SPIN_READ_SECS     1.4    // the prize + slots stay up this long after the socket
#define TOD_SPIN_TRIG_OUT      96     // the use trigger stands this far in front of the counter (front = local -Y)
#define TOD_SPIN_TRIG_R        64
#define TOD_SPIN_ITEMS         9      // PLATING OVERCLOCK HOLLOW-POINT LONG-SIGHT NANO-REPAIR ARC-CHAIN SALVAGE QUICK-REBOOT LUCKY-CHARM
#define TOD_SPIN_GUAR_LEG_PCT  25     // a full bar forces EPIC+; this share of the forced ones is LEGENDARY (docs/187 GUAR_LEG_SHARE)
#define TOD_SPIN_EXIT_GRACE    1.5    // s unhurtable after the panel closes (targetable again): no hit the instant control returns
#define TOD_SPIN_CHOICE_GRACE  0.6    // s at the start of a slot choice in which no confirm counts (a mashed button never replaces an item)
#define TOD_SPIN_TICK_MIN_MS   100    // the reel ticks at most every 100 ms (a tick per 50 ms frame was a buzz)
#define TOD_SPIN_LUCK_SND_AT   0.15   // the luck pour's sound starts just after the slam (docs/194 M3)
#define TOD_SPIN_SOCKET_SND_AT 0.3    // the socket click lands WITH the flying icon (TodSpinReel P3.FLY_MS 320)
#define TOD_SPIN_VO_BUY_PCT    70     // the dealer speaks on most spins, never on every one (docs/194 V lines)
#define TOD_SPIN_VO_COMMON_PCT 50     // a COMMON gets his "meh" half the time; EPIC / LEGENDARY always; RARE at TOD_SPIN_VO_RARE_PCT
#define TOD_SPIN_VO_CLOSE_PCT  35
#define TOD_SPIN_VO_AT         0.15   // a landing line follows the stop clunk at once (user 2026-09-30: "a little bit slow to react"; was 0.5)
#define TOD_SPIN_VO_LEG_AT     0.5    // ... the JACKPOT rides the jackpot sting's hit (was 1.1)
// THE DEALER'S VOICE (2026-09-30; ElevenLabs v4 through tools/black_market_vo, lines in its lines.json).
// Every line goes through vo_say(): ONE lane per player, and a line asked for while another is
// still speaking is DROPPED, never queued (he never talks over himself; a dropped line is logged
// VO_DROP). Lengths come from the GENERATED _tod_shop_vo.gsc. The idle mutters go to every
// player in earshot on their own lanes, and are held while anyone is spinning.
#define TOD_SPIN_VO_GAP_MS       150  // ms of silence kept between two lines on one lane
#define TOD_SPIN_VO_APPROACH_R   200  // u from the counter: the greeting, once per visit (was 260; the voice now fades by 480)
#define TOD_SPIN_VO_APPROACH_CD  75   // s per player between greetings
#define TOD_SPIN_VO_APPROACH_PCT 80
#define TOD_SPIN_VO_LUCK_PCT     60   // the pour's line: a FULL bar or one under half
#define TOD_SPIN_VO_RARE_PCT     30   // RARE: the sting speaks; he only sometimes adds to it
#define TOD_SPIN_VO_AFTER_PCT    60   // socket / upgrade / scrap
#define TOD_SPIN_VO_AFTER_AT     0.1  // ... this long after their own sound (was 0.5)
#define TOD_SPIN_VO_FULL_AT      1.0  // the "choose what dies" line, once the landing line has had its say (was 2.6)
#define TOD_SPIN_VO_IDLE_MIN     30   // s between idle mutters at the counter
#define TOD_SPIN_VO_IDLE_MAX     60
#define TOD_SPIN_VO_IDLE_R       480  // u: a mutter needs a player this close (= the 3D rows' DistMaxDry; was 900)
#define TOD_SPIN_VO_REGULAR_AT   4    // a player's Nth spin and after: half the greetings are the regular's
#define TOD_SPIN_VO_CLASS_PCT    60   // THE CLASSES (user 2026-10-01): a player with a class hears the dealer's line FOR that class this often (vo_cls), the generic one otherwise
// THE MOUTH (user 2026-09-30: "These lines should only be heard by the player. And it should come in the 3D
// world from the black market"): every line is played ON a script_origin at the dealer's mask, TO one player
// (PlaySoundToPlayer: stock _empgrenade / zm_cwpap lane), on 3D rows in tod_shop.csv - private and placed.
#define TOD_SPIN_VO_MOUTH_OFS    ( 0, 12, 70 )   // local to the shop: the mask behind the counter (counter face = local -Y)
#define TOD_SPIN_POUR_SECS     0.95   // the panel slams in (0.35) and the luck pours into the machine (0.6) before the reel moves - LOCKSTEP TodSpinReel.lua P3.POUR_MS
#define TOD_SPIN_SPARK_FX      "electric/fx_elec_spark_loop_sm"
// THE BLAST (a LEGENDARY at the counter, THE LAST ROLL's curse) was electric/fx_elec_burst_lg_z270_os until
// 2026-10-04: a gfx_debug_missing_fx STUB in the mod tools (memory stock-fx-can-be-a-stub) - it zoned, linked and
// drew nothing. Der Eisendrache's teleport flash is the teleporter's own bright discharge (real, zoned).
#define TOD_SPIN_BLAST_FX      "dlc1/castle/fx_elec_teleport_flash_lg"
// THE DEALER'S HOUSE (docs/207): THE LAST ROLL's rigged result. A tile that is not on the wheel: CURSED
// (TOD_SPIN_CURSED_TILE, item 15 to the reel's packing - LOCKSTEP TodSpinReel.lua CURSED.tile) landed with
// its own code (TOD_SPIN_CODE_CURSED - LOCKSTEP CURSED.code). house_roll runs the reel on every player's
// screen with one seed; it never pays, never scraps, never touches a slot. The hang before the fall is on a
// LEGENDARY LUCKY CHARM (TOD_SPIN_CURSED_TEASE: item 9, rarity 3) - the jackpot's own heartbeat, then the curse.
#define TOD_SPIN_CURSED_TILE   60
#define TOD_SPIN_CODE_CURSED   9
#define TOD_SPIN_CURSED_TEASE  39
// THE DEALER'S GIFT (docs/209, user 2026-10-04: "This concept of finding your parts etc is a bit much to get into the
// black market situation. I think he should gift you a random AI companion on first use that doesnt use up your luck.
// Then you can continue to upgrade ... make it easy for the player experience"). A player with NO companion who holds
// USE at the lit counter is GIVEN one: the same machine slams in, its reel runs the four companions and lands on his,
// the LUCK box stays exactly where his bar is (shown, never spent), no points, no streak, no spin count. The reel's
// tiles are gift tiles (TOD_GIFT_TILE_BASE + companion + 1 = 45..48: never an item tile, item * 4 + rarity <= 39, never
// CURSED 60) landed with TOD_SPIN_CODE_GIFT; the slot row comes up EMPTY in TOD_GIFT_SLOTS_MODE ("SPIN TO FILL").
// LOCKSTEP all three with TodSpinReel.lua P3.GIFT. From his next visit the counter sells spins for its items.
#define TOD_GIFT_TILE_BASE     44
#define TOD_SPIN_CODE_GIFT     8
#define TOD_GIFT_SLOTS_MODE    4
#define TOD_GIFT_POOL_MODE     5      // while the gift reel runs: the slot row shows the four companions it chooses from
#define TOD_GIFT_COMPANIONS    4      // LOCKSTEP _tod_partners define() count
#define TOD_GIFT_STEP_MAX_MS   450    // the gift's last tile (a spin crawls to 700): ~4.6 s over the same 30 tiles
#define TOD_GIFT_OPEN_SECS     0.5    // the slam and a beat to read THE DEALER'S GIFT (no luck pour: nothing is paid)
#define TOD_GIFT_READ_SECS     3.2    // the companion, its line and its three empty slots stay up this long
#define TOD_GIFT_VO_LAND_AT    0.35   // his word after the stop
#define TOD_GIFT_VO_LAND_WAIT  4.0    // s it waits for his reel line to finish (the landing line is never dropped by it). 2.5 -> 4.0
                                      // (LT-rest 2026-10-05): the 17:33 run pressed USE 0.85 s into the 9.234 s walk-up offer and the
                                      // landing line was dropped 634 ms short; 4.0 outlasts either offer line pressed at its first word
                                      // (the reel lands 5.05 s after the press, + LAND_AT 0.35; offer_2 + the lane gap ends 9.38 s in)
#define TOD_GIFT_VO_OFFER_CD   20     // s between two gift offers to one player at the counter
#define TOD_GIFT_NUDGE_SECS    8      // the one-time notice waits this long after the counter first lights
REGISTER_SYSTEM( "tod_shop", &__init__, undefined )
function __init__()
{
    // low four bits = component, high bit = existing dev/bring-up diagnostics.
    clientfield::register( "scriptmover", "todShopPart", VERSION_SHIP, 5, "int" );
}
function init()
{
    level endon( "end_game" );
    if ( isdefined( level.tod_shops ) ) return;
    level.tod_shops = []; level.tod_shop_active = -1; level.tod_shop_busy = false;
    orgs = tod_crown_data::shop_orgs(); yaws = tod_crown_data::shop_yaws();
    for ( i = 0; i < orgs.size; i++ )
    {
        shop = SpawnStruct(); shop.id = i; shop.origin = orgs[ i ]; shop.yaw = yaws[ i ]; shop.parts = [];
        shop.body = Spawn( "script_model", shop.origin );
        if ( !isdefined( shop.body ) ) { log( "INIT_FAIL slot=" + i + " reason=body_spawn" ); continue; }
        shop.body SetModel( "tod_shop_off" ); shop.body.angles = ( 0, shop.yaw, 0 );
        shop.body.targetname = "tod_item_shop"; shop.body NotSolid();
        level.tod_shops[ i ] = shop;
        log( "PLACED id=" + i + " origin=" + shop.origin + " yaw=" + shop.yaw + " powered=0" );
    }
    level thread end_cleanup();
    spin_init();
    log( "INIT rev=3 count=" + level.tod_shops.size + " cycle=round loop_ms=6000 sign=BLACK_MARKET letters=CET shared_faults=6 mask=independent_breath spark_events=10 spark_clusters=3 valve_travel=100" );
    old_round = -1; was_power = false;
    while ( true )
    {
        // THE DEALER'S HOUSE (docs/207): while the parlour's counter is his, the cycler sleeps
        if ( IS_TRUE( level.tod_shop_hold ) ) { wait 0.25; continue; }
        powered = level flag::exists( "power_on" ) && level flag::get( "power_on" );
        // DEV: the crown shop is live from the first frame (user 2026-09-28: "We
        // can make the crown item shop active in dev mode"), not after the power.
        if ( IS_TRUE( level.tod_dev ) ) powered = true;
        if ( !powered && was_power ) activate( -1, "power_off" );
        if ( powered && isdefined( level.round_number ) && level.round_number >= 1 )
        {
            if ( !was_power || level.tod_shop_active < 0 || level.round_number != old_round )
            {
                next = ( level.tod_shop_active + 1 ) % TOD_SHOP_CYCLE;
                activate( next, "round_" + level.round_number );
                old_round = level.round_number;
            }
        }
        was_power = powered;
        wait 0.25;
    }
}
// Public single-owner transition, also usable when the future shop purchase rules exist.
function activate( index, reason )
{
    if ( IS_TRUE( level.tod_shop_busy ) ) { log( "DENIED reason=transition_busy requested=" + index ); return false; }
    if ( index < -1 || index >= level.tod_shops.size || ( index >= 0 && !isdefined( level.tod_shops[ index ] ) ) )
    { log( "DENIED reason=invalid_shop requested=" + index ); return false; }
    if ( index == level.tod_shop_active ) return true;
    level.tod_shop_busy = true;
    previous = level.tod_shop_active; level.tod_shop_active = -1;
    // Turn off every old callback before replacing models. Two snapshots deliver zero.
    foreach ( s in level.tod_shops )
    {
        if ( !isdefined( s ) ) continue;
        foreach ( p in s.parts ) if ( isdefined( p ) ) { p clientfield::set( "todShopPart", 0 ); p notify( "shop_stop" ); }
    }
    wait 0.1;
    foreach ( s in level.tod_shops )
    {
        if ( !isdefined( s ) ) continue;
        foreach ( p in s.parts ) if ( isdefined( p ) ) p Delete();
        s.parts = [];
        if ( isdefined( s.body ) ) s.body SetModel( "tod_shop_off" );
    }
    if ( index < 0 ) { level.tod_shop_busy = false; spin_trigger_place( -1 ); log( "OFF previous=" + previous + " reason=" + reason ); return true; }
    s = level.tod_shops[ index ];
    if ( !isdefined( s.body ) ) { level.tod_shop_busy = false; log( "ACTIVATE_FAIL id=" + index + " reason=body_missing" ); return false; }
    names = array( "steady", "letter_t", "letter_e", "letter_c", "mask", "core_left", "core_counter", "core_right", "scan_0", "scan_1", "scan_2", "scan_3", "vendor", "valve", "needle" );
    failed = false;
    for ( j = 0; j < names.size; j++ )
    {
        offset = ( 0, 0, 0 );
        if ( names[ j ] == "valve" ) offset = ( 90, -32, 47 );
        if ( names[ j ] == "needle" ) offset = ( 73, -36.55, 74 );
        p = Spawn( "script_model", local_to_world( s.origin, s.yaw, offset ) );
        if ( !isdefined( p ) ) { failed = true; log( "PART_FAIL id=" + index + " part=" + names[ j ] ); break; }
        p SetModel( "tod_shop_" + names[ j ] ); p.angles = ( 0, s.yaw, 0 ); p NotSolid(); p Hide();
        p.tod_shop_kind = j + 1; p.tod_shop_yaw = s.yaw; s.parts[ s.parts.size ] = p;
    }
    if ( failed )
    {
        foreach ( p in s.parts ) if ( isdefined( p ) ) p Delete();
        s.parts = []; level.tod_shop_busy = false; return false;
    }
    wait 0.1; // model DObjs must exist before clients bind shaders/FX tags.
    s.body SetModel( "tod_shop_solid" );
    foreach ( p in s.parts )
    {
        p Show();
        if ( p.tod_shop_kind <= 12 )
        {
            value = p.tod_shop_kind;
            if ( IS_TRUE( level.tod_dev ) || TOD_SHOP_LOG ) value += 16;
            p clientfield::set( "todShopPart", value );
        }
        if ( p.tod_shop_kind >= 14 ) p thread pressure_motion();
    }
    level.tod_shop_active = index; level.tod_shop_busy = false;
    spin_trigger_place( index );
    log( "ACTIVE id=" + index + " previous=" + previous + " reason=" + reason + " parts=" + s.parts.size + " marker=wunderfizz sounds=3" );
    return true;
}
function local_to_world( origin, yaw, p )
{
    return origin + ( p[ 0 ] * Cos( yaw ) - p[ 1 ] * Sin( yaw ), p[ 0 ] * Sin( yaw ) + p[ 1 ] * Cos( yaw ), p[ 2 ] );
}
function pressure_motion()
{
    self endon( "death" ); self endon( "shop_stop" ); level endon( "end_game" );
    while ( true )
    {
        phase = ( GetTime() % 3000 ) * 360.0 / 3000;
        angle = pressure_angle( self.tod_shop_kind, phase );
        self RotateTo( ( angle, self.tod_shop_yaw, 0 ), 0.1 );
        wait 0.1;
    }
}
function pressure_angle( kind, phase )
{
    if ( kind == 15 ) return 24 * Sin( phase ) + 3.5 * Sin( phase * 10 );
    return 50 * ( 1 - Cos( phase ) );
}
function end_cleanup()
{
    level waittill( "end_game" );
    foreach ( s in level.tod_shops )
    {
        if ( !isdefined( s ) ) continue;
        foreach ( p in s.parts ) if ( isdefined( p ) ) { p clientfield::set( "todShopPart", 0 ); p notify( "shop_stop" ); }
    }
    wait 0.1;
    foreach ( s in level.tod_shops )
    {
        if ( !isdefined( s ) ) continue;
        foreach ( p in s.parts ) if ( isdefined( p ) ) p Delete();
        s.parts = []; if ( isdefined( s.body ) ) s.body SetModel( "tod_shop_off" );
    }
    level.tod_shop_active = -1; spin_trigger_place( -1 ); log( "CLEANUP end_game powered=0" );
}
function log( msg )
{
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) && !TOD_SHOP_LOG ) return;
    line = "[TOD_SHOP] ms=" + GetTime() + " " + msg;
    /#
    PrintLn( line );
    #/
}

// =============================================================================
// THE BLACK MARKET SPIN (docs/188). Everything below is the spin; everything
// above is the shop's art/state test, which it only reads (the active index and
// its origin/yaw).
// =============================================================================

// TWO TRIGGERS AT ONE COUNTER. BO3 has no per-player hint string, so the shop
// shows each player exactly one of two constant prompts through
// SetVisibleToPlayer / SetInvisibleToPlayer (spin_vis_apply_all):
//   BUY  - "BLACK MARKET - Spin for a companion item ... $2500", to a player who
//          holds a companion;
//   NEED - THE DEALER'S GIFT (docs/209): "BLACK MARKET - A free AI companion / No
//          points or luck - on the house" (no lock word, no price: the card's
//          footer reads TO TAKE), to a player who has none yet: holding USE there
//          runs gift(), and he walks away with a companion. (Until 2026-10-04
//          this was a locked card that sent him to a partner bench to build one;
//          the parts and benches are retired.)
// A SPINNING player sees neither: the prompt card must never sit on the reel.
// Both hints are constant (the triggerstring budget); "black market" is a TOD_NOUNS
// entry. Both triggers move with activate() via spin_trigger_place. ONE NAME
// (user 2026-09-29: "The Item Shop / Black Market is confusing. Lets just rename
// it Black Market all together"): the prompt, the neon sign on the model and the
// spin screen all say BLACK MARKET; "item shop" is never shown to a player.
function spin_init()
{
    buy = spin_trigger_make();
    need = spin_trigger_make();
    if ( !isdefined( buy ) || !isdefined( need ) ) { log( "SPIN_INIT_FAIL reason=trigger_spawn" ); return; }
    buy SetHintString( "Hold ^3[{+activate}]^7 ^5BLACK MARKET^7 - Spin for a companion item / Your luck sets the odds ^2[Cost: 2500]" );
    // THE DEALER'S GIFT (docs/209): no price row, no lock word; "free ai companion" makes the card's footer TO TAKE
    need SetHintString( "Hold ^3[{+activate}]^7 ^5BLACK MARKET^7 - A free AI companion / No points or luck - on the house" );
    level.tod_spin_trig = buy;
    level.tod_spin_need = need;
    level.tod_spin_vo_mouth = Spawn( "script_origin", ( 0, 0, -10000 ) );   // the dealer's voice comes from here
    buy thread spin_trigger_loop();
    need thread spin_trigger_loop();
    level thread spin_vis_watch();
    level thread vo_approach_watch();
    level thread vo_idle_watch();
    log( "SPIN_INIT cost=" + TOD_SPIN_COST + " steps=" + TOD_SPIN_STEPS + " items=" + TOD_SPIN_ITEMS + " prompts=buy+gift gift=free_no_luck dev_live=" + IS_TRUE( level.tod_dev ) );
}

function spin_trigger_make()
{
    t = Spawn( "trigger_radius_use", ( 0, 0, -10000 ), 0, TOD_SPIN_TRIG_R, 72 );
    if ( !isdefined( t ) ) return undefined;
    t TriggerIgnoreTeam();
    t SetCursorHint( "HINT_NOICON" );
    t TriggerEnable( false );
    return t;
}

function spin_trigger_place( index )
{
    buy = level.tod_spin_trig; need = level.tod_spin_need;
    if ( !isdefined( buy ) || !isdefined( need ) ) return;
    if ( index < 0 || !isdefined( level.tod_shops[ index ] ) )
    {
        buy TriggerEnable( false ); need TriggerEnable( false );
        buy.tod_shop = undefined; need.tod_shop = undefined;
        if ( isdefined( level.tod_spin_vo_mouth ) ) level.tod_spin_vo_mouth.origin = ( 0, 0, -10000 );
        log( "SPIN_TRIGGER off" );
        return;
    }
    s = level.tod_shops[ index ];
    org = local_to_world( s.origin, s.yaw, ( 0, 0 - TOD_SPIN_TRIG_OUT, 40 ) );
    buy.origin = org; need.origin = org;
    buy.tod_shop = s; need.tod_shop = s;
    if ( isdefined( level.tod_spin_vo_mouth ) ) level.tod_spin_vo_mouth.origin = local_to_world( s.origin, s.yaw, TOD_SPIN_VO_MOUTH_OFS );
    spin_vis_apply_all();          // each player's prompt is right before the first frame it can show
    buy TriggerEnable( true ); need TriggerEnable( true );
    log( "SPIN_TRIGGER on shop=" + index + " org=" + org );
    // THE DEALER'S GIFT (docs/209): the first time a counter lights, tell everyone who has no companion yet
    if ( !IS_TRUE( level.tod_gift_nudge_armed ) ) { level.tod_gift_nudge_armed = true; level thread gift_nudge(); }
}

function spin_trigger_loop()
{
    level endon( "end_game" );
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isdefined( p ) || !isplayer( p ) || IS_TRUE( p.tod_spin_busy ) ) continue;
        if ( !isdefined( self.tod_shop ) ) continue;
        p.tod_spin_busy = true;
        // THE DEALER'S GIFT (docs/209): whichever of the two prompts he used, a player with no companion is GIVEN
        // one and everyone else buys a spin (the prompts follow the same rule, but only every 0.25 s)
        if ( gift_wanted( p ) ) p thread gift( self.tod_shop );
        else p thread spin( self.tod_shop );
    }
}

function spin_vis_watch()
{
    level endon( "end_game" );
    for ( ;; )
    {
        spin_vis_apply_all();
        wait 0.25;
    }
}

// 0 = no prompt (spinning), 1 = the BUY prompt, 2 = the GIFT prompt (no companion
// yet: gift_wanted's rule, docs/209). Cached per player so the triggers are only
// touched when a player's state changes.
function spin_vis_apply_all()
{
    buy = level.tod_spin_trig; need = level.tod_spin_need;
    if ( !isdefined( buy ) || !isdefined( need ) ) return;
    foreach ( p in GetPlayers() )
    {
        if ( !isdefined( p ) || !isplayer( p ) ) continue;
        want = 1;
        if ( IS_TRUE( p.tod_spin_locked ) ) want = 0;
        else if ( !isdefined( p.tod_ptn ) || !isdefined( p.tod_ptn.chosen ) || p.tod_ptn.chosen < 0 ) want = 2;
        if ( isdefined( p.tod_spin_vis ) && p.tod_spin_vis == want ) continue;
        p.tod_spin_vis = want;
        if ( want == 1 ) buy SetVisibleToPlayer( p );
        else buy SetInvisibleToPlayer( p );
        if ( want == 2 ) need SetVisibleToPlayer( p );
        else need SetInvisibleToPlayer( p );
    }
}

// ---------------------------------------------------------------- the items
// Stored per player, per companion (user: "AI Companions can have 3 items
// equipped"): p.tod_spin_items[ companion ] = three packed values, item * 4 +
// rarity (item 1..9, rarity 0 COMMON .. 3 LEGENDARY), 0 = empty.
function items_of( p, comp )
{
    if ( !isdefined( p.tod_spin_items ) ) p.tod_spin_items = [];
    if ( !isdefined( p.tod_spin_items[ comp ] ) ) p.tod_spin_items[ comp ] = array( 0, 0, 0 );
    return p.tod_spin_items[ comp ];
}

function tile_item( v ) { return int( v / 4 ); }
function tile_rar( v ) { return v - int( v / 4 ) * 4; }

// PUBLIC (read by _tod_partners): the rarity this companion holds `item` at, or -1.
function item_rarity( p, comp, item )
{
    if ( !isdefined( p ) || !isdefined( comp ) || comp < 0 ) return -1;
    if ( !isdefined( p.tod_spin_items ) || !isdefined( p.tod_spin_items[ comp ] ) ) return -1;
    foreach ( v in p.tod_spin_items[ comp ] )
        if ( v > 0 && tile_item( v ) == item ) return tile_rar( v );
    return -1;
}

// THE ITEM TABLE (docs/188 section 2; LOCKSTEP with TodSpinReel.lua's effect lines).
function item_value( item, rar )
{
    switch ( item )
    {
        case 1: v = array( 1.25, 1.5, 1.8, 2.2 ); break;            // PLATING: max health x
        case 2: v = array( 1.15, 1.3, 1.5, 1.8 ); break;            // OVERCLOCK: fire rate x
        case 3: v = array( 1.2, 1.4, 1.7, 2.1 ); break;             // HOLLOW POINT: damage x
        case 4: v = array( 1.2, 1.35, 1.55, 1.8 ); break;           // LONG SIGHT: range x
        case 5: v = array( 0.01, 0.02, 0.03, 0.05 ); break;         // NANO REPAIR: max health / s
        case 6: v = array( 1, 1, 2, 3 ); break;                     // ARC CHAIN: extra zombies
        case 7: v = array( 10, 25, 40, 60 ); break;                 // SALVAGE: + points per kill
        case 8: v = array( 34000, 25000, 17000, 10000 ); break;     // QUICK REBOOT: rebuild ms
        case 9: v = array( 1.25, 1.5, 2.0, 2.5 ); break;            // LUCKY CHARM: luck per kill x
        default: return 0;
    }
    if ( rar < 0 ) rar = 0;
    if ( rar > 3 ) rar = 3;
    return v[ rar ];
}

function arc_frac( rar )
{
    v = array( 0.3, 0.5, 0.5, 0.6 );
    if ( rar < 0 ) rar = 0;
    if ( rar > 3 ) rar = 3;
    return v[ rar ];
}

// PUBLIC: a multiplier item's value, 1.0 when the companion does not hold it.
function item_mult( p, comp, item )
{
    r = item_rarity( p, comp, item );
    if ( r < 0 ) return 1.0;
    return item_value( item, r );
}

function item_name( item )
{
    names = array( "", "PLATING", "OVERCLOCK", "HOLLOW POINT", "LONG SIGHT", "NANO REPAIR", "ARC CHAIN", "SALVAGE", "QUICK REBOOT", "LUCKY CHARM" );
    if ( item < 1 || item > TOD_SPIN_ITEMS ) return "?";
    return names[ item ];
}

function rarity_name( rar )
{
    names = array( "COMMON", "RARE", "EPIC", "LEGENDARY" );
    if ( rar < 0 || rar > 3 ) return "?";
    return names[ rar ];
}

// ---------------------------------------------------------------- the roll
// docs/187 odds: a straight line from an empty bar (56/27/13/4) to a full one
// (36/36/20/8). LOCKSTEP with TodSpinReel.lua fillerRarity.
// THE HOT STREAK (docs/201 section 5): heat multiplies the EPIC and LEGENDARY slices (tod_luck::heat_mult, the one
// table _tod_upgrades roll_rarity also reads) and COMMON pays for it; the guarantees below never read heat.
// LOCKSTEP with TodSpinReel.lua heatOdds (the reel draws these true heated odds on its odds bar).
function roll_rarity( luck )   // self = player
{
    c = 56 - 0.20 * luck; r = 27 + 0.09 * luck; e = 13 + 0.07 * luck;
    hm = tod_luck::heat_mult( self );
    l = 100 - c - r - e;
    c = c - ( e * hm - e ) - ( l * hm - l );
    e = e * hm;
    roll = RandomFloat( 100 );
    rar = 3;
    if ( roll < c ) rar = 0;
    else if ( roll < c + r ) rar = 1;
    else if ( roll < c + r + e ) rar = 2;
    self.tod_spin_guar = "none";
    if ( luck >= 100 && rar < 2 )
    {
        rar = 2; self.tod_spin_guar = "full_epic";
        if ( RandomInt( 100 ) < TOD_SPIN_GUAR_LEG_PCT ) { rar = 3; self.tod_spin_guar = "full_legendary"; }
    }
    else if ( luck >= 50 && rar < 1 )
    {
        rar = 1; self.tod_spin_guar = "half_rare";
    }
    return rar;
}

// NO DEAD SPINS: the prize is an item this companion does not hold, or holds at
// a LOWER rarity (an upgrade). Rolled after the rarity.
function roll_item( slots, rar )
{
    pool = [];
    for ( i = 1; i <= TOD_SPIN_ITEMS; i++ )
    {
        held = -1;
        foreach ( v in slots ) if ( v > 0 && tile_item( v ) == i ) held = tile_rar( v );
        if ( held < rar ) pool[ pool.size ] = i;
    }
    if ( pool.size == 0 ) return 0;
    return pool[ RandomInt( pool.size ) ];
}

// THE NEAR MISS (see the defines): 0 = none, else kind * 64 + the teased tile (item * 4 + rarity), kind 1 STOPPED
// SHORT / 2 SLIPPED PAST. Rolled AFTER the prize from what it already is; it never touches the prize.
function near_plan( rar, slots )
{
    if ( rar >= 3 ) return 0;
    x = RandomInt( 100 );
    kind = 0;
    if ( x < TOD_SPIN_NEAR_SHORT_PCT ) kind = 1;
    else if ( x < TOD_SPIN_NEAR_SHORT_PCT + TOD_SPIN_NEAR_PAST_PCT ) kind = 2;
    if ( kind == 0 ) return 0;
    trar = rar + 1;
    if ( kind == 2 || RandomInt( 100 ) < TOD_SPIN_NEAR_LEG_PCT ) trar = 3;
    titem = roll_item( slots, trar );   // a tile that would really have been new or an upgrade
    if ( titem == 0 ) return 0;
    return kind * 64 + titem * 4 + trar;
}

// nkind = the near miss's kind (0 none): the LAST step carries the jackpot's crawl, the hang on the seam, or the
// creep across the jackpot. LOCKSTEP with tools/ui_mockup/render_spin.py step_ms.
function step_ms( k, rar, nkind )
{
    t = ( k - 1 ) * 1.0 / ( TOD_SPIN_STEPS - 1 );
    ms = TOD_SPIN_STEP_MIN_MS + ( TOD_SPIN_STEP_MAX_MS - TOD_SPIN_STEP_MIN_MS ) * t * t * t;
    if ( k == TOD_SPIN_STEPS )
    {
        if ( rar == 3 ) ms += TOD_SPIN_LEG_HITCH_MS;
        else if ( nkind == 1 ) ms += TOD_SPIN_NEAR_HANG_MS;
        else if ( nkind == 2 ) ms += TOD_SPIN_PAST_HOLD_MS;
    }
    ms = int( ms / 50 + 0.5 ) * 50;
    if ( ms < 50 ) ms = 50;
    return ms;
}

function spin_refusal( p )
{
    if ( !isalive( p ) || p laststand::player_is_in_laststand() ) return "down";
    // any card deal on this player (round event, solo or co-op station, the
    // dev CARD TEST bench) owns the screen and the freeze
    if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( p.tod_menu_frozen ) || IS_TRUE( p.tod_solo_upg_active ) ) return "menu";
    if ( IS_TRUE( p.tod_jumppad_flying ) ) return "flying";
    if ( gift_wanted( p ) ) return "no_companion";   // never reached: the trigger gives him the gift instead (docs/209)
    if ( !( p zm_score::can_player_purchase( TOD_SPIN_COST ) ) ) return "points";
    return "";
}

// ---------------------------------------------------------------- the spin
function spin( shop )   // self = player; tod_spin_busy already set by the trigger
{
    self endon( "disconnect" );
    num = self GetEntityNumber();
    reason = spin_refusal( self );
    if ( reason != "" )
    {
        if ( reason == "points" ) { self PlaySound( "zmb_no_purchase" ); self vo_say( "tod_spin_vo_no_points_" + ( RandomInt( 2 ) + 1 ) ); }
        if ( reason == "menu" ) self vo_say( "tod_spin_vo_busy" );   // a card deal owns the screen: "wait your turn"
        log( "SPIN_REFUSED player=" + num + " reason=" + reason );
        self spin_release_use();
        self.tod_spin_busy = false;
        return;
    }
    comp = self.tod_ptn.chosen;
    self zm_score::minus_to_player_score( TOD_SPIN_COST );
    if ( !isdefined( self.tod_spin_count ) ) self.tod_spin_count = 0;
    self.tod_spin_count++;   // the regular's greeting from the TOD_SPIN_VO_REGULAR_AT'th spin
    self PlayLocalSound( "tod_spin_coin" );   // docs/194 M1: the coin drops into the machine
    // The bar is read and paid into the machine AT THE PURCHASE (docs/188
    // section 1.3), before any wait: a card deal starting this same frame must
    // not spend it out from under the spin the player already paid for.
    luck = tod_luck::get( self );
    if ( luck > 100 ) luck = 100;
    if ( luck < 0 ) luck = 0;
    tod_luck::spend( self );
    self spin_lock( true );
    self spin_wait_world();

    slots = items_of( self, comp );
    rar = self roll_rarity( luck );
    item = roll_item( slots, rar );
    if ( item == 0 ) { rar = 3; item = roll_item( slots, 3 ); }   // unreachable with 9 items and 3 slots
    prize = item * 4 + rar;
    // THE NEAR MISS (docs/201 section 3): decided AFTER the prize, from what it already is
    near = near_plan( rar, slots );
    nkind = int( near / 64 );
    ntile = near - nkind * 64;
    // THE HOT STREAK (docs/201 section 5): the heat this spin rolled with rides to the reel with the near miss in
    // one int (heat * 256 + kind * 64 + tile), so its odds bar can draw the true heated odds
    hot = tod_luck::heat( self );
    tease = hot * 256 + near;
    seed = RandomIntRange( 1, 60000 );
    log( "SPIN_BUY player=" + num + " companion=" + comp + " cost=" + TOD_SPIN_COST + " luck=" + luck + " heat=" + hot + " slots=" + slots[ 0 ] + "," + slots[ 1 ] + "," + slots[ 2 ] );
    log( "SPIN_ROLL player=" + num + " rarity=" + rarity_name( rar ) + " item=" + item_name( item ) + " guarantee=" + self.tod_spin_guar + " heat=" + hot + " mult=" + tod_luck::heat_mult( self ) + " near=" + nkind + " tease=" + ntile + " seed=" + seed );

    // PASS 3 (docs/188): the companion's three slots are on screen from the open, so the
    // player sees what the spin is for; spin_open re-sends them on a resume after a deal
    self.tod_spin_slots_shown = slots;
    self spin_open( seed, prize, tease, luck, 0 );
    self PlayLocalSound( "tod_spin_open" );   // M2: the screen slams on
    counter = local_to_world( shop.origin, shop.yaw, ( 0, -50, 60 ) );
    tod_perk_scatter::play_sound_at_origin( counter, "tod_shop_spark_" + ( RandomInt( 3 ) + 1 ), 4 );
    level thread fx_burst( TOD_SPIN_SPARK_FX, counter, 0.5 );
    self spin_wait( TOD_SPIN_LUCK_SND_AT, seed, prize, tease, luck, 0 );
    if ( luck > 0 ) self PlayLocalSound( "tod_spin_luck" );   // M3: the luck pours in (the reel's pour animation)
    // the dealer reads the bar as it pours: a full one or a poor one gets a word, and that
    // word takes the greeting's place this spin (one lane; the greeting would be dropped anyway)
    self.tod_spin_vo_pour = false;
    // THE HOT STREAK (docs/201): a player HEATING UP or ON FIRE hears him notice it first
    if ( hot >= 2 ) self.tod_spin_vo_pour = self vo_say( "tod_spin_vo_hot_" + ( RandomInt( 3 ) + 1 ), TOD_SPIN_VO_HOT_PCT );
    if ( !IS_TRUE( self.tod_spin_vo_pour ) )
    {
        if ( luck >= 100 ) self.tod_spin_vo_pour = self vo_say( "tod_spin_vo_luck_full", TOD_SPIN_VO_LUCK_PCT );
        else if ( luck < 50 ) self.tod_spin_vo_pour = self vo_say( "tod_spin_vo_luck_low", TOD_SPIN_VO_LUCK_PCT );
    }
    self spin_wait( TOD_SPIN_POUR_SECS - TOD_SPIN_LUCK_SND_AT, seed, prize, tease, luck, 0 );

    last_tick = -1000;
    for ( k = 1; k <= TOD_SPIN_STEPS; k++ )
    {
        ms = step_ms( k, rar, nkind );
        self LuiNotifyEvent( &"tod_spin_step", 2, k, ms );
        if ( k == 1 )
            self PlayLocalSound( "tod_spin_start" );   // M4: the dealer yanks the lever, the reel releases
        else if ( k > TOD_SPIN_STEPS - 5 )
        {
            // M8: the last five tiles crawl in, the click climbing a semitone a tile
            // (alias rows tod_spin_crawl_1..5 = one wav at 0 / 100 / 200 / 300 / 400 cents)
            self PlayLocalSound( "tod_spin_crawl_" + ( k - ( TOD_SPIN_STEPS - 5 ) ) );
        }
        else if ( GetTime() - last_tick >= TOD_SPIN_TICK_MIN_MS )
        {
            // at full speed a tile passes every server frame; one tick per
            // TOD_SPIN_TICK_MIN_MS keeps the rattle fast without a 20 Hz buzz
            self PlayLocalSound( "tod_spin_tick_" + ( ( k % 3 ) + 1 ) );   // M5-M7 rotate: never a machine gun
            last_tick = GetTime();
        }
        if ( k == 3 && !IS_TRUE( self.tod_spin_vo_pour ) )
        {
            // V1-V3, the greeting; a regular (4th spin on) hears his own half the time
            if ( self.tod_spin_count >= TOD_SPIN_VO_REGULAR_AT && RandomInt( 2 ) == 0 ) self vo_say( "tod_spin_vo_regular_" + ( RandomInt( 2 ) + 1 ), TOD_SPIN_VO_BUY_PCT );
            else self vo_say( self vo_cls( "buy", 2, "tod_spin_vo_buy_" + ( RandomInt( 3 ) + 1 ) ), TOD_SPIN_VO_BUY_PCT );
        }
        if ( k % 10 == 0 || k == TOD_SPIN_STEPS ) log( "SPIN_STEP player=" + num + " k=" + k + " ms=" + ms );
        if ( rar == 3 && k == TOD_SPIN_STEPS )
        {
            // THE HEARTBEAT: the reel all but stops on the tile before the
            // jackpot, a thump lands in the middle of the crawl, then it rolls over
            self spin_wait( ms / 2000.0, seed, prize, tease, luck, k );
            self PlayLocalSound( "tod_pull_beat" );
            self spin_wait( ms / 2000.0, seed, prize, tease, luck, k );
        }
        else if ( nkind == 1 && k == TOD_SPIN_STEPS )
        {
            // STOPPED SHORT: the reel runs past the prize to the seam of the better tile and HANGS there (the
            // reel draws the run, the hang and the fall back from this step's ms); a LEGENDARY on the seam gets the
            // jackpot's own heartbeat, a lesser one the strained teeter
            self spin_wait( ( ms - TOD_SPIN_NEAR_HANG_MS - TOD_SPIN_SETTLE_MS ) / 1000.0, seed, prize, tease, luck, k );
            if ( tile_rar( ntile ) >= 3 ) self PlayLocalSound( "tod_pull_beat" );
            else self PlayLocalSound( "tod_spin_teeter" );
            self spin_wait( ( TOD_SPIN_NEAR_HANG_MS + TOD_SPIN_SETTLE_MS ) / 1000.0, seed, prize, tease, luck, k );
        }
        else if ( nkind == 2 && k == TOD_SPIN_STEPS )
        {
            // SLIPPED PAST: the reel creeps across the LEGENDARY it just reached, the heartbeat lands on it, and it
            // creeps on off it (never a stop: no clunk, no flare until the real prize)
            self spin_wait( TOD_SPIN_PAST_HOLD_MS / 2000.0, seed, prize, tease, luck, k );
            self PlayLocalSound( "tod_pull_beat" );
            self spin_wait( ( ms - TOD_SPIN_PAST_HOLD_MS / 2.0 ) / 1000.0, seed, prize, tease, luck, k );
        }
        else self spin_wait( ms / 1000.0, seed, prize, tease, luck, k );
    }

    // THE HIT
    held = -1; empty = -1;
    for ( i = 2; i >= 0; i-- )
    {
        if ( slots[ i ] == 0 ) empty = i;
        else if ( tile_item( slots[ i ] ) == item ) held = i;
    }
    code = 3;
    if ( held >= 0 ) code = 2;
    else if ( empty >= 0 ) code = 1;
    self LuiNotifyEvent( &"tod_spin_land", 2, prize, code );
    self PlayLocalSound( "tod_spin_stop" );   // M9: the reel locks onto the prize
    self land_feedback( counter, rar, item );
    // THE NEAR MISS (docs/201): the "so close" and the dealer's word take the landing line's place
    if ( nkind > 0 ) self thread spin_near_after( nkind, ntile );
    else self thread spin_vo_land( rar );
    // THE HOT STREAK (docs/201 section 5): the spin is one pull, its result the prize the reel just showed
    tod_luck::streak_result( self, rar + 1, "spin", TOD_SPIN_STREAK_FB_SECS );
    log( "SPIN_LAND player=" + num + " prize=" + rarity_name( rar ) + "_" + item_name( item ) + " code=" + code + " held_slot=" + held + " empty_slot=" + empty + " near=" + nkind );
    self LuiNotifyEvent( &"tod_spin_slots", 4, slots[ 0 ], slots[ 1 ], slots[ 2 ], 0 );
    if ( self spin_wait( 1.0, seed, prize, tease, luck, TOD_SPIN_STEPS ) )
        self spin_show_result( prize, code, slots, 0 );

    // SOCKET IT
    idx = -1; how = ""; result = 0;
    if ( code == 2 ) { idx = held; how = "upgrade"; }
    else if ( code == 1 ) { idx = empty; how = "auto"; }
    else
    {
        // "choose what dies" a beat into the choice; cancelled if the choice closes first
        self thread vo_say_later( "tod_spin_vo_full_1", 100, TOD_SPIN_VO_FULL_AT );
        idx = self choose_slot( slots, prize, seed, tease, luck ); how = "choice";
        self notify( "tod_spin_vo_cancel" );
    }
    if ( idx >= 0 )
    {
        slots[ idx ] = prize;
        self.tod_spin_items[ comp ] = slots;
        if ( code == 2 ) self thread spin_sound_later( "tod_spin_upgrade", TOD_SPIN_SOCKET_SND_AT );   // M11
        else self thread spin_sound_later( "tod_spin_socket", TOD_SPIN_SOCKET_SND_AT );                // M10
        if ( code == 2 ) self thread vo_say_later( "tod_spin_vo_upgrade_" + ( RandomInt( 2 ) + 1 ), TOD_SPIN_VO_AFTER_PCT, TOD_SPIN_SOCKET_SND_AT + TOD_SPIN_VO_AFTER_AT );
        else self thread vo_say_later( self vo_cls( "socket", 1, "tod_spin_vo_socket_" + ( RandomInt( 2 ) + 1 ) ), TOD_SPIN_VO_AFTER_PCT, TOD_SPIN_SOCKET_SND_AT + TOD_SPIN_VO_AFTER_AT );
        // mode 2 = RESULT: installed in slot idx (the reel says where it went)
        result = idx * 10 + 2;
        self LuiNotifyEvent( &"tod_spin_slots", 4, slots[ 0 ], slots[ 1 ], slots[ 2 ], result );
        log( "SPIN_SOCKET player=" + num + " companion=" + comp + " slot=" + ( idx + 1 ) + " how=" + how + " slots=" + slots[ 0 ] + "," + slots[ 1 ] + "," + slots[ 2 ] );
    }
    else
    {
        refund = array( 10, 20, 35, 50 );
        tod_luck::add( self, refund[ rar ] );
        self PlayLocalSound( "tod_spin_scrap" );   // M12: the prize breaks up, its luck comes back
        self thread vo_say_later( "tod_spin_vo_scrap_" + ( RandomInt( 2 ) + 1 ), TOD_SPIN_VO_AFTER_PCT, TOD_SPIN_VO_AFTER_AT );
        // mode 3 = RESULT: scrapped; the hundreds carry the luck it paid back
        result = refund[ rar ] * 100 + 30 + 3;
        self LuiNotifyEvent( &"tod_spin_slots", 4, slots[ 0 ], slots[ 1 ], slots[ 2 ], result );
        log( "SPIN_SCRAP player=" + num + " prize=" + rarity_name( rar ) + "_" + item_name( item ) + " luck_back=" + refund[ rar ] + " how=" + how );
    }
    if ( self spin_wait( TOD_SPIN_READ_SECS, seed, prize, tease, luck, TOD_SPIN_STEPS ) )
        self spin_show_result( prize, code, slots, result );
    self PlayLocalSound( "tod_spin_close" );   // M13: the machine powers down
    // V10 on the way out; after an EPIC or LEGENDARY he names the prize instead (a LEGENDARY's
    // laugh is usually still going, and the lane drops the item line then: the laugh is the moment)
    if ( rar >= 2 ) self vo_say( "tod_spin_vo_item_" + item_slug( item ) );
    else self vo_say( self vo_cls( "close", 1, "tod_spin_vo_close" ), TOD_SPIN_VO_CLOSE_PCT );
    self LuiNotifyEvent( &"tod_spin_end", 1, 0 );
    // NEVER UNFREEZE A PLAYER A CARD DEAL IS HOLDING: a deal that began in the
    // spin's last frame owns this player's freeze until it releases it itself
    while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.1;
    self spin_lock( false );
    if ( isdefined( level.tod_partner_items_changed ) ) [[ level.tod_partner_items_changed ]]( self, comp, idx >= 0 );
    self spin_release_use();
    self.tod_spin_slots_shown = undefined;
    self.tod_spin_busy = false;
    log( "SPIN_END player=" + num + " grace_s=" + TOD_SPIN_EXIT_GRACE + " ignoreme=" + IS_TRUE( self.ignoreme ) );
}

// PASS 3 SOUND (docs/194): a sound a beat later on the spinner's own lane (the
// socket click waits for the flying icon)
function spin_sound_later( alias, secs )   // self = player
{
    self endon( "disconnect" );
    wait secs;
    self PlayLocalSound( alias );
}

// The dealer's line on the landing: EPIC and LEGENDARY always, COMMON half the
// time, RARE sometimes (its sting speaks). One of two takes each, so it never nags.
function spin_vo_land( rar )   // self = player
{
    self endon( "disconnect" );
    alias = undefined;
    pct = 100;
    secs = TOD_SPIN_VO_AT;
    if ( rar >= 3 )
    {
        alias = "tod_spin_vo_legendary_" + ( RandomInt( 2 ) + 1 );
        secs = TOD_SPIN_VO_LEG_AT;
    }
    else if ( rar == 2 )
        alias = "tod_spin_vo_epic_" + ( RandomInt( 2 ) + 1 );
    else if ( rar == 1 )
    {
        alias = "tod_spin_vo_rare_" + ( RandomInt( 2 ) + 1 );
        pct = TOD_SPIN_VO_RARE_PCT;
    }
    else
    {
        alias = "tod_spin_vo_common_" + ( RandomInt( 2 ) + 1 );
        pct = TOD_SPIN_VO_COMMON_PCT;
    }
    wait secs;
    self vo_say( alias, pct );
}

// THE NEAR MISS's aftermath (docs/201 section 3): the deflate a beat after the stop, then the dealer's "so close"
// (the class's own line TOD_SPIN_VO_CLASS_PCT of the time, through vo_cls like every hook).
function spin_near_after( nkind, ntile )   // self = player
{
    self endon( "disconnect" );
    wait TOD_SPIN_NEAR_SND_AT;
    self PlayLocalSound( "tod_spin_near" );
    kind = "stopped_short";
    if ( nkind == 2 ) kind = "slipped_past";
    log( "SPIN_NEAR player=" + self GetEntityNumber() + " kind=" + kind + " tease=" + rarity_name( tile_rar( ntile ) ) + "_" + item_name( tile_item( ntile ) ) + " heartbeat=" + ( tile_rar( ntile ) >= 3 ) );
    wait TOD_SPIN_VO_NEAR_AT - TOD_SPIN_NEAR_SND_AT;
    self vo_say( self vo_cls( "near", 1, "tod_spin_vo_near_" + ( RandomInt( 4 ) + 1 ) ), TOD_SPIN_VO_NEAR_PCT );
}

// ---------------------------------------------------------------- the voice lane
// ONE lane per player: a line asked for while another is still speaking is dropped, never
// queued. Returns true when the line played. pct (optional) = the chance it is asked for at all.
function vo_say( alias, pct )   // self = player
{
    if ( isdefined( pct ) && RandomInt( 100 ) >= pct ) return false;
    if ( !isdefined( self ) || !isplayer( self ) ) return false;
    if ( isdefined( self.tod_spin_vo_until ) && GetTime() < self.tod_spin_vo_until )
    {
        log( "VO_DROP player=" + self GetEntityNumber() + " alias=" + alias + " busy_ms=" + ( self.tod_spin_vo_until - GetTime() ) );
        return false;
    }
    mouth = level.tod_spin_vo_mouth;
    if ( !isdefined( mouth ) || !isdefined( level.tod_shop_active ) || level.tod_shop_active < 0 ) return false;   // no lit counter, no dealer
    secs = tod_shop_vo::secs( alias );
    self.tod_spin_vo_until = GetTime() + int( secs * 1000 ) + TOD_SPIN_VO_GAP_MS;
    mouth PlaySoundToPlayer( alias, self );   // 3D from the mask, heard by this player only
    log( "VO player=" + self GetEntityNumber() + " alias=" + alias + " secs=" + secs + " from=" + mouth.origin );
    return true;
}

// The same, a beat later (the lane is checked when the line would play, not when it is asked for).
// Ends with the player's own "tod_spin_vo_cancel" (the slot choice closing under a pending line).
function vo_say_later( alias, pct, secs )   // self = player
{
    self endon( "disconnect" );
    self endon( "tod_spin_vo_cancel" );
    wait secs;
    self vo_say( alias, pct );
}

// THE CLASSES (user 2026-10-01: "the dealer has specific lines depending on the class interacting with
// him"): he recognises who is at his window. vo_cls() answers the class's OWN line for a hook
// (tod_spin_vo_cls_<slug>_<hook>_N, six per class in tools/black_market_vo/lines.json) TOD_SPIN_VO_CLASS_PCT
// of the time and the generic line otherwise, so the generic set keeps playing and no one line nags.
// A player with no class yet (the draft) always hears the generic line. The pct roll happens here, before
// vo_say's own chance roll, so the hook's overall rate is unchanged.
function vo_cls_slug()   // self = player: the dealer's name for the class, "" when he cannot tell
{
    if ( !isdefined( self.tod_class ) ) return "";
    switch ( self.tod_class )
    {
        case "assault":     return "archer";
        case "heavy":       return "breacher";
        case "slasher":     return "warrior";
        case "necromancer": return "necro";
    }
    return "";
}

function vo_cls( hook, n_cls, generic )   // self = player; hook = approach / buy / close / socket, n_cls = lines authored per class
{
    slug = self vo_cls_slug();
    if ( slug == "" || RandomInt( 100 ) >= TOD_SPIN_VO_CLASS_PCT ) return generic;
    return "tod_spin_vo_cls_" + slug + "_" + hook + "_" + ( RandomInt( n_cls ) + 1 );
}

function item_slug( item )
{
    slugs = array( "", "plating", "overclock", "hollow_point", "long_sight", "nano_repair", "arc_chain", "salvage", "quick_reboot", "lucky_charm" );
    if ( item < 1 || item >= slugs.size ) return "plating";
    return slugs[ item ];
}

function vo_counter_org()
{
    if ( !isdefined( level.tod_shop_active ) || level.tod_shop_active < 0 ) return undefined;
    s = level.tod_shops[ level.tod_shop_active ];
    if ( !isdefined( s ) ) return undefined;
    return local_to_world( s.origin, s.yaw, ( 0, -50, 60 ) );
}

// THE GREETING: a player walking up to the lit counter hears him once per visit (leave the
// radius to earn another), at most once per TOD_SPIN_VO_APPROACH_CD, never while spinning.
function vo_approach_watch()
{
    level endon( "end_game" );
    for ( ;; )
    {
        wait 0.15;   // was 0.5: the greeting must land as you arrive
        if ( IS_TRUE( level.tod_shop_hold ) ) continue;   // docs/207: the house's scene owns his voice
        counter = vo_counter_org();
        foreach ( p in GetPlayers() )
        {
            if ( !isdefined( p ) || !isplayer( p ) ) continue;
            if ( !isdefined( counter ) || !isalive( p ) )
            {
                p.tod_spin_vo_near = false;
                continue;
            }
            // MID-SPIN THE WALK-UP LATCH IS KEPT, NOT CLEARED (LT-rest 2026-10-05, the user's 17:33 run): clearing it
            // here made the end of every spin and gift a fresh walk-up, so he greeted a player who had never left
            // the counter (GIFT_END at ms=368450, a class "approach" line 150 ms later; the gift's offer path never
            // arms the greeting cooldown). Leaving the radius is still the only way to earn another greeting.
            if ( IS_TRUE( p.tod_spin_locked ) || IS_TRUE( p.tod_spin_busy ) )
            {
                p.tod_spin_vo_held = true;
                continue;
            }
            near = ( Distance2D( p.origin, counter ) <= TOD_SPIN_VO_APPROACH_R );
            if ( IS_TRUE( p.tod_spin_vo_held ) )
            {
                p.tod_spin_vo_held = undefined;
                log( "VO_GREET_HOLD player=" + p GetEntityNumber() + " near=" + near + " latch=" + IS_TRUE( p.tod_spin_vo_near ) + " (a spin's end is not a walk-up)" );
            }
            if ( near && !IS_TRUE( p.tod_spin_vo_near ) )
            {
                if ( gift_wanted( p ) )
                {
                    // THE DEALER'S GIFT (docs/209): a player with no companion hears the offer as he walks up - no
                    // chance roll (it is the line that tells him the gift is here), only a short cooldown so pacing at
                    // the edge of the radius never makes him repeat it
                    if ( !isdefined( p.tod_spin_vo_gift_ms ) || GetTime() - p.tod_spin_vo_gift_ms >= TOD_GIFT_VO_OFFER_CD * 1000 )
                    {
                        if ( p vo_say( "tod_spin_vo_gift_offer_" + ( RandomInt( 2 ) + 1 ) ) ) p.tod_spin_vo_gift_ms = GetTime();
                    }
                }
                else if ( !isdefined( p.tod_spin_vo_greet_ms ) || GetTime() - p.tod_spin_vo_greet_ms >= TOD_SPIN_VO_APPROACH_CD * 1000 )
                {
                    if ( p vo_say( p vo_cls( "approach", 2, "tod_spin_vo_approach_" + ( RandomInt( 4 ) + 1 ) ), TOD_SPIN_VO_APPROACH_PCT ) )
                        p.tod_spin_vo_greet_ms = GetTime();
                }
            }
            p.tod_spin_vo_near = near;
        }
    }
}

// THE MUTTERS: every 30-60 s the lit counter mutters to itself, to every player within
// TOD_SPIN_VO_IDLE_R (each on his own lane, from the mouth), only while someone is close enough
// to hear and nobody is mid-spin (a spinner's own lines must not fight the counter's).
function vo_idle_watch()
{
    level endon( "end_game" );
    for ( ;; )
    {
        wait RandomIntRange( TOD_SPIN_VO_IDLE_MIN, TOD_SPIN_VO_IDLE_MAX + 1 );
        if ( IS_TRUE( level.tod_shop_hold ) ) continue;   // docs/207: the house's scene owns his voice
        counter = vo_counter_org();
        if ( !isdefined( counter ) ) continue;
        heard = false; spinning = false;
        foreach ( p in GetPlayers() )
        {
            if ( !isdefined( p ) || !isplayer( p ) ) continue;
            if ( IS_TRUE( p.tod_spin_locked ) ) spinning = true;
            if ( isalive( p ) && Distance( p.origin, counter ) <= TOD_SPIN_VO_IDLE_R ) heard = true;
        }
        if ( !heard || spinning ) continue;
        alias = "tod_spin_vo_idle_" + ( RandomInt( 6 ) + 1 );
        n = 0;
        foreach ( p in GetPlayers() )
        {
            if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) ) continue;
            if ( Distance( p.origin, counter ) > TOD_SPIN_VO_IDLE_R ) continue;
            if ( p vo_say( alias ) ) n++;   // each hearer gets his own copy from the mouth, on his own lane
        }
        log( "VO_IDLE alias=" + alias + " hearers=" + n );
    }
}

// EVERY WAIT INSIDE A SPIN goes through here: a world pause (a card deal) that
// begins during it takes the screen at once instead of after the wait. Returns
// true when it held, so the caller can put the prize back on the resumed reel.
function spin_wait( secs, seed, prize, tease, luck, at )   // self = player
{
    held = false;
    while ( secs > 0.01 )   // not > 0: float residue from the 0.05 steps would cost a whole extra frame
    {
        if ( self spin_hold_for_pause( seed, prize, tease, luck, at ) ) held = true;
        step = 0.05;
        if ( secs < step ) step = secs;
        wait step;
        secs -= step;
    }
    if ( self spin_hold_for_pause( seed, prize, tease, luck, at ) ) held = true;
    return held;
}

// After a hold the reel re-opens empty at the landing tile: repaint the prize
// (banner, name, effect) and the slot row as they were.
function spin_show_result( prize, code, slots, packed )   // self = player
{
    self LuiNotifyEvent( &"tod_spin_land", 2, prize, code );
    self LuiNotifyEvent( &"tod_spin_slots", 4, slots[ 0 ], slots[ 1 ], slots[ 2 ], packed );
}

function spin_open( seed, prize, tease, luck, at )   // self = player
{
    self LuiNotifyEvent( &"tod_spin_open", 4, seed, prize, tease, luck * 64 + TOD_SPIN_STEPS );
    s = self.tod_spin_slots_shown;
    if ( isdefined( s ) ) self LuiNotifyEvent( &"tod_spin_slots", 4, s[ 0 ], s[ 1 ], s[ 2 ], 0 );
    // THE DEALER'S GIFT (docs/209): while its reel runs, the slot row is THE POOL (the four companions)
    if ( IS_TRUE( self.tod_gift_pool ) ) self LuiNotifyEvent( &"tod_spin_slots", 4, 0, 0, 0, TOD_GIFT_POOL_MODE );
    if ( at > 0 ) self LuiNotifyEvent( &"tod_spin_step", 2, at, 50 );
}

// A card deal (or any world pause) that begins at the purchase owns the screen
// first: the spin waits under it, then re-freezes and opens.
function spin_wait_world()   // self = player
{
    if ( !IS_TRUE( level.tod_upgrade_pause ) ) return;
    log( "SPIN_HOLD player=" + self GetEntityNumber() + " at=0 reason=world_pause_at_buy" );
    while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.1;
    wait 0.3;   // the card panel's own unfreeze lands first
    self tod_upgrades::menu_freeze( true );
    log( "SPIN_RESUME player=" + self GetEntityNumber() + " at=0" );
}

// A card deal (or a solo station freeze) that starts mid-spin owns the screen
// and the freeze: hide the reel, wait it out, then re-freeze and re-open the
// reel exactly where it was. The spinner stays untargetable throughout.
function spin_hold_for_pause( seed, prize, tease, luck, at )   // self = player
{
    if ( !IS_TRUE( level.tod_upgrade_pause ) ) return false;
    self LuiNotifyEvent( &"tod_spin_end", 1, 0 );
    log( "SPIN_HOLD player=" + self GetEntityNumber() + " at=" + at + " reason=world_pause" );
    while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.1;
    wait 0.3;   // the card panel's own unfreeze lands first
    self tod_upgrades::menu_freeze( true );
    self spin_open( seed, prize, tease, luck, at );
    log( "SPIN_RESUME player=" + self GetEntityNumber() + " at=" + at );
    return true;
}

// Full slots: TACTICAL / LETHAL (or the d-pad) move over SLOT 1 / 2 / 3 / SCRAP,
// hold JUMP or USE to confirm. Returns 0..2, or -1 = scrap. Timeout = scrap.
// NO ACCIDENTAL LOSSES (the first playtest confirmed a replace 0.65 s after the
// choice appeared): focus starts on the weakest slot ONLY when the prize beats
// it, otherwise on SCRAP; for TOD_SPIN_CHOICE_GRACE no hold counts; and a button
// that is down when the grace ends must be released before it can confirm.
function choose_slot( slots, prize, seed, tease, luck )   // self = player
{
    weakest = 0;
    for ( i = 1; i < 3; i++ ) if ( tile_rar( slots[ i ] ) < tile_rar( slots[ weakest ] ) ) weakest = i;
    focus = 3;
    if ( tile_rar( prize ) > tile_rar( slots[ weakest ] ) ) focus = weakest;
    held = 0; jump_armed = 0; use_armed = 0;
    grace = TOD_SPIN_CHOICE_GRACE;
    last_sec = ( ( self SecondaryOffhandButtonPressed() ) ? 1 : 0 );
    last_frg = ( ( self FragButtonPressed() ) ? 1 : 0 );
    last_d3 = 0; last_d4 = 0;
    left = TOD_SPIN_CHOICE_SECS;
    self LuiNotifyEvent( &"tod_spin_land", 2, prize, 3 );
    log( "SPIN_CHOICE_OPEN player=" + self GetEntityNumber() + " focus=" + focus + " weakest=" + weakest );
    sent = -1;
    while ( left > 0 )
    {
        if ( self spin_hold_for_pause( seed, prize, tease, luck, TOD_SPIN_STEPS ) )
        {
            self LuiNotifyEvent( &"tod_spin_land", 2, prize, 3 );
            sent = -1; held = 0; jump_armed = 0; use_armed = 0; grace = TOD_SPIN_CHOICE_GRACE;
        }
        want = focus;
        sec = ( ( self SecondaryOffhandButtonPressed() ) ? 1 : 0 );
        frg = ( ( self FragButtonPressed() ) ? 1 : 0 );
        d3 = ( ( self ActionSlotThreeButtonPressed() ) ? 1 : 0 );
        d4 = ( ( self ActionSlotFourButtonPressed() ) ? 1 : 0 );
        if ( ( sec && !last_sec ) || ( d3 && !last_d3 ) ) want = ( focus + 3 ) % 4;
        else if ( ( frg && !last_frg ) || ( d4 && !last_d4 ) ) want = ( focus + 1 ) % 4;
        last_sec = sec; last_frg = frg; last_d3 = d3; last_d4 = d4;
        if ( want != focus ) { focus = want; held = 0; self PlayLocalSound( "tod_ui_tick" ); }
        b_jump = self JumpButtonPressed();
        b_use = self UseButtonPressed();
        if ( grace > 0 )
        {
            grace -= 0.05;
            held = 0;
        }
        else
        {
            if ( !b_jump ) jump_armed = 1;
            if ( !b_use ) use_armed = 1;
            if ( ( b_jump && jump_armed ) || ( b_use && use_armed ) ) held += 0.05;
            else held = 0;
        }
        packed = int( held * 10 / TOD_SPIN_HOLD_SECS ) * 100 + focus * 10 + 1;
        if ( packed != sent ) { self LuiNotifyEvent( &"tod_spin_slots", 4, slots[ 0 ], slots[ 1 ], slots[ 2 ], packed ); sent = packed; }
        if ( held >= TOD_SPIN_HOLD_SECS )
        {
            log( "SPIN_CHOICE player=" + self GetEntityNumber() + " focus=" + focus + " after_ms=" + int( ( TOD_SPIN_CHOICE_SECS - left ) * 1000 ) );
            if ( focus == 3 ) return -1;
            return focus;
        }
        left -= 0.05;
        wait 0.05;
    }
    log( "SPIN_CHOICE player=" + self GetEntityNumber() + " timeout=1 scrap=1" );
    return -1;
}

// The card reveal's sound language (docs/187), so one ladder sounds one way:
// COMMON the card land, RARE / EPIC the sting, LEGENDARY the jackpot, and a
// LEGENDARY is announced to everyone else exactly like a Legendary card.
function land_feedback( counter, rar, item )   // self = player
{
    if ( rar >= 3 ) self PlayLocalSound( "tod_pull_legendary" );
    else if ( rar >= 1 ) self PlayLocalSound( "tod_super_sting" );
    else self PlayLocalSound( "tod_card_land" );
    if ( rar >= 1 ) tod_perk_scatter::play_sound_at_origin( counter, "tod_shop_spark_" + ( RandomInt( 3 ) + 1 ), 4 );
    if ( rar >= 2 ) level thread fx_burst( TOD_SPIN_SPARK_FX, counter, 0.4 + 0.4 * rar );
    if ( rar < 3 ) return;
    level thread fx_burst( TOD_SPIN_BLAST_FX, counter + ( 0, 0, 20 ), 0.8 );
    tod_perk_scatter::play_sound_at_origin( counter, "tod_thor_clap", 6 );
    // the teammates hear it and read it in our typeface: THE TOAST, kind 2 (TodToast.lua names the item; LOCKSTEP
    // item_name). RT 2026-10-05: it was a stock-font IPrintLnBold.
    self tod_upgrade_ui::team_toast( 2, item, "tod_pull_alert" );
}

// Frozen (the card panel's soft freeze: button reads stay live), UNTARGETABLE
// (stock's ignoreme refcount) and unhurtable (user: "During use of the item
// shop you cannot be targeted by enemies"). The invulnerability is re-asserted
// every tick, so a world pause ending mid-spin cannot strip it. The prompt
// leaves the spinner's screen the same frame (spin_vis_apply_all).
function spin_lock( on )   // self = player
{
    if ( on )
    {
        if ( IS_TRUE( self.tod_spin_locked ) ) return;
        self.tod_spin_locked = true;
        spin_vis_apply_all();
        self tod_upgrades::menu_freeze( true );
        self zm_utility::increment_ignoreme();
        self EnableInvulnerability();
        self thread spin_invuln_hold();
        log( "SPIN_LOCK player=" + self GetEntityNumber() + " ignoreme=" + IS_TRUE( self.ignoreme ) );
        return;
    }
    if ( !IS_TRUE( self.tod_spin_locked ) ) return;
    self.tod_spin_locked = undefined;
    self notify( "tod_spin_unlock" );
    self tod_upgrades::menu_freeze( false );
    self zm_utility::decrement_ignoreme();
    spin_vis_apply_all();
    self thread spin_exit_grace();
}

function spin_invuln_hold()   // self = player
{
    self endon( "disconnect" ); self endon( "tod_spin_unlock" );
    while ( IS_TRUE( self.tod_spin_locked ) ) { self EnableInvulnerability(); wait 0.1; }
}

// EXIT GRACE: zombies that idled next to an untargetable player re-acquire the
// frame the panel closes. For TOD_SPIN_EXIT_GRACE the player is targetable
// again but cannot be hurt, so control returns before the first swing lands.
function spin_exit_grace()   // self = player
{
    self endon( "disconnect" );
    self notify( "tod_spin_grace" );
    self endon( "tod_spin_grace" );
    self.tod_spin_grace = true;
    self EnableInvulnerability();
    wait TOD_SPIN_EXIT_GRACE;
    self.tod_spin_grace = undefined;
    if ( IS_TRUE( self.tod_spin_locked ) ) return;   // a new spin owns it now
    if ( IS_TRUE( self.tod_pause_invuln ) || ( self tod_upgrades::pause_invuln_held_elsewhere() ) ) return;
    self DisableInvulnerability();
    log( "SPIN_GRACE_END player=" + self GetEntityNumber() );
}

// The same held USE never buys twice.
function spin_release_use()   // self = player
{
    self endon( "disconnect" );
    for ( i = 0; i < 60 && self UseButtonPressed(); i++ ) wait 0.05;
    wait 0.2;
}

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

// =============================================================================
// THE DEALER'S GIFT (docs/209; the defines at the top). What the player sees and hears, in order:
//   the walk-up   - the GIFT prompt (BLACK MARKET - A free AI companion / No points or luck - on the house, TO TAKE) and
//                   the dealer's offer line (vo_approach_watch);
//   the hold      - locked, untargetable and unhurtable exactly like a spin (spin_lock); the machine slams in, his
//                   LUCK box reads his bar and NOTHING pours out of it; THE DEALER'S GIFT where the odds would be;
//   the reel      - the four companions rush past the needle and crawl in; the dealer leans in; his word;
//   the hit       - the companion's tile flares cyan, ON THE HOUSE stamps in, the companion's portrait punches into
//                   the right window, its name and what it does under the banner, its three item slots EMPTY with
//                   SPIN TO FILL (what the counter is for next time); his gift line;
//   the close     - the panel drops, control returns (the spin's exit grace) and the companion MATERIALISES beside
//                   him the same tick (_tod_partners arrive_fx: the teleporter's arrival).
// Every wait goes through spin_wait, so a card deal that starts mid-gift takes the screen and hands it back.
// =============================================================================

// PUBLIC (the dispatcher, the prompts, the greeting): this player has no companion yet, so the counter GIVES.
function gift_wanted( p )
{
    if ( !isdefined( p ) || !isplayer( p ) ) return false;
    return ( !isdefined( p.tod_ptn ) || !isdefined( p.tod_ptn.chosen ) || p.tod_ptn.chosen < 0 );
}

function gift_refusal( p )
{
    if ( !isalive( p ) || p laststand::player_is_in_laststand() ) return "down";
    if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( p.tod_menu_frozen ) || IS_TRUE( p.tod_solo_upg_active ) ) return "menu";
    if ( IS_TRUE( p.tod_jumppad_flying ) ) return "flying";
    if ( !gift_wanted( p ) ) return "has_companion";   // a tester's bench pick in the last 0.25 s: the BUY prompt is next
    if ( !isdefined( level.tod_partner_gift_fn ) ) return "no_partner_module";
    return "";
}

// RANDOM, and in co-op the dealer hands out a companion nobody else in the party holds while one is left (four players,
// four different companions); with all four taken, any of them. -> 0..TOD_GIFT_COMPANIONS - 1
function gift_pick( p )
{
    held = [];
    for ( i = 0; i < TOD_GIFT_COMPANIONS; i++ ) held[ i ] = false;
    foreach ( o in GetPlayers() )
    {
        if ( !isdefined( o ) || o == p || !isdefined( o.tod_ptn ) || !isdefined( o.tod_ptn.chosen ) ) continue;
        c = o.tod_ptn.chosen;
        if ( c >= 0 && c < TOD_GIFT_COMPANIONS ) held[ c ] = true;
    }
    pool = [];
    for ( i = 0; i < TOD_GIFT_COMPANIONS; i++ ) if ( !held[ i ] ) pool[ pool.size ] = i;
    if ( pool.size == 0 ) return RandomInt( TOD_GIFT_COMPANIONS );
    return pool[ RandomInt( pool.size ) ];
}

// The gift's reel: the spin's cubic slow-down over the same 30 tiles, crawling to TOD_GIFT_STEP_MAX_MS instead of
// 700 (no hitch, no near miss: nothing to tease, it is a gift). LOCKSTEP tools/ui_mockup/render_spin.py gift_step_ms.
function gift_step_ms( k )
{
    t = ( k - 1 ) * 1.0 / ( TOD_SPIN_STEPS - 1 );
    ms = TOD_SPIN_STEP_MIN_MS + ( TOD_GIFT_STEP_MAX_MS - TOD_SPIN_STEP_MIN_MS ) * t * t * t;
    ms = int( ms / 50 + 0.5 ) * 50;
    if ( ms < 50 ) ms = 50;
    return ms;
}

function gift( shop )   // self = player; tod_spin_busy already set by the trigger
{
    self endon( "disconnect" );
    num = self GetEntityNumber();
    reason = gift_refusal( self );
    if ( reason != "" )
    {
        if ( reason == "menu" ) self vo_say( "tod_spin_vo_busy" );   // a card deal owns the screen: "wait your turn"
        log( "GIFT_REFUSED player=" + num + " reason=" + reason );
        self spin_release_use();
        self.tod_spin_busy = false;
        return;
    }
    comp = gift_pick( self );
    // THE USER'S RULE: the gift never touches the luck bar. It is read for the LUCK box, never spent.
    luck = tod_luck::get( self );
    if ( luck > 100 ) luck = 100;
    if ( luck < 0 ) luck = 0;
    self spin_lock( true );
    self spin_wait_world();
    seed = RandomIntRange( 1, 60000 );
    prize = TOD_GIFT_TILE_BASE + comp + 1;
    self.tod_spin_slots_shown = undefined;   // no item slots while the reel picks: he has no companion yet ...
    self.tod_gift_pool = true;               // ... the row shows THE POOL instead (spin_open sends it, and again on a resume)
    log( "GIFT_BEGIN player=" + num + " companion=" + comp + " luck_kept=" + luck + " seed=" + seed + " party=" + GetPlayers().size );
    self spin_open( seed, prize, 0, luck, 0 );
    self PlayLocalSound( "tod_spin_open" );   // the screen slams on (no coin: it costs nothing)
    counter = local_to_world( shop.origin, shop.yaw, ( 0, -50, 60 ) );
    tod_perk_scatter::play_sound_at_origin( counter, "tod_shop_spark_" + ( RandomInt( 3 ) + 1 ), 4 );
    level thread fx_burst( TOD_SPIN_SPARK_FX, counter, 0.5 );
    self vo_say( "tod_spin_vo_gift_spin_" + ( RandomInt( 2 ) + 1 ) );   // "on the house"
    self spin_wait( TOD_GIFT_OPEN_SECS, seed, prize, 0, luck, 0 );

    last_tick = -1000;
    for ( k = 1; k <= TOD_SPIN_STEPS; k++ )
    {
        ms = gift_step_ms( k );
        self LuiNotifyEvent( &"tod_spin_step", 2, k, ms );
        if ( k == 1 )
            self PlayLocalSound( "tod_spin_start" );   // the lever
        else if ( k > TOD_SPIN_STEPS - 5 )
            self PlayLocalSound( "tod_spin_crawl_" + ( k - ( TOD_SPIN_STEPS - 5 ) ) );   // the climbing crawl
        else if ( GetTime() - last_tick >= TOD_SPIN_TICK_MIN_MS )
        {
            self PlayLocalSound( "tod_spin_tick_" + ( ( k % 3 ) + 1 ) );
            last_tick = GetTime();
        }
        if ( k % 10 == 0 || k == TOD_SPIN_STEPS ) log( "GIFT_STEP player=" + num + " k=" + k + " ms=" + ms );
        self spin_wait( ms / 1000.0, seed, prize, 0, luck, k );
    }

    // THE HIT: the companion is his, the moment the reel shows it
    self.tod_gift_pool = undefined;
    self LuiNotifyEvent( &"tod_spin_land", 2, prize, TOD_SPIN_CODE_GIFT );
    self PlayLocalSound( "tod_spin_stop" );
    self PlayLocalSound( "tod_super_sting" );   // the reveal's good-news sting (the card / spin sound language)
    tod_perk_scatter::play_sound_at_origin( counter, "tod_shop_spark_" + ( RandomInt( 3 ) + 1 ), 4 );
    level thread fx_burst( TOD_SPIN_SPARK_FX, counter, 1.2 );
    given = [[ level.tod_partner_gift_fn ]]( self, comp );
    self LuiNotifyEvent( &"tod_spin_slots", 4, 0, 0, 0, TOD_GIFT_SLOTS_MODE );   // its three item slots, empty: SPIN TO FILL
    self thread gift_vo_land( "tod_spin_vo_gift_land_" + ( RandomInt( 2 ) + 1 ) );
    log( "GIFT_LAND player=" + num + " companion=" + comp + " given=" + IS_TRUE( given ) + " luck_now=" + tod_luck::get( self ) );
    if ( self spin_wait( TOD_GIFT_READ_SECS, seed, prize, 0, luck, TOD_SPIN_STEPS ) )
        self gift_show_result( prize );

    self PlayLocalSound( "tod_spin_close" );
    self LuiNotifyEvent( &"tod_spin_end", 1, 0 );
    // NEVER UNFREEZE A PLAYER A CARD DEAL IS HOLDING (the spin's rule)
    while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.1;
    self spin_lock( false );   // the companion deploys on the manager's next tick (_tod_partners freeze_reason lifts)
    self spin_release_use();
    self.tod_spin_busy = false;
    log( "GIFT_END player=" + num + " companion=" + comp + " grace_s=" + TOD_SPIN_EXIT_GRACE );
}

// The gift's landing line is its payoff, so unlike every other dealer hook it is never DROPPED by the one-voice lane:
// it waits (up to TOD_GIFT_VO_LAND_WAIT) for his reel line to finish, then speaks - still never over himself. A walk-up
// offer still talking when he pressed USE can outlast the wait; then the offer was this gift's line.
function gift_vo_land( alias )   // self = player
{
    self endon( "disconnect" );
    wait TOD_GIFT_VO_LAND_AT;
    for ( i = 0; i < TOD_GIFT_VO_LAND_WAIT * 20 && isdefined( self.tod_spin_vo_until ) && GetTime() < self.tod_spin_vo_until; i++ ) wait 0.05;
    if ( !self vo_say( alias ) ) log( "GIFT_VO_LAND dropped=1 alias=" + alias + " waited_ms=" + ( i * 50 ) );
    else log( "GIFT_VO_LAND dropped=0 alias=" + alias + " waited_ms=" + ( i * 50 ) );
}

// After a card deal held the gift, the reel re-opens at the landing tile: repaint the companion and its empty slots.
function gift_show_result( prize )   // self = player
{
    self LuiNotifyEvent( &"tod_spin_land", 2, prize, TOD_SPIN_CODE_GIFT );
    self LuiNotifyEvent( &"tod_spin_slots", 4, 0, 0, 0, TOD_GIFT_SLOTS_MODE );
}

// THE NUDGE (once per match): TOD_GIFT_NUDGE_SECS after a counter first lights - the power coming on - every player
// with no companion is told where his free one waits. A card deal on screen goes first.
function gift_nudge()
{
    level endon( "end_game" );
    wait TOD_GIFT_NUDGE_SECS;
    while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.5;
    if ( !isdefined( level.tod_shop_active ) || level.tod_shop_active < 0 || IS_TRUE( level.tod_shop_hold ) ) { log( "GIFT_NUDGE skipped=no_lit_counter" ); return; }
    n = 0;
    foreach ( p in GetPlayers() )
    {
        if ( !isdefined( p ) || !isplayer( p ) || !gift_wanted( p ) || IS_TRUE( p.tod_gift_nudged ) ) continue;
        p.tod_gift_nudged = true;
        // WHERE, not only what (2026-10-04, the first real-run review): the counter lights at the POWER, when the
        // party is in the power room or on the balcony beside the one-way jump pad, and it is the ONLY Black Market
        // until the ground floor. Dev mode lit it from the first second, so nobody ever had to go back for it.
        p IPrintLnBold( ( ( level.tod_shop_active == 0 ) ? "A FREE AI COMPANION WAITS AT THE BLACK MARKET IN THE CROWN HALL" : "A FREE AI COMPANION WAITS AT THE BLACK MARKET" ) );
        n++;
    }
    log( "GIFT_NUDGE players=" + n );
}

// =============================================================================
// THE DEALER'S HOUSE (docs/207, user 2026-10-04): the parlour's counter and THE LAST ROLL.
// _tod_house.gsc owns the scene; this module owns the counter (its parts, its mouth, its
// cycler) and the reel protocol, so the rigged roll draws exactly like a bought one until it
// lands - on CURSED, a tile that is not on the wheel. Every player sees the same reel.
// =============================================================================
function shop_add( origin, yaw )   // PUBLIC: a fifth counter (the parlour's). -> its index, or -1. The cycler never reaches it.
{
    if ( !isdefined( level.tod_shops ) ) return -1;
    i = level.tod_shops.size;
    shop = SpawnStruct(); shop.id = i; shop.origin = origin; shop.yaw = yaw; shop.parts = [];
    shop.body = Spawn( "script_model", shop.origin );
    if ( !isdefined( shop.body ) ) { log( "ADD_FAIL slot=" + i + " reason=body_spawn" ); return -1; }
    shop.body SetModel( "tod_shop_off" ); shop.body.angles = ( 0, shop.yaw, 0 );
    shop.body.targetname = "tod_item_shop"; shop.body NotSolid();
    level.tod_shops[ i ] = shop;
    log( "ADDED id=" + i + " origin=" + origin + " yaw=" + yaw + " (the house's counter)" );
    return i;
}

function house_shop_begin( origin, yaw )   // PUBLIC: the parlour's counter lights; the cycler + the greeting / mutters hold. -> true when lit
{
    level.tod_shop_hold = true;
    if ( !isdefined( level.tod_house_shop ) ) level.tod_house_shop = shop_add( origin, yaw );
    if ( level.tod_house_shop < 0 ) return false;
    for ( i = 0; i < 40 && IS_TRUE( level.tod_shop_busy ); i++ ) wait 0.1;   // a transition in flight finishes first
    ok = activate( level.tod_house_shop, "house" );
    // the counter's own two prompts stay dark: THE LAST ROLL has its own (_tod_house)
    if ( isdefined( level.tod_spin_trig ) ) level.tod_spin_trig TriggerEnable( false );
    if ( isdefined( level.tod_spin_need ) ) level.tod_spin_need TriggerEnable( false );
    log( "HOUSE on id=" + level.tod_house_shop + " ok=" + ok );
    return ok;
}

function house_shop_end()   // PUBLIC: the parlour's counter goes dark; the crown's comes back on the cycler's next tick
{
    if ( isdefined( level.tod_house_shop ) && level.tod_shop_active == level.tod_house_shop )
    {
        for ( i = 0; i < 40 && IS_TRUE( level.tod_shop_busy ); i++ ) wait 0.1;
        activate( -1, "house_over" );
    }
    level.tod_shop_hold = false;
    log( "HOUSE off" );
}

function house_mouth()   // PUBLIC: the lit counter's mouth (his 3D lines play from it); undefined while no counter is lit
{
    if ( !isdefined( level.tod_shop_active ) || level.tod_shop_active < 0 ) return undefined;
    return level.tod_spin_vo_mouth;
}

// THE LAST ROLL: the reel to CURSED on every player's screen (one seed, the same steps, the same sounds),
// a STOPPED SHORT hang on a LEGENDARY and the fall onto the curse. Returns at the landing; the caller holds
// the read, the laugh and house_roll_end.
function house_roll( roller, party )
{
    level endon( "end_game" );
    s = undefined;
    if ( isdefined( level.tod_house_shop ) && isdefined( level.tod_shops[ level.tod_house_shop ] ) ) s = level.tod_shops[ level.tod_house_shop ];
    counter = undefined;
    if ( isdefined( s ) ) counter = local_to_world( s.origin, s.yaw, ( 0, -50, 60 ) );
    seed = RandomIntRange( 1, 60000 );
    prize = TOD_SPIN_CURSED_TILE;
    tease = 1 * 64 + TOD_SPIN_CURSED_TEASE;   // STOPPED SHORT (kind 1) on the LEGENDARY: the heartbeat, the hang, the fall
    luck = 100;                                // the bar reads full: "on the house"
    log( "HOUSE_ROLL roller=" + ( ( isdefined( roller ) ) ? roller GetEntityNumber() : -1 ) + " party=" + party.size + " seed=" + seed + " prize=cursed tease=" + TOD_SPIN_CURSED_TEASE );
    foreach ( p in party )
    {
        if ( !isdefined( p ) || !isplayer( p ) ) continue;
        p.tod_spin_slots_shown = undefined;
        p LuiNotifyEvent( &"tod_spin_open", 4, seed, prize, tease, luck * 64 + TOD_SPIN_STEPS );
        p PlayLocalSound( "tod_spin_open" );
    }
    if ( isdefined( counter ) )
    {
        tod_perk_scatter::play_sound_at_origin( counter, "tod_shop_spark_" + ( RandomInt( 3 ) + 1 ), 4 );
        level thread fx_burst( TOD_SPIN_SPARK_FX, counter, 0.5 );
    }
    wait TOD_SPIN_LUCK_SND_AT;
    foreach ( p in party ) if ( isdefined( p ) && isplayer( p ) ) p PlayLocalSound( "tod_spin_luck" );
    wait TOD_SPIN_POUR_SECS - TOD_SPIN_LUCK_SND_AT;
    last_tick = -1000;
    for ( k = 1; k <= TOD_SPIN_STEPS; k++ )
    {
        ms = step_ms( k, 0, 1 );   // a plain cadence with the STOPPED SHORT hang on the last step
        tick = ( k > 1 && k <= TOD_SPIN_STEPS - 5 && GetTime() - last_tick >= TOD_SPIN_TICK_MIN_MS );
        foreach ( p in party )
        {
            if ( !isdefined( p ) || !isplayer( p ) ) continue;
            p LuiNotifyEvent( &"tod_spin_step", 2, k, ms );
            if ( k == 1 ) p PlayLocalSound( "tod_spin_start" );
            else if ( k > TOD_SPIN_STEPS - 5 ) p PlayLocalSound( "tod_spin_crawl_" + ( k - ( TOD_SPIN_STEPS - 5 ) ) );
            else if ( tick ) p PlayLocalSound( "tod_spin_tick_" + ( ( k % 3 ) + 1 ) );
        }
        if ( tick ) last_tick = GetTime();
        if ( k == TOD_SPIN_STEPS )
        {
            // STOPPED SHORT on the jackpot: the needle on the seam, the heartbeat, then the fall onto the curse
            wait ( ms - TOD_SPIN_NEAR_HANG_MS - TOD_SPIN_SETTLE_MS ) / 1000.0;
            foreach ( p in party ) if ( isdefined( p ) && isplayer( p ) ) p PlayLocalSound( "tod_pull_beat" );
            wait ( TOD_SPIN_NEAR_HANG_MS + TOD_SPIN_SETTLE_MS ) / 1000.0;
        }
        else wait ms / 1000.0;
    }
    // THE HIT: CURSED (never a slot, never a scrap, never a payout)
    foreach ( p in party )
    {
        if ( !isdefined( p ) || !isplayer( p ) ) continue;
        p LuiNotifyEvent( &"tod_spin_land", 2, prize, TOD_SPIN_CODE_CURSED );
        p PlayLocalSound( "tod_house_cursed" );
    }
    if ( isdefined( counter ) )
    {
        level thread fx_burst( TOD_SPIN_BLAST_FX, counter + ( 0, 0, 20 ), 0.8 );
        tod_perk_scatter::play_sound_at_origin( counter, "tod_thor_clap", 6 );
    }
    log( "HOUSE_ROLL_LAND code=" + TOD_SPIN_CODE_CURSED + " party=" + party.size );
}

function house_roll_end( party )   // PUBLIC: the panel drops on every screen
{
    foreach ( p in party )
    {
        if ( !isdefined( p ) || !isplayer( p ) ) continue;
        p PlayLocalSound( "tod_spin_close" );
        p LuiNotifyEvent( &"tod_spin_end", 1, 0 );
    }
}
