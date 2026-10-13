// Default Hellbound Mangler: original body, skin, six clips, sounds and cannon.
// Cybercity owns round delivery, target/frontier checks and killer rewards.
// No donor rare variants, class-path player slows or continuous replacement.
#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_spawner;
#using scripts\zm\zm_tod2_cybercity\_tod_bosses;
#using scripts\zm\zm_tod2_cybercity\_tod_bo6_audio;
#using scripts\zm\zm_tod2_cybercity\_tod_doppelghast;
#using scripts\zm\zm_tod2_cybercity\_tod_luck;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;
#using scripts\zm\zm_tod2_cybercity\_tod_elite_fx;   // PK26: the death break-up (mangler_burst)
#insert scripts\shared\shared.gsh;
#using_animtree( "generic" );
#namespace tod_mangler;
#precache( "model", "hb_bo6_mangler" );
#precache( "fx", "dlc3/stalingrad/fx_raz_mc_charge" );
#precache( "fx", "dlc3/stalingrad/fx_raz_mc_muz_flash" );
#precache( "fx", "dlc3/stalingrad/fx_raz_mc_shockwave_projectile" );
#precache( "fx", "dlc3/stalingrad/fx_raz_mc_shockwave_projectile_impact" );
#precache( "fx", "hb/mangler/fx_hb_mangler_eyes" );
#precache( "fx", "hb/mangler/fx_hb_mangler_cannon_idle" );
#precache( "fx", "hb/mangler/fx_hb_mangler_projectile" );

#define TOD_MANGLER_CANNON_RATE 2.0
// THE CANNON MORE OFTEN (user 2026-10-05: "manglers dont shoot their blast enough"). The cannon waited 5 s after
// spawning and 5 s after every shot, and only fired at a player inside 800 u in plain sight: one blast every
// ~6.6 s at best (the 1.02 s windup + 0.53 s recovery at TOD_MANGLER_CANNON_RATE). Now 2.5 s / 2.5 s and 1100 u:
// one every ~4 s, from farther off. Melee (inside 90 u) and the 25-damage tracking blast are unchanged.
#define TOD_MANGLER_CANNON_FIRST_MS 2500   // ms after the attack loop starts before the first blast (was 5000)
#define TOD_MANGLER_CANNON_GAP_MS   2500   // ms from one blast's recovery to the next windup (was 5000)
#define TOD_MANGLER_CANNON_RANGE    1100   // u: a target farther than this is not shot at (was 800)
#define TOD_MANGLER_TELL_SECS   1.2
#define TOD_HUNT_RECHECK_MS     3000
// THE MANGLER'S FOOTFALLS (PK02, 2026-10-04: it "walks and runs in total
// silence"). Its run clip (BO2 Brutus, retargeted) carries six bare 'footstep'
// notes and its aitype's footstepTable is empty, so the engine plays nothing for
// them. step_watch reads the run clip's own phase (GetAnimTime: the stock human
// locomotion / Fury mocomp lane) and lands the BO6 heavy step on each note's
// time, so a footfall stays on the foot at any playback rate (the Keeper's soul
// line, the haven's 0.67, an EMP slow). A pause, a stun or an attack leaves the
// clip still and nothing fires; a poll that did not move the body fires nothing.
#define TOD_MANGLER_STEP_POLL      0.05
#define TOD_MANGLER_STEP_MIN_MOVE  1.5    // units per poll (30 u/s): below it the body is standing, whatever the clip says
#define TOD_MANGLER_RUN_FRAMES     67.0   // hb_mangler_run.XANIM_EXPORT: 68 frames = 67 intervals (the fallback's denominator)
#define TOD_MANGLER_STEP_MAX_SPAN  0.12   // a poll advances the 2.23 s cycle ~0.022 at 1x (0.12 = a 0.27 s server hitch); more is a clip restart, not a stride
// THE MANGLER'S DEATH (PK26, 2026-10-05: it "just blinks out of existence"). hb_mangler_death is 66
// frames at 30 fps (2.2 s); measured on its XANIM_EXPORT, the torso is down by frame ~27 and the
// cannon arm hits the floor at frames 48-54. Its BO6 ground impact lands on the arm's fall, the
// break-up (tod_elite_fx::mangler_burst: sparks, steam, scrap, smoke, a light) + the BO6 death impact
// at the clip's end, and the body hides under the burst's flash instead of vanishing.
#define TOD_MANGLER_GROUND_SECS    1.7    // frame 51: the cannon arm's fall
#define TOD_MANGLER_BURST_SECS     2.2    // frame 66: the clip's end
#define TOD_MANGLER_HIDE_SECS      0.1    // the body hides under the flash
#define TOD_MANGLER_GONE_SECS      0.6    // the hidden actor is deleted this long after
#define TOD_MANGLER_GROUND_ALIAS   "hb_bo6_fly_ai_mangler_death_ground_imp"   // sound/aliases/tod_elite_fx.csv (6 takes)
#define TOD_MANGLER_IMPACT_ALIAS   "hb_bo6_dst_ai_mangler_death_impact"       // sound/aliases/tod_elite_fx.csv (4.2 s break-up)
function configure_variant( actor )
{
    actor.tod_mangler_black = false;
    actor.tod_mangler_color = "normal";
    actor.tod_mangler_variant = "normal";
    actor.tod_mangler_speed = 1;
    actor.tod_mangler_hp_zombies = 5;
    actor.tod_mangler_cannon_rate = TOD_MANGLER_CANNON_RATE;
}

