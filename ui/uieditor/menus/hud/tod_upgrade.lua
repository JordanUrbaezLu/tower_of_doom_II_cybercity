require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership" )
-- =============================================================================
-- tod_upgrade.lua — the upgrade-choice panel (standalone additive overlay).
--
-- Opened per-player from GSC (`player OpenLUIMenu("tod_upgrade")`) — the SAFE
-- overlay path (cannot break the stock HUD; map 1 docs/19). Data arrives on
-- all-INT clientuimodel clientfields (zero string-cache / istring cost;
-- every visible string lives HERE, client-side):
--   todUpgShow  0 hidden | 1 choosing | 2 left picked | 3 right picked
--   todUpgAD/BD domain id  0 none | 1..18 = the DOMAIN table below
--   todUpgAR/BR rarity     1 regular | 2 SUPER | 3 ULTIMATE
--   todUpgHold  hold-to-lock progress 0..15 (the fill bar)
--   todUpgAL/BL current level 0..10
--   todUpgLuck  0..10 = luck bar in tens (the top-left bar AND the deal
--               badge); 11..14 = OVERCHARGE zap frames (v14.9 — the bar
--               secretly tracks to 150 server-side; at the ceiling
--               _tod_luck's overcharge_driver cycles these four values at
--               ~7 Hz, server-driven like every blink in this file)
--   todUpgFocus hover state, SERVER-driven blink (no UITimers client-side):
--               0 none | 1 left bright | 2 left dim | 3 right bright | 4 right dim
--               (the GSC hold-to-confirm loop toggles bright/dim at ~7 Hz while
--               the player holds AIM/FIRE; release cancels, 0.5s hold locks in)
--   todUpgTime  seconds until auto-select 15..0 (red at <= 5)
--
-- ART (all LIVE): USE_CARD_SET_ART is the primary switch — the 54 baked
-- cartoon cards (18 domains x 3 rarities, i_tod_card_<slug>_<rarity>, slugs
-- in CARD_SLUG below, rarities regular/super/ultimate) replace the composite
-- frame+base+icon path and force USE_FRAME/BASE/ICON_ART off (USE_TITLE_ART
-- stays). The per-piece composite flags remain the no-card-set fallback
-- (i_tod_frame_*, i_tod_card_base, icons, i_tod_title_plate), with the flat
-- TextWithBg panels as the final no-art fallback. A flag may only be true
-- once its images are installed as image assets WITH zone lines —
-- RegisterImage of a missing image is undefined behavior.
-- Server stays the state machine (_tod_upgrade_ui.gsc); this file is a dumb
-- renderer (the AccAreaBanner doctrine). Idioms copied from map 1's
-- shipped-ACTIVE acc_hud.lua ONLY (CoD.TextWithBg panels — never Hud.Bg;
-- Engine.CreateModel subscribe — never a bare GetModel that can hand nil;
-- keyframe tweens — never UITimers). L3akMod global whitelist honored.
-- =============================================================================

-- [tod v17.24] the ONE writer for a bind name inside the pale keycap — the fit
-- rule, the multi-bind trim and the cap's measured face geometry all live there,
-- shared with tod_class_select.lua and the pause legend. See its header.
--
-- [tod v17.30] AND IT IS FAIL-SAFED, because THIS is the file the lint header
-- above calls the highest-blast-radius in the tree. A require that throws — the
-- rawfile missing from the .ff, a Lua error inside the widget or inside
-- TodGlyphRow beneath it — aborts this ENTIRE file, silently, and takes the
-- upgrade panel, the crosshair damage numbers, the tower gauge, the luck bar,
-- the finale banner, the rampage seal AND the `tod_input_pad` receiver with it.
-- That is far too much to hang on one unguarded require for a decoration.
--
-- So: pcall the require, and route every call site through TodKeycapMake, which
-- degrades to the plain LUI text this menu already builds. THE STUB IS
-- DELIBERATELY LOCAL AND TWINNED across the three menus that use the widget — a
-- fail-safe that lives inside the thing it guards against is not a fail-safe,
-- and that is the one case where a twin beats a shared file.
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodKeycap" )

-- [tod v17.34] THE TYPEFACE, for the crosshair damage numbers. Same pcall for
-- the same reason as the line above, and the same shape of fallback: the damage
-- numbers degrade to the UIText they were until v17.34 rather than taking the
-- whole file down. CoD.TodGlyphText being nil is the ONE test — it is checked
-- where the pool is built and again where a number is drawn.
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphText" )

-- THE PULL (docs/187, 2026-09-28): the card-back / rarity-ladder / live-band
-- reveal. Same pcall shape: CoD.TodPull nil = the v14.52 socket reveal below
-- runs exactly as before, so a missing rawfile can never blank the panel.
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodPull" )
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodHudVeil" )   -- the HUD veil (2026-09-29)

-- [tod v18.32] IS THIS EXPANSION A BUTTON PICTURE? Declared HERE, above the
-- keycap stub, because the stub's own fallback needs it: with the widget
-- absent that fallback would set the engine's LT / RT / A icon as text inside a
-- pale keycap, which is the exact failure in the user's 2026-09-08 screenshot.
-- Twin of CoD.TodKeycap.IsPadGlyph, which is the canonical copy and carries the
-- whole argument; keep the two in step.
--
-- [tod v18.48] HIGH BYTES ONLY, AND THIS IS NOT A DEVICE TEST.
--
-- ⚠️ v18.47 scanned for `b < 32 or b > 126` AND USED IT TO PICK THE DEVICE.
-- Both halves were wrong. Something in the KEYBOARD expansion carries a low
-- control byte (a trailing NUL off the engine's C string is the obvious
-- candidate), so the test fired on every device and every keyboard player lost
-- their control set — user: *"Where is the KBM controls. All i see are
-- controller controls"*. Control characters prove nothing; only the HIGH range
-- can carry a button picture, since a keyboard key display name (SPACE, F,
-- MOUSE3, MIDDLE MOUSE) is printable ASCII.
--
-- It now answers ONE question — "may this string be drawn inside a keycap?" —
-- and is consulted only AFTER the baked typeface has failed to draw it. A key
-- name our own sheets can render never reaches it, which is what makes it
-- unable to turn a working keyboard into a controller whatever bytes come back.
-- The DEVICE is decided by UsingController below, on positive proof only.
local function TodPadGlyph( tok )
    local s = Engine.Localize( tok ) or ""
    s = s:gsub( "%^%d", "" )
    if s == "" then
        return false
    end
    for i = 1, #s do
        if string.byte( s, i ) > 126 then
            return true
        end
    end
    return false
end

local function TodKeycapMake( owner, text, controller )
    if CoD.TodKeycap then
        return CoD.TodKeycap.make( owner, text, controller )   -- RT: the controller resolves the KEY NAME (TodKeycap.Resolve)
    end
    return {
        hide = function ()
            if text then
                text:setAlpha( 0 )
            end
        end,
        paint = function ( capL, capT, capW, capH, token, alpha )
            if not text then
                return ""
            end
            -- [tod v18.32] never a button picture inside a keycap; the caller
            -- has already chosen the device, this is the backstop.
            if TodPadGlyph( token ) then
                text:setAlpha( 0 )
                return nil
            end
            local cy = capT + capH * 0.435
            text:setLeftRight( true, false, capL + 6, capL + capW - 6 )
            text:setTopBottom( true, false, cy - 8, cy + 8 )
            text:setScale( 1 )
            text:setText( Engine.Localize( token ) )
            text:setAlpha( ( alpha == nil ) and 1 or alpha )
            return ""
        end,
    }
end

-- [docs/160, 2026-09-23] THE DESCENT. Tower of Doom II starts at the crown and
-- goes DOWN, so a CLASS TIER floor requirement `need` (10 / 30, unchanged — it
-- is FLOORS OF PROGRESS) is shown as the floor the player will be standing on
-- when it clears: TIER_LAPS - need = 40 / 20. LOCKSTEP with TOD_GAUGE_DESCENT /
-- TOD_GAUGE_LAPS in _tod_gauge.gsc (tier_floor_display) and DESCENT in
-- gen_tower_map.js. Declared HERE, above the DETAIL table, because row 24's
-- act closure reads it — a local declared below that table would be a global
-- reference from the closure's point of view (the no-new-globals guard).
local TIER_DESCENT = true
local TIER_LAPS = 50
local function tierFloorShown( need )
    if TIER_DESCENT then
        return TIER_LAPS - need
    end
    return need
end

-- RT 2026-10-05 (the red return): the Map One navy / cyan / teal fallback tints join the one Fallen library - the
-- SWITCH word and the binds read in the red era's info blue (#9DD0FF), the hold fill and the chosen-card flash in
-- its READY red, the no-art glass in its charcoal (tools/artgen/synthwave.py THEME 'fallen').
local PAL = {
    glass = { 0.07, 0.07, 0.10 },     -- charcoal panel base (no-art fallback)
    line  = { 0.62, 0.82, 1.0 },      -- info blue: SWITCH, the binds, the fallback title
    text  = { 0.86, 0.9, 0.95 },      -- body text
    dim   = { 0.55, 0.62, 0.7 },      -- de-emphasized
    pick  = { 0.95, 0.13, 0.23 },     -- the READY red: the hold fill, LOCKED IN
    flash = { 0.94, 0.95, 0.98 },     -- the chosen card's strip flash: white reads LIT on every accent
    luck  = { 1.0, 0.88, 0.25 },      -- luck amber
    -- the card you are NOT on, while choosing: solid and this much darker (FocusCards)
    unfocusTone = 0.55,
}

-- DARK UPGRADES (v17.10): the sentinel the SERVER writes into the 4-bit level
-- field to mark a dealt card as DARK. LOCKSTEP with TOD_UPG_DARK_L in
-- _tod_upgrades.gsc and _tod_upgrade_ui.gsc -- all three are the literal 15.
-- Domain levels top out at 10, so 15 is unreachable as a real level; this is why
-- the feature spends no clientfield bits, and it is the TIER card's own idiom
-- (id 24 packs class+tier into this same field).
local DARK_L = 15

-- rarity id -> presentation (accent strip + tag)
-- FOUR RARITIES (2026-09-28, docs/187): COMMON white / RARE blue / EPIC purple /
-- LEGENDARY gold, paying +1..+4 levels. LOCKSTEP with TOD_RAR_* in _tod_upgrades.gsc.
-- The wire carries rarity - 1 (0..3) in todUpgAR/BR; Render decodes it.
local RARITY = {
    [1] = { tag = "COMMON",    col = { 0.914, 0.933, 0.961 }, lv = 1 },
    [2] = { tag = "RARE",      col = { 0.227, 0.659, 1.0 },   lv = 2 },
    [3] = { tag = "EPIC",      col = { 0.710, 0.361, 1.0 },   lv = 3 },
    [4] = { tag = "LEGENDARY", col = { 1.0, 0.761, 0.239 },   lv = 4 },
}

-- MOVE SPEED LADDER (v15 item 25). Cumulative PERCENTAGE POINTS for l levels
-- of any speed domain. Increments 5, 4, 3, 3, 3... so:
--   Lv1 5 · Lv2 9 · Lv3 12 · Lv4 15 · Lv5 18 · ... · Lv10 33
-- LOCKSTEP with speed_pct_for_level() in _tod_upgrades.gsc — same three
-- constants (0.05 / 0.04 / 0.03), expressed here in points rather than scale.
-- The GSC is the authority; if they ever disagree the PLAYER sees this one,
-- which is exactly why item 25 moved the number OFF the card art and onto the
-- pause menu: there is now one printed number and it is served from here.
-- THE SHARED 5-TIER LADDER (v16). Cumulative value at level l:
--   Lv1 10 · Lv2 18 · Lv3 24 · Lv4 28 · Lv5 32
-- LOCKSTEP with ladder5() in _tod_upgrades.gsc (TOD_LADDER5_L1..L5).
-- Unit-agnostic on purpose: RECOVERY and BACK ARMOR read it as a PERCENT,
-- VITALITY reads it as FLAT HP. The card art for all three is generic, so this
-- pause row is the ONLY place a player ever sees the real number.
local function ladder5( l )
    if not l or l <= 0 then return 0 end
    local T = { 10, 18, 24, 28, 32 }
    return T[ math.min( l, 5 ) ]
end

-- DMG REDUCTION's v16 ladder: cumulative 6/11/15/18/20 from increments
-- 6/5/4/3/2. MIRRORS dr_pct_for_level() in _tod_upgrades.gsc -- a lockstep pair
-- that nothing checks, so change both or neither. Deliberately NOT ladder5():
-- that table is 10/18/24/28/32 and belongs to RECOVERY/BACK ARMOR/VITALITY.
-- v17.3: the clamp at 5 is GONE, because the cap is per-class now (3/5/7/10)
-- and the heavy really does reach 10. Mirrors dr_pct_for_level exactly:
-- diminishing 6/5/4/3 to level 4, then a FLAT +2 per level on
-- TOD_UPG_DR_LN. Clamping here would have silently frozen the pause readout at
-- -20% for the two classes that now go past it, while the game applied more.
-- 2026-09-28 (user): 9 levels for EVERY class (no class caps), +5 / 3 / 2 / 2 / 2 ... =
-- 5 8 10 12 14 16 18 20 22% at Lv1..9. LOCKSTEP TOD_UPG_DR_L1..L4 / _LN in _tod_upgrades.gsc.
local function drPct( l )
    if not l or l <= 0 then return 0 end
    local T = { 5, 8, 10, 12 }
    if l <= 4 then return T[ l ] end
    return 12 + ( l - 4 ) * 2
end

-- LUCK and BOUNTY (2026-09-28, user: 9 levels, logarithmic, "Max both at +100% at level 9"):
-- 100 x ln( 1 + Lv ) / ln 10 = 30 / 48 / 60 / 70 / 78 / 85 / 90 / 95 / 100. LOCKSTEP
-- _tod_upgrades bounty_rate + _tod_luck add (both x card_curve).
local LOG9_PCT = { [0] = 0, 30, 48, 60, 70, 78, 85, 90, 95, 100 }
local function log9Pct( l )
    return LOG9_PCT[ math.min( math.max( l or 0, 0 ), 9 ) ]
end

local function speedPct( l )
    if not l or l <= 0 then return 0 end
    if l == 1 then return 5 end
    return 9 + ( l - 2 ) * 3
end

