-- =============================================================================
-- TodCompanionPlate.lua - THE COMPANION STATUS PLATE (PK08, 2026-10-05, wave 2 W2G).
--
-- The companion the Dealer gives each player (docs/209) had its status drawn by
-- three server hudelems (_tod_partners.gsc status_hud): a stock-font label
-- ("TALON - REBUILDING") over two plain white quads - the one flat-box, stock-font
-- piece on a HUD that is otherwise all synthwave art. This is its replacement: a
-- plate in the HUD V2 chassis (tools/artgen/packs/w2g_companion_plate.py), the
-- companion's portrait in an octagonal well whose neon ring says its STATE, its
-- name and state in the map's typeface, and the player's own health-bar art as
-- its bar (track, a damage ghost, the fill, the 15-cell frame).
--
-- A DUMB RENDERER. _tod_partners.gsc push_hud owns the state and sends ONE int
-- event to the owner only (a LuiNotifyEvent on the player: there is no party row
-- to key, the plate never shows a teammate's companion):
--   tod_ptn_hud ( companion + 1, state, value, len, flags )
--     companion  0 = none held, 1..4 = PROTECTOR / TALON / R.A.P.S. / CERBERUS
--                (_tod_partners.gsc define order, LOCKSTEP NAMES / IMG.comp below)
--     state      TOD_PTN_UI_*: 0 none, 1 out and fighting, 2 destroyed (rebuilding),
--                3 on its way (deploying)
--     value      active / deploying: health percent in 5 % steps (a living one never
--                reads 0); rebuilding: whole seconds until it is back
--     len        rebuilding: the rebuild's whole length in seconds (QUICK REBOOT
--                shortens it, even mid-rebuild), else 0 - the bar fills toward 1
--     flags      1 = it holds still with its owner (a spin, a card deal, a world
--                pause: _tod_partners freeze_reason), 2 = its owner is dead or
--                spectating (the plate hides; it is back the moment he respawns)
-- The server re-sends the current tuple every 3 s (a recreated HUD or a late
-- joiner never waits for the next change); a SAME-TUPLE re-send draws nothing.
--
-- EVERY STATE HAS A LOOK (the AAA bar, CLAUDE.md):
--   ONLINE     cyan ring, cyan fill, full-colour portrait. Arriving (from the gift,
--              a rebuild or a respawn) the ring flashes white-hot and the bar powers
--              up from empty.
--   DAMAGED    at or under LOW percent: amber ring that pulses, amber fill. Every hit
--              leaves a white GHOST of the lost health that holds, then drains, and
--              the ring flicks white.
--   DESTROYED  the moment it dies: ring flashes red, the portrait shakes and goes dark
--              red, DESTROYED reads for HOLD_MS, then BACK IN <n> counts down while
--              an amber bar fills smoothly to the second it returns.
--   DEPLOYING  violet ring, the portrait blinks, the bar shows the health it comes
--              back with, dimmed.
--   HOLDING    frozen with its owner: steel ring and bar, dim portrait (the HUD veil
--              usually hides it then, but never wrong when it does not).
--   none / owner out   the plate fades away.
-- It lives in tod_upgrade.lua's HudOnly, so the HUD VEIL (card deals, the Black
-- Market spin, the jump cine) and the pause menu / scoreboard gate hide it with
-- the rest of the HUD. The three item chips (TodSpinReel.lua) sit on its top edge.
--
-- LOCKSTEP: CP's geometry with w2g_companion_plate.py GEO (its --check reads this
-- table); the state codes and flags with _tod_partners.gsc TOD_PTN_UI_* /
-- TOD_PTN_HUD_*; tools/test_companion_plate.lua drives every state.
-- =============================================================================

require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership" )
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphText" )

