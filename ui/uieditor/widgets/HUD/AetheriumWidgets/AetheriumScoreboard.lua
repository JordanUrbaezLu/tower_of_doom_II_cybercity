require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership" )
-- Aetherium Custom Scoreboard Widget
-- BO6-style scoreboard with custom design

CoD.AetheriumScoreboard = InheritFrom( LUI.UIElement )

-- ===========================================================================
-- [tod v15 item 13] YOUR UPGRADES, ON THE SCOREBOARD
-- ===========================================================================
-- User: "Can we put the upgrade menu in the scoreboard as well so players can
-- move and read?" The owned-upgrades list previously existed ONLY in the pause
-- menu, which freezes you. The scoreboard is a plain HUD widget with no focus
-- lock, so the player keeps moving while it is up — which is the whole ask.
--
-- THE DATA IS ALREADY HERE AND COSTS NOTHING NEW. CoD.TodOwned is populated by
-- the always-open `tod_upgrade` HUD menu from the GSC spawn push, NOT by the
-- pause menu opening — AetheriumStartMenu.lua is a plain reader of the same
-- global. So a player who has never opened the pause menu still has a full
-- table here. No clientfield, no new LuiNotifyEvent, no GSC change at all.
-- (That mattered: the clientuimodel pool is at 60 of a proven 61 bits and
-- overflow is a map-load abort, not a glitch.)
--
-- PERSONAL LIST ONLY. Showing all four players' upgrades would need a fourth
-- int on the sync event, and 4-arg LuiNotifyEvent is stock-proven but not
-- tod-proven — not worth spending on a convenience panel.
--
-- THE PAUSE PLATES, NOT TEXT ROWS (user 2026-09-01: "we should just reuse the
-- images on the pause menu since those are too good"). This panel now draws the
-- SAME baked art AetheriumStartMenu.lua draws — i_tod_pause_hdr, one
-- i_tod_pause_r<NN> name plate per domain, i_tod_pause_pip / _pip_empty level
-- pips, i_tod_pause_reset_mark and i_tod_pause_legend_reset. Same images, same
-- meaning, two screens: nothing new was baked and nothing new was zoned. It also
-- settles the images-over-LUI rule for this panel, which the text version was
-- the one live exception to.
--
-- THE COMMENT THAT USED TO SIT HERE ARGUED FOR TEXT ON THE GROUND THAT A NEW
-- DOMAIN COULD RENDER AS A BLANK PLATE. That risk is real, and it is handled the
-- way the pause menu handles it rather than by avoiding art: TOD_UPG_PLATE_MAX
-- below is the highest id with baked row art, and ids above it fall back to a
-- text label. RegisterImage on a missing image is undefined behavior, so nothing
-- here ever reaches for a plate that does not exist. Note the test is a <= over
-- a CONTIGUOUS range — r01..r43 all exist on disk, including the eight RETIRED
-- but still-mapped ids (9, 11, 12, 22, 28, 30, 32, 34), which a player can
-- legitimately still hold a level in.
-- ⚠️ LOCKSTEP: the same number lives in AetheriumStartMenu.lua as
-- PAUSE_PLATE_MAX. Raise BOTH when new row art lands, or one screen shows a
-- plate where the other shows text.
--
-- THE SPACE IS TIGHTER HERE THAN IN THE PAUSE MENU, AND THE BOUNDS ARE REAL
-- ELEMENTS, NOT TASTE (the user flagged this up front: "we may have less space
-- on that screen"). Measured against this widget's own geometry:
--   * TOP y=90. map_info_bg is x15..323, y48..86 — the panel clears it.
--   * BOTTOM y=392. The player rows FILL FROM THE BOTTOM and the column header
--     is re-topped to sit directly above the top-most one (see the Visible
--     clip), so the header's HIGHEST possible top is the four-player case,
--     y=397. Four players is the worst case and the only one worth planning
--     against.
--   * WIDTH is the compensation. The pause panel is walled in at x=814 by
--     BGBlood; this one has the full 1280.
-- That is 302 usable pixels of height against the pause menu's 413, and 1280 of
-- width against its 750. Hence THREE columns of SIX rather than two of seven: 18
-- slots at a 44px pitch (the pause menu's 59), and THE ACTIVATION LINE IS
-- DROPPED. The effect line at your current level is what players open the board
-- to read; the pause menu remains the full readout.
--
-- The AetheriumQuestsCustom widget nominally owns y0..182 across the full width,
-- which would collide head-on — but it is setAlpha(0) in both state clips ("no
-- quest system on this map"), so that band is genuinely free.
--
-- 18 SLOTS IS HEADROOM, NOT A GUESS. v15 item 19 made persistence the rule on a
-- class promotion, which took the worst case from the pause menu's stated 14 to
-- 15 owned rows for a maxed HEAVY. Overflow past 18 prints a truthful "+N MORE"
-- rather than dropping rows silently.
--
-- EVERY SIZE BELOW HOLDS THE ART'S OWN ASPECT — the v6.6 stretched-plate lesson.
-- Read off the PNGs 2026-09-01: hdr 1000x70 (14.2857) -> 400x28; legend_reset
-- 760x56 (13.5714) -> 380x28; r<NN> 300x44 (6.8182) -> 191x28; pip and
-- pip_empty 24x24 and reset_mark 128x128, all square.
--
-- ⚠️ LUI FAILURES ARE SILENT and lint_tod_lua.js only proves bracket balance, so
-- every access below is nil-guarded and the whole thing is wrapped so a nil
-- global can never take the scoreboard down with it.
-- ⚠️ **THIS PANEL IS AREA-BOUND, AND THE BINDING CONSTRAINT IS HEIGHT, NOT
-- WIDTH** (measured 2026-09-01 on the user's "we have more width space to make
-- our images bigger"). They were right that width was being wasted, and it is
-- taken below — but width alone could not have grown the plates, because the
-- plate's ASPECT IS FIXED at 300:44. A wider plate is a taller plate, a taller
-- plate is a taller row, and rows are what the 302px band runs out of. Solved
-- rather than guessed:
--
--   plate h=28 (w=191)  row 45  ->  6 rows/col  = 18 slots   <- was
--   plate h=33 (w=225)  row 50  ->  6 rows/col  = 18 slots   <- IS (the ceiling)
--   plate h=36 (w=245)  row 53  ->  5 rows/col  = 15 slots
--   plate h=44 (w=300)  row 61  ->  4 rows/col  = 12 slots   <- native art size
--
-- **h=33 IS THE LARGEST PLATE THAT STILL FITS 18 SLOTS**, and it is an EXACT
-- aspect match — 300:44 reduces to 225:33 in whole pixels, the only clean
-- multiple in the usable range. +18% linear on every plate for free. Anything
-- past it BUYS PIXELS WITH ROWS: 245-wide plates cost 3 slots, native 300-wide
-- art costs 6 and would put a maxed HEAVY's list behind "+3 MORE". That trade is
-- available and is a design call, not a technical limit — it is not taken here
-- because hiding owned upgrades to enlarge the label defeats the panel.
--
-- WHERE THE 32px CAME FROM. The header and legend used to sit at y96..124,
-- directly above the rows, which cost the panel a whole row of growth. They now
-- sit at y56..84 BESIDE the map-info block, which only reaches x=323 — so
-- everything at x>330 is free to the top of the screen. That band was invisible
-- until the quest widget was deleted, and reclaiming it is what pays for h=33.
--
-- THE WIDTH THE USER SAW IS ALSO TAKEN: margins 50 -> 30 and columns 350 -> 389,
-- which additionally gives the effect line +45px and lets it come up from 0.82
-- to 0.90 scale. Right edge 1249; 30px margins each side are deliberate TV
-- overscan headroom, not slack.
-- [tod 2026-09-26] SCOREBOARD V2 (docs/181; user: "the scoreboard also needs the
-- same redesign"): the red "Fallen" scoreboard on 8 baked pieces (i_tod_sb_*) plus
-- the pause menu's pips and 26 icons. FALSE = the layout below, byte-for-byte.
local USE_SCOREBOARD_V2  = true
-- 2 x 6 = 12: THE USER'S PER-CLASS CAP (pause menu TOD_PAUSE_ROWS_CAP), on both
-- screens. tools/lint_tod_assets.js reads COLS x ROWS_COL as this panel's capacity.
local TOD_UPG_COLS       = 2
-- THE AI COMPANION ROW: the first row of every list (2026-09-28), LIVE since 2026-09-29 (user:
-- "wire it all up ... Make sure the upgrades are there as well"): the companion you hold (its
-- portrait, its name + state, its three Black Market items as rarity chips and by name), from
-- CoD.TodCompanionDescribe (TodSpinReel.lua). Nothing held = the fields below.
-- .view rides this table on purpose (no new upvalue). LOCKSTEP AetheriumStartMenu.lua TOD_PARTNER_ROW.
local TOD_PARTNER_SB     = { name = "AI COMPANION", eff = "NONE YET", icon = "i_tod_pm_ico_companion" }
TOD_PARTNER_SB.view = function()
	if CoD.TodCompanionDescribe then
		local ok, v = pcall( CoD.TodCompanionDescribe )
		if ok and type( v ) == "table" then return v end
	end
	return { held = false, name = TOD_PARTNER_SB.name, items = TOD_PARTNER_SB.eff, short = "", tone = "idle", slots = {} }
end
local TOD_UPG_ROWS_COL   = 5                  -- per column; 2 x 5 = 10 slots (the 10-row cap since 2026-09-28; was 2 x 6)
-- V2 frames: the top panel's 1536x520 art at 0.7637 -> 28..1201 x 28..425; the bottom
-- panel's 1540x280 at 0.7656 -> 46..1225 x 431..645; the points capsule 480x104 at
-- 0.4917 -> 522..758 x 650..701.
local SB_TX, SB_TY, SB_TS = 28, 28, 0.7637
local SB_BX, SB_BY, SB_BS = 46, 431, 0.7656
local function SBT( ax, ay ) return SB_TX + ax * SB_TS, SB_TY + ay * SB_TS end
local function SBB( ax, ay ) return SB_BX + ax * SB_BS, SB_BY + ay * SB_BS end
-- Column centres of the baked header strip, in bottom-panel art px (docs/181).
local SB_COL_AX = { 90, 277, 598, 803, 1023, 1224, 1407 }
local SB_PROW_H, SB_PROW_PITCH = 28, 28.5   -- 4 player rows in the strip's 122..272 art band
local SB_ICON = {
	[2] = "i_tod_pm_ico_dr", [3] = "i_tod_pm_ico_bounty",
	[4] = "i_tod_pm_ico_luck", [45] = "i_tod_pm_ico_riotshield",
	[24] = "i_tod_pm_ico_tier", [38] = "i_tod_pm_ico_summonpower", [39] = "i_tod_pm_ico_soulbeam",
	[59] = "i_tod_pm_ico_soulbomb", [41] = "i_tod_pm_ico_grapple", [57] = "i_tod_pm_ico_retriever",
	[58] = "i_tod_pm_ico_pellets", [60] = "i_tod_pm_ico_c4", [61] = "i_tod_pm_ico_cluster",
	[62] = "i_tod_pm_ico_bash", [63] = "i_tod_pm_ico_gravsmash",
	-- PK05 (2026-10-04): the 13 live cards that drew the generic hexagon. LOCKSTEP AetheriumStartMenu.lua PM_ICON.
	[29] = "i_tod_pm_ico_sprint", [6] = "i_tod_pm_ico_deadeye", [35] = "i_tod_pm_ico_quickdraw",
	[26] = "i_tod_pm_ico_piercing", [25] = "i_tod_pm_ico_adrenaline", [36] = "i_tod_pm_ico_fusion",
	[37] = "i_tod_pm_ico_vitality", [7] = "i_tod_pm_ico_armsspecialist", [48] = "i_tod_pm_ico_cleave",
	[12] = "i_tod_pm_ico_demonslayer", [5] = "i_tod_pm_ico_reapersreach", [19] = "i_tod_pm_ico_summonermaster",
	[9] = "i_tod_pm_ico_cloak",
}
local TOD_UPG_COL_X      = { 30, 445, 860 }   -- 26px gaps; col 3 ends at 1249, matching the 30px left margin
local TOD_UPG_COL_W      = 389
local TOD_UPG_Y0         = 92                 -- 8px under the header band (bottom 84)
local TOD_UPG_ROW_H      = 50                 -- last row: 92 + 5*50 + 33 + 16 = 391 <= 392
local TOD_UPG_PLATE_W    = 225                -- 300x44 art at EXACT 3/4 scale
local TOD_UPG_PLATE_H    = 33
local TOD_UPG_PIP_D      = 13
local TOD_UPG_PIP_PITCH  = 15                 -- plate + a full 10-pip run = 381 <= COL_W 389

local function TodBuildUpgradeList( self )
	-- Tear down last open's rows. One handle, closed before rebuild — the
	-- state-pool leak doctrine this kit has already been bitten by twice. EVERY
	-- element an open creates goes into this one list — plates, pips, badges and
	-- text alike — so nothing can outlive it. The header and the legend are the
	-- deliberate exceptions: they are built ONCE at construction and only
	-- alpha-toggled here, because their geometry never depends on the data.
	if self.todUpgRows then
		for i = 1, #self.todUpgRows do
			if self.todUpgRows[ i ] then
				self.todUpgRows[ i ]:close()
			end
		end
	end
	self.todUpgRows = {}

	local owned = CoD.TodOwned
	local info = CoD.TodDomainInfo
	if type( owned ) ~= "table" then
		return
	end

	-- AT THE TOP TIER THERE IS NOTHING LEFT TO LOSE — the same rule the pause
	-- menu applies, read off the same row, so the two screens can never badge
	-- differently. Row 24 is the CLASS TIER row: lvl = the current tier, max =
	-- tier_max(), compared as lvl >= max rather than against a hardcoded 3.
	-- ABSENT MEANS TIER 1, not "unknown" — that row is only sent from tier 2 on
	-- — so the nil path must leave the badges showing.
	local tierRow = owned[ 24 ]
	local atTopTier = tierRow ~= nil and tierRow.lvl ~= nil and tierRow.max ~= nil
	                  and tierRow.lvl >= tierRow.max

	-- Collect held domains. Ids run 1..63 (the domain-id field is 6 bits);
	-- the body is nil-guarded so unused ids cost nothing.
	local rows = {}
	for id = 1, 63 do
		local o = owned[ id ]
		if o and o.lvl and o.lvl > 0 and id ~= 24 then   -- 24 is the CLASS TIER row, not an upgrade
			local name = ( info and info[ id ] and info[ id ].name ) or ( "UPGRADE " .. id )
			local eff = nil
			if CoD.TodDomainDesc then
				eff = CoD.TodDomainDesc( id, o.lvl, o.dark )   -- v17.10
			end
			if not eff then
				eff = ( info and info[ id ] and info[ id ].desc ) or ""
			end
			rows[ #rows + 1 ] = {
				id = id,
				-- DARK UPGRADE (fix 2026-09-04, user: "Also check the scoreboard
				-- menu as well. Also not wired up correctly"). v17.10 passed
				-- o.dark into TodDomainDesc above, so this panel has printed the
				-- DARK VALUE since the day the feature landed — and then drew the
				-- ordinary blue plate over it, so the number moved with nothing on
				-- screen saying why. HALF-WIRING IS WORSE THAN NOT WIRING: a plain
				-- row showing a number the plain row cannot explain reads as a bug
				-- in the number.
				dark = ( o.dark == true ),
				lvl = o.lvl,
				-- o.max is ALREADY UNPACKED. GSC sync_max() adds 100 to the max
				-- arg to smuggle the survives-promotion bit through an int-only
				-- LuiNotifyEvent (no 4-arg form exists in-tree); tod_upgrade.lua
				-- strips the 100 into .safe before storing. Never re-mask here.
				max = o.max or 10,
				name = name,
				eff = eff,
				-- THE BADGE IS SERVER-COMPUTED, AND ONLY SERVER-COMPUTED HERE.
				-- The bit is set by the same domain_survives_tier() that
				-- tier_up's reset actually runs, so badge and reset cannot
				-- disagree. AetheriumStartMenu.lua additionally carries a static
				-- TIER_RESETS table for the o.safe == nil case; this
				-- deliberately does NOT copy it. A duplicated list of 13 ids is
				-- a second source of truth that nothing regenerates, and it has
				-- already had to be INVERTED once (v15 item 19). That path is
				-- dead anyway: tod_upgrade.lua writes .safe as true or false on
				-- every row and never leaves it nil. So unknown reads as SAFE —
				-- a missing warning is a smaller lie than a confident wrong one.
				resets = ( o.safe == false ) and ( not atTopTier ),
			}
		end
	end

	-- THE LIST ORDER (2026-09-28, the pause menu's): AI PARTNER first (V2 only), the class's own
	-- cards in id order, then the three every class shares (DMG REDUCTION, LUCK, BOUNTY).
	if USE_SCOREBOARD_V2 then
		local SHARED_ORDER = { [2] = 1, [4] = 2, [3] = 3 }
		local classRows, sharedRows = {}, {}
		for _, r in ipairs( rows ) do
			if SHARED_ORDER[ r.id ] then sharedRows[ #sharedRows + 1 ] = r else classRows[ #classRows + 1 ] = r end
		end
		table.sort( sharedRows, function( a, b ) return SHARED_ORDER[ a.id ] < SHARED_ORDER[ b.id ] end )
		rows = { { id = 0, partner = true, lvl = 0, max = 0, name = TOD_PARTNER_SB.name, eff = TOD_PARTNER_SB.eff, resets = false } }
		for _, r in ipairs( classRows ) do rows[ #rows + 1 ] = r end
		for _, r in ipairs( sharedRows ) do rows[ #rows + 1 ] = r end
	end

	if #rows == 0 then
		return
	end

	local cap = TOD_UPG_ROWS_COL * TOD_UPG_COLS
	local shown = #rows
	local overflow = 0
	if shown > cap then
		overflow = shown - cap
		shown = cap
	end

	-- Balance the columns, and only open a column when there is enough to fill
	-- one: a 4-row list reads as a single short block, not as three stubs side
	-- by side. perCol is the tallest column and columns fill left to right;
	-- ceil( shown / 3 ) * 3 >= shown is what guarantees col never exceeds 3.
	local perCol
	if shown <= TOD_UPG_ROWS_COL then
		perCol = shown
	elseif shown <= TOD_UPG_ROWS_COL * 2 then
		perCol = math.ceil( shown / 2 )
	else
		perCol = math.ceil( shown / TOD_UPG_COLS )
	end

	local anyReset = false

	if USE_SCOREBOARD_V2 then
		-- V2 ROWS: the body of the top panel is art x 64..1180, y 190..500. Six
		-- rows a column at pitch 40 (row 38 tall = 1024x112 art at 0.3393 ->
		-- 347.4 wide), the two columns centred with a 20 gap. Name (white) and the
		-- effect line (light blue) in the map TTF, the pips right-aligned, the
		-- icon (a pause-menu glyph, tinted) in the well. No activation line and
		-- no reset badge: the target shows neither, and the pause menu owns them.
		-- 2026-09-28: 2 x 5 (the 10-row cap). Rows 38 -> 43 tall (2 x 393 + 20 = 806 of the
		-- body's 852 units), pitch 40 -> 48 so five rows fill its 237 (4 x 48 + 43 = 235).
		-- Every metric below scales by RS = 43 / 38.
		local ROW_H = 43
		local ROW_W = ROW_H * 1024 / 200 * ( 200 / 112 )   -- 1024 x 112 art
		local PITCH = 48
		local RS = ROW_H / 38
		local bL, bT = SBT( 64, 190 )
		local bR, bB = SBT( 1180, 500 )
		local COLX = { ( bL + bR ) / 2 - 10 - ROW_W, ( bL + bR ) / 2 + 10 }
		local PD, PP = 8.5 * RS, 10 * RS   -- 9 pips; tighter so long names fit (2026-09-28)
		local function Pic( name, l, r, t, b, rgb )
			local e = LUI.UIImage.new()
			e:setLeftRight( true, false, l, r )
			e:setTopBottom( true, false, t, b )
			e:setImage( RegisterImage( name ) )
			if rgb then e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] ) end
			self:addElement( e )
			self.todUpgRows[ #self.todUpgRows + 1 ] = e
			return e
		end
		local function Txt( str, l, r, t, b, rgb )
			local e = LUI.UIText.new()
			e:setLeftRight( true, false, l, r )
			e:setTopBottom( true, false, t, b )
			e:setTTF( "fonts/tod_tower1.ttf" )
			e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
			e:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
			e:setText( str )
			self:addElement( e )
			self.todUpgRows[ #self.todUpgRows + 1 ] = e
			return e
		end
		for i = 1, shown do
			local r = rows[ i ]
			local col = math.floor( ( i - 1 ) / perCol ) + 1
			local idx = ( i - 1 ) % perCol
			local x = COLX[ col ] or COLX[ 1 ]
			local y = bT + idx * PITCH
			local dark = ( r.dark == true )
			-- THE AI COMPANION ROW (live, 2026-09-29): dimmed only when none is held
			local cd = r.partner and TOD_PARTNER_SB.view() or nil
			local held = ( cd ~= nil and cd.held == true )
			if cd then
				r.name = cd.name or TOD_PARTNER_SB.name
				if held and cd.short and cd.short ~= "" then r.name = r.name .. " - " .. cd.short end
				r.eff = cd.items or ""
			end
			local rowPic = Pic( dark and "i_tod_sb_row_violet" or "i_tod_sb_row", x, x + ROW_W, y, y + ROW_H )
			if r.partner and not held then rowPic:setAlpha( 0.6 ) end
			-- the well: art 10..102 x 10..102 of 112 -> centre (56, 56)
			local cx, cy = x + 56 * ROW_H / 112, y + 56 * ROW_H / 112
			if held and cd.portrait then
				local pw = 27 * RS   -- the companion's portrait (240 x 192) inside the well's frame
				Pic( cd.portrait, cx - pw / 2, cx + pw / 2, cy - pw * 0.4, cy + pw * 0.4 )
			else
				Pic( r.partner and TOD_PARTNER_SB.icon or SB_ICON[ r.id ] or "i_tod_pm_ico_generic", cx - 12 * RS, cx + 12 * RS, cy - 12 * RS, cy + 12 * RS,
				     r.partner and { 0.59, 0.64, 0.78 } or ( dark and { 0.71, 0.36, 1.0 } or { 0.95, 0.13, 0.23 } ) )   -- RT: icon the Fallen red (docs/181)
			end
			local pipN = r.max
			if pipN > 10 then pipN = 10 end
			if pipN < r.lvl then pipN = r.lvl end
			local px0 = x + ROW_W - 10 * RS - pipN * PP
			for p = 1, pipN do
				local px = px0 + ( p - 1 ) * PP
				local img = "i_tod_pm_pip_off"
				if p <= r.lvl then img = dark and "i_tod_pm_pip_on_violet" or "i_tod_pm_pip_on" end
				Pic( img, px, px + PD, y + 6.5 * RS, y + 6.5 * RS + PD )
			end
			local info = CoD.TodCompanionInfo
			if held and info then
				-- the three Black Market items where the pips go: the HUD chip, rarity-tinted
				local ch, cg = 13 * RS, 2
				local cy0 = y + 6.5 * RS + PD / 2 - ch / 2
				local right = x + ROW_W - 10 * RS
				for c = 1, 3 do
					local slot = cd.slots and cd.slots[ c ]
					local l = right - ( 4 - c ) * ch - ( 3 - c ) * cg
					local rgb = slot and slot.rgb or info.emptyRim
					local chip = Pic( info.chip, l, l + ch, cy0, cy0 + ch, rgb )
					if slot and slot.icon then
						local ins = ch * 4 / 28
						Pic( slot.icon, l + ins, l + ch - ins, cy0 + ins, cy0 + ch - ins, rgb )
					else
						chip:setAlpha( 0.35 )
					end
				end
				px0 = right - 3 * ch - 2 * cg
			end
			local tx = x + 120 * ROW_H / 112
			local idle = r.partner and not held
			local nameRGB = idle and { 0.74, 0.77, 0.82 } or { 0.93, 0.95, 0.97 }
			if held and cd.tone == "hot" then nameRGB = { 0.98, 0.64, 0.24 } end   -- destroyed: amber until it is back
			Txt( held and r.name or Engine.Localize( r.name ), tx, px0 - 4, y + 4.5 * RS, y + 17.5 * RS, nameRGB )
			Txt( r.eff, tx, x + ROW_W - 6, y + 20 * RS, y + 31 * RS, idle and { 0.59, 0.64, 0.78 } or { 0.50, 0.78, 0.96 } )
		end
		if overflow > 0 then
			Txt( "+" .. overflow .. " MORE", COLX[ 1 ], COLX[ 1 ] + ROW_W, bB - 12, bB, { 0.48, 0.51, 0.62 } )
		end
		-- THE CLASS HEADER (2026-09-28, the pause menu's, one source in tod_upgrade.lua): class name,
		-- TIER, what the next tier needs, and the PASSIVE, in the empty strip right of the ROUND box
		-- (top panel art x 660..990, y 18..98). Rebuilt with the rows on every open.
		local info = ( CoD.TodClassInfo or {} )[ CoD.TodClass or 0 ]
		if info then
			local hx0 = SBT( 660, 0 )
			local hx1 = SBT( 990, 0 )
			local function HTxt( str, ax0, ay0, ay1, rgb, align )
				if not str or str == "" then return end
				local x0 = SBT( ax0, 0 )
				local _, y0 = SBT( 0, ay0 )
				local _, y1 = SBT( 0, ay1 )
				local e = Txt( str, x0, hx1, y0, y1, rgb )
				if align then e:setAlignment( align ) end
			end
			local tierLine, nextLine = "", ""
			if CoD.TodClassTierLines then tierLine, nextLine = CoD.TodClassTierLines() end
			HTxt( info.name, 660, 18, 46, { 0.93, 0.95, 0.97 } )
			HTxt( tierLine, 660, 18, 36, { 1.0, 0.80, 0.30 }, Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT )
			HTxt( nextLine, 660, 37, 48, { 0.62, 0.66, 0.76 }, Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT )
			HTxt( "PASSIVE", 660, 56, 67, { 0.48, 0.51, 0.62 } )   -- the passive lines end at 88, clear of the panel's divider (~96)
			HTxt( info.passive[ 1 ], 724, 54, 70, { 0.50, 0.78, 0.96 } )
			HTxt( info.passive[ 2 ], 724, 72, 88, { 0.50, 0.78, 0.96 } )
		end
		return
	end

end

local PreLoadFunc = function ( self, controller )
	-- Set scoreboard UI models (BO6 pattern)
	if CoD.ScoreboardUtility and CoD.ScoreboardUtility.SetScoreboardUIModels then
		CoD.ScoreboardUtility.SetScoreboardUIModels( controller )
	end
end

local PostLoadFunc = function ( self, controller )
	-- Subscribe to scoreboard open/close events
	self:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "UIVisibilityBit." .. Enum.UIVisibilityBit.BIT_SCOREBOARD_OPEN ), function ( model )
		local isOpen = Engine.GetModelValue( model )
		self.m_inputDisabled = not isOpen
	end )
end

CoD.AetheriumScoreboard.new = function ( menu, controller )
	local self = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( self )

	if PreLoadFunc then
		PreLoadFunc( self, controller )
	end

	self:setUseStencil( false )
	self:setClass( CoD.AetheriumScoreboard )
	self.id = "AetheriumScoreboard"
	self.soundSet = "default"
	self:setLeftRight( true, false, 0, 1280 )
	self:setTopBottom( true, false, 0, 720 )
	self:makeFocusable()
	self.onlyChildrenFocusable = true
	self.anyChildUsesUpdateState = true

	-- ========================================
	-- BACKGROUND LAYERS
	-- ========================================

	-- Main background overlay
	self.bg_overlay_1 = LUI.UIImage.new()
	self.bg_overlay_1:setLeftRight( true, false, 1, 1281 )
	self.bg_overlay_1:setTopBottom( true, false, 0, 720 )
	self.bg_overlay_1:setImage( RegisterImage( "i_mtl_image_67c0e1be4519503c" ) )
	self.bg_overlay_1:setRGB( 1, 1, 1 )
	self:addElement( self.bg_overlay_1 )

	-- Background particles
	self.bg_particles = LUI.UIImage.new()
	self.bg_particles:setLeftRight(true, false, 1, 1281)
	self.bg_particles:setTopBottom(true, false, 0, 720)
	self.bg_particles:setImage( RegisterImage( "i_mtl_image_2a0561747aef24aa" ) )
	self.bg_particles:setRGB( 1, 1, 1 )
	self:addElement( self.bg_particles )

	-- Secondary overlay
	self.bg_overlay_2 = LUI.UIImage.new()
	self.bg_overlay_2:setLeftRight(true, false, 1, 1281)
	self.bg_overlay_2:setTopBottom(true, false, 0, 720)
	self.bg_overlay_2:setImage( RegisterImage( "i_mtl_image_40d71e2f7898114c" ) )
	self.bg_overlay_2:setRGB( 1, 1, 1 )
	self:addElement( self.bg_overlay_2 )

	-- QUEST BAND — REMOVED (user 2026-09-01: "the top of the scoreboard menu is
	-- not needed for us. That's like easter egg and parts that this map doesn't
	-- have"). Correct: it drew a Power icon, three SHIELD PARTS slots, five
	-- EASTER EGG ITEMS slots and three WONDER WEAPON slots, all on the same
	-- placeholder image, for three systems this map has none of.
	--
	-- IT WAS ALREADY setAlpha(0) IN BOTH STATE CLIPS, and it is being DELETED
	-- anyway rather than left to the alpha. A guard nobody has watched fire is
	-- not a guard: nothing in this repo has ever confirmed that alpha on this
	-- container actually cascades to its ~20 children, and "it should" is the
	-- reasoning that has already cost this map two bugs. Deleting is correct in
	-- BOTH worlds — a no-op if the alpha worked, the fix if it did not — and it
	-- takes ~20 elements out of the pool either way.
	--
	-- Removed the way the compass was (AetheriumHud.lua): instantiation
	-- commented, require dropped since it was function-local here. The two
	-- `if self.questWidget then ... setAlpha(0)` sites in the state clips below
	-- are left in place — with the field never assigned they are no-ops, and
	-- keeping them makes this a four-line uncomment to bring back.
	--

	-- THIS FREES y0..182 ACROSS THE FULL WIDTH. The upgrades panel above already
	-- assumed that band was free (it is why the header sits at y=96); it now is
	-- free by construction rather than by an unverified alpha.


	-- ========================================
	-- PLAYER ROW BACKGROUNDS
	-- ========================================

	-- Player 4 outline
	self.player_4_outline = LUI.UIImage.new()
	self.player_4_outline:setLeftRight(true, false, 124, 1158)
	self.player_4_outline:setTopBottom(true, false, 526, 558)
	self.player_4_outline:setImage( RegisterImage( "i_mtl_image_6d18dfae10338ee0" ) )
	self.player_4_outline:setRGB( 1, 1, 1 )
	self:addElement( self.player_4_outline )

	-- Player 4 outline background
	self.player_4_outline_bg = LUI.UIImage.new()
    self.player_4_outline_bg:setLeftRight(true, false, 124, 1157)
    self.player_4_outline_bg:setTopBottom(true, false, 526, 557)
	self.player_4_outline_bg:setImage( RegisterImage( "i_mtl_image_67118f82e09c58d9_light" ) )
	self.player_4_outline_bg:setRGB( 1, 1, 1 )
	self:addElement( self.player_4_outline_bg )

	-- Player 3 outline
	self.player_3_outline = LUI.UIImage.new()
	self.player_3_outline:setLeftRight( true, false, 124, 1158 )
	self.player_3_outline:setTopBottom( true, false, 494, 526 )
	self.player_3_outline:setImage( RegisterImage( "i_mtl_image_6d18dfae10338ee0" ) )
	self.player_3_outline:setRGB( 1, 1, 1 )
	self:addElement( self.player_3_outline )

	-- Player 3 outline background
	self.player_3_outline_bg = LUI.UIImage.new()
    self.player_3_outline_bg:setLeftRight(true, false, 124, 1157)
    self.player_3_outline_bg:setTopBottom(true, false, 493, 526)
	self.player_3_outline_bg:setImage( RegisterImage( "i_mtl_image_67118f82e09c58d9_light" ) )
	self.player_3_outline_bg:setRGB( 1, 1, 1 )
	self:addElement( self.player_3_outline_bg )

	-- Player 2 outline
	self.player_2_outline = LUI.UIImage.new()
	self.player_2_outline:setLeftRight( true, false, 124, 1158 )
	self.player_2_outline:setTopBottom( true, false, 462, 494 )
	self.player_2_outline:setImage( RegisterImage( "i_mtl_image_6d18dfae10338ee0" ) )
	self.player_2_outline:setRGB( 1, 1, 1 )
	self:addElement( self.player_2_outline )

	-- Player 2 outline background
	self.player_2_outline_bg = LUI.UIImage.new()
    self.player_2_outline_bg:setLeftRight(true, false, 124, 1157)
    self.player_2_outline_bg:setTopBottom(true, false, 462, 493)
	self.player_2_outline_bg:setImage( RegisterImage( "i_mtl_image_67118f82e09c58d9_light" ) )
	self.player_2_outline_bg:setRGB( 1, 1, 1 )
	self:addElement( self.player_2_outline_bg )

	-- Player 1 outline
	self.player_1_outline = LUI.UIImage.new()
	self.player_1_outline:setLeftRight( true, false, 124, 1158 )
	self.player_1_outline:setTopBottom( true, false, 430, 462 )
	self.player_1_outline:setImage( RegisterImage( "i_mtl_image_6d18dfae10338ee0" ) )
	self.player_1_outline:setRGB( 1, 1, 1 )
	self:addElement( self.player_1_outline )

	-- Player 1 outline background
	self.player_1_outline_bg = LUI.UIImage.new()
    self.player_1_outline_bg:setLeftRight(true, false, 124, 1157)
    self.player_1_outline_bg:setTopBottom(true, false, 431, 462)
	self.player_1_outline_bg:setImage( RegisterImage( "i_mtl_image_67118f82e09c58d9_light" ) )
	self.player_1_outline_bg:setRGB( 1, 1, 1 )
	self:addElement( self.player_1_outline_bg )

	-- Player hover element (currently not visible - can be enabled for focused player)
	self.player_hover_element = LUI.UIImage.new()
    self.player_hover_element:setLeftRight(true, false, 124, 1156)
    self.player_hover_element:setTopBottom(true, false, 430, 461)
	self.player_hover_element:setImage( RegisterImage( "i_mtl_image_31890d5179c65d58" ) )
	self.player_hover_element:setRGB( 1, 1, 1 )
	self.player_hover_element:setAlpha( 0 ) -- Hidden by default
	self:addElement( self.player_hover_element )

	-- ========================================
	-- BOTTOM INFO (Points & Salvage)
	-- ========================================

	-- Points icon
	self.points_icon = LUI.UIImage.new()
    self.points_icon:setLeftRight(true, false, 537, 556)
    self.points_icon:setTopBottom(true, false, 577, 597)
	self.points_icon:setImage( RegisterImage( "i_tod_h2_points" ) )
	self.points_icon:setRGB( 1, 1, 1 )
	self:addElement( self.points_icon )

	-- Points label
	self.points_label = LUI.UIText.new()
	self.points_label:setLeftRight(true, false, 556, 649)
	self.points_label:setTopBottom(true, false, 586, 594)
	self.points_label:setText( Engine.Localize( "Points" ) )
	self.points_label:setTTF( "fonts/tod_tower1.ttf" )
	self.points_label:setRGB( 0.941, 0.941, 0.941 )
	self.points_label:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.points_label )

	-- Points value (dynamic - subscribed to player score model)
	self.points_value = LUI.UIText.new()
	self.points_value:setLeftRight(true, false, 503, 650)
	self.points_value:setTopBottom(true, false, 600, 625)
	self.points_value:setText( Engine.Localize( "0" ) )
	self.points_value:setTTF( "fonts/tod_tower1.ttf" )
	self.points_value:setRGB(0.996078431372549, 0.9921568627450981, 0.4980392156862745)
	self.points_value:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
	-- Subscribe to local player score
	self.points_value:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "PlayerList." .. Engine.GetClientNum( controller ) .. ".playerScore" ), function ( model )
		local score = Engine.GetModelValue( model )
		if score then
			self.points_value:setText( Engine.Localize( score ) )
		end
	end )
	if not USE_SCOREBOARD_V2 then   -- V2 adds it after its chrome (below), or the POINTS capsule paints over it
		self:addElement( self.points_value )
	end

	-- Salvage icon
	self.salvage_icon = LUI.UIImage.new()
	self.salvage_icon:setLeftRight(true, false, 701, 720)
	self.salvage_icon:setTopBottom(true, false, 576, 596)
	self.salvage_icon:setImage( RegisterImage( "i_mtl_ui_icons_zombie_squad_info_salvage" ) )
	self.salvage_icon:setRGB( 1, 1, 1 )
	self:addElement( self.salvage_icon )

	-- Salvage label
	self.salvage_label = LUI.UIText.new()
	self.salvage_label:setLeftRight(true, false, 721, 814)
	self.salvage_label:setTopBottom(true, false, 585, 593)
	self.salvage_label:setText( Engine.Localize( "Salvage" ) )
	self.salvage_label:setTTF( "fonts/tod_tower1.ttf" )
	self.salvage_label:setRGB( 0.941, 0.941, 0.941 )
	self.salvage_label:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.salvage_label )

	-- Salvage value (dynamic - would need custom clientfield for salvage system)
	self.salvage_value = LUI.UIText.new()
	self.salvage_value:setLeftRight(true, false, 667, 814)
	self.salvage_value:setTopBottom(true, false, 600, 625)
	self.salvage_value:setText( Engine.Localize( "0" ) )
	self.salvage_value:setTTF( "fonts/tod_tower1.ttf" )
	self.salvage_value:setRGB( 0.941, 0.941, 0.941 )
	self.salvage_value:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
	-- TODO: Subscribe to salvage model when implemented
	self:addElement( self.salvage_value )

	-- ========================================
	-- TOP LEFT MAP INFO
	-- ========================================

	-- Map info background
	self.map_info_bg = LUI.UIImage.new()
    self.map_info_bg:setLeftRight(true, false, 15, 323)
    self.map_info_bg:setTopBottom(true, false, 48, 86)
	self.map_info_bg:setImage( RegisterImage( "i_mtl_image_6f2d9c8089a2153e" ) )
	self.map_info_bg:setRGB( 1, 1, 1 )
	self:addElement( self.map_info_bg )

	-- Game mode text
	self.game_mode_text = LUI.UIText.new()
	self.game_mode_text:setLeftRight(true, false, 39, 311)
	self.game_mode_text:setTopBottom(true, false, 38, 57)
	self.game_mode_text:setText( Engine.Localize( "ROUNDBASED ZOMBIES" ) )
	self.game_mode_text:setTTF( "fonts/tod_tower1.ttf" )
	self.game_mode_text:setRGB( 0.941, 0.941, 0.941 )
	self.game_mode_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.game_mode_text )

	-- Map name (dynamic from CoD.UsermapName)
	self.map_name_text = LUI.UIText.new()
	self.map_name_text:setLeftRight(true, false, 50, 241)
	self.map_name_text:setTopBottom(true, false, 20, 31)
	self.map_name_text:setText( Engine.Localize( CoD.UsermapName or "MAP_NAME" ) )
	self.map_name_text:setTTF( "fonts/tod_tower1.ttf" )
	self.map_name_text:setRGB( 0.941, 0.941, 0.941 )
	self.map_name_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.map_name_text )

	-- Round label
	self.round_label = LUI.UIText.new()
	self.round_label:setLeftRight(true, false, 158, 211)
	self.round_label:setTopBottom(true, false, 20, 31)
	self.round_label:setText( Engine.Localize( "ROUND" ) )
	self.round_label:setTTF( "fonts/tod_tower1.ttf" )
	self.round_label:setRGB( 0.941, 0.941, 0.941 )
	self.round_label:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.round_label )

	-- Round number (dynamic from round model)
	self.round_number = LUI.UIText.new()
	self.round_number:setLeftRight(true, false, 210, 263)
	self.round_number:setTopBottom(true, false, 20, 31)
	self.round_number:setText( Engine.Localize( "1" ) )
	self.round_number:setTTF( "fonts/tod_tower1.ttf" )
	self.round_number:setRGB( 0.941, 0.941, 0.941 )
	self.round_number:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	-- Subscribe to round number
	self.round_number:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "gameScore.roundsPlayed" ), function ( model )
		local roundsPlayed = Engine.GetModelValue( model )
		if roundsPlayed then
			-- BO3 counts rounds starting at 1, but display shows current round (roundsPlayed - 1)
			local currentRound = math.max( 1, roundsPlayed - 1 )
			self.round_number:setText( Engine.Localize( currentRound ) )
		end
	end )
	if not USE_SCOREBOARD_V2 then   -- V2 adds it after its chrome (below), or the ROUND box paints over it
		self:addElement( self.round_number )
	end

	-- [tod 2026-09-26] SCOREBOARD V2 CHROME (docs/181). Built once, alpha-toggled
	-- by the two clips like every other piece of chrome here. Added at this point
	-- so it paints UNDER the table texts and player rows created after it.
	if USE_SCOREBOARD_V2 then
		local function Chrome( name, l, r, t, b )
			local e = LUI.UIImage.new()
			e:setLeftRight( true, false, l, r )
			e:setTopBottom( true, false, t, b )
			e:setImage( RegisterImage( name ) )
			e:setAlpha( 0 )
			self:addElement( e )
			return e
		end
		self.sbBackdrop = Chrome( "i_tod_sb_backdrop", 0, 1280, 0, 720 )
		local l0, t0 = SBT( 0, 0 )
		local l1, t1 = SBT( 1536, 520 )
		self.sbPanelTop = Chrome( "i_tod_sb_panel_top", l0, l1, t0, t1 )
		-- our emblem over the panel's empty top-left notch (art x 40..170, y 0..150)
		local ex0, ey0 = SBT( 36, -16 )
		local ex1, ey1 = SBT( 176, 124 )
		self.sbEmblem = Chrome( "i_mtl_sat_ui_icon_gamemode_zm_standard", ex0, ex1, ey0, ey1 )
		local b0, u0 = SBB( 0, 0 )
		local b1, u1 = SBB( 1540, 280 )
		self.sbPanelBottom = Chrome( "i_tod_sb_panel_bottom", b0, b1, u0, u1 )
		self.sbPoints = Chrome( "i_tod_sb_points", 522, 758, 650, 701 )
		-- the round number into the top panel's ROUND box (art x 540..640, y 42..86)
		local nx0, ny0 = SBT( 540, 42 )
		local nx1, ny1 = SBT( 640, 86 )
		self.round_number:setLeftRight( true, false, nx0, nx1 )
		self.round_number:setTopBottom( true, false, ny0 + 4, ny1 - 4 )
		self.round_number:setRGB( 0.98, 0.11, 0.22 )   -- RT: the Fallen red (docs/181; synthwave was 1.00, 0.17, 0.82)
		self.round_number:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		-- the points value into the capsule's empty right two thirds (art x 170..470)
		self.points_value:setLeftRight( true, false, 522 + 170 * 0.4917, 522 + 466 * 0.4917 )
		self.points_value:setTopBottom( true, false, 662, 688 )
		self.points_value:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		-- RT 2026-10-05: the two live numbers go on AFTER the chrome (later children paint on top): added before it,
		-- the ROUND box and the POINTS capsule covered them and both read empty
		self:addElement( self.points_value )
		self:addElement( self.round_number )
	end

	-- ========================================
	-- SCOREBOARD HEADER
	-- ========================================

	-- Header background
	self.scoreboard_header = LUI.UIImage.new()
	self.scoreboard_header:setLeftRight( true, false, 124, 1158 )
	self.scoreboard_header:setTopBottom( true, false, 397, 430 )
	self.scoreboard_header:setImage( RegisterImage( "i_mtl_image_67118f82e09c58d9" ) )
	self.scoreboard_header:setRGB( 1, 1, 1 )
	self:addElement( self.scoreboard_header )

	-- Header Column: # (Player ID)
	self.header_id = LUI.UIText.new()
	self.header_id:setLeftRight( true, false, 152, 165 )
	self.header_id:setTopBottom( true, false, 407, 420 )
	self.header_id:setText( Engine.Localize( "#" ) )
	self.header_id:setTTF( "fonts/tod_tower1.ttf" )
	self.header_id:setRGB( 0.047, 0.776, 0.913 ) -- BO6 cyan
	self.header_id:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_id )

	-- Header Column: Level
	self.header_level = LUI.UIText.new()
    self.header_level:setLeftRight(true, false, 200, 243)
    self.header_level:setTopBottom(true, false, 409, 420)
	self.header_level:setText( Engine.Localize( "Level" ) )
	self.header_level:setTTF( "fonts/tod_tower1.ttf" )
	self.header_level:setRGB( 0.047, 0.776, 0.913 )
	self.header_level:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_level )

	-- Header Column: Name
	self.header_name = LUI.UIText.new()
    self.header_name:setLeftRight(true, false, 346, 382)
    self.header_name:setTopBottom(true, false, 409, 420)
	self.header_name:setText( Engine.Localize( "Name" ) )
	self.header_name:setTTF( "fonts/tod_tower1.ttf" )
	self.header_name:setRGB( 0.047, 0.776, 0.913 )
	self.header_name:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_name )

	-- Header Column: Total Points
	self.header_points = LUI.UIText.new()
	self.header_points:setLeftRight(true, false, 526, 672)
	self.header_points:setTopBottom(true, false, 409, 418)
	self.header_points:setText( Engine.Localize( "Total Points" ) )
	self.header_points:setTTF( "fonts/tod_tower1.ttf" )
	self.header_points:setRGB( 0.047, 0.776, 0.913 )
	self.header_points:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_points )

	-- Header Column: Eliminations
	self.header_kills = LUI.UIText.new()
	self.header_kills:setLeftRight(true, false, 661, 749)
	self.header_kills:setTopBottom(true, false, 409, 418)
	self.header_kills:setText( Engine.Localize( "Eliminations" ) )
	self.header_kills:setTTF( "fonts/tod_tower1.ttf" )
	self.header_kills:setRGB( 0.047, 0.776, 0.913 )
	self.header_kills:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_kills )

	-- Header Column: Critical Kills
	self.header_headshots = LUI.UIText.new()
    self.header_headshots:setLeftRight(true, false, 788, 885)
    self.header_headshots:setTopBottom(true, false, 409, 419)
	self.header_headshots:setText( Engine.Localize( "Critical Kills" ) )
	self.header_headshots:setTTF( "fonts/tod_tower1.ttf" )
	self.header_headshots:setRGB( 0.047, 0.776, 0.913 )
	self.header_headshots:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_headshots )

	-- Header Column: Downs
	self.header_downs = LUI.UIText.new()
    self.header_downs:setLeftRight(true, false, 934, 981)
    self.header_downs:setTopBottom(true, false, 409, 418)
	self.header_downs:setText( Engine.Localize( "Downs" ) )
	self.header_downs:setTTF( "fonts/tod_tower1.ttf" )
	self.header_downs:setRGB( 0.047, 0.776, 0.913 )
	self.header_downs:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_downs )

	-- Header Column: Revives
	self.header_revives = LUI.UIText.new()
    self.header_revives:setLeftRight(true, false, 1062, 1118)
    self.header_revives:setTopBottom(true, false, 409, 418)
	self.header_revives:setText( Engine.Localize( "Revives" ) )
	self.header_revives:setTTF( "fonts/tod_tower1.ttf" )
	self.header_revives:setRGB( 0.047, 0.776, 0.913 )
	self.header_revives:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self:addElement( self.header_revives )

	-- ========================================
	-- PLAYER DATA ROWS
	-- ========================================

	-- Create player data rows dynamically
	self.playerRows = {}
	
	local playerYPositions = { 430, 462, 494, 527 } -- Y positions for players 1-4
	
	-- Function to update a player's stats
	local function UpdatePlayerStats( playerIndex, clientNum )
		if not self.playerRows[playerIndex] then
			return
		end
		
		local playerRow = self.playerRows[playerIndex]
		
		if clientNum and clientNum >= 0 then
			-- Update kills
			local kills = Engine.GetScoreboardColumnForClient( clientNum, 1 )
			if playerRow.kills_text then
				playerRow.kills_text:setText( Engine.Localize( kills ) )
			end
			
			-- Update headshots
			local headshots = Engine.GetScoreboardColumnForClient( clientNum, 4 )
			if playerRow.headshots_text then
				playerRow.headshots_text:setText( Engine.Localize( headshots ) )
			end
			
			-- Update downs
			local downs = Engine.GetScoreboardColumnForClient( clientNum, 2 )
			if playerRow.downs_text then
				playerRow.downs_text:setText( Engine.Localize( downs ) )
			end
			
			-- Update revives
			local revives = Engine.GetScoreboardColumnForClient( clientNum, 3 )
			if playerRow.revives_text then
				playerRow.revives_text:setText( Engine.Localize( revives ) )
			end
		end
	end
	
	for playerIndex = 0, 3 do
		local yPos = playerYPositions[playerIndex + 1]
		local playerNum = playerIndex + 1
		
		-- Create player row container
		local playerRow = LUI.UIElement.new()
        CoD.TodUIOwnership.Attach( playerRow )
		playerRow:setLeftRight( true, false, 124, 1158 )
		playerRow:setTopBottom( true, false, yPos, yPos + 32 )
		if USE_SCOREBOARD_V2 then
			-- the bar spans the strip (art x 2..1538); rows stack from the top of
			-- the empty band (art y 122) in the Visible clip below
			local rl, ry = SBB( 2, 122 + playerIndex * ( SB_PROW_PITCH / SB_BS ) )
			local rr = SBB( 1538, 0 )
			playerRow:setLeftRight( true, false, rl, rr )
			playerRow:setTopBottom( true, false, ry, ry + SB_PROW_H )
			playerRow.sb_bar = LUI.UIImage.new()
			playerRow.sb_bar:setLeftRight( true, true, 0, 0 )
			playerRow.sb_bar:setTopBottom( true, true, 0, 0 )
			playerRow.sb_bar:setImage( RegisterImage( "i_tod_sb_player_row" ) )
			playerRow:addElement( playerRow.sb_bar )
		end
		
		-- Set the model for this player row (required for linkToElementModel to work)
		playerRow:subscribeToGlobalModel( controller, "PlayerList", tostring(playerIndex), function ( model )
			playerRow:setModel( model, controller )
		end )
		
		-- Player ID number
		playerRow.id_text = LUI.UIText.new()
		playerRow.id_text:setLeftRight( true, false, 28, 41 )
		playerRow.id_text:setTopBottom( true, false, 10, 23 )
		playerRow.id_text:setText( Engine.Localize( playerNum ) )
		playerRow.id_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.id_text:setRGB( 0.941, 0.941, 0.941 )
		playerRow.id_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
		if USE_SCOREBOARD_V2 then
			local function colBox( e, k, half, align )
				local c = SB_COL_AX[ k ] * SB_BS - 2 * SB_BS
				e:setLeftRight( true, false, c - half, c + half )
				e:setTopBottom( true, false, 7.5, 20.5 )
				e:setAlignment( align or Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
			end
			playerRow.sb_colBox = colBox
			colBox( playerRow.id_text, 1, 20 )
		end
		playerRow:addElement( playerRow.id_text )
		
		-- Prestige icon (placeholder - would need prestige system)
		playerRow.prestige_icon = LUI.UIImage.new()
		playerRow.prestige_icon:setLeftRight( true, false, 71, 95 )
		playerRow.prestige_icon:setTopBottom( true, false, 5, 28 )
		playerRow.prestige_icon:setImage( RegisterImage( "i_mtl_sat_ui_icon_rank_prestige_04" ) ) -- Placeholder
		playerRow.prestige_icon:setRGB( 1, 1, 1 )
		playerRow:addElement( playerRow.prestige_icon )
		playerRow.prestige_icon:setAlpha( 0 )   -- no leveling system on this map
		
		-- Level (placeholder - would need level system)
		playerRow.level_text = LUI.UIText.new()
		playerRow.level_text:setLeftRight( true, false, 76, 130 )
		playerRow.level_text:setTopBottom( true, false, 10, 23 )
		playerRow.level_text:setText( Engine.Localize( "1" ) )
		playerRow.level_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.level_text:setRGB( 0.941, 0.941, 0.941 )
		playerRow.level_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		playerRow:addElement( playerRow.level_text )
		playerRow.level_text:setAlpha( 0 )   -- no leveling system on this map
		
		-- Player Name (dynamic from PlayerList model)
		playerRow.name_text = LUI.UIText.new()
		playerRow.name_text:setLeftRight( true, false, 212, 380 )
		playerRow.name_text:setTopBottom( true, false, 10, 23 )
		playerRow.name_text:setText( Engine.Localize( "Player " .. playerNum ) )
		playerRow.name_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.name_text:setRGB( 0.941, 0.941, 0.941 )
		playerRow.name_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
		-- Subscribe to player name
		playerRow.name_text:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "PlayerList." .. playerIndex .. ".playerName" ), function ( model )
			local name = Engine.GetModelValue( model )
			if name then
				playerRow.name_text:setText( Engine.Localize( name ) )
			end
		end )
		if USE_SCOREBOARD_V2 then playerRow.sb_colBox( playerRow.name_text, 2, 110 ) end
		playerRow:addElement( playerRow.name_text )
		
		-- Total Points (dynamic from playerScore model)
		playerRow.points_text = LUI.UIText.new()
		playerRow.points_text:setLeftRight( true, false, 367, 503 )
		playerRow.points_text:setTopBottom( true, false, 10, 23 )
		playerRow.points_text:setText( Engine.Localize( "0" ) )
		playerRow.points_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.points_text:setRGB(0.996078431372549, 0.9921568627450981, 0.4980392156862745)
		playerRow.points_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		-- Subscribe to player score
		playerRow.points_text:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "PlayerList." .. playerIndex .. ".playerScore" ), function ( model )
			local score = Engine.GetModelValue( model )
			if score then
				playerRow.points_text:setText( Engine.Localize( score ) )
			end
		end )
		if USE_SCOREBOARD_V2 then playerRow.sb_colBox( playerRow.points_text, 3, 70 ) end
		playerRow:addElement( playerRow.points_text )
		
		-- Eliminations (dynamic via GetScoreboardColumnForClient)
		playerRow.kills_text = LUI.UIText.new()
		playerRow.kills_text:setLeftRight( true, false, 506, 627 )
		playerRow.kills_text:setTopBottom( true, false, 10, 23 )
		playerRow.kills_text:setText( Engine.Localize( "0" ) )
		playerRow.kills_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.kills_text:setRGB( 0.941, 0.941, 0.941 )
		playerRow.kills_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		if USE_SCOREBOARD_V2 then playerRow.sb_colBox( playerRow.kills_text, 4, 60 ) end
		playerRow:addElement( playerRow.kills_text )
		
		-- Critical Kills / Headshots (dynamic via GetScoreboardColumnForClient)
		playerRow.headshots_text = LUI.UIText.new()
		playerRow.headshots_text:setLeftRight( true, false, 641, 762 )
		playerRow.headshots_text:setTopBottom( true, false, 10, 23 )
		playerRow.headshots_text:setText( Engine.Localize( "0" ) )
		playerRow.headshots_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.headshots_text:setRGB( 0.941, 0.941, 0.941 )
		playerRow.headshots_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		if USE_SCOREBOARD_V2 then playerRow.sb_colBox( playerRow.headshots_text, 5, 60 ) end
		playerRow:addElement( playerRow.headshots_text )
		
		-- Downs (dynamic via GetScoreboardColumnForClient)
		playerRow.downs_text = LUI.UIText.new()
		playerRow.downs_text:setLeftRight( true, false, 769, 890 )
		playerRow.downs_text:setTopBottom( true, false, 10, 23 )
		playerRow.downs_text:setText( Engine.Localize( "0" ) )
		playerRow.downs_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.downs_text:setRGB( 0.941, 0.941, 0.941 )
		playerRow.downs_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		if USE_SCOREBOARD_V2 then playerRow.sb_colBox( playerRow.downs_text, 6, 60 ) end
		playerRow:addElement( playerRow.downs_text )
		
		-- Revives (dynamic via GetScoreboardColumnForClient)
		playerRow.revives_text = LUI.UIText.new()
		playerRow.revives_text:setLeftRight( true, false, 897, 1018 )
		playerRow.revives_text:setTopBottom( true, false, 10, 23 )
		playerRow.revives_text:setText( Engine.Localize( "0" ) )
		playerRow.revives_text:setTTF( "fonts/tod_tower1.ttf" )
		playerRow.revives_text:setRGB( 0.941, 0.941, 0.941 )
		playerRow.revives_text:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		if USE_SCOREBOARD_V2 then playerRow.sb_colBox( playerRow.revives_text, 7, 60 ) end
		playerRow:addElement( playerRow.revives_text )
		
		-- Store clientNum for this player and subscribe to updates
		playerRow.clientNum = nil
		playerRow:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "PlayerList." .. playerIndex .. ".clientNum" ), function ( model )
			local clientNum = Engine.GetModelValue( model )
			playerRow.clientNum = clientNum
			-- V2: YOUR row wears the red bar
			if playerRow.sb_bar and clientNum ~= nil then
				local mine = ( clientNum == Engine.GetClientNum( controller ) )
				playerRow.sb_bar:setImage( RegisterImage( mine and "i_tod_sb_player_row_local" or "i_tod_sb_player_row" ) )
			end
			UpdatePlayerStats( playerIndex, clientNum )
		end )
		
		-- Add player row to scoreboard
		self:addElement( playerRow )
		self.playerRows[playerIndex] = playerRow
	end
	
	-- Subscribe to global scoreboard update model to refresh all stats
	self:subscribeToModel( Engine.CreateModel( Engine.GetModelForController( controller ), "updateScoreboard" ), function ( model )
		for i = 0, 3 do
			if self.playerRows[i] and self.playerRows[i].clientNum then
				UpdatePlayerStats( i, self.playerRows[i].clientNum )
			end
		end
	end )

	-- ========================================
	-- VISIBILITY SYSTEM (Hidden by default, shown on TAB)
	-- ========================================
	
	-- Helper function to check if player exists
	local function IsPlayerActive( playerIndex )
		local playerModel = Engine.GetModel( Engine.GetModelForController( controller ), "PlayerList." .. playerIndex )
		if playerModel then
			local nameModel = Engine.GetModel( playerModel, "playerName" )
			if nameModel then
				local name = Engine.GetModelValue( nameModel )
				return name ~= nil and name ~= ""
			end
		end
		return false
	end
	
	self.clipsPerState = {
		DefaultState = {
			DefaultClip = function ()
				self:setupElementClipCounter( 0 )
				
				-- Hide all scoreboard elements
				self.bg_overlay_1:setAlpha( 0 )
				self.bg_particles:setAlpha( 0 )
				self.bg_overlay_2:setAlpha( 0 )
				if self.questWidget then
					self.questWidget:setAlpha(0)
				end
				
				self.player_4_outline:setAlpha( 0 )
				self.player_4_outline_bg:setAlpha( 0 )
				self.player_3_outline:setAlpha( 0 )
				self.player_3_outline_bg:setAlpha( 0 )
				self.player_2_outline:setAlpha( 0 )
				self.player_2_outline_bg:setAlpha( 0 )
				self.player_1_outline:setAlpha( 0 )
				self.player_1_outline_bg:setAlpha( 0 )
				self.player_hover_element:setAlpha( 0 )
				self.points_icon:setAlpha( 0 )
				self.points_label:setAlpha( 0 )
				self.points_value:setAlpha( 0 )
				self.salvage_icon:setAlpha( 0 )
				self.salvage_label:setAlpha( 0 )
				self.salvage_value:setAlpha( 0 )
				self.map_info_bg:setAlpha( 0 )
				self.game_mode_text:setAlpha( 0 )
				self.map_name_text:setAlpha( 0 )
				self.round_label:setAlpha( 0 )
				self.round_number:setAlpha( 0 )
				self.scoreboard_header:setAlpha( 0 )
				self.header_id:setAlpha( 0 )
				self.header_level:setAlpha( 0 )
				self.header_name:setAlpha( 0 )
				self.header_points:setAlpha( 0 )
				self.header_kills:setAlpha( 0 )
				self.header_headshots:setAlpha( 0 )
				self.header_downs:setAlpha( 0 )
				self.header_revives:setAlpha( 0 )
				
				-- Hide all player rows
				for i = 0, 3 do
					if self.playerRows[i] then
						self.playerRows[i]:setAlpha( 0 )
					end
				end
				if self.sbBackdrop then
					self.sbBackdrop:setAlpha( 0 )
					self.sbPanelTop:setAlpha( 0 )
					self.sbEmblem:setAlpha( 0 )
					self.sbPanelBottom:setAlpha( 0 )
					self.sbPoints:setAlpha( 0 )
				end

				-- [tod v15 item 13] and the owned-upgrades list. CLOSED, not just
				-- alpha'd: these are rebuilt from scratch on every open, so leaving
				-- them parented would grow the element pool once per scoreboard
				-- press for the whole match.
				if self.todUpgRows then
					for i = 1, #self.todUpgRows do
						if self.todUpgRows[ i ] then
							self.todUpgRows[ i ]:close()
						end
					end
					self.todUpgRows = {}
				end
			end
		},
		Visible = {
			DefaultClip = function ()
				self:setupElementClipCounter( 0 )
				
				-- Show all scoreboard elements
				self.bg_overlay_1:setAlpha( 1 )
				self.bg_particles:setAlpha( 1 )
				self.bg_overlay_2:setAlpha( 1 )
				if self.questWidget then
					self.questWidget:setAlpha(0)   -- no quest system on this map
				end
				
				-- Count active players
				local activePlayers = {}
				for i = 0, 3 do
					if IsPlayerActive( i ) then
						table.insert( activePlayers, i )
					end
				end
				local playerCount = #activePlayers
				
				-- Position players from bottom (fill slots 4, 3, 2, 1 based on count)
				local playerYPositions = { 430, 462, 494, 527 } -- Slots 1, 2, 3, 4
				local outlineElements = { self.player_1_outline, self.player_2_outline, self.player_3_outline, self.player_4_outline }
				local outlineBgElements = { self.player_1_outline_bg, self.player_2_outline_bg, self.player_3_outline_bg, self.player_4_outline_bg }
				
				-- Hide all outlines first
				for i = 1, 4 do
					outlineElements[i]:setAlpha( 0 )
					outlineBgElements[i]:setAlpha( 0 )
				end
				
				-- Show outlines for active slots (filling from bottom)
				for i = 1, playerCount do
					local slotIndex = 5 - i -- Start from slot 4 and go up (4, 3, 2, 1)
					outlineElements[slotIndex]:setAlpha( 1 )
					outlineBgElements[slotIndex]:setAlpha( 1 )
				end
				
				-- Position player rows to fill from bottom
				for i = 1, playerCount do
					local playerIndex = activePlayers[i]
					local slotIndex = 5 - i -- Slot position (4, 3, 2, 1)
					local yPos = playerYPositions[slotIndex]
					
					if self.playerRows[playerIndex] then
						self.playerRows[playerIndex]:setTopBottom( true, false, yPos, yPos + 32 )
						self.playerRows[playerIndex]:setAlpha( 1 )
					end
				end
				
				-- Hide inactive player rows
				for i = 0, 3 do
					local isActive = false
					for _, activeIdx in ipairs( activePlayers ) do
						if activeIdx == i then
							isActive = true
							break
						end
					end
					if not isActive and self.playerRows[i] then
						self.playerRows[i]:setAlpha( 0 )
					end
				end
				
				-- Position hover element on bottom-most active player
				if playerCount > 0 then
					local bottomSlot = 5 - 1 -- Slot 4
					local yPos = playerYPositions[bottomSlot]
					self.player_hover_element:setTopBottom( true, false, yPos, yPos + 32 )
					self.player_hover_element:setAlpha( 1 )
				else
					self.player_hover_element:setAlpha( 0 )
				end
				
				-- Position header directly above topmost active player
				if playerCount > 0 then
					local topSlot = 5 - playerCount -- Top-most slot being used
					local topPlayerY = playerYPositions[topSlot]
					local headerHeight = 33 -- Header is 33 pixels tall (430 - 397)
					local headerTop = topPlayerY - headerHeight
					local headerBottom = topPlayerY
					
					-- Reposition header
					if self.scoreboard_header then
						self.scoreboard_header:setTopBottom( true, false, headerTop, headerBottom )
					end
					
					-- Reposition all header text elements (they're offset from header position)
					local headerTextOffset = 10 -- Text starts 10px from header top
					local textY = headerTop + headerTextOffset
					
					if self.header_id then
						self.header_id:setTopBottom( true, false, textY, textY + 13 )
					end
					if self.header_level then
						self.header_level:setTopBottom( true, false, textY + 2, textY + 13 )
					end
					if self.header_name then
						self.header_name:setTopBottom( true, false, textY + 2, textY + 13 )
					end
					if self.header_points then
						self.header_points:setTopBottom( true, false, textY + 2, textY + 11 )
					end
					if self.header_kills then
						self.header_kills:setTopBottom( true, false, textY + 2, textY + 11 )
					end
					if self.header_headshots then
						self.header_headshots:setTopBottom( true, false, textY + 2, textY + 12 )
					end
					if self.header_downs then
						self.header_downs:setTopBottom( true, false, textY + 2, textY + 11 )
					end
					if self.header_revives then
						self.header_revives:setTopBottom( true, false, textY + 2, textY + 11 )
					end
				end
				
				self.points_icon:setAlpha( 1 )
				self.points_label:setAlpha( 1 )
				self.points_value:setAlpha( 1 )
				-- salvage disabled: no salvage economy on this map (audit 2026-08-19)
				self.salvage_icon:setAlpha( 0 )
				self.salvage_label:setAlpha( 0 )
				self.salvage_value:setAlpha( 0 )
				self.map_info_bg:setAlpha( 1 )
				self.game_mode_text:setAlpha( 1 )
				self.map_name_text:setAlpha( 1 )
				self.round_label:setAlpha( 1 )
				self.round_number:setAlpha( 1 )
				self.scoreboard_header:setAlpha( 1 )
				self.header_id:setAlpha( 1 )
				self.header_level:setAlpha( 0 )   -- no leveling system on this map
				self.header_name:setAlpha( 1 )
				self.header_points:setAlpha( 1 )
				self.header_kills:setAlpha( 1 )
				self.header_headshots:setAlpha( 1 )
				self.header_downs:setAlpha( 1 )
				self.header_revives:setAlpha( 1 )

				if USE_SCOREBOARD_V2 then
					-- The V2 chrome replaces the kit's: every old plate, outline,
					-- header text and the map-info block goes dark, the four new
					-- pieces come up, and the player rows stack from the TOP of
					-- the baked strip (the kit filled its slots from the bottom).
					for i = 1, 4 do
						outlineElements[i]:setAlpha( 0 )
						outlineBgElements[i]:setAlpha( 0 )
					end
					self.bg_overlay_1:setAlpha( 0 )
					self.bg_particles:setAlpha( 0 )
					self.bg_overlay_2:setAlpha( 0 )
					self.player_hover_element:setAlpha( 0 )
					self.points_icon:setAlpha( 0 )
					self.points_label:setAlpha( 0 )
					self.map_info_bg:setAlpha( 0 )
					self.game_mode_text:setAlpha( 0 )
					self.map_name_text:setAlpha( 0 )
					self.round_label:setAlpha( 0 )
					self.scoreboard_header:setAlpha( 0 )
					self.header_id:setAlpha( 0 )
					self.header_name:setAlpha( 0 )
					self.header_points:setAlpha( 0 )
					self.header_kills:setAlpha( 0 )
					self.header_headshots:setAlpha( 0 )
					self.header_downs:setAlpha( 0 )
					self.header_revives:setAlpha( 0 )
					self.sbBackdrop:setAlpha( 1 )
					self.sbPanelTop:setAlpha( 1 )
					self.sbEmblem:setAlpha( 1 )
					self.sbPanelBottom:setAlpha( 1 )
					self.sbPoints:setAlpha( 1 )
					for i = 1, playerCount do
						local playerIndex = activePlayers[i]
						local _, ry = SBB( 0, 122 + ( i - 1 ) * ( SB_PROW_PITCH / SB_BS ) )
						if self.playerRows[playerIndex] then
							self.playerRows[playerIndex]:setTopBottom( true, false, ry, ry + SB_PROW_H )
						end
					end
				end

				-- [tod v15 item 13] YOUR UPGRADES, ON THE SCOREBOARD.
				-- User: "Can we put the upgrade menu in the scoreboard as well so
				-- players can move and read?" Built here in the Visible clip, which
				-- re-runs on every open, so the list is current without a poll.
				TodBuildUpgradeList( self )
			end
		}
	}
	
	-- State conditions: Check if scoreboard should be visible
	self:mergeStateConditions( {
		{
			stateName = "Visible",
			condition = function ( menu, element, event )
				return Engine.IsVisibilityBitSet( controller, Enum.UIVisibilityBit.BIT_SCOREBOARD_OPEN )
			end
		}
	} )
	
	-- Subscribe to scoreboard open/close model
	self:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "UIVisibilityBit." .. Enum.UIVisibilityBit.BIT_SCOREBOARD_OPEN ), function ( model )
		menu:updateElementState( self, {
			name = "model_validation",
			menu = menu,
			modelValue = Engine.GetModelValue( model ),
			modelName = "UIVisibilityBit." .. Enum.UIVisibilityBit.BIT_SCOREBOARD_OPEN
		} )
	end )

	if PostLoadFunc then
		PostLoadFunc( self, controller )
	end


	-- =========================================================================
	return self
end

return CoD.AetheriumScoreboard
