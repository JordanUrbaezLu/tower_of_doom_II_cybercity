-- tools/test_round_counter_v2.lua - THE TOP-RIGHT "ROUND n" STAYS RETIRED UNDER HUD V2 (RT 2026-10-05).
-- Run: python -B tools/run_lua_harness.py tools/test_round_counter_v2.lua
--
-- User 2026-10-05: "the round X in top right still shows when we should have our assets actually replace that".
-- HUD V2 moved the round onto the top-left status plate (i_tod_h2_round_badge, tod_upgrade.lua Round2Row) and
-- AetheriumRoundCounter.lua was meant to keep running only to publish CoD.TodRound. It hid itself with ONE
-- container setAlpha( 0 ) - and AetheriumHud.lua writes that element's alpha back to 1 right after constructing it
-- and again in TodHudApply on every HUD state change, so the glyph row drew "ROUND n" in the top right all match.
-- This builds the REAL widget (TodGlyphRow + the generated metrics) under a minimal LUI mock, does what the HUD does
-- (setAlpha( 1 ), then the tod_round lane), and requires: NO glyph drawn, CoD.TodRound still published and still
-- following the lane. NEGATIVE CONTROL: the pre-RT widget (container alpha only) must FAIL the same checks.

local noop = function() end
local methods = {}
local GSUBS = {}
local function newElement()
    local e = setmetatable( { children = {}, alpha = 1 }, { __index = function( _, k )
        if methods[ k ] then return methods[ k ] end
        if type( k ) == 'string' and ( k:match( '^set' ) or k:match( '^make' ) ) then return noop end
    end } )
    return e
end
function methods:addElement( e ) self.children[ #self.children + 1 ] = e; e.parent = self end
function methods:getFirstChild() return self.children[ 1 ] end
function methods:getNextSibling()
    if not self.parent then return nil end
    for i, e in ipairs( self.parent.children ) do if e == self then return self.parent.children[ i + 1 ] end end
end
function methods:close() self.closed = true end
function methods:setAlpha( a ) self.alpha = a end
function methods:setImage( i ) self.image = i end
function methods:subscribeToGlobalModel( inst, group, name, fn ) GSUBS[ #GSUBS + 1 ] = fn end

Engine = setmetatable( { GetModelValue = function( m ) return m.name end }, { __index = function() return noop end } )
LUI = { UIElement = { new = newElement }, UIImage = { new = newElement },
        OverrideFunction_CallOriginalSecond = noop }
CoD = { GetScriptNotifyData = function( m ) return m.data end }
function InheritFrom() return {} end
function RegisterImage( s ) return s end

local function load( path )
    local f = assert( io.open( path, 'r' ) )
    local src = f:read( '*a' )
    f:close()
    return src
end
-- require() of the widget's own deps resolves to the real files
function require( mod )
    local path = mod:gsub( '%.', '/' ) .. '.lua'
    assert( loadstring( load( path ), path ) )()
end
require( 'ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphMetrics' )
require( 'ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership' )
require( 'ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphRow' )
local WIDGET = 'ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumRoundCounter.lua'

-- glyphs a player SEES: a pool image that is lit (alpha 1) on a container that is lit
local function drawn( w )
    if w.alpha <= 0 then return 0 end
    local n = 0
    for _, e in ipairs( w.children ) do
        if e.alpha > 0 and e.image and e.image ~= 'blacktransparent' then n = n + 1 end
    end
    return n
end

local function run( src )
    GSUBS = {}
    CoD.TodRound = nil
    assert( loadstring( src, WIDGET ) )()
    local w = CoD.AetheriumRoundCounter.new( newElement(), 0 )
    w:setAlpha( 1 )                        -- AetheriumHud.lua:571 and TodHudApply's base = 1
    for _, fn in ipairs( GSUBS ) do fn( { name = 'tod_round', data = { 12 } } ) end
    return w
end

local fails = {}
local live = load( WIDGET )
local w = run( live )
if drawn( w ) ~= 0 then fails[ #fails + 1 ] = 'the live widget draws ' .. drawn( w ) .. ' glyphs in the top right under HUD V2' end
if CoD.TodRound ~= 12 then fails[ #fails + 1 ] = 'CoD.TodRound did not follow the tod_round lane (got ' .. tostring( CoD.TodRound ) .. ')' end

-- the negative control: the pre-RT widget hid itself with container alpha only
local old = live:gsub( '\t\tif USE_HUD_V2 then\r?\n\t\t\tself%.row%.hide%(%)\r?\n\t\t\treturn\r?\n\t\tend\r?\n', '', 1 )
assert( old ~= live, 'negative control: the live widget no longer has the hide-and-return lane this test plants out' )
local w2 = run( old )
if drawn( w2 ) == 0 then fails[ #fails + 1 ] = 'NEGATIVE CONTROL: the pre-RT widget (alpha only) was NOT caught drawing in the top right' end

if #fails > 0 then error( 'ROUND COUNTER V2 FAILED:\n  ' .. table.concat( fails, '\n  ' ) ) end
print( 'round counter v2: the top-right ROUND n draws nothing under HUD V2 (after the HUD\'s alpha writes); CoD.TodRound = 12 follows the lane; the alpha-only control (' .. drawn( w2 ) .. ' glyphs) is caught.' )