-- FULL STEAM (42) pays the shared ladder x1.2 (v16.8, user 2026-09-01: "improve
-- the full steam upgrade by 20%"): 6 / 10.8 / 14.4 / 18 / 21.6 points on the
-- scale, LOCKSTEP with TOD_LMGS_MULT in _tod_upgrades.gsc (lmg_sprint_bonus).
-- DISPLAYED ROUNDED TO THE NEAREST WHOLE PERCENT (v16.8a, user: "round to
-- nearest whole number for pause description"): 6 / 11 / 14 / 18 / 22. The GSC
-- still pays the exact value; only this row rounds. SPRINT (5) and FORCED
-- MARCH (37) stay on speedPct raw.
local FULL_STEAM_MULT = 1.2
local function fullSteamPct( l )
    return math.floor( speedPct( l ) * FULL_STEAM_MULT + 0.5 )
end

-- RIOT SHIELD (45, v16.63): the user's ladder verbatim. LOCKSTEP with
-- TOD_SHIELD_HP_L1..L5 and TOD_SHIELD_RECHARGE_L1..L5 in _tod_riotshield.gsc
-- (seconds there; printed m:ss here). Index = level, clamped 1..5 so a level
-- outside the table can never index nil into a setText.
-- 9 levels since 2026-09-28 (the Breacher's card), LOCKSTEP TOD_SHIELD_HP_TABLE / _RECHARGE_TABLE.
local SHIELD_HP       = { 200, 295, 350, 390, 420, 445, 465, 485, 500 }
local SHIELD_RECHARGE = { "4:00", "3:22", "3:00", "2:44", "2:32", "2:22", "2:14", "2:06", "2:00" }
local function shieldLv( l )
    if l < 1 then return 1 end
    if l > #SHIELD_HP then return #SHIELD_HP end
    return l
end
local function shieldHp( l )
    return SHIELD_HP[ shieldLv( l ) ]
end
local function shieldRecharge( l )
    return SHIELD_RECHARGE[ shieldLv( l ) ]
end
-- A percentage that may carry a half step (TRAILBLAZER's slow ladder since
-- v18.6 is 3 + 4.5*L). Whole values print as integers so the common rows do not
-- grow a pointless ".0"; halves print one decimal rather than being rounded,
-- because this row is the only place the player ever reads the figure.
local function pctStr( x )
    if x == math.floor( x ) then
        return string.format( "%d", x )
    end
    return string.format( "%.1f", x )
end

-- domain id -> display (MUST mirror _tod_upgrades.gsc register_domains order/ids
-- AND _tod_upgrade_ui.gsc domain_id). max = that domain's level cap. v4 matrix.
local DOMAIN = {
    [1]  = { name = "DAMAGE",      desc = "retired - each class has its own core weapon card", max = 10 },   -- RETIRED 2026-09-27 (user: "remove the damage card altogether"); nil-safe row
    -- v17.3 max 5 -> 10: 10 is the CEILING (heavy). The per-class caps are
    -- 3 skirmisher / 5 slasher / 7 assault / 10 heavy, declared by
    -- set_class_max in _tod_upgrades.gsc, and the pause row's own max arrives
    -- per-player through tod_upg_sync, so this number is only the fallback.
    -- Desc carries no ladder now because the ladder ends somewhere different
    -- for every class.
    [2]  = { name = "DMG REDUCTION", desc = "take less damage, always on: 5% at Lv1 up to 22% at Lv9", face = { "TAKE LESS DAMAGE", "ALWAYS ON" },  max = 9 },   -- 9 for every class 2026-09-28 (user)
    [3]  = { name = "BOUNTY",      desc = "more points per kill: +30% at Lv1 up to +100% at Lv9", face = { "MORE POINTS PER KILL", "UP TO DOUBLE AT LV9" },        max = 9 },   -- 9, log 2026-09-28 (user); W3E 2026-10-05: POINTS, the word the scoreboard, the HUD and DETAIL[3] use (was MONEY)
    [4]  = { name = "LUCK",        desc = "your luck bar fills faster: +30% at Lv1 up to +100% at Lv9", face = { "LUCK BAR FILLS FASTER", "BETTER CARDS SOONER" },       max = 9 },   -- 9, log 2026-09-28 (user)
    [5]  = { name = "REAPER'S REACH", desc = "longer beam; a wider beam at Lv3, Lv6 and Lv9", face = { "LONGER SOUL SUCK BEAM", "WIDER BEAM AT LV3 / 6 / 9" }, max = 9 },   -- 2026-09-27 CLASS BUILD CARD (_tod_class_cards); reuses a retired id; text card + text row (CoD.TodTextPlate) until art; W3E 2026-10-05: names SOUL SUCK (the beam was renamed from SOUL BEAM 2026-09-27)
    [6]  = { name = "DEADEYE",     desc = "your bows hit harder; fatter arrows at Lv3, Lv6 and Lv9", face = { "YOUR BOWS HIT HARDER", "FATTER ARROWS AT LV3 / 6 / 9" }, max = 9 },   -- 2026-09-27: the ARCHER CORE WEAPON card (reuses retired HEADSHOT id; text card + text row, TodTextPlate)
    [7]  = { name = "ARMS SPECIALIST", desc = "your melee weapons hit harder and reach further; swing faster at Lv3, Lv6 and Lv9", face = { "HARDER HITS LONGER REACH", "FASTER SWINGS AT LV3 / 6 / 9" }, max = 9 },   -- 2026-09-27: the WARRIOR CORE WEAPON card (reuses retired MAG SIZE id; text card + text row, TodTextPlate); 2026-09-28: MELEE RANGE folded in (reach)
    -- max 6 = the ASSAULT cap (all other gun classes stop at 5; the server
    -- sends the real per-player cap, this is the display ceiling). [tod v9.2]
    -- renamed RESERVE -> SCAVENGER (user 2026-08-22); internal key + card slug
    -- stay "reserve", so the art FILENAMES are unchanged. The art itself was
    -- re-baked and does say SCAVENGER (verified 2026-08-23) — do not rename the
    -- files to match the label; the slug is the contract with the zone list.
    [8]  = { name = "SCAVENGER", desc = "REMOVED 2026-10-05", max = 5 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    -- 9 MOBILITY: max 10 -> 5 (v14.11, user 2026-08-30). Display ceiling only;
    -- the server sends the real cap in every sync/deal.
    -- 9 MOBILITY: domain RETIRED v15 (2026-08-31) — the heavy trades it for a
    -- higher base speed (0.75 -> 0.80) plus FULL STEAM (42). Row KEPT, like the
    -- 11/12/22/30/34 pattern: these tables are id-keyed and a fresh run can
    -- never own it, so the entry is inert.
    [9]  = { name = "INVISIBILITY CLOAK", desc = "earn the cloak on tactical: enemies lose you and nothing hurts you; longer and more often", face = { "CLOAK ON YOUR TACTICAL", "UNSEEN AND UNHARMED" }, max = 9 },   -- CLASS PASS 2 (2026-09-27): the NECROMANCER tactical, reuses JUGGERNAUT's id (retired the same day); text card + text row (CoD.TodTextPlate)
    [10] = { name = "PACK MASTER", desc = "helpers hit elites harder; faster hound bites at Lv3, a faster Mangler cannon at Lv6, thralls burst when they fall at Lv9", max = 9 },   -- 2026-09-27 CLASS BUILD CARD (_tod_class_cards); reuses a retired id; text card + text row (CoD.TodTextPlate) until art
    [11] = { name = "ECHO ROUNDS", desc = "+10%/Lv chance to strike twice",      max = 10 },
    -- 12 REGEN: DOMAIN REMOVED v14.11 (2026-08-30, with 22/30/34). The row
    -- stays because this table is keyed by id — the server can no longer send
    -- 12. The heavy's sustain is VITALITY (38) + RECOVERY (39) now.
    -- ⚠️ THIS LINE SAID "with 11/22/30/34" UNTIL 2026-09-11 AND IT COST A
    -- SESSION. Id 11 is ECHO ROUNDS and it was REMOVED 2026-08-23 (v9.35), a
    -- week before v14.11 — see :558 below, which has always had it right, and
    -- the `// Was:` block in _tod_upgrades.gsc. A v18.85 copy fix read THIS
    -- line, believed it, and wrote "retired in v14.11" into five places
    -- including the CHANGELOG and a shipped art brief. Two lines in one file
    -- disagreeing is worse than neither being here: when a retirement date
    -- matters, read the domain's OWN `// Was:` block in the GSC.
    [12] = { name = "DEMON SLAYER", desc = "killing an elite heals you a little and makes you faster and hit harder for a while; lasts longer at Lv3, Lv6 and Lv9", face = { "ELITE KILLS POWER YOU UP", "LASTS LONGER AT LV3 / 6 / 9" }, max = 9 },   -- 9 levels + a heal 2026-09-28 (user; it was 6 for an hour)   -- CLASS PASS 2 (2026-09-27): the WARRIOR, reuses EXECUTIONER's id; text card + text row (CoD.TodTextPlate)
    [13] = { name = "LEECH",       desc = "blade kills heal you (+1 stage)",     max = 5 },
    -- 14 CLEAVE: max 6 -> 3 (v14.11 — "too OP"; one banked extra now).
    [14] = { name = "CLEAVE",      desc = "+33%/Lv chance for an extra zombie",  max = 3 },
    -- 15 v18.85 (2026-09-11): "truly fires faster per level" lost the word
    -- TRULY. It was contrasting this domain with ECHO ROUNDS (11), REMOVED
    -- 2026-08-23 (v9.35) — see :558 in this file, and the `// Was:` block in
    -- _tod_upgrades.gsc — so it had been contrasting nothing for 19 days and
    -- players read it as filler. LOCKSTEP with the add_domain string and the
    -- baked i_tod_card_fire_rate_* value plates (docs/134).
    -- ⚠️ This comment first shipped saying "retired in v14.11, for a month",
    -- copied from :272 below, which is the one line in this file that gets
    -- that date wrong. Read :558, not :272.
    [15] = { name = "FIRE RATE", desc = "REMOVED 2026-10-05", max = 3 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    [16] = { name = "HANDLING", desc = "REMOVED 2026-10-05", max = 3 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    -- 17 v9.45: TWO levels now (-10/-20% since the 2026-08-26 assault buff). max here is the display ceiling for
    -- the pips/level line; the real cap is add_domain's, and the generator's
    -- AXIS.r decides which weapon forms exist. All three say 2.
    [17] = { name = "SOUL SIPHON", desc = "REMOVED 2026-10-05", max = 9 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    [18] = { name = "MELEE SPEED", desc = "retired - folded into HEAVY HANDS", max = 5 },   -- RETIRED 2026-09-27 into HEAVY HANDS (id 7); nil-safe row
    [19] = { name = "SUMMONER MASTER", desc = "kills by your helpers raise your max health while you are at full health; a higher cap per level and per tier", face = { "HELPER KILLS AT FULL HEALTH", "RAISE YOUR MAX HEALTH" }, max = 9 },   -- CLASS PASS 2 (2026-09-27): the NECROMANCER, reuses BURNED OUT's id (Burned Out is the class passive now); text card + text row (CoD.TodTextPlate)
    [20] = { name = "THOR'S THUNDER", desc = "melee hits call lightning on the 2-6 nearest zombies, bigger and more often per level", max = 5 },
    -- 21 SPRINT FIRE: card art installed + zoned 2026-08-22 (files (26).zip),
    -- CARD_SLUG[21] = "sprint_fire". This row is the no-art fallback text.
    [21] = { name = "SPRINT FIRE", desc = "REMOVED 2026-10-05", max = 1 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    -- 22 CHAIN LUNGE: DOMAIN REMOVED 2026-08-24 (user: "it doesnt work"). The
    -- row stays for the same reason 11 and 30 do — this table is keyed by id,
    -- the server can no longer send 22, and deleting it would gain nothing.
    -- CARD_SLUG[22] and the three i_tod_card_chain_lunge_* zone lines ARE gone:
    -- an unreachable art slug is dead weight in the .ff, unlike a Lua row.
    [22] = { name = "CHAIN LUNGE", desc = "REMOVED 2026-08-24", max = 5 },
    -- 23 RUN AND GUN (2026-08-22, skirmisher): baked art installed + zoned
    -- (files (28).zip) -> CARD_SLUG[23] = "run_and_gun"; this row is the
    -- no-art fallback text.
    -- 23 v14.11: gained the DAMAGE half (same ladder, same movement test).
    -- 23 v16.36: REQUIRES SPRINT FIRE (id 21) — server-side prerequisite in _tod_upgrades set_requires; the card never rolls before it is owned, so no text change here.
    -- 23 v16.50: FIVE levels on a stage table, 16 / 28 / 38 / 46 / 52% (was 20/35/50 over 3). LOCKSTEP: TOD_RNG_PCT_L* / TOD_UPG_RNG_DMG_L* / DETAIL[23].
    [23] = { name = "RUN AND GUN", desc = "REMOVED 2026-10-05", max = 5 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    -- CLASS TIERS (docs/25, 2026-08-22). The domain-id fields are 6 bits now.
    -- 24 is the TIER card: its "level" field carries (class-1)*2 + (tier-2),
    -- and PaintCard rewrites name/desc from TIER_LADDER below. 25..31 are the
    -- per-gun uniques — baked art landed 2026-08-22 (CARD_SLUG[25..31]); these
    -- rows are the no-art fallback text + the pause-menu names.
    [24] = { name = "CLASS TIER",       desc = "promote your class: a new weapon, UNPACKED; every upgrade card stays", max = 3 },   -- 2026-09-29: "gun upgrades reset" was false - no live card is gun-scoped (docs/193)
    [25] = { name = "ADRENALINE",       desc = "3 quick explosive kills heal you and give a 3 sec burst of speed and damage; more of each and a shorter cooldown per level", face = { "3 QUICK EXPLOSIVE KILLS", "HEAL AND SPEED BURST" }, max = 9 },   -- explosive kills only since 2026-09-27 (class pass 2)
    [26] = { name = "PIERCING", desc = "arrows and bolts go through zombies: pierced hits land harder; one more zombie at Lv3, Lv6 and Lv9", face = { "ARROWS GO THROUGH ZOMBIES", "+1 ZOMBIE AT LV3 / 6 / 9" }, max = 9 },   -- 2026-09-27 CLASS PASS 3 (user): PIERCING (Archer; _tod_class_cards::pierce) reuses HUNTER'S MARK's id; text card + text row (CoD.TodTextPlate)
    -- 27 KILL RELOAD: DOMAIN REMOVED 2026-09-01 (user: "No one likes it").
    -- Row kept for the same reason 11/12/22/28/30/32/34 are: this table is keyed
    -- by id and the server can no longer send 27. CARD_SLUG[27] and its three
    -- zone lines ARE gone (the IMPACT ROUNDS form) — the PNGs stay in source_data.
    [27] = { name = "KILL RELOAD",      desc = "REMOVED 2026-09-01", max = 3 },
    -- 28 v9.45: TEN levels at 3% each (was 3 levels at 10%) — same 30% ceiling,
    -- a much longer climb to it.
    -- 28 IMPACT ROUNDS: DOMAIN REMOVED 2026-08-31 (user: "No one likes it").
    -- Row kept for the same reason 11/12/22/30/34 are: this table is keyed by
    -- id and the server can no longer send 28. CARD_SLUG[28] and its three
    -- zone lines ARE gone (the CHAIN LUNGE form) — unreachable art is dead
    -- weight in the .ff, a Lua row is not.
    [28] = { name = "IMPACT ROUNDS",    desc = "REMOVED 2026-08-31", max = 10 },
    [29] = { name = "SPRINT", desc = "sprint faster", face = { "SPRINT FASTER" }, max = 9 },   -- CLASS PASS 2 (2026-09-27): the ARCHER, key "sprint" moved 5 -> 29 (AERIALIST retired the same day); counts only while sprinting; text card + text row (CoD.TodTextPlate)
    [30] = { name = "MEAT GRINDER",     desc = "keep firing, hit harder: up to +50 / +75 / +100%", max = 3 },
    -- [31] MELEE RANGE RETIRED 2026-09-28 (user: "move melee range upgrade inside of arms specialist"); its reach is ARMS SPECIALIST [7]. Was: [31] = { name = "MELEE RANGE",      desc = "your swings reach further: a swing that misses hits the nearest zombie in reach, and CLEAVE's extra hits reach further too", max = 6 },   -- 2026-09-26: reuses DRAW CUT's id (docs/upgrade_ids.md); max 5 -> 6 CLASS PASS 2 (2026-09-27)
    -- 32 SPRINT ARMOR (2026-08-23, skirmisher + slasher): baked art installed
    -- + zoned the same day (files (32).zip, docs/29) -> CARD_SLUG[32] =
    -- "sprint_armor", pause plate r32; this row is the no-art fallback text.
    -- 32 SPRINT ARMOR: DOMAIN REMOVED 2026-08-31 (user: "Retire sprint armor
    -- entirely"). Row kept — id-keyed table, server can no longer send 32.
    -- CARD_SLUG[32] and its three zone lines ARE gone (CHAIN LUNGE form).
    [32] = { name = "SPRINT ARMOR",     desc = "REMOVED 2026-08-31", max = 5 },
    -- 33 SECOND WIND / 34 MOMENTUM (2026-08-23): the MP7's replacement unique
    -- and a new skirmisher class domain. Card art AND pause plates are both
    -- installed + zoned (i_tod_card_second_wind_*, i_tod_card_momentum_*,
    -- i_tod_pause_r33/r34), CARD_SLUG[33]/[34] are set, and PAUSE_PLATE_MAX is
    -- 34 — so these render as full art rows, not text. These rows are the
    -- no-art fallback text.
    -- 33 SECOND WIND is the MP5's unique since v14.11 (was the MP7's).
    [33] = { name = "SECOND WIND", desc = "REMOVED 2026-10-05", max = 5 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    -- 34 MOMENTUM: DOMAIN REMOVED v14.11 (2026-08-30) — RUN AND GUN's damage
    -- half is the moving-damage card now. Row kept, id-keyed table.
    [34] = { name = "MOMENTUM",         desc = "REMOVED 2026-08-30", max = 5 },
    -- 35 GIANT SLAYER / 36 BACK ARMOR (2026-08-23, v9.45). Card art AND pause
    -- plates installed + zoned the same day (files (38).zip, docs/31) ->
    -- CARD_SLUG[35]/[36] set, PAUSE_PLATE_MAX 36. These rows are the no-art
    -- fallback text and the pause-menu names.
    [35] = { name = "QUICK DRAW", desc = "draw, shoot and reload faster, and arrows fly faster; 3 times as fast at Lv9, an almost automatic bow", face = { "DRAW AND SHOOT FASTER", "ALMOST AUTOMATIC AT LV9" }, max = 9 },   -- 2026-09-27 class pass 4 (user): SHOT SPEED (Archer) reuses SHADOWSTEP's id; 2026-09-28 retune (x2 at max, arrow velocity, steps at 2/4/6); text card + text row (CoD.TodTextPlate); 2026-10-05 THE AUTOMATIC BOW: x3 at Lv9 (user: "when it's maxed out it almost becomes an automatic bow"). LOCKSTEP _tod_upgrades add_domain desc
    [36] = { name = "EXPLOSIVE FUSION", desc = "your C4 and Cluster explosions heal you when you stand in them, and jumping as your Cluster bursts launches you high into the air", face = { "YOUR BLASTS HEAL YOU", "JUMP + CLUSTER LAUNCHES YOU" }, max = 9 },   -- 2026-09-29 (user): the launch needs a jump; the burst pushes you away from it   -- CLASS PASS 2 (2026-09-27): the BREACHER, reuses POINT BLANK's id (retired the same day); text card + text row (CoD.TodTextPlate)
    -- 37 FORCED MARCH (2026-08-24, assault / FIRE BOW only). Card art + pause
    -- plate installed + zoned the same day (files (39).zip, docs/33) ->
    -- CARD_SLUG[37] = "march", PAUSE_PLATE_MAX = 37. This row is the no-art
    -- fallback text.
    [37] = { name = "VITALITY", desc = "more max health: +10 at Lv1, a little less each level after (+57 at Lv9)", face = { "MORE MAX HEALTH", "+57 AT LV9" }, max = 9 },   -- 6 -> 9 levels 2026-09-28 (user)   -- CLASS PASS 2 (2026-09-27): the WARRIOR, key "vitality" moved 38 -> 37 (DEMOLITIONIST retired the same day); text card + text row (CoD.TodTextPlate)
    -- 38 VITALITY / 39 RECOVERY (v14.11, 2026-08-30 — the heavy's new sustain
    -- pair, replacing REGEN). NO card art or pause plates yet: these render
    -- through the no-art text fallback (PaintCard's nil-slug branch) and as
    -- text rows in the pause list (38 > PAUSE_PLATE_MAX). When the art drop
    -- lands: add CARD_SLUG[38]/[39], bump PAUSE_PLATE_MAX to 39, install +
    -- zone the images — the v14.11 art prompt doc carries the checklist.
    -- 38 / 39 REUSED 2026-09-26 by the NECROMANCER (VITALITY / RECOVERY were cut
    -- with the Breacher's cards the same day; docs/upgrade_ids.md). New keys
    -- summonpower / soulbeam; no card art yet (text fallback, TodTextPlate).
    [38] = { name = "SUMMONING POWER",  desc = "faster binds, longer-lived helpers that hit elites harder; a helper slot at Lv3 and Lv6, a 2nd Mangler at Lv9", face = { "FASTER STRONGER HELPERS", "MORE HELPERS AT LV3 / 6 / 9" }, max = 9 },
    [39] = { name = "SOUL SUCK",        desc = "Soul Suck hits harder and costs less; one more soul at once and a faster soul-rip at Lv3, Lv6 and Lv9", face = { "SOUL SUCK HITS HARDER", "+1 SOUL AT LV3 / 6 / 9" }, max = 9 },   -- 2026-09-27: the NECROMANCER CORE WEAPON card, 5 -> 9; renamed SOUL BEAM -> SOUL SUCK (CLASS PASS 2 (2026-09-27); the old card art bakes SOUL BEAM, so it draws as text)
    -- 40 PERK SLOTS: RETIRED AGAIN 2026-09-27 (user: "no perk limit on this map").
    -- No add_domain, so no deal can roll it; the id stays reserved. Row kept nil-safe.
    [40] = { name = "PERK SLOTS",       desc = "retired - the map has no perk limit", max = 5 },
    -- 41 DISTRACTION (v14.59; reshaped v16.49) - the assault's Cymbal Monkey.
    -- The LEVEL IS THE CARRY CAP: Lv1 holds 1, Lv2 holds 2, Lv3 holds 3; MAX
    -- AMMO adds +1 at every level. (The Lv2 Li'l Arnies swap is gone.)
    -- Art landed 2026-09-01 (files (78).zip, docs/54) and is re-baked for 3
    -- pips under docs/75: CARD_SLUG[41] is set and i_tod_pause_r41 is
    -- installed + zoned, so this row is the desc fallback only, never what a
    -- player actually sees. LOCKSTEP max 3: add_domain / TOD_DISTRACT_MAX_CARRY.
    [41] = { name = "GRAPPLE",          desc = "longer grapple; landing gives a burst of speed and less damage", face = { "LONGER GRAPPLE", "LANDING SPEED AND ARMOR BURST" }, max = 9 },   -- 9 levels on ln(1+l)/ln(10) since 2026-09-27, LOCKSTEP _tod_archer.gsc grapple_curve + TOD_ARCHER_LAND_*
    -- 57 HELL'S RETRIEVER (2026-09-26): the Archer's lethal is earned by this
    -- card. No card art yet: this row IS the card (text fallback, like 41).
    -- LOCKSTEP max 8: add_domain / TOD_RET_MAX_LV in _tod_retriever.gsc.
    [57] = { name = "HELL'S RETRIEVER", desc = "throwing axe that chains and returns; more damage; another stored throw at Lv3, Lv6 and Lv9", face = { "THROWING AXE THAT RETURNS", "+1 THROW AT LV3 / 6 / 9" }, max = 9 },
    -- 58..61 THE BREACHER'S CARDS (2026-09-26). Text fallback (no card art yet).
    -- LOCKSTEP names/max with add_domain in _tod_upgrades.gsc; pellet counts with
    -- gen_tod_twins.js gun.pellets; C4 / CLUSTER max 9 with TOD_C4_MAX_LV / TOD_CLUSTER_MAX_LV. (59 EXPLOSIVES cut 2026-09-26.)
    [58] = { name = "BUCKSHOT",         desc = "your shotguns hit harder; more pellets at Lv3, Lv6 and Lv9", face = { "YOUR SHOTGUNS HIT HARDER", "MORE PELLETS AT LV3 / 6 / 9" }, max = 9 },   -- 2026-09-27: the BREACHER CORE WEAPON card (PELLETS folded in; text card + text row, TodTextPlate)
    [59] = { name = "SOUL PULSE",       desc = "charges on a smaller share of the round's zombies and hits elites harder; a wider pulse at Lv3, Lv6 and Lv9", face = { "CHARGES FASTER HITS HARDER", "WIDER PULSE AT LV3 / 6 / 9" }, max = 9 },
    [60] = { name = "STICKY C4",        desc = "earn the sticky C4: more damage; another charge per round and a bigger blast at Lv3, Lv6 and Lv9", face = { "STICKY C4 HITS HARDER", "+1 CHARGE AT LV3 / 6 / 9" }, max = 9 },
    [61] = { name = "CLUSTER",          desc = "earn the Cluster grenade: more damage; a bomblet layer at Lv3, a layer, a 2nd grenade and bigger blasts at Lv6, a 3rd grenade and bigger blasts at Lv9", face = { "CLUSTER HITS HARDER", "MORE BOMBLETS AT LV3 / 6 / 9" }, max = 9 },
    -- 62 BASH / 63 CYBER SMASH (key gravsmash; GRAVITY SMASH until build 16, user
    -- 2026-09-26: "Gravity Smash, we're going to transition that over to Cyber Smash"):
    -- the Warrior's tactical and lethal,
    -- Hellbound's 8-level ladders. Text fallback (no card art yet).
    -- LOCKSTEP max 8: add_domain / TOD_BASH_MAX_LV / TOD_GS_MAX_LV in _tod_class_kit.gsc.
    -- W3E 2026-10-05: BASH is a dash with whatever the Warrior holds - the fists, the
    -- gauntlet or the sword (_tod_class_kit bash proxies) - so it never says "blade".
    [62] = { name = "BASH",             desc = "dash and strike: hits harder and recharges faster; a 2nd dash at Lv3, a 3rd at Lv6, a wider burst at Lv9", face = { "DASH AND STRIKE", "+1 DASH AT LV3 AND LV6" }, max = 9 },
    [63] = { name = "CYBER SMASH",      desc = "fewer kills to charge and a bigger hit on elites; a longer elite stun at Lv3, Lv6 and Lv9", face = { "CHARGES FASTER HITS HARDER", "LONGER STUN AT LV3 / 6 / 9" }, max = 9 },
    -- FULL STEAM (v15 item 24) — the heavy's MOBILITY replacement. Art landed
    -- 2026-09-01 (files (78).zip, docs/56): CARD_SLUG[42] is set, so this row is
    -- the desc fallback only. The three cards were RE-BAKED 2026-09-01 (files
    -- (81).zip) and now read "KEEP SPRINTING FOR SPEED" — no number, so the
    -- 1.5s -> 1.0s retune that made the old art wrong cannot recur. This card
    -- set is the reason the no-numbers rule exists: it was the one card in the
    -- v15 pass that baked a value, and it went stale within hours.
    [42] = { name = "BULWARK", desc = "take less damage while 3+ zombies are close; a bigger step at Lv3, Lv6 and Lv9", max = 9 },   -- 2026-09-27 CLASS BUILD CARD (_tod_class_cards); reuses a retired id; text card + text row (CoD.TodTextPlate) until art
    -- ATHLETE (v16, 2026-09-01) — the slasher gets its mobility card back, in
    -- the hole the retired chain lunge (22) left. Art landed the SAME DAY
    -- (files (79).zip, docs/57): CARD_SLUG[43] is set and PAUSE_PLATE_MAX is 43,
    -- so this row is now the desc fallback only, never what a player sees.
    [43] = { name = "ATHLETE",          desc = "slide faster, jump higher, steer in the air, wall-run", max = 5 },   -- v16.23: air steering added; v16.34: wall-run (2026-09-02)
    -- 44 GUNSLINGER (v16.51, 2026-09-02) — the slasher's sidearm vs bosses and
    -- elites: +30%/Lv on top of the class's 2.25x baseline. Art landed the
    -- same day (v16.54, docs/79): CARD_SLUG[44] is set and i_tod_pause_r44 is
    -- installed + zoned, so this row is the desc fallback only. LOCKSTEP:
    -- TOD_UPG_GUNSLINGER_PER_LVL in _tod_upgrades.gsc.
    [44] = { name = "GUNSLINGER",       desc = "+30% sidearm damage to bosses and elites per level", max = 5 },
    -- 46 TRAILBLAZER (v16.62, docs/80): text fallback only until the art lands (45 went to RIOT SHIELD the same day).
    [46] = { name = "TRAILBLAZER", desc = "REMOVED 2026-10-05", max = 5 },   -- parked card RETIRED WHOLE 2026-10-05 (W2E): no add_domain, no lane; nil-safe id-keyed row
    -- 45 RIOT SHIELD (v16.63, 2026-09-02) — UNIVERSAL: a riot shield every
    -- class carries; each level adds shield HP and shortens the recharge that
    -- hands it back after it breaks (200..500 HP, 4:00..2:00). Art PENDING
    -- (docs/82) LANDED 2026-09-03: CARD_SLUG[45] is set and i_tod_pause_r45 is
    -- installed + zoned, so this row is the desc fallback only. LOCKSTEP: SHIELD_HP /
    -- SHIELD_RECHARGE above, TOD_SHIELD_* in _tod_riotshield.gsc.
    [45] = { name = "RIOT SHIELD",      desc = "earn a riot shield that recharges after it breaks; tougher and faster each level, the cyber shield at Lv9", face = { "A SHIELD THAT RECHARGES", "CYBER SHIELD AT LV9" }, max = 9 },   -- BREACHER ONLY, 9 levels since 2026-09-28 (user)
    -- 47 DEADSHOT (v16.64, 2026-09-02) — ASSAULT, max 1, ALWAYS an ULTIMATE card
    -- (server-side rarity lock): permanent head-snap aim assist (controller),
    -- perk-bar crest, no perk slot. Art PENDING (docs/84, ONE card):
    -- CARD_SLUG[47] unset, so this row IS the card until the drop lands.
    [47] = { name = "DEADSHOT",         desc = "aim bot: your aim locks onto zombie heads", max = 1 },
    [48] = { name = "CLEAVE", desc = "your swings hit more zombies; always 2 at Lv3, 3 at Lv6, 4 at Lv9", face = { "SWINGS HIT MORE ZOMBIES", "UP TO 4 AT LV9" }, max = 9 },   -- 2026-09-27 class pass 4 (user): CLEAVE (Warrior, key sweep) reuses BATTLE RHYTHM's id; text card + text row (CoD.TodTextPlate)
    -- 11 ECHO ROUNDS and 30 MEAT GRINDER were REMOVED 2026-08-23. Their rows
    -- stay because this table is keyed by id, not ordered — a stale row is
    -- never reachable (the server can no longer send those ids) and deleting
    -- one would gain nothing while risking the ids around it.
}

-- The TIER card (id 24): class id -> the gun each promotion hands out. Class
-- ids mirror tod_class_select.lua / _tod_class_select.gsc::class_key. Pure
-- client-side strings (zero config-string cost); the baked tier-card art
-- replaces this text once USE_TIER_CARD_ART flips.
local TIER_DOMAIN = 24
-- the tier-card class keys, [class id] = key (file scope: the tier art and THE PULL's
-- card-v2 tier illustrations both read it). [1] NECROMANCER tier cards installed
-- 2026-09-26 (docs/179: SOUL HOUNDS / THE MANGLER).
local TOD_TCLS = { "necromancer", "assault", "heavy", "slasher" }

local TIER_LADDER = {
    -- W3E 2026-10-05: the Necromancer's promotions hand out weapons like every other class's
    -- (2026-09-27: _tod_classes register_gun tier 2 tod_necro_staff2 "Soul Staff", tier 3
    -- tod_necro_staff3 "Crown of the Damned"), and the tier cards' pictures are those staffs
    -- (r2_card_subjects, 2026-10-04). The summons still grow with the tier; the card names the weapon.
    [1] = { class = "NECROMANCER", [2] = "SOUL STAFF", [3] = "CROWN OF THE DAMNED" },
    [2] = { class = "ARCHER",    [2] = "R1 SHADOWHUNTER", [3] = "FIRE BOW" },
    [3] = { class = "BREACHER",   [2] = "REMINGTON 870", [3] = "PEACEKEEPER" },   -- TOD II (docs/157)
    [4] = { class = "WARRIOR",    [2] = "GAUNTLET OF SIEGFRIED", [3] = "CYBER SWORD" },   -- 2026-09-26: tier 2 is the Dragon Gauntlet (the Warrior swap)
}

local MAX_LEVEL = 10

-- ---------------------------------------------------------------------------
-- [tod] UPGRADE DETAIL — what each upgrade does, and how it activates.
-- (user 2026-08-23: players forget or never learn what a domain actually does,
-- so the pause menu's YOUR UPGRADES panel now prints these two lines under
-- every owned row.)
--
-- Every entry below was read back off the ACTUAL apply hook in
-- scripts/zm/zm_tod2_cybercity/*.gsc, NOT off the add_domain() desc string and
-- NOT off DOMAIN.desc above — several of those are stale or imprecise. Each
-- was then adversarially re-verified against the code a second time. If you
-- change a domain's numbers in GSC, change `val` here in the SAME commit: the
-- panel prints the value at the player's CURRENT level, so a drifted formula
-- lies to the player instead of merely reading oddly.
--
--   eff  effect line. "{V}" is replaced by val( lvl ), formatted to `dec`
--        decimal places. Omit val for a domain that has no number.
--   act  activation line — the TRIGGER, plus any window / cooldown / chance /
--        stack cap. LEAVE IT "" for a pure passive — a sub-line reading
--        "always on" was on 16 of 38 rows and taught nothing (user
--        2026-09-03: make it clear, cut unnecessary words). Only write an
--        act line when there IS a restriction or a trigger.
--   dec  decimal places for the substituted value (default 0).
--
-- HARD LIMITS. There is NO text-measurement and NO wrap API in this LUI build
-- (verified repo-wide: zero uses of setFontSize/setWrap/getTextWidth) — a long
-- line cannot be measured or broken at runtime, it just overflows the column
-- into the next one. Keep eff <= 40 chars WITH the value substituted and
-- act <= 44 chars. The column is 344px; orbitron at these scales runs about
-- 6.8px/char, so 44 chars is ~300px and leaves margin.
-- ---------------------------------------------------------------------------
-- the Necromancer damage curve (2026-09-28): ln( 1 + lvl ) / ln( 10 ), 0 at Lv0 and 1 at Lv9.
-- LOCKSTEP _tod_necro_summon::card_curve (index = level).
-- THE CLASS HEADER (2026-09-28): the class name, its PASSIVE and its TIER, drawn by BOTH the pause
-- menu and the scoreboard beside the ROUND box. ONE SOURCE (it lived in AetheriumStartMenu.lua as
-- TOD_CLASS_INFO until today). Keyed by _tod_classes class_id (1 Necromancer, 2 Archer, 3 Breacher,
-- 4 Warrior), read from CoD.TodClass. LOCKSTEP the passives in _tod_class_cards.gsc /
-- _tod_upgrades.gsc / _tod_necro_skull.gsc. No "%" in these lines: the menu face draws it like "7.".
CoD.TodClassInfo = {
    [1] = { name = "NECROMANCER", passive = { "SOUL METER REFILLS ITSELF", "WIDOW'S WINE GIVES BURNED OUT" } },
    [2] = { name = "ARCHER",      passive = { "SHOOT WHILE SPRINTING", "NO SLOWDOWN WHEN YOU LAND" } },
    [3] = { name = "BREACHER",    passive = { "TAKES NO EXPLOSIVE DAMAGE", "STEERS IN THE AIR" } },   -- 2026-09-29 (user): air steering, map 1's Slasher style (_tod_class_kit breacher_air_steer)
    [4] = { name = "WARRIOR",     passive = { "HEALS 2 PERCENT HEALTH", "EVERY SECOND" } },
}
-- The tier line: the CLASS TIER row's level (sent from tier 2 on; absent = tier 1) and what the
-- next promotion needs, taken from that row's own act text (DETAIL[24]) so the floors stay
-- LOCKSTEP with tier_floor_ok. Returns "TIER 2 OF 3", "NEXT: PAP + FLOOR 20" (or "FINAL TIER").
CoD.TodClassTierLines = function()
    local row = ( CoD.TodOwned or {} )[ 24 ]
    local tier = ( row and row.lvl and row.lvl >= 1 ) and row.lvl or 1
    local tierMax = ( row and row.max and row.max >= 1 ) and row.max or 3
    local nextLine = "FINAL TIER"
    if tier < tierMax then
        nextLine = ""
        if CoD.TodDomainDesc then
            local _, act = CoD.TodDomainDesc( 24, tier )
            local floor = act and string.match( act, "floor (%d+)" )
            if floor then nextLine = "NEXT: PAP + FLOOR " .. floor end   -- PAP stays SHORT here on purpose (W3E 2026-10-05, measured): "NEXT: PACK-A-PUNCH + FLOOR 20" runs into the class name beside it ("NECROMANCER", "BREACHER") in both the pause menu and the scoreboard
        end
    end
    return "TIER " .. tier .. " OF " .. tierMax, nextLine
end

local CARD_CURVE = { [0] = 0, 0.301, 0.4771, 0.6021, 0.699, 0.7782, 0.8451, 0.9031, 0.9542, 1 }
local DETAIL = {
    [1]  = { eff = "retired", act = "", val = function( l ) return l end },   -- DAMAGE retired 2026-09-27
    [2]  = { eff = "-{V}% damage taken",                  act = ""          ,                                  val = function( l ) return drPct( l ) end },   -- v16: flat 5*l -> the 6/11/15/18/20 ladder
    -- 3, 6, 8, 25, 27, 29, 35: the "class gun only" wording is GONE from all
    -- seven (audit 2026-08-24). The 2026-08-23 widening put every weapon on one
    -- damage lane and un-gated on_class_gun_kill, so these lines had been
    -- describing a restriction the code stopped enforcing. LEECH (13) keeps its
    -- gate and its wording; the TWIN domains (15/16/17/19) really are class-gun
    -- only, because the variant forms only exist for that gun.
    -- v18.9: "paid out every 10s" read as a ten-second TIMER, next to seven rows
    -- where s means seconds. There is no timer - it banks and pays on the kill in
    -- whole tens of points. "whole 10s" was rejected for keeping the same
    -- ambiguous token.
    [3]  = { eff = "+{V}% points on every kill",          act = "banked, paid in 10-point steps",  val = function( l ) return log9Pct( l ) end },   -- BOUNTY log, +100% at Lv9 (2026-09-28)
    -- v18.9: the act line now says what the BAR IS FOR. Every in-game surface
    -- that named luck was circular - this row explained how to raise it, the HUD
    -- art says "LUCK", the deal badge says "LUCK 60% BOOSTED" and stops one noun
    -- short - so the only place the payoff was ever written was the Steam page.
    -- A player asked outright in the Workshop comments on 2026-09-06. The
    -- 100-150 overcharge band stays secret, deliberately.
    [4]  = { eff = "+{V}% luck bar gain",                 act = "a fuller bar deals rarer cards",   val = function( l ) return log9Pct( l ) end },   -- LUCK log, +100% at Lv9 (2026-09-28)
    -- [tod] 2026-08-26: the "lv5+ tireless (skirmisher)" rider is GONE — the
    -- unlimited-sprint grant was removed after three failed attempts to make the
    -- meter actually stop draining. SPRINT is move speed only, for both classes.
    [5]  = { eff = "{V}", act = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) if b == 0 then return "a wider beam at Lv3, Lv6 and Lv9" end return "wider beam: step " .. b .. " of 3" end, val = function( l ) return "+" .. ( 4 * math.max( l, 0 ) ) .. "% beam reach" end },   -- 2026-09-27 CLASS BUILD CARD. LOCKSTEP _tod_class_cards / the class module
    [6]  = { eff = "{V}", act = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) return "arrows " .. ({ "normal width", "wider", "wider still", "widest" })[ b + 1 ] end, val = function( l ) return "+" .. ( 7 * math.max( l, 0 ) ) .. "% bow damage" end },   -- DEADEYE (2026-09-27 class pass 4 (user): shot speed moved to SHOT SPEED). LOCKSTEP TOD_CORE_DMG_ARCHER 0.07 / gen_tod_twins AXIS.d girth
    [7]  = { eff = "{V}", act = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) return "swings " .. ({ 0, 15, 24, 30 })[ b + 1 ] .. "% faster" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "+" .. ( 7 * L ) .. "% damage, +" .. ( 10 * L ) .. "% reach" end },   -- ARMS SPECIALIST. LOCKSTEP TOD_CORE_DMG_WARRIOR 0.07 / axis_level k2 / k4 / k5 / _tod_warrior_melee TOD_WM_RANGE_STEP 0.10 (2026-09-28)
    -- [tod] v16.42 (2026-09-02) the user's KILLS-PER-ROUND ladder. Mirrors GSC
    -- scav_kills10 (TOD_SCAV_KILLS10_*, which holds these x10 as tenths):
    -- Lv1..Lv6 = 2.8 / 2.3 / 2 / 1.8 / 1.6 / 1.4 — LOCKSTEP with the GSC table,
    -- change both. (v16.41 4/2.9/2.3/2.0/1.9/1.8 and v16.40 5/3.3/2.6/2.3/2.1/
    -- 1.9 each lasted one build; 2026-08-26 → v16.39 was 1 per 5/4/3/2/1 and
    -- 3 per 2 at Lv6.)
    -- val returns a whole PHRASE rather than a number (the formatter above
    -- tostring()s any non-number, so this is supported): the kills-per-round
    -- reading is the one the user thinks in ("1 bullet every N kills").
    -- 8 SCAVENGER: RETIRED WHOLE 2026-10-05 (W2E, a parked card). The notes above are its history.
    [8]  = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },
        -- =======================================================================
    -- ⚠️ KEEP THESE SHORT. THE PANEL DOES NOT WRAP, IT OVERLAPS.
    -- User 2026-09-03, with a screenshot: *"Looks how horrible it is. We need
    -- to remember that this has to be short and concise. This has happened
    -- multiple times where our description is super long and overlaps"* — and
    -- it HAD, repeatedly, because every new domain wrote its row without ever
    -- seeing the panel full.
    --
    -- THE BUDGET, measured off AetheriumStartMenu's real rows: the column is
    -- COL_W 369 with eff at scale 0.90 and act at 0.79, so roughly
    --     eff <= 40 characters, act <= 46
    -- with {V} counted at its widest substitution. Over that the line runs
    -- past the column and paints on top of the row below.
    --
    -- THE TRAP THAT MADE THIS RECUR: a row whose eff is literally "{V}" hides
    -- its real length inside the val FUNCTION, so eyeballing the table finds
    -- nothing. TRAILBLAZER read 4 characters here and rendered 76 on screen.
    -- tools/lint_tod_lua.js now measures BOTH the literals and the strings
    -- built inside val, and fails the build over budget.
    -- =======================================================================
    -- 9 MOBILITY: RETIRED v15 — unreachable, left inert (see the DOMAIN note).
    [12] = { eff = "{V}", act = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) return "for " .. ( 6 + 2 * b ) .. " sec after an elite kill" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "+" .. ( 5 * L ) .. "% damage, +" .. ( 2 * L ) .. "% speed, heal " .. ( 2 * L ) .. "%" end },   -- DEMON SLAYER. LOCKSTEP _tod_class_cards TOD_DEMON_* (+5% dmg / +2% speed / 2% max-health heal per Lv; 6 s + 2 s at Lv3/6/9)
    [9]  = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 1 ), 9 ) return "^3[{+smoke}]^7 cloaks, every " .. ( 60 - 3 * L ) .. " sec" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) local b = math.min( math.floor( L / 3 ), 3 ) return "cloaked " .. string.format( "%g", ( 3000 + 250 * L + 1000 * b ) / 1000 ) .. " sec, unseen and unharmed" end },   -- INVISIBILITY CLOAK (CLASS PASS 2 (2026-09-27)). LOCKSTEP _tod_class_cards TOD_CLOAK_* (3 s + 0.25 s / Lv + 1 s at Lv3/6/9; 60 s - 3 s / Lv)
    [10] = { eff = "{V}", act = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) local t = { "faster hound bites", "faster Mangler cannon", "thralls burst" } local o = {} for i = 1, b do o[ #o + 1 ] = t[ i ] end if b == 0 then return "more at Lv3, Lv6 and Lv9" end return table.concat( o, ", " ) end, val = function( l ) return "helpers hit elites +" .. ( 10 * math.max( l, 0 ) ) .. "%" end },   -- 2026-09-27 CLASS BUILD CARD. LOCKSTEP _tod_class_cards / the class module
    -- 11 ECHO ROUNDS: domain REMOVED 2026-08-23. No detail row — unreachable.
    -- 12 REGEN: domain REMOVED v14.11 (2026-08-30). No detail row — unreachable
    -- (the 11/22/30 pattern; a fresh run can never own it).
    -- v18.9: the eff still read "per blade kill" after 2026-09-05 made it ONE
    -- heal per swing however many bodies the swing killed, and the empty act line
    -- had nowhere to say so. (A THOR'S THUNDER proc can still take a swing's heal
    -- to zero by stamping tod_no_leech on the primary victim first - that is a
    -- design call, not a copy fix, and is left alone here.)
    [13] = { eff = "heal +{V} hp on a blade kill",        act = "once per swing, not once per body", val = function( l ) return ({0,4,6,8,9,10})[ math.min(l,5) + 1 ] or 10 end },
    -- CLEAVE is NOT a chance: the ladder passes 100% at Lv3 (one guaranteed
    -- extra target) and caps at 200% = +2. The wording must never say "chance".
    -- 14 v14.11: cap 3 — one banked extra at Lv3 (the 200% clamp is dead belt).
    [14] = { eff = "{V}% chance to hit 1 extra zombie",   act = "melee hits, within 60 units",            val = function( l ) local v = math.floor( 100 * l / 3 + 0.5 ) if v > 200 then v = 200 end return v end },
    [15] = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },   -- RETIRED WHOLE 2026-10-05 (W2E, a parked card)
    [16] = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },   -- RETIRED WHOLE 2026-10-05 (W2E, a parked card)
    [17] = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },   -- RETIRED WHOLE 2026-10-05 (W2E, a parked card)
    [18] = { eff = "retired", act = "folded into HEAVY HANDS", val = function( l ) return l end },   -- MELEE SPEED retired 2026-09-27
    -- PENETRATION is a penetrateType TIER, not a number. Lv0 = small (BELOW
    -- stock) but a row only renders at lvl > 0, so index straight by level.
    [19] = { eff = "{V}", act = "+1 max health per helper kill at full health", val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "up to +" .. ( 4 * L ) .. " max health per tier" end },   -- SUMMONER MASTER (CLASS PASS 2 (2026-09-27)). LOCKSTEP _tod_class_cards TOD_SM_* (cap 4 x Lv x class tier)
    -- [tod v16.3] numbers re-read off _tod_upgrades.gsc TOD_THOR_DMG_BASE/PER_LV
    -- (0.04 + 0.12/Lv = 16..64%) and TOD_THOR_CD_MAX/STEP/MIN (4.5s -> 1.5s);
    -- this row had kept the pre-nerf 20-80% / 3.8-1.3s.
    -- v18.9: it never said the strike SKIPS bosses and elites (thor_strike
    -- excludes the boss triad outright - Panzer, Protector, Reaver, hound). The
    -- strike still visibly fires on them, because it is centred on the melee
    -- victim's own origin, so a slasher reading "64% of enemy max hp" reasonably
    -- concluded this was their boss answer. Same omission already fixed on
    -- TRAILBLAZER's row.
    [20] = { eff = "lightning for {V}% of enemy max hp",  act = "Stormbreaker; elites immune; 4.5-1.5s cd",  val = function( l ) return 4 + 12 * l end },
    [21] = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },   -- RETIRED WHOLE 2026-10-05 (W2E, a parked card)
    -- 22 CHAIN LUNGE: domain REMOVED 2026-08-24. No detail row — unreachable.
    -- 23 v14.11: both halves share one number, so one {V} substitution covers
    -- them (string.gsub replaces every occurrence).
    -- 23 v16.50: stage table 16/28/38/46/52 — LOCKSTEP with TOD_RNG_PCT_L1..L5 (_tod_runandgun.gsc) and TOD_UPG_RNG_DMG_L1..L5 (_tod_upgrades.gsc).
    [23] = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },   -- RETIRED WHOLE 2026-10-05 (W2E, a parked card)
    -- 24 CLASS TIER: `lvl` is the plain tier number — refresh_upgrade_list
    -- sends it raw, and since v14.35 it sends it FROM TIER 1 (it used to start
    -- at 2), because this row is now where a player reads what the NEXT
    -- promotion costs. The pause lane does not carry the CLASS, so this line
    -- stays class-agnostic on purpose; naming the gun here would need a new
    -- channel.
    --
    -- `act` IS A FUNCTION HERE — the only row that does that. It states the
    -- requirement for the promotion you have not taken yet, so it has to change
    -- with the level the way `eff` does.
    --
    -- ⚠ LOCKSTEP with GSC TOD_TIER2_FLOOR / TOD_TIER3_FLOOR in
    -- _tod_upgrades.gsc. These floor numbers are the gate's, not this file's —
    -- the client cannot ask the server for them (the clientuimodel pool is at
    -- its 61-bit ceiling), so they are copied, and a change to the gate is not
    -- finished until this line changes with it. Same discipline as RUN AND
    -- GUN's constants across _tod_upgrades / _tod_runandgun.
    [24] = { eff = "your class weapon is tier {V} of 3",
             -- v18.9: the act line stated the REQUIREMENT and never the COST.
             -- Three separate Workshop reports describe the same surprise - the
             -- promotion hands back the next weapon UNPACKED (pap_tier is keyed on
             -- the gun's stem). The card art carries
             -- no warning and the LUI fallback that once did is dead behind
             -- USE_TIER_CARD_ART, so this row and the promotion toast in
             -- _tod_upgrades.gsc are the whole notice.
             -- W3E 2026-10-05: "Pack-a-Punch" in full, as every prompt and toast
             -- spells it, and WEAPON not gun (user: "This map is more weapons
             -- rather than guns"). The "tier N:" prefix went to pay for it inside
             -- the 46-character budget: the eff line above already names the tier,
             -- so this line is the NEXT promotion's price. CoD.TodClassTierLines
             -- reads "floor (%d+)" out of it - keep the word "floor" before the
             -- number. The FLOOR NUMBERS ARE LOCKSTEP with tier_floor_ok - do not
             -- edit them here. [docs/160] under the DESCENT the floors read
             -- 20 / 40 (the same 30 / 10 floors of progress, counted from the crown).
             act = function( l )
                 if l >= 3 then
                     return "final tier"
                 elseif l == 2 then
                     return "Pack-a-Punch + floor " .. tierFloorShown( 30 ) .. "; new weapon unpacked"
                 end
                 return "Pack-a-Punch + floor " .. tierFloorShown( 10 ) .. "; new weapon unpacked"
             end,
             val = function( l ) return l end },
    -- 25 ADRENALINE: THREE effects off ONE number since v17.85 (speed, bullet
    -- damage, and a heal of DOUBLE that % of max health on trigger), so the row
    -- switched from a "+{V}%" template to the composed "{V}" form — the heal is
    -- instant and the other two last 3s, which no single template sentence can
    -- say. LOCKSTEP with adren_bonus() in _tod_upgrades.gsc (lvl *
    -- TOD_ADREN_PCT_PER_LV, +TOD_DARK_ADREN_ADD when dark) and with
    -- adren_cooldown_ms (MAX 20000 - 2000/lv, floor 12000). The heal prints
    -- 6*l because it is adren_bonus() x TOD_ADREN_HEAL_MULT (2.0) -- if that
    -- define moves, this 6 and the dark 50 below move with it.
    [25] = { eff = "{V}",  act = function( l ) return "3 blast kills: 3 sec burst, " .. math.max( 12, 20 - ( l - 1 ) ) .. " sec cooldown" end,            val = function( l ) return "+" .. ( 3 * l ) .. "% speed and damage, heals " .. ( 6 * l ) .. "%" end },
    [26] = { eff = "{V}", act = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) return "goes through " .. ( 1 + b ) .. ( b == 0 and " zombie" or " zombies" ) .. ", 600 units" end, val = function( l ) return "pierced hits deal " .. ( 50 + 5 * math.max( l, 0 ) ) .. "%" end },   -- PIERCING (2026-09-27 CLASS PASS 3 (user)). LOCKSTEP TOD_PIERCE_* in _tod_class_cards.gsc
    -- 27 KILL RELOAD: REMOVED 2026-09-01. Kept as a nil-safe id-keyed row.
    [27] = { eff = "REMOVED", act = "retired 2026-09-01", val = function( l ) return 0 end },
    -- 28 IMPACT ROUNDS: REMOVED 2026-08-31. Kept as a nil-safe id-keyed row.
    [28] = { eff = "REMOVED", act = "retired 2026-08-31", val = function( l ) return 0 end },
    -- 29 SUPPRESSING FIRE nerfed 2026-08-24: 25/40/55 -> 12/24/36, so the val
    -- is a flat 12 per level now (it was 15*l + 10). The CARD ART carries these
    -- numbers baked in and is stale until re-baked — see the art work list.
    [29] = { eff = "+{V}% sprint speed", act = "counts only while you sprint", val = function( l ) return math.floor( 30 * CARD_CURVE[ math.min( math.max( l, 0 ), 9 ) ] + 0.5 ) end },   -- SPRINT (CLASS PASS 2 (2026-09-27), the Archer). LOGARITHMIC since 2026-09-28 (user): 30 x CARD_CURVE = 9 / 14 / 18 / 21 / 23 / 25 / 27 / 29 / 30. LOCKSTEP _tod_upgrades sprint_card_bonus / TOD_SPRINT_CARD_MAX
    -- 30 MEAT GRINDER: domain REMOVED 2026-08-23. No detail row — unreachable.
    -- [31] MELEE RANGE retired 2026-09-28 (folded into [7]). Was: [31] = { eff = "+{V}% melee reach",                   act = "a swing that misses reaches the nearest zombie", val = function( l ) return 15 * math.min( math.max( l, 0 ), 6 ) end },   -- MELEE RANGE 2026-09-26 (was DRAW CUT); 6 levels since CLASS PASS 2 (2026-09-27) (TOD_WM_RANGE_MAX_LV 6)
    -- 32 SPRINT ARMOR: REMOVED 2026-08-31. Nil-safe id-keyed row.
    [32] = { eff = "REMOVED", act = "retired 2026-08-31", val = function( l ) return 0 end },
    [33] = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },   -- RETIRED WHOLE 2026-10-05 (W2E, a parked card)
    -- 34 MOMENTUM: domain REMOVED v14.11 (2026-08-30). No detail row — unreachable.
    -- 35 GIANT SLAYER: the multiplier is ADDITIVE with DAMAGE and HEADSHOT, and
    -- pays out only against the boss/elite triad (Panzer, Rogue Protector,
    -- Reaver) — never on the horde. Both boss-damage lanes call
    -- tod_upgrades::boss_damage_bonus, so there is one number, not two.
    [35] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 0 ), 9 ) local S = { 1, 1, 1.28, 1.28, 1.63, 1.63, 2.08, 2.08, 2.66, 2.66 } local V = { 1, 1, 1.15, 1.15, 1.30, 1.30, 1.45, 1.45, 1.60, 1.60 } return string.format( "draws x%.2f faster, arrows x%.2f", S[ L + 1 ], V[ L + 1 ] ) .. ( ( L % 2 == 1 ) and ", +13% hits" or "" ) end, val = function( l ) local D = { 1, 1.13, 1.28, 1.44, 1.63, 1.84, 2.08, 2.35, 2.66, 3 } return string.format( "x%.2f shot speed", D[ math.min( math.max( l, 0 ), 9 ) + 1 ] ) end },   -- QUICK DRAW 9 levels; 2026-10-05 THE AUTOMATIC BOW (user: maxed = "almost an automatic bow"): x3 at Lv9 on 3^(Lv/9), +13% every level - the weapon steps at Lv2 / 4 / 6 / 8 (S), an odd level's 13% is damage (_tod_archer_bow quickdraw_mult). LOCKSTEP gen_tod_twins SHOTSPEED_STEP / SHOTSPEED_VEL + _tod_archer_bow shot_step + _tod_upgrades axis_level (tools/test_archer_autobow.js)
    -- 36 BACK ARMOR: multiplies AFTER DMG REDUCTION and SPRINT ARMOR (all three
    -- stack multiplicatively). The arc is 140 degrees measured off the player's
    -- VIEW forward, flattened to 2D — 70 degrees either side of due back.
    [36] = { eff = "{V}", act = function( l ) return "jump + Cluster: " .. ( 260 + 40 * math.min( math.max( l, 0 ), 9 ) ) .. " high, no fall damage" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "heal " .. ( 8 * L ) .. "% per C4, " .. ( 4 * L ) .. "% per Cluster" end },   -- EXPLOSIVE FUSION (CLASS PASS 2 (2026-09-27)), % of max health. LOCKSTEP _tod_class_cards TOD_FUSION_* (C4 8% / burst 4% / bomblet 1% per Lv)
    -- 37 FORCED MARCH (2026-08-24): the assault's only speed domain, and it
    -- rides the same +5%/Lv lane as SPRINT (5) and MOBILITY (9) in
    -- _tod_upgrades::apply_move_speed — one owner, three doors.
    [37] = { eff = "+{V} max health", act = "", val = function( l ) return ({ 0, 10, 19, 27, 34, 40, 45, 49, 53, 57 })[ math.min( math.max( l, 0 ), 9 ) + 1 ] end },   -- VITALITY: +10/9/8/7/6/5/4/4/4 per Lv since 2026-09-28, LOCKSTEP _tod_upgrades vitality_hp. (CLASS PASS 2 (2026-09-27), the Warrior). LOCKSTEP _tod_upgrades TOD_VITALITY_HP_LV 10
    -- 38/39 (v14.11): read back off the apply sites — apply_upgrade +
    -- body_systems_loop's want-floor for 38, recovery_loop for 39.
    -- 38 / 39 / 59 NECROMANCER (2026-09-26). LOCKSTEP _tod_necro_summon.gsc
    -- TOD_POWER_* / TOD_BEAM_* / TOD_BOMB_*.
    [38] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "bind " .. string.format( "%.1f", 7.2 * ( 1 - 0.071 * L ) ) .. " sec; life x" .. string.format( "%.2f", 1 + 0.81 * CARD_CURVE[ L ] ) .. "; thralls " .. ( 12 + 2 * L ) .. " kills" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) local n = ( L >= 3 and 1 or 0 ) + ( L >= 6 and 1 or 0 ) return "slots +" .. n .. ( L >= 9 and ", 2 Manglers" or "" ) .. ", elites x" .. string.format( "%.2f", 1 + 1.98 * CARD_CURVE[ L ] ) end },   -- 9 levels 2026-09-27, LOCKSTEP _tod_necro_summon TOD_POWER_* (life + elite hits on the log curve 2026-09-28)
    [39] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 0 ), 9 ) local b = math.floor( L / 3 ) return "beam costs " .. ( 5 * L ) .. "% less; souls rip in " .. string.format( "%.2f", 1.0 - 0.15 * b ) .. " sec" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) local b = math.floor( L / 3 ) return "+" .. math.floor( 90 * CARD_CURVE[ L ] + 0.5 ) .. "% damage, " .. ( 2 + b ) .. " souls, " .. ( 3 + b ) .. " packed" end },   -- SOUL BEAM core card (2026-09-27). LOCKSTEP _tod_necro_summon TOD_BEAM_* + _tod_necro_skull TOD_NECRO_MAX_TARGETS 2 / TOD_NECRO_SOUL_MIN_MS 1000
    -- 40 PERK SLOTS: RETIRED 2026-09-27 (no perk limit). Kept as a nil-safe id-keyed row.
    [40] = { eff = "no perk limit", act = "retired", val = function( l ) return l end },
    -- v16.49: the level IS the carry cap (1/2/3 Cymbal Monkeys); MAX AMMO gives
    -- +1 at every level, it does NOT refill (v14.61). val prints the CAP the
    -- player holds, the PERK SLOTS idiom — "carry up to 3" beats "+1".
    -- LOCKSTEP: TOD_DISTRACT_MAXAMMO_ADD / TOD_DISTRACT_MAX_CARRY / max = 3 above.
    [41] = { eff = "{V}", act = function( l ) local c = ( { [0] = 0, 0.301, 0.4771, 0.6021, 0.699, 0.7782, 0.8451, 0.9031, 0.9542, 1 } )[ math.min( math.max( l, 0 ), 9 ) ] return "range " .. math.floor( 3000 + 2000 * c + 0.5 ) .. "; landing lasts " .. string.format( "%.1f", 0.75 + 1.75 * c ) .. " sec" end, val = function( l ) local c = ( { [0] = 0, 0.301, 0.4771, 0.6021, 0.699, 0.7782, 0.8451, 0.9031, 0.9542, 1 } )[ math.min( math.max( l, 0 ), 9 ) ] return "landing: +" .. math.floor( 35 * c + 0.5 ) .. "% speed, -" .. math.floor( 60 * c + 0.5 ) .. "% damage" end },   -- " sec", not "s": the menu font draws S like a 5 (2026-09-28). LOCKSTEP TOD_ARCHER_RANGE(_ADD) / _LAND_SPEED / _LAND_DR / _LAND_SECS0 / _SECS_ADD; ln(1+l)/ln(10) since 2026-09-27
    -- 57 HELL'S RETRIEVER. LOCKSTEP _tod_retriever.gsc: charges_max (1 / 2 at
    -- Lv3 / 3 at Lv6), TOD_RET_REFILL 5 s, damage_mult table.
    [57] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 1 ), 9 ) local n = ( L >= 9 and 4 ) or ( L >= 6 and 3 ) or ( L >= 3 and 2 ) or 1 return n .. ( n == 1 and " throw" or " throws" ) .. " stored; 5 sec refill each" end, val = function( l ) local M = { 1.0, 1.5, 1.86, 2.14, 2.37, 2.56, 2.72, 2.87, 3.0 } return string.format( "x%.2f", M[ math.min( math.max( l, 1 ), 9 ) ] ) .. " axe damage" end },   -- 9 levels 2026-09-27
    -- 58 PELLETS. LOCKSTEP gen_tod_twins.js gun.pellets: Mozambique +1/+2/+3,
    -- 870 +2/+3/+5, Peacekeeper +2/+4/+7.
    [59] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return string.format( "%d", math.floor( 50 - 2.22 * L + 0.5 ) ) .. "% of a round to charge; " .. ( 360 + 80 * math.floor( L / 3 ) ) .. " radius" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "elites take " .. string.format( "%.1f", 2 + 4.5 * CARD_CURVE[ L ] ) .. " zombies' health" end },   -- 9 levels 2026-09-27; radius in buckets (the ring bands)
    [58] = { eff = "{V}", act = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) if b == 0 then return "more pellets at Lv3, Lv6 and Lv9" end return "Moz +" .. ({ 1, 2, 3 })[ b ] .. ", 870 +" .. ({ 2, 3, 5 })[ b ] .. ", PK +" .. ({ 2, 4, 7 })[ b ] .. " pellets" end, val = function( l ) return "+" .. ( 4 * math.max( l, 0 ) ) .. "% shotgun damage" end },   -- BUCKSHOT core card (2026-09-27). LOCKSTEP TOD_CORE_DMG_BREACHER 0.04 + gen_tod_twins gun.pellets (e1..e3 at Lv3 / 6 / 9)
    -- 60 STICKY C4 / 61 CLUSTER. LOCKSTEP _tod_class_kit.gsc c4_max / cluster_max /
    -- kit_dmg_mult: C4 1+L/3 charges, Cluster 1/2/3 at Lv1/6/9, layers 1+L/3 (max 3), damage x(1 + 0.175 x (L-1)).
    [60] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 1 ), 9 ) return string.format( "x%.2f", 1 + 0.175 * ( L - 1 ) ) .. " C4 damage" end, val = function( l ) local L = math.min( math.max( l, 1 ), 9 ) local n = 1 + math.floor( L / 3 ) return n .. ( n == 1 and " charge" or " charges" ) .. " per round" end },   -- 9 levels 2026-09-27
    [61] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 1 ), 9 ) return string.format( "x%.2f", 1 + 0.175 * ( L - 1 ) ) .. " damage, " .. ( 1 + math.min( math.floor( L / 3 ), 2 ) ) .. ( L < 3 and " layer" or " layers" ) end, val = function( l ) local L = math.min( math.max( l, 1 ), 9 ) local n = 1 + ( L >= 6 and 1 or 0 ) + ( L >= 9 and 1 or 0 ) return n .. ( n == 1 and " Cluster" or " Clusters" ) .. " per round" end },   -- 9 levels 2026-09-27
    -- 62 BASH. LOCKSTEP _tod_class_kit.gsc: damage 2.0 + 0.5/Lv x the blade swing,
    -- recharge 12 - 0.5/Lv s, charges 1 + Lv/4.
    [62] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 0 ), 9 ) local n = 1 + math.floor( math.min( L, 6 ) / 3 ) return n .. ( n == 1 and " dash" or " dashes" ) .. " stored; " .. ( string.gsub( string.format( "%.1f", 12 - 0.45 * L ), "%.0$", "" ) ) .. " sec recharge" .. ( L >= 9 and "; wide burst" or "" ) end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return string.format( "x%.2f", 2.0 + 0.45 * L ) .. " bash damage" end },   -- 9 levels 2026-09-27; W3E 2026-10-05: "bash", not "blade" (the fists and the gauntlet bash too), and a whole recharge drops its ".0" ("8 sec", "12 sec") - the Lv9 line "3 dashes stored; 8.0 sec recharge; wide burst" overran its pause column (268 of 260.6 px, render_menus at Lv9)
    -- 63 GRAVITY SMASH. LOCKSTEP _tod_class_kit.gsc: tier 3 only, charged by
    -- TOD_GS_KILLS 20 - TOD_GS_KILLS_STEP 1/Lv kills (was a 45 - 2.5/Lv s cooldown,
    -- user 2026-09-26), elites take 2.0 + 1.75/Lv round-zombie healths.
    [63] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return ( 20 - L ) .. " kills to charge; elite stun " .. string.format( "%.1f", 1.5 + math.floor( L / 3 ) ) .. " sec" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "elites take " .. string.format( "%.2f", 2.0 + 1.55 * L ) .. " zombies' health" end },   -- 9 levels 2026-09-27
    [42] = { eff = "{V}", act = "while 3+ zombies are within 200", val = function( l ) local b = math.min( math.floor( math.max( l, 0 ) / 3 ), 3 ) return "-" .. ( 2 * math.max( l, 0 ) + 5 * b ) .. "% damage taken" end },   -- 2026-09-27 CLASS BUILD CARD. LOCKSTEP _tod_class_cards / the class module
    -- ATHLETE carries THREE numbers, so it uses the "{V}" string form (same shape
    -- as 41) rather than one interpolated percent, and the third rides the `act`
    -- line as a FUNCTION of the level (the CLASS TIER row's idiom — CoD.TodDomainDesc
    -- pcalls it). LOCKSTEP: the 10, the 25, the 20 + 8/Lv and the 90 + 30/Lv
    -- here are TOD_ATH_SLIDE_PER_LV, TOD_ATH_JUMP_PER_LV, TOD_ATH_AIR_STEER_MAX_BASE
    -- + _PER_LV and TOD_ATH_AIR_TURN_BASE + _PER_LV in _tod_athlete.gsc (v16.23
    -- air steering; v16.28 strafe-only; v16.33 the steer budget per jump and the
    -- eased 120..240 rate).
    -- 44 GUNSLINGER (v16.51): val prints the domain's own bonus; the class
    -- baseline (2.25x) is not the domain's and is not printed here.
    [44] = { eff = "+{V}% sidearm damage vs bosses", act = "class secondary only", val = function( l ) return 30 * l end },
    -- 46 TRAILBLAZER: RETIRED WHOLE 2026-10-05 (W2E). History (v16.62): three
    -- numbers, so a composed string like ATHLETE. LOCKSTEP with _tod_upgrades.gsc, and this row was the ONLY place a player
    -- reads any of them (the baked card carries no figures, generic-card-text
    -- rule) — so a retune that skips it ships a lie:
    --     trail_pct()        = 1 + L                    -> (1 + L) %/s
    --     trail_slow_mult()  = 1 - (0.03 + 0.045*L)     -> (3 + 4.5*L) % slower
    --     trail_life_ms()    = 1500 + 500*L             -> (1.5 + 0.5*L) s
    -- v16.94 cut the burn hard so the trail cannot be farmed and added the slow
    -- in its place; v17.84 DOUBLED the slow (user: "double the slow rate") and
    -- made the base version SLOW ELITES WITHOUT BURNING THEM, which is what the
    -- act line now has to say. The old act read "bosses immune", which was true
    -- of the damage and is now false of the effect as a whole — the exact way a
    -- player ends up believing the trail does nothing to a Panzer.
    [46] = { eff = "REMOVED", act = "retired 2026-10-05", val = function( l ) return 0 end },   -- RETIRED WHOLE 2026-10-05 (W2E, a parked card)
    [43] = { eff = "{V}",                                act = function( l ) return "steer " .. ( 20 + 8 * l ) .. " deg; wall-run improves per Lv" end,     val = function( l ) return "+" .. ( 10 * l ) .. "% slide speed, +" .. ( 25 * l ) .. "% jump height" end },
    -- 45 RIOT SHIELD (v16.63): two numbers, so the "{V}" string form like 41/43.
    [45] = { eff = "{V}",                                act = "hold or wear it; recharges when broken", val = function( l ) return shieldHp( l ) .. " HP shield, back in " .. shieldRecharge( l ) end },
    -- 47 DEADSHOT (v16.64): one level, no number — the whole value is the state.
    [47] = { eff = "{V}",                                act = "controller only",                      val = function( l ) return "aim locks onto zombie heads" end },
    -- lint_tod_lua.js caps eff at 40 chars and act at 46 AND MEASURES THE
    -- STRING LITERALS INSIDE THESE val CLOSURES. Re-measure before rewording.
    [48] = { eff = "{V}", act = function( l ) local L = math.min( math.max( l, 0 ), 9 ) local r = L % 3 if r == 0 then return "every swing" end return ( r == 1 and "33" or "67" ) .. "% chance of one more" end, val = function( l ) local L = math.min( math.max( l, 0 ), 9 ) return "hits " .. ( 1 + math.floor( L / 3 ) ) .. ( L >= 3 and " zombies" or " zombie" ) end },   -- CLEAVE (2026-09-27 class pass 4 (user)). LOCKSTEP _tod_warrior_melee TOD_WM_CLEAVE_*
}

-- PUBLIC — read by AetheriumStartMenu.lua (same client Lua VM, the same way it
-- already reads CoD.TodDomainInfo). Returns the effect line and the activation
-- line for one owned upgrade, or nil,nil when the id has no detail row (a
-- removed domain, or an id added in GSC but not here yet) — the caller then
-- falls back to DOMAIN.desc so a new domain is never rendered blank.
-- [tod v16.57] THE ROUNDING GUARD (user 2026-09-02: "the pause menu was showing
-- something like 10.00000000001 ... All upgrades should round to nearest 10th
-- at max"). Every upgrade line that reaches a setText passes through this:
-- any number carrying TWO OR MORE decimals is rounded to ONE, and a trailing
-- ".0" is dropped. Numeric `val`s were already formatted with %.<dec>f below;
-- this covers string-built lines (SCAVENGER, ATHLETE), the DOMAIN.desc
-- fallbacks and any future row, whichever one produces the artifact.
CoD.TodRoundText = function( s )
    if type( s ) ~= "string" then
        return s
    end
    return ( string.gsub( s, "(%d+)%.(%d%d+)", function( whole, frac )
        local v = tonumber( whole .. "." .. frac )
        if not v then
            return whole .. "." .. frac
        end
        local r = math.floor( v * 10 + 0.5 ) / 10
        local out = string.format( "%.1f", r )
        return ( string.gsub( out, "%.0$", "" ) )
    end ) )
end

-- =============================================================================
-- DARK UPGRADE READOUTS (v17.10). One row per domain that can hold a dark
-- upgrade — 24 of them, the mirror of set_no_dark() in _tod_upgrades.gsc.
--
-- WHY A PARALLEL TABLE AND NOT A FLAG INSIDE DETAIL: every row above is a
-- FUNCTION of the level, and a dark upgrade is not a level. Threading a second
-- argument through 37 existing closures to serve 24 of them would touch every
-- row that does not need it, which is how the ATHLETE and TRAILBLAZER rows
-- picked up their lockstep bugs. These override; nothing above changes.
--
-- ⚠️ KEEP THEM SHORT. Same rule as DETAIL: the panel does NOT wrap, it
-- OVERLAPS (user 2026-09-03, with a screenshot). lint_tod_lua.js measures these.
--
-- LOCKSTEP with the TOD_DARK_* defines in _tod_upgrades.gsc. This table is the
-- ONLY place a player ever reads a dark number — the card art is generic by the
-- generic-card-text rule, so if these disagree with the GSC the player is told
-- the wrong thing and nothing catches it.
local DARK = {
    [1]  = { val = function( l ) return 10 * l + 50 end },                       -- DAMAGE      +100 -> +150
    [2]  = { val = function( l ) return drPct( l ) + 10 end },                   -- DMG REDUCTION +10 points (22 -> 32 at Lv9 since 2026-09-28)
    [3]  = { val = function( l ) return log9Pct( l ) + 50 end },                 -- BOUNTY      +100 -> +150 (log since 2026-09-28)
    -- [4] LUCK: no dark step since 2026-09-05 (set_no_dark in the GSC).
    -- [5] SPRINT dark row removed 2026-09-27 (class pass 2): id 5 is REAPER'S REACH and SPRINT (29) is set_no_dark.
    [6]  = { val = function( l ) return 12 * l + 25 end },                       -- HEADSHOT    +60 -> +85  (was 5*l+25 = +50 -> +75 until the 2026-09-08 12%/Lv x 5 pass; the dark STEP is still +25)
    -- [8] SCAVENGER's dark row removed 2026-10-05 (W2E): the parked card retired whole.
    [10] = { val = function( l ) return "0.14" end },                            -- BULLET FEED 5.0 -> 7.0 rounds/s
    [13] = { val = function( l ) return 25 end },                                -- LEECH       flat 25 HP (one heal per swing)
    [14] = { eff = "always hits 2 extra zombies",                                -- CLEAVE      a guaranteed 2nd extra
             val = nil },
    [20] = { act = "Stormbreaker only; 1.0s cooldown",                           -- THOR        +50% on every term
             val = function( l ) return math.floor( ( 4 + 12 * l ) * 1.5 + 0.5 ) end },
    -- [23] RUN AND GUN's dark row removed 2026-10-05 (W2E): the parked card retired whole.
    -- ADRENALINE +15 -> +25, on all three lanes at once (v17.85).
    [25] = { val = function( l ) return "+" .. ( 3 * l + 10 ) .. "% speed and damage, heals " .. ( 6 * l + 20 ) .. "%" end },   -- dark +10% (TOD_DARK_ADREN_ADD), heal x2; 9 levels 2026-09-28
    -- [26] OVERDRIVE's dark row removed 2026-09-27 CLASS PASS 3 (user): id 26 is PIERCING, which has no dark card
    -- [35] GIANT SLAYER's dark row removed 2026-09-27 class pass 4 (user): id 35 is SHOT SPEED, which has no dark card
    -- [36] BACK ARMOR dark row removed 2026-09-27 (class pass 2): id 36 is EXPLOSIVE FUSION (set_no_dark).
    -- [37] FORCED MARCH dark row removed 2026-09-27 (class pass 2): id 37 is VITALITY (set_no_dark).
    -- 38 / 39: VITALITY / RECOVERY dark rows removed 2026-09-26 (the ids now carry
    -- the Necromancer's SUMMONING POWER / SOUL BEAM, which have no dark card).
    [42] = { val = function( l ) return fullSteamPct( l ) + 20 end },            -- FULL STEAM  +21.6 -> +41.6
    [43] = { act = function( l ) return "steer " .. ( 20 + 8 * ( l + 2 ) ) .. " deg; wall-run improves per Lv" end,
             val = function( l ) local d = l + 2                                 -- ATHLETE     computes as level 7
                return "+" .. ( 10 * d ) .. "% slide speed, +" .. ( 25 * d ) .. "% jump height" end },
    [44] = { val = function( l ) return 30 * l + 30 end },                       -- GUNSLINGER  +150 -> +180
    -- THE FOUR WEAPON-VARIANT DOMAINS (v17.10). Unlike every row above, these
    -- are not a number in script -- they are a real weapon the player is holding
    -- (gen_tod_twins.js axisMaxUp), and they exist ONLY on the PACKED tier-3 gun
    -- of the class. LOCKSTEP with the step tables in that generator:
    --   MAG_STEP m4 1.9 / HANDLING_STEP h4 0.45 / RECOIL_STEP r3 0.40 / KNIFE_STEP k6 0.54
    [7]  = { act = "FIRE BOW, Pack-a-Punched",       val = function( l ) return 90 end },   -- MAG SIZE   +60 -> +90
    -- [16] HANDLING / [17] (RECOIL, then SOUL SIPHON) dark rows removed 2026-10-05 (W2E): both parked cards retired whole.
    -- [18] KNIFE SPEED dark rung RETIRED 2026-09-26 (set_no_dark + DARK_NONE[18]): it was "the PaP sword at -46%", and the sword ignores Knife Speed now. Was: [18] = { act = "Gold Battle Sword, Pack-a-Punched", val = function( l ) return 46 end },
    [45] = { act = "hold or wear it; elite kills -2 sec recharge",                  -- RIOT SHIELD
             val = function( l ) return "700 HP shield, back in 1:15" end },
    -- [46] TRAILBLAZER's dark row removed 2026-10-05 (W2E): the parked card retired whole.
}

-- Enabled Dark cards awaiting baked art use the composite DARK text card: list
-- such an id here (lint_tod_assets parses this table) and delete it once its
-- dark card is baked and zoned. Empty: every dark-capable domain has its art.
local DARK_TEXT_ONLY = { }

CoD.TodDomainDesc = function( id, lvl, dark )
    local d = DETAIL[ id ]
    if not d then
        return nil, nil
    end
    -- DARK UPGRADE (v17.10): swap in the dark readout. A SHALLOW COPY, never a
    -- mutation -- DETAIL rows are shared across every player row the pause menu
    -- draws, and writing through one would leak the dark value onto teammates
    -- who do not have it. [14] deliberately clears val by omitting it, so the
    -- copy must not carry the base val forward for that row.
    if dark and DARK[ id ] then
        local o = DARK[ id ]
        d = { eff = o.eff or d.eff,
              act = ( o.act ~= nil and o.act ) or d.act,
              val = o.val,
              dec = d.dec }
    end
    local eff = d.eff
    if d.val then
        -- pcall: a level outside a fixed ladder (e.g. a GSC cap raised without
        -- this table) indexes nil rather than erroring the whole pause menu.
        local ok, v = pcall( d.val, lvl )
        if not ok or v == nil then
            return nil, nil
        end
        if type( v ) == "number" then
            v = string.format( "%." .. ( d.dec or 0 ) .. "f", v )
        else
            v = tostring( v )
        end
        -- ⚠️ FUNCTION REPLACEMENT, NEVER A STRING ONE (v17.86, user 2026-09-05:
        -- "I got a UI error when I paused").
        --
        -- In Lua, when gsub's third argument is a STRING, `%` is an ESCAPE: it
        -- must be followed by a digit (a capture) or another `%`. A `%` followed
        -- by anything else -- a space, a slash, a comma, or end-of-string --
        -- raises "invalid use of '%' in replacement string". Our value lines are
        -- FULL OF percent signs ("+15% speed and damage, heals 30%",
        -- "burns 6%/s, slows 34%", "+10% slide speed"), so every one of them was
        -- a live error waiting on the row being owned and the menu being opened.
        --
        -- THE pcall ABOVE DOES NOT COVER THIS. It wraps the val CALL only; the
        -- substitution happens out here, so the throw takes the whole pause menu
        -- with it rather than degrading one row to blank. That is why the symptom
        -- is "the pause menu errored", with nothing pointing at a domain.
        --
        -- A function replacement has NO escape processing: whatever it returns is
        -- inserted verbatim. CoD.TodRoundText below already used the function form
        -- (that is why it never hit this), so this line was the file's one
        -- remaining string-replacement gsub.
        --
        -- The bug is OLDER than the row that exposed it: ATHLETE (43) has returned
        -- a percent-bearing string here since v16.23 and TRAILBLAZER (46) since
        -- v16.94. v17.85 put ADRENALINE (25) -- a far more commonly owned domain --
        -- on the same lane, which is what made it show up. Do not "fix" this by
        -- rewording a row; any row may legitimately contain a percent sign.
        eff = string.gsub( eff, "{V}", function() return v end )
    end
    eff = CoD.TodRoundText( eff )
    -- `act` is normally a plain string; the CLASS TIER row (24) makes it a
    -- FUNCTION of the level, because what it states is the requirement for the
    -- promotion you have NOT taken yet. Same pcall guard as `val` for the same
    -- reason — a level outside the expected range must not error the whole
    -- pause menu — and a failed call degrades to no activation line rather than
    -- to a wrong one.
    local act = d.act
    if type( act ) == "function" then
        local okA, a = pcall( act, lvl )
        act = ( okA and type( a ) == "string" and a ) or nil
    end
    return eff, act
end

-- [tod] shared with AetheriumStartMenu.lua (same client Lua VM): the pause
-- menu's "YOUR UPGRADES" panel renders CoD.TodOwned (accumulated below from
-- the GSC tod_upg_sync LuiNotifyEvents) using these names.
CoD.TodDomainInfo = DOMAIN

CoD.TodOwned = CoD.TodOwned or {}
-- [tod v14.35] The CLASS TIER floor requirement for the deal currently being
-- shown, or 0 when the floor is not what is blocking this player. Written by
-- the tod_upg_tier_need receiver below (the HUD menu, always open) and read by
-- the choice panel while it paints — the same shared-global pattern
-- CoD.TodOwned already uses to cross menus inside this one client VM.
CoD.TodTierNeed = CoD.TodTierNeed or 0

-- Per-piece art flags — flip a flag ONLY once its i_tod_* image assets are
-- installed + zoned. 2026-08-18 drop 2: COMPLETE set live
-- (source_data/tod_ui_images.gdt — frames, base plate, icons, title plate).
local USE_TITLE_ART = true
-- FULL-CARD SET ART (user drop files (10).zip 2026-08-20): 54 baked cartoon
-- cards (18 domains x 3 rarities, PORTRAIT 2:3, all text in the art) REPLACE
-- the composite frame+base+icon+text. Images-over-LUI doctrine: LUI keeps
-- only layout and the focus/hold/timer overlays.
--
-- THERE IS NO "Lv X > Y" LINE. This header advertised one until 2026-08-30 and
-- it was WRONG — the overlay was removed 2026-08-20 (see the note at the
-- card.Desc construction below, which is authoritative). Two sessions read this
-- comment and concluded the deal screen shows a live value; it does not.
-- NO LUI TEXT IS DRAWN ON THE CARDS AT ALL — PaintCard blanks Tag/Name/Desc and
-- the baked art carries everything, with the rarity gem "+N" carrying the gain.
-- CONSEQUENCE FOR CARD ART: a number that is not baked into the card is not
-- visible at deal time anywhere. Level-aware values live ONLY in the pause menu
-- (CoD.TodDomainDesc -> DETAIL[id].val(lvl)). That is the deliberate trade for
-- level-agnostic art that never needs re-baking on a retune — see docs/47.
-- The composite path below survives as the no-art fallback.
local USE_CARD_SET_ART = true
-- [tod 2026-09-26] HUD V2 (docs/182): the in-match HUD in the red "Fallen" language.
-- Here it owns the TOP-LEFT STATUS PLATE (round + luck) and the DESCENT GAUGE. The
-- same flag name lives in AetheriumLoadout / PlayerInfo / PartyPlayers / PerkItem /
-- PowerupNotification / RoundCounter - flip them together. FALSE = the old HUD.
local USE_HUD_V2 = true
-- DARK UPGRADES (v17.10) -- the fourth rarity, above ULTIMATE. 37 baked cards
-- (i_tod_card_<slug>_dark) are INSTALLED in source art and PROOFREAD, but they
-- are NOT ZONED, so this flag is OFF and must stay off until they are.
--
-- WHY IT IS A FLAG AND NOT JUST CODE: this file's own contract, at the top --
-- "RegisterImage of a missing image is undefined behavior". Registering 37
-- names with no zone line behind them is the WHITE SQUARE failure, and
-- tools/lint_tod_assets.js hard-codes [regular,super,ultimate] so it would not
-- catch it.
--
-- FLIPPING IT IS A THREE-PART COMMIT, none of which can be skipped:
--   1. zone lines + GDT blocks for the dark cards that can actually be DEALT
--      (27 of the 37 -- the other ten have no dark step, see set_no_dark),
--   2. teach lint_tod_assets.js the fourth rarity, and
--   3. accept the load-RAM bill: cards are uncompressed 768x1152 = 3.375 MiB
--      EACH, so 27 is ~91 MiB on a UI-art set already costing 536 MiB. The
--      cheaper route is ONE shared dark overlay frame (~3.4 MiB) -- that lane
--      is already built here (art.frames / FrameArt, composited ABOVE CardImg)
--      and force-disabled one screen below. docs/92 THE ART has the numbers.
--
-- WITH IT OFF the dark card still deals, still pays, and still sounds different
-- (tod_dark_aura); it simply wears the ULTIMATE artwork with a DARK UPGRADE tag.
local USE_DARK_CARD_ART = false   -- 2026-09-28: DARK UPGRADES RETIRED (docs/187); art unzoned
-- [tod v14.35] CLASS TIER GATE STRIP — the "why is there no tier card in this
-- deal" line under the cards. Images-over-LUI like everything else on this
-- panel: two baked strips (i_tod_tier_gate_2 / _3, one per requirement),
-- prompt + specs in docs/50. LIVE since 2026-08-31: both PNGs are installed in
-- source_data/tod_ui_images/_images, entered in tod_ui_images.gdt and carry
-- their two `image,` lines in the .zone. The user picked explore direction 3
-- (steel pill, amber stacked double chevron — "climb", not "refused"); 420x90,
-- RGBA, verified legible downscaled to its on-screen 280x60 before install.
-- The LUI text below survives as the no-art fallback.
-- [2026-09-02] THE FLOOR -> TIER TABLE. LOCKSTEP with GSC tier_floor_req
-- (TOD_TIER2_FLOOR / TOD_TIER3_FLOOR in _tod_upgrades.gsc). The badge block
-- used to derive the tier as math.floor( need / 10 ) + 1 -- the exact inverse
-- of a 10/20 ladder and nothing else. The day T3 moved to floor 30 (user,
-- docs/72) that arithmetic answered 4, found no strip and would have silently
-- dropped the badge art for every tier-2 player. A floor missing from this
-- table falls back to tier 2 (the text line still shows the real floor).
local TIER_FLOOR_TO_TIER = { [10] = 2, [30] = 3 }
-- [docs/160, 2026-09-23] THE DESCENT (TIER_DESCENT / tierFloorShown, declared
-- above the DETAIL table): the two baked strips (i_tod_tier_gate_2 / _3)
-- carried "FLOOR 10" / "FLOOR 30", the CLIMB's numbers, so under the descent
-- the art was OFF and the text line below drew the right floor (40 / 20).
-- [PK01, 2026-10-04] RE-BAKED FOR THE DESCENT and back ON: the strips now read
-- TIER 2 AT FLOOR 40 / TIER 3 AT FLOOR 20 (the floor the player stands on when
-- the gate clears = TIER_LAPS - need) in the map typeface, chevrons pointing
-- DOWN. GENERATED by tools/artgen/packs/pk01_card_text_rebake.py, whose --check
-- (a build gate) holds the baked 40 / 20 against TIER_LAPS, TIER_FLOOR_TO_TIER
-- and the GSC defines - so a floor retune fails the build until the strips are
-- re-generated. The TierLine text stays as the per-tier no-art fallback.
local USE_TIER_GATE_ART = true
-- [tod v16] CLASS BADGE (docs/59, user: "players also want an update to the
-- upgrade menu that shows what class you are playing as"). Four baked plates,
-- 420x90, drawn 280x60 in the panel's left gutter -- the exact mirror of the
-- luck badge on the right, same chassis. Costs ZERO clientuimodel bits: the
-- class rides the int-only LuiNotifyEvent lane, same as tod_upg_tier_need.
local USE_CLASS_BADGE_ART = true
-- [tod v18.10] THE LUCK LEGEND -- 420x90 drawn 280x60, the luck badge's own
-- chassis, sitting immediately under it and captioning it in two words. The bar
-- was on screen with its payoff written nowhere in the game: this row's DETAIL
-- line explains how to RAISE luck, the HUD art says "LUCK", and the badge says
-- "LUCK 60% BOOSTED" and stops one noun short. A player asked outright in the
-- Workshop comments on 2026-09-06 and had to be answered on Steam.
--
-- THE NEUTRAL (steel) VARIANT WAS CHOSEN over the amber one on purpose: the
-- badge above it recolours with the fill (gold at 100%, green at 50%), so a gold
-- caption would only look right at full. Steel sits correctly at every value.
local USE_LUCK_LEGEND_ART = true
-- [tod v16.32, KBM audit — docs/69 §6] THE HINT PLATES DRAW THE LIVE BINDS.
-- The baked plates carry the DEFAULT keys (MOUSE1/MOUSE2/V/SPACE, an Xbox
-- "A"), so a rebinder, a PlayStation-layout pad and a pad player before the
-- first d-pad press all read the wrong thing. With this on, the plate is the
-- BLANK frame (i_tod_hint_frame, files (96).zip) and the key line is LUI text
-- carrying the engine's [{+bind}] tokens, which expand to the key or pad glyph
-- bound RIGHT NOW on THIS device — the mechanism every stock "Hold [X]" hint
-- rides and the one PromptDefault.lua's SetFooter uses. The baked keyed plates
-- (re-baked with F in the same drop) stay as the flag-off look; the LOCKED
-- plate stays baked under both (it names no key).
local USE_HINT_FRAME_ART = true
-- [tod v16.88] BAKED BUTTON GLYPHS (docs/88). User, after seeing the v16.83
-- text plates on a pad: *"Again this needs to show a dpad. Use the <dpad icon>
-- to switch ... the KBM UI is pretty bad"*. The premise the old design rested
-- on was false: the engine renders `[{+bind}]` as a TEXT NAME, never a picture,
-- so a controller player literally read "LT" and "RT". Nine baked images now
-- carry every fixed part; the ONLY engine-drawn thing left on the control UI is
-- the keyboard key NAME, and it sits inside a baked keycap.
--
-- DEVICE RULE — read this before "fixing" it. There is no reliable server-side
-- device read (`GetControllerType()` is documented but unexercised, see
-- docs/88), so the glyph set is chosen by `CoD.TodPad`, the one-way
-- action-slot latch. That latch is NOT a device proof (v16.81: a keyboard
-- binds 3/4 to action slots), so a keyboard player who taps 3 or 4 will see
-- pad glyphs. That is the known, accepted cost of showing a d-pad at all, and
-- it is strictly better than the status quo, where EVERY pad player read
-- letters. The fix is a real device read, not a different guess.
local USE_CARD_GLYPH_ART = true
-- [v17.27] `TOD_KEYCAP_TEXT_SCALE` (v17.4) IS GONE, in both this file and
-- tod_class_select.lua. Keycap text is no longer LUI text at all — it is set in
-- the map's baked typeface by `CoD.TodKeycap`, which MEASURES the string and
-- picks the size. Retired whole rather than left as an unread constant.
-- CLASS TIER card art (docs/25 §10): all 8
-- i_tod_card_tier_<skirmisher|assault|heavy|slasher>_<2|3> images installed +
-- zoned 2026-08-22 (user art drop files (31).zip, docs/26 build-out). The
-- composite text stack (PaintCard's no-art branch, name/desc from
-- TIER_LADDER) stays as the fallback if this is ever flipped back.
local USE_TIER_CARD_ART = true  -- 2026-09-25: back ON - the Theme B tier cards (docs/171, docs/173) carry the current roster (was OFF Sep 24 while the art was replaced)
-- portrait card rect (1280-canvas), side by side.
--
-- REVERTED 2026-08-24 to the pre-v10.3 size (user, after playing it: "I think we
-- reduced the size of the upgrade menu by 15%. Whatever we did lets revert that.
-- Its too small now and it was actually in a good spot"). v10.3 had taken
-- 213x320 -> 181x272 on an earlier playtest note ("takes up so much of the
-- screen"); this puts all four numbers back exactly, re-expanded about each
-- card's own centre so the pair keeps its layout.
--
-- These FOUR numbers are the whole knob: every overlay (icon inset, hint
-- plates, hold bar, fallback text stack) is keyed off them, so nothing else
-- needed touching in either direction. The card ART is unaffected too — the
-- PNGs are 768x1152 and the engine scales them into this rect, so no re-bake.
-- CARDS DRAWN BIGGER (user 2026-08-27: "Some have text that is so hard to
-- read"). The card art is 768x1152 and was being drawn at 213x320 — a 0.277
-- downscale, 2.3x harder than anything else in the UI (the pause header is
-- 0.70, the name plates 0.64, the switch hint 0.61). At that scale the card's
-- SUBLINE — the line carrying qualifiers like "CLASS PRIMARY ONLY" — lands at
-- about 7 virtual px, i.e. ~10px at 1080p and ~7px at 720p. Unreadable inside a
-- 15-second timed pick.
--
-- Now 234x351 — EXACTLY +10% linear (user 2026-08-27: "Only increase card size
-- by 10%. Thats all"). The layout had room for +19%, but 10% is the call; the
-- headroom is recorded here rather than taken.
--
-- 234/351 is EXACTLY 2:3, matching the art's 768/1152, so this is a pure
-- scale-up with no new stretch. Every child element positions off xLo/xHi/
-- CARD_Y0/CARD_Y1 and follows automatically. Nothing else on the menu moves:
--   * TOP  banner ends at y=215                     -> Y0 226 (11px clear)
--   * BOT  hold bar sits at CARD_Y1+39..+43 and must clear the switch-hint
--          plate at y=650                           -> Y1 577, bar ends 620 (30px clear)
--   * RIGHT luck badge starts at x=950              -> 911 (39px clear)
--   * the 74px gap between the two cards is unchanged and both stay centred on
--     x=640.
--
-- This alone takes the subline from ~6.7 to ~7.4 virtual px. It is the smaller
-- half of the fix: the other half is baking the subline larger in the art (see
-- the card-legibility prompt). The two compound, and this half re-bakes nothing.
local CARD_Y0, CARD_Y1 = 226, 577

-- ---------------------------------------------------------------------------
-- [tod v18.32] THE HOLD PLATE, MEASURED OFF ITS OWN PIXELS — twin of the block
-- in tod_class_select.lua, where the full argument and the two bugs it fixes
-- live. `i_tod_hold_plate` is 460x70: bright ink x96..401, the empty gap
-- between "HOLD" and "TO LOCK" at x169..286 (118 wide, centred at 227.5 — two
-- and a half pixels LEFT of the plate's own centre), lettering band y25..42.
--
-- THIS MENU ALREADY HAD THE ASPECT RULE (v16.4, see HintImg below) and its
-- plate is drawn true at 222x34. What it did NOT have is the gap: the keycap
-- was a typed 64 px against a 56 px gap, so it overhung the baked lettering by
-- 4 px each side, exactly as it did on the draft. Both glyph sizes are now
-- arithmetic off these numbers.
-- ---------------------------------------------------------------------------
local PLATE_ASPECT = 460 / 70      -- 6.571. A plate drawn off this is stretched.
local PLATE_GAP_CX = 227.5 / 460   -- 0.4946 — the GAP's centre, not the plate's
local PLATE_GAP_W  = 118 / 460     -- 0.2565 — the widest a glyph may be drawn
local PLATE_INK_CY = 33.5 / 70     -- 0.4786 — the lettering's optical centre
local CARD_AX0, CARD_AX1 = 369, 603
local CARD_BX0, CARD_BX1 = 677, 911

-- ===========================================================================
-- THE CARD REVEAL (v14.52, user 2026-08-31: "like when you pull a super cool
-- camo in csgo or ... apex legends crates ... if a slot is ultimate it can be
-- empty for 0.5s and then grow into its ultimate card and then make an epic
-- noise ... enhance the player experience when they pull upgrade cards").
--
-- IT COSTS ZERO CLIENTUIMODEL BITS. The pool sits at 60 of its PROVEN 61 (see
-- _tod_upgrade_ui.gsc __init__), so a new field was not affordable — and not
-- needed. The reveal is DERIVED from three facts the panel already carried:
--
--   show == 1 AND focus == 0   the reveal is running. This pair is a SERVER
--                              CONTRACT and is unreachable any other way:
--                              every path that raises show to 1 sets focus
--                              1..4 in the same breath, and wait_for_choice
--                              never writes 0. present_choice holds focus at 0
--                              for exactly the length of the reveal.
--   R >= 1 while D == 0        that slot is an EMPTY SOCKET, and R is what it
--                              is charging toward. R == 0 means no card is
--                              coming to that slot at all (a one-card deal).
--   D goes 0 -> N              that slot's card LANDS, now, at rarity R.
--
-- The server separates the R push and the D push by a real wait, so the two
-- can never arrive in one snapshot — which is what makes reading R on the D
-- edge safe. Model callbacks fire in clientfield REGISTRATION order (AD before
-- AR), so without that gap a card would land wearing the last deal's rarity.
--
-- ⚠️ REVEAL_HOLD_MS is LOCKSTEP with TOD_REVEAL_HOLD_* in _tod_upgrade_ui.gsc
-- (ms here, seconds there). The socket's rim ramps over the same span the
-- server waits, so the ramp completes exactly as the card arrives. Drift does
-- not BREAK anything — a short ramp holds its end state, a long one is cut off
-- by the card — it just stops looking deliberate.
-- HALVED in v14.53 with the server's TOD_REVEAL_HOLD_* — see the lockstep note.
local REVEAL_HOLD_MS = { [1] = 50, [2] = 200, [3] = 300, [4] = 300 }
-- The flip. MUST stay under the server's SHORTEST gap between two pushes, or a
-- later push's Render lands mid-tween and snaps the card to its end rect. The
-- station runs the whole show at half speed (TOD_REVEAL_LIVE_SCALE), so the
-- real floor is min(GAP, TAIL) * 0.5.
--
-- ⚠️ v14.53 RECOMPUTED, and this is the non-obvious cost of halving the server
-- timings: that floor moved with them, from min(280,300)*0.5 = 140ms down to
-- min(140,150)*0.5 = **70ms**. The old 120ms flip would have been legal on a
-- round event (140ms gap) and SNAPPED AT THE STATION — an animation that
-- silently stops existing in one of the two places it runs, which is the
-- hardest kind of bug to notice. 60ms keeps 10ms of margin everywhere.
-- THE PULL (docs/187): longer the rarer. Each runs after its slot's LAST push
-- and is bounded by that slot's beat x 0.5 (COMMON 130 ms at a co-op altar).
local REVEAL_FLIP_MS   = { [1] = 90, [2] = 110, [3] = 130, [4] = 160 }
local REVEAL_SOCKET_MS = 55    -- socket blowing apart as the face opens
-- The burst does NOT block anything and is not bound by that floor, so it is
-- cut LESS than half — the user's second note was that the ultimate should hit
-- HARDER, and shrinking its burst in proportion to the pacing would have pulled
-- against that. 380ms still finishes before slot B lands (GAP 140 + HOLD 300).
local REVEAL_FLARE_MS  = { [1] = 0, [2] = 200, [3] = 380, [4] = 480 }
-- REGULAR GETS NOTHING ON PURPOSE. If every pull flashes, no pull is special —
-- the whole point is that SUPER and ULTIMATE feel different from the card you
-- see four times an hour. Flare = the one-shot burst; glow = the aura the card
-- keeps for the rest of the panel.
local REVEAL_FLARE_PEAK = { [1] = 0,  [2] = 0.55, [3] = 0.92, [4] = 1.0 }
local REVEAL_FLARE_GROW = { [1] = 0,  [2] = 18,   [3] = 34, [4] = 48 }
local REVEAL_GLOW       = { [1] = 0,  [2] = 0.22, [3] = 0.40, [4] = 0.55 }
local REVEAL_GLOW_PAD   = 14   -- how far the aura stands proud of the card
local REVEAL_SOCKET_PAD = 3    -- socket rim thickness

local MAX_LEVEL_TIME_DANGER = 5   -- countdown turns red at this many seconds

-- Per-input wording (user 2026-08-20): controller vs KBM. (PS-vs-Xbox glyphs
-- are not distinguishable on PC BO3 — the engine only knows gamepad vs KBM.)
--
-- [tod v16.3] NO MORE GUESSING (repo review 2026-09-01). This used to ask
-- Engine.IsGamepadEnabled( 0 ) and fall back to CONTROLLER wording when the
-- hook was absent — and keyboard players kept reading "HOLD A" (four Workshop
-- reports, the last one AFTER the 08-24 keyboard fix), because a pad that is
-- merely plugged in answers true and the nil path said controller too. This is
-- a PC-only mod: default to the KEYBOARD plates, and flip to the pad plates the
-- moment the SERVER proves the device off this player's first d-pad press
-- (_tod_upgrade_ui::pad_latch -> "tod_input_pad" int-notify, received below
-- into CoD.TodPad, a client-VM global that outlives the per-life menu rebuild).
-- [tod v17.55] ... AND the bind expansion. The latch alone drew a THIRD control
-- set to every pad player before their first d-pad press: keycap art filled by
-- the engine with "LT" / "RT" / "A". CoD.TodKeycap.PadDevice() reads the pad off
-- the offhand pair's expansion, so a pad now gets pad glyphs from the first
-- frame. ONE reader for all three surfaces; the argument lives in TodKeycap.lua.
-- [tod v18.16] THE THIRD CONTROL SET, FOR THE THIRD TIME. User 2026-09-07:
-- *"all I want is a KBM set and then a D pad and A set ... there's a third one
-- that comes up for left trigger, right trigger, and the a button. I want that
-- completely removed"* — and, decisively: *"It's not that I don't want right
-- trigger left trigger to be able to use for controller. I just don't want the
-- UI to say that."* So LT/RT keep WORKING; they may never be DRAWN.
--
-- WHY v17.55 DID NOT CLOSE IT. That pass put the device read in
-- CoD.TodKeycap.PadDevice() and had every surface call it. Correct, but it is
-- reached through `CoD.TodKeycap ~= nil and ...` — and this menu deliberately
-- pcall-requires that widget, so if the require ever fails the whole test
-- silently returns FALSE. A pad player then gets the KEYBOARD layout, and the
-- engine fills those caps with the pad's own words: LT / RT. The guard for the
-- third set lived inside the thing whose absence causes the third set.
--
-- So the test is twinned HERE, with no dependency on the widget — the same
-- argument the stub above is built on, and the same one CoD.TodKeycap.IsPadName
-- makes; that copy stays the canonical one. Keep them in step.
--
-- [tod v18.32] THE FOURTH TIME, AND THE FIRST ONE WITH A PICTURE OF IT. User
-- 2026-09-08: *"When we show A, LT, and RT why are they inside key caps ... If
-- you are using controller we dont use key caps asset."* The screenshot settles
-- what three passes of lexical matching could not: the engine expands a pad
-- bind into a BUTTON ICON, not the letters "LT". No path in this file draws a
-- pad image and a keycap together, so the icon in that shot came out of the
-- expansion, through the keycap's own text fallback. Matching on spelling was
-- always going to miss it. TodPadGlyph is the structural test — see
-- CoD.TodKeycap.IsPadGlyph for the whole argument; keep the two in step.
local function TodPadWord( tok )
    local s = Engine.Localize( tok ) or ""
    s = s:gsub( "%^%d", "" )
    local cut = s:find( "%s*[,/]" ) or s:find( "%s+[Oo][Rr]%s+" )
    if cut and cut > 1 then
        s = s:sub( 1, cut - 1 )
    end
    s = s:gsub( "^%s+", "" ):gsub( "%s+$", "" )
    s = string.upper( s )
    if s == "" then
        return false
    end
    -- Xbox LB RB LT RT / PlayStation L1 R1 L2 R2, plus any spelled-out form.
    -- Kept for a build that DOES spell the button out; the icon test above is
    -- what actually fires on this engine.
    if s:match( "^[LR][BT12]$" ) then
        return true
    end
    return s:find( "TRIGGER", 1, true ) ~= nil or s:find( "BUMPER", 1, true ) ~= nil
        or s:find( "DPAD", 1, true ) ~= nil or s:find( "D-PAD", 1, true ) ~= nil
end
-- [tod v18.48] KEYBOARD IS THE DEFAULT; A PAD MUST BE PROVEN. User 2026-09-08:
-- *"I thought we decided on starting KBM controls and if controller is detected
-- we use controller controls."* So this returns false unless something POSITIVE
-- says pad, and the only two proofs allowed are ones that cannot misfire toward
-- the pad: the d-pad latch, and a pad BUTTON NAME (LT/RT/LB/RB/L1..R2) in the
-- offhand expansion, which no keyboard key is called.
--
-- TodPadGlyph is NOT consulted here any more — see the note on it above. A test
-- that can be wrong in the direction of "pad" has no business in a function
-- whose default is "keyboard"; it cost the keyboard its whole control set for
-- one build. It still runs, but only at draw time on one keycap's contents.
local function UsingController()
    if CoD.TodPad == true then
        return true
    end
    if CoD.TodKeycap ~= nil and CoD.TodKeycap.PadDevice() == true then
        return true
    end
    -- ...and the widget-free arm, so a failed require cannot resurrect the
    -- third set. The offhand pair only: A/B/X/Y are keyboard key names too.
    return TodPadWord( "[{+smoke}]" ) or TodPadWord( "[{+frag}]" )
end
local function LockHint()
    if UsingController() then
        return "HOLD [ A ] TO LOCK"
    end
    return "HOLD [ SPACE ] TO LOCK"
end
local function SwitchHint()
    if UsingController() then
        -- v14.20: NOT "/ STICK" any more. The server-side panel latches the
        -- device off the first d-pad press and from then on ignores stick, RT,
        -- LT, R3 and X for that player (_tod_upgrade_ui::wait_for_choice), so
        -- the d-pad is the only lane a pad player can rely on. The BAKED pad
        -- hint plate (retired 2026-10-05; the live-bind frame names the d-pad) drew a d-pad glyph alone
        -- and needs no re-bake — this is the no-art fallback catching up.
        -- [tod v18.16] ONE LANE, NOT THREE — twin of the class draft; the
        -- argument lives there. LB/RB still switch, they are just not named.
        return "SWITCH: D-PAD   LOCK: HOLD [ A ]"
    end
    -- v10.19: mouse + F joined (user retest: "keyboard still does nothing" —
    -- the movement/jump reads were never live-verified on KBM; mouse1/mouse2
    -- and USE ride reads the engine core exercises constantly). Arrows work
    -- when bound to movement; the engine exposes no raw-key read.
    -- v10.20: advertise the PROVEN lane only. WASD/arrows reach the server via
    -- GetNormalizedMovement, which reads ~0 under the menu freeze's 0.001
    -- move-speed pin, so they are a bonus and must never be the headline.
    -- Mouse/V/R are action buttons every keyboard binds by default.
    return "SWITCH: [TACTICAL] [LETHAL] or [V]   LOCK: HOLD [ SPACE / F ]"
end

-- [tod v16.32, docs/69 §6] THE OVERLAY LINES drawn over the blank frame when
-- USE_HINT_FRAME_ART is on. Every [{+bind}] token is expanded by the ENGINE
-- into the key or pad glyph bound right now on this device, so the plate
-- follows the player's real device and binds at every render — no latch, no
-- lock-in (user 2026-09-02: "keep detecting and swapping assets"; the server
-- cannot tell which device locked a class, because jump and use exist on
-- both, so a lock-in would prove nothing). The one-way d-pad latch
-- (CoD.TodPad) is used only to SHORTEN the line once the pad is proven —
-- before that the shared lanes (RT/LT/R3, or MOUSE1/MOUSE2/V) are the truth
-- for either device, and D-PAD is named on the line so a pad player finds the
-- lane that arms the latch early instead of fighting the shared ones at the
-- station. ^5 cyan labels / ^3 gold keys / ^7 white: the baked plates' palette.
-- The strings must be set through Engine.Localize at SHOW time — the tokens
-- expand when the string is set, not when it is drawn.
-- [tod v16.83, user 2026-09-03: "our last update made it more confusing and
-- less simplified by adding so much to look at"] ONE LANE PER ACTION, AND ITS
-- DIRECTION.
--
-- WHAT WAS ON SCREEN. Measured against the user's own
-- `players/bindings_0.cfg` (+smoke=E, +frag=G, +melee=V, +gostand=SPACE,
-- +activate=F), a single 15-second deal drew THREE plates, FOUR lines and
-- SEVEN key names for a two-button decision:
--     SWITCH: E / G / V / D-PAD          (plate line 1)
--     LOCK: HOLD SPACE / F               (plate line 2)
--     HOLD SPACE / F TO LOCK             (under the focused card — the SAME
--                                         instruction, said twice)
--     AUTO IN 15s
-- Nothing here was ever removed: pre-v16.32 this was ONE baked plate with ONE
-- line; v16.32 split it in two to fit the tokens, v16.57 swapped in the
-- offhand pair and kept D-PAD. Every step added.
--
-- THE REAL DEFECT IS NOT THE LENGTH, IT IS THAT A LIST HAS NO DIRECTION.
-- "SWITCH: E / G / V" tells a player which keys are live and NOT which card
-- each one moves to — the one fact they need. Direction is now the whole line.
--
-- WHICH LANE GETS NAMED. The offhand pair, because it is the ONLY pair that is
-- correct on every device in every place this panel opens: tactical/lethal are
-- read ABOVE the station's device gate in `_tod_upgrade_ui::wait_for_choice`,
-- so they survive the pad's d-pad-only station rule, and by v16.57's argument
-- they sit left/right on every pad layout by construction. Melee, reload,
-- WASD, the strafe stick and the d-pad all keep working exactly as before —
-- they are simply no longer ADVERTISED. A prompt teaches one reliable way;
-- stock does the same ("Hold [X] To Buy" never lists its alternatives).
--
-- NO DEVICE BRANCH ANY MORE. Both strings are now identical for pad and
-- keyboard, because the engine expands every token into the live device's own
-- key or glyph — the D-PAD tail was the last thing on these plates that keyed
-- off `CoD.TodPad`, and that latch is not a device proof (v16.81: a keyboard
-- binds 3/4 to action slots). So a falsely-latched KBM player can no longer be
-- shown pad wording here. `UsingController()` survives for the flag-off baked
-- plates below, which are per-device art.
local function SwitchLine1()
    return "^3[{+smoke}]^7 ^5<  SWITCH  >^7 ^3[{+frag}]^7"
end
-- LOCK IS SAID ONCE, UNDER THE FOCUSED CARD, where the eye already is and
-- where the hold bar fills. The bottom plate no longer repeats it.
local function LockLine()
    return "HOLD ^3[{+gostand}]^7 TO LOCK"
end

CoD.TodUpgradePanel = InheritFrom( LUI.UIElement )

function CoD.TodUpgradePanel.new( HudRef, InstanceRef )
    local self = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( self )
    -- a panel torn down mid-deal must not leave the HUD hidden
    LUI.OverrideFunction_CallOriginalSecond( self, "close", function ( element )
        if CoD.TodHudVeil then
            CoD.TodHudVeil.Set( "cards", false )
        end
    end )
    self:setClass( CoD.TodUpgradePanel )
    self.id = "TodUpgradePanel"
    self.soundSet = "HUD"
    self:setLeftRight( true, true, 0, 0 )
    self:setTopBottom( true, true, 0, 0 )
    self:setAlpha( 0 )

    -- Art handles, registered once (each block only when its assets exist).
    local art = {}
    if USE_TITLE_ART then
        art.title = RegisterImage( "i_tod_title_plate" )
    end
    if USE_CARD_SET_ART then
        -- UI-family art (files (11).zip): banners, luck badges, input hints
        -- (the PANZER/PROTECTORS spawn banners that used to live in createMenu
        -- were deleted 2026-08-22 — see the note there.)
        art.bannerUpgrade = RegisterImage( "i_tod_banner_upgrade" )
        if USE_LUCK_LEGEND_ART then
            art.luckLegend = RegisterImage( "i_tod_luck_legend" )
        end
        if USE_TIER_GATE_ART then
            -- keyed by the TIER the strip names (2 or 3), not by the floor, so
            -- a floor retune re-bakes the art without moving the table
            art.tierGate = {
                [2] = RegisterImage( "i_tod_tier_gate_2" ),
                [3] = RegisterImage( "i_tod_tier_gate_3" ),
            }
        end
        art.badges = {}
        for i = 1, 10 do
            art.badges[ i ] = RegisterImage( "i_tod_badge_luck_" .. ( i * 10 ) )
        end
        -- [tod v16] CLASS BADGE plates, keyed by CLASS ID 1..4 -- the same ids
        -- tod_class_select.lua's CLASSES table and _tod_classes::class_id use.
        -- Class 0 is CLASSLESS (pre-draft) and deliberately has no entry.
        if USE_CLASS_BADGE_ART then
            art.classPlate = {
                [1] = RegisterImage( "i_tod_upg_class_necromancer" ),   -- docs/179 (2026-09-26)
                [2] = RegisterImage( "i_tod_upg_class_assault" ),
                [3] = RegisterImage( "i_tod_upg_class_heavy" ),
                [4] = RegisterImage( "i_tod_upg_class_slasher" ),
            }
        end
        art.hintLocked = RegisterImage( "i_tod_hint_locked" )
        if USE_HINT_FRAME_ART then
            art.hintFrame = RegisterImage( "i_tod_hint_frame" )
        end
        -- [tod v16.88] REAL BUTTON GLYPHS (docs/88, drop 2026-09-03 13:38).
        -- The engine renders a bind token as a TEXT NAME, never a picture — a
        -- pad player read the letters "LT"/"RT" — so the glyphs are baked here
        -- and only the KEYBOARD key name is still engine-drawn, inside a baked
        -- keycap. See the switch-glyph block below for the device rule.
        if USE_CARD_GLYPH_ART then
            art.padDpadL   = RegisterImage( "i_tod_pad_dpad_left" )
            art.padDpadR   = RegisterImage( "i_tod_pad_dpad_right" )
            art.padBtnA    = RegisterImage( "i_tod_pad_button_a" )
            -- (i_tod_key_blank, the SQUARE keycap, is deliberately NOT
            -- registered or zoned: the bind expansion can be "MOUSE3", and
            -- since nothing here can measure it in advance the WIDE cap is
            -- used for every key. A single letter simply centres in it. The
            -- PNG and its GDT block stay for the day a width read exists.)
            art.keyWide    = RegisterImage( "i_tod_key_blank_wide" )
            art.holdPlate  = RegisterImage( "i_tod_hold_plate" )
            -- (i_tod_hold_fill is NOT used and NOT zoned. It was drawn to fill
            -- the plate groove, but the plate bakes HOLD / TO LOCK ON TOP of
            -- that groove, so a fill layered over the plate would cover the
            -- words and a fill layered under it would be hidden by the opaque
            -- plate. The progress bar therefore sits BELOW the plate using the
            -- timer pair. PNG + GDT kept for a future plate whose groove is
            -- clear of its lettering.)
            -- ONE bar pair serves BOTH the hold-to-lock progress and the
            -- auto-pick countdown: they are the same object (a track that
            -- fills or drains), so they share art rather than minting a
            -- second pair that would have to be kept in visual lockstep.
            art.barTrack   = RegisterImage( "i_tod_timer_track" )
            art.barFill    = RegisterImage( "i_tod_timer_fill" )
        end
        -- the 54-card baked set, keyed [domain id][rarity 1..3]
        local RNAME = { [1] = "regular", [2] = "super", [3] = "ultimate" }
        local CARD_SLUG = {
            -- MAP 1 PURGE (2026-10-04): the old one-face cards of the four live classes left the zone -
            -- every one of them deals layered card v2 (TodCardArt.lua) - and so did the parked
            -- domains' faces. Only the three shared cards stay as the no-v2 fallback.
            --[[1 DAMAGE retired 2026-09-27]] [2]  = "dmg_reduction", [3]  = "bounty",
            [4]  = "luck",        --[[5 SPRINT retired 2026-09-26 (no class holds it after the Warrior + Necromancer cut); cards zoned out]] --[[6 HEADSHOT retired 2026-09-26 (Archer card cut)]]
            --[[7 MAG SIZE retired 2026-09-25]]
            -- [9] "mobility" REMOVED v15 (2026-08-31) with the domain. On the
            -- IMPACT ROUNDS precedent: an unreachable art slug is dead weight in
            -- the .ff (where an inert Lua DOMAIN/DETAIL row costs nothing), so
            -- the slug AND the three i_tod_card_mobility_* zone lines are gone.
            -- The PNGs stay in source_data. Id 9 is still MAPPED everywhere else.
            -- [10] BULLET FEED retired 2026-09-26 (Breacher card cut); its cards are zoned out
            -- 11 echo_rounds / 12 regen: slugs + the six i_tod_card_echo_rounds_*
            -- / i_tod_card_regen_* zone lines REMOVED 2026-09-03 (v16.86), the
            -- v16.80 perkslots treatment applied to the domains retired before
            -- it. Neither has a live add_domain, so no deal can roll them; the
            -- cards were still packed uncompressed (768x1152 = 3.4 MB of load
            -- RAM each). PNGs stay in source_data; ids stay MAPPED elsewhere.
            -- [13] LEECH and [14] CLEAVE retired 2026-09-26 (Warrior card cut); their cards are zoned out
            --[[17 RECOIL retired 2026-09-25]] --[[18 MELEE SPEED retired 2026-09-27 into HEAVY HANDS]]
            -- [19] PENETRATION retired 2026-09-26 (Breacher card cut); its cards are zoned out
            -- [20] THOR'S THUNDER retired 2026-09-26 (Warrior card cut); its cards are zoned out
            -- 22 chain_lunge: slug + zone lines REMOVED 2026-08-24 with the domain.
            -- CLASS TIER uniques 25..31 — art installed + zoned 2026-08-22
            -- (files (31).zip, docs/26 build-out). 24 (the TIER card) is keyed
            -- by class+tier in art.tier below, not here.
            -- [26] OVERDRIVE retired 2026-09-26 (Breacher card cut); its cards are zoned out
            -- 27 kill_reload: slug + zone lines REMOVED 2026-09-01 with the domain.
            -- [29] SUPPRESSING FIRE retired 2026-09-26 (Breacher card cut); its cards are zoned out
            -- 30 meat_grinder: slug + zone lines REMOVED 2026-09-03 (v16.86) with the domain.
            -- [31] DRAW CUT retired 2026-09-26 (Warrior card cut #2); its cards are zoned out
            -- 34 momentum: slug + zone lines REMOVED 2026-09-03 (v16.86) with the domain.
            -- [35] GIANT SLAYER retired 2026-09-26 (Archer card cut); its cards are zoned out
            -- [36] BACK ARMOR retired 2026-09-26 (Breacher card cut); its cards are zoned out
            -- [37] FORCED MARCH retired 2026-09-26 (Archer card cut); its cards are zoned out
            -- [38] / [39]: VITALITY / RECOVERY retired 2026-09-26 (Breacher card cut); the ids are the NECROMANCER's now:
            -- [39] "soul_beam" REMOVED 2026-09-27 (class pass 2): the card was renamed SOUL SUCK and the art bakes SOUL BEAM,
            -- so it draws as TEXT until re-baked (the id 58 BUCKSHOT precedent). Its three card zone lines are unzoned in the same edit.
            -- [40] PERK SLOTS retired 2026-09-27 (no perk limit); its cards are zoned out
            -- [42] FULL STEAM retired 2026-09-26 (Breacher card cut); its cards are zoned out
            -- [43] ATHLETE retired 2026-09-26 (Warrior card cut); its cards are zoned out
            -- [44] GUNSLINGER retired 2026-09-26 (Warrior card cut); its cards are zoned out
            -- [58] PELLETS art retired 2026-09-27: id 58 is BUCKSHOT now (text card until its art lands)
            -- [47] DEADSHOT retired 2026-09-25 (user: not an Archer card any more); its art is zoned out
        }
        -- ONE-IMAGE DOMAINS (v16.67, DEADSHOT 47): a domain that is only ever
        -- dealt at ONE rarity (server-side set_rarity_lock) ships ONE card file,
        -- so registering "_regular"/"_super" would name images that do not
        -- exist. Fill all three rarity slots with the one image instead — the
        -- tier cards' own { img, img, img } idiom — so PaintCard's set[ rar ]
        -- can never be nil whatever rarity arrives on the wire.
        local CARD_ONE_IMAGE = {
        }
        art.cards = {}
        for id, slug in pairs( CARD_SLUG ) do
            art.cards[ id ] = {}
            if CARD_ONE_IMAGE[ id ] then
                local img = RegisterImage( "i_tod_card_" .. slug .. "_" .. CARD_ONE_IMAGE[ id ] )
                art.cards[ id ] = { img, img, img }
            else
                -- ONE FACE PER UPGRADE (docs/187): only the _regular file is zoned
                -- now; the rarity is drawn live by TodPull. Registering the retired
                -- _super/_ultimate names would ask the .ff for images it lacks.
                art.cards[ id ][ 1 ] = RegisterImage( "i_tod_card_" .. slug .. "_" .. RNAME[ 1 ] )
            end
        end
        -- DARK UPGRADE cards, keyed by domain id. Reuses CARD_SLUG so a rename
        -- follows automatically.
        --
        -- DARK_NONE IS THE MIRROR OF set_no_dark() IN _tod_upgrades.gsc AND IT IS
        -- LOAD-BEARING, not documentation: these thirteen domains have no dark
        -- step, so their dark cards are NOT zoned, and RegisterImage on an
        -- unzoned name is undefined behavior (this file's own contract, top of
        -- file). Registering all 37 would name thirteen images that do not exist
        -- in the .ff.
        --
        -- The first ten are permanent; the last three (MAG SIZE / HANDLING /
        -- KNIFE SPEED) are PARKED and come off this list the same commit the
        -- generator learns per-gun axis levels. The art for all thirteen is
        -- already baked and waiting in source_data.
        local DARK_NONE = {
            [41] = true, [47] = true,                             -- DISTRACTION / DEADSHOT (SPRINT FIRE 21 / SECOND WIND 33 retired whole 2026-10-05)
            [29] = true, [31] = true,                             -- SUPPRESSING FIRE / MELEE RANGE (31, was DRAW CUT)
            [4]  = true,                                          -- LUCK (removed 2026-09-05)
            [19] = true, [40] = true,                             -- PENETRATION / PERK SLOTS (FIRE RATE 15 retired whole 2026-10-05)
            [62] = true, [63] = true,   -- BASH / GRAVITY SMASH: set_no_dark in _tod_upgrades.gsc, no _dark art (2026-09-26)
            [38] = true, [39] = true, [59] = true,   -- SUMMONING POWER / SOUL BEAM / SOUL BOMB: set_no_dark, no _dark art (docs/179)
            [18] = true,   -- KNIFE SPEED: dark rung retired 2026-09-26 (the sword ignores the card; see _tod_upgrades set_no_dark)
            [57] = true, [58] = true, [60] = true, [61] = true,   -- HELL'S RETRIEVER / PELLETS / STICKY C4 / CLUSTER: set_no_dark, no _dark art (docs/177, 178). Missed on install; the user's 13:49 log showed "Could not find image" for all four _dark names
        }
        if USE_DARK_CARD_ART then
            art.dark = {}
            for id, slug in pairs( CARD_SLUG ) do
                if not DARK_NONE[ id ] and not DARK_TEXT_ONLY[ id ] then
                    art.dark[ id ] = RegisterImage( "i_tod_card_" .. slug .. "_dark" )
                end
            end
        end

        -- the 8 TIER cards, keyed [class id][tier 2|3]
        if USE_TIER_CARD_ART then
            -- #TCLS, not a literal 4: the table is the authority, so adding
            -- a fifth class here is a one-line change. Identical at four.
            local TCLS = TOD_TCLS   -- file scope since 2026-09-29 (THE PULL reads it for the card-v2 tier art)
            art.tier = {}
            for c = 1, #TCLS do
                art.tier[ c ] = {}
                for t = 2, 3 do
                    -- skip a class with layered card-v2 art (TodCardArt.classes): THE PULL draws its tier card
                    -- and its old baked one left with the Map 1 purge (2026-10-04)
                    if TCLS[ c ] and not ( CoD.TodCardArt and CoD.TodCardArt.classes and CoD.TodCardArt.classes[ TCLS[ c ] ] ) then art.tier[ c ][ t ] = RegisterImage( "i_tod_card_tier_" .. TCLS[ c ] .. "_" .. t ) end
                end
            end
        end
    end
    -- ---- title plate --------------------------------------------------------
    local TitleBg = CoD.TextWithBg.new( HudRef, InstanceRef )
    TitleBg:setLeftRight( false, false, -300, 300 )
    TitleBg:setTopBottom( true, false, 148, 186 )
    TitleBg.Text:setText( "" )
    TitleBg.Bg:setRGB( PAL.glass[ 1 ], PAL.glass[ 2 ], PAL.glass[ 3 ] )
    TitleBg.Bg:setAlpha( 0.85 )
    self:addElement( TitleBg )

    if art.title then
        local TitleArt = LUI.UIImage.new()
        TitleArt:setLeftRight( false, false, -300, 300 )
        TitleArt:setTopBottom( true, false, 144, 190 )
        TitleArt:setImage( art.title )
        self:addElement( TitleArt )
        TitleBg.Bg:setAlpha( 0 )   -- the plate art replaces the flat panel
    end

    local Title = LUI.UIText.new()
    Title:setTTF( "fonts/tod_tower1.ttf" )   -- RT: no-art fallbacks in our typeface (TOD_TTF)
    Title:setLeftRight( false, false, -300, 300 )
    Title:setTopBottom( true, false, 154, 180 )
    Title:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
    Title:setRGB( PAL.line[ 1 ], PAL.line[ 2 ], PAL.line[ 3 ] )
    self:addElement( Title )
    if art.bannerUpgrade then
        -- baked banner (900x140 art at 600x93) replaces the plate + text
        local BannerImg = LUI.UIImage.new()
        BannerImg:setLeftRight( false, false, -300, 300 )
        BannerImg:setTopBottom( true, false, 122, 215 )
        BannerImg:setImage( art.bannerUpgrade )
        self:addElement( BannerImg )
    else
        Title:setText( "UPGRADE AVAILABLE - CHOOSE ONE" )
    end

    -- LUCK BOOST: a baked badge per 10% (top-right, clear of the banner);
    -- replaces the old "LUCK N0% BOOSTED THESE ROLLS" LUI text.
    local LuckLine = LUI.UIText.new()
    LuckLine:setTTF( "fonts/tod_tower1.ttf" )   -- RT: no-art fallbacks in our typeface (TOD_TTF)
    LuckLine:setLeftRight( false, false, -300, 300 )
    LuckLine:setTopBottom( true, false, 192, 212 )
    LuckLine:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
    LuckLine:setRGB( PAL.luck[ 1 ], PAL.luck[ 2 ], PAL.luck[ 3 ] )
    LuckLine:setScale( 0.85 )
    LuckLine:setText( "" )
    self:addElement( LuckLine )
    local LuckBadge = nil
    if art.badges then
        LuckBadge = LUI.UIImage.new()
        LuckBadge:setLeftRight( true, false, 950, 1230 )
        LuckBadge:setTopBottom( true, false, 150, 210 )
        LuckBadge:setAlpha( 0 )
        self:addElement( LuckBadge )
    end

    -- [tod v18.10] THE LEGEND, directly beneath the badge and in the badge's own
    -- box width (950..1230 = 280) at the same 60 height, so the two stack as one
    -- unit and the 420x90 art keeps its aspect exactly. y 214..274 is clear of
    -- everything: the cards start at CARD_Y0 226 but are centred (cx +/- 117),
    -- the LuckLine text band ends at 212, and the CLASS badge is the mirror on
    -- the far left. It shows and hides WITH the badge -- it is a caption, and a
    -- caption under nothing is noise.
    local LuckLegend = nil
    if art.luckLegend then
        LuckLegend = LUI.UIImage.new()
        LuckLegend:setLeftRight( true, false, 950, 1230 )
        LuckLegend:setTopBottom( true, false, 214, 274 )
        LuckLegend:setImage( art.luckLegend )
        LuckLegend:setAlpha( 0 )
        self:addElement( LuckLegend )
    end

    -- THE HOT STREAK + ONE SEGMENT SHORT (docs/201, 2026-10-02): two short lines under the luck badge's legend, in
    -- the map's typeface. HeatLine names the streak this deal is rolled on (CoD.TodHeat) and pulses when the deal
    -- raises it; SegLine says which guarantee a bar one segment short of it just missed (true information - the
    -- reason to bank luck before the next deal). y 280..314: under the legend (214..274), over card B's ladder
    -- (x 927.., y 362..). The panel has no scriptNotify subscription of its own: the HUD menu's tod_luck_heat
    -- handler calls self.todHeatPaint.
    local function LineText( opts )
        local t
        if CoD.TodGlyphText then
            t = CoD.TodGlyphText.new( opts )
        else
            t = LUI.UIText.new()
            t:setLeftRight( true, false, opts.left, opts.right )
            t:setTopBottom( true, false, opts.top, opts.bottom )
            t:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
            t:setRGB( opts.rgb[ 1 ], opts.rgb[ 2 ], opts.rgb[ 3 ] )
        end
        t:setAlpha( 0 )
        self:addElement( t )
        return t
    end
    local HeatLine = LineText( { left = 950, right = 1230, top = 280, bottom = 296, align = "center", pool = 22, rgb = { 1, 0.52, 0.14 } } )
    local SegLine = LineText( { left = 950, right = 1230, top = 300, bottom = 314, align = "center", pool = 26, rgb = PAL.luck } )
    local HEAT_WORD = { "WARM", "HEATING UP", "ON FIRE" }
    local heatShown = 0
    local function HeatPaint( h, pop )
        h = tonumber( h ) or 0
        heatShown = h
        HeatLine:completeAnimation()
        local w = HEAT_WORD[ h ]
        if not w then
            HeatLine:setText( "" )
            HeatLine:setAlpha( 0 )
            return
        end
        HeatLine:setText( "HOT STREAK - " .. w )
        if pop then
            HeatLine:setAlpha( 0.15 )
            HeatLine:beginAnimation( "tod_heat_line", 260, false, false, CoD.TweenType.Linear )
        end
        HeatLine:setAlpha( 1 )
    end
    self.todHeatPaint = HeatPaint

    -- [tod v16] CLASS badge -- the luck badge's mirror, same 280x60 at the same
    -- height on the opposite side. The tier-gate strip USED to fall back to this
    -- exact rect when no card was dealt; it now sits one row lower (see the
    -- TierGateImg placement below) so the two can never overlap.
    local ClassBadge = nil
    if art.classPlate then
        ClassBadge = LUI.UIImage.new()
        ClassBadge:setLeftRight( true, false, 50, 330 )
        ClassBadge:setTopBottom( true, false, 150, 210 )
        ClassBadge:setAlpha( 0 )
        self:addElement( ClassBadge )
    end

    -- SWITCH-HINT plate (controller/KBM baked; the countdown stays live text)
    -- 280x43 = the art's true 460x70 aspect (was 320x32 — visibly stretched,
    -- user 2026-08-20); below the powerup tray band, countdown text BELOW it
    -- (they overlapped before).
    local SwitchHintImg = nil
    if art.hintFrame then
        SwitchHintImg = LUI.UIImage.new()
        -- [tod v16.83] BACK TO ONE LINE, so back to ONE geometry. v16.32 grew
        -- this to 320x49 purely to fit a second text line; with LOCK said only
        -- under the focused card there is one line again, and 280x43 is the
        -- art's own 460/70 aspect. Both paths share it now — the frame path
        -- and the baked path can no longer be different sizes.
        SwitchHintImg:setLeftRight( false, false, -140, 140 )
        SwitchHintImg:setTopBottom( true, false, 650, 693 )
        SwitchHintImg:setAlpha( 0 )
        self:addElement( SwitchHintImg )
    end

    -- [tod v16.32, one line since v16.83] the key line drawn over the blank
    -- frame (USE_HINT_FRAME_ART; see SwitchLine1 at the top of the file).
    -- Centred in the plate's 650..693 band.
    local SwitchHintText1 = nil
    if SwitchHintImg and USE_HINT_FRAME_ART and art.hintFrame then
        SwitchHintText1 = LUI.UIText.new()
        SwitchHintText1:setLeftRight( false, false, -134, 134 )
        SwitchHintText1:setTopBottom( true, false, 663, 680 )
        SwitchHintText1:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
        SwitchHintText1:setTTF( "fonts/tod_tower1.ttf" )   -- RT: our typeface (TOD_TTF)
        SwitchHintText1:setRGB( 1, 1, 1 )
        SwitchHintText1:setAlpha( 0 )
        self:addElement( SwitchHintText1 )
    end

    -- [tod v16.88] THE SWITCH GLYPHS — one beside each card, on the side it
    -- moves to. DIRECTION IS A POSITION, not a sentence: the left glyph sits
    -- outside card A (which starts at x 369), the right one outside card B
    -- (which ends at 911), both on the cards' mid-height. This is what
    -- REPLACES the bottom plate; that plate stays constructed above purely as
    -- the flag-off fallback, and ShowSwitchPlate picks exactly one of the two.
    --
    -- Each side is an image plus a text slot. On a pad the image is the d-pad
    -- glyph and the text is empty — the lit arm carries the meaning. On a
    -- keyboard the image is the WIDE blank keycap and the text is the bind
    -- token, engine-expanded into whatever that player actually bound, drawn
    -- INSIDE the cap. The wide cap is used for both because the expansion can
    -- be as long as "MOUSE3"; a single letter simply centres in it.
    -- THE PAIR SITS CENTRED UNDER THE CARDS, in the band the old switch plate
    -- occupied (user 2026-09-03: *"i wanted to keep the position under the
    -- cards in the middle of the screen. Same spot as before"*). v16.88 first
    -- put them out at the cards' outer edges to make direction spatial; the
    -- user's call is that the familiar spot matters more, and the d-pad glyph
    -- carries its own arrow anyway, so nothing is lost by moving them back.
    --
    -- BOTH RECTS ARE SET PER DEVICE by the writer, not here: the pad glyph is
    -- square (48) and the keycap is wide and short (72 x 36), so a single
    -- construction-time rect cannot serve both without stretching one of them.
    -- Each slot stores only its SIDE; the writer does the arithmetic about a
    -- fixed screen centre so the pair stays centred at either size.
    local SwitchGlyph = {}
    if USE_CARD_GLYPH_ART and art.padDpadL then
        local function GlyphSlot( side )
            local g = { side = side }
            g.Img = LUI.UIImage.new()
            g.Img:setAlpha( 0 )
            self:addElement( g.Img )
            g.Text = LUI.UIText.new()
            g.Text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
            g.Text:setRGB( 0.06, 0.07, 0.10 )   -- dark ink on the pale keycap
            g.Text:setAlpha( 0 )
            self:addElement( g.Text )
            -- [tod v17.27] the key name in the MAP'S OWN TYPEFACE. Built after
            -- g.Img so the glyphs draw over the cap, and given g.Text as the
            -- no-glyph fallback. See TodKeycap.lua.
            g.Key = TodKeycapMake( self, g.Text, InstanceRef )
            return g
        end
        SwitchGlyph.L = GlyphSlot( -1 )
        SwitchGlyph.R = GlyphSlot(  1 )
    end

    -- ---------------------------------------------------------------------
    -- [tod v18.32] THE WORD BETWEEN THEM — twin of the class draft, where the
    -- whole argument lives. Short version: v16.88 replaced the baked switch
    -- plate with two glyphs and hid the plate for the whole match, and the
    -- plate was the only thing that said SWITCH. `SwitchLine1()` still spells
    -- the documented copy and has been unreachable on every real build since.
    -- Drawn in the map's baked typeface so the row is one piece of lettering.
    -- ---------------------------------------------------------------------
    local SwitchWord, SwitchWordText = nil, nil
    if SwitchGlyph.L then
        SwitchWordText = LUI.UIText.new()
        SwitchWordText:setTTF( "fonts/tod_tower1.ttf" )   -- RT: no-art fallbacks in our typeface (TOD_TTF)
        SwitchWordText:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
        SwitchWordText:setRGB( PAL.line[ 1 ], PAL.line[ 2 ], PAL.line[ 3 ] )
        SwitchWordText:setAlpha( 0 )
        self:addElement( SwitchWordText )
        if CoD.TodGlyphRow then
            SwitchWord = CoD.TodGlyphRow.make( self, 8 )   -- "SWITCH" is 6
            SwitchWord.setRGB( PAL.line[ 1 ], PAL.line[ 2 ], PAL.line[ 3 ] )
        end
    end

    -- ONE writer for the switch plate (image + its lines): every show/hide
    -- site goes through here so the frame path and the baked path can never
    -- disagree about what is on screen.
    local function ShowSwitchPlate( on )
        -- [tod v16.88] TWO PRESENTATIONS, EXACTLY ONE OF THEM VISIBLE. With the
        -- glyphs available this writer drives them and leaves the bottom plate
        -- hidden for the whole match; with the flag off it falls back to the
        -- v16.83 plate untouched. Keeping both behind ONE writer is what stops
        -- the two from ever being on screen together.
        if SwitchGlyph.L then
            local pad = UsingController()
            -- SCREEN CENTRE, then half-width + half-gap out on each side.
            -- 640 is the 1280 canvas centre; the y band is the old plate's.
            local CX, HW, Y0, Y1
            if pad then
                CX, HW, Y0, Y1 = 640, 24, 644, 692   -- 48 sq glyph
            else
                -- 96 x 48, the art's true 2:1. [v17.4] widened it from 72 x 36
                -- on the premise that a MULTI-BOUND action needs the room —
                -- `+frag` is on BOTH G and MOUSE3 in the user's bindings_0.cfg,
                -- and the engine expands that to `G OR MIDDLE MOUSE`.
                --
                -- [v17.27] THE ROOM WAS NEVER THE PROBLEM. That expansion is
                -- now TRIMMED to its first key, and the key is drawn in the
                -- map's baked typeface by CoD.TodKeycap, which measures it and
                -- shrinks only if it truly will not fit. The size stays because
                -- it is a good size for one big legible key, not because a
                -- 17-character string has to fit in it.
                CX, HW, Y0, Y1 = 640, 48, 644, 692   -- 96 x 48 keycap
            end
            -- [tod v18.32] the word sets the spacing, so the two buttons flank
            -- it instead of touching each other. WCAP is the lettering height;
            -- WPAD is the air between a button and the word.
            local WCAP, WPAD = 17, 18
            local wordW = -1
            if SwitchWord then
                wordW = SwitchWord.measure( "SWITCH", WCAP, CoD.TodGlyphRow.nameSet )
            end
            local wordOk = ( wordW > 0 )
            if not wordOk then
                wordW = 78          -- the UIText fallback's box
            end
            local HALF = HW + WPAD + wordW / 2
            local WCY  = ( Y0 + Y1 ) / 2
            if not on then
                if SwitchWord then SwitchWord.hide() end
                SwitchWordText:setAlpha( 0 )
            elseif wordOk then
                -- the row draws RIGHT-aligned; baseline is half a cap below
                -- the optical centre, the same rule TodKeycap uses.
                SwitchWord.set( "SWITCH", WCAP, CX + wordW / 2, WCY + WCAP / 2, CoD.TodGlyphRow.nameSet )
                SwitchWordText:setAlpha( 0 )
            else
                SwitchWordText:setLeftRight( true, false, CX - wordW / 2, CX + wordW / 2 )
                SwitchWordText:setTopBottom( true, false, WCY - 9, WCY + 9 )
                SwitchWordText:setText( "SWITCH" )
                SwitchWordText:setAlpha( 0.95 )
            end
            local function Paint( g, padImg, tok )
                if not on then
                    g.Img:setAlpha( 0 )
                    g.Key.hide()
                    return
                end
                local cx = CX + g.side * HALF
                g.Img:setLeftRight( true, false, cx - HW, cx + HW )
                g.Img:setTopBottom( true, false, Y0, Y1 )
                -- [tod v18.16] THE LAST WORD ON WHAT GETS DRAWN, and it reads
                -- the very string it is about to draw. `pad` is a decision made
                -- once, further up, from a latch and a device probe; TodPadWord
                -- asks the only question that actually matters here — "is this
                -- token going to render as LT/RT?" — and if so we draw the
                -- d-pad glyph instead. A stale latch, a failed widget require or
                -- a device switched mid-menu cannot get a pad word onto a
                -- keycap any more, because the check is on the text, not on a
                -- belief about the player. The d-pad is a live input lane in
                -- both menus, so the glyph it draws is always true.
                if pad or TodPadWord( tok ) then
                    g.Img:setImage( padImg )
                    g.Key.hide()
                else
                    -- [tod v17.27] the cap's rect is ALL TodKeycap needs: it
                    -- measures the key name in the baked typeface and picks the
                    -- size that fits the art's own bright face. It also trims
                    -- the multi-bind (`+frag` renders as `G OR MIDDLE MOUSE`).
                    g.Img:setImage( art.keyWide )
                    if g.Key.paint( cx - HW, Y0, HW * 2, Y1 - Y0, tok ) == nil then
                        -- [tod v18.48] THE KEYCAP REFUSED IT. The name could
                        -- not be drawn in our typeface AND carries a high byte,
                        -- i.e. the engine is handing back a button PICTURE — so
                        -- draw the button, rather than a pale cap with an
                        -- engine icon squatting inside it (the 2026-09-08
                        -- screenshot). This is the ONLY place the glyph test
                        -- still decides anything, and the worst it can do is
                        -- put one wrong glyph on screen; it cannot flip the
                        -- menu's device, which is what v18.47 did.
                        local half = ( Y1 - Y0 ) / 2
                        g.Img:setImage( padImg )
                        g.Img:setLeftRight( true, false, cx - half, cx + half )
                    end
                end
                g.Img:setAlpha( 1 )
            end
            Paint( SwitchGlyph.L, art.padDpadL, "[{+smoke}]" )
            Paint( SwitchGlyph.R, art.padDpadR, "[{+frag}]" )
            if SwitchHintImg then
                SwitchHintImg:setAlpha( 0 )
                if SwitchHintText1 then
                    SwitchHintText1:setAlpha( 0 )
                end
            end
            return
        end
        if not SwitchHintImg then
            return
        end
        if not on then
            SwitchHintImg:setAlpha( 0 )
            if SwitchHintText1 then
                SwitchHintText1:setAlpha( 0 )
            end
            return
        end
        if SwitchHintText1 then
            SwitchHintImg:setImage( art.hintFrame )
            SwitchHintText1:setText( Engine.Localize( SwitchLine1() ) )
            SwitchHintText1:setAlpha( 0.95 )
        end
        SwitchHintImg:setAlpha( 0.9 )
    end

    -- ONE writer for a card's under-plate. mode = "lock" (focused: the key
    -- line), "locked" (the baked LOCKED plate — it names no key, so it stays
    -- baked under both paths), "off". `a` = alpha for the visible modes.
    local function CardHint( card, mode, a )
        if not card.HintImg then
            return
        end
        if mode == "off" then
            card.HintImg:setAlpha( 0 )
            if card.HintText then
                card.HintText:setAlpha( 0 )
            end
            if card.LockGlyph then
                card.LockGlyph:setAlpha( 0 )
                card.LockKey.hide()
            end
            return
        end
        if mode == "locked" then
            card.HintImg:setImage( art.hintLocked )
            if card.HintText then
                card.HintText:setAlpha( 0 )
            end
            if card.LockGlyph then
                card.LockGlyph:setAlpha( 0 )
                card.LockKey.hide()
            end
        elseif card.LockGlyph then
            -- [tod v16.88] THE BAKED PLATE SAYS THE WORDS; THE GAP HOLDS THE
            -- BUTTON. `i_tod_hold_plate` carries "HOLD" and "TO LOCK" as art
            -- with a deliberate empty gap between them, and the glyph drops
            -- into that gap: the A button on a pad, a blank keycap carrying
            -- the engine-expanded jump bind on a keyboard. No LUI text on the
            -- plate itself any more.
            card.HintImg:setImage( art.holdPlate )
            if card.HintText then
                card.HintText:setAlpha( 0 )
            end
            -- [tod v18.32] the jump token gets the ICON test as well: if the
            -- engine is going to hand us a picture of the A button, the pale
            -- keycap must not be drawn behind it (2026-09-08 screenshot).
            -- [tod v18.32] BOTH SIZES COME OUT OF THE MEASURED GAP, each art at
            -- its own aspect — twin of the draft. The old literals (30 and 64)
            -- were typed against a 56 px gap and the wide one overhung the
            -- baked lettering.
            local cx, cy = card.lockCx, card.lockCy
            -- [tod v18.48] DEVICE ONLY. v18.47 OR'd the jump token's icon
            -- test in here; that test fires on a keyboard too, so it put every
            -- KBM player on the A button. The keycap's own fallback still
            -- refuses to draw a picture inside itself — that is where the
            -- guard belongs, not in the device choice.
            if UsingController() then
                local s = math.floor( card.plateH * 0.85 / 2 )   -- half of ~28
                card.LockGlyph:setImage( art.padBtnA )
                card.LockGlyph:setLeftRight( true, false, cx - s, cx + s )
                card.LockGlyph:setTopBottom( true, false, cy - s, cy + s )
                card.LockKey.hide()
            else
                -- [tod v17.27] TodKeycap measures the key name in the map's own
                -- typeface and sizes it to the cap's bright face, so the cap
                -- only has to be the right SHAPE and inside the gap.
                local w = math.floor( ( card.lockGapW - 2 ) / 2 ) * 2
                local h = math.floor( w / 2 )                    -- the art is 2:1
                card.LockGlyph:setImage( art.keyWide )
                card.LockGlyph:setLeftRight( true, false, cx - w / 2, cx + w / 2 )
                card.LockGlyph:setTopBottom( true, false, cy - h / 2, cy + h / 2 )
                card.LockKey.paint( cx - w / 2, cy - h / 2, w, h, "[{+gostand}]", a )
            end
            card.LockGlyph:setAlpha( a )
        elseif card.HintText then
            card.HintImg:setImage( art.hintFrame )
            card.HintText:setText( Engine.Localize( LockLine() ) )
            card.HintText:setAlpha( a )
        end
        card.HintImg:setAlpha( a )
    end

    -- (BOSS BANNERS lived here until 2026-08-20, when they moved to
    -- LUI.createMenu.tod_upgrade — this panel's root alpha is 0 outside upgrade
    -- events, which swallowed the banner in the ONLY scenario it fired: round
    -- start. They were then DELETED outright 2026-08-22, user: unnecessary.
    -- Kept as a warning: anything that must render outside an upgrade event
    -- belongs at the MENU root, not in this panel.)

    -- [tod v14.35] WHY THERE IS NO TIER CARD IN THIS DEAL.
    --
    -- Sits in the clear band between the cards' input hints (which end at
    -- CARD_Y1 + 35 = 612) and the countdown (697) — measured, not guessed,
    -- because both neighbours are baked-art rows and an overlap here would land
    -- on the one screen the player cannot look away from.
    --
    -- Shown ONLY when the floor gate is the sole thing withholding the card
    -- (GSC tier_floor_pending decides; 0 = say nothing). It is deliberately not
    -- a general "here is why you got what you got" line: a message that fires
    -- for every reason teaches players to stop reading it.
    --
    -- BAKED ART is the real thing here (docs/50, two badges keyed by tier); the
    -- LUI text below is the no-art fallback and is what ships until the PNGs
    -- land. Amber, not the luck cyan — this is a requirement, not a bonus.
    --
    -- IT IS THE EXACT MIRROR OF THE LUCK BADGE: that one is 280x60 at
    -- x 950..1230, y 150..210, so this is 280x60 at x 50..330 on the same row —
    -- the banner between them spans 340..940, so both gutters are free and the
    -- panel's two deal-status indicators become a matched pair. Source canvas
    -- 420x90 = the luck badge's own, aspect 4.667 held EXACTLY (the v6.6
    -- stretched-plate lesson: never draw a plate off its own aspect).
    --
    -- IT IS *NOT* UNDER THE CARDS, and that is measured rather than preferred:
    -- the band below them is already full. The cards' input hints end at
    -- CARD_Y1 + 35 = 612, SwitchHintImg occupies 650..693, and the countdown
    -- 697..717 — 38 free pixels, which cannot hold a legible plate. Anything
    -- placed there lands on the switch hint.
    -- DECLARED HERE, CONSTRUCTED AFTER THE CARDS — see the addElement below.
    -- LUI draws in addElement order, so an element added before CardA/CardB is
    -- BEHIND them. That was harmless while this badge lived in the empty
    -- top-left gutter and fatal the moment it became a stamp across the card:
    -- it would have been invisible, and "the art did not pack" is exactly what
    -- that looks like from the outside.
    local TierGateImg = nil
    -- The FALLBACK sits in that 38px band instead, because unstyled text needs
    -- the full panel width to stay legible and would clip inside the badge box.
    -- Different position from the art on purpose; only one of the two is ever
    -- visible.
    local TierLine = LUI.UIText.new()
    TierLine:setTTF( "fonts/tod_tower1.ttf" )   -- RT: no-art fallbacks in our typeface (TOD_TTF)
    TierLine:setLeftRight( false, false, -300, 300 )
    TierLine:setTopBottom( true, false, 618, 642 )
    TierLine:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
    TierLine:setScale( 0.85 )
    TierLine:setRGB( 1.0, 0.78, 0.30 )
    TierLine:setText( "" )
    self:addElement( TierLine )

    -- countdown to auto-select (below the cards; red when nearly out)
    local TimeLine = LUI.UIText.new()
    TimeLine:setTTF( "fonts/tod_tower1.ttf" )   -- RT: no-art fallbacks in our typeface (TOD_TTF)
    TimeLine:setLeftRight( false, false, -300, 300 )
    TimeLine:setTopBottom( true, false, 697, 717 )
    TimeLine:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
    TimeLine:setScale( 0.9 )
    TimeLine:setText( "" )
    self:addElement( TimeLine )

    -- [tod v16.88] THE COUNTDOWN AS A DRAINING BAR. "AUTO IN 15s" was the last
    -- pure-LUI element on the control UI, and a bar says the same thing with no
    -- digits to render — which is also why it needs no per-number art. Same two
    -- images as the card hold bar: a countdown and a hold are the same object,
    -- one draining and one filling. 280 x 15 is the art's true 460/24 aspect;
    -- it sits in the band the deleted bottom plate used to occupy.
    -- THE PANEL IS NEVER TOLD THE TIMEOUT LENGTH. `todUpgTime` is a countdown
    -- of whole seconds and no field carries its starting value (the pool is at
    -- its proven 61-bit ceiling — see __init__ — so adding one is not on the
    -- table). The bar therefore learns the maximum by WATCHING: the first tick
    -- of a deal is the largest value it will ever see, so remember the highest
    -- and reset on hide. That is exact for a round deal and for the shorter
    -- station deal alike, with no server change at all.
    local timeMaxSeen = 0
    local TimeTrack, TimeFill = nil, nil
    if USE_CARD_GLYPH_ART and art.barTrack then
        TimeTrack = LUI.UIImage.new()
        TimeTrack:setLeftRight( false, false, -140, 140 )
        TimeTrack:setTopBottom( true, false, 700, 714 )
        TimeTrack:setImage( art.barTrack )
        TimeTrack:setAlpha( 0 )
        self:addElement( TimeTrack )

        TimeFill = LUI.UIImage.new()
        TimeFill:setLeftRight( false, false, -140, 140 )
        TimeFill:setTopBottom( true, false, 700, 714 )
        TimeFill:setImage( art.barFill )
        TimeFill:setAlpha( 0 )
        self:addElement( TimeFill )
    end

    -- ---- one card (built twice) --------------------------------------------
    -- xLo..xHi on the 1280 canvas; bind = the input label on the footer.
    -- PORTRAIT layout (2:3 card-set art). The composite elements survive as
    -- the no-art fallback, restacked portrait; with the card set on, the
    -- single CardImg carries frame+icon+title+desc+rarity and the composite
    -- texts are blanked in PaintCard. Lv + Bind + hold bar stay LUI (live).
    local function BuildCard( xLo, xHi, bind )
        local card = {}

        local Bg = CoD.TextWithBg.new( HudRef, InstanceRef )
        Bg:setLeftRight( true, false, xLo, xHi )
        Bg:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
        Bg.Text:setText( "" )
        Bg.Bg:setRGB( PAL.glass[ 1 ], PAL.glass[ 2 ], PAL.glass[ 3 ] )
        Bg.Bg:setAlpha( 0.85 )
        self:addElement( Bg )
        card.Bg = Bg

        -- ---- REVEAL LAYER (v14.52) -----------------------------------------
        -- Added HERE, before every face element, because LUI draws in
        -- addElement order and both of these belong BEHIND the card: the aura
        -- stands proud of the card rect (so it reads as a halo around opaque
        -- 2:3 card art), and the socket is what you look at while the face is
        -- still alpha 0. The Flare is the mirror case and is built after BOTH
        -- cards — see below.
        --
        -- DELIBERATELY OUTSIDE card.group. That group's alpha is driven by
        -- "does this slot have a domain yet", which is exactly false for the
        -- whole socket phase; joining it would blank the socket the moment it
        -- matters. The aura instead follows focus through card.glowMul.
        local Glow = CoD.TextWithBg.new( HudRef, InstanceRef )
        Glow:setLeftRight( true, false, xLo - REVEAL_GLOW_PAD, xHi + REVEAL_GLOW_PAD )
        Glow:setTopBottom( true, false, CARD_Y0 - REVEAL_GLOW_PAD, CARD_Y1 + REVEAL_GLOW_PAD )
        Glow.Text:setText( "" )
        Glow.Bg:setAlpha( 1 )
        Glow:setAlpha( 0 )
        self:addElement( Glow )
        card.Glow = Glow
        card.glowBase = 0    -- set on land, read by the focus/flash branches
        card.glowMul  = 1

        -- The socket is two flat panels, not one bordered one: a rarity-tinted
        -- rect with a dark rect inset over it leaves a REVEAL_SOCKET_PAD rim,
        -- which is the only way to draw a border out of CoD.TextWithBg. The rim
        -- is what carries the charge — its alpha ramps over the server's hold.
        local SockRim = CoD.TextWithBg.new( HudRef, InstanceRef )
        SockRim:setLeftRight( true, false, xLo, xHi )
        SockRim:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
        SockRim.Text:setText( "" )
        SockRim.Bg:setAlpha( 1 )
        SockRim:setAlpha( 0 )
        self:addElement( SockRim )
        card.SockRim = SockRim

        local SockFill = CoD.TextWithBg.new( HudRef, InstanceRef )
        SockFill:setLeftRight( true, false, xLo + REVEAL_SOCKET_PAD, xHi - REVEAL_SOCKET_PAD )
        SockFill:setTopBottom( true, false, CARD_Y0 + REVEAL_SOCKET_PAD, CARD_Y1 - REVEAL_SOCKET_PAD )
        SockFill.Text:setText( "" )
        SockFill.Bg:setRGB( PAL.glass[ 1 ], PAL.glass[ 2 ], PAL.glass[ 3 ] )
        SockFill.Bg:setAlpha( 1 )
        SockFill:setAlpha( 0 )
        self:addElement( SockFill )
        card.SockFill = SockFill

        if art.cards then
            -- THE card: one baked image per (domain, rarity)
            local CardImg = LUI.UIImage.new()
            CardImg:setLeftRight( true, false, xLo, xHi )
            CardImg:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
            self:addElement( CardImg )
            card.CardImg = CardImg
            Bg.Bg:setAlpha( 0 )   -- the art IS the card
        end

        local Top = CoD.TextWithBg.new( HudRef, InstanceRef )
        Top:setLeftRight( true, false, xLo, xHi )
        Top:setTopBottom( true, false, CARD_Y0, CARD_Y0 + 4 )
        Top.Text:setText( "" )
        Top.Bg:setAlpha( 0.95 )
        self:addElement( Top )
        card.Top = Top

        local Bot = CoD.TextWithBg.new( HudRef, InstanceRef )
        Bot:setLeftRight( true, false, xLo, xHi )
        Bot:setTopBottom( true, false, CARD_Y1 - 4, CARD_Y1 )
        Bot.Text:setText( "" )
        Bot.Bg:setAlpha( 0.95 )
        self:addElement( Bot )
        card.Bot = Bot

        local function Line( topPx, botPx, scale )
            local t = LUI.UIText.new()
            t:setTTF( "fonts/tod_tower1.ttf" )   -- RT: no-art fallbacks in our typeface (TOD_TTF)
            t:setLeftRight( true, false, xLo + 14, xHi - 14 )
            t:setTopBottom( true, false, topPx, botPx )
            t:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
            t:setScale( scale )
            self:addElement( t )
            return t
        end

        -- fallback composite stack (blanked when the card set is on)
        card.Tag   = Line( CARD_Y0 + 12, CARD_Y0 + 34, 0.8 )     -- SUPER / ULTIMATE
        card.Name  = Line( CARD_Y0 + 36, CARD_Y0 + 68, 1.15 )    -- domain name
        card.Desc  = Line( CARD_Y0 + 72, CARD_Y0 + 92, 0.75 )    -- effect line
        card.Desc:setRGB( PAL.dim[ 1 ], PAL.dim[ 2 ], PAL.dim[ 3 ] )
        -- (the "Lv X > Y" overlay was REMOVED 2026-08-20 — no LUI text on the
        -- cards, the doctrine; the baked rarity gem "+N" carries the gain)
        card.Bind  = Line( CARD_Y1 + 6, CARD_Y1 + 30, 0.9 )      -- fallback text (blank w/ hint art)
        if art.hintFrame then
            -- baked input-hint plate under the card (460x70 art at 200x30)
            local HintImg = LUI.UIImage.new()
            HintImg:setLeftRight( true, false, xLo + 6, xHi - 6 )
            -- ASPECT, and it must be RECOMPUTED whenever the card rect moves.
            -- v10.4 set 26px for the SHRUNKEN 181px card. v10.16 reverted the
            -- card to 213x320 (drawn width 201) but left this literal alone —
            -- and the revert's own comment claiming "every overlay is keyed off
            -- these four numbers, so nothing else needed touching" was wrong
            -- about exactly this one. 201/26 = 7.73 against the art's 460/70 =
            -- 6.571, i.e. ~18% horizontally stretched. 31px restores it.
            -- THE RULE: height = drawn_width / (460/70). Drawn width is
            -- (xHi-6) - (xLo+6) = CARD_AX1 - CARD_AX0 - 12.
            -- [tod v16.88] +35 -> +38: 222 x 34 is the hold plate's true
            -- 460/70 aspect, and the extra 3 px is what lets a 30 px button
            -- glyph sit in its gap without touching the rim. The hold bar
            -- below moved down with it (see HoldTrack).
            -- [tod v18.32] and now the rule is CODE, not a literal that happens
            -- to satisfy it. Still 34 today; it stays right the next time the
            -- card width moves — which is exactly how the class draft's copy of
            -- this plate came to be 27% too tall when a fifth card narrowed it.
            local plateH = math.floor( ( ( xHi - 6 ) - ( xLo + 6 ) ) / PLATE_ASPECT + 0.5 )
            HintImg:setTopBottom( true, false, CARD_Y1 + 4, CARD_Y1 + 4 + plateH )
            HintImg:setAlpha( 0 )
            self:addElement( HintImg )
            card.HintImg = HintImg
            -- [tod v16.88] the button that drops into the plate's baked gap,
            -- centred on the card. Two sizes: the round A button at 30 px, the
            -- wide keycap at 52 px (it may have to hold "MOUSE3"). CardHint
            -- sets the image, the width and the text.
            if USE_CARD_GLYPH_ART and art.holdPlate then
                local cx = ( xLo + xHi ) / 2
                -- [tod v18.32] where the GAP is, from the plate as drawn. Both
                -- rects are written by CardHint (the pad button is square, the
                -- keycap is 2:1 — no one rect serves both unstretched).
                local plateL = xLo + 6
                local plateW = ( xHi - 6 ) - plateL
                card.plateH   = math.floor( plateW / PLATE_ASPECT + 0.5 )
                card.lockCx   = math.floor( plateL + plateW * PLATE_GAP_CX )
                card.lockCy   = math.floor( CARD_Y1 + 4 + card.plateH * PLATE_INK_CY )
                card.lockGapW = math.floor( plateW * PLATE_GAP_W )
                local LockGlyph = LUI.UIImage.new()
                LockGlyph:setAlpha( 0 )
                self:addElement( LockGlyph )
                card.LockGlyph = LockGlyph
                local LockKeyText = LUI.UIText.new()
                LockKeyText:setLeftRight( true, false, cx - 26, cx + 26 )
                LockKeyText:setTopBottom( true, false, CARD_Y1 + 13, CARD_Y1 + 29 )
                LockKeyText:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
                LockKeyText:setRGB( 0.06, 0.07, 0.10 )
                LockKeyText:setAlpha( 0 )
                self:addElement( LockKeyText )
                card.LockKeyText = LockKeyText
                -- [tod v17.27] the key name in the map's typeface, over this
                -- cap. Built last so the glyphs draw above plate and cap alike.
                card.LockKey = TodKeycapMake( self, LockKeyText, InstanceRef )
            end
            if USE_HINT_FRAME_ART and art.hintFrame then
                -- [tod v16.32] the key line over the blank frame; centred on
                -- the plate (plate spans CARD_Y1+4..+35, centre +19.5)
                local HintText = LUI.UIText.new()
                HintText:setLeftRight( true, false, xLo + 16, xHi - 16 )
                HintText:setTopBottom( true, false, CARD_Y1 + 14, CARD_Y1 + 26 )
                HintText:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
                HintText:setTTF( "fonts/tod_tower1.ttf" )   -- RT: our typeface (TOD_TTF)
                HintText:setRGB( 1, 1, 1 )
                HintText:setAlpha( 0 )
                self:addElement( HintText )
                card.HintText = HintText
            end
        end
        card.Bind:setText( bind )
        card.Bind:setRGB( PAL.line[ 1 ], PAL.line[ 2 ], PAL.line[ 3 ] )

        -- Hold-to-lock progress bar (under the card, below the bind line;
        -- driven by todUpgHold 0..15). Track + fill.
        local HoldTrack = CoD.TextWithBg.new( HudRef, InstanceRef )
        HoldTrack:setLeftRight( true, false, xLo + 14, xHi - 14 )
        -- pushed +34 -> +39 to clear the un-squashed hint plate above (it now
        -- ends at CARD_Y1 + 35)
        HoldTrack:setTopBottom( true, false, CARD_Y1 + 39, CARD_Y1 + 43 )
        HoldTrack.Text:setText( "" )
        HoldTrack.Bg:setRGB( PAL.dim[ 1 ], PAL.dim[ 2 ], PAL.dim[ 3 ] )
        HoldTrack.Bg:setAlpha( 0 )
        self:addElement( HoldTrack )
        card.HoldTrack = HoldTrack

        local HoldFill = CoD.TextWithBg.new( HudRef, InstanceRef )
        HoldFill:setLeftRight( true, false, xLo + 14, xLo + 14 )
        HoldFill:setTopBottom( true, false, CARD_Y1 + 39, CARD_Y1 + 43 )
        HoldFill.Text:setText( "" )
        HoldFill.Bg:setRGB( PAL.pick[ 1 ], PAL.pick[ 2 ], PAL.pick[ 3 ] )
        HoldFill.Bg:setAlpha( 0 )
        self:addElement( HoldFill )
        card.HoldFill = HoldFill

        -- [tod v16.88] THE HOLD BAR IN ART. Deliberately NEW elements rather
        -- than re-skinning the two above: `CoD.TextWithBg` is defined in the
        -- bytecode LUI core, so whether its `.Bg` accepts setImage is
        -- UNVERIFIABLE from this tree — and a wrong guess in LUI fails
        -- SILENTLY, taking the whole menu with it. The colour quads stay
        -- constructed and are simply held at alpha 0 whenever the art is on;
        -- with the flag off they are still the bar, unchanged.
        -- Geometry: the plate above now ends at CARD_Y1 + 38, so the bar sits
        -- at +42 and is 10 px tall — the timer art's true 460/24 aspect at
        -- this width, where the old quad was a flat 4 px.
        if USE_CARD_GLYPH_ART and art.barTrack then
            local BarTrack = LUI.UIImage.new()
            BarTrack:setLeftRight( true, false, xLo + 14, xHi - 14 )
            BarTrack:setTopBottom( true, false, CARD_Y1 + 42, CARD_Y1 + 52 )
            BarTrack:setImage( art.barTrack )
            BarTrack:setAlpha( 0 )
            self:addElement( BarTrack )
            card.BarTrack = BarTrack

            local BarFill = LUI.UIImage.new()
            BarFill:setLeftRight( true, false, xLo + 14, xLo + 14 )
            BarFill:setTopBottom( true, false, CARD_Y1 + 42, CARD_Y1 + 52 )
            BarFill:setImage( art.barFill )
            BarFill:setAlpha( 0 )
            self:addElement( BarFill )
            card.BarFill = BarFill
        end
        card.holdLo = xLo + 14
        card.holdHi = xHi - 14

        -- THE BURST. Added LAST inside BuildCard so it draws over this card's
        -- own face. It does not need to clear the OTHER card: the two rects are
        -- 74px apart and the burst grows by at most REVEAL_FLARE_GROW (34).
        local Flare = CoD.TextWithBg.new( HudRef, InstanceRef )
        Flare:setLeftRight( true, false, xLo, xHi )
        Flare:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
        Flare.Text:setText( "" )
        Flare.Bg:setAlpha( 1 )
        Flare:setAlpha( 0 )
        self:addElement( Flare )
        card.Flare = Flare

        -- own geometry, so the reveal helpers take a card and nothing else
        card.xLo, card.xHi = xLo, xHi
        card.xMid = ( xLo + xHi ) * 0.5

        card.group = { Bg, Top, Bot, card.Tag, card.Name, card.Desc, card.Bind }
        if card.CardImg then
            card.group[ #card.group + 1 ] = card.CardImg
        end
        return card
    end

    local function SetCardAlpha( card, a )
        for i = 1, #card.group do
            -- CardImg stays hidden while it does not carry this card (see imgLive)
            if card.group[ i ] == card.CardImg and card.imgLive == false then
                card.group[ i ]:setAlpha( 0 )
            else
                card.group[ i ]:setAlpha( a )
            end
        end
    end

    -- THE PULL's dim + edge glow draw BEHIND the cards: built before them.
    local PullUnder = nil
    if CoD.TodPull then
        PullUnder = CoD.TodPull.AttachUnder( self, HudRef, InstanceRef,
            { a = { CARD_AX0, CARD_AX1 }, b = { CARD_BX0, CARD_BX1 } }, CARD_Y0, CARD_Y1 )
    end
    local Pull = nil   -- built after the tier badge, below

    local CardA = BuildCard( CARD_AX0, CARD_AX1, "" )
    local CardB = BuildCard( CARD_BX0, CARD_BX1, "" )

    -- ---- THE REVEAL, client half (v14.52) ----------------------------------
    -- Per-slot latches. Render() runs on EVERY model change, so "this card just
    -- landed" has to be told apart from "this card is still sitting there" —
    -- these carry what the slot looked like on the previous paint. They are
    -- reset in the show == 0 branch, so a deal can never inherit the last one's
    -- edges.
    local rv = { a = { d = 0, r = 0 }, b = { d = 0, r = 0 } }
    local wasRevealing = false

    -- ONLY ALPHA AND RECTS ARE EVER TWEENED here. Those are the two lanes this
    -- file and the vendored Aetherium kit it copies from have actually shipped
    -- (AetheriumPowerupNotification tweens both; nothing in-tree tweens colour).
    -- An RGB tween would be a guess, so every colour below is STAMPED and only
    -- its alpha moves.

    -- Socket down, now. Called on every settled paint rather than only on the
    -- transition — the same both-directions-every-paint discipline as the
    -- locked-card tint further down. A socket stranded by an aborted deal has
    -- nothing else that would ever take it back down.
    local function SocketClear( card )
        card.SockRim:completeAnimation()
        card.SockFill:completeAnimation()
        card.SockRim:setAlpha( 0 )
        card.SockFill:setAlpha( 0 )
        card.SockRim:setLeftRight( true, false, card.xLo, card.xHi )
        card.SockFill:setLeftRight( true, false, card.xLo + REVEAL_SOCKET_PAD, card.xHi - REVEAL_SOCKET_PAD )
    end

    -- The empty slot, charging toward `rar`. Re-entered on every rarity change,
    -- which is exactly when the server starts that slot's hold — so the ramp
    -- and the wait are the same event seen from two sides.
    local function SocketOpen( card, rar )
        local col = ( RARITY[ rar ] or RARITY[ 1 ] ).col
        card.SockRim:completeAnimation()
        card.SockFill:completeAnimation()
        card.SockRim:setLeftRight( true, false, card.xLo, card.xHi )
        card.SockRim:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
        card.SockRim.Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
        card.SockFill:setLeftRight( true, false, card.xLo + REVEAL_SOCKET_PAD, card.xHi - REVEAL_SOCKET_PAD )
        card.SockFill:setTopBottom( true, false, CARD_Y0 + REVEAL_SOCKET_PAD, CARD_Y1 - REVEAL_SOCKET_PAD )
        card.SockFill:setAlpha( 0.9 )

        card.SockRim:setAlpha( 0.12 )
        card.SockRim:beginAnimation( "tod_charge", REVEAL_HOLD_MS[ rar ] or 100,
                                     false, false, CoD.TweenType.Linear )
        card.SockRim:setAlpha( ( rar >= 2 ) and 1 or 0.5 )

        card.Flare:completeAnimation()
        card.Flare:setAlpha( 0 )
        card.Glow:completeAnimation()
        card.Glow:setAlpha( 0 )
        card.glowBase = 0
    end

    -- The pull. Socket blows apart into the card's spine, the face opens out of
    -- that same spine, and the rarity pays for itself in the burst it throws.
    local function LandCard( card, rar )
        local col = ( RARITY[ rar ] or RARITY[ 1 ] ).col
        local mid = card.xMid

        card.SockRim:completeAnimation()
        card.SockFill:completeAnimation()
        card.SockRim:beginAnimation( "tod_sock_out", REVEAL_SOCKET_MS, false, false, CoD.TweenType.Linear )
        card.SockRim:setLeftRight( true, false, mid - 2, mid + 2 )
        card.SockRim:setAlpha( 0 )
        card.SockFill:beginAnimation( "tod_sock_out", REVEAL_SOCKET_MS, false, false, CoD.TweenType.Linear )
        card.SockFill:setLeftRight( true, false, mid - 2, mid + 2 )
        card.SockFill:setAlpha( 0 )

        -- Bounce OVERSHOOTS the final rect and settles back — that is the pop.
        -- Linear here reads as the card sliding into place, which is the one
        -- thing this whole feature exists to stop looking like.
        -- (No-art fallback: with USE_CARD_SET_ART off there is no CardImg to
        -- open, so the flip is skipped and the burst carries the moment alone.)
        if card.CardImg then
            card.CardImg:completeAnimation()
            card.CardImg:setLeftRight( true, false, mid - 3, mid + 3 )
            card.CardImg:setTopBottom( true, false, CARD_Y0 + 26, CARD_Y1 - 26 )
            -- a text-only card (imgLive false) flips its frame, never a stale picture
            card.CardImg:setAlpha( ( card.imgLive == false ) and 0 or 1 )
            card.CardImg:beginAnimation( "tod_flip", REVEAL_FLIP_MS[ rar ] or 90, false, false, CoD.TweenType.Bounce )
            card.CardImg:setLeftRight( true, false, card.xLo, card.xHi )
            card.CardImg:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
        end

        -- the aura it keeps, and the burst it throws once
        card.glowBase = REVEAL_GLOW[ rar ] or 0
        card.Glow:completeAnimation()
        card.Glow.Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
        card.Glow:setAlpha( card.glowBase * ( card.glowMul or 1 ) )

        card.Flare:completeAnimation()
        local peak = REVEAL_FLARE_PEAK[ rar ] or 0
        if peak > 0 then
            local grow = REVEAL_FLARE_GROW[ rar ]
            card.Flare.Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
            card.Flare:setLeftRight( true, false, card.xLo, card.xHi )
            card.Flare:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
            card.Flare:setAlpha( peak )
            card.Flare:beginAnimation( "tod_flare", REVEAL_FLARE_MS[ rar ], false, false, CoD.TweenType.Linear )
            card.Flare:setLeftRight( true, false, card.xLo - grow, card.xHi + grow )
            card.Flare:setTopBottom( true, false, CARD_Y0 - grow, CARD_Y1 + grow )
            card.Flare:setAlpha( 0 )
        else
            card.Flare:setAlpha( 0 )
        end
    end

    -- Panel down: every reveal element back to its rest state, INCLUDING the
    -- card face's RECT. A deal aborted mid-flip (the player goes down, the
    -- station's takeover) otherwise leaves CardImg parked at whatever sliver
    -- the tween had reached, and the NEXT deal paints a correct image into a
    -- wrong rect — a bug that would only ever show up on the second card.
    local function RevealHide( card )
        SocketClear( card )
        card.Flare:completeAnimation()
        card.Flare:setAlpha( 0 )
        card.Glow:completeAnimation()
        card.Glow:setAlpha( 0 )
        card.glowBase = 0
        card.glowMul = 1
        if card.CardImg then
            card.CardImg:completeAnimation()
            card.CardImg:setLeftRight( true, false, card.xLo, card.xHi )
            card.CardImg:setTopBottom( true, false, CARD_Y0, CARD_Y1 )
        end
    end

    -- One slot, one paint. `rar`/`dom` are that slot's live fields; see the
    -- REVEAL header at the top of this file for the three-fact contract.
    local function RevealDrive( key, card, rar, dom, revealing )
        local s = rv[ key ]
        if revealing then
            if dom == 0 then
                if Pull then
                    -- THE PULL draws the face-down back and its climb instead
                    SocketClear( card )
                elseif rar >= 1 then
                    if s.r ~= rar or s.d ~= 0 then
                        SocketOpen( card, rar )
                    end
                else
                    SocketClear( card )   -- one-card deal: no second socket
                end
            elseif s.d == 0 then
                LandCard( card, rar )
            end
        else
            SocketClear( card )
        end
        s.d = dom
        s.r = rar
    end

    -- The aura follows the card it belongs to: full on the focused card, dimmed
    -- on the passed-over one, gone when the slot never landed. Called at the end
    -- of every Render so it cannot disagree with the alphas set above it.
    local function ApplyGlow( card )
        card.Glow:setAlpha( ( card.glowBase or 0 ) * ( card.glowMul or 1 ) )
    end

    -- THE PULL (docs/187): backs, ladders, live band + pips, banner, shards,
    -- flash — on top of both cards. Its face layer joins each card.group, so the
    -- band and pips take every alpha the card takes.
    if CoD.TodPull and PullUnder then
        Pull = CoD.TodPull.Attach( self, HudRef, InstanceRef, PullUnder, { a = CardA, b = CardB }, {
            RARITY = RARITY, DOMAIN = DOMAIN, TIER_DOMAIN = TIER_DOMAIN,
            TIER_LADDER = TIER_LADDER, TCLS = TOD_TCLS,
            y0 = CARD_Y0, y1 = CARD_Y1,
        } )
    end

    -- [tod v14.39] CLASS TIER GATE BADGE - constructed HERE, after both cards
    -- AND after THE PULL's layers, because LUI draws in addElement order and
    -- this has to sit ON TOP of the locked card (user 2026-08-31: "grayed out
    -- with these new images over the top of it"). [PK01, 2026-10-04] It used to
    -- be built just BEFORE CoD.TodPull.Attach, which adds every card's layered
    -- v2 face (body, picture, frame, crest, title) to this menu - so for every
    -- class with a layered set the stamp drew UNDER card B's dimmed tier
    -- picture. Keep it the LAST element this menu adds;
    -- tools/test_tier_gate_strip.lua holds the order. Declared far above so the
    -- render closure captures it; only the construction is deferred. Position
    -- is set per paint - the stamp band over card B when a locked tier card is
    -- dealt, the top-left gutter otherwise - so the coordinates here are just a
    -- safe initial state.
    if art.tierGate then
        TierGateImg = LUI.UIImage.new()
        TierGateImg:setLeftRight( true, false, 50, 330 )
        TierGateImg:setTopBottom( true, false, 150, 210 )
        TierGateImg:setAlpha( 0 )
        self:addElement( TierGateImg )
    end

    -- ---- state + render -----------------------------------------------------
    local st = { show = 0, ad = 0, ar = 1, arw = 0, al = 0, bd = 0, br = 1, brw = 0, solo = 0, bl = 0, luck = 0, focus = 0, time = 0, hold = 0 }
    -- LUCK AT DEAL TIME, latched on the show 0->1 edge (audit 2026-08-25).
    -- todUpgLuck is the LIVE luck bar and it keeps moving while the cards are
    -- up — which is fine for the top-left bar, but the badge claims to describe THESE
    -- rolls. At a HEAVENLY GIFT ALTAR the world is NOT paused, so a player who
    -- keeps killing watched the badge climb under a deal it had nothing to do
    -- with. Latched client-side because a second clientfield is not affordable
    -- (the pool is at 58 of the proven 61 bits).
    local dealLuck = 0
    local wasShown = 0

    local function PaintCard( card, dom, rar, cur )
        local d = DOMAIN[ dom ]
        -- TIER card: decode (class-1)*2 + (tier-2) from the level field and
        -- name the actual promotion ("TIER 2: MP5"). A fresh table each paint —
        -- never mutate the shared DOMAIN row.
        local tierCls, tierN = nil, nil
        if dom == TIER_DOMAIN and d ~= nil then
            tierCls = math.floor( cur / 2 ) + 1
            tierN = ( cur % 2 ) + 2
            local lad = TIER_LADDER[ tierCls ]
            local gun = ( lad and lad[ tierN ] ) or "NEW WEAPON"
            local cls = ( lad and lad.class ) or "CLASS"
            -- [tod v14.12] the kept-list is NOT enumerated here on purpose: it
            -- has grown three times (DR+LUCK -> +sprint pair -> +vitality ->
            -- +headshot/scavenger) and a stale enumeration lies on a card.
            -- tierSafe() in AetheriumStartMenu.lua is the fallback; the pause
            -- menu's reset badges show the player exactly what survives.
            d = { name = "TIER " .. tierN .. ": " .. gun,
                  desc = cls .. " - new weapon, unpacked. Every upgrade card stays",
                  max = 3 }
        end
        local r = RARITY[ rar ] or RARITY[ 1 ]
        -- DARK UPGRADE: the server sends the sentinel in the LEVEL field rather
        -- than a real level. Checked AFTER the tier decode above on purpose --
        -- the tier card packs class+tier into the same field and can legally
        -- reach 15 (class 4 / tier 3 would be 7, so it cannot today, but the
        -- ordering is what keeps that true if the ladder ever grows).
        local isDark = ( cur == DARK_L and dom ~= TIER_DOMAIN )
        if isDark then
            r = { tag = "DARK UPGRADE", col = { 0.85, 0.15, 0.22 } }
        end
        local visible = ( d ~= nil )
        card.v2 = false   -- set by the layered-card branch below (no rarity strips on it)

        for i = 1, #card.group do
            card.group[ i ]:setAlpha( visible and 1 or 0 )
        end
        if not visible then
            return
        end

        -- FULL-CARD SET: one baked image carries everything; blank the
        -- composite texts (setText "" — never alpha-juggle, the group loop
        -- owns alpha) and skip the composite branches below.
        if card.CardImg then
            -- CARD V2 (docs/191): an upgrade whose layers are installed is drawn by
            -- THE PULL as a layered card with live text; the old baked image is held
            -- hidden (imgLive false keeps every alpha writer off it) and so is the
            -- composite text. The focus strips keep working as ever.
            if Pull and CoD.TodPull.UsesV2( Pull, dom, cur ) then
                card.CardImg:setAlpha( 0 )
                card.imgLive = false
                card.Bg.Bg:setAlpha( 0 )
                -- NO RARITY STRIPS ON THE LAYERED CARD (user 2026-09-29: "you still have like some
                -- leftover assets. Like there are these bottom and top lines that kind of flash").
                -- The old card's 4 px strips sat on its top and bottom edge, pulsed with the focus
                -- blink and turned teal on the lock; the layered card's own frame is its border, and
                -- THE PULL owns its focus dim and lock tint. The old baked / text cards keep them.
                card.v2 = true
                card.Top.Bg:setAlpha( 0 )
                card.Bot.Bg:setAlpha( 0 )
                card.Tag:setText( "" )
                card.Name:setText( "" )
                card.Desc:setText( "" )
                return
            end
            local set = art.cards[ dom ]
            -- TIER card art is keyed by class/tier, not rarity: present it as a
            -- 3-slot set of the same image so the branch below needs no change.
            if tierCls and art.tier then
                local img = art.tier[ tierCls ] and art.tier[ tierCls ][ tierN ]
                set = img and { img, img, img } or nil
            end
            -- DARK art wins when it exists. When USE_DARK_CARD_ART is off there
            -- is no art.dark table at all and a dark card falls through to its
            -- ULTIMATE image -- correct-looking, just not yet distinct.
            local darkImg = isDark and art.dark and art.dark[ dom ] or nil
            -- An enabled Dark card without its own art must show DARK text,
            -- never the Ultimate image with its baked, incorrect +3 label.
            if isDark and not darkImg then
                set = nil
            end
            -- imgLive (2026-09-09): whether CardImg currently carries THIS card.
            -- LandCard's flip and SetCardAlpha used to set its alpha to 1
            -- unconditionally, so a text-only DARK card (no _dark art) drew
            -- its composite text over the PREVIOUS deal's picture (user
            -- 2026-09-09, with a screenshot). An image element cannot be cleared, only
            -- hidden, so every alpha writer has to know whether it is live.
            card.imgLive = true
            if darkImg then
                card.CardImg:setImage( darkImg )
                card.CardImg:setAlpha( 1 )
            elseif set and set[ 1 ] then
                -- ONE FACE PER UPGRADE (docs/187): the rarity is drawn live by
                -- TodPull (band + pips) over it, so every rarity wears the same
                -- image. Until the rarity-neutral faces land this is the old
                -- _regular art, whose baked band TodPull covers.
                card.CardImg:setImage( set[ 1 ] )
                card.CardImg:setAlpha( 1 )
            elseif set then
                card.CardImg:setImage( set[ 1 ] )
                card.CardImg:setAlpha( 1 )
            else
                -- NO baked art for this domain (a new domain shipped before
                -- its cards). Without this branch the image element kept the
                -- PREVIOUS card's art and silently showed the wrong upgrade.
                -- Hide it and render the composite text stack instead.
                card.CardImg:setAlpha( 0 )
                card.imgLive = false
                card.Bg.Bg:setAlpha( 0.85 )
                card.Top.Bg:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
                card.Top.Bg:setAlpha( 0.95 )
                card.Bot.Bg:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
                card.Bot.Bg:setAlpha( 0.95 )
                card.Tag:setText( r.tag )
                card.Tag:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
                card.Name:setText( d.name )
                card.Name:setRGB( PAL.text[ 1 ], PAL.text[ 2 ], PAL.text[ 3 ] )
                card.Desc:setText( d.desc )
                return
            end
            card.Bg.Bg:setAlpha( 0 )
            -- re-baseline strip alpha EVERY render (FocusCards only writes the
            -- focused card; without this the unfocused card's accent froze at
            -- whatever blink phase last touched it — verify 2026-08-20)
            card.Top.Bg:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
            card.Top.Bg:setAlpha( 0.95 )
            card.Bot.Bg:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
            card.Bot.Bg:setAlpha( 0.95 )
            card.Tag:setText( "" )
            card.Name:setText( "" )
            card.Desc:setText( "" )
            return
        end

        -- The flat glass panel + the rarity strips (the composite base / frame / icon art left with
        -- the Map 1 purge, 2026-10-04; every live class deals baked or layered cards).
        card.Bg.Bg:setAlpha( 0.85 )
        card.Top.Bg:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
        card.Bot.Bg:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
        card.Tag:setText( r.tag )
        card.Tag:setRGB( r.col[ 1 ], r.col[ 2 ], r.col[ 3 ] )
        card.Name:setText( d.name )
        card.Name:setRGB( PAL.text[ 1 ], PAL.text[ 2 ], PAL.text[ 3 ] )
        card.Desc:setText( d.desc )
    end

    -- Dim the passed-over card, teal-flash the chosen one (show = 2 / 3).
    -- The accent strips are re-raised EXPLICITLY (alpha 0.95): with frame art
    -- on, PaintCard zeroes them every render — without the raise the flash
    -- was invisible (verify pass 2026-08-19).
    local function FlashPick( chosen, other )
        if not chosen.v2 then   -- the layered card has no strips (PaintCard)
            chosen.Top.Bg:setRGB( PAL.flash[ 1 ], PAL.flash[ 2 ], PAL.flash[ 3 ] )
            chosen.Top.Bg:setAlpha( 0.95 )
            chosen.Bot.Bg:setRGB( PAL.flash[ 1 ], PAL.flash[ 2 ], PAL.flash[ 3 ] )
            chosen.Bot.Bg:setAlpha( 0.95 )
        end
        if chosen.HintImg then
            CardHint( chosen, "locked", 1 )
            chosen.Bind:setText( "" )
        else
            chosen.Bind:setText( "LOCKED IN" )
            chosen.Bind:setRGB( PAL.pick[ 1 ], PAL.pick[ 2 ], PAL.pick[ 3 ] )
            chosen.Bind:setAlpha( 1 )
        end
        CardHint( other, "off", 0 )
        for i = 1, #other.group do
            other.group[ i ]:setAlpha( 0.2 )
        end
    end

    local function Render()
        -- THE WIRE (docs/187): todUpgAR/BR carry rarity - 1 (0..3), and todUpgSolo
        -- says a deal has ONE card. Decoded here, once, into the 1..4 rarity (0 =
        -- no card in that slot) that everything below has always read.
        st.ar = ( st.arw or 0 ) + 1
        if ( st.solo or 0 ) == 1 then
            st.br = 0
        else
            st.br = ( st.brw or 0 ) + 1
        end
        -- THE HUD VEIL: the whole HUD hides while cards are up (dealt, chosen,
        -- flashing) and comes back the frame the panel closes. This panel is the
        -- one owner of the "cards" key.
        if CoD.TodHudVeil then
            CoD.TodHudVeil.Set( "cards", st.show ~= 0 )
        end
        if st.show == 0 then
            RevealHide( CardA )
            RevealHide( CardB )
            if Pull then
                CoD.TodPull.Render( Pull, st, false )
            end
            rv.a.d, rv.a.r = 0, 0
            rv.b.d, rv.b.r = 0, 0
            -- [2026-10-02] the panel closed: the NEXT show 0 -> 1 edge latches that deal's luck. This return used to
            -- skip `wasShown = st.show` below, so wasShown stayed 2 / 3 and only a life's FIRST deal ever latched -
            -- every later deal's LUCK badge showed the first deal's luck (found by tools/test_card_pull.lua, docs/201)
            wasShown = 0
            self:completeAnimation()
            self:beginAnimation( "keyframe", 250, false, false, CoD.TweenType.Linear )
            self:setAlpha( 0 )
            return
        end

        if st.show ~= 0 and wasShown == 0 then
            dealLuck = st.luck            -- freeze the luck this deal was rolled at
        end
        wasShown = st.show

        -- [tod v14.52] THE REVEAL IS RUNNING. show == 1 with focus == 0 is the
        -- server's reveal contract and is reachable no other way — see the
        -- REVEAL header at the top of this file. While it holds, the panel is
        -- NOT an input surface: no focus, no hold bar, no countdown, no gate
        -- badge. Everything below reads this rather than re-deriving it.
        local revealing = ( st.show == 1 and st.focus == 0 )

        -- [tod v14.52] THE PANEL'S OWN completeAnimation MOVED UP HERE, away
        -- from the beginAnimation/setAlpha pair it used to sit against at the
        -- bottom of this function. LUI's completeAnimation is documented
        -- nowhere in this tree and MAY snap child animations as well as the
        -- element's own — and if it does, calling it after the reveal has just
        -- started a card's tween would end that tween on the frame it began,
        -- silently, with everything still looking correct in the code. Run it
        -- FIRST and the question stops mattering: whatever it reaches, it
        -- reaches before this paint's tweens exist. The fade-in pair stays at
        -- the bottom, where it only ever touches this element's alpha.
        self:completeAnimation()

        -- [tod v14.52] ARM THE SOCKETS OFF THE REVEAL'S OWN 0 -> 1 EDGE, not off
        -- the slot data. rv latches per-slot FIELDS, and a deal can re-open with
        -- the same rarity sitting in the same slot — no field changes, no edge,
        -- no socket, and slot A spends its whole hold as a blank gap.
        --
        -- That is not hypothetical: a round event kills an in-flight PERSONAL
        -- STATION pick (level notify "tod_global_upg_takeover") and re-presents
        -- immediately, so show goes 1 -> 1 and the show == 0 reset below is
        -- never reached. -1 is a rarity no slot can hold, which forces the
        -- "rarity changed" branch in RevealDrive exactly once.
        if revealing and not wasRevealing then
            rv.a.r, rv.a.d = -1, 0
            rv.b.r, rv.b.d = -1, 0
        end
        wasRevealing = revealing

        PaintCard( CardA, st.ad, st.ar, st.al )
        PaintCard( CardB, st.bd, st.br, st.bl )

        -- [tod v16] CLASS badge. Unlike the luck badge this is not keyed to the
        -- deal -- it states a standing fact about the player, so it is simply on
        -- whenever the panel is. CoD.TodClass is pushed by
        -- _tod_upgrades::push_panel_hints before EVERY deal (0 = classless).
        if ClassBadge then
            local ci = CoD.TodClass or 0
            -- NO UPPER CLAMP: the table is the authority, so a new class
            -- shows its badge the moment art.classPlate gains its entry. The
            -- old "ci <= 4" would have hidden it silently.
            if ci >= 1 and art.classPlate[ ci ] then
                ClassBadge:setImage( art.classPlate[ ci ] )
                ClassBadge:setAlpha( 1 )
            else
                ClassBadge:setAlpha( 0 )
            end
        end

        -- LUCK BOOST badge (baked per 10%); LuckLine text is the no-art fallback
        if LuckBadge then
            local li = dealLuck            -- the deal's luck, not the live bar
            if li > 10 then li = 10 end
            if li > 0 and art.badges[ li ] then
                LuckBadge:setImage( art.badges[ li ] )
                LuckBadge:setAlpha( 1 )
                if LuckLegend then LuckLegend:setAlpha( 1 ) end
            else
                LuckBadge:setAlpha( 0 )
                if LuckLegend then LuckLegend:setAlpha( 0 ) end
            end
            LuckLine:setText( "" )
        elseif dealLuck > 0 then
            LuckLine:setText( "LUCK " .. ( dealLuck * 10 ) .. "% BOOSTED THESE ROLLS" )
        else
            LuckLine:setText( "" )
        end
        -- ONE SEGMENT SHORT (docs/201 section 6), on the luck this deal was rolled at (dealLuck is the bar in tens:
        -- 4 = 40..49, one segment under the RARE guarantee; 9 = 90..99, one under the EPIC one)
        if dealLuck == 9 then
            SegLine:setText( "ONE SEGMENT FROM AN EPIC" )
            SegLine:setAlpha( 1 )
        elseif dealLuck == 4 then
            SegLine:setText( "ONE SEGMENT FROM A RARE" )
            SegLine:setAlpha( 1 )
        else
            SegLine:setText( "" )
            SegLine:setAlpha( 0 )
        end
        -- THE HOT STREAK (docs/201): the line follows CoD.TodHeat (a change while the panel is up arrives through
        -- self.todHeatPaint with its pulse; this only catches a panel that opened on a heat it has not drawn)
        if heatShown ~= ( tonumber( CoD.TodHeat ) or 0 ) then
            HeatPaint( CoD.TodHeat, false )
        end

        -- [tod v14.35] CLASS TIER floor requirement — see TierLine above.
        -- Read live from the shared global rather than latched at panel-open:
        -- GSC pushes the value immediately BEFORE it raises todUpgShow, so it
        -- is already correct on the first paint, and a re-push (the station's
        -- re-present after a round event takes over) lands without any extra
        -- wiring. Rendered only while the panel is actually up, so a value left
        -- over from the last deal can never flash on a hidden panel.
        local need = CoD.TodTierNeed or 0
        -- [tod v14.39] IS THE RIGHT CARD A LOCKED TIER CARD? The server deals
        -- the promotion even below its floor gate now and marks it unselectable
        -- (_tod_upgrades::make_tier_option). No new channel was needed to say
        -- so: `bd == TIER_DOMAIN` means a tier card is in the right slot, and
        -- `need > 0` means this player is floor-blocked — together they can only
        -- mean the dealt card is the locked one. A tier card dealt to a player
        -- who HAS cleared the floor arrives with need == 0 and stays takeable.
        -- `not revealing` (v14.52): while the cards are still being dealt, bd is
        -- 0 for slot B by design, so this would read false, park the badge in
        -- the gutter, and then jump it onto the card the instant B lands. One
        -- badge that MOVES mid-reveal is worse than one that arrives with the
        -- card it belongs to.
        local lockedB = ( not revealing ) and ( st.bd == TIER_DOMAIN ) and need > 0
        -- WHERE THE BADGE GOES depends on whether there is a card to attach it
        -- to: STAMPED ACROSS the locked card when one is dealt, in the top-left
        -- gutter otherwise. NEVER BOTH — one badge, one meaning, two homes.
        --
        -- THE STAMP BAND IS MEASURED OFF THE CARD ART, not eyeballed (user
        -- 2026-08-31: "grayed out with these new images over the top of it").
        -- The 768x1152 tier card draws into 234x351 at x 677..911, y 226..577,
        -- and it is dense with text that must stay readable — the whole reason
        -- the card is shown at all is so the player sees WHAT they are climbing
        -- toward. Bands, as fractions of the source art:
        --   0.074-0.165  "TIER 2" header      -> screen 252..284   KEEP
        --   0.19 -0.61   gun illustration     -> screen 293..440   stamp here
        --   0.616-0.69   class name banner    -> screen 442..468   KEEP
        --   0.707-0.868  gun name + "GUN UPGRADES RESET" -> 474..531  KEEP
        -- So the badge lands on the PICTURE and never on a word. It overhangs
        -- the card by 23px each side, which reads as a deliberate stamp rather
        -- than a mis-sized inlay, and clears card A (ends 603) comfortably.
        if TierGateImg then
            if lockedB then
                TierGateImg:setLeftRight( true, false, 654, 934 )   -- 280 wide, centred on card B's 794
                TierGateImg:setTopBottom( true, false, 336, 396 )   -- across the gun illustration only
            else
                -- [tod v16] ONE ROW DOWN. This was 150..210, which the CLASS
                -- badge now owns; stacked under it instead of on top of it.
                TierGateImg:setLeftRight( true, false, 50, 330 )
                TierGateImg:setTopBottom( true, false, 216, 276 )
            end
        end
        if st.show == 1 and need > 0 and not revealing then
            -- The tier comes from TIER_FLOOR_TO_TIER (file scope, LOCKSTEP with
            -- GSC tier_floor_req). It was floor/10+1 until 2026-09-02, which
            -- only inverts an evenly spaced ladder; see the table's comment.
            local nextTier = TIER_FLOOR_TO_TIER[ need ] or 2
            -- ART FIRST, text only when the strip for this tier is missing —
            -- and per-tier, not per-set, so a half-installed pair still shows
            -- the correct thing for the tier that has its strip.
            local strip = art.tierGate and art.tierGate[ nextTier ]
            if TierGateImg and strip then
                TierGateImg:setImage( strip )
                TierGateImg:setAlpha( 1 )
                TierLine:setText( "" )
                -- [PK01] THE STAMP REPLACES CARD B'S "NEW TIER" BANNER. A locked
                -- tier card reveals as a COMMON, and focus opens the panel 0.26 s
                -- (live) to 0.51 s (paused) after its flip, while THE PULL's
                -- 0.66 s banner still holds - right in the stamp's band (y 322..398,
                -- 340 wide against the strip's 280). The stamp draws over it now,
                -- so its ends and its top would show round the strip; the badge
                -- says what the card really is, so the banner goes the moment it
                -- lands. Only the reveal ever starts a banner.
                if lockedB and Pull and CoD.TodPull.BannerOff then
                    CoD.TodPull.BannerOff( Pull )
                end
            else
                if TierGateImg then
                    TierGateImg:setAlpha( 0 )
                end
                TierLine:setText( "CLASS TIER " .. nextTier .. " - REACH FLOOR " .. tierFloorShown( need ) )
            end
        else
            if TierGateImg then
                TierGateImg:setAlpha( 0 )
            end
            TierLine:setText( "" )
        end

        -- `not revealing` (v14.52): the countdown does not start until input
        -- does, and it does not — wait_for_choice runs AFTER the reveal. Showing
        -- "AUTO IN 15s" over two empty sockets promises a clock that is not
        -- ticking yet.
        if st.show == 1 and st.time > 0 and not revealing then
            ShowSwitchPlate( true )
            if TimeTrack then
                -- [tod v16.88] THE BAR IS THE CLOCK — no digits. It drains from
                -- full toward the left as the deal times out. The server sends
                -- whole seconds and MAX is the deal's own start value, so the
                -- first paint is always a full bar whatever the timeout is set
                -- to; clamped because a station deal and a round deal do not
                -- share a length.
                TimeLine:setText( "" )
                if st.time > timeMaxSeen then
                    timeMaxSeen = st.time
                end
                local maxT = timeMaxSeen
                if maxT < 1 then
                    maxT = 1
                end
                local frac = st.time / maxT
                if frac > 1 then frac = 1 end
                if frac < 0 then frac = 0 end
                TimeFill:setLeftRight( false, false, -140, -140 + 280 * frac )
                TimeTrack:setAlpha( 0.85 )
                TimeFill:setAlpha( 1 )
                -- the last few seconds go red, the one thing the text did that
                -- a bar must not lose
                if st.time <= MAX_LEVEL_TIME_DANGER then
                    TimeFill:setRGB( 1.0, 0.25, 0.3 )
                else
                    TimeFill:setRGB( 1, 1, 1 )
                end
            elseif SwitchHintImg then
                TimeLine:setText( "AUTO IN " .. st.time .. "s" )
            else
                TimeLine:setText( SwitchHint() .. "   AUTO IN " .. st.time .. "s" )
            end
            if not TimeTrack then
                if st.time <= MAX_LEVEL_TIME_DANGER then
                    TimeLine:setRGB( 1.0, 0.25, 0.3 )
                else
                    TimeLine:setRGB( PAL.dim[ 1 ], PAL.dim[ 2 ], PAL.dim[ 3 ] )
                end
            end
        else
            ShowSwitchPlate( false )
            TimeLine:setText( "" )
            if TimeTrack then
                TimeTrack:setAlpha( 0 )
                TimeFill:setAlpha( 0 )
                -- reset the watched maximum, or the NEXT deal starts its bar
                -- part-drained against the previous deal's longer clock
                timeMaxSeen = 0
            end
        end

        -- Focus (server-blinked; a card is ALWAYS focused while choosing).
        -- v4.4 polish: the focused card stays at FULL presence — the blink
        -- phase pulses only the ACCENT (rarity frame / strips + bind line),
        -- so focus reads as a glow, not a flicker. The hold-to-lock bar
        -- fills under the focused card (todUpgHold 0..15).
        local function FocusCards( focused, other, bright, hold )
            SetCardAlpha( focused, 1 )
            focused.tone = 1
            -- THE CARD YOU ARE NOT ON STAYS SOLID (2026-09-29; the user: "Consider the player
            -- experience for the best experience we can create and you can make the decision").
            -- At 0.4 alpha the room showed through its words, so comparing the two cards meant
            -- switching focus just to read the other one. A layered card now DARKENS instead
            -- (fully opaque, PAL.unfocusTone; its white words still read) and the focused card is
            -- the bright one. Cards without the layered art keep the old see-through dim.
            if other.v2 then
                SetCardAlpha( other, 1 )
                other.tone = PAL.unfocusTone
            else
                SetCardAlpha( other, 0.4 )
            end
            if not focused.v2 then   -- the layered card has no strips to pulse (PaintCard)
                focused.Top.Bg:setAlpha( bright and 0.95 or 0.5 )
                focused.Bot.Bg:setAlpha( bright and 0.95 or 0.5 )
            end
            if focused.HintImg then
                CardHint( focused, "lock", bright and 1 or 0.75 )
                CardHint( other, "off", 0 )
                focused.Bind:setText( "" )
            else
                focused.Bind:setText( LockHint() )
                focused.Bind:setRGB( PAL.pick[ 1 ], PAL.pick[ 2 ], PAL.pick[ 3 ] )
                focused.Bind:setAlpha( bright and 1 or 0.75 )
            end
            other.Bind:setText( "" )
            local w = ( focused.holdHi - focused.holdLo ) * ( hold / 15 )
            -- [tod v16.88] ART BAR WHEN PRESENT, COLOUR QUADS OTHERWISE — never
            -- both, or the quad shows through the art's rounded ends.
            if focused.BarTrack then
                focused.HoldTrack.Bg:setAlpha( 0 )
                focused.HoldFill.Bg:setAlpha( 0 )
                focused.BarTrack:setAlpha( 0.85 )
                focused.BarFill:setLeftRight( true, false, focused.holdLo, focused.holdLo + w )
                focused.BarFill:setAlpha( ( hold > 0 ) and 1 or 0 )
                other.BarTrack:setAlpha( 0 )
                other.BarFill:setAlpha( 0 )
            else
                focused.HoldTrack.Bg:setAlpha( 0.3 )
                focused.HoldFill:setLeftRight( true, false, focused.holdLo, focused.holdLo + w )
                focused.HoldFill.Bg:setAlpha( ( hold > 0 ) and 0.95 or 0 )
            end
            other.HoldTrack.Bg:setAlpha( 0 )
            other.HoldFill.Bg:setAlpha( 0 )
        end
        -- single-option events (todUpgBD == 0): CardB was hidden by PaintCard
        -- with STALE text still set — never re-raise it (the ghost-card bug,
        -- verify pass 2026-08-19).
        local two = ( DOMAIN[ st.bd ] ~= nil )
        CardA.tone, CardB.tone = 1, 1   -- only FocusCards darkens a card, and only while choosing
        if revealing then
            -- [tod v14.52] THE FOCUS BLOCK IS SKIPPED, NOT ADAPTED. It writes an
            -- alpha to every element of both cards on every paint, which is
            -- precisely what a reveal tween cannot survive — and there is
            -- nothing for it to say yet: no card is focused until the deal
            -- finishes. PaintCard has already put each slot at its natural
            -- alpha (1 once its domain arrives, 0 while it is still a socket),
            -- so the cards are correct without it.
            CardA.glowMul = 1
            CardB.glowMul = 1
            CardA.Bind:setText( "" )
            CardB.Bind:setText( "" )
            CardHint( CardA, "off", 0 )
            CardHint( CardB, "off", 0 )
            CardA.HoldTrack.Bg:setAlpha( 0 )
            CardA.HoldFill.Bg:setAlpha( 0 )
            CardB.HoldTrack.Bg:setAlpha( 0 )
            CardB.HoldFill.Bg:setAlpha( 0 )
            -- [tod v16.88] the art bar hides with the quads
            if CardA.BarTrack then
                CardA.BarTrack:setAlpha( 0 )
                CardA.BarFill:setAlpha( 0 )
                CardB.BarTrack:setAlpha( 0 )
                CardB.BarFill:setAlpha( 0 )
            end
        elseif st.show == 1 then
            if two and ( st.focus == 3 or st.focus == 4 ) then
                FocusCards( CardB, CardA, st.focus == 3, st.hold )
                CardB.glowMul, CardA.glowMul = 1, 0.45
            else
                FocusCards( CardA, CardB, st.focus ~= 2, st.hold )
                CardA.glowMul, CardB.glowMul = 1, 0.45
                if not two then
                    SetCardAlpha( CardB, 0 )
                    CardB.HoldTrack.Bg:setAlpha( 0 )
                    CardB.HoldFill.Bg:setAlpha( 0 )
                    CardB.glowMul = 0
                end
            end
        else
            CardA.HoldTrack.Bg:setAlpha( 0 )
            CardA.HoldFill.Bg:setAlpha( 0 )
            CardB.HoldTrack.Bg:setAlpha( 0 )
            CardB.HoldFill.Bg:setAlpha( 0 )
            -- [tod v16.88] the art bar hides with the quads
            if CardA.BarTrack then
                CardA.BarTrack:setAlpha( 0 )
                CardA.BarFill:setAlpha( 0 )
                CardB.BarTrack:setAlpha( 0 )
                CardB.BarFill:setAlpha( 0 )
            end
        end

        -- [tod v14.39] THE LOCKED CARD'S LOOK — applied AFTER the focus block,
        -- because that block is what sets the alphas and would otherwise undo
        -- this on the next paint.
        --
        -- A normal unfocused card already sits at 0.4; that is not enough on its
        -- own, because "unfocused" and "unselectable" would look identical and
        -- the player would keep trying to reach it. So the locked card ALSO
        -- takes a cold grey-blue tint, which no live card ever has — the tint,
        -- not the alpha, is what carries "dead", and the stamped badge says why.
        --
        -- THE DIM IS DELIBERATELY MILD (0.55, not the 0.22 this first shipped
        -- with). Alpha and tint MULTIPLY: 0.22 x ~0.5 left the card at ~0.11
        -- effective, which grey it out so hard the gun name stopped being
        -- readable — and being able to read WHAT you are climbing toward is the
        -- entire reason the card is dealt instead of hidden. 0.55 x ~0.6 lands
        -- near 0.33: below a live unfocused card, still legible.
        --
        -- THE RESTORE IS NOT OPTIONAL. setRGB persists on the element, so a
        -- deal that skipped this branch would inherit the previous deal's tint
        -- and show a live, takeable card looking dead. Both directions are
        -- written every paint, deliberately — the same discipline as the
        -- ghost-card fix above.
        if CardB.CardImg then
            if lockedB and st.show == 1 then
                CardB.CardImg:setRGB( 0.55, 0.60, 0.72 )
                if CardB.todFace2 then CardB.todFace2:setRGB( 0.55, 0.60, 0.72 ) end
            else
                CardB.CardImg:setRGB( 1, 1, 1 )
                -- the unfocused tone (FocusCards), or full brightness; written every paint
                local k = CardB.tone or 1
                if CardB.todFace2 then CardB.todFace2:setRGB( k, k, k ) end
                if CardB.todFace then CardB.todFace:setRGB( k, k, k ) end
            end
        end
        do
            local k = CardA.tone or 1   -- the left card can never be floor-locked
            if CardA.todFace2 then CardA.todFace2:setRGB( k, k, k ) end
            if CardA.todFace then CardA.todFace:setRGB( k, k, k ) end
        end
        if lockedB and st.show == 1 then
            SetCardAlpha( CardB, 0.55 )
            CardB.Bind:setText( "" )
            CardHint( CardB, "off", 0 )
            CardB.HoldTrack.Bg:setAlpha( 0 )
            CardB.HoldFill.Bg:setAlpha( 0 )
        end

        if st.show == 2 then
            FlashPick( CardA, CardB )
            CardA.glowMul, CardB.glowMul = 1, 0.2
            if not two then
                SetCardAlpha( CardB, 0 )
                CardB.glowMul = 0
            end
        elseif st.show == 3 then
            FlashPick( CardB, CardA )
            CardB.glowMul, CardA.glowMul = 1, 0.2
        end

        -- [tod v14.52] THE REVEAL RUNS LAST, deliberately. PaintCard has already
        -- set each slot's image and its natural alpha, and the focus/flash
        -- blocks above have had their say about presence — the reveal is what
        -- gets to overwrite the RECT, and it must not then be overwritten back.
        RevealDrive( "a", CardA, st.ar, st.ad, revealing )
        RevealDrive( "b", CardB, st.br, st.bd, revealing )
        ApplyGlow( CardA )
        ApplyGlow( CardB )
        if Pull then
            CoD.TodPull.Render( Pull, st, revealing )
        end

        self:beginAnimation( "keyframe", 250, false, false, CoD.TweenType.Linear )
        self:setAlpha( 1 )
    end

    -- ---- model subscriptions (CreateModel = idempotent, never nil) ----------
    local ctrl = Engine.GetModelForController( InstanceRef )
    local function Watch( name, key )
        local m = Engine.CreateModel( ctrl, name )
        if m then
            self:subscribeToModel( m, function ( ModelRef )
                st[ key ] = tonumber( Engine.GetModelValue( ModelRef ) ) or 0
                Render()
            end )
        end
    end
    Watch( "todUpgAD", "ad" )
    Watch( "todUpgAR", "arw" )
    Watch( "todUpgAL", "al" )
    Watch( "todUpgBD", "bd" )
    Watch( "todUpgBR", "brw" )
    Watch( "todUpgSolo", "solo" )
    Watch( "todUpgBL", "bl" )
    Watch( "todUpgLuck", "luck" )
    Watch( "todUpgFocus", "focus" )
    Watch( "todUpgTime", "time" )
    Watch( "todUpgHold", "hold" )
    Watch( "todUpgShow", "show" )   -- last: paints with the full state on arrival

    return self
end

-- ---------------------------------------------------------------------------
-- Crosshair damage numbers (map 1's proven CoD.AccDmgNum design, ported):
-- each todDmgNum push (dmg*4 + headshot*2 + parity) spawns a number from a
-- pool at a scattered point near the crosshair; it rises and fades over 0.5s.
-- Headshots render teal and 25% larger; normal hits amber.
-- ---------------------------------------------------------------------------
--
-- v17.34 (user 2026-09-04: "our damage numbers ... displayed at center of
-- screen ... change all of that to use the alphabet we created and numbers").
-- The pool is CoD.TodGlyphText now, not UIText. Everything else about this
-- element is unchanged -- same 12 slots, same scatter table, same rise-and-fade
-- keyframe, same colour rules, same 14-bit decode.
--
-- SIZE IS A CAP, NOT A SCALE. setScale multiplied a TTF's own base size, which
-- is why DMG_SCALE's 0.4 never meant anything in canvas pixels (see the
-- lui-text-size-is-scale-not-box note). A cap height IS canvas pixels: 14, and
-- 17.5 for a headshot, which is the same 25% the two scales expressed.
local DMG_COLOR    = { 1.0, 0.88, 0.25 }
local DMG_COLOR_HS = { 0.20, 0.95, 0.85 }
-- ARMORED (sprinter) hits: RED, and red WINS over the headshot colour (v13.9,
-- user: "should be red too. Specific for this type of enemy to show you are
-- doing reduced damage" -- a reduced headshot is still reduced, and that is
-- the fact the colour carries). Distinct from WARN_COLOR's alarm red only by
-- use; same family on purpose.
local DMG_COLOR_RED = { 1.0, 0.22, 0.18 }
local DMG_POOL   = 12
local DMG_LIFE   = 500
local DMG_RISE   = 36
-- v17.36 (user 2026-09-04, after playing v17.34: "the on screen damage numbers
-- need to be about 20% smaller"). 14 -> 11.2 and 17.5 -> 14, both x0.8, so the
-- headshot's +25% survives the cut untouched.
local DMG_CAP    = 11.2    -- cap height in canvas px (17 physical at 1080p)
local DMG_CAP_HS = 14      -- +25%, the ratio the old 0.4/0.5 scales carried
-- Kept for the fail-safe path only (TodGlyphText missing -> UIText, top of file)
local DMG_SCALE    = 0.4
local DMG_SCALE_HS = 0.5
-- The box is 34 tall and centred on the scatter point, so the baseline has to
-- sit BELOW the middle by half a cap for the number to read as centred.
-- DERIVED, not typed: v17.34 typed 0.71 for a cap of 14, and the very next
-- change moved the cap and would have left the number sitting low.
local DMG_BASEF  = 0.5 + DMG_CAP / 68   -- 68 = 2 x the box's 34px height
local DMG_SPREAD = 0.4
local DMG_BOXW   = 80
local DMG_SCATTER = {
    { 0, 0 }, { 30, -16 }, { -26, -22 }, { 10, 28 }, { -36, 6 }, { 38, 12 },
    { -12, -34 }, { 22, 34 }, { -38, -10 }, { 6, -26 }, { 34, -30 }, { -24, 26 },
}

CoD.TodDmgNum = InheritFrom( LUI.UIElement )

function CoD.TodDmgNum.new( HudRef, InstanceRef )
    local self = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( self )
    self:setClass( CoD.TodDmgNum )
    self.id = "TodDmgNum"
    self:setLeftRight( true, true, 0, 0 )
    self:setTopBottom( true, true, 0, 0 )

    -- The typeface, or the pre-v17.34 UIText if the require above did not land.
    local glyph = ( CoD.TodGlyphText ~= nil )

    local pool = {}
    for i = 1, DMG_POOL do
        local t
        if glyph then
            -- centred = true: the box is an OFFSET FROM THE SCREEN CENTRE,
            -- which is how this element has always been authored. pool 7 covers
            -- the encoding ceiling (2,047,000, seven digits) exactly.
            t = CoD.TodGlyphText.new( {
                left = -DMG_BOXW, right = DMG_BOXW, top = -17, bottom = 17,
                centered = true, align = "center", set = "digits", pool = 7,
                cap = DMG_CAP, baseFrac = DMG_BASEF,
                rgb = DMG_COLOR,
            } )
        else
            t = LUI.UIText.new()
            t:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
            t:setScale( DMG_SCALE )
            t:setRGB( DMG_COLOR[ 1 ], DMG_COLOR[ 2 ], DMG_COLOR[ 3 ] )
            t:setLeftRight( false, false, -DMG_BOXW, DMG_BOXW )
            t:setTopBottom( false, false, -17, 17 )
        end
        t:setAlpha( 0 )
        self:addElement( t )
        pool[ i ] = t
    end
    local nextIdx = 1

    local function spawnNum( dmg, hs, red )
        local t = pool[ nextIdx ]
        local p = DMG_SCATTER[ nextIdx ]
        nextIdx = ( nextIdx % DMG_POOL ) + 1
        -- red (armored/reduced) beats headshot; scale still honours the headshot
        local c  = red and DMG_COLOR_RED or ( hs and DMG_COLOR_HS or DMG_COLOR )
        local cx = p[ 1 ] * DMG_SPREAD
        local cy = p[ 2 ] * DMG_SPREAD
        t:completeAnimation()
        t:setRGB( c[ 1 ], c[ 2 ], c[ 3 ] )
        if glyph then
            t:setCap( hs and DMG_CAP_HS or DMG_CAP )
            t:setText( tostring( dmg ) )
            -- setBox, not setLeftRight/setTopBottom: the glyph row lays out
            -- inside the box, so the one call that repaints is the one that
            -- moves it.
            t:setBox( cx - DMG_BOXW, cx + DMG_BOXW, cy - 17, cy + 17 )
        else
            t:setText( tostring( dmg ) )
            t:setScale( hs and DMG_SCALE_HS or DMG_SCALE )
            t:setLeftRight( false, false, cx - DMG_BOXW, cx + DMG_BOXW )
            t:setTopBottom( false, false, cy - 17, cy + 17 )
        end
        t:setAlpha( 1.0 )
        -- The RISE stays on the raw setTopBottom on purpose: it only moves the
        -- box, and the glyphs are children laid out in box-local coordinates,
        -- so they ride along without a repaint. Calling setBox here would
        -- re-lay-out the string 60 times a second for no visible difference.
        t:beginAnimation( "keyframe", DMG_LIFE, false, false, CoD.TweenType.Linear )
        t:setTopBottom( false, false, cy - 17 - DMG_RISE, cy + 17 - DMG_RISE )
        t:setAlpha( 0 )
    end

    local dmgModel = Engine.CreateModel( Engine.GetModelForController( InstanceRef ), "todDmgNum" )
    if dmgModel then
        self:subscribeToModel( dmgModel, function ( ModelRef )
            local v = tonumber( Engine.GetModelValue( ModelRef ) ) or 0
            if v == 0 then return end
            -- LOCKSTEP with push_dmg_num_now (15 bits since 2026-09-09):
            -- 2026-09-09: 15 bits. dmg*16 + SCALE*8 + reduced*4 + headshot*2 + parity;
            -- scale 0 = hundreds (cap 204,700), 1 = thousands (cap 2,047,000, seven digits).
            -- POWER SCALE (2026-09-25): damage is a tenth, so the number is exact now:
            -- scale 0 = the value itself (1..2,047), 1 = hundreds (to 204,700).
            local scale = ( math.floor( v / 8 ) % 2 >= 1 ) and 100 or 1
            local dmg = math.floor( v / 16 ) * scale
            if dmg <= 0 then return end
            local red = math.floor( v / 4 ) % 2 >= 1
            local hs  = math.floor( v / 2 ) % 2 >= 1
            spawnNum( dmg, hs, red )
        end )
    end

    return self
end

-- (THE FINALE ROAD BANNER, CoD.TodFinaleWarn - the blinking "RUN FOR THE CROWN"
-- plate the Map One ending drove through the todFinaleWarn clientuimodel bit -
-- RETIRED WHOLE 2026-10-05 with the ending: the widget, its baked banner art
-- and the bit in both VMs, one build.)

function LUI.createMenu.tod_upgrade( Instance )
    local Hud = CoD.Menu.NewForUIEditor( "tod_upgrade" )
    CoD.TodUIOwnership.Attach( Hud )

    Hud.soundSet = "HUD"
    Hud:setOwner( Instance )
    Hud:setLeftRight( true, true, 0, 0 )
    Hud:setTopBottom( true, true, 0, 0 )

    -- THE HUD VEIL (2026-09-29, user: "Make sure the HUD doesnt show when cards are
    -- getting pulled"). Every HUD piece this menu draws (damage numbers, luck bar,
    -- tower gauge) lives in HudOnly, built FIRST so it sits under the card panel,
    -- and HudOnly's alpha follows CoD.TodHudVeil. The card panel and the shop
    -- wheel stay on Hud itself, so the veil can never hide them.
    local HudOnly = LUI.UIElement.new()
    HudOnly:setLeftRight( true, true, 0, 0 )
    HudOnly:setTopBottom( true, true, 0, 0 )
    CoD.TodUIOwnership.Attach( HudOnly )
    Hud:addElement( HudOnly )
    if CoD.TodHudVeil then
        CoD.TodHudVeil.Listen( HudOnly, function ( hidden )
            HudOnly:setAlpha( hidden and 0 or 1 )
        end )
    end

    local Panel = CoD.TodUpgradePanel.new( Hud, Instance )
    Hud:addElement( Panel )
    Hud.todUpgradePanel = Panel

    local DmgNum = CoD.TodDmgNum.new( Hud, Instance )
    HudOnly:addElement( DmgNum )   -- under the veil
    Hud.todDmgNum = DmgNum

    -- [tod 2026-09-28] THE BLACK MARKET SPIN (docs/188): the Item Shop reel + the
    -- companion loadout chips. Fail-safed like every other optional require here.
    -- (session 9c's widget; lines added by the docs/187 session at its request)
    pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodSpinReel" )
    if CoD.TodSpinReel then
        local SpinReel = CoD.TodSpinReel.new( Hud, Instance )
        Hud:addElement( SpinReel )
        Hud.todSpinReel = SpinReel
    end
    -- [W2G 2026-10-05] THE COMPANION STATUS PLATE (PK08): the held companion's portrait, state and
    -- bar, on the tod_ptn_hud event (_tod_partners.gsc push_hud), in place of the stock-font
    -- hudelems. In HudOnly, so the HUD veil hides it with the rest of the HUD; the item chips
    -- (TodSpinReel above) sit on its top edge. Fail-safed like every other optional require here.
    pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodCompanionPlate" )
    if CoD.TodCompanionPlate then
        local CompanionPlate = CoD.TodCompanionPlate.new( Hud, Instance )
        HudOnly:addElement( CompanionPlate )   -- under the veil
        Hud.todCompanionPlate = CompanionPlate
    end
    -- [RT 2026-10-05] THE TOAST (docs/218): a teammate's LEGENDARY / ON FIRE and your own tier, re-arm and Archer
    -- lines, in our typeface on the title plate (they were stock-font IPrintLnBold lines across the deal banner).
    -- On Hud itself, after the card panel and the reel, so it draws above both (these moments land mid-deal); it
    -- hides itself under any other veil owner. Fail-safed like every other optional require here.
    pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodToast" )
    if CoD.TodToast then
        local Toast = CoD.TodToast.new( Hud, Instance )
        Hud:addElement( Toast )
        Hud.todToast = Toast
    end

    -- HIDE THE WHOLE MAP HUD FOR THE PAUSE MENU AND THE SCOREBOARD
    -- (audit 2026-08-25). Every widget on this menu -- the tower gauge, the
    -- luck bar, the crosshair damage numbers, the upgrade card panel and the
    -- class draft -- was painting straight over both,
    -- including over the post-loss Restart Map / End Game menu, which is the
    -- one screen a player is trying to read at that moment.
    --
    -- Gated on the ROOT rather than per widget, so anything added to this
    -- menu later is covered without a second thought. This is the vendored
    -- kit's own pattern, copied from AetheriumHud.lua:399 and :442 -- same
    -- model path, same "nil or 0 means visible" test.
    local function todGateHud( bit )
        local m = Engine.GetModel( Engine.GetModelForController( Instance ), "UIVisibilityBit." .. bit )
        if not m then
            return
        end
        Hud:subscribeToModel( m, function ( model )
            local v = Engine.GetModelValue( model )
            Hud:setAlpha( ( v and v ~= 0 ) and 0 or 1 )
        end )
    end
    todGateHud( Enum.UIVisibilityBit.BIT_SCOREBOARD_OPEN )
    todGateHud( Enum.UIVisibilityBit.BIT_UI_ACTIVE )

    -- LUCK BAR v3 (user art drop 2026-08-29, files (65).zip): 11 BAKED fill
    -- states, i_tod_luck_00 (empty) .. i_tod_luck_10 (full) — one whole-image
    -- swap per todUpgLuck change (_tod_luck pushes bar/10). Replaces the v2
    -- frame-with-transparent-window + 10 tinted LUI quads; the gold hot tell
    -- (8..9) and the molten MAX state are baked into the art, so there is no
    -- client-side tinting or fill math left. Same screen rect as v2.
    local LUCK_X, LUCK_Y, LUCK_W, LUCK_H = 24, 56, 304, 38
    -- (The V1 baked fill states - i_tod_luck_00..10, the rampage set and the overcharge frames - left
    -- with the Map 1 purge, 2026-10-04: HUD V2's status plate draws the luck. LuckBar is kept as the
    -- owner of the luck / todRampage / tod_upg_sync subscriptions and draws nothing.)
    local LuckBar = LUI.UIImage.new()
    LuckBar:setLeftRight( true, false, LUCK_X, LUCK_X + LUCK_W )
    LuckBar:setTopBottom( true, false, LUCK_Y, LUCK_Y + LUCK_H )
    HudOnly:addElement( LuckBar )

    -- HUD V2 STATUS PLATE (docs/182 A + B): ROUND and LUCK in one low plate at
    -- (20, 16), 1280x240 art at 0.25. LuckBar stays alive (it owns the luck, rampage
    -- and tod_upg_sync subscriptions) but draws nothing in V2. The ten segments sit
    -- in the plate's channel (art x 400..1240, y 132..204); the round number sits in
    -- its box (art x 32..336, y 80..224) and reads the server's tod_round lane
    -- directly - the same feed AetheriumRoundCounter drew from, re-sent per life by
    -- _tod_upgrade_ui::player_lui_life, so it holds through the Fall.
    -- ROUND BADGE (user drop 2026-09-26): the round left the plate's baked box for
    -- its own 192x192 badge at 0.375 (x 16..88, y 10..82); its number window is
    -- art x 38..153 y 60..123 in BOTH variants = canvas x 30.25..73.75, y 32.5..56.5.
    -- The plate is now the luck-only cut (944x240 at 0.25, x 94..330). The badge and
    -- the plate swap to their RAMPAGE art together, in drawLuckV2, off the one
    -- todRampage flag the Rampage Inducer drives.
    local Status2, LuckSeg2, Round2Row, Badge2 = nil, {}, nil, nil
    local STATUS_IMG, STATUS_RMP_IMG = nil, nil
    local BADGE_IMG, BADGE_RMP_IMG = nil, nil
    local LUCK_ON_IMG, LUCK_OFF_IMG = nil, nil
    local round2 = 1
    -- THE BATTLE ARENA (docs/185 v2.2; user 2026-10-03: "replace the round HUD with Battle Arena /
    -- Level 1 ... rounds dont count in there and its a static difficulty of progression"): while the
    -- party fights in the arena the badge swaps to its ARENA TWIN (i_tod_h2_arena_badge, GENERATED by
    -- tools/battle_arena/make_badge.py from the round badge: the pill reads BATTLE ARENA, the window
    -- carries a LEVEL caption along its top) and the window's number is the LEVEL, drawn under that
    -- caption. arenaLvl > 0 = in the arena. It rides the zero-bit tod_arena event TodArena.lua reads
    -- (show, level, levels, wave, waves, left, flags), re-sent every 2 s, show 0 on the ride home;
    -- the round keeps arriving on tod_round underneath and is back on the badge the moment it ends.
    local arenaLvl = 0
    local ARENA_IMG, ARENA_RMP_IMG = nil, nil
    local TOD_ARENA_NUM_CAP, TOD_ARENA_NUM_BASE = 12.75, 55   -- LOCKSTEP make_badge.py WINDOW_TEXT: the caption owns the window's art rows 60..71, the number rows 86..120
    local function paintRound2()
        if not Round2Row then return end
        local s, cap0, base = string.format( "%d", round2 ), 17, 53
        if arenaLvl > 0 then s, cap0, base = string.format( "%d", arenaLvl ), TOD_ARENA_NUM_CAP, TOD_ARENA_NUM_BASE end
        local cap = cap0
        local w = Round2Row.measure( s, cap, CoD.TodGlyphRow.digitSet )
        if w > 38 then cap = cap * 38 / w; w = 38 end
        Round2Row.set( s, cap, 52 + w / 2, base - ( cap0 - cap ) / 2, CoD.TodGlyphRow.digitSet )
    end
    if USE_HUD_V2 then
        LuckBar:setAlpha( 0 )
        STATUS_IMG     = RegisterImage( "i_tod_h2_luck_plate" )
        STATUS_RMP_IMG = RegisterImage( "i_tod_h2_luck_plate_rampage" )
        BADGE_IMG      = RegisterImage( "i_tod_h2_round_badge" )
        BADGE_RMP_IMG  = RegisterImage( "i_tod_h2_round_badge_rampage" )
        ARENA_IMG      = RegisterImage( "i_tod_h2_arena_badge" )
        ARENA_RMP_IMG  = RegisterImage( "i_tod_h2_arena_badge_rampage" )
        LUCK_ON_IMG    = RegisterImage( "i_tod_h2_luck_on" )
        LUCK_OFF_IMG   = RegisterImage( "i_tod_h2_luck_off" )
        Status2 = LUI.UIImage.new()
        Status2:setLeftRight( true, false, 94, 330 )
        Status2:setTopBottom( true, false, 16, 76 )
        Status2:setImage( STATUS_IMG )
        HudOnly:addElement( Status2 )
        Badge2 = LUI.UIImage.new()
        Badge2:setLeftRight( true, false, 16, 88 )
        Badge2:setTopBottom( true, false, 10, 82 )
        Badge2:setImage( BADGE_IMG )
        HudOnly:addElement( Badge2 )
        for i = 1, 10 do
            local e = LUI.UIImage.new()
            local x = 110 + ( i - 1 ) * 21 + 1
            e:setLeftRight( true, false, x, x + 19 )
            e:setTopBottom( true, false, 52, 64 )
            e:setImage( LUCK_OFF_IMG )
            HudOnly:addElement( e )
            LuckSeg2[ i ] = e
        end
        if CoD.TodGlyphRow then
            Round2Row = CoD.TodGlyphRow.make( Hud, 4 )
            Round2Row.setRGB( 0.98, 0.11, 0.22 )   -- RT: the round number is the Fallen red (r4 ROUND2_TINT pins it to the art's theme)
        end
        round2 = ( CoD.TodRound and CoD.TodRound >= 1 ) and CoD.TodRound or 1
        paintRound2()
        Status2:subscribeToGlobalModel( Instance, "PerController", "scriptNotify", function ( model )
            if Engine.GetModelValue( model ) ~= "tod_round" then return end
            local d = CoD.GetScriptNotifyData( model )
            local r = d and tonumber( d[ 1 ] )
            if r == nil then return end
            r = math.floor( r )
            if r < 1 or r == round2 then return end
            round2 = r
            paintRound2()
        end )
    end

    -- (no LUI text — the fill + baked gold-at-hot IS the readout, doctrine
    -- since 2026-08-20)
    -- RAMPAGE: cached because todUpgLuck changes constantly while todRampage
    -- changes at most a handful of times a match, so the luck subscription
    -- must not have to read a second model on every push.
    local luckRampageOn = false
    local luckLastValue = 0
    local heatNow = 0   -- THE HOT STREAK (docs/201): 0 cold .. 3 ON FIRE, from tod_luck_heat (heatPaint below)

    -- ONE draw path for both sets — the table is chosen here and nowhere else,
    -- so the rampage and overcharge branches can never disagree about which
    -- art is live.
    -- V2: ten segments. 0..10 = that many lit; 11..14 = the OVERCHARGE frames the
    -- server cycles, drawn as all ten white-hot with the two spark frames alternating.
    -- the badge's art: the round badge, or its ARENA twin while the party fights there (docs/185 v2.2),
    -- each with its rampage variant. ONE chooser, read by drawLuckV2 and by the tod_arena lane below.
    local function badgeImage()
        if arenaLvl > 0 then return luckRampageOn and ARENA_RMP_IMG or ARENA_IMG end
        return luckRampageOn and BADGE_RMP_IMG or BADGE_IMG
    end
    local function drawLuckV2( v )
        Status2:setImage( luckRampageOn and STATUS_RMP_IMG or STATUS_IMG )
        Badge2:setImage( badgeImage() )
        if v < 0 then v = 0 elseif v > 10 then v = 10 end   -- 11..14 (the retired overcharge) clamp to full
        for i = 1, 10 do LuckSeg2[ i ]:setImage( ( i <= v ) and LUCK_ON_IMG or LUCK_OFF_IMG ) end
        -- THE HOT STREAK (docs/201): ON FIRE runs the lit segments orange; anything less wears the art's own colour
        local fire = ( heatNow >= 3 )
        for i = 1, 10 do
            if fire and i <= v then
                LuckSeg2[ i ]:setRGB( 1, 0.62, 0.3 )
            else
                LuckSeg2[ i ]:setRGB( 1, 1, 1 )
            end
        end
    end

    -- THE BATTLE ARENA's lane (docs/185 v2.2): tod_arena ( show, level, levels, wave, waves, left, flags ).
    -- show 1 with a level puts the badge in arena dress and writes the LEVEL in its window; show 0 (the
    -- ride home) hands it back to the round. Change-gated: the server re-sends the same state every 2 s
    -- to hydrate a rebuilt HUD, and a re-send must not repaint.
    if USE_HUD_V2 then
        Badge2:subscribeToGlobalModel( Instance, "PerController", "scriptNotify", function ( model )
            if Engine.GetModelValue( model ) ~= "tod_arena" then return end
            local d = CoD.GetScriptNotifyData( model )
            local lvl = 0
            if d and tonumber( d[ 1 ] ) == 1 then
                lvl = math.floor( tonumber( d[ 2 ] ) or 0 )
                if lvl < 1 then lvl = 0 end
            end
            if lvl == arenaLvl then return end
            arenaLvl = lvl
            Badge2:setImage( badgeImage() )
            paintRound2()
        end )
    end

    local function drawLuck( v )
        drawLuckV2( v )
    end

    local luckModel = Engine.CreateModel( Engine.GetModelForController( Instance ), "todUpgLuck" )
    if luckModel then
        LuckBar:subscribeToModel( luckModel, function ( ModelRef )
            luckLastValue = math.floor( tonumber( Engine.GetModelValue( ModelRef ) ) or 0 )
            drawLuck( luckLastValue )
        end )
    end

    -- RAMPAGE INDUCER (v14.20): swap the whole set the moment hard mode is
    -- toggled, WITHOUT waiting for the next luck change — a player sitting at a
    -- static bar (very common right after an upgrade event resets it to 0)
    -- would otherwise keep seeing amber until their next kill. Redraws at the
    -- last known fill level.
    local rampageModel = Engine.CreateModel( Engine.GetModelForController( Instance ), "todRampage" )
    if rampageModel then
        LuckBar:subscribeToModel( rampageModel, function ( ModelRef )
            local v = math.floor( tonumber( Engine.GetModelValue( ModelRef ) ) or 0 )
            luckRampageOn = ( v ~= 0 )
            drawLuck( luckLastValue )
        end )
    end

    -- THE HOT STREAK (docs/201, 2026-10-02): the luck bar runs hot. Embers rise off the lit segments (2 / 4 / 6 by
    -- heat: the card reveal's pip sprite tinted orange, on a FIXED scatter - no random source runs in this menu's
    -- Lua), a chip beside the plate names it (WARM / HEATING UP / ON FIRE, the map's typeface), and ON FIRE runs the
    -- lit segments orange (drawLuckV2). Everything lives in HudOnly, so the veil hides it with the rest of the HUD.
    local HEAT_RGB = { 1, 0.52, 0.14 }
    local EMBER_X = { 0.12, 0.71, 0.38, 0.9, 0.55, 0.24 }    -- fractions along the segment row
    local EMBER_MS = { 900, 1050, 820, 980, 1120, 860 }
    local heatLay = { x0 = 111, x1 = 319, y = 58, chipX = 336, chipY = 40 }   -- V2: the segment row is x 111..319, y 52..64
    local emberImg = CoD.TodCardArt and CoD.TodCardArt.fx and CoD.TodCardArt.fx.pip
    local embers = {}
    for i = 1, #EMBER_X do
        local e = LUI.UIImage.new()
        e:setLeftRight( true, false, 0, 5 )
        e:setTopBottom( true, false, 0, 5 )
        if emberImg then e:setImage( RegisterImage( emberImg ) ) end
        e:setRGB( HEAT_RGB[ 1 ], HEAT_RGB[ 2 ], HEAT_RGB[ 3 ] )
        e:setAlpha( 0 )
        HudOnly:addElement( e )
        embers[ i ] = e
    end
    local HeatChip
    if CoD.TodGlyphText then
        HeatChip = CoD.TodGlyphText.new( { left = heatLay.chipX, right = heatLay.chipX + 120, top = heatLay.chipY, bottom = heatLay.chipY + 16,
                                           align = "left", pool = 12, rgb = HEAT_RGB } )
    else
        HeatChip = LUI.UIText.new()
        HeatChip:setLeftRight( true, false, heatLay.chipX, heatLay.chipX + 120 )
        HeatChip:setTopBottom( true, false, heatLay.chipY, heatLay.chipY + 16 )
        HeatChip:setRGB( HEAT_RGB[ 1 ], HEAT_RGB[ 2 ], HEAT_RGB[ 3 ] )
    end
    HeatChip:setAlpha( 0 )
    HudOnly:addElement( HeatChip )

    local function emberLaunch( i )
        local e = embers[ i ]
        local x = heatLay.x0 + EMBER_X[ i ] * ( heatLay.x1 - heatLay.x0 )
        e:setLeftRight( true, false, x - 2, x + 3 )
        e:setTopBottom( true, false, heatLay.y - 2, heatLay.y + 3 )
        e:setAlpha( 0.95 )
        e:beginAnimation( "tod_heat_ember", EMBER_MS[ i ], false, false, CoD.TweenType.Linear )
        e:setTopBottom( true, false, heatLay.y - 26, heatLay.y - 21 )
        e:setAlpha( 0 )
    end
    for i = 1, #embers do
        local k = i
        embers[ i ]:registerEventHandler( "transition_complete_tod_heat_ember", function ( element, event )
            if event and event.interrupted then return end
            if k <= 2 * heatNow then emberLaunch( k ) end
        end )
    end

    -- the one painter: the embers (new ones start, running ones keep their own chain), the chip (a pulse on a rise),
    -- and the segments' ON FIRE tint (through drawLuck, at the bar's last value)
    local HEAT_CHIP = { "WARM", "HEATING UP", "ON FIRE" }
    local function heatPaint( h, change )
        h = math.max( 0, math.min( 3, math.floor( tonumber( h ) or 0 ) ) )
        local was = heatNow
        heatNow = h
        for i = 1, #embers do
            if i <= 2 * h then
                if i > 2 * was then emberLaunch( i ) end
            else
                embers[ i ]:completeAnimation()
                embers[ i ]:setAlpha( 0 )
            end
        end
        HeatChip:completeAnimation()
        local w = HEAT_CHIP[ h ]
        if w then
            HeatChip:setText( w )
            if change == 1 then
                HeatChip:setAlpha( 0.15 )
                HeatChip:beginAnimation( "tod_heat_chip", 260, false, false, CoD.TweenType.Linear )
            end
            HeatChip:setAlpha( 1 )
        else
            HeatChip:setText( "" )
            HeatChip:setAlpha( 0 )
        end
        drawLuck( luckLastValue )
    end
    heatPaint( CoD.TodHeat or 0, 0 )   -- a rebuilt HUD picks up the last heat it was told

    -- BOSS/ELITE SPAWN BANNERS — REMOVED 2026-08-22 (user: "remove all the
    -- announcement banners for the enemies spawning in. Its unnecessary").
    -- Gone from here: the UIImage + UIText elements, the id->art tables, and
    -- the "tod_boss_banner" scriptNotify subscription. Gone from the server
    -- side: _tod_bosses::banner/banner_notify_all/boss_banner_show/
    -- boss_banner_show_seq and the eventstring precache. Gone from the zone:
    -- the i_tod_banner_panzer / i_tod_banner_protectors image lines.
    -- (i_tod_banner_choose_class and i_tod_banner_upgrade are NOT spawn
    -- banners and stay.)
    -- Enemies now announce themselves diegetically — Panzer music, the Reaver's
    -- meteor, the Protector slam, and the floor gauge's boss pip. Same doctrine
    -- as the removed floaty kill text: no on-screen gameplay captions.

    -- ======================================================================
    -- TOWER GAUGE (user 2026-08-20) — the floor indicator, right screen edge.
    --
    -- Assembled, not a single picture: the DARK gauge is the always-on
    -- backing, then one lit cell is stamped onto every floor at or below the
    -- player, the crown lights on the roof, the base cap lights with the
    -- first cell, a pip marks the lowest live boss, and any cell holding a
    -- DOWNED TEAMMATE swaps to its red down tile. LUI has no UV/crop, so
    -- per-cell stamping is the only way to show a variable-height lit trail —
    -- the tiles are cut out of the delivered masters by tools/slice_gauge.js.
    --
    -- v2 ART (2026-09-02, docs/70): EVERY CELL HAS ITS OWN LIT AND DOWN TILE
    -- (i_tod_gauge_c01..c25 / d01..d25), each a full-width 180x42 band of
    -- the registered master. That is what lets the trail carry the tower's
    -- five DISTRICT colours (cells 1-5 blue, 6-10 green, 11-15 orange, 16-20
    -- gold, 21-25 red — LOCKSTEP with `DISTRICTS` in gen_tower_map.js) and
    -- the lounges (cells 5/10/15/20) their wider plate, with no per-cell
    -- logic here at all: the cell number IS the image name. A shared tile
    -- was measured and rejected — the plate's vignette differs per row, so
    -- one band stamped at another height prints a faint rectangle.
    --
    -- Fed by TWO GSC LuiNotifyEvents, both of which cost ZERO clientuimodel
    -- bits (the 61-bit budget is full): tod_floor (floor, bossFloor) and
    -- tod_down (downMaskLo, downMaskHi). Two events and not one 3-arg event
    -- because the 25-cell down mask is split to keep every transmitted number
    -- under 8192 — the reasoning is written out in _tod_gauge.gsc's header.
    -- At MENU ROOT so it is never alpha-gated by the upgrade panel.
    --
    -- Art grid (canvas 180x1440, v2): crown y0..290 (crown + neck), 25 cells
    -- y290..1340 at pitch 42 (cell f top = 290 + (25 - f) * 42, full canvas
    -- width), base cap y1340..1440. Floor 25 is the TOP cell. Everything
    -- below scales that grid by GA_S — LOCKSTEP with tools/slice_gauge.js,
    -- which cuts the tiles on exactly these lines.
    -- ======================================================================
    -- ======================================================================
    -- HUD V2 DESCENT GAUGE (docs/182 C; user 2026-09-26: "on this map, people are
    -- going from top to bottom"). One rail (64x900 art at 0.5 = x 1232..1264,
    -- y 110..560; crown cap on top, ground cap at the bottom), 25 WHITE segments,
    -- a red "you are here" chevron, a boss marker and a pool of four downed
    -- markers. ~32 elements against V1's 125 (5 caps + 60 lit + 60 down + pip).
    --
    -- THE DATA IS V1's, UNCHANGED: tod_floor (cell the player is on, boss cell),
    -- tod_down (two 13-bit chunks, GA_SPLIT 13 LOCKSTEP with TOD_GAUGE_MASK_SPLIT);
    -- 25 tower cells, LOCKSTEP with V1's GA_CELLS. THE FALL is a descent, so the
    -- floors ABOVE you light, crown down to your cell (i >= f) - progress reads top
    -- to bottom, as the party travels. (The Endless Spire's mode - a 35-cell climb
    -- on its own rail - was removed with the spire, 2026-09-29.)
    -- The tower's five district colours ride the cell index (1-5 blue .. 21-25 red,
    -- LOCKSTEP with DISTRICTS in gen_tower_map.js, same bands V1 baked); lounge
    -- cells (every 5th) draw the wider segment. A downed teammate's cell turns its
    -- segment white-hot red and gets a marker beside the rail.
    -- ======================================================================
    if USE_HUD_V2 then
        local G2_TOWER, G2_SPLIT = 25, 13
        local G2_T0, G2_T1, G2_CX = 148, 522, 1248      -- the track (art y 76..824)
        local G2_DIST = {
            { 0.25, 0.85, 0.91 }, { 0.31, 0.86, 0.47 }, { 1.00, 0.59, 0.16 },
            { 0.96, 0.77, 0.26 }, { 0.94, 0.32, 0.29 },
        }
        local G2_DOWN_RGB = { 1.0, 0.18, 0.22 }
        local RAIL_TOWER = RegisterImage( "i_tod_h2_gauge_tower" )
        local SEG, SEG_HUB, SEG_OFF = RegisterImage( "i_tod_h2_gauge_seg" ), RegisterImage( "i_tod_h2_gauge_seg_hub" ), RegisterImage( "i_tod_h2_gauge_seg_off" )

        local Rail = LUI.UIImage.new()
        Rail:setLeftRight( true, false, 1232, 1264 )
        Rail:setTopBottom( true, false, 110, 560 )
        Rail:setImage( RAIL_TOWER )
        HudOnly:addElement( Rail )

        local Segs = {}
        for i = 1, G2_TOWER do
            local e = LUI.UIImage.new()
            e:setAlpha( 0 )
            HudOnly:addElement( e )
            Segs[ i ] = e
        end
        local function marker( img, rgb )
            local e = LUI.UIImage.new()
            e:setImage( RegisterImage( img ) )
            if rgb then e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] ) end
            e:setAlpha( 0 )
            HudOnly:addElement( e )
            return e
        end
        local You  = marker( "i_tod_h2_gauge_you" )
        local Boss = marker( "i_tod_h2_gauge_boss", { 1.0, 0.45, 0.2 } )
        local Down = {}
        for k = 1, 4 do Down[ k ] = marker( "i_tod_h2_gauge_down" ) end

        local g2F, g2Boss = G2_TOWER + 1, 0
        local g2Down = { 0, 0 }
        local G2_BIT = {}
        do
            local v = 1
            for i = 1, G2_SPLIT do G2_BIT[ i ] = v; v = v * 2 end
        end
        local function isHub( i ) return ( i % 5 == 0 ) and ( i < G2_TOWER ) end
        -- centre y of cell i (floor 1 at the BOTTOM of the track)
        local function cellY( i )
            local p = ( G2_T1 - G2_T0 ) / G2_TOWER
            return G2_T1 - ( i - 0.5 ) * p
        end
        local function isDown( i )
            local chunk = math.floor( ( i - 1 ) / G2_SPLIT )
            local bit = ( i - 1 ) - chunk * G2_SPLIT
            return ( math.floor( ( g2Down[ chunk + 1 ] or 0 ) / G2_BIT[ bit + 1 ] ) % 2 ) >= 1
        end
        local function layout()
            local h = 8.4
            for i = 1, G2_TOWER do
                local e = Segs[ i ]
                local w = 14
                if isHub( i ) then w = w * 1.4 end
                local y = cellY( i )
                e:setLeftRight( true, false, G2_CX - w / 2, G2_CX + w / 2 )
                e:setTopBottom( true, false, y - h / 2, y + h / 2 )
                e:setAlpha( 1 )
            end
        end
        local function apply()
            local n = G2_TOWER
            local atTop = g2F > n
            local f = atTop and ( n + 1 ) or g2F
            local dk = 0
            for i = 1, n do
                local e = Segs[ i ]
                local lit = ( i >= f )
                if isDown( i ) then
                    e:setImage( SEG )
                    e:setRGB( G2_DOWN_RGB[ 1 ], G2_DOWN_RGB[ 2 ], G2_DOWN_RGB[ 3 ] )
                    if dk < #Down then
                        dk = dk + 1
                        local y = cellY( i )
                        Down[ dk ]:setLeftRight( true, false, 1207, 1219 )
                        Down[ dk ]:setTopBottom( true, false, y - 6, y + 6 )
                        Down[ dk ]:setAlpha( 1 )
                    end
                elseif lit then
                    local c = G2_DIST[ math.min( 5, math.floor( ( i - 1 ) / 5 ) + 1 ) ]
                    e:setImage( isHub( i ) and SEG_HUB or SEG )
                    e:setRGB( c[ 1 ], c[ 2 ], c[ 3 ] )
                else
                    e:setImage( isHub( i ) and SEG_HUB or SEG_OFF )
                    if isHub( i ) then e:setRGB( 0.22, 0.22, 0.28 ) else e:setRGB( 1, 1, 1 ) end
                end
            end
            for k = dk + 1, #Down do Down[ k ]:setAlpha( 0 ) end
            -- you: beside your cell, or beside the top cap when you are on the roof
            local yy = atTop and 128 or ( ( f < 1 ) and 540 or cellY( f ) )
            You:setLeftRight( true, false, 1220, 1232 )
            You:setTopBottom( true, false, yy - 6, yy + 6 )
            You:setAlpha( 1 )
            if g2Boss >= 1 and g2Boss <= n then
                local by = cellY( g2Boss )
                Boss:setLeftRight( true, false, 1194, 1206 )
                Boss:setTopBottom( true, false, by - 6, by + 6 )
                Boss:setAlpha( 1 )
            else
                Boss:setAlpha( 0 )
            end
        end
        layout()
        apply()

        Rail:subscribeToGlobalModel( Instance, "PerController", "scriptNotify", function ( model )
            local ev = Engine.GetModelValue( model )
            if ev ~= "tod_floor" and ev ~= "tod_down" then
                return
            end
            local d = CoD.GetScriptNotifyData( model )
            if not d then return end
            if ev == "tod_down" then
                g2Down[ 1 ] = ( type( d[ 1 ] ) == "number" ) and d[ 1 ] or 0
                g2Down[ 2 ] = ( type( d[ 2 ] ) == "number" ) and d[ 2 ] or 0
                apply()
                return
            end
            g2F = ( type( d[ 1 ] ) == "number" ) and d[ 1 ] or 0
            g2Boss = ( type( d[ 2 ] ) == "number" ) and d[ 2 ] or 0
            apply()
        end )
    end

    -- [tod] OWNED-UPGRADES SYNC (pause-menu list): GSC's refresh_upgrade_list
    -- sends one int-only LuiNotifyEvent per owned domain (id, level, max) —
    -- map 1's kill-feed lane (scriptNotify PerController model +
    -- CoD.GetScriptNotifyData). Accumulated here because THIS menu is always
    -- open; AetheriumStartMenu.lua reads CoD.TodOwned on every pause open.
    CoD.TodOwned = CoD.TodOwned or {}
    LuckBar:subscribeToGlobalModel( Instance, "PerController", "scriptNotify", function ( model )
        if Engine.GetModelValue( model ) == "tod_upg_sync" then
            local d = CoD.GetScriptNotifyData( model )
            if d and type( d[ 1 ] ) == "number" and type( d[ 2 ] ) == "number" then
                -- [tod v14.13] the max arg CARRIES the survives-promotion bit:
                -- GSC sync_max() adds 100 when THIS player's copy of the domain
                -- survives a tier card (SCAVENGER is assault-only persistence
                -- now, so a static table cannot know — the server does). Strip
                -- it here; AetheriumStartMenu's reset badge reads .safe and
                -- falls back to its static tierSafe() only when .safe is nil.
                local m = ( type( d[ 3 ] ) == "number" and d[ 3 ] ) or 10
                -- DARK UPGRADES (v17.10): a SECOND packed bit, +200, and it MUST be
                -- stripped BEFORE the +100 survives bit. A dark row that also
                -- survives arrives as 10 + 100 + 200 = 310; testing >= 100 first
                -- would strip one hundred and leave 210, reporting a nonsense max
                -- and losing the dark flag entirely.
                local dark = false
                if m >= 200 then
                    dark = true
                    m = m - 200
                end
                local safe = nil
                if m >= 100 then
                    safe = true
                    m = m - 100
                else
                    safe = false
                end
                CoD.TodOwned[ d[ 1 ] ] = { lvl = d[ 2 ], max = m, safe = safe, dark = dark }
            end
        elseif Engine.GetModelValue( model ) == "tod_upg_class" then
            -- [tod v16] one int: this player's CLASS ID, 1..4, or 0 when they
            -- have not drafted yet. Pushed before EVERY deal alongside the tier
            -- hint, so the panel can read it while it paints and nothing has to
            -- clear it when the panel closes.
            local d = CoD.GetScriptNotifyData( model )
            CoD.TodClass = ( d and type( d[ 1 ] ) == "number" and d[ 1 ] ) or 0
        elseif Engine.GetModelValue( model ) == "tod_input_pad" then
            -- [tod v16.3] the server saw this player's d-pad (pad_latch): pad
            -- plates from now on, in this menu and the class draft. See
            -- UsingController() above. One int, always 1; never cleared.
            CoD.TodPad = true
        elseif Engine.GetModelValue( model ) == "tod_upg_tier_need" then
            -- [tod v14.35] one int: the floor this player must still REACH
            -- before a CLASS TIER card can be dealt, or 0 when the floor is not
            -- what is stopping them. GSC pushes it before EVERY deal (0
            -- included), so the panel can read it without anyone having to
            -- clear it when the panel closes.
            local d = CoD.GetScriptNotifyData( model )
            CoD.TodTierNeed = ( d and type( d[ 1 ] ) == "number" and d[ 1 ] ) or 0
        elseif Engine.GetModelValue( model ) == "tod_luck_heat" then
            -- [tod 2026-10-02] THE HOT STREAK (docs/201): ( heat, streak, change ), change 1 = it just rose,
            -- 2 = it just ended, 0 = a refresh. Recorded as CoD.TodHeat (the card reveal's warm backs read it),
            -- drawn on the luck plate, and handed to the card panel's HOT STREAK line.
            local d = CoD.GetScriptNotifyData( model )
            local h = ( d and type( d[ 1 ] ) == "number" and d[ 1 ] ) or 0
            local change = ( d and type( d[ 3 ] ) == "number" and d[ 3 ] ) or 0
            CoD.TodHeat = h
            heatPaint( h, change )
            if Panel and Panel.todHeatPaint then
                Panel.todHeatPaint( h, change == 1 )
            end
        end
    end )

    -- MAG +N chip — DELETED v17.9. It was dead AND in the way, which is why it
    -- goes rather than being left alone:
    --   DEAD: it read the todMagBonus model, whose only writer is
    --   _tod_upgrade_ui::set_mag_bonus, and that function has ZERO call sites.
    --   Nothing has pushed a value into it since it was written.
    --   IN THE WAY: setLeftRight(false,true,-330,-180) / setTopBottom(false,
    --   true,-52,-30) put it at canvas x950..1100, y668..690 — straight through
    --   the v17.9 gun panel's reserve row (x1000..1256, y604..678) — and this
    --   menu is the always-open additive overlay, so it draws ON TOP of the HUD.
    --   A dead element that cannot be seen is clutter; a dead element that
    --   overdraws a live readout is a bug waiting for someone to call the
    --   function. set_mag_bonus is left in the GSC as the documented entry point
    --   if the bottomless-mag pool ever needs a readout again — it would want a
    --   slot inside the gun panel now, not a chip floating over it.

    return Hud
end
