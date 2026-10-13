// =============================================================================
// zm_tod2_cybercity.csc — client entry script (stock template structure).
// =============================================================================

#using scripts\codescripts\struct;
#using scripts\shared\audio_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\exploder_shared;
#using scripts\shared\scene_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#using scripts\zm\_load;
#using scripts\zm\_zm_weapons;

//Perks
#using scripts\zm\_zm_pack_a_punch;
#using scripts\zm\zm_cwpap;   // v13.6 — ALXS CW/BO6 PaP client half (crown machine)
#using scripts\zm\_zm_perk_additionalprimaryweapon;
#using scripts\zm\_zm_perk_doubletap2;
// [tod] v14.16 — Wisp Tea client half, in Deadshot's old slot — MUST match
// the entry .gsc #using (clientfield lockstep).
#using scripts\zm\_zm_perk_wisp_tea;
// [tod] Client half of the stock cherry pipeline (_tod_perk_electric_cherry
// rides its tesla FX) — MUST match the entry .gsc #using or the clientfield
// registration mismatches at load (map 1 pattern).
#using scripts\zm\_zm_perk_electric_cherry;
#using scripts\zm\_zm_perk_juggernaut;
#using scripts\zm\_zm_perk_quick_revive;
#using scripts\zm\_zm_perk_sleight_of_hand;
#using scripts\zm\_zm_perk_staminup;
// [tod] Widow's Wine client half — MUST match the entry .gsc #using.
#using scripts\zm\_zm_perk_widows_wine;

//Powerups
#using scripts\zm\_zm_powerup_double_points;
#using scripts\zm\_zm_powerup_carpenter;
#using scripts\zm\_zm_powerup_fire_sale;
#using scripts\zm\_zm_powerup_free_perk;
#using scripts\zm\_zm_powerup_full_ammo;
#using scripts\zm\_zm_powerup_insta_kill;
#using scripts\zm\_zm_powerup_nuke;
// [tod] Logical's Powerups + our custom drops — MUST match the entry .gsc
// #usings (clientfield lockstep: timewarp/infiniteammo/powerup_admin_gun)
#using scripts\zm\logical\powerups\_zm_powerup_timewarp;
#using scripts\zm\logical\powerups\_zm_powerup_infiniteammo;
#using scripts\zm\zm_tod2_cybercity\_tod_powerups;
#using scripts\zm\zm_tod2_cybercity\_tod_wunderstrahl;   // [tod] THE WUNDERSTRAHL (docs/219): its tray clientfield (REGISTER_SYSTEM self-init)
#using scripts\zm\zm_tod2_cybercity\_tod_lucky;   // THE LUCKY CLOVER's client half: include + add (docs/197)
// [tod] Gift of Death (Xmas Gun) client half — clientfield lockstep with the
// entry .gsc (xmas_gun_proj_stop + zm_xmas_frz)
#using scripts\zm\zm_weap_xmas_gun;

//Traps
#using scripts\zm\_zm_trap_electric;

// Aetherium HUD (Owen-C137 kit — per its README, ABOVE zm_usermap)
#using scripts\zm\_zm_aetherium_hud;

#using scripts\zm\zm_usermap;

// [tod] client modules (clientfield lockstep with the .gsc twins)
#using scripts\zm\zm_tod2_cybercity\_tod_cyber_sword;
#using scripts\zm\zm_tod2_cybercity\_tod_archer;
#using scripts\zm\zm_tod2_cybercity\_tod_class_cards;   // the Invisibility Cloak's look (2026-09-28): visionset_mgr + tod_cloak_fx LOCKSTEP with the .gsc
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;    // THE ABILITY FEEDBACK (docs/203, 2026-10-02): every ability's 1p / 3p halves; clientfield lockstep with the .gsc
#using scripts\zm\zm_tod2_cybercity\_tod_necro_skull;   // THE NECROMANCER (2026-09-26): skull + Burned Out client FX (lockstep with _tod_main)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_lights;
#using scripts\zm\zm_tod2_cybercity\_tod_wunderfizz_machine;
#using scripts\zm\zm_tod2_cybercity\_tod_eye_glow;   // THE HORDE'S EYES (PK04, 2026-10-04): red / gold eye glow instead of stock orange; init() below, client only
#using scripts\zm\zm_tod2_cybercity\_tod_shop;
#using scripts\zm\zm_tod2_cybercity\_tod_sky_ships;   // THE SKY FLEET (docs/192): client-only huge ships flying the sky; no server half, no clientfields
#using scripts\zm\zm_tod2_cybercity\_tod_jump_title;   // THE FIRST JUMP'S CRASH (docs/196 s4): client-only warships / fireball / blazing sign; beats from _tod_jumppad.gsc (util::clientNotify), no clientfields
#using scripts\zm\zm_tod2_cybercity\_tod_war_damage;   // THE WAR DAMAGE PASS (docs/205): client-only war damage models + effects; one world clientfield (the power) from _tod_war_damage.gsc
#using scripts\zm\zm_tod2_cybercity\_tod_war_sky;      // THE WAR DAMAGE PASS (docs/205) phase 2: the war in the sky, client-only (far flashes, tracers, a stricken ship)
#using scripts\zm\zm_tod2_cybercity\_tod_amb;          // THE WORLD AMBIENCE (PK23): client-only wind / far city by altitude, the Undercity + plaza room tones (REGISTER_SYSTEM self-init)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_electric_cherry;   // v13.19 — DEATH PERCEPTION outline callbacks (lineage name, see its header)
#using scripts\zm\zm_tod2_cybercity\_tod_upgrade_ui;
// The Civil Protector companion's stock pack (REGISTER_SYSTEM self-init — the
// #using alone wires it; MUST be present whenever the .gsc half is in the
// fastfile: clientfield lockstep; the installed zm_ai_zod_companion.zpkg names
// it) + the tod boss FX pulse module (the companions' shot / zap pulses).
// RETIRED WHOLE 2026-10-05, BOTH VMs IN ONE BUILD: the Panzer pack (mechz_spiki),
// the Apothicon Fury pack (zm_genesis_apothicon_fury: its client half registered
// "apothicon_fury_spawn_meteor", whose server half went with _tod_reaver) and
// the Keeper's client half (_tod_keeper.csc: the tod_keeper_death /
// tod_keeper_link actor fields, whose server registrations left _tod_keeper.gsc
// the same build).
#using scripts\zm\zm_zod_robot;
#using scripts\zm\zm_tod2_cybercity\_tod_boss_fx;
// 2026-09-26 (Warrior): the GRAVITY SMASH lethal is stock's Gravity Spikes slam
// (_tod_class_kit.gsc #using scripts\zm\_zm_weap_gravityspikes). That script's
// __init__ registers 13 clientfields on the SERVER; without this client half
// nothing drew the slam and the field tables could not match. LOCKSTEP with the
// .gsc #using; the slam FX it names are zoned beside the Warrior blades.
#using scripts\zm\_zm_weap_gravityspikes;