-- ONE TABLE (Lua 5.1's 60-upvalue cap; TodSpinReel.lua learned it the hard way).
local CP = {
    X0 = 1002, Y0 = 524, W = 188, H = 38,
    WELL = { 2, 2, 36, 36 }, WELL_CUT = 6,
    PORT = { 6, 6, 32, 32 },
    RING = { 0, 0, 38, 38 },
    BAR = { 42, 23, 180, 35 },
    NAME = { 42, 4, 112, 16 },
    TAG = { 112, 5, 182, 16 },
    -- the glyph pools are a HARD length cut (TodGlyphText): "PROTECTOR" is 9; "BACK IN 45" is 10 and a
    -- 3-digit countdown ("BACK IN 100") 11 - the rebuild is 45 s today, the pool does not assume it stays so
    NAME_CAP = 9, TAG_CAP = 7, NAME_POOL = 9, TAG_POOL = 11,
    LOW = 35,                       -- at or under this health percent it reads DAMAGED
    HOLD_MS = 1400,                 -- DESTROYED reads this long before the countdown
    IN_MS = 260, OUT_MS = 220, SLIDE = 24,
    FLASH_MS = 380, HIT_MS = 160, GHOST_HOLD_MS = 300, GHOST_MS = 360, FILL_MS = 220, UP_MS = 450,
    PULSE_MS = 520, BLINK_MS = 420, SHAKE_MS = 45, SHAKE_N = 6, SHAKE_PX = 2,
    NONE = 0, ACTIVE = 1, REBUILD = 2, DEPLOYING = 3, F_FROZEN = 1, F_OUT = 2,
    NAMES = { "PROTECTOR", "TALON", "R.A.P.S.", "CERBERUS" },
    IMG = { plate = "i_tod_h2_comp_plate", ring = "i_tod_h2_comp_ring", track = "i_tod_h2_hp_fill",
            frame = "i_tod_h2_hp_frame",
            comp = { "i_tod_spin_ico_comp_protector", "i_tod_spin_ico_comp_talon", "i_tod_spin_ico_comp_raps",
                     "i_tod_spin_ico_comp_cerberus" } },
    -- the state colours: cyan = live (the companion's own identity colour, the Black Market reel's), amber =
    -- warning, the gauge's downed red, violet = deploying, steel = idle / holding (RT 2026-10-05: the Fallen theme's
    -- dark-card violet PM_VIOLET, grey-blue idle PM_IDLE and cool white text; the synthwave pass had violet
    -- 0.66 / 0.5 / 1, lavender and lavender-white. w2g_companion_plate.py --check pins VIOLET / STEEL / TEXT to
    -- tools/artgen/synthwave.py THEME)
    CYAN = { 0.12, 0.9, 1 }, AMBER = { 1, 0.69, 0.13 }, RED = { 1, 0.18, 0.22 }, VIOLET = { 0.71, 0.36, 1 },
    STEEL = { 0.59, 0.64, 0.78 }, TEXT = { 0.94, 0.95, 0.98 }, TRACK = { 0.05, 0.07, 0.11 }, GHOST = { 1, 0.97, 0.94 },
    DEAD_PORT = { 0.55, 0.16, 0.2 },
}

local function text( parent, box, cap, pool, align, rgb )
    local t
    if CoD.TodGlyphText then
        t = CoD.TodGlyphText.new( { left = box[ 1 ], right = box[ 3 ], top = box[ 2 ], bottom = box[ 4 ], cap = cap,
                                    pool = pool, align = align, rgb = rgb } )
    else
        t = LUI.UIText.new()
        t:setLeftRight( true, false, box[ 1 ], box[ 3 ] )
        t:setTopBottom( true, false, box[ 2 ], box[ 4 ] )
        if align == "right" then
            t:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT )
        end
        t:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
    end
    parent:addElement( t )
    return t
end

local function image( parent, box, name, rgb, alpha )
    local e = LUI.UIImage.new()
    e:setLeftRight( true, false, box[ 1 ], box[ 3 ] )
    e:setTopBottom( true, false, box[ 2 ], box[ 4 ] )
    if name then
        e:setImage( RegisterImage( name ) )
    end
    if rgb then
        e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
    end
    e:setAlpha( alpha or 1 )
    parent:addElement( e )
    return e