function cannon_fx( color, stage )
{
    if ( stage == "idle" ) return "hb/mangler/fx_hb_mangler_cannon_idle";
    if ( stage == "projectile" ) return "hb/mangler/fx_hb_mangler_projectile";
    if ( stage == "charge" ) return "dlc3/stalingrad/fx_raz_mc_charge";
    if ( stage == "flash" ) return "dlc3/stalingrad/fx_raz_mc_muz_flash";
    return "dlc3/stalingrad/fx_raz_mc_shockwave_projectile_impact";
}

function dev_log( message )
{
    if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
    line = "[TOD_MANGLER] ms=" + GetTime() + " " + message;
    /# PrintLn( line ); #/
}

function live_manglers()
{
    found = [];
    foreach ( actor in GetAISpeciesArray( "all", "all" ) )
        if ( isdefined( actor ) && isalive( actor ) && IS_TRUE( actor.tod_mangler ) )
            found[found.size] = actor;
    return found;
}
function valid_target( p )
{
    return tod_doppelghast::valid_target( p );
}
function target_player()
{
    candidates = [];
    foreach ( p in GetPlayers() )
        if ( valid_target( p ) ) candidates[candidates.size] = p;
    if ( candidates.size == 0 ) return undefined;
    return candidates[RandomInt( candidates.size )];
}
function hunt_target()
{
    // ITS OWN PICK (2026-10-05, the 17:33 run): every companion sets allow_zombie_to_target_ai, so the stock
    // Raz target service writes the COMPANION into favoriteenemy between our ticks. This read that back, found
    // no player and re-picked every 250 ms (160 RETARGET lines, a FindPath per player each time), and attacks()
    // - which read favoriteenemy too - skipped its cannon and swipe whenever it held the companion. The chase
    // writes its pick to tod_hunt_player as well, and both read that.
    current = self.tod_hunt_player;
    keep = valid_target( current );
    // THE HAVEN'S GUARDIANS (docs/202 v3): a guardian hunts its own floor only (tod_hunt_filter, _tod_haven::guard_target_ok)
    if ( keep && isdefined( self.tod_hunt_filter ) && !( self [[ self.tod_hunt_filter ]]( current ) ) ) keep = false;
    if ( keep )
    {
        now = GetTime();
        if ( !isdefined( self.tod_hunt_recheck_ms ) ) self.tod_hunt_recheck_ms = now + TOD_HUNT_RECHECK_MS;
        if ( now < self.tod_hunt_recheck_ms ) return current;
        self.tod_hunt_recheck_ms = now + TOD_HUNT_RECHECK_MS;
        if ( self FindPath( self.origin, current.origin, false, false ) ) return current;
    }
    best = undefined;
    best_d = 0;
    nearest = undefined;
    nearest_d = 0;
    foreach ( p in GetPlayers() )
    {
        if ( !valid_target( p ) ) continue;
        if ( isdefined( self.tod_hunt_filter ) && !( self [[ self.tod_hunt_filter ]]( p ) ) ) continue;   // not on this guardian's floor
        d = DistanceSquared( self.origin, p.origin );
        if ( !isdefined( nearest ) || d < nearest_d ) { nearest = p; nearest_d = d; }
        if ( keep && p == current ) continue;   // just proved off the mesh this pass
        if ( !( self FindPath( self.origin, p.origin, false, false ) ) ) continue;
        if ( !isdefined( best ) || d < best_d || ( d == best_d && RandomInt( 2 ) == 0 ) )
        {
            best = p;
            best_d = d;
        }
    }
    reachable = isdefined( best );
    if ( !reachable )
    {
        if ( keep ) return current;   // nobody reachable: hold, and let the relocate lane work
        if ( isdefined( self.tod_hunt_filter ) && !isdefined( nearest ) )
            return undefined;   // a guardian with nobody on its floor stands down
        best = nearest;
    }
    if ( isdefined( best ) && ( !isdefined( current ) || best != current ) )
        dev_log( "RETARGET kind=" + ( isdefined( self.tod_bo6_dev_kind ) ? self.tod_bo6_dev_kind : "mangler" ) + " entity=" + self GetEntityNumber() + " player=" + best GetEntityNumber() + " dist=" + Int( Distance( self.origin, best.origin ) ) + " reachable=" + reachable + " kept_previous=" + keep );
    return best;
}
function spawn_tell( org, secs, label )
{
    effect = undefined;
    if ( isdefined( level._effect ) && isdefined( level._effect[ "lightning_dog_spawn" ] ) )
        effect = level._effect[ "lightning_dog_spawn" ];
    if ( isdefined( effect ) )
    {
        bolt = fx_host( effect, org, ( 0, 0, 0 ) );
        if ( isdefined( bolt ) ) bolt thread expire_fx( secs + 1.5 );
    }
    tod_perk_scatter::play_sound_at_origin( org, "zmb_hellhound_prespawn" );
    dev_log( "TELL " + label + " entity=" + self GetEntityNumber() + " origin=" + org + " secs=" + secs + " fx=" + ( isdefined( effect ) ? effect : "none" ) );
    self SetGoal( self.origin );   // hold the spot; the BT has no target while ignoreall
    elapsed = 0;
    while ( elapsed < secs )
    {
        wait 0.1;
        if ( !IS_TRUE( level.tod_upgrade_pause ) ) elapsed += 0.1;
    }
    while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.1;
    tod_perk_scatter::play_sound_at_origin( org, "zmb_hellhound_bolt" );
    Earthquake( 0.4, 0.6, org, 800 );
    self ForceTeleport( org, self.angles );   // back on the bolt, whatever the BT did meanwhile
}

