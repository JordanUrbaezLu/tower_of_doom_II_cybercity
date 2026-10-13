    /////////////////////////////////////////////////////
   //
  //	         ALXS - CW-BO6 PAP         v1.1.2
 //
/////////////////////////////////////////////////////
//CREDITS//
//PAP model and Anims - Madgaz, Owen C137
//PAP script - RiDD_Alexis31, JoaoSlideCancelo, Prov3ntus, Shidouri, Resxt, CF4_99, Rayjiun, devraw and mod tools servers support and more
//PAP sounds - Owen C137
//
// =============================================================================
// [tod v13.12] DE-SINGULARIZED (user 2026-08-29: "just do it that way now" —
// every Pack-a-Punch machine runs THIS script's proven flow, not a graft of
// it). The original pack drives exactly ONE machine through the literal
// `level.packAPunchModel`; this fork makes the machine a parameter:
//
//   * register_pap_machine( model, trig_org, trig_angles, b_jingle ) — public.
//     The CROWN registers itself in __init__ from the prefab's own struct,
//     byte-faithful to the original bootstrap. The FOUR BREATHER VENDORS
//     register from _tod_powerups::breather_pap_place. Five machines, one
//     code path — whatever the crown does, every machine does.
//   * Every `level.packAPunchModel` became `self` (the functions were already
//     threaded ON the model) or an explicit machine parameter (the
//     player-threaded ones). No behavior changed by the transform.
//   * ONE NETWORK (user: "they all need to act as if they work together so I
//     cant just walk up and double pack from a different machine"):
//     the purchase cooldown is LEVEL-GLOBAL (level.tod_cwpap_cooldown_end) —
//     five stations, one machine's throughput. Double-upgrading is already
//     impossible at the weapon table (an _up form has no further upgrade row),
//     so the shared cooldown is what makes the network FEEL single.
//   * THE CLASS-GUN LANE is woven in (this map's tier-card system requires
//     it): class primaries fail stock's can_upgrade_weapon by design (the
//     twin roster), so the stock branch would deny them with a blank hint.
//     A class primary now buys at 5000 through the same show, latching
//     player.tod_pap_owned — _tod_upgrades::reconcile_twin swaps the _up
//     form within 1s, exactly the proven vendor lane's economics inside the
//     pack's presentation.
//   * The jingle runs on the machines with b_jingle true only (crown +
//     vendors all pass true would mean five overlapping music stings with
//     unknown 2d/3d routing — the crown keeps it, vendors stay quiet except
//     their idle hum; flip the vendor arg in _tod_powerups if wanted).
//   * Per-machine POWER-ON work is STAGGERED 0-1s (user: "started lagging a
//     bit when I turned on power" — the KB's simultaneous-FX-burst rule).
//   * USE_HAND_KNUCKLE stays false: the anim needs weapon
//     "zombie_knuckle_crack", which T7 does not ship and no installed pack
//     declares (see the zone comment). Re-enable together with a sourced
//     knuckle weapon port.
// =============================================================================

// [tod v13.14] HEADER RESTORED TO THE ORIGINAL'S FULL SET. The v13.12 rewrite
// slimmed the #usings and dropped the original's #precache block — losing the
// THREE HINT STRINGS (an unprecached &string kills SetHintString, i.e. every
// machine's prompt) and the aats using that pulls the AAT system in. Faithful
// means the whole header, not just the functions.
#using scripts\codescripts\struct;

#using scripts\shared\array_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;
#using scripts\shared\fx_shared;
#using scripts\shared\trigger_shared;
#using scripts\shared\animation_shared;
#using scripts\shared\aat_shared;
#using scripts\shared\audio_shared;
#using scripts\shared\laststand_shared;   // [tod v17.51] giveWeaponRepacked never raises into last stand

#using scripts\zm\_util;
#using scripts\zm\_zm;
#using scripts\zm\_zm_audio;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_unitrigger;
#using scripts\zm\_zm_weapons;
#using scripts\zm\_zm_perks;

// [tod v13.17] AAT using REMOVED (user 2026-08-29: "its allowing me to double
// pack my guns... adding some elemental part... disable"). This using was the
// ONLY thing registering the AAT system map-wide (verified: no other module
// or zone line touches aats) — without it level.aat_in_use never goes true,
// so none of these five machines can offer the 2500 elemental re-pack (the
// "roof stock PaP" this line used to name does not exist: the hall's ALXS
// prefab is the ONLY PaP prefab in the .map — corrected 2026-09-02). The
// USE_AAT_REPACK define below gates the branches too,
// in case a future module re-registers AATs for its own reasons.
// #using scripts\zm\aats\_zm_aat_blast_furnace;

#using scripts\zm\zm_tod2_cybercity\_tod_classes;   // [tod] is_class_primary — the tier-card lane

