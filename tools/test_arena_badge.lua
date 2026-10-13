-- tools/test_arena_badge.lua - THE BATTLE ARENA on the round badge (docs/185 v2.2) under the REAL
-- upgrade menu. Run: python -B tools/run_lua_harness.py tools/test_arena_badge.lua
--
-- User 2026-10-03: "in the Battle Arena we should replace the round HUD with Battle Arena / Level 1
-- etc ... rounds dont count in there and its a static difficulty of progression". HUD V2's status
-- plate (the round badge + the luck plate) lives in tod_upgrade.lua, so this builds the real
-- LUI.createMenu.tod_upgrade and drives the two server lanes the badge reads -
--     tod_round ( n )  and  tod_arena ( show, level, levels, wave, waves, left, flags )
-- - and checks what the badge shows: the round badge + the round number by default; the ARENA twin
-- (i_tod_h2_arena_badge: BATTLE ARENA in the pill, a LEVEL caption in the window) + the LEVEL number,
-- drawn smaller and lower so it sits under that caption, while show is 1; the rampage variants when
-- the Rampage Inducer is on; a 2 s re-send repaints nothing; a round that advances during the fight
-- stays off the badge and is there the moment the arena hands back. Negative controls: a plate that
-- re-dresses the badge on every re-send, and one whose badge ignores the arena, must both FAIL.