function clear_of_players( org )
{
    foreach ( p in GetPlayers() )
        if ( isdefined( p.origin ) && isalive( p ) && DistanceSquared( p.origin, org ) < 40000 )
            return false;
    return true;
}

function spawn_position( target )
{
    return tod_doppelghast::reloc_point( target );
}

function init()
{
    tod_bo6_audio::init();
    level.tod_mangler_generation = 0;
    dev_log( "INIT skin=default animations=Hellbound director=tod_cyber_elites" );
}
function spawn_at( org, target, angles )
{
    actor = SpawnActor( "spawner_hb_mangler", org, angles, "tod_mangler", true );
    if ( !isdefined( actor ) ) return undefined;
    actor Ghost();   // hidden until initialize_actor's tell has played (spawn_tell)
    level.tod_mangler_actor = actor;
    level.tod_mangler_last_spawn_ms = GetTime();
    level.tod_mangler_generation++;
    actor.tod_mangler_generation = level.tod_mangler_generation;
    actor.tod_mangler = true;
    configure_variant( actor );
    actor.is_boss = true;
    actor.acc_is_boss = true;
    actor.acc_is_mini_boss = true;
    actor.tod_boss_kind = "mangler";
    actor.tod_boss_custom_speed = true;
    actor.acc_boss_custom_speed = true;
    actor.ignore_enemy_count = true;
    actor.ignore_round_spawn_failsafe = true;
    actor.no_powerups = true;
    actor.disableAmmoDrop = true;
    actor.ignore_nuke = true;
    actor.spawn_time = GetTime();
    actor.starting_round = level.round_number;
    actor.zombieMeleePlayerCounter = 0;
    actor ClearEntityOwner();
    actor.health = tod_doppelghast::hunter_hp( actor.tod_mangler_hp_zombies );
    actor.maxhealth = actor.health;
    actor.favoriteenemy = target;
    actor.tod_hunt_player = target;
    actor.ignoreall = true;
    actor.ignoreme = true;
    actor thread initialize_actor();
    dev_log( "SPAWN generation=" + actor.tod_mangler_generation + " entity=" + actor GetEntityNumber() + " hp=" + actor.health + " origin=" + org + " live=" + live_manglers().size + " cap=" + ( isdefined( level.tod_mangler_cap ) ? level.tod_mangler_cap : 1 ) );
    actor thread death_watch();
    return actor;
}

function death_watch()
{
    level endon( "end_game" );
    generation = self.tod_mangler_generation;
    self waittill( "death", attacker );
    if ( isdefined( attacker ) && isplayer( attacker ) )
        tod_luck::boss_kill( attacker, "mangler" );
    org = undefined;
    if ( isdefined( self ) ) org = self.origin;
    tod_bosses::grant_elite_reward( "MANGLER", attacker, org );
    dev_log( "DEATH generation=" + generation + " reward=elite_killer live=" + live_manglers().size );
    if ( isdefined( self ) )
    {
        tod_bo6_audio::death( self, "mangler" );
        self thread corpse_cleanup();
    }
}