#insert scripts\shared\aat_zm.gsh;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#precache("xmodel", "p9_fxanim_zm_gp_pap_xmodel_off");
#precache("xmodel", "p9_fxanim_zm_gp_pap_xmodel");
#precache( "xanim", "xanim_c5969f9b9bb4e89_idle");
#precache( "xanim", "xanim_a79285d6b6f48f4_in_use");
#precache("string", "ZOMBIE_PERK_PACKAPUNCH");
#precache("string", "ZOMBIE_PERK_PACKAPUNCH_AAT");
#precache("string", "ZOMBIE_NEED_POWER");

#define SND_UNSUP_PAPPING          true
#define AAT_FX_COLORS              2
#define USE_HAND_KNUCKLE           false    // [tod v13.9] see the header — needs a knuckle weapon port
#define USE_AAT_REPACK             false    // [tod v13.17] the 2500 elemental re-pack lane — OFF (user order, see the aats using tombstone)
#define TRIGGER_COOLDOWN_TIME      4
#define UPGRADE_FXANIM_TIME        4
// [tod v17.51] a same-asset pack (an additive class's same-asset primary) keeps the gun for a moment — see giveWeaponRepacked.
// v17.53 (user: "4 seconds is way too long. Can we shorten as much as possible
// while it still works"): 1.0 s. The floor is set by what has to be SEEN, not
// by the machine: the take lowers the gun and the engine raises the other
// weapon (~0.5 s); the return then lowers that and raises the gun. Under ~1 s
// the two overlap, the second switch can be eaten mid-raise (camo_regive's
// re-assert catches it, but it reads as a stutter), and the take stops
// registering as a take at all. The machine's own 4 s show runs on
// UPGRADE_FXANIM_TIME regardless.
#define TOD_PAP_TIER_HOLD_SECS     0.5   // v17.53b (user: "What about 500ms?") — the re-assert in camo_regive covers an eaten switch; 1.0 is the fallback if it stutters
// [tod v16.27] THE TRIGGER ORIGIN FLOATS OFF THE FLOOR. This map has paid twice
// for a solid brush sitting on a script trigger's origin — the extraction
// obelisk and the hall crate's clip column both killed their buy outright
// (_tod_finale::spawn_props records both) — and v16.7 gave every breather
// lounge a 1u glowing floor inlay whose EAST SPOKE runs exactly under the
// pap_trig anchor (the generator ends the spoke 44u from the machine; the
// trigger is 56u out). The stub used to sit AT floor level, the stock prefab
// convention, which is fine on a bare floor (the crown, verified) and dead
// under a decal. The unitrigger's own range test is Distance2DSquared (stock
// _zm_unitrigger.gsc:431), so height costs no reach; 8 clears any 1u decal.
// The upgrade stations lift for the same reason (_tod_upgrades,
// TOD_STATION_TRIG_LIFT) — that one is the crown altar's actual bug.
#define TOD_PAP_TRIG_LIFT          8
// [tod PK02 2026-10-04] THE STING AND THE JINGLE PLAY. Their cw_ aliases were
// never defined anywhere (docs/43 B2: the loaded zm_cwpap_sound.csv names the
// same CW wavs WITHOUT the prefix, and the unprefixed names also exist in
// stock, so the prefix stays and tod_ui.csv now defines both). With the jingle
// audible for the first time, pap_jingle_logic holds it while the Fall's
// alarm siren is up (a music-box tune under a nuclear siren reads wrong),
// under the Fall's intro track and the teddy-bear song, through a world
// pause, and for this long after a pack's sting (it used to StopSound a sting
// the player had just paid for). The class-gun lane now stops the jingle
// before its sting, like the other two lanes always did.
#define TOD_CWPAP_STING_HOLD_MS    9500   // mus_packapunch_sting.wav is 8.89 s

#using_animtree("cwpapanimtree");

#namespace zm_cwpap;

REGISTER_SYSTEM_EX( "zm_cwpap", &__init__, undefined, undefined )

function __init__()
{
    clientfield::register( "scriptmover", "t9_pap_FX_idle", VERSION_SHIP, 1, "int" );
    clientfield::register( "scriptmover", "t9_pap_FX_inuse", VERSION_SHIP, 2, "int" );
    clientfield::register( "scriptmover", "t9_pap_FX_inuse_aat", VERSION_SHIP, 3, "int" );
    clientfield::register( "scriptmover", "t9_pap_FX_aat_bf", VERSION_SHIP, 3, "int" );
    clientfield::register( "scriptmover", "t9_pap_FX_aat_dw", VERSION_SHIP, 3, "int" );
    clientfield::register( "scriptmover", "t9_pap_FX_aat_fw", VERSION_SHIP, 3, "int" );
    clientfield::register( "scriptmover", "t9_pap_FX_aat_tw", VERSION_SHIP, 3, "int" );
    clientfield::register( "scriptmover", "t9_pap_FX_aat_t", VERSION_SHIP, 3, "int" );
    level.snd_unsup_pap = SND_UNSUP_PAPPING;
    level.use_papknuckles = USE_HAND_KNUCKLE;
    level.tod_cwpap_cooldown_end = 0;   // [tod] ONE cooldown for the whole network

    // THE CROWN — the pack's original machine, registered through the same
    // public lane the vendors use. [tod v13.15] MOVED TO THE LATE LANE: the
    // v13.12 direct call here ran at REGISTER_SYSTEM_EX time and guarded with
    // isdefined — if the prefab's entities are not findable that early, the
    // guard SKIPS SILENTLY and the crown simply never exists (the original
    // pack had no guard, so it never taught us whether system-time GetEnt on
    // prefab ents is safe). The retry lane below is the crown_pap_clips
    // (_tod_powerups v13.9) proven pattern, and it names its failure on
    // screen in dev instead of swallowing it.
    level thread crown_register_late();
}

