-- =============================================================================
-- TodArena.lua — THE BATTLE ARENA's readout (docs/185 v2.1 / v2.2): the fight you can read.
--
-- User 2026-10-03: "Give the arena one more pass from a players perspective".
-- The first thing a player asks in a wave fight is "how many are left?" and the
-- second is "which wave is this?". _tod_arena.gsc answers both on the zero-bit
-- tod_arena event (the clientuimodel pool is full):
--     tod_arena ( show, level, levels, wave, waves, left, flags )
--         show 1/0; wave 0 = the breath before wave 1; left = enemies still to kill
--         in this wave (not yet risen + still up); flags bit 0 = a wave just began,
--         bit 1 = the wave was just cleared, bit 3 = the level is cleared, bit 4 =
--         THE DEALER'S HOUSE, bit 5 = THE DEALER lives (LOCKSTEP _tod_arena.gsc
--         TOD_ARENA_HUD_*). Bit 2 (THE KEEPER lives) retired with the Keeper,
--         2026-10-05: a stale bit 2 draws nothing of its own.
--
-- What the player sees, top centre, in the map's typeface:
--     WAVE 2 OF 3                 cyan (GET READY in the breath before wave 1)
--     14 LEFT                     white, the biggest line; RED at HOT or fewer (hunt
--                                 them); WAVE CLEARED / LEVEL CLEARED in gold; THE
--                                 DEALER in red while he lives
-- THE LEVEL IS NOT HERE (v2.2, user 2026-10-03: "replace the round HUD with Battle
-- Arena / Level 1 ... rounds dont count in there"): the HUD V2 round badge
-- (tod_upgrade.lua's status plate) reads the SAME event and wears BATTLE ARENA /
-- LEVEL n for the whole fight, where the round used to be. This widget carries the
-- wave and the count only; the level argument is read and passed through untouched.
-- A wave's start flashes the wave line and the count; every kill ticks the count;
-- the readout fades away when the party rides home.
--
-- IDEMPOTENT: the server re-sends the state every 2 s to hydrate a rebuilt HUD; a
-- re-send with the same state and no flags changes nothing on screen. A child of
-- AetheriumHud (hidden with the rest of the HUD: the card deal's veil covers it);
-- elements are built once and only tweened (the element-pool rules, docs/133 / 142).
-- =============================================================================

require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership" )
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphText" )

-- LOCKSTEP _tod_arena.gsc TOD_ARENA_HUD_WAVE / _CLEARED / _LEVEL / _HOUSE / _DEALER / TOD_ARENA_HUD_HOT
-- (4 was _BOSS, THE KEEPER: retired with him 2026-10-05; the value stays unused)
local FLAG_WAVE = 1
local FLAG_CLEARED = 2
local FLAG_LEVEL = 8
local FLAG_HOUSE = 16    -- THE DEALER'S HOUSE (docs/207): the wave line reads THE FINAL FIGHT
local FLAG_DEALER = 32   -- THE DEALER lives (the count line names him)
local HOT = 3

local GOLD = { 1.00, 0.84, 0.46 }
local CYAN = { 0.30, 0.90, 1.00 }
local WHITE = { 0.96, 0.98, 1.00 }
local RED = { 1.00, 0.32, 0.24 }
local DIM = 0.80                              -- a row's resting alpha while the readout shows
local IN_MS, OUT_MS = 260, 420
local FLASH_IN_MS, FLASH_OUT_MS = 60, 520     -- a wave begins / is cleared: up to full, then settle
local TICK_IN_MS, TICK_OUT_MS = 40, 180       -- a kill: a short tick on the count

CoD.TodArena = InheritFrom( LUI.UIElement )

-- flags is 0..15, the four bits above (no bitwise operators in this Lua)
local function hasFlag( flags, bit )
	return math.floor( flags / bit ) % 2 == 1
end

function CoD.TodArena.new( HudRef, InstanceRef )
	local self = LUI.UIElement.new()
	CoD.TodUIOwnership.Attach( self )
	self:setClass( CoD.TodArena )
	self.id = "TodArena"
	self:setLeftRight( true, true, 0, 0 )
	self:setTopBottom( true, true, 0, 0 )

	-- two rows in the map's typeface (text fallback: none — every glyph here is in the set)
	local Wave, Count
	if CoD.TodGlyphText then
		Wave = CoD.TodGlyphText.new( { left = 440, right = 840, top = 44, bottom = 64, align = "center", pool = 14 } )
		Wave:setRGB( CYAN[ 1 ], CYAN[ 2 ], CYAN[ 3 ] )
		Wave:setAlpha( 0 )
		self:addElement( Wave )
		Count = CoD.TodGlyphText.new( { left = 390, right = 890, top = 68, bottom = 106, align = "center", pool = 14 } )
		Count:setRGB( WHITE[ 1 ], WHITE[ 2 ], WHITE[ 3 ] )
		Count:setAlpha( 0 )
		self:addElement( Count )
	end

	local st = { show = false, wave = "", line = "", settle = {} }

	local function fadeTo( el, a, ms, name )
		if not el then
			return
		end
		el:beginAnimation( name, ms, false, false, CoD.TweenType.Linear )
		el:setAlpha( a )
	end
	-- the resting alpha of a row: DIM while the readout shows (0 for an empty count line)
	local function restOf( el )
		if not st.show then
			return 0
		end
		if el == Count and st.line == "" then
			return 0
		end
		return DIM
	end
	-- a flash: up to full at once, then settle back (a two-step chain on the element)
	local function flash( el, name, inMs, outMs )
		if not el then
			return
		end
		st.settle[ name ] = outMs
		el:beginAnimation( name .. "_in", inMs, false, false, CoD.TweenType.Linear )
		el:setAlpha( 1 )
	end
	local function settleOn( el, name )
		if not el then
			return
		end
		el:registerEventHandler( "transition_complete_" .. name .. "_in", function ( element, event )
			if event and event.interrupted then
				return
			end
			el:beginAnimation( name .. "_out", st.settle[ name ] or FLASH_OUT_MS, false, false, CoD.TweenType.Linear )
			el:setAlpha( restOf( el ) )
		end )
	end
	settleOn( Wave, "tod_arena_wave" )
	settleOn( Count, "tod_arena_count" )

	local function hide()
		if not st.show then
			return   -- a re-send: already hidden
		end
		st.show = false
		st.wave, st.line = "", ""
		fadeTo( Wave, 0, OUT_MS, "tod_arena_wave_out" )
		fadeTo( Count, 0, OUT_MS, "tod_arena_count_out" )
	end

	local function apply( show, lvl, levels, wave, waves, left, flags )
		if show ~= 1 then
			hide()
			return
		end
		local dealer = hasFlag( flags, FLAG_DEALER )
		local house = hasFlag( flags, FLAG_HOUSE )
		local started = hasFlag( flags, FLAG_WAVE )
		local cleared = hasFlag( flags, FLAG_CLEARED ) or hasFlag( flags, FLAG_LEVEL )
		local line, rgb
		if hasFlag( flags, FLAG_LEVEL ) then
			line, rgb = "LEVEL CLEARED", GOLD
		elseif dealer then
			line, rgb = "THE DEALER", RED
		elseif house then
			line, rgb = "", WHITE   -- the house between his rise and his death: nothing to count
		elseif wave > 0 and ( hasFlag( flags, FLAG_CLEARED ) or left <= 0 ) then
			line, rgb = "WAVE CLEARED", GOLD
		elseif wave > 0 then
			line, rgb = tostring( left ) .. " LEFT", ( left <= HOT ) and RED or WHITE
		else
			line, rgb = "", WHITE
		end
		local waveLine = ( wave > 0 ) and ( "WAVE " .. tostring( wave ) .. " OF " .. tostring( waves ) ) or "GET READY"
		if house then
			waveLine = "THE FINAL FIGHT"   -- THE DEALER'S HOUSE (docs/207)
		end
		if st.show and line == st.line and waveLine == st.wave and not started and not cleared then
			return   -- a re-send: the screen already shows this
		end
		local fresh = not st.show
		local ticked = st.show and line ~= st.line and not started and not cleared
		local countWasEmpty = ( st.line == "" )
		st.show = true
		st.wave, st.line = waveLine, line
		if Wave then
			Wave:setText( waveLine )
		end
		if Count then
			Count:setText( line )
			Count:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
		end
		if fresh then
			fadeTo( Wave, DIM, IN_MS, "tod_arena_wave_out" )
			fadeTo( Count, restOf( Count ), IN_MS, "tod_arena_count_out" )
		end
		if started then
			flash( Wave, "tod_arena_wave", FLASH_IN_MS, FLASH_OUT_MS )
			flash( Count, "tod_arena_count", FLASH_IN_MS, FLASH_OUT_MS )
		elseif cleared then
			flash( Count, "tod_arena_count", FLASH_IN_MS, FLASH_OUT_MS )
		elseif ticked then
			flash( Count, "tod_arena_count", TICK_IN_MS, TICK_OUT_MS )
		elseif not fresh and countWasEmpty and line ~= "" then
			fadeTo( Count, DIM, IN_MS, "tod_arena_count_out" )
		elseif not fresh and line == "" then
			fadeTo( Count, 0, OUT_MS, "tod_arena_count_out" )
		end
	end

	self:subscribeToGlobalModel( InstanceRef, "PerController", "scriptNotify", function ( model )
		local name = Engine.GetModelValue( model )
		if name ~= "tod_arena" then
			return
		end
		local d = CoD.GetScriptNotifyData( model ) or {}
		apply( d[ 1 ] or 0, d[ 2 ] or 0, d[ 3 ] or 0, d[ 4 ] or 0, d[ 5 ] or 0, d[ 6 ] or 0, d[ 7 ] or 0 )
	end )

	LUI.OverrideFunction_CallOriginalSecond( self, "close", function ( element )
		st.show = false
		st.wave, st.line = "", ""
	end )

	return self
end