function initialize_actor()
{
    self endon( "death" );
    level endon( "end_game" );
    wait 0.05;
    self.targetname = "zombie_boss";
    self.animname = "zombie_boss";
    self.is_zombie = true;
    self.allowdeath = true;
    self.gibbed = true;
    self.head_gibbed = true;
    self.force_gib = false;
    self allowedStances( "stand" );
    self setPhysParams( 15, 0, 72 );
    self.goalradius = 32;
    self.disableArrivals = true;
    self.disableExits = true;
    self.ignoreSuppression = true;
    self.grenadeawareness = 0;
    self.badplaceawareness = 0;
    self.a.disablepain = true;
    self.allowpain = false;
    self.allowmelee = false;
    self.canattack = false;
    self.meleeDamage = 35;
    self.variant_type = 0;
    self.zombie_move_speed = "sprint";
    self.zombie_arms_position = "down";
    self.freezegun_damage = 0;
    self.flame_damage_time = 0;
    self.zombie_damaged_by_bar_knockdown = false;
    self.ai_state = "zombie_think";
    self.find_flesh_struct_string = "find_flesh";
    self.zombie_think_done = true;
    self.zombie_init_done = true;
    self.team = level.zombie_team;
    self.updateSight = false;
    self setAvoidanceMask( "avoid none" );
    self PushActors( true );
    self zm_utility::disable_react();
    self zm_utility::init_zombie_run_cycle();
    self.zombie_move_speed = "sprint";
    self.zombie_arms_position = "down";
    self.variant_type = 0;
    self.needs_run_update = true;
    self.deathanim = %hb_mangler_death;
    self.deathFunction = &zm_spawner::zombie_death_animscript;
    self.thundergun_knockdown_func = level.basic_zombie_thundergun_knockdown;
    self.tesla_head_gib_func = &zm_spawner::zombie_tesla_head_gib;
    self thread zm_spawner::enemy_death_detection();
    level thread zm_spawner::zombie_death_event( self );
    zm_utility::recalc_zombie_array();
    self spawn_tell( self.origin, TOD_MANGLER_TELL_SECS, "kind=mangler variant=" + self.tod_mangler_variant + " generation=" + self.tod_mangler_generation );
    self EnableAimAssist();
    self Show();
    self.ignoreme = false;
    self.ignoreall = false; // zombieTargetService returns early while true.
    self.hasSeenFavoriteEnemy = true;
    self SetGoal( self.origin );
    self PathMode( "move allowed" );
    tod_bo6_audio::attach( self, "mangler" );
    self notify( "zombie_init_done" );
    self thread step_watch();
    self thread chase();
    self thread attacks();
    self thread damage_log();
    self thread dev_verify_rig();
    level thread body_lights( self, self.tod_mangler_generation );
    dev_log( "READY revision=cybercity_default_1 generation=" + self.tod_mangler_generation + " variant=" + self.tod_mangler_variant + " color=" + self.tod_mangler_color + " model=" + self.model );
}
function body_lights( owner, generation )
{
    level endon( "end_game" );
    tags = [];
    tags[0] = "tag_eye";
    tags[1] = "tag_flash";
    effects = [];
    effects[0] = "hb/mangler/fx_hb_mangler_eyes";
    effects[1] = cannon_fx( owner.tod_mangler_color, "idle" );
    hosts = [];
    for ( i = 0; i < tags.size; i++ )
    {
        if ( !isdefined( owner ) || !isalive( owner ) ) break;
        org = owner GetTagOrigin( tags[i] );
        if ( !isdefined( org ) )
        {
            dev_log( "LIGHT_DENIED generation=" + generation + " reason=missing_tag tag=" + tags[i] );
            continue;
        }
        host = Spawn( "script_model", org );
        if ( !isdefined( host ) )
        {
            dev_log( "LIGHT_DENIED generation=" + generation + " reason=entity_pool tag=" + tags[i] );
            continue;
        }
        host SetModel( "tag_origin" );
        host LinkTo( owner, tags[i], (0,0,0), (0,0,0) );
        PlayFXOnTag( effects[i], host, "tag_origin" );
        hosts[hosts.size] = host;
        dev_log( "LIGHT_ATTACH generation=" + generation + " host=" + host GetEntityNumber() + " tag=" + tags[i] + " effect=" + effects[i] );
    }
    expected = 2;
    dev_log( "LIGHT_READY generation=" + generation + " hosts=" + hosts.size + " expected=" + expected );
    while ( isdefined( owner ) && isalive( owner ) ) wait 0.1;
    removed = 0;
    foreach ( host in hosts )
        if ( isdefined( host ) ) { host Delete(); removed++; }
    dev_log( "LIGHT_CLEANUP generation=" + generation + " reason=death_or_removed deleted=" + removed );
}
function dev_verify_rig()
{
    if ( !IS_TRUE( level.tod_dev ) || self.tod_mangler_generation > 2 ) return;
    self endon( "death" );
    level endon( "end_game" );
    max_radius = 0;
    max_span = 0;
    missing = 0;
    outliers = 0;
    for ( sample = 0; sample < 120; sample++ )
    {
        wrist = self GetTagOrigin( "j_wrist_le" );
        pinky = self GetTagOrigin( "j_pinky_le_3" );
        ring = self GetTagOrigin( "j_ring_le_3" );
        if ( !isdefined( wrist ) || !isdefined( pinky ) || !isdefined( ring ) )
            missing++;
        else
        {
            radius = Distance( pinky, self.origin );
            span = Distance( pinky, wrist );
            ring_span = Distance( ring, wrist );
            if ( ring_span > span ) span = ring_span;
            if ( radius > max_radius ) max_radius = radius;
            if ( span > max_span ) max_span = span;
            if ( radius > 160 || span > 24 )
            {
                outliers++;
                if ( outliers <= 3 )
                    dev_log( "RIG_OUTLIER generation=" + self.tod_mangler_generation + " sample=" + sample + " radius=" + radius + " finger_span=" + span );
            }
        }
        wait 0.25;
    }
    dev_log( "RIG_CHECK revision=parent_pose_2 generation=" + self.tod_mangler_generation + " samples=120 missing=" + missing + " outliers=" + outliers + " max_hand_radius=" + max_radius + " max_finger_span=" + max_span );
}
function disabled_by_card()
{
    now = GetTime();
    if ( isdefined( self.tod_emp_until ) && now < self.tod_emp_until ) return true;
    if ( isdefined( self.tod_stun_until ) && now < self.tod_stun_until ) return true;
    return false;
}

