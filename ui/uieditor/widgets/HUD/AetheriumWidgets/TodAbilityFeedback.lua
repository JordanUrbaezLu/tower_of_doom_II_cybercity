-- TodAbilityFeedback.lua - the ability TILES react (docs/203, 2026-10-02).
--
-- Before docs/203 the four classes' tiles went from 40% to 100% alpha and nothing
-- else. Now EVERY kit's two tiles get:
--   READY FLASH   the tile blooms (a bright overlay fades, the tile grows and
--                 settles) the moment an ability becomes usable;
--   CAST PULSE    a white snap when a ready ability is spent;
--   RECHARGE FRAME the perimeter fills as the ability comes back. The server sends
--                 seconds / kills / souls left, never a total, so the TOTAL IS
--                 INFERRED: the first value seen after a cast is the whole bar,
--                 and a value that climbs above it becomes the new total.
--   REFUSED PULSE (PK18, 2026-10-05) a red snap on the tile whose button was
--                 pressed while it cannot fire (Bash recharging, C4 empty, the
--                 Cloak on cooldown, the Soul Pulse charging, a refused grapple),
--                 with the server's muted "nope" (tod_ability_fx::kit_deny). The
--                 one server event: tod_kit_deny( slot ), via Refused().
-- Everything is client-side: no new server events, no clientfield bits.
--
-- Driven by AetheriumLoadout.lua: Attach() once, Kit( widget, slot, state, value )
-- on every kit update (state = "locked" / "ready" / "active" / "cd" / "empty"),
-- and KitOff() when the kit view leaves.
-- Test: tools/test_ability_feedback.lua.
CoD.TodAbilityFeedback = {}
local Feedback = CoD.TodAbilityFeedback