function crown_register_late()
{
    level endon( "end_game" );
    while ( !( level flag::exists( "initial_blackscreen_passed" ) ) )
        wait 0.05;
    level flag::wait_till( "initial_blackscreen_passed" );
    for ( i = 0; i < 40; i++ )
    {
        crown_struct = struct::get("pap_trigger_struct", "targetname");
        crown_model  = GetEnt("pack_a_punch_model", "targetname");
        if ( isdefined( crown_model ) && isdefined( crown_struct ) )
        {
            register_pap_machine( crown_model, crown_struct.origin, crown_struct.angles, true );
            return;
        }
        wait 0.25;
    }
    if ( IS_TRUE( level.tod_dev ) )
        IPrintLnBold( "[PAP] CROWN NOT FOUND — prefab ents missing after 10s" );
}

// [tod v13.12] PUBLIC — one call makes any script_model a full Pack-a-Punch
// station on this script's flow. Late registration is fine (the vendors
// register at gameplay init, after clients connect).
function register_pap_machine( model, trig_org, trig_angles, b_jingle )
{
    if ( !isdefined( model ) )
        return;
    if ( !isdefined( b_jingle ) )
        b_jingle = false;
    model.tod_cwpap_jingle = b_jingle;
    model.tod_cwpap_crown = b_jingle;   // [tod 2026-09-25] only the crown registers with the jingle

    model thread setup_unitrigger( trig_org, trig_angles );
    model thread papIdleSound();
    model thread machine_power_watch();
}

// Per-machine power watch — the original monitorPower, per machine, with the
// [tod] anti-burst stagger (five machines flipping in the same frame was the
// user's power-on lag; the KB documents the pattern).
function machine_power_watch()
{
    // [tod v13.13 — THE "MAP WONT START" BOOT FIX, 2026-08-29 ~3:25am]
    // Two bugs in one line pair, found from the user's terminal-error screen
    // ("cannot cast undefined to bool, flag_shared.gsc:0"):
    //  1. The CROWN registers from __init__ (system-registration time), so
    //     this thread ran BEFORE stock creates ANY flag — flag::wait_till on
    //     an unregistered flag is the exact cast error on the screen. The
    //     vendors register at gameplay init and never tripped it, which is
    //     why the de-sing booted in no earlier test: the crown was the only
    //     __init__-lane machine and this build was its first boot.
    //  2. "all_players_spawned" DOES NOT EXIST in this map at all — stock's
    //     only mention is a commented-out line (_zm.gsc:6849). Even guarded,
    //     the wait would never return and NO machine would ever power on.
    // Fix: the exists-loop + blackscreen wait (the _tod_ammo_crate precedent,
    // required for any pre-gameplay-init thread), then "power_on", which is
    // registered by stock zm_power long before the blackscreen passes.
    while ( !( level flag::exists( "initial_blackscreen_passed" ) ) )
        wait 0.1;
    level flag::wait_till( "initial_blackscreen_passed" );
    self wait_machine_power();
    wait RandomFloatRange( 0.05, 1.0 );
    if ( !isdefined( self ) )
        return;
    self thread powerOnAnimation();
    self thread monitorPackAPunch();
}

// [tod 2026-10-04, map 1's bug review F12, docs/208] What the machine will NOT pack even
// though the weapons CSV pairs it with an `_upgraded` form. Stock's own
// _zm_pack_a_punch::can_pack_weapon refuses `weapon.isriotshield` outright; this port had no
// such test, so a held RIOT SHIELD (the Breacher's zod_riotshield, paired with
// zod_riotshield_upgraded in zm_levelcommon_weapons.csv) showed "Pack-a-Punch 5000", took
// the points, and _tod_riotshield's reconcile swapped the upgraded shield straight back.
// Gates the prompt, the charge and the give.
function tod_pap_refuses(weapon)
{
    return ( isdefined( weapon ) && IS_TRUE( weapon.isriotshield ) );
}