// THE MANGLER'S FOOTFALLS (the note at the defines). self = the Mangler.
function step_watch()
{
    self endon( "death" );
    level endon( "end_game" );
    times = GetNotetrackTimes( %hb_mangler_run, "footstep" );
    source = "clip_notes";
    if ( !isdefined( times ) || times.size == 0 )
    {
        // the run clip's six 'footstep' frames, if the converter kept no note list
        times = array( 9 / TOD_MANGLER_RUN_FRAMES, 20 / TOD_MANGLER_RUN_FRAMES, 32 / TOD_MANGLER_RUN_FRAMES,
                       43 / TOD_MANGLER_RUN_FRAMES, 54 / TOD_MANGLER_RUN_FRAMES, 64 / TOD_MANGLER_RUN_FRAMES );
        source = "fallback_frames";
    }
    dev_log( "STEPS generation=" + self.tod_mangler_generation + " notes=" + times.size + " source=" + source );
    last_t = undefined;
    last_org = self.origin;
    min_move_sq = TOD_MANGLER_STEP_MIN_MOVE * TOD_MANGLER_STEP_MIN_MOVE;
    while ( 1 )
    {
        wait TOD_MANGLER_STEP_POLL;
        t = self GetAnimTime( %hb_mangler_run );
        moved_sq = DistanceSquared( self.origin, last_org );
        last_org = self.origin;
        if ( !isdefined( t ) || IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_mangler_attacking ) || moved_sq < min_move_sq )
        {
            last_t = undefined;   // re-anchor on the next moving poll: a resumed clip never fires the notes it skipped
            continue;
        }
        if ( step_crossed( times, last_t, t ) )
            tod_bo6_audio::mangler_step( self, "anim_time" );
        last_t = t;
    }
}

// PURE (tools/sfx/silent_sounds/test_mangler_steps.js runs it): did the run clip's phase move from last_t to t
// across a footstep note? One step per poll at most: the notes are 0.37 s apart at 1x, a poll is 0.05 s.
function step_crossed( times, last_t, t )
{
    if ( !isdefined( last_t ) || !isdefined( t ) || t == last_t )
        return false;
    span = t - last_t;
    if ( span < 0 )
        span += 1;   // the loop wrapped
    if ( span >= TOD_MANGLER_STEP_MAX_SPAN )
        return false;   // a clip restart or a jump, not a stride
    foreach ( s in times )
    {
        if ( t > last_t )
        {
            if ( s > last_t && s <= t )
                return true;
        }
        else if ( s > last_t || s <= t )
            return true;
    }
    return false;
}

