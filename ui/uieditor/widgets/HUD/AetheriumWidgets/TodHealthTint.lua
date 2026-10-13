-- One tint owner for local and party HP bars: red while downed, white otherwise.
-- The color parent sits apart from the fill's health/bleedout shader animation.
-- Since docs/202 v3 (2026-10-03, tweak #3) it also carries THE HAVEN BLEED MASK:
-- a player downed inside a safe field bleeds out BLEED_MULT times slower, and the
-- two kit bars ask BleedoutMs() for the bar's duration so it drains at the real rate.
CoD.TodHealthTint = {}
local Tint = CoD.TodHealthTint
local BLEED_MULT = 1.5   -- LOCKSTEP _tod_haven.gsc TOD_HAVEN_BLEEDOUT

local function Mode( widget )
    if widget.currentPlayerState == 1 then return "down" end
    return "normal"
end

function Tint.Paint( widget )
    if not widget.health_tint or widget.todHealthClosed then return end
    local mode = Mode( widget )
    if widget.todHealthMode == mode then return end
    widget.todHealthMode = mode
    widget.health_tint:completeAnimation()
    if mode == "down" then
        widget.health_tint:setRGB( 1, 0.2, 0.2 )
    else
        widget.health_tint:setRGB( 1, 1, 1 )
    end
end

-- THE HAVEN BLEED (docs/202 v3): the bleed-out bar's duration for this widget's
-- player. The server's tod_haven_bleed mask (bit = entity number, one bit per
-- player) says who stands inside a safe field; stock's own bleed-out is `base` ms.
function Tint.BleedoutMs( widget, base )
    local id = widget.todHealthClientNum
    if id ~= nil and id >= 0 and id <= 3 then
        if math.floor( ( widget.todHavenBleedMask or 0 ) / ( 2 ^ id ) ) % 2 == 1 then
            return base * BLEED_MULT
        end
    end
    return base
end

-- Replaces the existing addElement(fill) call, keeping the large local widget
-- below its compiled closure limit. Original fill coordinates stay unchanged.
-- isLocal (the local bar vs a party row) stays in the signature: both player
-- widgets pass it and AetheriumPlayerInfo.lua cannot take an edited call.
function Tint.Attach( widget, controller, isLocal )
    widget.todHavenBleedMask = 0
    local parent = LUI.UIElement.new()
    parent:setLeftRight( true, true, 0, 0 )
    parent:setTopBottom( true, true, 0, 0 )
    widget.health_tint = parent
    widget:addElement( parent )
    parent:addElement( widget.health_fill )
    widget:linkToElementModel( widget, "clientNum", true, function( model )
        widget.todHealthClientNum = Engine.GetModelValue( model )
        Tint.Paint( widget )
    end )
    -- One subscription per widget lifetime, never per roster rebind.
    widget:subscribeToGlobalModel( controller, "PerController", "scriptNotify", function( model )
        local name = Engine.GetModelValue( model )
        if name == "tod_haven_bleed" then
            local data = CoD.GetScriptNotifyData( model )
            local value = data and data[1]
            if type( value ) ~= "number" then return end
            widget.todHavenBleedMask = value   -- a duration, not a colour: no repaint
        end
    end )
    LUI.OverrideFunction_CallOriginalSecond( widget, "close", function( element )
        element.todHealthClosed = true
        parent:completeAnimation()
        -- Party rows may already have closed the fill. Close only children
        -- still attached, so the local UIList row also releases its fill.
        local child = parent:getFirstChild()
        while child do
            local nextChild = child:getNextSibling()
            child:close()
            child = nextChild
        end
        parent:close()
    end )
    Tint.Paint( widget )
end
