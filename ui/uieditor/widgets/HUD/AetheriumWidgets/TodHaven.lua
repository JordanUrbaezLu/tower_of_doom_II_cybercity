-- =============================================================================
-- TodHaven.lua — THE HAVENS' screen effect, the safe zones' half you SEE (docs/202).
--
-- User 2026-10-02: the safe zones "need to act more like a safe zone ... a force
-- field that animates when you walk in and walk out. And maybe has a small visual
-- effect on your screen". User 2026-10-03 (v3): the haven is EVIL until its
-- guardians are dead - "two distinct states. One when its not safe and one when
-- it is after defeating them."
--
-- _tod_haven.gsc owns membership; this widget only draws what it is told, on the
-- zero-bit tod_haven / tod_haven_hit / tod_haven_state events (the clientuimodel
-- pool is full):
--     tod_haven ( inside, flags, state, left )
--                     inside 1/0; flags bit 0 = a real crossing (play the pulse),
--                     bit 1 = show the "what it does" lines; state 1 = CORRUPTED,
--                     2 = SAFE; left = guardians still to kill (corrupted)
--     tod_haven_hit ( 1 )   a hit landed while a safe field held: a quick flicker
--     tod_haven_state ( kind, floor, left )
--                     a banner: 1 = the guardians rise, 3 = a guardian down (left),
--                     2 = the haven secured (everyone hears this one; left = 1 when YOU
--                     are on its floor: the bigger flash), and the purification's beats
--                     (v5) for the players on its floor: 4 = the convulsion began,
--                     6 = one strobe of it (left = its index), 5 = the collapse
--
-- What the player sees:
--   * INSIDE A SAFE FIELD: the field's tint at the screen's edges — a cyan vignette
--     threaded with the dome's own hex lattice and a fine scanline (i_tod_haven_vignette,
--     white art tinted here), steady and quiet so it never fights the fight.
--   * CROSSING IN: the edges flash white-cyan and settle into the tint; SAFE ZONE
--     rises at the top centre in the map's typeface (the first few times with
--     ENEMIES SLOWED - DAMAGE REDUCED and KILLS PAY 25 PERCENT under it) and fades
--     away. (The typeface has no percent sign, so the word is spelled out.)
--   * INSIDE A CORRUPTED FIELD: the same vignette in the field's hostile RED, and
--     CORRUPTED HAVEN with DEFEAT THE GUARDIANS - N LEFT (the count follows the
--     fight). No safe lines, no hit flicker: the evil field does nothing for you.
--   * THE DARKNESS (v4, user 2026-10-03: "Going inside will make your screen dark like
--     you are being taken over by the darkness. Not crazy but for sure noticable and
--     sligtly annoying. But of course once its a safe zone its fine"): inside a
--     CORRUPTED field a near-black smoky veil (i_tod_haven_darkness: a dim centre, heavy
--     edges, tendrils creeping in) takes the screen over DARK_IN_MS, then BREATHES
--     (full -> DARK_LO -> full, DARK_BREATH_MS each way) for as long as you stay; it
--     lifts over DARK_OUT_MS the moment you leave or the haven is taken (the server
--     plays the swallow and the heartbeat to the same player).
--   * THE BANNERS: FLOOR N GUARDIANS RISE when they wake, GUARDIAN DOWN - N LEFT
--     as they fall, FLOOR N HAVEN SECURED - SAFE ZONE ONLINE when the last one does
--     (with a cyan flash; the tint turns cyan in place if you are standing inside).
--   * THE PURIFICATION (v5, user 2026-10-04: "the transition of purification to be
--     nicely animated"): standing inside when the last guardian falls, the veil GRIPS
--     (the breath stops, the darkness holds full) and the edges flicker red with every
--     STROBE of the dome, in step with the heart's flashes and the sound's clicks
--     (FLOOR N PURIFYING over it); at THE COLLAPSE the screen goes BLACK for VOID_MS
--     (the void, a plain fill over everything but the text), then the SECURED banner's
--     full white-cyan flash comes through as the darkness lifts and the tint turns cyan
--     in place. On the floor but outside the dome: the banner and the bigger SECURED
--     flash only; elsewhere the SECURED banner with its ordinary pulse.
--   * CROSSING OUT: one last flash of the edges as the tint drains away.
--   * HIT INSIDE (safe): the edges flicker brighter for a beat — the field took a third.
--
-- IDEMPOTENT: the server re-sends the state every 2 s to hydrate a rebuilt HUD; a
-- re-send with the same state and no pulse flag changes nothing on screen (a
-- changed guardian count only updates the line). First child of AetheriumHud, so
-- every readout draws over it; elements are built once and only tweened (the
-- element-pool rules, docs/133 / docs/142).
-- =============================================================================

require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership" )
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphText" )

-- LOCKSTEP _tod_haven.gsc TOD_HAVEN_HUD_PULSE / TOD_HAVEN_HUD_HINT / TOD_HAVEN_STATE_* / TOD_HAVEN_BANNER_*
local FLAG_PULSE = 1
local FLAG_HINT = 2
local STATE_CORRUPT = 1
local STATE_SAFE = 2
local BANNER_WAKE = 1
local BANNER_SECURED = 2
local BANNER_DOWN = 3
local BANNER_PURGE = 4                   -- v5: the convulsion began
local BANNER_COLLAPSE = 5                -- v5: the collapse (the void)
local BANNER_STROBE = 6                  -- v5: one strobe of the convulsion
-- THE PURIFICATION's screen half (v5). LOCKSTEP _tod_haven.gsc: VOID_MS = TOD_HAVEN_PURGE_VOID_SECS x 1000
local VOID_MS = 350                      -- black for the players inside, from the collapse
local VOID_IN_MS, VOID_OUT_MS = 40, 260  -- the black snaps in and clears into the bloom
local GRIP_MS = 250                      -- the veil tightens to full at the convulsion's start
local STROBE_A, STROBE_IN_MS, STROBE_OUT_MS = 0.5, 30, 160   -- the red flicker per strobe of the dome
local PURGE_HOLD_MS = 1500               -- FLOOR N PURIFYING holds this long (the SECURED banner follows it)
local NEAR_PULSE_OUT_MS = 900            -- the SECURED flash for the players on the floor: full, and slower to clear

local TINT = { 0.30, 0.90, 1.00 }        -- the safe field's cyan (fx_tod_haven_*, the dome texture)
local HOT = { 0.80, 1.00, 1.00 }         -- the safe crossing flash
local DARK = { 1.00, 0.20, 0.12 }        -- the corrupted field's red (fx_tod_haven_corrupt, the dark dome)
local DARK_HOT = { 1.00, 0.50, 0.32 }    -- its flash
local IDLE_A, DARK_IDLE_A = 0.34, 0.24   -- the steady tint while inside (safe / corrupted: lower, the darkness carries the mood)
local DARK_VEIL = { 0.035, 0.0, 0.025 }  -- the darkness (v4): near-black with a breath of the corruption's red
local DARK_HI, DARK_LO = 1.0, 0.8        -- its breathing range (the image itself is 0.17 at the centre, 0.8 at the edges)
local DARK_IN_MS, DARK_OUT_MS, DARK_BREATH_MS = 900, 600, 1800
local TINT_IN_MS, TINT_OUT_MS = 380, 520
local PULSE_A, PULSE_IN_MS, PULSE_OUT_MS = 0.72, 70, 540
local HIT_A, HIT_IN_MS, HIT_OUT_MS = 0.45, 40, 230
local CUT_A = 0.6                        -- THE DEALER'S HOUSE (docs/207): one bite of the drain, inside his dome
local LABEL_IN_MS, LABEL_HOLD_MS, LABEL_OUT_MS = 160, 1700, 480
local BANNER_HOLD_MS = 2600

CoD.TodHaven = InheritFrom( LUI.UIElement )

function CoD.TodHaven.new( HudRef, InstanceRef )
	local self = LUI.UIElement.new()
	CoD.TodUIOwnership.Attach( self )
	self:setClass( CoD.TodHaven )
	self.id = "TodHaven"
	self:setLeftRight( true, true, 0, 0 )
	self:setTopBottom( true, true, 0, 0 )

	-- the darkness (v4): under the tint, so the corrupted field's red lattice reads over the veil
	local Dark = LUI.UIImage.new()
	Dark.id = "TodHavenDark"
	Dark:setLeftRight( true, true, 0, 0 )
	Dark:setTopBottom( true, true, 0, 0 )
	Dark:setImage( RegisterImage( "i_tod_haven_darkness" ) )
	Dark:setRGB( DARK_VEIL[ 1 ], DARK_VEIL[ 2 ], DARK_VEIL[ 3 ] )
	Dark:setAlpha( 0 )
	self:addElement( Dark )

	-- the steady tint (inside)
	local Tint = LUI.UIImage.new()
	Tint.id = "TodHavenTint"
	Tint:setLeftRight( true, true, 0, 0 )
	Tint:setTopBottom( true, true, 0, 0 )
	Tint:setImage( RegisterImage( "i_tod_haven_vignette" ) )
	Tint:setRGB( TINT[ 1 ], TINT[ 2 ], TINT[ 3 ] )
	Tint:setAlpha( 0 )
	self:addElement( Tint )

	-- the crossing flash and the hit flicker (one element: a new beat interrupts the old)
	local Pulse = LUI.UIImage.new()
	Pulse.id = "TodHavenPulse"
	Pulse:setLeftRight( true, true, 0, 0 )
	Pulse:setTopBottom( true, true, 0, 0 )
	Pulse:setImage( RegisterImage( "i_tod_haven_vignette" ) )
	Pulse:setRGB( HOT[ 1 ], HOT[ 2 ], HOT[ 3 ] )
	Pulse:setAlpha( 0 )
	self:addElement( Pulse )

	-- THE VOID (v5): a plain black fill (no image: a bare UIImage draws solid, the jump scene's
	-- letterbox bars) over the tint and the pulse, under the text; it snaps in at the collapse
	-- for the players inside and clears into the bloom
	local Void = LUI.UIImage.new()
	Void.id = "TodHavenVoid"
	Void:setLeftRight( true, true, 0, 0 )
	Void:setTopBottom( true, true, 0, 0 )
	Void:setRGB( 0, 0, 0 )
	Void:setAlpha( 0 )
	self:addElement( Void )

	-- the label + two lines under it, in the map's typeface (text fallback: none —
	-- every glyph here is in the set, so the rows always draw)
	local Label, Hint, Hint2
	if CoD.TodGlyphText then
		Label = CoD.TodGlyphText.new( { left = 360, right = 920, top = 94, bottom = 120, align = "center", pool = 24 } )
		Label:setRGB( HOT[ 1 ], HOT[ 2 ], HOT[ 3 ] )
		Label:setText( "SAFE ZONE" )
		Label:setAlpha( 0 )
		self:addElement( Label )
		Hint = CoD.TodGlyphText.new( { left = 390, right = 890, top = 124, bottom = 138, align = "center", pool = 32 } )
		Hint:setRGB( TINT[ 1 ], TINT[ 2 ], TINT[ 3 ] )
		Hint:setText( "ENEMIES SLOWED - DAMAGE REDUCED" )
		Hint:setAlpha( 0 )
		self:addElement( Hint )
		-- the cost of sitting inside (user 2026-10-02: "Kills inside a zone are at 25% money")
		Hint2 = CoD.TodGlyphText.new( { left = 390, right = 890, top = 142, bottom = 156, align = "center", pool = 32 } )
		Hint2:setRGB( TINT[ 1 ], TINT[ 2 ], TINT[ 3 ] )
		Hint2:setText( "KILLS PAY 25 PERCENT" )
		Hint2:setAlpha( 0 )
		self:addElement( Hint2 )
	end

	local st = { inside = false, state = 0, left = 0, pulsing = false, dark = false, breathLow = false, gripped = false }

	local function palette( state )
		if state == STATE_CORRUPT then
			return DARK, DARK_HOT, DARK_IDLE_A
		end
		return TINT, HOT, IDLE_A
	end

	local function tintTo( a, ms )
		Tint:beginAnimation( "tod_haven_tint", ms, false, false, CoD.TweenType.Linear )
		Tint:setAlpha( a )
	end

	-- THE DARKNESS: in -> breathe (lo, hi, lo, ...) while it holds -> out. One element, tweened only.
	-- (v5: the purification GRIPS it - the breath stops and the veil holds full until it lifts)
	local function breathe()
		if not st.dark or st.gripped then
			return
		end
		st.breathLow = not st.breathLow
		Dark:beginAnimation( "tod_haven_dark_breathe", DARK_BREATH_MS, false, false, CoD.TweenType.Linear )
		Dark:setAlpha( st.breathLow and DARK_LO or DARK_HI )
	end
	Dark:registerEventHandler( "transition_complete_tod_haven_dark_in", function ( element, event )
		if event and event.interrupted then
			return
		end
		breathe()
	end )
	Dark:registerEventHandler( "transition_complete_tod_haven_dark_breathe", function ( element, event )
		if event and event.interrupted then
			return
		end
		breathe()
	end )
	local function darkTo( on )
		if on and not st.dark then
			st.dark, st.breathLow, st.gripped = true, false, false
			Dark:beginAnimation( "tod_haven_dark_in", DARK_IN_MS, false, false, CoD.TweenType.Linear )
			Dark:setAlpha( DARK_HI )
		elseif not on and st.dark then
			st.dark, st.gripped = false, false
			Dark:beginAnimation( "tod_haven_dark_out", DARK_OUT_MS, false, false, CoD.TweenType.Linear )
			Dark:setAlpha( 0 )
		end
	end
	-- THE GRIP (v5): the convulsion tightens the veil to full and holds it there (no breath) until it lifts
	local function grip()
		if not st.dark then
			return
		end
		st.gripped = true
		Dark:beginAnimation( "tod_haven_dark_grip", GRIP_MS, false, false, CoD.TweenType.Linear )
		Dark:setAlpha( DARK_HI )
	end

	-- THE VOID (v5): black snaps in at the collapse, holds for the void, clears into the bloom
	local function voidIn()
		Void:beginAnimation( "tod_haven_void_in", VOID_IN_MS, false, false, CoD.TweenType.Linear )
		Void:setAlpha( 1 )
	end
	Void:registerEventHandler( "transition_complete_tod_haven_void_in", function ( element, event )
		if event and event.interrupted then
			return
		end
		Void:beginAnimation( "tod_haven_void_hold", VOID_MS - VOID_IN_MS, false, false, CoD.TweenType.Linear )
		Void:setAlpha( 1 )
	end )
	Void:registerEventHandler( "transition_complete_tod_haven_void_hold", function ( element, event )
		if event and event.interrupted then
			return
		end
		Void:beginAnimation( "tod_haven_void_out", VOID_OUT_MS, false, false, CoD.TweenType.Linear )
		Void:setAlpha( 0 )
	end )

	local function pulse( peak, inMs, outMs, rgb )
		st.pulsing = true
		st.pulseOut = outMs
		Pulse:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
		Pulse:beginAnimation( "tod_haven_pulse_in", inMs, false, false, CoD.TweenType.Linear )
		Pulse:setAlpha( peak )
	end
	Pulse:registerEventHandler( "transition_complete_tod_haven_pulse_in", function ( element, event )
		if event and event.interrupted then
			return
		end
		Pulse:beginAnimation( "tod_haven_pulse_out", st.pulseOut or PULSE_OUT_MS, false, false, CoD.TweenType.Linear )
		Pulse:setAlpha( 0 )
	end )
	Pulse:registerEventHandler( "transition_complete_tod_haven_pulse_out", function ( element, event )
		if event and event.interrupted then
			return
		end
		st.pulsing = false
	end )

	-- the label: in -> hold -> out, a three-step chain on its own element; the two
	-- lines ride it (an empty line stays hidden)
	local function labelShow( text, line1, line2, rgb, lineRgb, holdMs )
		if not Label then
			return
		end
		st.hold = holdMs or LABEL_HOLD_MS
		Label:setText( text )
		Label:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
		Label:beginAnimation( "tod_haven_label_in", LABEL_IN_MS, false, false, CoD.TweenType.Linear )
		Label:setAlpha( 1 )
		if Hint then
			Hint:setText( line1 or "" )
			Hint:setRGB( lineRgb[ 1 ], lineRgb[ 2 ], lineRgb[ 3 ] )
			Hint:beginAnimation( "tod_haven_hint_in", LABEL_IN_MS, false, false, CoD.TweenType.Linear )
			Hint:setAlpha( ( line1 and line1 ~= "" ) and 0.9 or 0 )
		end
		if Hint2 then
			Hint2:setText( line2 or "" )
			Hint2:setRGB( lineRgb[ 1 ], lineRgb[ 2 ], lineRgb[ 3 ] )
			Hint2:beginAnimation( "tod_haven_hint2_in", LABEL_IN_MS, false, false, CoD.TweenType.Linear )
			Hint2:setAlpha( ( line2 and line2 ~= "" ) and 0.9 or 0 )
		end
	end
	local function labelHide( ms )
		if not Label then
			return
		end
		Label:beginAnimation( "tod_haven_label_out", ms, false, false, CoD.TweenType.Linear )
		Label:setAlpha( 0 )
		if Hint then
			Hint:beginAnimation( "tod_haven_hint_out", ms, false, false, CoD.TweenType.Linear )
			Hint:setAlpha( 0 )
		end
		if Hint2 then
			Hint2:beginAnimation( "tod_haven_hint2_out", ms, false, false, CoD.TweenType.Linear )
			Hint2:setAlpha( 0 )
		end
	end
	if Label then
		Label:registerEventHandler( "transition_complete_tod_haven_label_in", function ( element, event )
			if event and event.interrupted then
				return
			end
			Label:beginAnimation( "tod_haven_label_hold", st.hold or LABEL_HOLD_MS, false, false, CoD.TweenType.Linear )
			Label:setAlpha( 1 )
		end )
		Label:registerEventHandler( "transition_complete_tod_haven_label_hold", function ( element, event )
			if event and event.interrupted then
				return
			end
			labelHide( LABEL_OUT_MS )
		end )
	end

	-- the field's own lines for a state
	local function fieldLines( state, left, withHint )
		if state == STATE_CORRUPT then
			local line = "DEFEAT ITS GUARDIANS"
			if left and left > 0 then
				line = "DEFEAT THE GUARDIANS - " .. left .. " LEFT"
			end
			return "CORRUPTED HAVEN", line, ""
		end
		if withHint then
			return "SAFE ZONE", "ENEMIES SLOWED - DAMAGE REDUCED", "KILLS PAY 25 PERCENT"
		end
		return "SAFE ZONE", "", ""
	end

	local function setInside( inside, flags, state, left )
		-- flags is 0..3: bit 0 the crossing pulse, bit 1 the hint lines
		local crossing = ( flags % 2 ) == 1
		local hint = ( math.floor( flags / 2 ) % 2 ) == 1
		if state ~= STATE_CORRUPT and state ~= STATE_SAFE then
			state = STATE_SAFE
		end
		left = left or 0
		if inside then
			local tint, hot, idle = palette( state )
			if not st.inside then
				-- a crossing in (or a respawn / teleport inside: no pulse flag, the tint still rises)
				st.inside, st.state, st.left = true, state, left
				Tint:setRGB( tint[ 1 ], tint[ 2 ], tint[ 3 ] )
				tintTo( idle, TINT_IN_MS )
				darkTo( state == STATE_CORRUPT )
				if crossing then
					pulse( PULSE_A, PULSE_IN_MS, PULSE_OUT_MS, hot )
					local a, b, c = fieldLines( state, left, hint )
					labelShow( a, b, c, hot, tint )
				end
			elseif state ~= st.state then
				-- the field changed under your feet: the cleanse (corrupted -> safe). The
				-- banner already said HAVEN SECURED; the tint turns cyan in place and the
				-- darkness lifts.
				st.state, st.left = state, left
				Tint:setRGB( tint[ 1 ], tint[ 2 ], tint[ 3 ] )
				tintTo( idle, TINT_IN_MS )
				darkTo( state == STATE_CORRUPT )
				if crossing then
					pulse( PULSE_A, PULSE_IN_MS, PULSE_OUT_MS, hot )
				end
			elseif state == STATE_CORRUPT and left ~= st.left then
				-- the count moved: the line follows, no pulse
				st.left = left
				local a, b, c = fieldLines( state, left, false )
				labelShow( a, b, c, hot, tint )
			end
			-- a plain re-send: the screen already shows this state
		else
			if not st.inside then
				return   -- a re-send of "outside"
			end
			local tint, hot = palette( st.state )
			st.inside, st.state, st.left = false, 0, 0
			tintTo( 0, TINT_OUT_MS )
			darkTo( false )
			labelHide( 200 )
			if crossing then
				pulse( PULSE_A * 0.7, PULSE_IN_MS, PULSE_OUT_MS, hot )
			end
		end
	end

	local function banner( kind, floor, left )
		floor = floor or 0
		left = left or 0
		local insideCorrupt = st.inside and st.state == STATE_CORRUPT
		if kind == BANNER_WAKE then
			labelShow( "FLOOR " .. floor .. " GUARDIANS RISE", "DEFEAT THEM TO SECURE THE HAVEN", "", DARK_HOT, DARK, BANNER_HOLD_MS )
			if not st.pulsing then
				pulse( 0.55, PULSE_IN_MS, PULSE_OUT_MS, DARK_HOT )
			end
		elseif kind == BANNER_DOWN then
			local line = "ONE LEFT"
			if left > 1 then
				line = left .. " LEFT"
			end
			labelShow( "GUARDIAN DOWN", line, "", DARK_HOT, DARK, LABEL_HOLD_MS )
			if not st.pulsing then
				pulse( 0.35, PULSE_IN_MS, HIT_OUT_MS, DARK_HOT )
			end
		elseif kind == BANNER_SECURED then
			labelShow( "FLOOR " .. floor .. " HAVEN SECURED", "SAFE ZONE ONLINE", "ENEMIES SLOWED - DAMAGE REDUCED", HOT, TINT, BANNER_HOLD_MS )
			if left == 1 then
				pulse( 1.0, PULSE_IN_MS, NEAR_PULSE_OUT_MS, HOT )   -- you are on its floor: the full flash (v5)
			else
				pulse( PULSE_A, PULSE_IN_MS, PULSE_OUT_MS, HOT )
			end
		elseif kind == BANNER_PURGE then
			-- THE CONVULSION (v5): the veil grips and the edges flicker for the players inside; the floor reads the line
			labelShow( "FLOOR " .. floor .. " PURIFYING", "THE LAST GUARDIAN HAS FALLEN", "", DARK_HOT, DARK, PURGE_HOLD_MS )
			if insideCorrupt then
				grip()
				pulse( STROBE_A, STROBE_IN_MS, STROBE_OUT_MS, DARK_HOT )
			end
		elseif kind == BANNER_STROBE then
			-- one strobe of the dome: a red flicker in step with it (a new strobe interrupts the last)
			if insideCorrupt then
				pulse( STROBE_A, STROBE_IN_MS, STROBE_OUT_MS, DARK_HOT )
			end
		elseif kind == BANNER_COLLAPSE then
			-- THE COLLAPSE (v5): black for the void, for the players inside; the SECURED banner follows
			labelHide( 120 )
			if insideCorrupt then
				voidIn()
			end
		end
	end

	self:subscribeToGlobalModel( InstanceRef, "PerController", "scriptNotify", function ( model )
		local name = Engine.GetModelValue( model )
		if name == "tod_haven" then
			local d = CoD.GetScriptNotifyData( model ) or {}
			setInside( ( d[ 1 ] or 0 ) == 1, d[ 2 ] or 0, d[ 3 ] or 0, d[ 4 ] or 0 )
		elseif name == "tod_haven_hit" then
			if st.inside and st.state == STATE_SAFE and not st.pulsing then
				pulse( HIT_A, HIT_IN_MS, HIT_OUT_MS, HOT )
			end
		elseif name == "tod_house_cut" then
			-- THE DEALER'S HOUSE (docs/207): one bite of the drain, inside his corrupted dome: a red flicker
			if st.inside and st.state == STATE_CORRUPT and not st.pulsing then
				pulse( CUT_A, HIT_IN_MS, HIT_OUT_MS, DARK_HOT )
			end
		elseif name == "tod_haven_state" then
			local d = CoD.GetScriptNotifyData( model ) or {}
			banner( d[ 1 ] or 0, d[ 2 ] or 0, d[ 3 ] or 0 )
		end
	end )

	LUI.OverrideFunction_CallOriginalSecond( self, "close", function ( element )
		st.inside = false
		st.state = 0
		st.pulsing = false
		st.dark = false   -- a breathe completing after the close does nothing
		st.gripped = false
	end )

	return self
end