function chase()
{
    self endon( "death" );
    level endon( "end_game" );
    previous = self.origin;
    stuck = 0;
    logged_motion = false;
    while ( 1 )
    {
        wait 0.25;
        if ( IS_TRUE( level.tod_upgrade_pause ) || self disabled_by_card() )
        {
            self.ignoreall = true;
            self.v_zombie_custom_goal_pos = self.origin;
            self ASMSetAnimationRate( 0.05 );
            continue;
        }
        rate = self.tod_mangler_speed;
        if ( isdefined( self.tod_emp_slow_until ) && GetTime() < self.tod_emp_slow_until ) rate *= 0.5;
        // THE HAVEN'S FIELD (docs/202): 0.67 inside a safe-zone dome while it moves (its melee waits a fixed 0.77 s)
        if ( isdefined( self.tod_safe_mult ) && !IS_TRUE( self.tod_mangler_attacking ) ) rate *= self.tod_safe_mult;
        self ASMSetAnimationRate( rate );
        self.ignoreall = false;
        target = self hunt_target();
        self.tod_hunt_player = target;   // hunt_target / attacks read this (the stock service rewrites favoriteenemy)
        if ( !isdefined( target ) )
        {
            if ( isdefined( self.tod_hunt_home ) ) self.v_zombie_custom_goal_pos = self.tod_hunt_home;   // a haven guardian walks home
            continue;
        }
        self.favoriteenemy = target;
        self.hasSeenFavoriteEnemy = true;
        self.v_zombie_custom_goal_pos = target.origin;
        if ( DistanceSquared( self.origin, previous ) < 64 && DistanceSquared( self.origin, target.origin ) > 22500 ) stuck += 0.25;
        else { stuck = 0; previous = self.origin; }
        if ( !logged_motion && DistanceSquared( self.origin, self.tod_motion_start ) > 4096 )
        {
            logged_motion = true;
            dev_log( "MOVED generation=" + self.tod_mangler_generation + " origin=" + self.origin );
        }
        behind_seal = false; // Cybercity relocates through its own door/zone frontier.
        if ( !IS_TRUE( self.tod_mangler_attacking ) && ( behind_seal || stuck >= 12 ) )
        {
            org = spawn_position( target );
            if ( isdefined( org ) )
            {
                self ForceTeleport( org );
                self.tod_motion_start = org; // A teleport is not proof of locomotion.
                dev_log( "RELOCATE generation=" + self.tod_mangler_generation + " sealed=" + behind_seal + " origin=" + org );
                stuck = 0;
                previous = org;
            }
        }
    }
}

