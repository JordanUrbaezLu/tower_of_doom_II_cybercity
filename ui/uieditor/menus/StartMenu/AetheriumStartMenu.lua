-- Aetherium Pause Menu (Custom Design)

require("ui.uieditor.widgets.StartMenu.AetheriumMenuButton")
require("ui.uieditor.widgets.StartMenu.AetheriumSmallButton")
-- [tod v17.24] the ONE writer for a bind name inside the pale keycap, shared
-- with tod_upgrade.lua and tod_class_select.lua. See its header.
--
-- [tod v17.30] AND IT IS FAIL-SAFED, because this file is THE PAUSE MENU. A
-- require that throws — the rawfile missing from the .ff, a Lua error inside the
-- widget or inside TodGlyphRow beneath it — aborts this entire file, silently,
-- and a player who cannot open the pause menu cannot leave the match. Risking
-- that on an unguarded require, for the sake of a key name drawn on a legend, is
-- not a trade worth making.
--
-- So: pcall the require, and route the call site through TodKeycapMake, which
-- degrades to the plain LUI text this menu already builds. THE STUB IS
-- DELIBERATELY LOCAL AND TWINNED across the three menus that use the widget — a
-- fail-safe that lives inside the thing it guards against is not a fail-safe,
-- and that is the one case where a twin beats a shared file.
pcall(require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodKeycap")

-- [tod v18.32] IS THIS EXPANSION A BUTTON PICTURE? Twin of the test in the two
-- card menus and of CoD.TodKeycap.IsPadGlyph, which is the canonical copy and
-- carries the argument. It has to be twinned HERE for the same reason the stub
-- below is: a guard that lives inside the widget cannot cover the widget being
-- absent, and with the widget absent the stub's own fallback would happily set
-- the engine's LT / RT / A icon as text inside a pale keycap -- the exact
-- failure in the user's 2026-09-08 screenshot.
local function TodPadGlyph(tok)
	local s = Engine.Localize(tok) or ""
	s = s:gsub("%^%d", "")
	if s == "" then
		return false
	end
	-- [tod v18.48] HIGH BYTES ONLY. v18.47 also matched b < 32 and every
	-- keyboard player was drawn as a controller -- something in the KEYBOARD
	-- expansion carries a low control byte. And this is no longer a DEVICE
	-- test: it decides only whether a string may be drawn inside a keycap, and
	-- is consulted after the typeface has already failed to draw it.
	for i = 1, #s do
		if string.byte(s, i) > 126 then
			return true
		end
	end
	return false
end
local function TodKeycapMake(owner, text)
	if CoD.TodKeycap then
		return CoD.TodKeycap.make(owner, text)
	end
	return {
		hide = function ()
			if text then
				text:setAlpha(0)
			end
		end,
		paint = function (capL, capT, capW, capH, token, alpha)
			if not text then
				return ""
			end
			-- never a button picture inside a keycap
			if TodPadGlyph(token) then
				text:setAlpha(0)
				return nil
			end
			local cy = capT + capH * 0.435
			text:setLeftRight(true, false, capL + 6, capL + capW - 6)
			text:setTopBottom(true, false, cy - 8, cy + 8)
			text:setScale(1)
			text:setText(Engine.Localize(token))
			text:setAlpha((alpha == nil) and 1 or alpha)
			return ""
		end,
	}
end

-- Configuration
local ShowSignatures = true  -- Set to false to hide signature images

-- [tod 2026-09-26] PAUSE MENU V2 — the red "Fallen" menu (docs/180; user: "implement
-- this in place of the current pause menu ... the new reference that we must follow
-- exactly"). 60 baked pieces (i_tod_pm_*), every changing word/number/pip drawn here
-- in the map TTF. FALSE = the old Aetherium layout below, byte-for-byte, which is kept
-- whole as the fallback. Geometry is the target image x 0.7656 (1672 -> 1280) read
-- against the delivered art; the table in docs/180 "Canvas layout" is the record.
local USE_PAUSE_V2 = true

-- The TTF every live string in this menu uses.
local TOD_TTF = "fonts/tod_tower1.ttf"

-- THE ROW CAP (user 2026-09-26: "a class can only have 12 upgrades max. That
-- needs to be defined"). The panel draws 2 columns x 6 rows at ONE fixed size,
-- never a compact preset, never "+N MORE". tools/lint_tod_assets.js reads this
-- constant and FAILS THE BUILD when any live class's reachable domain set (plus
-- the CLASS TIER row) exceeds it.
-- 10 since 2026-09-28 (user: "cleanly fit 10 upgrades max ... adjust the spacing"): every class
-- holds 9 cards + the CLASS TIER row = 10, drawn 2 x 5 with taller rows and more air.
local TOD_PAUSE_ROWS_CAP = 10
local TOD_PAUSE_ROWS_COL = 5

-- V2 panel frames (docs/180 "Canvas layout", 2026-09-26 second pass: the user
-- wanted the left side bigger, so the left panel takes the screen height and
-- the right panel narrows 3.6% to make room). LX/LY/LS map the left panel's
-- 1468x1196 art to the canvas; RX/RY/RS the right panel's 896x1208 art.
local LX, LY, LS = 20, 40, 0.5436     -- left panel: 20..818 x 40..690
local RX, RY, RS = 830, 62, 0.482     -- right panel: 830..1262 x 62..644
local function LArt( ax, ay ) return LX + ax * LS, LY + ay * LS end

-- THE CLASS AND ITS PASSIVE (2026-09-27, user: "somewhere in the pause screen we need
-- to show the class name and passive ability"). Keyed by _tod_classes class_id (the
-- registration order: 1 Necromancer, 2 Archer, 3 Breacher, 4 Warrior), read
-- from CoD.TodClass (tod_upgrade.lua; the server pushes it with every pause-list
-- refresh). LOCKSTEP the passives in _tod_class_cards.gsc / _tod_upgrades.gsc /
-- _tod_necro_skull.gsc: a passive changed there is changed here.
-- THE CLASS HEADER lives in tod_upgrade.lua since 2026-09-28 (CoD.TodClassInfo / CoD.TodClassTierLines),
-- shared with the scoreboard; read at draw time.
-- THE AI COMPANION ROW: the first row of every list (2026-09-28), LIVE since 2026-09-29 (user:
-- "there is an upgrade in the pause menu. That shows AI companion. I don't think it's wired up
-- yet, to the actual companion that the player has ... Make sure the upgrades are there as
-- well"). It draws the companion you hold: its portrait in the well, its name, its three Black
-- Market items as the HUD's rarity chips (right, where the pips go), the item names (the blue
-- line) and its state (the grey line: active + health, destroyed + seconds to rebuild, on its
-- way). What it says comes from CoD.TodCompanionDescribe (TodSpinReel.lua, the one source for
-- the names, portraits, items and rarity colours; the server's tod_ptn_items + tod_ptn_state).
-- Nothing held, or the HUD not built yet = the fields below. Never dealt, no level.
-- .view and .tone ride this table ON PURPOSE: the list builder is near Lua 5.1's 60-upvalue
-- cap, and a new local here would be one more upvalue for it. LOCKSTEP AetheriumScoreboard.lua.
local TOD_PARTNER_ROW = { name = "AI COMPANION", eff = "NONE YET", act = "the Black Market dealer gives you one free", icon = "i_tod_pm_ico_companion",
	tone = { good = { 0.45, 0.85, 0.65 }, hot = { 0.98, 0.64, 0.24 }, idle = { 0.48, 0.51, 0.62 } } }
TOD_PARTNER_ROW.view = function()
	if CoD.TodCompanionDescribe then
		local ok, v = pcall( CoD.TodCompanionDescribe )
		if ok and type( v ) == "table" then return v end
	end
	return { held = false, name = TOD_PARTNER_ROW.name, items = TOD_PARTNER_ROW.eff, status = TOD_PARTNER_ROW.act, tone = "idle", slots = {} }
end

local function RArt( ax, ay ) return RX + ax * RS, RY + ay * RS end

-- Icon tints (the D and F glyphs are delivered WHITE so one file serves every state).
-- [RT 2026-10-05] THE RED RETURN (user: "id rather the red theme please"): PM_RED is the Fallen red
-- again (docs/180), for the held-row icons AND the focused button glyph - focus is red in the Fallen theme.
-- The art's theme switch is tools/artgen/synthwave.py THEME; r3_synthwave_system.py --check pins these lines
-- (CODE_TINTS) to it.
local PM_RED    = { 0.95, 0.13, 0.23 }
local PM_VIOLET = { 0.71, 0.36, 1.00 }
local PM_IDLE   = { 0.59, 0.64, 0.78 }   -- the target's grey-blue idle button glyph

-- Domain id -> row icon (docs/180). Ids are _tod_upgrade_ui::domain_id; an id
-- missing here draws the generic icon, never a missing image. FULL LITERAL NAMES on
-- purpose: lint_tod_assets GATE A can only prove a name is zoned when it can read it.
local PM_ICON = {
	[2] = "i_tod_pm_ico_dr",
	[3] = "i_tod_pm_ico_bounty",
	[4] = "i_tod_pm_ico_luck",
	[45] = "i_tod_pm_ico_riotshield",
	[24] = "i_tod_pm_ico_tier",
	[38] = "i_tod_pm_ico_summonpower",
	[39] = "i_tod_pm_ico_soulbeam",
	[59] = "i_tod_pm_ico_soulbomb",
	[41] = "i_tod_pm_ico_grapple",
	[57] = "i_tod_pm_ico_retriever",
	[58] = "i_tod_pm_ico_pellets",
	[60] = "i_tod_pm_ico_c4",
	[61] = "i_tod_pm_ico_cluster",
	[62] = "i_tod_pm_ico_bash",
	[63] = "i_tod_pm_ico_gravsmash",
	-- PK05 (2026-10-04, tools/artgen/packs/pk05_glyph_icons.py): the 13 live cards that drew the generic
	-- hexagon. LOCKSTEP AetheriumScoreboard.lua SB_ICON (same ids, same names).
	[29] = "i_tod_pm_ico_sprint",          -- Archer
	[6] = "i_tod_pm_ico_deadeye",
	[35] = "i_tod_pm_ico_quickdraw",
	[26] = "i_tod_pm_ico_piercing",
	[25] = "i_tod_pm_ico_adrenaline",      -- Breacher
	[36] = "i_tod_pm_ico_fusion",
	[37] = "i_tod_pm_ico_vitality",        -- Warrior
	[7] = "i_tod_pm_ico_armsspecialist",
	[48] = "i_tod_pm_ico_cleave",
	[12] = "i_tod_pm_ico_demonslayer",
	[5] = "i_tod_pm_ico_reapersreach",     -- Necromancer
	[19] = "i_tod_pm_ico_summonermaster",
	[9] = "i_tod_pm_ico_cloak",
}
local function PmIcon( id )
	return PM_ICON[ id ] or "i_tod_pm_ico_generic"
end

-- ONE owner of the page swap (main list <-> settings list), for both layouts. It
-- was three hand-copied bodies (Game Settings, the fourth icon button, Back). In
-- V2 the icon row STAYS on the settings page — it opens Graphics / Audio / Controls,
-- which is why the settings list drops those three entries (docs/180 difference 4).
--
-- [tod 2026-09-26, the user's first V2 test: "the setting button on right ...
-- changes the selectable setting and you cant change back unless you close and
-- reopen"] V2 NO LONGER STACKS TWO LISTS ON ONE RECT. The old page swap left the
-- main list at alpha 0 UNDER the settings list, still focusable and still taking
-- mouse hover/clicks, so a mouse on the settings page kept focusing invisible
-- buttons and BACK could never be pressed. V2 has ONE list (ButtonList) whose
-- data source answers with the settings entries while TodV2Settings[controller]
-- holds; the swap is updateDataSource(), the same call ToggleThirdPerson relabels
-- through. OptionsList still exists in V2 but is never shown and never focusable.
local TodV2Settings = {}
-- The settings entries' BUILDER FUNCTION (assigned below the main list). NEVER call
-- DataSources.AetheriumOptionsButtons( controller ): the engine's ListHelper_SetupDataSource
-- returns a datasource TABLE, so that call is "attempt to call a table" = the user's
-- UI Error 95573 on the gear icon / Game Settings (2026-09-26; the harness mocks
-- returned the function, which is why they passed).
local TodOptionsBuild
local function TodSetPage( menu, controller, settings )
	menu.ButtonList:completeAnimation()
	menu.SmallButtonList:completeAnimation()
	menu.OptionsList:completeAnimation()
	menu.OptionsHeaderText:completeAnimation()
	menu.PauseMenuText:completeAnimation()
	menu.TodOptionsOpen = settings
	if USE_PAUSE_V2 then
		TodV2Settings[ controller ] = settings and true or nil
		menu.ButtonList:updateDataSource()
		if menu.TodPmTitle then
			menu.TodPmTitle:setImage( RegisterImage( settings and "i_tod_pm_title_settings" or "i_tod_pm_title_pause" ) )
		end
		menu.ButtonList:processEvent( { name = "gain_focus", controller = controller } )
		return
	else
		menu.ButtonList:setAlpha( settings and 0 or 1 )
		menu.SmallButtonList:setAlpha( settings and 0 or 1 )
		menu.PauseMenuText:setAlpha( settings and 0 or 1 )
		menu.OptionsList:setAlpha( settings and 1 or 0 )
		menu.OptionsHeaderText:setAlpha( settings and 1 or 0 )
	end
	local target = settings and menu.OptionsList or menu.ButtonList
	target:processEvent( { name = "gain_focus", controller = controller } )
end

-- V2 list widgets. Defined in this file on purpose: a new widget FILE is a new zoned
-- rawfile, and a require that fails aborts the pause menu (see TodKeycap above).
local function PmCloseChildren( element )
	local child = element:getFirstChild()
	while child do
		local nextChild = child:getNextSibling()
		child:close()
		child = nextChild
	end
end

-- The menu button: 386 x 42 (art 1024 x 112). Frame + red focus twin, the glyph in
-- the icon cell (x 0..68), the live label from x 75. Chevron is baked into both frames.
CoD.TodPmButton = InheritFrom( LUI.UIElement )
CoD.TodPmButton.new = function ( menu, controller )
	local self = LUI.UIElement.new()
	self:setClass( CoD.TodPmButton )
	self.id = "TodPmButton"
	self.soundSet = "default"
	self:setLeftRight( true, false, 0, 1024 * 0.3633 )   -- 372 x 40.7 (1024 x 112 art at RS-scaled width)
	self:setTopBottom( true, false, 0, 112 * 0.3633 )
	self:makeFocusable()
	self:setHandleMouse( true )
	self.anyChildUsesUpdateState = true

	self.Frame = LUI.UIImage.new()
	self.Frame:setLeftRight( true, true, 0, 0 )
	self.Frame:setTopBottom( true, true, 0, 0 )
	self.Frame:setImage( RegisterImage( "i_tod_pm_btn" ) )
	self:addElement( self.Frame )

	self.FrameFocus = LUI.UIImage.new()
	self.FrameFocus:setLeftRight( true, true, 0, 0 )
	self.FrameFocus:setTopBottom( true, true, 0, 0 )
	self.FrameFocus:setImage( RegisterImage( "i_tod_pm_btn_focus" ) )
	self.FrameFocus:setAlpha( 0 )
	self:addElement( self.FrameFocus )

	self.Glyph = LUI.UIImage.new()
	self.Glyph:setLeftRight( true, false, 22.7, 42.7 )   -- icon cell centre = art x 90 -> 32.7
	self.Glyph:setTopBottom( true, false, 10.3, 30.3 )
	self.Glyph:setRGB( PM_IDLE[ 1 ], PM_IDLE[ 2 ], PM_IDLE[ 3 ] )
	self.Glyph:setAlpha( 0 )
	self.Glyph:linkToElementModel( self, "glyph", true, function ( model )
		local g = Engine.GetModelValue( model )
		if g and g ~= "" then
			self.Glyph:setImage( RegisterImage( g ) )
			self.Glyph:setAlpha( 1 )
		else
			self.Glyph:setAlpha( 0 )
		end
	end )
	self:addElement( self.Glyph )

	self.ButtonText = LUI.UIText.new()
	self.ButtonText:setLeftRight( true, false, 72, 338 )
	self.ButtonText:setTopBottom( true, false, 13, 27.7 )
	self.ButtonText:setTTF( TOD_TTF )
	self.ButtonText:setLetterSpacing( 1 )
	self.ButtonText:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
	self.ButtonText:setRGB( 0.91, 0.93, 0.98 )
	self.ButtonText:linkToElementModel( self, "displayText", true, function ( model )
		local displayText = Engine.GetModelValue( model )
		if displayText then
			self.ButtonText:setText( Engine.Localize( displayText ) )
		end
	end )
	self:addElement( self.ButtonText )

	local function paint( focused )
		self.FrameFocus:completeAnimation()
		self.FrameFocus:setAlpha( focused and 1 or 0 )
		local c = focused and PM_RED or PM_IDLE   -- RT: focus = the Fallen RED (the lit line on i_tod_pm_btn_focus)
		self.Glyph:setRGB( c[ 1 ], c[ 2 ], c[ 3 ] )
		self.ButtonText:setRGB( focused and 1 or 0.91, focused and 1 or 0.93, focused and 1 or 0.98 )
	end
	self.clipsPerState = {
		DefaultState = {
			DefaultClip = function ()
				self:setupElementClipCounter( 1 )
				paint( false )
				self.clipFinished( self.FrameFocus, {} )
			end,
			Focus = function ()
				self:setupElementClipCounter( 1 )
				paint( true )
				self.clipFinished( self.FrameFocus, {} )
			end
		}
	}

	LUI.OverrideFunction_CallOriginalSecond( self, "close", PmCloseChildren )
	return self
end

-- The settings icon button: 81 x 48 (art 324 x 192), the glyph centred at 28 x 28.
CoD.TodPmIconButton = InheritFrom( LUI.UIElement )
CoD.TodPmIconButton.new = function ( menu, controller )
	local self = LUI.UIElement.new()
	self:setClass( CoD.TodPmIconButton )
	self.id = "TodPmIconButton"
	self.soundSet = "default"
	self:setLeftRight( true, false, 0, 78 )     -- 324 x 192 art at RS
	self:setTopBottom( true, false, 0, 46.2 )
	self:makeFocusable()
	self:setHandleMouse( true )
	self.anyChildUsesUpdateState = true

	self.Frame = LUI.UIImage.new()
	self.Frame:setLeftRight( true, true, 0, 0 )
	self.Frame:setTopBottom( true, true, 0, 0 )
	self.Frame:setImage( RegisterImage( "i_tod_pm_iconbtn" ) )
	self:addElement( self.Frame )

	self.FrameFocus = LUI.UIImage.new()
	self.FrameFocus:setLeftRight( true, true, 0, 0 )
	self.FrameFocus:setTopBottom( true, true, 0, 0 )
	self.FrameFocus:setImage( RegisterImage( "i_tod_pm_iconbtn_focus" ) )
	self.FrameFocus:setAlpha( 0 )
	self:addElement( self.FrameFocus )

	self.ButtonIcon = LUI.UIImage.new()
	self.ButtonIcon:setLeftRight( true, false, 25.5, 52.5 )
	self.ButtonIcon:setTopBottom( true, false, 9.6, 36.6 )
	self.ButtonIcon:setRGB( 0.93, 0.95, 1 )
	self.ButtonIcon:linkToElementModel( self, "icon", true, function ( model )
		local iconPath = Engine.GetModelValue( model )
		if iconPath then
			self.ButtonIcon:setImage( RegisterImage( iconPath ) )
		end
	end )
	self:addElement( self.ButtonIcon )

	self.clipsPerState = {
		DefaultState = {
			DefaultClip = function ()
				self:setupElementClipCounter( 1 )
				self.FrameFocus:completeAnimation()
				self.FrameFocus:setAlpha( 0 )
				self.clipFinished( self.FrameFocus, {} )
			end,
			Focus = function ()
				self:setupElementClipCounter( 1 )
				self.FrameFocus:completeAnimation()
				self.FrameFocus:setAlpha( 1 )
				self.clipFinished( self.FrameFocus, {} )
			end
		}
	}

	self:registerEventHandler( "mouseenter", function ( element, event )
		element:processEvent( { name = "gain_focus" } )
		return false
	end )
	self:registerEventHandler( "mouseleave", function ( element, event )
		element:processEvent( { name = "lose_focus" } )
		return false
	end )

	LUI.OverrideFunction_CallOriginalSecond( self, "close", PmCloseChildren )
	return self
end

-- Third Person Toggle Functions
local GetThirdPersonLabel = function(controller)
	local thirdPersonModel = Engine.GetModel(Engine.GetModelForController(controller), "ui_menu_option_third_person")
	local thirdPerson = Engine.GetModelValue(thirdPersonModel)
	
	if thirdPerson == nil then
		Engine.SetModelValue(thirdPersonModel, false)
		thirdPerson = false
	end
	
	return thirdPerson and "Switch To First Person" or "Switch To Third Person"
end

local ToggleThirdPerson = function(self, element, controller, actionParam, menu)
	local thirdPersonModel = Engine.CreateModel(Engine.GetModelForController(controller), "ui_menu_option_third_person")
	local newValue = not Engine.GetModelValue(thirdPersonModel)
	Engine.SetModelValue(thirdPersonModel, newValue)
	Engine.SendMenuResponse(controller, "StartMenu_Main", "ui_menu_option_third_person|" .. (newValue and "1" or "0"))
	
	-- Update button list to show new label
	if menu.ButtonList then
		menu.ButtonList:updateDataSource()
	end
end

-- [tod] GAME-OVER MODE (v9.24, port of map 1's retry-on-death v3): on a wipe (or
-- the finale's win), _tod_gameover.gsc re-enables the ingame menu (stock disables
-- it at end_game), force-opens THIS menu on every player and sets the host-side
-- dvar tod_go_active=1. In that mode the button list is exactly two entries —
-- Restart Map / End Game — navigated with the menu's own native up/down +
-- confirm. The dvar is host-machine-only, so co-op peers get the normal pause
-- list (Leave Game works there; restarting is the host's call). GSC scrubs the
-- dvar at init, so a mid-run pause menu is never in this mode. Every read is
-- pcall'd through a try-list (the dvar-read signature differs by build).
local TodGoActive = function(controller)
	local tries = {
		function() return Engine.DvarString(controller, "tod_go_active") end,
		function() return Engine.DvarString("tod_go_active") end,
		function() return Engine.GetDvarString("tod_go_active") end,
	}
	for i = 1, #tries do
		local ok, r = pcall(tries[i])
		if ok and r ~= nil and tostring(r) == "1" then
			return true
		end
	end
	return false
end

-- [tod] map_restart IS A SOLO-ONLY LANE (2026-09-07, Workshop report from
-- Ticksy: "Fix restart level button please, it kicks the other player out in
-- coop!").
--
-- The RESTART LEVEL entry is the KIT's, not ours: byte-identical in this map's
-- first commit, in v14.16 and in the working tree, and identical in map 1. We
-- never authored or touched it, so nothing recent broke it. What DID change is
-- discoverability — v17.26 (shipped in the Sep 4 publish) linked the icon row
-- to the button column, and before that the column was unreachable on a gamepad
-- and reachable only by mouse hover. An always-broken button became a findable
-- one, and the reports started.
--
-- Engine.Exec(controller, "map_restart") runs the console command on the
-- PRESSING machine. On the host that reloads the level; the connected peer does
-- not come with it and lands back at the main menu — which is exactly the
-- report ("the OTHER player", i.e. the presser was the host). The game-over
-- RESTART MAP entry is the same call and carries the same defect, so both are
-- gated here.
--
-- ⚠️ THIS DOES NOT USE Engine.GetPlayerCount(), AND THE FIRST VERSION DID.
-- That call is made by the Leave Game lane below, which is why it was taken as
-- proven — but look at it: both branches of its `if` are IDENTICAL disconnects,
-- so its return value has never decided anything and a wrong value could not be
-- seen. Gating a real button on it hid RESTART LEVEL in SOLO (user 2026-09-07:
-- "I didnt see it in solo") — the first time this map ever read that function's
-- answer. A call nobody has watched DECIDE something is not a proven call.
--
-- The count now comes from GSC, where GetPlayers().size is authoritative, over
-- the same dvar channel TodGoActive above reads. That channel IS proven: the
-- two-entry game-over menu has shipped on it since v9.24 and is the only reason
-- that menu ever appears. Publisher: _tod_main::party_dvar_watch.
--
-- READ POSITIVELY — hide only on a number that is definitely above 1. A missing
-- dvar, an unreadable one, or a non-numeric value all leave the button exactly
-- where it has always been, so the worst case is the pre-gate behaviour rather
-- than a feature quietly disappearing. A co-op PEER reads "" (SetDvar is
-- host-side) and keeps the button; pressing it drops only that peer, while the
-- HOST pressing it drops the party, and the host is the seat this covers.
--
-- Each action re-checks at press time too, for a cached button list that
-- outlives a join. Closing the menu beats booting a teammate.
local TodCoop = function(controller)
	local tries = {
		function() return Engine.DvarString(controller, "tod_party") end,
		function() return Engine.DvarString("tod_party") end,
		function() return Engine.GetDvarString("tod_party") end,
	}
	for i = 1, #tries do
		local ok, r = pcall(tries[i])
		if ok and r ~= nil then
			local n = tonumber(tostring(r))
			if n ~= nil then
				return n > 1
			end
		end
	end
	return false
end

-- DataSource for small top buttons
DataSources.AetheriumSmallMenuButtons = ListHelper_SetupDataSource("AetheriumSmallMenuButtons", function(controller)
	local buttons = {}

	-- Graphics Settings
	table.insert(buttons, {
		models = {
			icon = USE_PAUSE_V2 and "i_tod_pm_gly_graphics" or "i_mtl_icon_ftueftus_audio_config_tv",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_Graphics_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_Graphics", controller, "", "")
				end
			end
		}
	})

	-- Sound/Audio Settings
	table.insert(buttons, {
		models = {
			icon = USE_PAUSE_V2 and "i_tod_pm_gly_audio" or "i_mtl_image_2d767ba54c664e54",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_Sound_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_Sound", controller, "", "")
				end
			end
		}
	})

	-- Keybinds/Controls Settings
	table.insert(buttons, {
		models = {
			icon = USE_PAUSE_V2 and "i_tod_pm_gly_controls" or "i_mtl_firing_range_input_settings_kbm",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_Controls_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_Controls", controller, "", "")
				end
			end
		}
	})

	-- All Options (Show inline options)
	table.insert(buttons, {
		models = {
			icon = USE_PAUSE_V2 and "i_tod_pm_gly_settings" or "i_mtl_ui_menu_codhq_icon_settings",
			action = function(self, element, controller, actionParam, menu)
				-- Same action as Game Settings button (one owner: TodSetPage)
				TodSetPage(menu, controller, true)
			end
		}
	})

	return buttons
end, true)

-- DataSource for menu buttons
DataSources.AetheriumStartMenuButtons = ListHelper_SetupDataSource("AetheriumStartMenuButtons", function(controller)
	local buttons = {}

	-- V2 settings page: the SAME list answers with the settings entries (see
	-- TodSetPage). Game-over mode never opens it (its list has no settings entry).
	if USE_PAUSE_V2 and TodV2Settings[ controller ] and TodOptionsBuild then
		return TodOptionsBuild( controller )
	end

	-- [tod] game-over mode: two choices solo, ONE in co-op, both the existing
	-- pause-menu lanes verbatim (Restart Level's map_restart, Leave Game's
	-- disconnect). No "Return To Game" — there is no game to return to.
	if TodGoActive(controller) then
		-- Co-op gets End Game only: map_restart reloads the level under the
		-- host and drops the peer to the main menu (see TodCoop above).
		if not TodCoop(controller) then
			table.insert(buttons, {
				models = {
					glyph = "i_tod_pm_gly_restart",
					displayText = "Restart Map",
					action = function(self, element, controller, actionParam, menu)
						GoBack(menu, controller)
						if TodCoop(controller) then return end
						Engine.Exec(controller, "map_restart")
					end
				}
			})
		end
		table.insert(buttons, {
			models = {
				glyph = "i_tod_pm_gly_leave",
				displayText = "End Game",
				action = function(self, element, controller, actionParam, menu)
					menu:processEvent({
						name = "close_all_ingame_menus",
						controller = controller
					})
					Engine.SendMenuResponse(controller, "popup_leavegame", "endround")
					Engine.SetDvar("cl_paused", 0)
					Engine.Exec(controller, "disconnect")
				end
			}
		})
		return buttons
	end

	table.insert(buttons, {
		models = {
			glyph = "i_tod_pm_gly_return",
			displayText = "Return To Game",
			action = function(self, element, controller, actionParam, menu)
				RefreshLobbyRoom(menu, controller)
				StartMenuGoBack(menu, controller)
			end
		}
	})

	-- [tod] SOLO ONLY (see TodCoop above): in co-op this button reloads the
	-- level under the host and drops the teammate to the main menu, so it is
	-- not offered at all. Leave Game below is the co-op exit.
	if not TodCoop(controller) then
		table.insert(buttons, {
			models = {
				glyph = "i_tod_pm_gly_restart",
				displayText = "Restart Level",
				action = function(self, element, controller, actionParam, menu)
					-- Close menu first
					GoBack(menu, controller)
					if TodCoop(controller) then return end
					-- Restart the map
					Engine.Exec(controller, "map_restart")
				end
			}
		})
	end

	table.insert(buttons, {
		models = {
			glyph = "i_tod_pm_gly_camera",
			displayText = GetThirdPersonLabel(controller),
			action = ToggleThirdPerson
		}
	})

	table.insert(buttons, {
		models = {
			glyph = "i_tod_pm_gly_settings",
			displayText = "Game Settings",
			action = function(self, element, controller, actionParam, menu)
				-- Instantly switch to options (one owner: TodSetPage)
				TodSetPage(menu, controller, true)
			end
		}
	})

	-- HUD Settings and Social buttons removed

	table.insert(buttons, {
		models = {
			glyph = "i_tod_pm_gly_leave",
			displayText = "Leave Game",
			action = function(self, element, controller, actionParam, menu)
				-- Close all menus first
				menu:processEvent({
					name = "close_all_ingame_menus",
					controller = controller
				})
				
				-- Send menu response for proper cleanup
				Engine.SendMenuResponse(controller, "popup_leavegame", "endround")
				
				-- ⚠️ THIS BRANCH IS INERT AND MUST NOT BE CITED AS PROOF OF
				-- ANYTHING (2026-09-07). Both arms are the same three lines, so
				-- Engine.GetPlayerCount()'s return value has never changed a
				-- single behaviour here — which means a WRONG value is invisible
				-- in this file. Two separate changes read this code as evidence
				-- that the call works and shipped bugs on it: the solo Quick
				-- Revive price (quoted 1500 in solo from 2026-08-23) and the
				-- co-op restart gate (hid RESTART LEVEL in SOLO, 2026-09-07).
				-- It does not report solo. If you need the party size, read the
				-- `tod_party` dvar that _tod_main::party_dvar_watch publishes —
				-- see TodCoop at the top of this file.
				--
				-- Kept rather than deleted only because it is upstream kit code
				-- and deleting it changes nothing; the comment is the point.
				Engine.SetDvar("cl_paused", 0)
				Engine.Exec(controller, "disconnect")
			end
		}
	})

	return buttons
end, true)

-- DataSource for options buttons (shown when Game Settings is clicked)
TodOptionsBuild = function(controller)
	local options = {}
	
	if not USE_PAUSE_V2 then table.insert(options, {   -- V2: the icon row opens this (docs/180 difference 4)
		models = {
			displayText = "Graphics",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_Graphics_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_Graphics", controller, "", "")
				end
			end
		}
	}) end
	
	if not USE_PAUSE_V2 then table.insert(options, {   -- V2: the icon row opens this (docs/180 difference 4)
		models = {
			displayText = "Audio",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_Sound_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_Sound", controller, "", "")
				end
			end
		}
	}) end
	
	if not USE_PAUSE_V2 then table.insert(options, {   -- V2: the icon row opens this (docs/180 difference 4)
		models = {
			displayText = "Controls",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_Controls_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_Controls", controller, "", "")
				end
			end
		}
	}) end
	
	table.insert(options, {
		models = {
			glyph = "i_tod_pm_gly_voice",
			displayText = "Voice & Muting",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_Voice_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_Voice", controller, "", "")
				end
			end
		}
	})
	
	table.insert(options, {
		models = {
			glyph = "i_tod_pm_gly_network",
			displayText = "Network",
			action = function(self, element, controller, actionParam, menu)
				OpenPopup(menu, "StartMenu_Options_Network", controller, "", "")
			end
		}
	})
	
	table.insert(options, {
		models = {
			glyph = "i_tod_pm_gly_safearea",
			displayText = "Safe Area",
			action = function(self, element, controller, actionParam, menu)
				OpenPopup(menu, "StartMenu_Options_Graphics_SafeArea", controller, "", "")
			end
		}
	})
	
	table.insert(options, {
		models = {
			glyph = "i_tod_pm_gly_content",
			displayText = "Content Filter",
			action = function(self, element, controller, actionParam, menu)
				if IsPC() then
					OpenPopup(menu, "StartMenu_Options_GraphicContent_PC", controller, "", "")
				else
					OpenPopup(menu, "StartMenu_Options_GraphicContent", controller, "", "")
				end
			end
		}
	})
	
	table.insert(options, {
		models = {
			glyph = "i_tod_pm_gly_credits",
			displayText = "Credits",
			action = function(self, element, controller, actionParam, menu)
				OpenPopup(menu, "Credit_Fullscreen", controller, "", "")
			end
		}
	})
	
	table.insert(options, {
		models = {
			glyph = "i_tod_pm_gly_back",
			displayText = "Back",
			action = function(self, element, controller, actionParam, menu)
				-- Instantly hide options and show main menu (one owner: TodSetPage)
				TodSetPage(menu, controller, false)
			end
		}
	})
	
	return options
end
DataSources.AetheriumOptionsButtons = ListHelper_SetupDataSource("AetheriumOptionsButtons", TodOptionsBuild, true)

local PostLoadFunc = function(self, controller)
	self:registerEventHandler("menu_opened", function(element, event)
		Engine.SetUIActive(controller, true)
		
		-- Hide HUD when pause menu opens
		local controllerModel = Engine.GetModelForController(controller)
		local hudVisibilityModel = Engine.GetModel(controllerModel, "UIVisibility.Visibility")
		if hudVisibilityModel then
			Engine.SetModelValue(hudVisibilityModel, 0)
		end
		
		return true
	end)
	
	self:registerEventHandler("menu_closed", function(element, event)
		Engine.SetUIActive(controller, false)
		
		-- Show HUD when pause menu closes
		local controllerModel = Engine.GetModelForController(controller)
		local hudVisibilityModel = Engine.GetModel(controllerModel, "UIVisibility.Visibility")
		if hudVisibilityModel then
			Engine.SetModelValue(hudVisibilityModel, 1)
		end
		
		return true
	end)
	
	if CoD.isZombie then
		self.disableDarkenElement = true
		self.disablePopupOpenCloseAnim = false
	end
end

LUI.createMenu.StartMenu_Main = function(controller)
	local self = CoD.Menu.NewForUIEditor("StartMenu_Main")

	self.soundSet = "default"
	self:setOwner(controller)
	self:setLeftRight(true, true, 0, 0)
	self:setTopBottom(true, true, 0, 0)
	self:playSound("menu_open", controller)
	self.buttonModel = Engine.CreateModel(Engine.GetModelForController(controller), "StartMenu_Main.buttonPrompts")
	self.anyChildUsesUpdateState = true

	-- Dark Blur Overlay
	self.DarkOverlay = LUI.UIImage.new()
	self.DarkOverlay:setLeftRight(true, true, 0, 0)
	self.DarkOverlay:setTopBottom(true, true, 0, 0)
	self.DarkOverlay:setImage(RegisterImage("$white"))
	self.DarkOverlay:setRGB(0.05, 0.05, 0.05)
	self.DarkOverlay:setAlpha(USE_PAUSE_V2 and 0.65 or 0.8)   -- V2: the backdrop's vignette carries the rest
	self:addElement(self.DarkOverlay)

	if USE_PAUSE_V2 then
		local function Img( name, l, r, t, b )
			local e = LUI.UIImage.new()
			e:setLeftRight( true, false, l, r )
			e:setTopBottom( true, false, t, b )
			e:setImage( RegisterImage( name ) )
			self:addElement( e )
			return e
		end
		-- Full-screen vignette + corner text, then the two panels at the target's
		-- proportions (docs/180 "Canvas layout"). Every rect holds its art's aspect.
		self.TodPmBackdrop = Img( "i_tod_pm_backdrop", 0, 1280, 0, 720 )
		local l0, t0 = LArt( 0, 0 )
		local l1, t1 = LArt( 1468, 1196 )
		self.TodPmPanelL   = Img( "i_tod_pm_panel_left", l0, l1, t0, t1 )
		local r0, u0 = RArt( 0, 0 )
		local r1, u1 = RArt( 896, 1208 )   -- 1208: build 14 padded 2 transparent rows at the bottom (multiple-of-4 rule); the rect carries them so the art keeps its aspect
		self.TodPmPanelR   = Img( "i_tod_pm_panel_right", r0, r1, u0, u1 )
		-- Our emblem over the panel's empty top-left notch (it overhangs the top
		-- edge on purpose, as in the target). Same kit image the old layout drew.
		local ex0, ey0 = LArt( 88, -48 )
		local ex1, ey1 = LArt( 280, 144 )
		self.GameModeIcon = Img( "i_mtl_sat_ui_icon_gamemode_zm_standard", ex0, ex1, ey0, ey1 )
		-- The round number, inside the panel's ROUND box (art 790..930 x 60..125).
		local nx0, ny0 = LArt( 790, 64 )
		local nx1, ny1 = LArt( 930, 120 )
		self.RoundNumber = LUI.UIText.new()
		self.RoundNumber:setLeftRight( true, false, nx0, nx1 )
		self.RoundNumber:setTopBottom( true, false, ny0, ny1 )
		self.RoundNumber:setTTF( TOD_TTF )
		self.RoundNumber:setRGB( 0.98, 0.11, 0.22 )   -- RT: the Fallen red (docs/180; synthwave was 1.00, 0.17, 0.82)
		self.RoundNumber:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		-- Same authority as the old readout below: CoD.TodRound first (v17.25).
		self.RoundNumber:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "gameScore.roundsPlayed" ), function ( model )
			local roundsPlayed = Engine.GetModelValue( model )
			if CoD.TodRound and CoD.TodRound >= 1 then
				self.RoundNumber:setText( Engine.Localize( tostring( CoD.TodRound ) ) )
			elseif roundsPlayed then
				self.RoundNumber:setText( Engine.Localize( tostring( math.max( 1, roundsPlayed - 1 ) ) ) )
			end
		end )
		self:addElement( self.RoundNumber )
		-- THE CLASS AND ITS PASSIVE, in the empty strip right of the ROUND box (art
		-- 955..1415 x 30..140, above the divider at 146). Nothing is drawn before the
		-- draft (CoD.TodClass 0).
		local ci = CoD.TodClass or 0
		local info = ( CoD.TodClassInfo or {} )[ ci ]
		if info then
			local cx0 = LArt( 955, 0 )
			local cx1 = LArt( 1415, 0 )
			local function ClassTxt( str, ay0, ay1, rgb, align )
				if not str or str == "" then return end
				local _, y0 = LArt( 0, ay0 )
				local _, y1 = LArt( 0, ay1 )
				local e = LUI.UIText.new()
				e:setLeftRight( true, false, cx0, cx1 )
				e:setTopBottom( true, false, y0, y1 )
				e:setTTF( TOD_TTF )
				e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
				e:setAlignment( align or Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
				e:setText( str )
				self:addElement( e )
			end
			-- 2026-09-28: the CLASS TIER moved here from the upgrade list (user). Tier = the tier row's
			-- level (sent from tier 2 on; absent = tier 1); the next-tier line reuses the tier row's own
			-- act text (DETAIL[24]), so the floors stay LOCKSTEP with tier_floor_ok.
			local tierLine, nextLine = "", ""
			if CoD.TodClassTierLines then tierLine, nextLine = CoD.TodClassTierLines() end
			ClassTxt( info.name, 32, 70, { 0.93, 0.95, 0.97 } )
			ClassTxt( tierLine, 32, 56, { 1.0, 0.80, 0.30 }, Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT )
			ClassTxt( nextLine, 58, 76, { 0.62, 0.66, 0.76 }, Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT )
			-- PASSIVE: a grey label with the passive lines hanging beside it
			local indent = 104
			local function PassTxt( str, ay0, ay1 )
				if not str or str == "" then return end
				local px0 = LArt( 955 + indent, 0 )
				local _, y0 = LArt( 0, ay0 )
				local _, y1 = LArt( 0, ay1 )
				local e = LUI.UIText.new()
				e:setLeftRight( true, false, px0, cx1 )
				e:setTopBottom( true, false, y0, y1 )
				e:setTTF( TOD_TTF )
				e:setRGB( 0.50, 0.78, 0.96 )
				e:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
				e:setText( str )
				self:addElement( e )
			end
			ClassTxt( "PASSIVE", 84, 100, { 0.48, 0.51, 0.62 } )
			PassTxt( info.passive[ 1 ], 80, 102 )
			PassTxt( info.passive[ 2 ], 106, 128 )
		end
		-- Title plate (one of three, swapped by TodSetPage / game-over mode).
		local tx0, ty0 = RArt( 84, 56 )
		local tx1, ty1 = RArt( 596, 180 )   -- 1024 x 248 art at RS/2
		self.TodPmTitle = Img( "i_tod_pm_title_pause", tx0, tx1, ty0, ty1 )
	else
	-- pause_menu_bg
	self.BGMain = LUI.UIImage.new()
	self.BGMain:setLeftRight(true, false, 0, 1280)
	self.BGMain:setTopBottom(true, false, 0, 720)
	self.BGMain:setImage(RegisterImage("i_mtl_image_2c20915dba690ea5"))
	self:addElement(self.BGMain)

	-- sat_pause_menu_bg
	self.BGRight = LUI.UIImage.new()
	self.BGRight:setLeftRight(true, false, 823, 1252)
	self.BGRight:setTopBottom(true, false, 0, 720)
	self.BGRight:setImage(RegisterImage("i_mtl_sat_pause_menu_bg"))
	self:addElement(self.BGRight)

	-- bg_blood
	self.BGBlood = LUI.UIImage.new()
	self.BGBlood:setLeftRight(true, false, 814, 1338)
	self.BGBlood:setTopBottom(true, false, 390, 711)
	self.BGBlood:setImage(RegisterImage("i_mtl_image_273102a380412bec"))
	self:addElement(self.BGBlood)

	-- Game mode icon
	self.GameModeIcon = LUI.UIImage.new()
	self.GameModeIcon:setLeftRight(true, false, 5, 97)
	self.GameModeIcon:setTopBottom(true, false, 10, 102)
	self.GameModeIcon:setImage(RegisterImage("i_mtl_sat_ui_icon_gamemode_zm_standard"))
	self:addElement(self.GameModeIcon)

	-- Logo
	self.Logo = LUI.UIImage.new()
    self.Logo:setLeftRight(true, false, 79, 377)
    self.Logo:setTopBottom(true, false, 55, 102)
	self.Logo:setImage(RegisterImage("i_mtl_image_2fe6956607db6e68"))
	self:addElement(self.Logo)

	-- Map Name
	self.MapName = LUI.UIText.new()
    self.MapName:setLeftRight(true, false, 102, 192)
    self.MapName:setTopBottom(true, false, 37, 50)
	self.MapName:setText(Engine.Localize(CoD.UsermapName or "UNKNOWN MAP"))
	self.MapName:setTTF( "fonts/tod_tower1.ttf")
	self.MapName:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_LEFT)
	self:addElement(self.MapName)

	-- Round Label
	self.RoundLabel = LUI.UIText.new()
    self.RoundLabel:setLeftRight(true, false, 217, 281)
    self.RoundLabel:setTopBottom(true, false, 37, 50)
	self.RoundLabel:setText(Engine.Localize("ROUND"))
	self.RoundLabel:setTTF( "fonts/tod_tower1.ttf")
	self:addElement(self.RoundLabel)

	-- Round Number
	self.RoundNumber = LUI.UIText.new()
    self.RoundNumber:setLeftRight(true, false, 293, 330)
    self.RoundNumber:setTopBottom(true, false, 37, 50)
	self.RoundNumber:setTTF( "fonts/tod_tower1.ttf")
	-- [tod v17.25] THE HUD'S NUMBER WINS. CoD.TodRound is published by
	-- AetheriumRoundCounter from the server's own level.round_number (the
	-- tod_round LuiNotifyEvent lane) — the same number the top-right readout is
	-- showing. The stock "gameScore.roundsPlayed" model stays as the fallback
	-- for the window before the first push, but it is NOT the authority: note
	-- the -1 it needs to read right, which nobody here can explain, and which is
	-- reached through the three round functions _tod_endless_rounds.gsc
	-- replaces. Two round readouts that disagree is worse than either one being
	-- a beat late, so they now share a source.
	self.RoundNumber:subscribeToModel(Engine.GetModel(Engine.GetModelForController(controller), "gameScore.roundsPlayed"), function(model)
		local roundsPlayed = Engine.GetModelValue(model)
		if CoD.TodRound and CoD.TodRound >= 1 then
			self.RoundNumber:setText(Engine.Localize(tostring(CoD.TodRound)))
		elseif roundsPlayed then
			self.RoundNumber:setText(Engine.Localize(tostring(math.max(1, roundsPlayed - 1))))
		end
	end)
	self:addElement(self.RoundNumber)

	-- Game Mode Text
	self.GameModeText = LUI.UIText.new()
    self.GameModeText:setLeftRight(true, false, 102, 357)
    self.GameModeText:setTopBottom(true, false, 57, 74)
	self.GameModeText:setText(Engine.Localize("Round Based Zombies"))
	self.GameModeText:setTTF( "fonts/tod_tower1.ttf")
	self:addElement(self.GameModeText)
	end   -- USE_PAUSE_V2 chrome

	-- [tod] YOUR UPGRADES — pause-menu-only readout (user 2026-08-20: the
	-- always-on HUD column cluttered play). Data = CoD.TodOwned, accumulated
	-- by tod_upgrade.lua (always-open HUD menu) from GSC tod_upg_sync
	-- LuiNotifyEvents; this menu is re-created on every pause, so a plain
	-- read here is always current. Names come from CoD.TodDomainInfo (the
	-- HUD's own DOMAIN table — one source of truth).
	--
	-- (The V1 baked plate list - i_tod_pause_hdr / rNN / pip - left with the Map 1 purge, 2026-10-04:
	-- USE_PAUSE_V2 draws the i_tod_pm_* rows; the text rows below stay as the no-art fallback.)

	-- [tod] WHAT A CLASS TIER-UP TAKES FROM YOU (user 2026-08-27: "players dont
	-- know about is that upgrading class tiers will reset after an upgrade ...
	-- maybe in pause menu we can mark that upgrades that will get lost").
	--
	-- [tod v14.13] THE BADGE IS SERVER-COMPUTED NOW. v14.13 made persistence a
	-- property of the PLAYER, not just the domain (SCAVENGER survives a tier
	-- card for the ASSAULT ALONE — set_scope's scope_class lane), so a static
	-- client table can no longer answer "will a promotion take this row?".
	-- GSC's sync_max() packs the answer into every tod_upg_sync row (+100 on
	-- the max arg; tod_upgrade.lua strips it into row.safe), computed by the
	-- same domain_survives_tier() that tier_up's reset actually uses — the
	-- badge and the reset can never disagree, and class SWITCHING at stations
	-- re-syncs it for free. This table is the FALLBACK ONLY (row.safe == nil:
	-- an event older than the pack, which no live build sends). It lists the
	-- INVERTED 2026-08-31 (v15 item 19): persistence is now the RULE, so this
	-- fallback lists the EXCEPTIONS — the 13 domains a promotion still destroys
	-- — and anything absent is safe. It used to list the ten survivors; a build
	-- that still reads it that way is stale.
	-- SCAVENGER (8) is now SAFE FOR EVERY CLASS (the v14.13 assault-only
	-- carve-out is gone), so it is simply absent, and the fallback is right for
	-- all three classes that roll it rather than for one.
	--   6 twin ladders:  7 MAG SIZE  15 FIRE RATE  16 HANDLING  17 RECOIL
	--                   18 KNIFE SPEED  19 PENETRATION
	--   7 gun-bound:    25 ADRENALINE  26 OVERDRIVE  29 SUPPRESSING FIRE
	--                   31 DRAW CUT  33 SECOND WIND  37 FORCED MARCH
	--                   20 THOR'S THUNDER
	-- 2026-09-27 class pass 2: [19] / [29] / [37] left - SUMMONER MASTER / SPRINT / VITALITY
	-- (class scope, they keep through a promotion) took those ids.
	-- 2026-10-05 (W2E): [15] FIRE RATE, [16] HANDLING and [33] SECOND WIND left with their cards (parked, retired whole).
	local TIER_RESETS = { [18] = true, [20] = true }   -- [7] ARMS SPECIALIST / [17] left 2026-09-28 (class scope); [25] left 2026-09-28 (ADRENALINE, a Breacher class card); [26] PIERCING / [31] MELEE RANGE (class scope) reuse theirs
	-- 24 is the CLASS TIER row itself and is never badged, so it must read safe.
	local function tierSafe( id ) return id == 24 or not TIER_RESETS[ id ] end

	local todOwned = CoD.TodOwned or {}
	local todInfo = CoD.TodDomainInfo or {}

	-- AT THE TOP TIER THERE IS NOTHING LEFT TO LOSE (user 2026-08-27: "if you are
	-- in last tier in class the pause menu shouldnt show the reset icon assets
	-- anymore"). A player on their class's final gun can never be dealt another
	-- CLASS TIER card, so no upgrade they hold is at risk and every badge would be
	-- a warning about an event that cannot happen.
	--
	-- Row 24 is the CLASS TIER row: refresh_upgrade_list sends lvl = the current
	-- tier and max = tier_max(). Compared as lvl >= max rather than against a
	-- hardcoded 3, so raising tier_max never silently strands this.
	-- ABSENT MEANS TIER 1, not "unknown": that row is only sent from tier 2 on
	-- (tier 1 is the baseline, not an upgrade). Tier 1 is the furthest thing from
	-- the top, so the badges must show — which is what the nil path here does.
	local tierRow = todOwned[ 24 ]
	local atTopTier = tierRow ~= nil and tierRow.lvl ~= nil and tierRow.max ~= nil
	                  and tierRow.lvl >= tierRow.max
	local todRows = {}
	for id = 1, 63 do   -- the domain-id field is 6 bits (2026-08-22); ids above PAUSE_PLATE_MAX (below) render as TEXT rows; the body is nil-guarded so unused ids cost nothing
		local o = todOwned[ id ]
		if o and o.lvl and o.lvl > 0 then
			-- Detail lines come from tod_upgrade.lua's DETAIL table via
			-- CoD.TodDomainDesc — LEVEL-AWARE, so the number shown is the value
			-- at the level this player actually holds, not the per-level rule.
			-- Nil-guarded twice: the accessor may be absent (older HUD lua) and
			-- may return nil for an id with no detail row; DOMAIN.desc is the
			-- fallback so a new domain is never rendered blank.
			local eff, act = nil, nil
			if CoD.TodDomainDesc then
				eff, act = CoD.TodDomainDesc( id, o.lvl, o.dark )   -- v17.10: o.dark comes off the +200 bit sync_max packs into the max arg
			end
			if not eff then
				eff = ( todInfo[ id ] and todInfo[ id ].desc ) or ""
			end
			if CoD.TodRoundText then   -- [tod v16.57] the rounding guard (see tod_upgrade.lua)
				eff = CoD.TodRoundText( eff )
				act = CoD.TodRoundText( act )
			end
			todRows[ #todRows + 1 ] = {
				id = id,
				dark = ( o.dark == true ),   -- v17.10: drives the RED plate; comes off sync_max's +200 bit

				lvl = o.lvl,
				max = o.max or 10,
				name = ( todInfo[ id ] and todInfo[ id ].name ) or ( "UPGRADE " .. id ),
				eff = eff,
				act = act or "",
				-- Marked with the warning badge below. Will-be-taken AND a
				-- promotion still possible — at the top tier nothing can be
				-- taken, so the whole column of badges disappears. The
				-- authority is the row's server-computed safe bit (v14.13);
				-- tierSafe() is only the nil fallback.
				resets = ( not ( ( o.safe ~= nil and o.safe ) or ( o.safe == nil and tierSafe( id ) ) ) )
				         and ( not atTopTier ),
			}
		end
	end

	if USE_PAUSE_V2 then
		-- THE LIST ORDER (2026-09-28, user: "room for one more shared upgrade ... the AI partner card.
		-- And it will always go in the first spot of your list (top left)" + "keep a placeholder there
		-- so players know its something in the map" + "Drop class tier and we can put that next to the
		-- copy that says what class you are"): AI PARTNER (a fixed info row, never dealt), then the
		-- class's own cards in id order, then the three every class shares (DMG REDUCTION, LUCK,
		-- BOUNTY). The CLASS TIER row (24) is not in the list any more - the class header shows it.
		local SHARED_ORDER = { [2] = 1, [4] = 2, [3] = 3 }
		local classRows, sharedRows = {}, {}
		for _, r in ipairs( todRows ) do
			if r.id ~= 24 then
				if SHARED_ORDER[ r.id ] then sharedRows[ #sharedRows + 1 ] = r else classRows[ #classRows + 1 ] = r end
			end
		end
		table.sort( sharedRows, function( a, b ) return SHARED_ORDER[ a.id ] < SHARED_ORDER[ b.id ] end )
		todRows = { { id = 0, partner = true, lvl = 0, max = 0, name = TOD_PARTNER_ROW.name,
		              eff = TOD_PARTNER_ROW.eff, act = TOD_PARTNER_ROW.act, resets = false } }
		for _, r in ipairs( classRows ) do todRows[ #todRows + 1 ] = r end
		for _, r in ipairs( sharedRows ) do todRows[ #todRows + 1 ] = r end

		-- ------------------------------------------------------------------
		-- V2 UPGRADE ROWS (docs/180). Same todRows as the old panel, drawn as
		-- the target's cards: i_tod_pm_row (violet twin for a DARK row) with the
		-- domain icon in the well, then THE LIVE TEXT in the map TTF: name (white),
		-- effect at the player's level (light blue), activation (grey), and the
		-- level pips as a right-aligned column. RIGHT-ALIGNED on purpose: the
		-- target trails the pips after each name, but UIText cannot report its
		-- width here (no getTextWidth in this build), and a guessed width
		-- overlaps the name. A column cannot.
		--
		-- ONE FIXED SIZE, 2 x TOD_PAUSE_ROWS_COL (the 12-row cap the user set):
		-- no scaling preset, no "+N MORE" — the lint refuses a class that could
		-- need a 13th row, so the overflow line below is a belt that never bites.
		-- The body frame in the panel art is x 70..1450, y 320..1070; six rows
		-- at pitch 67 (h 63, width 63 x 5.12 = 322.6 at the art's aspect) fill
		-- its 407 canvas units of height; the two columns sit centred with a 24
		-- gap (the art's aspect fixes the width, so the side margins are what
		-- is left, 41 each).
		-- 2026-09-28: 2 x 5 (the 10-row cap). Rows 63 -> 67 tall (the width the two columns can
		-- take: 2 x 343 + 24 = 710 of the body's 751), pitch 67 -> 83 so five rows fill the
		-- body's 407 units (4 x 83 + 67 = 399). Every metric below scales by RS = 67 / 63.
		local ROW_H  = 67
		local ROW_W  = ROW_H * 1024 / 200
		local ROW_PITCH = 83
		local RS = ROW_H / 63
		local bodyL, bodyT = LArt( 70, 320 )
		local bodyR, bodyB = LArt( 1450, 1070 )
		local gapX  = 24
		local COL_X = { ( bodyL + bodyR ) / 2 - gapX / 2 - ROW_W, ( bodyL + bodyR ) / 2 + gapX / 2 }
		local ROW_Y0 = bodyT + 4
		local n = #todRows
		local overflow = 0
		if n > TOD_PAUSE_ROWS_CAP then overflow = n - TOD_PAUSE_ROWS_CAP; n = TOD_PAUSE_ROWS_CAP end
		local perCol = ( n > TOD_PAUSE_ROWS_COL ) and math.ceil( n / 2 ) or n

		local function Txt( str, l, r, t, b, rgb, align )
			local e = LUI.UIText.new()
			e:setLeftRight( true, false, l, r )
			e:setTopBottom( true, false, t, b )
			e:setTTF( TOD_TTF )
			e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
			e:setAlignment( align or Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
			e:setText( str )
			self:addElement( e )
			return e
		end
		local function Pic( name, l, r, t, b, rgb )
			local e = LUI.UIImage.new()
			e:setLeftRight( true, false, l, r )
			e:setTopBottom( true, false, t, b )
			e:setImage( RegisterImage( name ) )
			if rgb then e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] ) end
			self:addElement( e )
			return e
		end

		-- Text metrics inside a 63-tall row (the user's "pretty small" pass:
		-- name 13 -> 16, effect 9.5 -> 12, activation 8.5 -> 11 canvas units).
		local NAME_T, NAME_B = 11.5 * RS, 26.5 * RS
		local EFF_T,  EFF_B  = 32.5 * RS, 44.5 * RS
		local ACT_T,  ACT_B  = 46.5 * RS, 57.5 * RS
		local TEXT_X = 70 * RS            -- clear of the 164-px well (art 14..178) + air, scaled with the row
		local PIP_D, PIP_P, PIP_Y = 9 * RS, 10.5 * RS, 15.5 * RS   -- 9 pips = 100 units (was 10 / 12.5: the long names ran into them)

		local anyReset = false
		for i = 1, n do
			local r = todRows[ i ]
			local col, idx = 1, i
			if i > perCol then col, idx = 2, i - perCol end
			local x = COL_X[ col ]
			local y = ROW_Y0 + ( idx - 1 ) * ROW_PITCH
			local dark = ( r.dark == true )
			-- THE AI COMPANION ROW (live, 2026-09-29): what the companion you hold says right now
			-- (TOD_PARTNER_ROW.view -> CoD.TodCompanionDescribe); dimmed only when none is held.
			local cd = r.partner and TOD_PARTNER_ROW.view() or nil
			local held = ( cd ~= nil and cd.held == true )
			if cd then r.name, r.eff, r.act = cd.name or TOD_PARTNER_ROW.name, cd.items or "", cd.status or "" end
			local rowPic = Pic( dark and "i_tod_pm_row_violet" or "i_tod_pm_row", x, x + ROW_W, y, y + ROW_H )
			if r.partner and not held then rowPic:setAlpha( 0.6 ) end
			-- icon well = art 14..178 x 18..182 (centre 96, 100); the glyph is 40 x 40 there
			local cx, cy = x + 96 * ROW_H / 200, y + 100 * ROW_H / 200
			if held and cd.portrait then
				-- the companion's portrait (docs/195, 240 x 192) framed inside the well's glow at its own aspect
				local pw = 42 * RS
				Pic( cd.portrait, cx - pw / 2, cx + pw / 2, cy - pw * 0.4, cy + pw * 0.4 )
			else
				Pic( r.partner and TOD_PARTNER_ROW.icon or PmIcon( r.id ), cx - 20 * RS, cx + 20 * RS, cy - 20 * RS, cy + 20 * RS,
				     r.partner and PM_IDLE or ( dark and PM_VIOLET or PM_RED ) )
			end
			if r.resets then
				anyReset = true
				Pic( "i_tod_pm_reset_mark", cx + 10 * RS, cx + 26 * RS, y + 1, y + 1 + 16 * RS )
			end
			-- pips: right-aligned column, capped at 10 (the highest domain max)
			local pipN = r.max
			if pipN > 10 then pipN = 10 end
			if pipN < r.lvl then pipN = r.lvl end
			local px0 = x + ROW_W - 12 - pipN * PIP_P
			for p = 1, pipN do
				local px = px0 + ( p - 1 ) * PIP_P
				local img = "i_tod_pm_pip_off"
				if p <= r.lvl then img = dark and "i_tod_pm_pip_on_violet" or "i_tod_pm_pip_on" end
				Pic( img, px, px + PIP_D, y + PIP_Y, y + PIP_Y + PIP_D )
			end
			local info = CoD.TodCompanionInfo
			if held and info then
				-- its three Black Market items, where the pips go: the HUD's loadout chip tinted by
				-- rarity with the item's icon (TodSpinReel onItems), an empty slot a dim rim
				local ch, cg = 18 * RS, 3
				local cy0 = y + PIP_Y + PIP_D / 2 - ch / 2
				local right = x + ROW_W - 12
				for c = 1, 3 do
					local slot = cd.slots and cd.slots[ c ]
					local l = right - ( 4 - c ) * ch - ( 3 - c ) * cg
					local rgb = slot and slot.rgb or info.emptyRim
					local chip = Pic( info.chip, l, l + ch, cy0, cy0 + ch, rgb )
					if slot and slot.icon then
						local ins = ch * 4 / 28   -- the HUD chip's icon inset (a 20 icon in a 28 chip)
						Pic( slot.icon, l + ins, l + ch - ins, cy0 + ins, cy0 + ch - ins, rgb )
					else
						chip:setAlpha( 0.35 )
					end
				end
				px0 = right - 3 * ch - 2 * cg
			end
			local tx = x + TEXT_X
			local idle = r.partner and not held
			Txt( held and r.name or Engine.Localize( r.name ), tx, px0 - 4, y + NAME_T, y + NAME_B, idle and { 0.74, 0.77, 0.82 } or { 0.93, 0.95, 0.97 } )
			Txt( r.eff, tx, x + ROW_W - 8, y + EFF_T, y + EFF_B, idle and PM_IDLE or { 0.50, 0.78, 0.96 } )
			if cd and r.act ~= "" then
				-- the companion's state, coloured: green active, amber destroyed, grey otherwise
				Txt( r.act, tx, x + ROW_W - 8, y + ACT_T, y + ACT_B, TOD_PARTNER_ROW.tone[ cd.tone or "idle" ] or TOD_PARTNER_ROW.tone.idle )
			elseif r.act ~= "" then
				-- Localize: a [{+bind}] token in an act line expands to the live key
				Txt( Engine.Localize( r.act ), tx, x + ROW_W - 8, y + ACT_T, y + ACT_B, { 0.48, 0.51, 0.62 } )
			end
		end

		if n == 0 then
			Txt( Engine.Localize( "NO UPGRADES YET" ), bodyL, bodyR, ( bodyT + bodyB ) / 2 - 9, ( bodyT + bodyB ) / 2 + 9, { 0.48, 0.51, 0.62 }, Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
		end
		if overflow > 0 then
			Txt( "+" .. overflow .. " MORE", COL_X[ 1 ], COL_X[ 1 ] + ROW_W, bodyB + 2, bodyB + 14, { 0.48, 0.51, 0.62 } )
		end
		-- The footer slot (art x 72..672, y 1108..1138): the reset legend when a
		-- row carries the badge, else the flavour line. Same rect (docs/180 A4 / C7).
		local fx0, fy0 = LArt( 72, 1108 )
		local fx1, fy1 = LArt( 672, 1138 )
		Pic( anyReset and "i_tod_pm_legend_reset" or "i_tod_pm_footer_flavor", fx0, fx1, fy0, fy1 )
	elseif #todRows > 0 then
		-- text fallback (pre-art path)
		self.TodUpgHeader = LUI.UIText.new()
		self.TodUpgHeader:setLeftRight( true, false, 102, 380 )
		self.TodUpgHeader:setTopBottom( true, false, 132, 149 )
		self.TodUpgHeader:setText( Engine.Localize( "YOUR UPGRADES" ) )
		self.TodUpgHeader:setTTF( "fonts/tod_tower1.ttf" )
		self.TodUpgHeader:setRGB( 0.35, 0.9, 1 )
		self.TodUpgHeader:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
		self:addElement( self.TodUpgHeader )

		local y = 158
		for i = 1, #todRows do
			local r = todRows[ i ]
			local t = LUI.UIText.new()
			t:setLeftRight( true, false, 102, 380 )
			t:setTopBottom( true, false, y, y + 14 )
			t:setText( Engine.Localize( r.name .. "  " .. r.lvl .. "/" .. r.max ) )
			t:setTTF( "fonts/tod_tower1.ttf" )
			t:setRGB( 0.86, 0.9, 0.95 )
			t:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
			self:addElement( t )

			local d = LUI.UIText.new()
			d:setLeftRight( true, false, 102, 500 )
			d:setTopBottom( true, false, y + 14, y + 26 )
			d:setText( r.eff )
			d:setTTF( "fonts/tod_tower1.ttf" )
			d:setRGB( 0.6, 0.66, 0.74 )
			d:setScale( 0.75 )
			d:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_LEFT )
			self:addElement( d )

			y = y + 30
		end
	end

	if USE_PAUSE_V2 then
		-- The time bar (GAME TIME baked, art 1024 x 98) and the live red value in
		-- its empty right half. Same server-time source as the old readout.
		self.TodPmTimeBar = LUI.UIImage.new()
		local bx0, by0 = RArt( 68, 376 )
		local bx1, by1 = RArt( 840, 451.4 )   -- 1024 x 100 art (98 + 2 padded rows, multiple-of-4 rule)
		self.TodPmTimeBar:setLeftRight( true, false, bx0, bx1 )
		self.TodPmTimeBar:setTopBottom( true, false, by0, by1 )
		self.TodPmTimeBar:setImage( RegisterImage( "i_tod_pm_timebar" ) )
		self:addElement( self.TodPmTimeBar )
		self.GameTimeValue = LUI.UIText.new()
		local vx0, vy0 = RArt( 502, 394 )
		local vx1, vy1 = RArt( 812, 432 )
		self.GameTimeValue:setLeftRight( true, false, vx0, vx1 )
		self.GameTimeValue:setTopBottom( true, false, vy0, vy1 )
		self.GameTimeValue:setTTF( TOD_TTF )
		self.GameTimeValue:setRGB( 0.98, 0.11, 0.22 )   -- RT: the Fallen red (docs/180; synthwave was 1.00, 0.17, 0.82)
		self.GameTimeValue:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT )
		self.GameTimeValue:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "hudItems.time.game_start_time" ), function ( model )
			local time = Engine.GetModelValue( model )
			if time then
				self.GameTimeValue:setupServerTime( time )
			end
		end )
		self:addElement( self.GameTimeValue )
	else
	-- Game Time Label
	self.GameTimeLabel = LUI.UIText.new()
    self.GameTimeLabel:setLeftRight(true, false, 925, 1033)
    self.GameTimeLabel:setTopBottom(true, false, 173, 187)
	self.GameTimeLabel:setText(Engine.Localize("Game Time:"))
	self.GameTimeLabel:setTTF( "fonts/tod_tower1.ttf")
	self.GameTimeLabel:setRGB(1, 1, 1)
	self.GameTimeLabel:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)
	self:addElement(self.GameTimeLabel)

	-- Game Time Value (Official Method)
	self.GameTimeValue = LUI.UIText.new()
    self.GameTimeValue:setLeftRight(true, false, 1041, 1114)
    self.GameTimeValue:setTopBottom(true, false, 172, 188)
	self.GameTimeValue:setTTF( "fonts/tod_tower1.ttf")
	self.GameTimeValue:setRGB(0.878, 0, 0)
	self.GameTimeValue:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)
	self.GameTimeValue:subscribeToModel(Engine.GetModel(Engine.GetModelForController(controller), "hudItems.time.game_start_time"), function(model)
		local time = Engine.GetModelValue(model)
		if time then
			self.GameTimeValue:setupServerTime(time)
		end
	end)
	self:addElement(self.GameTimeValue)
	end   -- USE_PAUSE_V2 time bar

	-- [tod 2026-09-02, KBM audit] UPGRADE CARDS controls legend.
	--
	-- The upgrade panel and the class draft show their controls on BAKED
	-- plates that carry the DEFAULT binds (MOUSE1 / MOUSE2 / V / SPACE, or the
	-- Xbox-layout pad glyphs). This line is the one place a player can read
	-- the LIVE ones: every [{+bind}] token below is expanded by the engine into
	-- the key or pad glyph bound RIGHT NOW on THIS device -- the same mechanism
	-- every stock "Hold [X]" hint rides, and the one PromptDefault.lua's
	-- SetFooter now uses for the cursor-hint cards. A rebinder who moved USE to
	-- E reads E here; a PS-layout pad reads its own glyphs.
	--
	-- Pad players get the d-pad line once the server has PROVED the pad
	-- (CoD.TodPad, the same one-way latch the HUD plates key on) -- before the
	-- latch the keyboard line is ALSO the truth for a pad, because RT / LT / R3
	-- are live lanes until the first d-pad press. Nothing here reads the
	-- device itself: the LUI probe guessed wrong for keyboard players with a
	-- pad plugged in (v16.3), and the latch is the only proof there is.
	--
	-- Menu-only by design (the card panels keep their art, the images-over-LUI
	-- rule), and it doubles as the first in-game proof of which bind names the
	-- engine expands: if any token here renders as literal "[{+...}]", that
	-- name is wrong and the frame-plate art in docs/69 must not use it.
	-- Sits under the button list (ends y=560); the signatures start at 637.
	if USE_PAUSE_V2 then
		-- V2: the whole UPGRADE CARDS box is one baked piece (card fan, title,
		-- SAME MAP DIFFERENT NIGHTMARE); the live glyph row below sits in its
		-- empty control row (art x 190..800, y 105..190 = canvas 881..1141, 619..655).
		self.TodCtlHeader = LUI.UIImage.new()
		local gx0, gy0 = RArt( 22, 1024 )
		local gx1, gy1 = RArt( 894, 1208 )   -- 1024 x 216 art (214 + 2 padded rows, multiple-of-4 rule)
		self.TodCtlHeader:setLeftRight(true, false, gx0, gx1)
		self.TodCtlHeader:setTopBottom(true, false, gy0, gy1)
		self.TodCtlHeader:setImage(RegisterImage("i_tod_pm_legend_box"))
		self:addElement(self.TodCtlHeader)
	else
		self.TodCtlHeader = LUI.UIText.new()
		self.TodCtlHeader:setLeftRight(true, false, 868, 1210)
		self.TodCtlHeader:setTopBottom(true, false, 576, 592)
		self.TodCtlHeader:setText(Engine.Localize("UPGRADE CARDS"))
		self.TodCtlHeader:setTTF( "fonts/tod_tower1.ttf")
		self.TodCtlHeader:setRGB(0.35, 0.9, 1)
		self.TodCtlHeader:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)
		self:addElement(self.TodCtlHeader)
	end

	-- [tod v16.83] THIS LINE WAS ADVERTISING TWO DEAD LANES. It named
	-- `+attack` and `+speed_throw` -- fire and aim -- which v16.57 REMOVED as
	-- menu inputs (they can never be given a side that is right on both a pad
	-- and a mouse; `_tod_upgrade_ui::wait_for_choice` still reads them, but
	-- only for the dev probe, and neither one assigns `want` any more). A
	-- player following this legend pressed fire, watched the focus not move,
	-- and concluded the menu was broken. It now names the same single lane the
	-- in-world plates do -- the offhand pair, with its direction -- so the two
	-- readouts can never disagree again.
	--
	-- No `CoD.TodPad` branch: that latch is not a device proof (v16.81 -- a
	-- keyboard binds 3/4 to action slots), and it never needed to be here.
	-- The engine expands each token into the live device's own key or glyph.
	-- [tod v16.93] THE LEGEND GETS THE SAME GLYPHS AS THE CARD MENUS.
	-- v16.83 fixed this line's WORDING and stopped there, so the pause menu was
	-- still spelling out key names while both card panels had moved to baked
	-- button art (v16.88). A readout that disagrees with the thing it describes
	-- is the exact failure v16.83 was fixing, one level up -- so it is not
	-- enough for the legend to be CORRECT, it has to MATCH.
	--
	-- Layout: two switch glyphs, the word SWITCH, the lock glyph, the word LOCK,
	-- inside the same 868..1210 band the text used. Rects are computed PER
	-- DEVICE for the reason the card menus document: the pad glyph is square and
	-- the keycap is wide and short, so one fixed rect would stretch one of them.
	-- [tod v17.55] the latch OR the bind expansion, through the ONE reader the
	-- card menus use (CoD.TodKeycap.PadDevice, argument in TodKeycap.lua) — so
	-- a pad player never reads keycaps here while the panels show a d-pad.
	local TodPad = ( CoD.TodPad == true )
	if not TodPad and CoD.TodKeycap ~= nil then
		TodPad = ( CoD.TodKeycap.PadDevice() == true )
	end
	-- [tod v18.48] the widget-free arm is GONE. v18.47 put a byte scan here and
	-- it reported "pad" for keyboard players, so this legend -- and both card
	-- menus -- drew controller art for everyone. KEYBOARD IS THE DEFAULT and a
	-- pad has to be proven; the only proof this file can make without the
	-- widget is CoD.TodPad, which it already reads above.
	local GW, GH = 30, 30           -- pad glyph: square
	if not TodPad then
		-- [v17.4] 64 x 32 and the text scaled: a multi-bound action (the user's
		-- +frag sits on both G and MOUSE3) expands to a string naming both, and
		-- the old 56 could not hold it. Same fix as the two card menus.
		GW, GH = 64, 32             -- keycap: wide and short
	end
	-- V2: the legend box's control row is 36 tall and 260 wide, so both glyph
	-- shapes shrink and the row is LEFT-aligned under UPGRADE CARDS (the box's
	-- right column is baked text).
	local CTL_CY = 616                 -- old band: glyph row 601..631, centre 616
	-- V2: the box's empty control row is art x 190..800, y 105..190 (of 1024 x
	-- 216): canvas 918..1169 wide, centre y = RY + (1024 + 147.5) * RS.
	local CTL_X0 = 918.6
	if USE_PAUSE_V2 then
		CTL_CY = RY + 1171.5 * RS
		if TodPad then GW, GH = 24, 24 else GW, GH = 44, 22 end
	end
	local gy = CTL_CY - GH / 2
	local function CtlGlyph(x, img)
		local e = LUI.UIImage.new()
		e:setLeftRight(true, false, x, x + GW)
		e:setTopBottom(true, false, gy, gy + GH)
		e:setImage(RegisterImage(img))
		self:addElement(e)
		return e
	end
	-- [tod 2026-09-26, the user's first V2 test: the caps read "E", "G OR / MIDDL",
	-- "SPACE" as the ENGINE's own dark key pictures, wrapped]. Engine.Localize hands
	-- Lua the UNEXPANDED token (docs/145, byte 21 + [{+frag}] + byte 20), so
	-- CoD.TodKeycap's trim-and-measure route finds no glyph for "[" and falls back
	-- to a UIText holding the token, which the engine expands into its own key
	-- picture at draw time - a full "G OR MIDDLE MOUSE" jammed into a 40-wide cap.
	-- V2 resolves the key FIRST: GetKeyBindingLocalizedString for the command,
	-- trimmed at the " OR " separator, uppercased, set as PLAIN TEXT in our TTF
	-- inside the pale cap. A read that still carries a token falls through to the
	-- old path.
	local function TodResolveKey(tok)
		local command = string.match(tok, "%[%{(.-)%}%]")
		if not command or not Engine.GetKeyBindingLocalizedString then return nil end
		local ok, raw = pcall(Engine.GetKeyBindingLocalizedString, controller, command, 0, false, false)
		if not ok or type(raw) ~= "string" or raw == "" then return nil end
		if string.find(raw, "[{", 1, true) then return nil end
		raw = string.gsub(raw, "%^%d", "")
		raw = string.gsub(raw, "[%c]", "")
		local sep = string.find(raw, "%s+[Oo][Rr]%s+")
		if sep then raw = string.sub(raw, 1, sep - 1) end
		raw = string.gsub(raw, "^%s+", "")
		raw = string.gsub(raw, "%s+$", "")
		if raw == "" then return nil end
		return string.upper(raw)
	end
	local function CtlKey(x, tok)
		if USE_PAUSE_V2 then
			local name = TodResolveKey(tok)
			if name then
				-- the cap's readable face: x inset 7.6%, centre at 43.5% of its height
				local inset = GW * 0.076
				local cy = gy + GH * 0.435
				local h = GH * 0.62
				-- MOUSE3, BUTTON4, SPACE...: fit the face (RT 2026-10-05: SPACE at full height needed 38.5 of 37.3)
				if #name > 4 then h = h * 4.6 / #name end
				local t = LUI.UIText.new()
				t:setLeftRight(true, false, x + inset, x + GW - inset)
				t:setTopBottom(true, false, cy - h / 2, cy + h / 2)
				t:setTTF( "fonts/tod_tower1.ttf")
				t:setRGB(0.10, 0.13, 0.20)
				t:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)
				t:setText(name)
				self:addElement(t)
				return t
			end
		end
		-- only drawn on KBM: the live bind, INSIDE the keycap.
		-- [tod v17.27] set in the MAP'S OWN TYPEFACE through CoD.TodKeycap, the
		-- one writer shared with both card menus. It trims a multi-bound action
		-- to its first key, measures the string in the baked glyph sheets and
		-- sizes it to the art's own bright face (centred at 43.5% of the cap
		-- height, not 50%). The UIText stays as the no-glyph fallback.
		local t = LUI.UIText.new()
		t:setTTF( "fonts/tod_tower1.ttf")
		t:setRGB(0.06, 0.07, 0.10)
		t:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)
		t:setAlpha(0)
		self:addElement(t)
		TodKeycapMake(self, t).paint(x, gy, GW, GH, tok)
		return t
	end
	local function CtlWord(x, w, str)
		local t = LUI.UIText.new()
		t:setLeftRight(true, false, x, x + w)
		-- V2: 13 tall, not 16 (2026-09-28, the menu render: "SWITCH" at 16 needed 52 of its 46-wide slot)
		local hh = USE_PAUSE_V2 and 6.5 or 8
		t:setTopBottom(true, false, CTL_CY - hh, CTL_CY + hh)
		t:setText(Engine.Localize(str))
		t:setTTF( "fonts/tod_tower1.ttf")
		t:setRGB(0.86, 0.9, 0.95)
		t:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)
		self:addElement(t)
		return t
	end
	do
		-- pack the row and centre it in the band
		local gap, wordW = 4, 62
		local gapW, gapL = 6, 16
		if USE_PAUSE_V2 then gap, wordW, gapW, gapL = 2, 46, 5, 10 end   -- 44+2+44+5+46+10+44+5+46 = 246 <= the row's 251
		local rowW = GW + gap + GW + gapW + wordW + gapL + GW + gapW + wordW
		local x = 1039 - rowW / 2      -- 1039 = centre of 868..1210
		if USE_PAUSE_V2 then x = CTL_X0 end
		local lImg = CtlGlyph(x, TodPad and "i_tod_pad_dpad_left" or "i_tod_key_blank_wide")
		if not TodPad then CtlKey(x, "[{+smoke}]") end
		x = x + GW + gap
		local rImg = CtlGlyph(x, TodPad and "i_tod_pad_dpad_right" or "i_tod_key_blank_wide")
		if not TodPad then CtlKey(x, "[{+frag}]") end
		x = x + GW + gapW
		CtlWord(x, wordW, "SWITCH")
		x = x + wordW + gapL
		CtlGlyph(x, TodPad and "i_tod_pad_button_a" or "i_tod_key_blank_wide")
		if not TodPad then CtlKey(x, "[{+gostand}]") end
		x = x + GW + gapW
		CtlWord(x, wordW, "LOCK")
		-- keep the handle the rest of the file expects to exist
		self.TodCtlLine = lImg
		self.TodCtlLineR = rImg
	end

	-- Options Header Text (hidden by default, shown with options)
	self.OptionsHeaderText = LUI.UIText.new()
    self.OptionsHeaderText:setLeftRight(true, false, 907, 1168)
    self.OptionsHeaderText:setTopBottom(true, false, 108, 132)
	self.OptionsHeaderText:setText(Engine.Localize("Options & Controls"))
	self.OptionsHeaderText:setTTF( "fonts/tod_tower1.ttf")
	self.OptionsHeaderText:setRGB(1, 1, 1)
	self.OptionsHeaderText:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)
	self.OptionsHeaderText:setAlpha(0)
	self:addElement(self.OptionsHeaderText)

	-- Pause Menu Text (hidden when options are shown)
	self.PauseMenuText = LUI.UIText.new()
	self.PauseMenuText:setLeftRight(true, false, 952, 1127)
	self.PauseMenuText:setTopBottom(true, false, 44, 68)
	self.PauseMenuText:setText(Engine.Localize("Pause Menu"))
	self.PauseMenuText:setTTF( "fonts/tod_tower1.ttf")
	self.PauseMenuText:setRGB(1, 1, 1)
	self.PauseMenuText:setAlignment(Enum.LUIAlignment.LUI_ALIGNMENT_LEFT)
	if USE_PAUSE_V2 then
		-- V2 draws its titles as baked plates (self.TodPmTitle); these two stay as
		-- inert handles for TodSetPage and the game-over retitle, never shown.
		self.PauseMenuText:setAlpha(0)
	end
	self:addElement(self.PauseMenuText)

	-- Small Top Buttons List
	self.SmallButtonList = LUI.UIList.new(self, controller, 2, 0, nil, true, false, 0, 0, false, false)
	self.SmallButtonList:makeFocusable()
	self.SmallButtonList:setLeftRight(true, false, 897, 1176)
	self.SmallButtonList:setTopBottom(true, false, 101, 142)
	self.SmallButtonList:setWidgetType(CoD.AetheriumSmallButton)
	self.SmallButtonList:setHorizontalCount(4)
	self.SmallButtonList:setSpacing(9)
	if USE_PAUSE_V2 then
		-- 4 x 78 at an 87 pitch (the target's), under the right panel's divider
		local ix0, iy0 = RArt( 98, 242 )
		local ix1, iy1 = RArt( 98 + 4 * 180.6, 338 )
		self.SmallButtonList:setLeftRight(true, false, ix0, ix1)
		self.SmallButtonList:setTopBottom(true, false, iy0, iy1)
		self.SmallButtonList:setWidgetType(CoD.TodPmIconButton)
		self.SmallButtonList:setSpacing(18.6 * RS)
	end
	self.SmallButtonList:setDataSource("AetheriumSmallMenuButtons")
	self.SmallButtonList:registerEventHandler("gain_focus", function(element, event)
		local retVal = nil
		if element.gainFocus then
			retVal = element:gainFocus(event)
		elseif element.super.gainFocus then
			retVal = element.super:gainFocus(event)
		end
		CoD.Menu.UpdateButtonShownState(element, self, controller, Enum.LUIButton.LUI_KEY_XBA_PSCROSS)
		return retVal
	end)
	self.SmallButtonList:registerEventHandler("lose_focus", function(element, event)
		local retVal = nil
		if element.loseFocus then
			retVal = element:loseFocus(event)
		elseif element.super.loseFocus then
			retVal = element.super:loseFocus(event)
		end
		return retVal
	end)
	self:AddButtonCallbackFunction(self.SmallButtonList, controller, Enum.LUIButton.LUI_KEY_XBA_PSCROSS, "ENTER", function(element, menu, controller, model)
		ProcessListAction(self, element, controller)
		return true
	end, function(element, menu, controller)
		CoD.Menu.SetButtonLabel(menu, Enum.LUIButton.LUI_KEY_XBA_PSCROSS, "MENU_SELECT")
		return true
	end, false)
	self:addElement(self.SmallButtonList)
	self.SmallButtonList.id = "SmallButtonList"

	-- Button List (replaces individual button images)
	self.ButtonList = LUI.UIList.new(self, controller, 5, 0, nil, false, false, 0, 0, false, false)
	self.ButtonList:makeFocusable()
	self.ButtonList:setLeftRight(true, false, 868, 1210)
	self.ButtonList:setTopBottom(true, false, 221, 560)
	self.ButtonList:setWidgetType(CoD.AetheriumMenuButton)
	self.ButtonList:setVerticalCount(7)
	self.ButtonList:setSpacing(10)
	if USE_PAUSE_V2 then
		-- 372 x 40.7 buttons. This list is ALSO the settings page (6 entries,
		-- see TodSetPage), and the legend box's frame starts at art y 1024
		-- (canvas 555.6): 6 x 40.7 + 5 x 4.7 = 268 from 290.5 ends 558.5 - the
		-- box's top edge has 3 units of transparent air, so nothing touches.
		-- The main page has at most 5 entries and never gets near it.
		local lx0, ly0 = RArt( 68, 474 )
		local lx1, ly1 = RArt( 840, 1030 )
		self.ButtonList:setLeftRight(true, false, lx0, lx1)
		self.ButtonList:setTopBottom(true, false, ly0, ly1)
		self.ButtonList:setWidgetType(CoD.TodPmButton)
		self.ButtonList:setVerticalCount(6)
		self.ButtonList:setSpacing(4.7)
	end
	self.ButtonList:setDataSource("AetheriumStartMenuButtons")
	self.ButtonList:registerEventHandler("gain_focus", function(element, event)
		local retVal = nil
		if element.gainFocus then
			retVal = element:gainFocus(event)
		elseif element.super.gainFocus then
			retVal = element.super:gainFocus(event)
		end
		CoD.Menu.UpdateButtonShownState(element, self, controller, Enum.LUIButton.LUI_KEY_XBA_PSCROSS)
		return retVal
	end)
	self.ButtonList:registerEventHandler("lose_focus", function(element, event)
		local retVal = nil
		if element.loseFocus then
			retVal = element:loseFocus(event)
		elseif element.super.loseFocus then
			retVal = element.super:loseFocus(event)
		end
		return retVal
	end)
	self:AddButtonCallbackFunction(self.ButtonList, controller, Enum.LUIButton.LUI_KEY_XBA_PSCROSS, "ENTER", function(element, menu, controller, model)
		ProcessListAction(self, element, controller)
		return true
	end, function(element, menu, controller)
		CoD.Menu.SetButtonLabel(menu, Enum.LUIButton.LUI_KEY_XBA_PSCROSS, "MENU_SELECT")
		return true
	end, false)
	self:addElement(self.ButtonList)
	self.ButtonList.id = "ButtonList"
	
	-- Options List (hidden by default, shown when Game Settings is clicked)
	self.OptionsList = LUI.UIList.new(self, controller, 5, 0, nil, false, false, 0, 0, false, false)
	self.OptionsList:makeFocusable()
	self.OptionsList:setLeftRight(true, false, 868, 1210)
	self.OptionsList:setTopBottom(true, false, 221, 560)
	self.OptionsList:setWidgetType(CoD.AetheriumMenuButton)
	self.OptionsList:setVerticalCount(9)
	self.OptionsList:setSpacing(10)
	if USE_PAUSE_V2 then
		-- V2: INERT. The settings page is the main list re-sourced (TodSetPage);
		-- this list keeps existing for the old layout and for every handle the
		-- rest of the file holds, but it can never be seen, focused or hovered.
		self.OptionsList:setLeftRight(true, false, 0, 1)
		self.OptionsList:setTopBottom(true, false, 0, 1)
	end
	self.OptionsList:setDataSource("AetheriumOptionsButtons")
	self.OptionsList:setAlpha(0)
	self.OptionsList:registerEventHandler("gain_focus", function(element, event)
		local retVal = nil
		if element.gainFocus then
			retVal = element:gainFocus(event)
		elseif element.super.gainFocus then
			retVal = element.super:gainFocus(event)
		end
		CoD.Menu.UpdateButtonShownState(element, self, controller, Enum.LUIButton.LUI_KEY_XBA_PSCROSS)
		return retVal
	end)
	self.OptionsList:registerEventHandler("lose_focus", function(element, event)
		local retVal = nil
		if element.loseFocus then
			retVal = element:loseFocus(event)
		elseif element.super.loseFocus then
			retVal = element.super:loseFocus(event)
		end
		return retVal
	end)
	self:AddButtonCallbackFunction(self.OptionsList, controller, Enum.LUIButton.LUI_KEY_XBA_PSCROSS, "ENTER", function(element, menu, controller, model)
		ProcessListAction(self, element, controller)
		return true
	end, function(element, menu, controller)
		CoD.Menu.SetButtonLabel(menu, Enum.LUIButton.LUI_KEY_XBA_PSCROSS, "MENU_SELECT")
		return true
	end, false)
	
	-- Add fade animations to OptionsList
	self.OptionsList.clipsPerState = {
		DefaultState = {
			FadeIn = function()
				self.OptionsList:completeAnimation()
				self.OptionsList:setAlpha(1, 150)
			end,
			FadeOut = function()
				self.OptionsList:completeAnimation()
				self.OptionsList:setAlpha(0, 150)
			end
		}
	}
	
	self:addElement(self.OptionsList)
	self.OptionsList.id = "OptionsList"
	if USE_PAUSE_V2 then
		self.OptionsList:makeNotFocusable()
		TodV2Settings[ controller ] = nil   -- every open starts on the main page
	end

	-- [tod] CONTROLLER / ARROW-KEY NAVIGATION BETWEEN THE TWO LISTS (v17.26).
	-- The kit shipped the top icon row (SmallButtonList, horizontal) and the
	-- main button column (ButtonList, vertical) as two INDEPENDENT UILists with
	-- nothing linking them. A UIList only ever moves INSIDE itself: LUI.UIList.new
	-- registers LUI_KEY_UP/DOWN/LEFT/RIGHT callbacks that call navigateItem*(),
	-- and GridLayout.navigateItem* returns FALSE at the grid's edge, which leaves
	-- the press unhandled. Focus starts on the icon row (see the bottom of this
	-- function), so on a gamepad the stick walked the four icons and DOWN did
	-- NOTHING — Return To Game / Restart Level / Leave Game were unreachable
	-- without a mouse. Mouse HOVER focuses either list directly, which is the
	-- only reason this survived: it is a gamepad/keyboard-only bug, it is
	-- upstream's (map 1's copy of the kit has it too), and a KBM tester with a
	-- hand on the mouse can play the whole menu and never see it.
	--
	-- The framework's own linkage is LUI.UIElement.navigation — the
	-- {up=,down=,left=,right=} table stock menus set (e.g.
	-- StartMenu_Options_Controls_ButtonLayout wiring its list to its dropdown).
	-- We deliberately do NOT use it. A UIList hands each ITEM an empty navigation
	-- table and its own table is only reached after the press bubbles, so whether
	-- the list's internal move or the navigation hop wins depends on the relative
	-- order of two different input paths: the ButtonBits model subscriptions that
	-- drive buttonFunctions, and the gamepad_button event that drives
	-- handleGamepadButton. Lose that race and UP jumps out of the column from the
	-- middle instead of stepping a row. So instead we REPLACE the two edge
	-- callbacks — a second AddButtonCallbackFunction for the same element+button
	-- overwrites element.buttonFunctions[button] — and ONE handler owns each
	-- direction. Every handler tries the list's own move first and only hops when
	-- that returns false, so movement inside a list is byte-for-byte the stock
	-- behaviour.
	--
	-- The hop replays the two steps stock's doNavigationForElement performs —
	-- gain_focus on the target, then lose_focus on the source with
	-- ignoreFocusCheck — but it does NOT gate on the gain_focus RETURN VALUE the
	-- way stock does. The decompiled `LUI.UIList.gainFocus` is lossy (dead
	-- stores, no visible return), so what it hands back here is UNKNOWN, and a
	-- wrong guess either strands focus on nothing or leaves both lists lit. We
	-- gate on the OBSERVABLE post-condition instead: `hasListFocus`, the flag
	-- `UIList.loseFocus` and `setListItemInFocus` both read. If the target
	-- refuses, focus stays exactly where it was — the failure mode is "the press
	-- does nothing", which is today's behaviour, never a dead panel.
	--
	-- Guard: game-over mode makes SmallButtonList NOT focusable and the Game
	-- Settings page hides it, so TodHopLists refuses a non-focusable target and
	-- UP at the top of the column is simply inert in both — never a dead panel.
	local TodHopLists = function(from, to, hopController, dir)
		if to == nil or to.m_focusable == false then
			return false
		end
		local took = to:processEvent({
			name = "gain_focus",
			controller = hopController,
			button = dir
		})
		if took ~= true and to.hasListFocus ~= true then
			return false
		end
		from:processEvent({
			name = "lose_focus",
			controller = hopController,
			button = dir,
			ignoreFocusCheck = true
		})
		return true
	end

	self:AddButtonCallbackFunction(self.SmallButtonList, controller, Enum.LUIButton.LUI_KEY_DOWN, "DOWNARROW", function(element, menu, cbController, model)
		if self.SmallButtonList.m_disableNavigation then
			return false
		end
		if self.SmallButtonList:navigateItemDown() then
			return true
		end
		return TodHopLists(self.SmallButtonList, self.ButtonList, cbController, "down")
	end, nil, false)

	self:AddButtonCallbackFunction(self.ButtonList, controller, Enum.LUIButton.LUI_KEY_UP, "UPARROW", function(element, menu, cbController, model)
		if self.ButtonList.m_disableNavigation then
			return false
		end
		if self.ButtonList:navigateItemUp() then
			return true
		end
		return TodHopLists(self.ButtonList, self.SmallButtonList, cbController, "up")
	end, nil, false)

	-- Add fade animations to ButtonList and SmallButtonList
	self.ButtonList.clipsPerState = {
		DefaultState = {
			FadeIn = function()
				self.ButtonList:completeAnimation()
				self.ButtonList:setAlpha(1, 150)
			end,
			FadeOut = function()
				self.ButtonList:completeAnimation()
				self.ButtonList:setAlpha(0, 150)
			end
		}
	}
	
	self.SmallButtonList.clipsPerState = {
		DefaultState = {
			FadeIn = function()
				self.SmallButtonList:completeAnimation()
				self.SmallButtonList:setAlpha(1, 150)
			end,
			FadeOut = function()
				self.SmallButtonList:completeAnimation()
				self.SmallButtonList:setAlpha(0, 150)
			end
		}
	}
	
	-- Add fade animations to OptionsHeaderText
	self.OptionsHeaderText.clipsPerState = {
		DefaultState = {
			FadeIn = function()
				self.OptionsHeaderText:completeAnimation()
				self.OptionsHeaderText:setAlpha(1, 150)
			end,
			FadeOut = function()
				self.OptionsHeaderText:completeAnimation()
				self.OptionsHeaderText:setAlpha(0, 150)
			end
		}
	}

	-- Signature Images (optional)
	if ShowSignatures then
		self.KingsLayerKyleSignature = LUI.UIImage.new()
		self.KingsLayerKyleSignature:setLeftRight(true, false, 0, 125)
		self.KingsLayerKyleSignature:setTopBottom(true, false, 637, 720)
		self.KingsLayerKyleSignature:setImage(RegisterImage("i_mtl_ui_icon_kingslayer_kyle_signature"))
		self:addElement(self.KingsLayerKyleSignature)

		self.OwenC137Signature = LUI.UIImage.new()
		self.OwenC137Signature:setLeftRight(true, false, 128, 253)
		self.OwenC137Signature:setTopBottom(true, false, 637, 720)
		self.OwenC137Signature:setImage(RegisterImage("i_mtl_ui_icon_owenc137_signature"))
		self:addElement(self.OwenC137Signature)

		self.ShidouriSignature = LUI.UIImage.new()
		self.ShidouriSignature:setLeftRight(true, false, 255, 380)
		self.ShidouriSignature:setTopBottom(true, false, 637, 720)
		self.ShidouriSignature:setImage(RegisterImage("i_mtl_ui_icon_shidouri_signature"))
		self:addElement(self.ShidouriSignature)

		self.MadgazSignature = LUI.UIImage.new()
		self.MadgazSignature:setLeftRight(true, false, 383, 508)
		self.MadgazSignature:setTopBottom(true, false, 637, 720)
		self.MadgazSignature:setImage(RegisterImage("i_mtl_ui_icon_madgaz_signature"))
		self:addElement(self.MadgazSignature)

		-- V2: the target has no slot for the kit authors' credit; it is KEPT (never
		-- dropped silently), at 60% under the right panel (y 667..717), where the
		-- backdrop is empty. The user decides the final home (docs/180 difference 5).
		if USE_PAUSE_V2 then
			local sigs = { self.KingsLayerKyleSignature, self.OwenC137Signature, self.ShidouriSignature, self.MadgazSignature }
			for i = 1, #sigs do
				local l = 930 + ( i - 1 ) * 79
				sigs[ i ]:setLeftRight(true, false, l, l + 75)
				sigs[ i ]:setTopBottom(true, false, 650, 699.8)   -- under the right panel (ends 644), 125 x 83 aspect
				sigs[ i ]:setAlpha(0.7)
			end
		end
	end

	-- Button Callbacks
	self:AddButtonCallbackFunction(self, controller, Enum.LUIButton.LUI_KEY_XBB_PSCIRCLE, nil, function(element, menu, controller, model)
		RefreshLobbyRoom(menu, controller)
		StartMenuGoBack(menu, controller)
		return true
	end, function(element, menu, controller)
		CoD.Menu.SetButtonLabel(menu, Enum.LUIButton.LUI_KEY_XBB_PSCIRCLE, "MENU_BACK")
		return true
	end, false)

	self:AddButtonCallbackFunction(self, controller, Enum.LUIButton.LUI_KEY_START, "M", function(element, menu, controller, model)
		RefreshLobbyRoom(menu, controller)
		StartMenuGoBack(menu, controller)
		return true
	end, function(element, menu, controller)
		CoD.Menu.SetButtonLabel(menu, Enum.LUIButton.LUI_KEY_START, "MENU_DISMISS_MENU")
		return true
	end, false)

	self:AddButtonCallbackFunction(self, controller, Enum.LUIButton.LUI_KEY_NONE, "ESCAPE", function(element, menu, controller, model)
		RefreshLobbyRoom(menu, controller)
		StartMenuGoBack(menu, controller)
		return true
	end, function(element, menu, controller)
		CoD.Menu.SetButtonLabel(menu, Enum.LUIButton.LUI_KEY_NONE, "")
		return true
	end, false, true)

	self:processEvent({
		name = "menu_loaded",
		controller = controller
	})

	self:processEvent({
		name = "update_state",
		menu = self
	})

	-- [tod] game-over mode visuals (see TodGoActive above): retitle, hide the
	-- pause-only top row of settings icons (and take it out of focus navigation
	-- so up/down can never land on an invisible list), and put initial focus
	-- straight on the two-entry button list. One guarded block — a failure here
	-- may cost polish but can never take down the menu.
	local todGo = TodGoActive(controller)
	if todGo then
		pcall(function()
			self.PauseMenuText:setText(Engine.Localize("Game Over"))
			if self.TodPmTitle then
				self.TodPmTitle:setImage(RegisterImage("i_tod_pm_title_gameover"))
			end
			self.SmallButtonList:setAlpha(0)
		end)
		pcall(function()
			self.SmallButtonList:makeNotFocusable()
		end)
	end

	if todGo then
		self.ButtonList:processEvent({
			name = "gain_focus",
			controller = controller
		})
	elseif not self:restoreState() then
		-- Give initial focus to small buttons
		self.SmallButtonList:processEvent({
			name = "gain_focus",
			controller = controller
		})
	end

	if PostLoadFunc then
		PostLoadFunc(self, controller)
	end

	LUI.OverrideFunction_CallOriginalSecond(self, "close", function(element)
		-- The old fixed list omitted OptionsList, upgrade plates/pips/text and
		-- the controls legend. Close every direct child, including locals that
		-- have no named member. UIList.close also releases its item bindings.
		local child = element:getFirstChild()
		while child do
			local nextChild = child:getNextSibling()
			child:close()
			child = nextChild
		end
		Engine.UnsubscribeAndFreeModel(Engine.GetModel(Engine.GetModelForController(controller), "StartMenu_Main.buttonPrompts"))
	end)

	return self
end