end

local function tint( e, rgb )
    e:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
end

-- a whole number from an event argument (a missing or non-number argument reads 0)
local function int( v )
    v = tonumber( v ) or 0
    return math.floor( v )
end

CoD.TodCompanionPlate = InheritFrom( LUI.UIElement )
CoD.TodCompanionPlate.CP = CP   -- read by tools/test_companion_plate.lua and the render

function CoD.TodCompanionPlate.new( HudRef, InstanceRef )
    local self = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( self )
    self:setClass( CoD.TodCompanionPlate )
    self.id = "TodCompanionPlate"
    self:setLeftRight( true, true, 0, 0 )
    self:setTopBottom( true, true, 0, 0 )

    -- ---------------------------------------------------------------- the elements
    local el = {}
    el.plate = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( el.plate )
    el.plate.id = "TodCompPlateBody"
    el.plate:setLeftRight( true, false, CP.X0, CP.X0 + CP.W )
    el.plate:setTopBottom( true, false, CP.Y0, CP.Y0 + CP.H )
    el.plate:setAlpha( 0 )
    self:addElement( el.plate )
    local P = el.plate
    el.back = image( P, { 0, 0, CP.W, CP.H }, CP.IMG.plate )
    el.portBox = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( el.portBox )
    el.portBox:setLeftRight( true, false, CP.PORT[ 1 ], CP.PORT[ 3 ] )
    el.portBox:setTopBottom( true, false, CP.PORT[ 2 ], CP.PORT[ 4 ] )
    P:addElement( el.portBox )
    el.port = image( el.portBox, { 0, 0, CP.PORT[ 3 ] - CP.PORT[ 1 ], CP.PORT[ 4 ] - CP.PORT[ 2 ] }, CP.IMG.comp[ 1 ] )
    el.ring = image( P, CP.RING, CP.IMG.ring, CP.CYAN )
    el.flash = image( P, CP.RING, CP.IMG.ring, CP.GHOST, 0 )
    el.track = image( P, CP.BAR, CP.IMG.track, CP.TRACK )
    el.ghost = image( P, CP.BAR, CP.IMG.track, CP.GHOST, 0 )
    el.fill = image( P, CP.BAR, CP.IMG.track, CP.CYAN )
    el.frame = image( P, CP.BAR, CP.IMG.frame )
    el.name = text( P, CP.NAME, CP.NAME_CAP, CP.NAME_POOL, "left", CP.TEXT )
    el.tag = text( P, CP.TAG, CP.TAG_CAP, CP.TAG_POOL, "right", CP.CYAN )
    -- an empty element whose tween is the DESTROYED hold's timer (no UITimers in this tree)
    el.hold = LUI.UIElement.new()
    el.hold:setLeftRight( true, false, 0, 1 )
    el.hold:setTopBottom( true, false, 0, 1 )
    el.hold:setAlpha( 0 )
    self:addElement( el.hold )

    -- ---------------------------------------------------------------- state
    local st = { key = nil, shown = false, comp = 0, state = 0, value = 0, len = 0, frozen = false,
                 fill = 0, ghost = 0, ghostHolding = false, tone = nil, pulsing = false, pulseHi = true, blinking = false,
                 blinkHi = true, shakeN = 0, holding = false }
    self.todCP = { el = el, st = st }   -- read by tools/test_companion_plate.lua only

    local function barX( frac )
        if frac < 0 then
            frac = 0
        elseif frac > 1 then
            frac = 1
        end
        return CP.BAR[ 1 ] + ( CP.BAR[ 3 ] - CP.BAR[ 1 ] ) * frac
    end
    local function setBar( e, frac, ms, name )
        e:completeAnimation()
        if ms and ms > 0 then
            e:beginAnimation( name, ms, false, false, CoD.TweenType.Linear )
        end
        e:setLeftRight( true, false, CP.BAR[ 1 ], barX( frac ) )
    end

    -- the ring's state colour, and the loops that belong to a state
    local function pulse( on )
        if on == st.pulsing then
            return
        end
        st.pulsing = on
        el.ring:completeAnimation()
        el.ring:setAlpha( 1 )
        if on then
            st.pulseHi = false
            el.ring:beginAnimation( "tod_cp_pulse", CP.PULSE_MS, false, false, CoD.TweenType.Linear )
            el.ring:setAlpha( 0.45 )
        end
    end
    el.ring:registerEventHandler( "transition_complete_tod_cp_pulse", function ( element, event )
        if ( event and event.interrupted ) or not st.pulsing then
            return
        end
        st.pulseHi = not st.pulseHi
        element:beginAnimation( "tod_cp_pulse", CP.PULSE_MS, false, false, CoD.TweenType.Linear )
        element:setAlpha( st.pulseHi and 1 or 0.45 )
    end )

    local function blink( on )
        if on == st.blinking then
            return
        end
        st.blinking = on
        el.port:completeAnimation()
        el.port:setAlpha( 1 )
        if on then
            st.blinkHi = false
            el.port:beginAnimation( "tod_cp_blink", CP.BLINK_MS, false, false, CoD.TweenType.Linear )
            el.port:setAlpha( 0.3 )
        end
    end
    el.port:registerEventHandler( "transition_complete_tod_cp_blink", function ( element, event )
        if ( event and event.interrupted ) or not st.blinking then
            return
        end
        st.blinkHi = not st.blinkHi
        element:beginAnimation( "tod_cp_blink", CP.BLINK_MS, false, false, CoD.TweenType.Linear )
        element:setAlpha( st.blinkHi and 0.9 or 0.3 )
    end )

    -- a white-hot (or coloured) flash of the ring that fades out
    local function flash( rgb )
        el.flash:completeAnimation()
        tint( el.flash, rgb )
        el.flash:setAlpha( 1 )
        el.flash:beginAnimation( "tod_cp_flash", CP.FLASH_MS, false, false, CoD.TweenType.Linear )
        el.flash:setAlpha( 0 )
    end

    -- the portrait shakes (a hit that kills it). EVERY completeAnimation in this file runs BEFORE the state its
    -- handler reads is set: if the engine fires the old tween's transition_complete from it, the handler sees the
    -- OLD state and does nothing harmful (tools/test_companion_plate.lua runs both engine semantics).
    local function shake()
        el.portBox:completeAnimation()
        st.shakeN = CP.SHAKE_N
        el.portBox:beginAnimation( "tod_cp_shake", CP.SHAKE_MS, false, false, CoD.TweenType.Linear )
        el.portBox:setLeftRight( true, false, CP.PORT[ 1 ] - CP.SHAKE_PX, CP.PORT[ 3 ] - CP.SHAKE_PX )
    end
    el.portBox:registerEventHandler( "transition_complete_tod_cp_shake", function ( element, event )
        if event and event.interrupted then
            return
        end
        st.shakeN = st.shakeN - 1
        local dx = 0
        if st.shakeN > 0 then
            dx = ( st.shakeN % 2 == 0 ) and -CP.SHAKE_PX or CP.SHAKE_PX
            element:beginAnimation( "tod_cp_shake", CP.SHAKE_MS, false, false, CoD.TweenType.Linear )
        end
        element:setLeftRight( true, false, CP.PORT[ 1 ] + dx, CP.PORT[ 3 ] + dx )
    end )

    -- the damage ghost: holds the lost health for a beat, then drains to the bar
    el.ghost:registerEventHandler( "transition_complete_tod_cp_ghost_hold", function ( element, event )
        if ( event and event.interrupted ) or not st.ghostHolding then
            return
        end
        st.ghostHolding = false
        element:beginAnimation( "tod_cp_ghost", CP.GHOST_MS, false, false, CoD.TweenType.Linear )
        element:setLeftRight( true, false, CP.BAR[ 1 ], barX( st.fill ) )
        element:setAlpha( 0 )
        st.ghost = st.fill
    end )

    -- DESTROYED holds, then the countdown takes the tag
    local function tagText()
        if st.state == CP.REBUILD then
            if st.holding then
                return "DESTROYED", CP.RED
            end
            return "BACK IN " .. st.value, CP.AMBER
        elseif st.frozen then
            return "HOLDING", CP.STEEL
        elseif st.state == CP.DEPLOYING then
            return "DEPLOYING", CP.VIOLET
        elseif st.value <= CP.LOW then
            return "DAMAGED", CP.AMBER
        end
        return "ONLINE", CP.CYAN
    end
    local function paintTag()
        local s, rgb = tagText()
        el.tag:setText( s )
        el.tag:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
    end
    el.hold:registerEventHandler( "transition_complete_tod_cp_hold", function ( element, event )
        if ( event and event.interrupted ) or not st.holding then
            return
        end
        st.holding = false
        if st.shown and st.state == CP.REBUILD then
            paintTag()
        end
    end )

    local function appear()
        st.shown = true
        P:completeAnimation()
        P:setLeftRight( true, false, CP.X0 + CP.SLIDE, CP.X0 + CP.SLIDE + CP.W )
        P:setAlpha( 0 )
        P:beginAnimation( "tod_cp_in", CP.IN_MS, false, false, CoD.TweenType.Linear )
        P:setLeftRight( true, false, CP.X0, CP.X0 + CP.W )
        P:setAlpha( 1 )
    end
    local function disappear()
        st.shown = false
        st.state, st.comp, st.value, st.frozen, st.holding = CP.NONE, 0, 0, false, false
        pulse( false )
        blink( false )
        P:completeAnimation()
        P:beginAnimation( "tod_cp_out", CP.OUT_MS, false, false, CoD.TweenType.Linear )
        P:setAlpha( 0 )
    end

    -- ---------------------------------------------------------------- one event
    local function onHud( d )
        local comp, state, value, len, flags = int( d[ 1 ] ), int( d[ 2 ] ), int( d[ 3 ] ), int( d[ 4 ] ), int( d[ 5 ] )
        local key = comp .. "/" .. state .. "/" .. value .. "/" .. len .. "/" .. flags
        if key == st.key then
            return   -- the heartbeat: the same tuple draws nothing
        end
        st.key = key
        local out = ( math.floor( flags / CP.F_OUT ) % 2 == 1 )
        local known = ( comp >= 1 and comp <= #CP.NAMES and state >= CP.ACTIVE and state <= CP.DEPLOYING )
        if out or not known then
            if st.shown then
                disappear()
            end
            return
        end
        local was, wasValue, wasComp = st.state, st.value, st.comp
        local arriving = not st.shown
        if arriving then
            appear()
        end
        if comp ~= wasComp then
            el.port:setImage( RegisterImage( CP.IMG.comp[ comp ] ) )
            el.name:setText( CP.NAMES[ comp ] )
            was, wasValue = CP.NONE, 0   -- a different companion is a fresh arrival, never a hit
        end
        st.comp, st.state, st.value, st.len = comp, state, value, len
        st.frozen = ( flags % 2 == 1 )
        if state ~= CP.REBUILD then
            st.holding = false
        end

        local tone
        if state == CP.REBUILD then
            -- DESTROYED: the moment it dies, then an amber bar that fills to the second it is back
            if was ~= CP.REBUILD then
                el.hold:completeAnimation()
                st.holding = true
                el.hold:setAlpha( 0 )
                el.hold:beginAnimation( "tod_cp_hold", CP.HOLD_MS, false, false, CoD.TweenType.Linear )
                el.hold:setAlpha( 0.01 )
                flash( CP.RED )
                shake()
                st.ghostHolding = false
                el.ghost:completeAnimation()
                el.ghost:setAlpha( 0 )
            end
            -- the bar shows the rebuild served, and runs one second ahead with the clock (the server
            -- sends each whole second, so the fill never stalls between them)
            local total = ( len >= value and len > 0 ) and len or value
            local served = ( total > 0 ) and ( ( total - value ) / total ) or 0
            local ahead = ( total > 0 ) and ( ( total - value + 1 ) / total ) or 1
            setBar( el.fill, served )
            el.fill:beginAnimation( "tod_cp_count", 1000, false, false, CoD.TweenType.Linear )
            el.fill:setLeftRight( true, false, CP.BAR[ 1 ], barX( ahead ) )
            st.fill = ahead
            st.ghost = 0
            tint( el.fill, CP.AMBER )
            el.fill:setAlpha( 1 )
            tint( el.port, CP.DEAD_PORT )
            tone = CP.RED
            pulse( false )
            blink( false )
        else
            local frac = value / 100
            if state == CP.DEPLOYING then
                tone = st.frozen and CP.STEEL or CP.VIOLET
                setBar( el.fill, frac, CP.FILL_MS, "tod_cp_fill" )
                tint( el.fill, tone )
                el.fill:setAlpha( 0.45 )
                tint( el.port, CP.TEXT )
                pulse( false )
                blink( not st.frozen )
                if st.frozen then
                    el.port:setAlpha( 0.55 )
                end
            else
                -- ACTIVE
                tone = CP.CYAN
                if st.frozen then
                    tone = CP.STEEL
                elseif value <= CP.LOW then
                    tone = CP.AMBER
                end
                blink( false )
                tint( el.port, { 1, 1, 1 } )
                el.port:setAlpha( st.frozen and 0.55 or 1 )
                el.fill:setAlpha( 1 )
                tint( el.fill, tone )
                if was == CP.ACTIVE and value < wasValue then
                    -- a hit: the ghost keeps the lost health (a burst of hits keeps the top of the
                    -- burst, so it drains once, the whole chunk), the bar drops, the ring flicks
                    local top = math.max( st.ghost, wasValue / 100 )
                    st.ghostHolding = false
                    el.ghost:completeAnimation()
                    st.ghost = top
                    st.ghostHolding = true
                    el.ghost:setLeftRight( true, false, CP.BAR[ 1 ], barX( top ) )
                    el.ghost:setAlpha( 0.9 )
                    el.ghost:beginAnimation( "tod_cp_ghost_hold", CP.GHOST_HOLD_MS, false, false, CoD.TweenType.Linear )
                    el.ghost:setAlpha( 0.9 )
                    setBar( el.fill, frac, CP.FILL_MS, "tod_cp_fill" )
                    el.flash:completeAnimation()
                    tint( el.flash, CP.GHOST )
                    el.flash:setAlpha( 0.8 )
                    el.flash:beginAnimation( "tod_cp_flash", CP.HIT_MS, false, false, CoD.TweenType.Linear )
                    el.flash:setAlpha( 0 )
                elseif was == CP.ACTIVE then
                    -- healed (NANO REPAIR) or a frozen / thawed re-send: the bar moves, nothing flashes
                    setBar( el.fill, frac, CP.UP_MS, "tod_cp_fill" )
                    st.ghost = frac
                else
                    -- ONLINE: it arrives (the gift, back from a rebuild, a respawn) - the bar powers up
                    setBar( el.fill, 0 )
                    setBar( el.fill, frac, CP.UP_MS, "tod_cp_fill" )
                    st.ghostHolding = false
                    el.ghost:completeAnimation()
                    el.ghost:setAlpha( 0 )
                    st.ghost = frac
                    flash( { 1, 1, 1 } )
                end
                pulse( value <= CP.LOW and not st.frozen )
            end
            st.fill = frac
        end
        tint( el.ring, tone )
        st.tone = tone
        paintTag()
    end

    self:subscribeToGlobalModel( InstanceRef, "PerController", "scriptNotify", function ( model )
        if Engine.GetModelValue( model ) ~= "tod_ptn_hud" then
            return
        end
        onHud( CoD.GetScriptNotifyData( model ) or {} )
    end )

    return self
end

return CoD.TodCompanionPlate