function attacks()
{
    self endon( "death" );
    level endon( "end_game" );
    self.tod_motion_start = self.origin;
    next_cannon = GetTime() + TOD_MANGLER_CANNON_FIRST_MS;
    while ( 1 )
    {
        wait 0.1;
        if ( IS_TRUE( level.tod_upgrade_pause ) || self disabled_by_card() ) continue;
        target = self.tod_hunt_player;   // its own pick, never the companion the stock service wrote into favoriteenemy
        if ( !valid_target( target ) ) continue;
        dist = DistanceSquared( self.origin, target.origin );
        if ( !BulletTracePassed( self.origin + (0,0,48), target.origin + (0,0,36), false, self, target ) ) continue;
        if ( dist < 8100 )
        {
            self.tod_mangler_attacking = true;
            self AnimScripted( "note_notify", self.origin, VectorToAngles( ( target.origin[0], target.origin[1], self.origin[2] ) - self.origin ), %hb_mangler_melee );
            self PlaySound( "hb_mangler_melee" );
            tod_bo6_audio::mangler_melee( self );   // + the BO6 armour lunge at the clip's frame 5 (its AudioOneShot@ note never reaches script, PK02)
            dev_log( "SOUND generation=" + self.tod_mangler_generation + " alias=hb_mangler_melee event=melee_start" );
            wait 0.77; // BO6 hit_melee marker: frame 23 at 30 fps.
            if ( !IS_TRUE( level.tod_upgrade_pause ) && !( self disabled_by_card() ) && valid_target( target ) &&
                 DistanceSquared( self.origin, target.origin ) < 14400 && BulletTracePassed( self.origin + (0,0,48), target.origin + (0,0,36), false, self, target ) )
            {
                target DoDamage( 35, target.origin, self, self, "none", "MOD_MELEE" );
                dev_log( "MELEE_HIT generation=" + self.tod_mangler_generation );
            }
            wait 1.1;
            self.tod_mangler_attacking = false;
        }
        else if ( dist < TOD_MANGLER_CANNON_RANGE * TOD_MANGLER_CANNON_RANGE && GetTime() >= next_cannon )
        {
            self.tod_mangler_attacking = true;
            cannon_started = GetTime();
            windup = 2.04 / self.tod_mangler_cannon_rate;
            recovery = 1.06 / self.tod_mangler_cannon_rate;
            aim = target.origin + (0,0,36);
            self AnimScripted( "note_notify", self.origin, VectorToAngles( ( aim[0], aim[1], self.origin[2] ) - self.origin ), %hb_mangler_cannon, "normal", undefined, self.tod_mangler_cannon_rate, 0.1 );
            tod_bo6_audio::mangler_cannon_windup( self, self.tod_mangler_cannon_rate );   // click / pull-back / charge whine on the clip's frames 1 / 10 / 27 (PK02: the windup was silent)
            charge = fx_host( cannon_fx( self.tod_mangler_color, "charge" ), self GetTagOrigin( "tag_flash" ), self.angles );
            if ( isdefined( charge ) )
            {
                charge LinkTo( self, "tag_flash", (0,0,0), (0,0,0) );
                charge thread expire_fx( windup, self );
            }
            dev_log( "CANNON_WINDUP generation=" + self.tod_mangler_generation + " color=" + self.tod_mangler_color + " duration_ms=" + Int( windup * 1000 ) + " rate=" + self.tod_mangler_cannon_rate + " aim=" + aim );
            wait windup; // BO6 frame-61 shoot marker, scaled with the clip.
            if ( !IS_TRUE( level.tod_upgrade_pause ) && !( self disabled_by_card() ) && isdefined( target ) && valid_target( target ) )
            {
                aim = target.origin + (0,0,40); // Refresh after the charge, then steer throughout flight.
                muzzle = self GetTagOrigin( "tag_flash" );
                launch_base = self.origin + (0,0,54);
                barrel_trace = BulletTrace( launch_base, muzzle, false, self );
                if ( barrel_trace["fraction"] < 1 )
                {
                    muzzle = barrel_trace["position"] + VectorNormalize( launch_base-muzzle )*3;
                    dev_log( "CANNON_MUZZLE_CLAMP generation=" + self.tod_mangler_generation + " fraction=" + barrel_trace["fraction"] + " origin=" + muzzle );
                }
                direction = VectorNormalize( aim - muzzle );
                flash = fx_host( cannon_fx( self.tod_mangler_color, "flash" ), muzzle, VectorToAngles( direction ) );
                if ( isdefined( flash ) ) flash thread expire_fx( 0.6 );
                tod_perk_scatter::play_sound_at_origin( muzzle, "hb_mangler_fire" );
                dev_log( "SOUND generation=" + self.tod_mangler_generation + " alias=hb_mangler_fire event=shoot_marker origin=" + muzzle );
                level thread cannon_projectile( self, self.tod_mangler_generation, muzzle, direction, target, self.tod_mangler_color );
                dev_log( "CANNON_FIRE generation=" + self.tod_mangler_generation + " color=" + self.tod_mangler_color + " windup_ms=" + ( GetTime() - cannon_started ) + " muzzle=" + muzzle + " aim=" + aim );
            }
            else
            {
                tod_bo6_audio::mangler_cannon_cancel( self );   // a windup that never fires does not leave its whine ringing
                dev_log( "CANNON_CANCEL generation=" + self.tod_mangler_generation + " reason=pause_or_target_lost" );
            }
            wait recovery;
            self.tod_mangler_attacking = false;
            next_cannon = GetTime() + TOD_MANGLER_CANNON_GAP_MS;
        }
    }
}
function fx_host( effect, org, facing )
{
    host = Spawn( "script_model", org );
    if ( !isdefined( host ) ) return undefined;
    host SetModel( "tag_origin" );
    host.angles = facing;
    PlayFXOnTag( effect, host, "tag_origin" );
    return host;
}

function expire_fx( seconds, owner )
{
    level endon( "end_game" );
    had_owner = isdefined( owner );
    deadline = GetTime() + Int( seconds * 1000 );
    while ( GetTime() < deadline )
    {
        if ( had_owner && ( !isdefined( owner ) || !isalive( owner ) || IS_TRUE( level.tod_upgrade_pause ) ) ) break;
        wait 0.05;
    }
    if ( isdefined( self ) ) self Delete();
}

