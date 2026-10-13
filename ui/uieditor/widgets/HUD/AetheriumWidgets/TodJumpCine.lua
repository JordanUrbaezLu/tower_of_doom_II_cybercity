-- =============================================================================
-- TodJumpCine.lua — THE FIRST JUMP'S OPENING SCENE, the screen half (docs/196).
--
-- User 2026-09-29: the crown -> tower jump should play "like an opening scene
-- but only on the first time they use the jump pad". _tod_jumppad.gsc owns the
-- whole timeline (the camera turns to the sky's TOWER OF DOOM II sign, holds it,
-- swings back to the tower); this widget only draws the two letterbox bars and
-- holds the shared HUD veil (CoD.TodHudVeil, key "jump") while the server says so:
--     tod_jump_cine ( 1 )   bars in, HUD hidden
--     tod_jump_cine ( 0 )   bars out, HUD back
--     tod_jump_cine ( 2 )   THE IMPACT (user 2026-09-29: two ships "crash into each other they do
--                           a huge explosion so you can't see anything and then behind is actually
--                           the tower of doom sign all lit up completely bright"): a white-hot flash
--                           that HOLDS at full white for a quarter second (the hulls go and the sign's
--                           glows come on behind it, _tod_jump_title.csc), then burns out through orange
--                           in ~0.75 s onto THE FIREBALL, which then fills the frame for seconds (user,
--                           after the first play: "the kaboom ended early" - the white used to hide it)
-- The flash lives UNDER the bars (added first), so the letterbox stays black through it.
-- A DUMB RENDERER: the server sends 0 on every exit path (the end of the shot, a
-- card deal taking the screen, death, the flight ending under the scene). Belt
-- and braces: a WATCHDOG drops the bars and the veil if the 0 never arrives, and
-- closing the HUD (death -> spectate, a rebuild) releases the veil too, so the
-- HUD can never stay hidden.
--
-- The bars are pure black, full width, BAR_H tall: 86 of 720 each = a 2.35:1
-- picture (LOCKSTEP with the preview tool's BAR_FRAC 0.12). They are the LAST
-- child of AetheriumHud, so they draw over every HUD piece; the veil hides those
-- pieces anyway.
-- =============================================================================

require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership" )
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodHudVeil" )

local BAR_H = 86           -- canvas units of 720: 12% top + 12% bottom = 2.35:1
local IN_MS = 650          -- the bars close in as the camera starts to turn
local OUT_MS = 550
-- The longest scene is ~11.6 s of a 13.3 s flight; if the "off" is ever lost the
-- watchdog opens the frame and gives the HUD back.
local WATCHDOG_MS = 17000
-- THE IMPACT FLASH: in fast (the eye reads it as a blast, not a fade), a short hold at
-- white (nothing can be seen), then it burns out through orange as the fireball takes over.
-- LOCKSTEP: tools/jump_title/test_jump_title.js reads these three (the ignite and the hull
-- removal must fall inside the full white; the fireball must be seen after it).
local FLASH_IN_MS = 60
local FLASH_HOLD_MS = 250   -- full white 4.66..4.91 s into the flight: the ignite (4.8) happens behind it
local FLASH_OUT_MS = 750
local FLASH_HOT = { 1.0, 0.97, 0.9 }     -- the white-hot core
local FLASH_BURN = { 1.0, 0.55, 0.22 }   -- it cools to fire as it clears

local function veilSet( on )
	if CoD.TodHudVeil then
		CoD.TodHudVeil.Set( "jump", on )
	end
end

CoD.TodJumpCine = InheritFrom( LUI.UIElement )

function CoD.TodJumpCine.new( HudRef, InstanceRef )
	local self = LUI.UIElement.new()
	CoD.TodUIOwnership.Attach( self )
	self:setClass( CoD.TodJumpCine )
	self.id = "TodJumpCine"
	self:setLeftRight( true, true, 0, 0 )
	self:setTopBottom( true, true, 0, 0 )

	-- THE FLASH: first child, so it draws under the bars (the letterbox stays black).
	local Flash = LUI.UIImage.new()
	Flash.id = "TodJumpCineFlash"
	Flash:setLeftRight( true, true, 0, 0 )
	Flash:setTopBottom( true, true, 0, 0 )
	Flash:setRGB( FLASH_HOT[ 1 ], FLASH_HOT[ 2 ], FLASH_HOT[ 3 ] )
	Flash:setAlpha( 0 )
	self:addElement( Flash )

	local Top = LUI.UIImage.new()
	Top.id = "TodJumpCineTop"
	Top:setLeftRight( true, true, 0, 0 )
	Top:setTopBottom( true, false, 0, 0 )
	Top:setRGB( 0, 0, 0 )
	Top:setAlpha( 1 )
	self:addElement( Top )

	local Bot = LUI.UIImage.new()
	Bot.id = "TodJumpCineBot"
	Bot:setLeftRight( true, true, 0, 0 )
	Bot:setTopBottom( false, true, 0, 0 )
	Bot:setRGB( 0, 0, 0 )
	Bot:setAlpha( 1 )
	self:addElement( Bot )

	-- The watchdog: an empty element whose long tween is the timer (no UITimers
	-- in this tree — TodSpinReel's pattern). A new beginAnimation interrupts the
	-- old one, and an interrupted completion is ignored below.
	local Watch = LUI.UIElement.new()
	Watch.id = "TodJumpCineWatch"
	Watch:setLeftRight( true, false, 0, 1 )
	Watch:setTopBottom( true, false, 0, 1 )
	Watch:setAlpha( 0 )
	self:addElement( Watch )

	local st = { on = false }

	local function barsTo( h, ms )
		Top:beginAnimation( "tod_jump_bars", ms, false, false, CoD.TweenType.Linear )
		Top:setTopBottom( true, false, 0, h )
		Bot:beginAnimation( "tod_jump_bars", ms, false, false, CoD.TweenType.Linear )
		Bot:setTopBottom( false, true, -h, 0 )
	end

	-- THE FLASH, a three-step chain (in -> hold -> out); every step is its own named
	-- tween so a new flash, or the scene ending, interrupts the chain cleanly.
	local function flashStop()
		st.flash = nil
		Flash:beginAnimation( "tod_jump_flash_stop", 1, false, false, CoD.TweenType.Linear )
		Flash:setAlpha( 0 )
	end

	local function flashImpact()
		st.flash = "impact"
		Flash:setRGB( FLASH_HOT[ 1 ], FLASH_HOT[ 2 ], FLASH_HOT[ 3 ] )
		Flash:beginAnimation( "tod_jump_flash_in", FLASH_IN_MS, false, false, CoD.TweenType.Linear )
		Flash:setAlpha( 1 )
	end

	Flash:registerEventHandler( "transition_complete_tod_jump_flash_in", function ( element, event )
		if ( event and event.interrupted ) or st.flash ~= "impact" then
			return
		end
		Flash:beginAnimation( "tod_jump_flash_hold", FLASH_HOLD_MS, false, false, CoD.TweenType.Linear )
		Flash:setAlpha( 1 )
	end )
	Flash:registerEventHandler( "transition_complete_tod_jump_flash_hold", function ( element, event )
		if ( event and event.interrupted ) or st.flash ~= "impact" then
			return
		end
		Flash:beginAnimation( "tod_jump_flash_out", FLASH_OUT_MS, false, false, CoD.TweenType.Linear )
		Flash:setRGB( FLASH_BURN[ 1 ], FLASH_BURN[ 2 ], FLASH_BURN[ 3 ] )
		Flash:setAlpha( 0 )
	end )

	local function setOn( on )
		if on == st.on then
			return
		end
		st.on = on
		veilSet( on )
		if not on then
			flashStop()
		end
		if on then
			barsTo( BAR_H, IN_MS )
			Watch:setAlpha( 0 )
			Watch:beginAnimation( "tod_jump_watch", WATCHDOG_MS, false, false, CoD.TweenType.Linear )
			Watch:setAlpha( 0.01 )
		else
			barsTo( 0, OUT_MS )
			Watch:beginAnimation( "tod_jump_watch_off", 50, false, false, CoD.TweenType.Linear )
			Watch:setAlpha( 0 )
		end
	end

	Watch:registerEventHandler( "transition_complete_tod_jump_watch", function ( element, event )
		if event and event.interrupted then
			return
		end
		setOn( false )
	end )

	self:subscribeToGlobalModel( InstanceRef, "PerController", "scriptNotify", function ( model )
		if Engine.GetModelValue( model ) ~= "tod_jump_cine" then
			return
		end
		local d = CoD.GetScriptNotifyData( model ) or {}
		if d[ 1 ] == 2 then
			if st.on then
				flashImpact()   -- only inside a live scene: a stray 2 never flashes a free screen
			end
		elseif d[ 1 ] == 3 then
			-- THE DEALER'S HOUSE (docs/207): a scene that outlasts the watchdog (his lines run long) re-arms it
			if st.on then
				Watch:setAlpha( 0 )
				Watch:beginAnimation( "tod_jump_watch", WATCHDOG_MS, false, false, CoD.TweenType.Linear )
				Watch:setAlpha( 0.01 )
			end
		else
			setOn( d[ 1 ] == 1 )
		end
	end )

	-- The HUD closes with its menu (death -> spectate, a HUD rebuild): never leave
	-- the veil held by bars that no longer exist.
	LUI.OverrideFunction_CallOriginalSecond( self, "close", function ( element )
		st.flash = nil
		if st.on then
			st.on = false
			veilSet( false )
		end
	end )

	return self
end