local FLASH_MS, CAST_MS, DENY_MS = 480, 220, 300
local DENY_RGB = { 1, 0.22, 0.16 }   -- the refusal red (the HUD's warning red, never the ready cyan)
local SLAB = "i_tod_hud_health_fill"   -- an opaque slab by contract (edge to edge, every column alike)
-- slot 1 = TACTICAL (x 1160), slot 2 = LETHAL (x 1210): the makeOffhandSlot order
local SLOT_X = { 1160, 1210 }
local FRAME_RGB = { { 0.35, 0.8, 1 }, { 0.35, 0.9, 0.55 } }

local function Frame( owner, x, color )
    local frame = { tracks = {}, fills = {} }
    local edges = {
        { x, x + 46, 568, 570 }, { x + 44, x + 46, 570, 598 },
        { x, x + 46, 598, 600 }, { x, x + 2, 570, 598 },
    }
    for i, edge in ipairs( edges ) do
        for _, group in ipairs( { frame.tracks, frame.fills } ) do
            local image = LUI.UIImage.new()
            image:setImage( RegisterImage( SLAB ) )
            image:setLeftRight( true, false, edge[1], edge[2] )
            image:setTopBottom( true, false, edge[3], edge[4] )
            image:setRGB( color[1], color[2], color[3] )
            image:setAlpha( 0 )
            owner:addElement( image )
            group[i] = image
        end
    end
    frame.set = function( percent )
        local active = type( percent ) == "number" and percent >= 0
        local left = active and math.min( percent, 100 ) * 148 / 100 or 0
        for i, edge in ipairs( edges ) do
            local length = ( i == 1 or i == 3 ) and 46 or 28
            local n = math.min( math.max( left, 0 ), length )
            left = left - length
            frame.tracks[i]:setAlpha( active and 0.18 or 0 )
            frame.fills[i]:setAlpha( active and n > 0 and 0.75 or 0 )
            if i == 1 then frame.fills[i]:setLeftRight( true, false, edge[1], edge[1] + n )
            elseif i == 2 then frame.fills[i]:setTopBottom( true, false, edge[3], edge[3] + n )
            elseif i == 3 then frame.fills[i]:setLeftRight( true, false, edge[2] - n, edge[2] )
            else frame.fills[i]:setTopBottom( true, false, edge[4] - n, edge[4] ) end
        end
    end
    return frame
end

-- a full-tile overlay for the flash / cast pulses
local function Overlay( owner, x, rgb )
    local el = LUI.UIImage.new()
    el:setImage( RegisterImage( SLAB ) )
    el:setLeftRight( true, false, x, x + 46 )
    el:setTopBottom( true, false, 568, 600 )
    el:setRGB( rgb[1], rgb[2], rgb[3] )
    el:setAlpha( 0 )
    owner:addElement( el )
    return el
end

local function Pulse( el, x, alpha, grow, ms, name )
    if not el then return end
    el:completeAnimation()
    el:setLeftRight( true, false, x - grow, x + 46 + grow )
    el:setTopBottom( true, false, 568 - grow, 600 + grow )
    el:setAlpha( alpha )
    el:beginAnimation( name, ms, false, false, CoD.TweenType.Linear )
    el:setLeftRight( true, false, x, x + 46 )
    el:setTopBottom( true, false, 568, 600 )
    el:setAlpha( 0 )
end

function Feedback.Attach( widget, dx )
    local tacticalFrame = Frame( widget, SLOT_X[1] + dx, FRAME_RGB[1] )
    local lethalFrame   = Frame( widget, SLOT_X[2] + dx, FRAME_RGB[2] )
    widget.todKitFrames = { tacticalFrame, lethalFrame }
    widget.todKitFlash = { Overlay( widget, SLOT_X[1] + dx, { 0.55, 0.95, 1 } ), Overlay( widget, SLOT_X[2] + dx, { 0.55, 0.95, 1 } ) }
    widget.todKitCast  = { Overlay( widget, SLOT_X[1] + dx, { 1, 1, 1 } ), Overlay( widget, SLOT_X[2] + dx, { 1, 1, 1 } ) }
    widget.todKitDeny  = { Overlay( widget, SLOT_X[1] + dx, DENY_RGB ), Overlay( widget, SLOT_X[2] + dx, DENY_RGB ) }
    widget.todKitX = { SLOT_X[1] + dx, SLOT_X[2] + dx }
    widget.todKit = { {}, {} }
end

-- ---- the refused press (PK18) -------------------------------------------------------
-- slot 1 = tactical, 2 = lethal. A short red snap that tightens onto the tile; never
-- touches the state machine below (a refusal changes nothing about readiness).
function Feedback.Refused( widget, slot )
    if not widget.todKitDeny or not widget.todKitDeny[slot] then return end
    Pulse( widget.todKitDeny[slot], widget.todKitX[slot], 0.8, 2, DENY_MS, "tod_abfx_deny" )
    widget.todKitRefused = ( widget.todKitRefused or 0 ) + 1
end

-- ---- the kit path (every class) ---------------------------------------------------
-- slot 1 = tactical, 2 = lethal; state "locked" / "ready" / "active" / "cd" / "empty";
-- value = what is left on a "cd" (seconds, kills, souls), else ignored.
function Feedback.Kit( widget, slot, state, value )
    if not widget.todKit or not widget.todKit[slot] then return end
    local s = widget.todKit[slot]
    local prev = s.prev
    local frame = widget.todKitFrames[slot]
    if state == "ready" then
        if prev and prev ~= "ready" then
            Pulse( widget.todKitFlash[slot], widget.todKitX[slot], 0.85, 4, FLASH_MS, "tod_abfx_flash" )
            s.flashes = ( s.flashes or 0 ) + 1
        end
        s.total = nil
        frame.set( -1 )
    elseif state == "cd" then
        if prev == "ready" or prev == "active" then
            if prev == "ready" then
                Pulse( widget.todKitCast[slot], widget.todKitX[slot], 0.7, 2, CAST_MS, "tod_abfx_cast" )
                s.casts = ( s.casts or 0 ) + 1
            end
            s.total = nil
        end
        local v = type( value ) == "number" and value or 0
        if not s.total or v > s.total then s.total = v end
        local pct = ( s.total and s.total > 0 ) and ( 100 * ( 1 - v / s.total ) ) or 0
        frame.set( math.max( 0, math.min( 100, pct ) ) )
    else
        if state == "active" and prev == "ready" then
            Pulse( widget.todKitCast[slot], widget.todKitX[slot], 0.7, 2, CAST_MS, "tod_abfx_cast" )
            s.casts = ( s.casts or 0 ) + 1
        end
        if state ~= "active" then s.total = nil end
        frame.set( -1 )
    end
    s.prev = state
end

function Feedback.KitOff( widget )
    if not widget.todKit then return end
    for slot = 1, 2 do
        widget.todKit[slot] = {}
        widget.todKitFrames[slot].set( -1 )
        for _, el in ipairs( { widget.todKitFlash[slot], widget.todKitCast[slot] } ) do
            el:completeAnimation()
            el:setAlpha( 0 )
        end
        local deny = widget.todKitDeny and widget.todKitDeny[slot]
        if deny then
            deny:completeAnimation()
            deny:setAlpha( 0 )
        end
    end
end