function cannon_projectile( owner, generation, org, direction, target, color )
{
    level endon( "end_game" );
    wave = fx_host( cannon_fx( color, "projectile" ), org, VectorToAngles( direction ) );
    if ( !isdefined( wave ) ) { dev_log( "CANNON_DENIED reason=entity_pool" ); return; }
    wave PlaySound( "hb_mangler_pulse" );
    dev_log( "SOUND generation=" + generation + " alias=hb_mangler_pulse event=projectile_start" );
    flight_started = GetTime();
    reason = "timeout";
    launch_org = org;
    target_start = target.origin;
    target_id = target GetEntityNumber();
    traveled = 0;
    turns = 0;
    dev_log( "CANNON_TRACK generation=" + generation + " target=" + target_id + " speed=650 lifetime_ms=4000 range=1800" );
    for ( step = 0; step < 80; step++ )
    {
        if ( IS_TRUE( level.tod_upgrade_pause ) ) { reason = "upgrade_pause"; break; }
        if ( !valid_target( target ) ) { reason = "target_lost"; break; }
        if ( DistanceSquared( launch_org, target.origin ) > 3240000 || traveled >= 1800 ) { reason = "range"; break; }
        desired = VectorNormalize( target.origin + (0,0,40) - org );
        if ( VectorDot( direction, desired ) < 0.999 ) turns++;
        direction = VectorNormalize( direction * 0.65 + desired * 0.35 );
        next = org + direction * 32.5; // 650 units/sec, 50 ms steps.
        trace = BulletTrace( org, next, false, owner );
        next = trace["position"];
        blocked = trace["fraction"] < 1;
        nearest = Distance( org, next );
        foreach ( p in GetPlayers() )
        {
            if ( !zm_utility::is_player_valid( p ) ) continue;
            center = p.origin + (0,0,36);
            along = VectorDot( center - org, direction );
            if ( along < 0 ) along = 0;
            if ( along > nearest ) along = nearest;
            point = org + direction * along;
            if ( DistanceSquared( center, point ) < 1600 &&
                 BulletTracePassed( point, center, false, owner, p ) )
            {
                nearest = along;
                next = point;
                blocked = true;
                reason = "player";
            }
        }
        traveled += Distance( org, next );
        wave.angles = VectorToAngles( direction );
        wave MoveTo( next, 0.05 );
        wait 0.05;
        org = next;
        if ( blocked )
        {
            if ( reason != "player" ) reason = "world";
            break;
        }
    }
    wave StopSound( "hb_mangler_pulse" );
    wave thread expire_fx( 0.15 );
    moved = -1;
    if ( isdefined( target ) ) moved = Distance( target_start, target.origin );
    dev_log( "CANNON_TRACK_END generation=" + generation + " target=" + target_id + " reason=" + reason + " turns=" + turns + " target_moved=" + moved + " traveled=" + traveled + " flight_ms=" + ( GetTime() - flight_started ) );
    if ( reason == "range" || reason == "timeout" || reason == "target_lost" ) return;
    if ( reason == "upgrade_pause" || IS_TRUE( level.tod_upgrade_pause ) )
    {
        dev_log( "CANNON_CANCEL generation=" + generation + " reason=upgrade_pause_in_flight" );
        return;
    }
    impact_org = org - direction * 2; // Keep LOS/FX just outside the hit surface.
    impact = fx_host( cannon_fx( color, "impact" ), impact_org, VectorToAngles( direction * -1 ) );
    if ( isdefined( impact ) ) impact thread expire_fx( 2 );
    tod_perk_scatter::play_sound_at_origin( impact_org, "hb_mangler_impact" );
    dev_log( "SOUND generation=" + generation + " alias=hb_mangler_impact event=collision origin=" + impact_org );
    hits = 0;
    foreach ( p in GetPlayers() )
        if ( zm_utility::is_player_valid( p ) && DistanceSquared( p.origin + (0,0,36), impact_org ) < 14400 &&
             BulletTracePassed( impact_org, p.origin + (0,0,36), false, owner, p ) )
        {
            p DoDamage( 25, p.origin, owner, owner, "none", "MOD_PROJECTILE_SPLASH" );
            hits++;
        }
    dev_log( "CANNON_IMPACT generation=" + generation + " color=" + color + " reason=" + reason + " origin=" + impact_org + " flight_ms=" + ( GetTime() - flight_started ) + " hits=" + hits );
}

function damage_log()
{
    self endon( "death" );
    if ( !IS_TRUE( level.tod_dev ) ) return;
    while ( 1 )
    {
        self waittill( "damage", amount );
        dev_log( "DAMAGE generation=" + self.tod_mangler_generation + " amount=" + amount + " hp=" + self.health );
    }
}

// self = the dead Mangler (the TOD_MANGLER_GROUND_SECS note): the arm's thud, the break-up at the clip's end, the
// body hidden under its flash, then gone.
function corpse_cleanup()
{
    level endon( "end_game" );
    generation = self.tod_mangler_generation;
    wait TOD_MANGLER_GROUND_SECS;
    if ( !isdefined( self ) ) return;
    tod_bo6_audio::sound_at( TOD_MANGLER_GROUND_ALIAS, self.origin, 3 );
    wait TOD_MANGLER_BURST_SECS - TOD_MANGLER_GROUND_SECS;
    if ( !isdefined( self ) ) return;
    torso = self GetTagOrigin( "j_spine4" );
    if ( !isdefined( torso ) ) torso = self.origin + (0,0,12);
    tod_elite_fx::mangler_burst( torso, generation );
    tod_bo6_audio::sound_at( TOD_MANGLER_IMPACT_ALIAS, torso, 6 );
    dev_log( "DEATH_BURST generation=" + generation + " torso=" + torso );
    wait TOD_MANGLER_HIDE_SECS;
    if ( !isdefined( self ) ) return;
    self Hide();
    wait TOD_MANGLER_GONE_SECS;
    if ( isdefined( self ) ) self Delete();
}