function monitorPackAPunch()
{
    if ( IS_TRUE( self.tod_cwpap_jingle ) )
        self thread pap_jingle_logic();

    for(;;)
    {
        self waittill( "trigger_activated", player );

        if( GetTime() > level.tod_cwpap_cooldown_end && !IS_TRUE( player.tod_tier_busy ) && !IS_TRUE( player.tod_swap_busy ) ) // network-global throughput and player inventory lock
        {
            weapon = player GetCurrentWeapon();

            // [tod] CLASS-GUN LANE — class primaries fail stock can_upgrade
            // by roster design; they buy here at the same price through the
            // same show, latching the flag the tier-card system reads.
            // reconcile_twin (_tod_upgrades) swaps the _up form within 1s.
            // [tod v13.14] is_class_primary is (player, weapon) — the v13.12
            // one-arg call returned false silently and killed the whole lane.
            if ( tod_classes::is_class_primary( player, weapon ) && tod_classes::pap_tier( player, weapon ) == 0 )
            {
                if ( player zm_score::can_player_purchase( 5000 ) && zm_utility::is_player_valid( player ) )
                {
                    player zm_score::minus_to_player_score( 5000 );
                    self PlaySoundToPlayer("zmb_cha_ching", player);
                    tod_classes::pap_first_grant( player, weapon );
                    if ( tod_classes::pap_independent( player, weapon ) )
                        player thread giveWeaponRepacked( weapon );
                    self thread papFXIdle(0);
                    self thread papFXInUse(1);
                    self UseAnimTree(#animtree);
                    self AnimScripted( "optionalNotify", self.origin , self.angles, %xanim_a79285d6b6f48f4_in_use);
                    self thread stopUpgradeAnimationAfterTime(UPGRADE_FXANIM_TIME);
                    self thread papInUseSound();
                    self thread papLeverSound();
                    self StopSound( "cw_mus_perks_packa_sting" );
                    self StopSound( "cw_mus_perks_packa_jingle" );   // [tod PK02] the class-gun lane never stopped the jingle
                    wait 0.05;
                    self PlaySound( "cw_mus_perks_packa_sting" );
                    self.tod_cwpap_sting_ms = GetTime();   // [tod PK02] the jingle waits out the sting
                    player zm_audio::create_and_play_dialog( "weapon_pickup", "upgrade" );
                }
                else
                {
                    self PlaySoundToPlayer("zmb_perks_packa_deny", player);
                    player zm_audio::create_and_play_dialog( "general", "outofmoney");
                }
            }
            else if ( zm_weapons::is_weapon_upgraded( weapon ) || tod_weapon_is_packed( player, weapon ) )   // [tod v16.27] the CSV-blind packed forms deny here too, not via can_upgrade
            {
                if (USE_AAT_REPACK && zm_weapons::weapon_supports_aat(weapon) && ( isdefined( level.aat_in_use ) && level.aat_in_use ) )
                {
                    if(player hasEnoughMoney(2500, self) && zm_utility::is_player_valid( player ) )
                    {
                        player thread giveWeaponAAT( self );
                        self thread papFXIdle(0);
                        self UseAnimTree(#animtree);
                        self AnimScripted( "optionalNotify", self.origin , self.angles, %xanim_a79285d6b6f48f4_in_use);
                        self thread stopUpgradeAnimationAfterTime(UPGRADE_FXANIM_TIME);
                        self thread papInUseAATSound();
                        self thread papLeverSound();
                        self StopSound( "cw_mus_perks_packa_sting" );
                        self StopSound( "cw_mus_perks_packa_jingle" );
                        wait 0.05;
                        self PlaySound( "cw_mus_perks_packa_sting" );
                        self.tod_cwpap_sting_ms = GetTime();   // [tod PK02] the jingle waits out the sting
                        player zm_audio::create_and_play_dialog( "weapon_pickup", "upgrade" );
                    }
                }
                else
                {
                    if(level.snd_unsup_pap)
                    {
                        self PlaySoundToPlayer("zmb_perks_packa_deny", player);
                    }
                    player zm_audio::create_and_play_dialog( "general", "oh_shit" );
                }
            }
            else
            {
                if (zm_weapons::can_upgrade_weapon(weapon) && !tod_pap_refuses(weapon))
                {
                    if(player hasEnoughMoney(5000, self) && zm_utility::is_player_valid( player ) )
                    {
                        player thread giveWeaponUpgraded();
                        self thread papFXIdle(0);
                        self thread papFXInUse(1);
                        self UseAnimTree(#animtree);
                        self AnimScripted( "optionalNotify", self.origin , self.angles, %xanim_a79285d6b6f48f4_in_use);
                        self thread stopUpgradeAnimationAfterTime(UPGRADE_FXANIM_TIME);
                        self thread papInUseSound();
                        self thread papLeverSound();
                        self StopSound( "cw_mus_perks_packa_sting" );
                        self StopSound( "cw_mus_perks_packa_jingle" );
                        wait 0.05;
                        self PlaySound( "cw_mus_perks_packa_sting" );
                        self.tod_cwpap_sting_ms = GetTime();   // [tod PK02] the jingle waits out the sting
                        if(level.use_papknuckles)
                        {
                            wait 2.2;
                            player zm_audio::create_and_play_dialog( "weapon_pickup", "upgrade" );
                        }
                        else
                        {
                            player zm_audio::create_and_play_dialog( "weapon_pickup", "upgrade" );
                        }
                    }
                }
                else
                {
                    if(level.snd_unsup_pap)
                    {
                        self PlaySoundToPlayer("zmb_perks_packa_deny", player);
                    }
                    player zm_audio::create_and_play_dialog( "general", "oh_shit" );
                }
            }

            level.tod_cwpap_cooldown_end = GetTime() + ( TRIGGER_COOLDOWN_TIME * 1000 );
        }
    }
}

function papFXIdle(reproduce)
{
    self clientfield::set( "t9_pap_FX_idle", reproduce );
}

function papFXInUse(reproduce)
{
    self clientfield::set( "t9_pap_FX_inuse", reproduce );
}

function papFXInUseAAT(reproduce)
{
    self clientfield::set( "t9_pap_FX_inuse_aat", reproduce );
}

function powerOnAnimation()
{
    self SetModel("p9_fxanim_zm_gp_pap_xmodel");
    self thread playIdleAnimation();
}

// Animación de espera del Pack-a-Punch
function playIdleAnimation()
{
    self UseAnimTree(#animtree);
    self AnimScripted( "", self.origin , self.angles, %xanim_c5969f9b9bb4e89_idle);
    self thread papFXIdle(1);
}

// Detener animación de mejora después de un tiempo
function stopUpgradeAnimationAfterTime(duration)
{
    wait(duration);
    self thread papFXInUse(0);
    self thread papFXInUseAAT(0);
    self thread playIdleAnimation();
}

// Verificar si el jugador tiene suficiente dinero (y COBRAR — the original
// charges inside the check; [tod] the machine rides in as a param now)
function hasEnoughMoney(amount, machine)
{
    weapon = self GetCurrentWeapon();
    player = self;
    if(player zm_score::can_player_purchase(amount))
    {
        if (zm_weapons::is_weapon_upgraded(weapon))
        {
            if (zm_weapons::weapon_supports_aat(weapon) && ( isdefined( level.aat_in_use ) && level.aat_in_use ) )
            {
                if (amount >= 2500)
                {
                    player zm_score::minus_to_player_score(amount);
                    machine PlaySoundToPlayer("zmb_cha_ching", self);
                }
            }
        }
        else
        {
            if (zm_weapons::can_upgrade_weapon(weapon) && !tod_pap_refuses(weapon))
            {
                if (amount >= 5000)
                {
                    player zm_score::minus_to_player_score(amount);
                    machine PlaySoundToPlayer("zmb_cha_ching", self);
                }
            }
        }
        return true;
    }
    else
    {
        machine PlaySoundToPlayer("zmb_perks_packa_deny", self);
        player zm_audio::create_and_play_dialog( "general", "outofmoney");
        return false;
    }
}

function giveWeaponUpgraded()
{
    weapon = self GetCurrentWeapon();
    self takeWeapon(weapon);
    upgrade_weapon = zm_weapons::get_upgrade_weapon(weapon, false);
    if(level.use_papknuckles)
    {
        self DisableWeaponCycling();
        hands = GetWeapon("zombie_knuckle_crack");
        self GiveWeapon(hands);
        self SwitchToWeapon(hands);
        wait(2.2);
        self takeWeapon(hands);
        self EnableWeaponCycling();
    }
    self zm_weapons::weapon_give(upgrade_weapon, true, false, true, true);
    // [tod v17.39] THE CAMO IS STAMPED HERE, AT THE SOURCE. weapon_give hands
    // the packed form over with stock's camo index (42 — a row this map's
    // four-slot tables do not have; every stock camo material is a name-only
    // stub here anyway, see tools/gen_tod_camo.js). Options are per-give and
    // the only give that changes them on an owned asset is take -> give, so
    // the gun is re-dressed immediately, ammo preserved, and raised. The
    // watcher in _tod_classes is a backstop only from this build on.
    self tod_classes::camo_regive( upgrade_weapon, true );
    self switchToWeapon(upgrade_Weapon);
}

// [tod v17.39] THE SAME-ASSET PACK — a class primary whose packed form is the
// asset already held (tod_classes::pap_independent). Same shape as the
// 5,000 buy above — take at the lever, hand back after the show — with ONE
// difference: the asset does not change, so only the re-give can carry the
// packed camo (weapon options are per-give). Taking it at the machine, where the
// player has just pressed USE, is the state the 5,000 buy has used for months;
// weapon_give on a weapon NOT held runs stock's full path (melee slot, fallback
// take, purchase notify), exactly as the first pack did.
//
// [tod v17.51] THE MACHINE KEEPS THE GUN FOR ITS SHOW (user 2026-09-04). A
// same-asset take -> give in one frame plays nothing, so the pack looked inert
// even once the camo changed. Now the take lands at the lever and the give
// lands TOD_PAP_TIER_HOLD_SECS later, so the gun comes back — re-dressed in
// its packed camo — with a real raise. During the window the
// player holds their other weapon, exactly as at every stock Pack-a-Punch.
// tod_tier_busy holds the class-gun watchdog off (it re-gives a missing class
// gun after 3 s — one second SHORTER than the show) and reconcile with it;
// cleared on EVERY exit. A player who goes down mid-show still gets the gun
// back (never raised into last stand — the engine owns the weapon there).
function giveWeaponRepacked( weapon )
{
    self endon( "disconnect" );
    level endon( "end_game" );
    if ( !isdefined( weapon ) || weapon == level.weaponNone || !( self HasWeapon( weapon ) ) )
        return;
    self.tod_tier_busy = true;
    self takeWeapon( weapon );
    if(level.use_papknuckles)
    {
        self DisableWeaponCycling();
        hands = GetWeapon("zombie_knuckle_crack");
        self GiveWeapon(hands);
        self SwitchToWeapon(hands);
        wait(2.2);
        self takeWeapon(hands);
        self EnableWeaponCycling();
    }
    else
    {
        wait TOD_PAP_TIER_HOLD_SECS;
    }
    self zm_weapons::weapon_give( weapon, true, false, true, true );   // full ammo — every Pack-a-Punch hands back a topped-up gun
    if ( self laststand::player_is_in_laststand() )
    {
        self tod_classes::camo_regive( weapon, false );   // dressed, holstered; the engine owns the pistol
        self.tod_tier_busy = undefined;
        return;
    }
    self tod_classes::camo_regive( weapon, true );
    self switchToWeapon( weapon );
    self.tod_tier_busy = undefined;
}

function giveWeaponAAT( machine ) //self = who is upgrading
{
    weapon = self GetCurrentWeapon();
    self thread aat::acquire( weapon );
    if(AAT_FX_COLORS == 1)
    {
        machine thread papFXInUseAAT(1);
    }
    if(AAT_FX_COLORS == 2)
    {
        self thread watchAAT(weapon, machine);
    }
}

function PapPromptAndVisibility(player)
{
    weapon = player GetCurrentWeapon();

    m_power = self.stub.related_parent;   // [tod 2026-09-25] the crown's machine is live from the alarm
    if ( isdefined( m_power ) && m_power machine_powered() )
    {
        // [tod] class primaries: stock can_upgrade rejects the twin roster by
        // design, which used to blank this hint — the class lane prices here.
        if ( tod_classes::is_class_primary( player, weapon ) && tod_classes::pap_tier( player, weapon ) == 0 )
        {
            self SetHintString( &"ZOMBIE_PERK_PACKAPUNCH", 5000 );
        }
        else if ( zm_weapons::is_weapon_upgraded( weapon ) || tod_weapon_is_packed( player, weapon ) )
        {
            if (USE_AAT_REPACK && zm_weapons::weapon_supports_aat(weapon))
            {
                self SetHintString( &"ZOMBIE_PERK_PACKAPUNCH_AAT", 2500 );
            }
            else
            {
                // [tod v16.27] was SetHintString( "" ) — "packed is packed". A
                // blank hint is the double-pack confusion; see tod_set_packed_hint.
                self tod_set_packed_hint( player, weapon );
            }
        }
        else
        {
            if (zm_weapons::can_upgrade_weapon(weapon) && !tod_pap_refuses(weapon))
            {
                self SetHintString( &"ZOMBIE_PERK_PACKAPUNCH", 5000 );
            }
            else
            {
                self SetHintString("");
            }
        }
    }
    else
    {
        self SetHintString( &"ZOMBIE_NEED_POWER");
    }

    return true;
}

// =============================================================================
// [tod v16.27] THE PACKED STATES — real copy instead of a blank hint.
//
// WHAT WAS WRONG (user 2026-09-02: "Many people get confused cause it still
// says [the buy prompt] when you try to double pap"). Every packed weapon in
// hand set SetHintString( "" ), and the Aetherium router IGNORED a blank hint
// (ZMCursorHintNew.lua only re-evaluated its state on non-empty text — fixed
// alongside this), so the card that was up last — "Pack-a-Punch / Upgrade
// your weapon / 5000 / Hold F To Upgrade", i.e. the prompt you had just bought
// through — simply stayed on screen. Hold F again: deny sound, no explanation.
// That is the double-pack confusion, and it is worst right after a purchase,
// when the packed gun is the one in your hands.
//
// NOW: a packed weapon in hand draws the DEFAULT card as a STATUS line (no
// button token, so PromptDefault hides the footer — nothing to press):
//     ALREADY PACKED
//     upgrade at the Heavenly Gift Altar
//     sidearm can still be packed        (only while that is true)
// The sidearm (or the class gun, when the packed thing in hand is the sidearm)
// still buys through the stock lane exactly as before — this changes only what
// the machine SAYS when it has nothing to sell you.
//
// THREE distinct strings, all constant. tools/lint_tod_hints.js counts this
// file since v16.27 (it was the lint's declared blind spot; this is the first
// authored copy in it). "already packed" is in TOD_NOUNS, so the router claims
// the line by name before isPAPHint can see "upgrade"/"pack" in it, and the
// detail deliberately never says "weapon" (upgrade+weapon = the PaP card,
// which never reads the text). A hyphen or slash may appear ONLY as the " - "
// and " / " separators — PromptDefault splits on the first of each. Detail
// lines are kept to ~30 characters: the card's detail box is 146px wide.
//
// PACKED-NESS IS A NAME TEST, NOT is_weapon_upgraded ALONE. Stock's
// is_weapon_upgraded reads level.zombie_weapons_upgraded, which the CSV rows
// for the Enfield / knife / Leviathan (and three sidearms) never populate —
// the weapons-CSV `_zm` suffix mismatch — so a packed Enfield in hand fell
// through to can_upgrade_weapon (false for every twin) and blanked too. The
// class primary answers by tod_pap_owned (the tier system's own latch, set the
// moment the buy lands and before reconcile_twin swaps the form) or by the
// `_up` substring; a class sidearm by the same `_up` test
// _tod_classes::pap_secondary uses. Nothing else in this map packs.
// =============================================================================

function tod_weapon_is_packed( player, weapon )
{
    if ( !isdefined( weapon ) || weapon == level.weaponNone || !isdefined( weapon.name ) )
        return false;
    if ( tod_classes::is_class_primary( player, weapon ) )
        return tod_classes::pap_tier( player, weapon ) > 0;
    if ( zm_weapons::is_weapon_upgraded( weapon ) )
        return true;
    return ( tod_classes::is_class_secondary( player, weapon ) && IsSubStr( weapon.name, "_up" ) );
}

// Is there an UN-packed class sidearm in the inventory that the stock lane
// would sell an upgrade for? Drives the "sidearm can still be packed" line.
function tod_sidearm_packable( player )
{
    weapons = player GetWeaponsListPrimaries();
    foreach ( w in weapons )
    {
        if ( !isdefined( w ) || !isdefined( w.name ) )
            continue;
        if ( !tod_classes::is_class_secondary( player, w ) )
            continue;
        if ( IsSubStr( w.name, "_up" ) || zm_utility::is_offhand_weapon( w ) )
            continue;
        return zm_weapons::can_upgrade_weapon( w );
    }
    return false;
}

// Is the class primary still un-packed? The mirror line, shown when the packed
// thing in hand is the sidearm.
function tod_primary_packable( player )
{
    weapons = player GetWeaponsListPrimaries();
    foreach ( w in weapons )
    {
        if ( !isdefined( w ) || !isdefined( w.name ) )
            continue;
        if ( tod_classes::is_class_primary( player, w ) && tod_classes::pap_tier( player, w ) == 0 )
            return true;
    }
    return false;
}

// self = the player's own unitrigger. Each literal is handed to SetHintString
// DIRECTLY rather than returned through a helper that takes arguments, because
// that is the shape tools/lint_tod_hints.js can count — keep it that way.
function tod_set_packed_hint( player, weapon )
{
    if ( tod_classes::is_class_primary( player, weapon ) )
    {
        if ( tod_sidearm_packable( player ) )
            self SetHintString( "^1ALREADY PACKED^7 - upgrade at the Heavenly Gift Altar / sidearm can still be packed" );
        else
            self SetHintString( "^1ALREADY PACKED^7 - upgrade at the Heavenly Gift Altar" );
        return;
    }
    if ( tod_primary_packable( player ) )
        self SetHintString( "^1ALREADY PACKED^7 - upgrade at the Heavenly Gift Altar / class weapon can still be packed" );   // W3E 2026-10-05: WEAPON, not gun (user)
    else
        self SetHintString( "^1ALREADY PACKED^7 - upgrade at the Heavenly Gift Altar" );
}

function papInUseSound()
{
    self PlaySound("alxs_cwpap_inuse");
}

function papInUseAATSound()
{
    self PlaySound("alxs_cwpap_inuse_aat");
}

// [tod 2026-09-25] THE CROWN'S PaP WAKES WITH THE ALARM (user: "when you turn
// on that power in the crown, pack a punch should be turned on as well. So you
// have a chance to make enough money to pack a punch your gun ... depending on
// if you want to stay that long"). _tod_fall's flood() sets
// level.tod_crown_pap_live at the alarm pull; every OTHER machine still waits
// for the real power switch.
function machine_powered()   // self = the machine model
{
    if ( level flag::exists( "power_on" ) && level flag::get( "power_on" ) )
        return true;
    return IS_TRUE( self.tod_cwpap_crown ) && IS_TRUE( level.tod_crown_pap_live );
}

function wait_machine_power()   // self = the machine model
{
    if ( !IS_TRUE( self.tod_cwpap_crown ) )
    {
        level flag::wait_till( "power_on" );
        return;
    }
    while ( isdefined( self ) && !self machine_powered() )
        wait 0.25;
}

function papIdleSound()
{
    if ( IS_TRUE( self.tod_cwpap_crown ) )
        self wait_machine_power();   // the crown: the alarm or the power
    else
        level waittill("power_on");   // every vendor: unchanged
    if ( !isdefined( self ) )
        return;
    self PlaySound("alxs_cwpap_appear");
    wait 1;
    if ( isdefined( self ) )
        self PlayLoopSound("alxs_cwpap_idle_lp");
}

function papLeverSound()
{
    self PlaySound("alxs_cwpap_lever_down");
    wait 1.82;
    if ( isdefined( self ) )
        self PlaySound("alxs_cwpap_lever_up");
}

function watchAAT(weapon, machine)
{
    keys = getarraykeys(level.aat);
    if(self.aat[weapon] == "zm_aat_blast_furnace")
    {
        machine thread papFXInUseAAT(2);
    }
    if(self.aat[weapon] == "zm_aat_dead_wire")
    {
        machine thread papFXInUseAAT(3);
    }
    if(self.aat[weapon] == "zm_aat_fire_works")
    {
        machine thread papFXInUseAAT(4);
    }
    if(self.aat[weapon] == "zm_aat_thunder_wall")
    {
        machine thread papFXInUseAAT(5);
    }
    if(self.aat[weapon] == "zm_aat_turned")
    {
        machine thread papFXInUseAAT(6);
    }
}

function pap_jingle_logic()
{
    wait RandomIntRange( 10, 60 );
    plays = 0;
    for( ;; )
    {
        // [tod PK02] hold the jingle under the alarm siren, the intro / teddy-bear music, a world pause or a fresh sting (TOD_CWPAP_STING_HOLD_MS)
        held = self jingle_hold_reason();
        if ( held != "" )
        {
            jingle_log( "HOLD reason=" + held );
            while ( self jingle_hold_reason() != "" )
                wait 1;
        }
        self StopSound( "cw_mus_perks_packa_sting" );
        wait 0.05;
        self PlaySound( "cw_mus_perks_packa_jingle" );
        plays++;
        jingle_log( "PLAY count=" + plays + " length_ms=" + SoundGetPlaybackTime( "cw_mus_perks_packa_jingle" ) + " origin=" + self.origin );
        wait ( SoundGetPlaybackTime( "cw_mus_perks_packa_jingle" ) * .001 ) + RandomIntRange( 30, 120 );
    }
}

// [tod PK02] "" = the jingle may start now (self = the machine model).
function jingle_hold_reason()
{
    if ( IS_TRUE( level.tod_fall_siren_on ) )
        return "alarm_siren";
    if ( IS_TRUE( level.tod_upgrade_pause ) )
        return "world_pause";
    // the Fall's intro track and the teddy-bear song are never sung over (the user's "they should never overlap" /
    // "NOTHING overtakes it"); _tod_atmosphere owns both states
    if ( isdefined( level.tod_music_cur ) && level.tod_music_cur == "tod_fall_intro" )
        return "intro_music";
    if ( IS_TRUE( level.tod_music_ee ) )
        return "teddy_song";
    if ( isdefined( self.tod_cwpap_sting_ms ) && GetTime() - self.tod_cwpap_sting_ms < TOD_CWPAP_STING_HOLD_MS )
        return "sting";
    return "";
}

// [tod PK02] dev / diag only: [TOD_PAP_AUDIO] HOLD reason= / PLAY count= length_ms= (length_ms 0 = the alias is not in the bank).
function jingle_log( msg )
{
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
        return;
    line = "[TOD_PAP_AUDIO] ms=" + GetTime() + " " + msg;
    /#
    PrintLn( line );
    #/
}

function setup_unitrigger( trig_org, trig_angles )
{
    unitrigger_pap = SpawnStruct();
    unitrigger_pap.origin = trig_org + ( 0, 0, TOD_PAP_TRIG_LIFT );   // [tod v16.27] off the floor decals — see the define
    unitrigger_pap.angles = trig_angles;
    unitrigger_pap.script_unitrigger_type = "unitrigger_box_use";
    unitrigger_pap.cursor_hint = "HINT_NOICON";
    unitrigger_pap.script_width = 40;
    unitrigger_pap.script_height = 50;
    unitrigger_pap.script_length = 40;
    unitrigger_pap.related_parent = self;
    unitrigger_pap.inactive_reassess_time = 1;
    zm_unitrigger::unitrigger_force_per_player_triggers(unitrigger_pap, true);
    unitrigger_pap.prompt_and_visibility_func = &PapPromptAndVisibility;
    zm_unitrigger::register_static_unitrigger( unitrigger_pap, &zm_unitrigger::unitrigger_logic );
}