local noop = function() end
local elements = {}
local methods = {}
local GSUBS = {}
local function newElement()
    local e = setmetatable( { children = {}, handlers = {}, alpha = 1, rgb = { 1, 1, 1 } }, { __index = function( _, k )
        if methods[ k ] then return methods[ k ] end
        if k:match( '^set' ) or k:match( '^make' ) or k:match( '^link' ) or k:match( '^Add' ) then return noop end
    end } )
    elements[ #elements + 1 ] = e
    return e
end
function methods:addElement( e ) self.children[ #self.children + 1 ] = e; e.parent = self end
function methods:getParent() return self.parent end
function methods:getFirstChild() return self.children[ 1 ] end
function methods:getNextSibling()
    if not self.parent then return nil end
    for i, e in ipairs( self.parent.children ) do if e == self then return self.parent.children[ i + 1 ] end end
end
function methods:close()
    self.closed = true
    if self.parent then
        for i, e in ipairs( self.parent.children ) do if e == self then table.remove( self.parent.children, i ); break end end
        self.parent = nil
    end
end
function methods:registerEventHandler( k, v ) self.handlers[ k ] = v end
function methods:setAlpha( a ) self.alpha = a end
function methods:setRGB( r, g, b ) self.rgb = { r, g, b } end
function methods:setLeftRight( a, b, l, r ) self.l, self.r = l, r end
function methods:setTopBottom( a, b, t, bt ) self.t, self.b = t, bt end
function methods:setImage( i ) self.image = i; self.imageWrites = ( self.imageWrites or 0 ) + 1 end
function methods:setText( t ) self.text = t end
function methods:completeAnimation() self.anim = nil end
function methods:beginAnimation( name, ms ) self.anim = { name = name, ms = ms } end
function methods:getOwner() return 0 end
function methods:processEvent( e ) if self.handlers[ e.name ] then return self.handlers[ e.name ]( self, e ) end end
function methods:getLocalLeftRight() return true, false, 0, 80 end
function methods:getLocalTopBottom() return true, false, 0, 20 end

-- models: subscribeToModel stores the callback; push() sets a value and fires it.
-- scriptNotify: subscribeToGlobalModel stores the callback; notify() fires every one with the event
-- the way a server LuiNotifyEvent lands (the model's value is the event's name; GetScriptNotifyData its args).
local MODELS, SUBS = {}, {}
function methods:subscribeToModel( m, fn ) SUBS[ m ] = SUBS[ m ] or {}; table.insert( SUBS[ m ], fn ) end
function methods:subscribeToGlobalModel( inst, group, name, fn ) GSUBS[ #GSUBS + 1 ] = fn end
local function push( name, v )
    local key = 'ctrl.' .. name
    MODELS[ key ] = v
    for _, fn in ipairs( SUBS[ key ] or {} ) do fn( key ) end
end
local function notify( name, data )
    for _, fn in ipairs( GSUBS ) do fn( { name = name, data = data } ) end
end

local function enums() return setmetatable( {}, { __index = function( t, k ) local v = enums(); rawset( t, k, v ); return v end } ) end
Enum = enums()
Engine = setmetatable( {
    Localize = function( s ) return s end, GetModelForController = function() return 'ctrl' end,
    GetModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
    CreateModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
    GetModelValue = function( k ) if type( k ) == 'table' then return k.name end return MODELS[ k ] or 0 end,
    IsInGame = function() return true end,
    GetCurrentMap = function() return 'zm_tod2_cybercity' end, GetClientNum = function() return 0 end,
}, { __index = function() return noop end } )
DataSources = {}
DataSourceHelpers = { ListSetup = function( _, fn ) return fn end }
function ListHelper_SetupDataSource( _, fn ) return { __build = fn } end
CoD = { Menu = { NewForUIEditor = newElement }, TweenType = { Linear = 0, Bounce = 1 }, isZombie = true, TodOwned = {}, TodClass = 2, TodClassTier = 1,
        GetScriptNotifyData = function( m ) return m.data end }
CoD.Menu.SetButtonLabel = noop; CoD.Menu.UpdateButtonShownState = noop
LUI = { UIElement = { new = newElement }, UIImage = { new = newElement }, UIText = { new = newElement }, UIList = { new = newElement }, UITimer = { new = newElement }, createMenu = {} }
function LUI.OverrideFunction_CallOriginalSecond( e, key, fn )
    local old = e[ key ]; e[ key ] = function( ... ) fn( ... ); if old then return old( ... ) end end
end
function InheritFrom() return {} end
function RegisterImage( s ) return s end
function IsPC() return true end
function IsGamepad() return false end
function IsInGame() return true end
function RegisterOpenedMenu() end
function IsPrimaryController() return true end
function IsModelValueEqualTo() return false end
require = function() end

dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodUIOwnership.lua' )
CoD.TextWithBg = { new = function()
    local e = newElement()
    CoD.TodUIOwnership.Attach( e )
    e.Text = newElement(); e.Bg = newElement()
    e:addElement( e.Text ); e:addElement( e.Bg )
    return e
end }
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodGlyphMetrics.lua' )
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodGlyphRow.lua' )
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodHudVeil.lua' )
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodCardArt.lua' )
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodPull.lua' )
do local n = 0; Enum.UIVisibilityBit = setmetatable( {}, { __index = function( t, k ) n = n + 1; rawset( t, k, n ); return n end } ) end

local PATH = 'ui/uieditor/menus/hud/tod_upgrade.lua'
local fh = assert( io.open( PATH, 'r' ) )
local SOURCE = fh:read( '*a' ); fh:close()

-- the number window (canvas): art x 38..153 / y 57..124 of a 192 px badge at 0.375 from (16, 10);
-- the LEVEL caption's bottom row is art y 71 (make_badge.py WINDOW_TEXT): canvas 10 + 71 * 0.375
local WIN_L, WIN_R, WIN_T, WIN_B = 16 + 38 * 0.375, 16 + 153 * 0.375, 10 + 57 * 0.375, 10 + 124 * 0.375
local CAPTION_BOTTOM = 10 + 71 * 0.375
local DIGITS = CoD.TodGlyphMetrics.digits

local function run( src )
    elements = {}
    GSUBS = {}
    MODELS, SUBS = {}, {}
    CoD.TodRound = nil
    assert( loadstring( src, '@' .. PATH ) )()
    local menu = LUI.createMenu.tod_upgrade( 0 )
    local badge
    for _, e in ipairs( elements ) do
        if e.image == 'i_tod_h2_round_badge' and e.l == 16 and e.t == 10 then badge = e end
    end
    assert( badge, 'the HUD V2 round badge exists at (16, 10)' )
    -- the number: the digit-set glyph cells drawn inside the badge's window, left to right
    local function digits()
        local out = {}
        for _, e in ipairs( elements ) do
            if e.alpha == 1 and type( e.image ) == 'string' and e.l and e.t then
                local c = string.match( e.image, '^i_tod_hud_d(%d)$' )
                if c and e.l >= WIN_L - 2 and e.r <= WIN_R + 2 and e.t >= WIN_T - 6 and e.b <= WIN_B + 6 then
                    out[ #out + 1 ] = { c = c, l = e.l, t = e.t, b = e.b }
                end
            end
        end
        table.sort( out, function( a, b ) return a.l < b.l end )
        local s = ''
        for _, g in ipairs( out ) do s = s .. g.c end
        return s, out
    end
    local function geom()
        local _, g = digits()
        assert( #g > 0, 'a number is drawn' )
        local s = ( g[ 1 ].b - g[ 1 ].t ) / DIGITS.ch            -- canvas px per source px
        local baseline = g[ 1 ].t + DIGITS.baseline * s
        return { cap = DIGITS.cap * s, baseline = baseline, inkTop = baseline - DIGITS.cap * s, inkBottom = baseline }
    end
    assert( digits() == '1', 'the badge starts at ROUND 1 (' .. digits() .. ')' )
    notify( 'tod_round', { 5 } )
    assert( digits() == '5', 'tod_round writes the round (' .. digits() .. ')' )
    local round = geom()
    assert( round.inkTop >= WIN_T and round.inkBottom <= WIN_B, 'the round number sits in the window' )
    -- the arena: the badge in arena dress, the LEVEL in the window under the baked caption
    notify( 'tod_arena', { 1, 3, 10, 0, 3, 0, 0 } )
    assert( badge.image == 'i_tod_h2_arena_badge', 'the arena puts the badge in arena dress (' .. tostring( badge.image ) .. ')' )
    assert( digits() == '3', 'the window shows the LEVEL (' .. digits() .. ')' )
    local arena = geom()
    assert( arena.cap < round.cap, 'the level number is smaller than the round number' )
    assert( arena.inkTop >= CAPTION_BOTTOM + 1.5, string.format( 'the level number clears the LEVEL caption (ink top %.2f vs caption bottom %.2f)', arena.inkTop, CAPTION_BOTTOM ) )
    assert( arena.inkBottom <= WIN_B, 'the level number stays inside the window' )
    -- a 2 s re-send with the same level: nothing repaints
    local dress = badge.imageWrites
    notify( 'tod_arena', { 1, 3, 10, 1, 3, 12, 1 } )
    assert( badge.imageWrites == dress, 'a re-send does not re-dress the badge' )
    assert( digits() == '3', 'a re-send keeps the level' )
    -- the round advances under the fight: it stays off the badge
    notify( 'tod_round', { 6 } )
    assert( digits() == '3' and badge.image == 'i_tod_h2_arena_badge', 'a round change during the fight stays off the badge' )
    -- the Rampage Inducer: the arena twin has its own rampage dress
    push( 'todRampage', 1 )
    assert( badge.image == 'i_tod_h2_arena_badge_rampage', 'rampage on in the arena: the arena rampage badge (' .. tostring( badge.image ) .. ')' )
    assert( digits() == '3', 'rampage keeps the level' )
    push( 'todRampage', 0 )
    assert( badge.image == 'i_tod_h2_arena_badge', 'rampage off: the arena badge' )
    -- the next level
    notify( 'tod_arena', { 1, 4, 10, 0, 3, 0, 0 } )
    assert( digits() == '4', 'the next level writes 4 (' .. digits() .. ')' )
    -- level 10: two digits still fit the window
    notify( 'tod_arena', { 1, 10, 10, 3, 3, 9, 4 } )
    assert( digits() == '10', 'level 10 (' .. digits() .. ')' )
    local _, g10 = digits()
    assert( g10[ 1 ].l >= WIN_L and g10[ #g10 ].l < WIN_R, 'level 10 fits the window' )
    -- the ride home: the round badge, with the round that advanced meanwhile
    notify( 'tod_arena', { 0, 10, 10, 3, 3, 0, 0 } )
    assert( badge.image == 'i_tod_h2_round_badge', 'the ride home hands the badge back to the round (' .. tostring( badge.image ) .. ')' )
    assert( digits() == '6', 'the round that advanced during the fight is on the badge (' .. digits() .. ')' )
    assert( math.abs( geom().cap - round.cap ) < 0.001, 'the round number is back at its size' )
    -- rampage outside the arena: the round badge's rampage dress
    push( 'todRampage', 1 )
    assert( badge.image == 'i_tod_h2_round_badge_rampage', 'rampage outside the arena: the round rampage badge' )
    push( 'todRampage', 0 )
    -- harmless inputs: no args, an unrelated event, show 1 with no level
    notify( 'tod_arena', {} )
    notify( 'tod_other', { 1, 2 } )
    notify( 'tod_arena', { 1, 0, 10, 0, 3, 0, 0 } )
    assert( badge.image == 'i_tod_h2_round_badge' and digits() == '6', 'no args / an unrelated event / show with no level leave the round badge alone' )
    return true
end

assert( run( SOURCE ) )

-- NEGATIVE CONTROL 1: a plate that re-dresses the badge on every 2 s re-send must fail.
local bad1 = string.gsub( SOURCE, 'if lvl == arenaLvl then return end', '-- (gate removed)', 1 )
assert( bad1 ~= SOURCE, 'negative control 1 patched the plate' )
local ok1, err1 = pcall( run, bad1 )
assert( not ok1 and string.find( tostring( err1 ), 'a re-send does not re-dress the badge', 1, true ),
    'negative control 1: a re-send that repaints must be caught (' .. tostring( err1 ) .. ')' )

-- NEGATIVE CONTROL 2: a badge that ignores the arena must fail.
local bad2 = string.gsub( SOURCE, 'if arenaLvl > 0 then return luckRampageOn and ARENA_RMP_IMG or ARENA_IMG end', '', 1 )
assert( bad2 ~= SOURCE, 'negative control 2 patched the plate' )
local ok2, err2 = pcall( run, bad2 )
assert( not ok2 and string.find( tostring( err2 ), 'arena dress', 1, true ),
    'negative control 2: a badge that never changes must be caught (' .. tostring( err2 ) .. ')' )

print( 'ARENA BADGE HUD OK: the round badge reads BATTLE ARENA / LEVEL n through the fight and hands back to the round; 2 negative controls caught' )