function main()
{
	zm_usermap::main();

	// THE HORDE'S EYES (PK04): zm_usermap::main() just set the stock ORANGE eye glow (level._effect[ "eye_glow" ]);
	// point every zombie's stock eye lane at the horde's red and the golden zombie's gold before any actor lights one.
	tod_eye_glow::init();

	include_weapons();

	// Upgrade-choice LUI (the 4-file contract: GSC #precache lui_menu +
	// OpenLUIMenu, this LuiLoad, the zone rawfile line, the .lua itself).
	LuiLoad( "ui.uieditor.menus.hud.tod_upgrade" );
	LuiLoad( "ui.uieditor.menus.hud.tod_wunderfizz" );
	// Class-draft LUI (same contract; GSC half = _tod_class_select.gsc)
	LuiLoad( "ui.uieditor.menus.hud.tod_class_select" );
	// TELEMETRY PROBE LUI (tools/telemetry_probe; same 4-file contract; removed whole by land.js --remove)
	LuiLoad( "ui.uieditor.menus.hud.tod_telem_probe" );

	util::waitforclient( 0 );

	// ---------------------------------------------------------------------
	// NO OVERRIDE OF character_fire_death_torso HERE — AND THAT IS THE POINT
	// (v16.91, reverting v16.90's override; user: "on this map when i get a
	// nuke i can see the zombies are burned").
	//
	// v16.90 pointed both fire handles at fire/fx_fire_ai_human_torso_loop on
	// the theory that stock's "zombie/fx_fire_torso_zmb" could never draw,
	// because THAT FILE IN THE MOD TOOLS is a 5,092-byte placeholder whose one
	// material is `gfx_debug_missing_fx`. The theory was wrong, and the reason
	// is worth keeping:
	//
	//   A STUB IN share\raw IS A MISSING *SOURCE*, NOT A MISSING *ASSET*.
	//   Treyarch shipped placeholder .efx sources for effects they did not
	//   release, but the real COMPILED effects are in the base-game fastfiles.
	//   An effect your map never zones resolves from those at runtime and
	//   renders perfectly — the nuke burn does, and always has here.
	//   You only inherit the placeholder when YOUR zone packs it, because then
	//   your fastfile supplies the empty version. `zombie/fx_fire_torso_zmb`
	//   is NOT in this map's zone, which is exactly why the nuke burns.
	//
	// So the nuke's fire needs nothing from us. Overriding these handles would
	// have quietly replaced the nuke's own look map-wide with a different fire,
	// which is the opposite of what was asked for.
	//
	// v18.12 — TRAILBLAZER NO LONGER RIDES THIS LANE. It used to increment the
	// same `zm_nuked` field and inherit the nuke fire for free; it now sets
	// `arch_actor_fire_fx` = 2 (BURN_CORPSE) instead, because a trail kill
	// reading as "somebody pulled a Nuke" was the whole complaint. That lane is
	// registered by stock's own archetype_shared autoexec and carries its own
	// FX and burn loop, so it needs nothing from this file either — and, like
	// the nuke's, its effects must NOT be zoned here or we would pack the
	// placeholder over the working stock ones.
	//
	// Do not "fix" a blank effect by swapping the handle until you have checked
	// whether your zone is the thing packing the placeholder over it.
	// ---------------------------------------------------------------------
}

function include_weapons()
{
	zm_weapons::load_weapon_spec_from_table( "gamedata/weapons/zm/zm_levelcommon_weapons.csv", 1 );
}
