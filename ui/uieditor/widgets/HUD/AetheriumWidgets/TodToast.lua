-- =============================================================================
-- TodToast.lua - THE TOAST (RT 2026-10-05, the red return; docs/218).
--
-- A teammate's big moment, and a few of your own, used to be IPrintLnBold lines: the stock CenterConsole's bold
-- engine font, dropped straight across the card deal's banner band (y 68..166). User 2026-10-05: "the upgrade and
-- choose class banners should be in our typography". They are ONE int event now, drawn on the title plate
-- (i_tod_title_plate, zoned) in the map's own glyph cells, ABOVE the deal banner and the Black Market frame:
--
--   tod_toast ( kind, who, code )      _tod_upgrade_ui.gsc team_toast (every OTHER player) / self_toast
--     kind  1 <name> / PULLED A LEGENDARY                  a card (LEGENDARY gold)
--           2 <name> / PULLED A LEGENDARY <item>           the Black Market; code = the item 1..9 (T.ITEMS)
--           3 <name> / IS ON FIRE                          the hot streak (the heat's orange)
--           4 CLASS TIER n UNLOCKS AT FLOOR f              code = n * 1000 + f
--           5 FLOOR f REACHED - CLASS TIER n UNLOCKED      code = n * 1000 + f; + 100000 = the gun still needs a
--                                                          Pack-a-Punch (a second line: PACK-A-PUNCH TO PROMOTE)
--           6 NEW WEAPONS ARE NOT PACK-A-PUNCHED
--           7 the Archer's arm line (two lines)
--     who   the client number of the player it is about (kinds 1-3 put his name on the top line, in our face;
--           a name we cannot draw falls back to the TTF of the same face, never to nothing)
--
-- A moment, not a state: a new toast REPLACES the one showing. It drops in, holds, fades. It rides above the card
-- panel and the Black Market reel (these moments land mid-deal), and hides while any OTHER full-screen moment
-- holds the HUD veil (the jump cine, the class terminal). LOCKSTEP: the kinds / codes with _tod_upgrade_ui.gsc
-- and its callers, T.ITEMS with _tod_shop.gsc item_name; tools/test_toast.lua drives every kind.
-- =============================================================================

require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership" )
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphText" )

-- ONE TABLE (Lua 5.1's 60-upvalue cap).
local T = {
    X0 = 352, Y0 = 38, W = 576, H = 72,          -- the title plate (1024 x 128 art) at 0.5625: x 352..928, y 38..110
    LINE1 = { 56, 15, 520, 33 },                 -- plate-local boxes, inside the hex's inner frame (art y 28..100) and
    LINE2 = { 56, 35, 520, 58 },                 -- clear of its two studs (art x 84 / 940)
    ONE = { 56, 23, 520, 49 },
    POOL1 = 40, POOL2 = 52,
    SLIDE = 10, IN_MS = 160, OUT_MS = 420, HOLD_MS = 3200, HOLD_LONG_MS = 5200,
    WHITE = { 0.94, 0.95, 0.98 }, GOLD = { 1.0, 0.761, 0.239 }, HEAT = { 1, 0.52, 0.14 },
    AMBER = { 1.0, 0.69, 0.13 }, INFO = { 0.62, 0.82, 1.0 },
    IMG = "i_tod_title_plate", TTF = "fonts/tod_tower1.ttf",
    -- LOCKSTEP _tod_shop.gsc item_name (the Black Market's nine items, 1..9)
    ITEMS = { "PLATING", "OVERCLOCK", "HOLLOW POINT", "LONG SIGHT", "NANO REPAIR", "ARC CHAIN", "SALVAGE", "QUICK REBOOT",
              "LUCKY CHARM" },
    -- the veil owners a toast still shows over (it is ABOUT those moments); any other owner hides it
    VEIL_OK = { cards = true, spin = true },
    NOBODY = "A TEAMMATE",
}

local function int( v )
    v = tonumber( v ) or 0
    return math.floor( v )
end

CoD.TodToast = InheritFrom( LUI.UIElement )
CoD.TodToast.T = T   -- read by tools/test_toast.lua

-- kind, who, code -> line1, rgb1, line2, rgb2 (line2 nil = a one-line toast), or nil for an unknown kind
function CoD.TodToast.lines( kind, code, name )
    if kind == 1 then
        return name, T.WHITE, "PULLED A LEGENDARY", T.GOLD
    elseif kind == 2 then
        local item = T.ITEMS[ code ]
        return name, T.WHITE, item and ( "PULLED A LEGENDARY " .. item ) or "PULLED A LEGENDARY", T.GOLD
    elseif kind == 3 then
        return name, T.WHITE, "IS ON FIRE", T.HEAT
    elseif kind == 4 then
        return "CLASS TIER " .. math.floor( ( code % 100000 ) / 1000 ) .. " UNLOCKS AT FLOOR " .. ( code % 1000 ), T.AMBER
    elseif kind == 5 then
        local top = "FLOOR " .. ( code % 1000 ) .. " REACHED - CLASS TIER " .. math.floor( ( code % 100000 ) / 1000 ) .. " UNLOCKED"
        if code >= 100000 then
            return top, T.WHITE, "PACK-A-PUNCH TO PROMOTE", T.AMBER
        end
        return top, T.AMBER
    elseif kind == 6 then
        return "NEW WEAPONS ARE NOT PACK-A-PUNCHED", T.AMBER
    elseif kind == 7 then
        return "ARCHER - HOLD YOUR TACTICAL TO GRAPPLE", T.WHITE, "NO FALL DAMAGE - EARN HELL'S RETRIEVER FROM A CARD", T.INFO
    end
    return nil
end

function CoD.TodToast.new( HudRef, InstanceRef )
    local self = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( self )
    self:setClass( CoD.TodToast )
    self.id = "TodToast"
    self:setLeftRight( true, true, 0, 0 )
    self:setTopBottom( true, true, 0, 0 )

    local el = {}
    el.plate = LUI.UIElement.new()
    CoD.TodUIOwnership.Attach( el.plate )
    el.plate.id = "TodToastPlate"
    el.plate:setLeftRight( true, false, T.X0, T.X0 + T.W )
    el.plate:setTopBottom( true, false, T.Y0, T.Y0 + T.H )
    el.plate:setAlpha( 0 )
    self:addElement( el.plate )
    local P = el.plate
    el.back = LUI.UIImage.new()
    el.back:setLeftRight( true, false, 0, T.W )
    el.back:setTopBottom( true, false, 0, T.H )
    el.back:setImage( RegisterImage( T.IMG ) )
    P:addElement( el.back )
    local function text( box, pool, name )
        local t
        if CoD.TodGlyphText then
            t = CoD.TodGlyphText.new( { left = box[ 1 ], right = box[ 3 ], top = box[ 2 ], bottom = box[ 4 ], align = "center",
                                        pool = pool, fallbackTTF = name and T.TTF or nil } )
        else
            -- the fail-safe: the SAME face as a TTF (never the engine's default font)
            t = LUI.UIText.new()
            t:setLeftRight( true, false, box[ 1 ], box[ 3 ] )
            t:setTopBottom( true, false, box[ 2 ], box[ 4 ] )
            t:setTTF( T.TTF )
            t:setAlignment( Enum.LUIAlignment.LUI_ALIGNMENT_CENTER )
        end
        P:addElement( t )
        return t
    end
    el.line1 = text( T.LINE1, T.POOL1, true )
    el.line2 = text( T.LINE2, T.POOL2, false )
    el.one = text( T.ONE, T.POOL1, false )

    local st = { phase = 0, kind = 0, shown = false, veiled = false, hold = T.HOLD_MS }
    self.todToast = { el = el, st = st }   -- read by tools/test_toast.lua only

    local function nameOf( who )
        local root = Engine.GetModelForController( InstanceRef )
        if root then
            for i = 0, 3 do
                local cm = Engine.GetModel( root, "PlayerList." .. i .. ".clientNum" )
                if cm and Engine.GetModelValue( cm ) == who then
                    local nm = Engine.GetModel( root, "PlayerList." .. i .. ".playerName" )
                    local s = nm and Engine.GetModelValue( nm )
                    if type( s ) == "string" and s ~= "" then
                        return Engine.Localize( s )
                    end
                end
            end
        end
        return T.NOBODY
    end
    local function paint( t, s, rgb )
        t:setText( s or "" )
        if rgb then
            t:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
        end
        t:setAlpha( s and 1 or 0 )
    end

    -- the three beats, one tween each, chained through transition_complete; a stale or interrupted tween never
    -- continues the chain (st.phase says which beat is live)
    local function fadeOut()
        st.phase = 3
        P:beginAnimation( "tod_toast_out", T.OUT_MS, false, false, CoD.TweenType.Linear )
        P:setAlpha( 0 )
    end
    P:registerEventHandler( "transition_complete_tod_toast_in", function ( element, event )
        if ( event and event.interrupted ) or st.phase ~= 1 then
            return
        end
        st.phase = 2
        element:beginAnimation( "tod_toast_hold", st.hold, false, false, CoD.TweenType.Linear )
        element:setAlpha( 1 )
    end )
    P:registerEventHandler( "transition_complete_tod_toast_hold", function ( element, event )
        if ( event and event.interrupted ) or st.phase ~= 2 then
            return
        end
        fadeOut()
    end )
    P:registerEventHandler( "transition_complete_tod_toast_out", function ( element, event )
        if ( event and event.interrupted ) or st.phase ~= 3 then
            return
        end
        st.phase = 0
        st.shown = false
    end )

    local function show( kind, who, code )
        local name = ( kind >= 1 and kind <= 3 ) and nameOf( who ) or nil
        local l1, c1, l2, c2 = CoD.TodToast.lines( kind, code, name )
        if not l1 then
            return
        end
        st.kind, st.shown = kind, true
        st.hold = ( kind == 7 ) and T.HOLD_LONG_MS or T.HOLD_MS
        if l2 then
            paint( el.line1, l1, c1 )
            paint( el.line2, l2, c2 )
            paint( el.one, nil )
        else
            paint( el.line1, nil )
            paint( el.line2, nil )
            paint( el.one, l1, c1 )
        end
        st.phase = 0                       -- the old chain is dead before its tween is cut (a loud completion is ignored)
        P:completeAnimation()
        P:setTopBottom( true, false, T.Y0 - T.SLIDE, T.Y0 - T.SLIDE + T.H )
        P:setAlpha( 0 )
        st.phase = 1
        P:beginAnimation( "tod_toast_in", T.IN_MS, false, false, CoD.TweenType.Linear )
        P:setTopBottom( true, false, T.Y0, T.Y0 + T.H )
        P:setAlpha( 1 )
    end

    -- the veil: shown over the card deal and the Black Market (that is where these moments land), hidden under any
    -- other owner (the jump cine, the class terminal); the plate keeps its own beat underneath
    if CoD.TodHudVeil and CoD.TodHudVeil.Listen then
        CoD.TodHudVeil.Listen( self, function ( hidden )
            local block = false
            if hidden then
                for key, on in pairs( CoD.TodHudVeil.owners or {} ) do
                    if on and not T.VEIL_OK[ key ] then
                        block = true
                    end
                end
            end
            st.veiled = block
            self:setAlpha( block and 0 or 1 )
        end )
    end

    self:subscribeToGlobalModel( InstanceRef, "PerController", "scriptNotify", function ( model )
        if Engine.GetModelValue( model ) ~= "tod_toast" then
            return
        end
        local d = CoD.GetScriptNotifyData( model ) or {}
        show( int( d[ 1 ] ), int( d[ 2 ] ), int( d[ 3 ] ) )
    end )

    return self
end

return CoD.TodToast
