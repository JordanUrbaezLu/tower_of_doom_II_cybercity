-- Lua 5.1 harness for TodArena.lua (docs/185 v2.1 / v2.2, THE BATTLE ARENA's readout): loads the
-- real module under BO3's no-new-globals rule, builds it on mocked LUI elements, and
-- drives it through its scriptNotify subscription exactly as _tod_arena.gsc does:
--     tod_arena ( show, level, levels, wave, waves, left, flags )
-- Asserts: the two rows (wave over count; the LEVEL lives on the round badge since v2.2,
-- tools/test_arena_badge.lua) start hidden; a show in the landing breath reads GET READY
-- with an empty count; a wave's start writes WAVE w OF n and the count, and flashes both;
-- a re-send with the same state and no flags changes NOTHING; a kill ticks the count; HOT
-- or fewer turns the count red; a cleared wave reads WAVE CLEARED (gold); a stale bit 2 (the
-- retired Keeper's boss flag) draws nothing of its own; the level flag reads LEVEL CLEARED; THE DEALER'S HOUSE flags (docs/207)
-- read THE FINAL FIGHT over THE DEALER; a hide fades every row and a
-- second hide is silent; missing arguments and unrelated events are harmless; the close
-- hook resets the state; the widget never names the level (that is the badge's). Negative
-- controls: a module that re-flashes on a re-send, one that names THE KEEPER again (W2E: he
-- retired whole 2026-10-05), and one that never names THE DEALER, must all FAIL.
local path = "ui/uieditor/widgets/HUD/AetheriumWidgets/TodArena.lua"
local f = assert( io.open( path, "r" ) )
local source = f:read( "*a" ); f:close()

local function newEl( kind )
    local el = { kind = kind, children = {}, alpha = 1, anims = {}, handlers = {} }
    local m = {}
    function m.setLeftRight( self, a, b, l, r ) self.lr = { a, b, l, r } end
    function m.setTopBottom( self, a, b, t, bo ) self.tb = { a, b, t, bo } end
    function m.setAlpha( self, a ) self.alpha = a end
    function m.setRGB( self, r, g, b ) self.rgb = { r, g, b } end
    function m.setImage( self, img ) self.image = img end
    function m.setText( self, s ) self.text = s end
    function m.addElement( self, c ) table.insert( self.children, c ); c.parent = self end
    function m.beginAnimation( self, name, ms ) table.insert( self.anims, { name = name, ms = ms } ) end
    function m.registerEventHandler( self, name, fn ) self.handlers[ name ] = fn end
    function m.subscribeToGlobalModel( self, inst, a, b, fn ) self.notify = fn end
    function m.setClass( self ) end
    function m.close( self ) if self.onClose then self:onClose() end end
    setmetatable( el, { __index = function( t, k )
        if m[ k ] then return m[ k ] end
        if type( k ) == "string" and ( string.find( k, "^set" ) or string.find( k, "^get" ) ) then return function() end end
        return nil
    end } )
    return el
end

local function build( src )
    local CoD = {
        TodUIOwnership = { Attach = function() end },
        GetScriptNotifyData = function( model ) return model.data end,
        TweenType = { Linear = 0 },
        TodGlyphText = { new = function( opts ) local e = newEl( "glyph" ); e.opts = opts; return e end },
    }
    local LUI = { UIElement = { new = function() return newEl( "el" ) end },
                  UIImage = { new = function() return newEl( "img" ) end },
                  OverrideFunction_CallOriginalSecond = function( el, fname, fn ) el.onClose = function( self ) fn( self ) end end }
    local env = {
        CoD = CoD, LUI = LUI,
        Engine = { GetModelValue = function( m ) return m.name end },
        InheritFrom = function() return {} end,
        RegisterImage = function( name ) return name end,
        require = function() end,
        pcall = pcall, type = type, pairs = pairs, ipairs = ipairs, string = string, table = table, math = math, tostring = tostring,
    }
    setmetatable( env, { __index = _G, __newindex = function( _, k ) error( "LUI Error: Tried to create global variable " .. k ) end } )
    local chunk = assert( loadstring( src, "@" .. path ) )
    setfenv( chunk, env )
    assert( pcall( chunk ) )
    local w = CoD.TodArena.new( nil, 0 )
    assert( w.notify, "subscribed to scriptNotify" )
    local glyphs = {}
    for _, c in ipairs( w.children ) do
        if c.kind == "glyph" then table.insert( glyphs, c ) end
    end
    assert( #glyphs == 2, "two rows: the wave and the count (the level is the round badge's, v2.2)" )
    local wave, count = glyphs[ 1 ], glyphs[ 2 ]
    local function send( name, data ) w.notify( { name = name, data = data } ) end
    -- complete the last tween of an element (the engine's transition_complete)
    local function finish( el )
        local a = el.anims[ #el.anims ]
        if a and el.handlers[ "transition_complete_" .. a.name ] then el.handlers[ "transition_complete_" .. a.name ]( el, { interrupted = false } ) end
    end
    return w, wave, count, send, finish
end

local function lastAnim( el ) return el.anims[ #el.anims ] and el.anims[ #el.anims ].name end
local function isRed( el ) return el.rgb and el.rgb[ 1 ] > 0.9 and el.rgb[ 2 ] < 0.5 end
local function isGold( el ) return el.rgb and el.rgb[ 1 ] > 0.9 and el.rgb[ 2 ] > 0.7 and el.rgb[ 3 ] < 0.6 end

local function run( src )
    local w, wave, count, send, finish = build( src )
    assert( wave.alpha == 0 and count.alpha == 0, "everything starts hidden" )
    assert( wave.opts.top < count.opts.top, "wave over count" )
    assert( count.opts.bottom - count.opts.top > wave.opts.bottom - wave.opts.top, "the count is the biggest line" )
    assert( wave.opts.top >= 40 and count.opts.bottom <= 110, "the readout keeps to the top band, clear of the haven label at y 94 (it never shows at the same time) and the round badge's corner" )
    -- a hide before any show is silent
    send( "tod_arena", { 0, 3, 10, 0, 3, 0, 0 } )
    assert( #wave.anims == 0 and #count.anims == 0, "a hide while hidden does nothing" )
    -- the landing breath
    send( "tod_arena", { 1, 3, 10, 0, 3, 0, 0 } )
    assert( wave.text == "GET READY", "the breath reads GET READY" )
    assert( count.text == "" and count.alpha == 0, "no count in the breath" )
    assert( wave.alpha > 0.5, "the wave row fades in" )
    -- wave 1 begins
    local wAnims = #wave.anims
    send( "tod_arena", { 1, 3, 10, 1, 3, 12, 1 } )
    assert( wave.text == "WAVE 1 OF 3", "the wave line (" .. tostring( wave.text ) .. ")" )
    assert( count.text == "12 LEFT" and not isRed( count ), "the count, white" )
    assert( lastAnim( wave ) == "tod_arena_wave_in" and wave.alpha == 1, "a wave's start flashes the wave line" )
    assert( lastAnim( count ) == "tod_arena_count_in" and count.alpha == 1, "... and the count" )
    finish( wave ); finish( count )
    assert( lastAnim( wave ) == "tod_arena_wave_out" and wave.alpha < 1 and wave.alpha > 0.5, "the wave line settles" )
    assert( lastAnim( count ) == "tod_arena_count_out" and count.alpha < 1 and count.alpha > 0.5, "the count settles" )
    -- a re-send: nothing moves
    local wA, cA = #wave.anims, #count.anims
    send( "tod_arena", { 1, 3, 10, 1, 3, 12, 0 } )
    assert( #wave.anims == wA and #count.anims == cA, "a re-send changes nothing" )
    -- the level is not this widget's (v2.2: the round badge draws it): a level-only change is a silent re-send
    send( "tod_arena", { 1, 4, 10, 1, 3, 12, 0 } )
    assert( #wave.anims == wA and #count.anims == cA and count.text == "12 LEFT", "the level is not this widget's: a level-only change draws nothing" )
    -- a kill ticks the count
    send( "tod_arena", { 1, 3, 10, 1, 3, 11, 0 } )
    assert( count.text == "11 LEFT" and lastAnim( count ) == "tod_arena_count_in", "a kill ticks the count" )
    assert( #wave.anims == wA, "a kill does not touch the wave line" )
    finish( count )
    -- the last few turn hot
    send( "tod_arena", { 1, 3, 10, 1, 3, 3, 0 } )
    assert( count.text == "3 LEFT" and isRed( count ), "3 LEFT is red (hunt them)" )
    send( "tod_arena", { 1, 3, 10, 1, 3, 4, 0 } )
    assert( not isRed( count ), "4 LEFT is white" )
    -- the wave is cleared
    send( "tod_arena", { 1, 3, 10, 1, 3, 0, 2 } )
    assert( count.text == "WAVE CLEARED" and isGold( count ), "WAVE CLEARED in gold" )
    assert( lastAnim( count ) == "tod_arena_count_in", "the clear flashes the count" )
    finish( count )
    -- wave 2 with a STALE bit 2 (the retired Keeper's boss flag): it draws nothing of its own
    send( "tod_arena", { 1, 3, 10, 2, 3, 5, 5 } )
    assert( wave.text == "WAVE 2 OF 3", "wave 2" )
    assert( count.text == "5 LEFT" and not isRed( count ), "a stale boss bit is the ordinary count (the Keeper retired)" )
    local kA = #count.anims
    send( "tod_arena", { 1, 3, 10, 2, 3, 5, 4 } )
    assert( count.text == "5 LEFT" and #count.anims == kA, "a stale boss bit on a re-send draws nothing" )
    send( "tod_arena", { 1, 3, 10, 2, 3, 2, 0 } )
    assert( count.text == "2 LEFT" and isRed( count ), "the count ticks down, hot" )
    -- the level is cleared
    send( "tod_arena", { 1, 3, 10, 3, 3, 0, 8 } )
    assert( count.text == "LEVEL CLEARED" and isGold( count ), "LEVEL CLEARED in gold" )
    -- THE DEALER'S HOUSE (docs/207): the house flag reads THE FINAL FIGHT; the dealer flag names him
    send( "tod_arena", { 1, 10, 10, 0, 3, 1, 16 + 32 + 1 } )
    assert( wave.text == "THE FINAL FIGHT", "the house flag: THE FINAL FIGHT (" .. tostring( wave.text ) .. ")" )
    assert( count.text == "THE DEALER" and isRed( count ), "the dealer flag names THE DEALER in red" )
    local hA = #count.anims
    send( "tod_arena", { 1, 10, 10, 0, 3, 1, 16 + 32 } )
    assert( count.text == "THE DEALER" and #count.anims == hA, "a house re-send holds THE DEALER and draws nothing" )
    send( "tod_arena", { 1, 10, 10, 0, 3, 0, 16 + 8 } )
    assert( wave.text == "THE FINAL FIGHT" and count.text == "LEVEL CLEARED" and isGold( count ), "the house's win: LEVEL CLEARED under THE FINAL FIGHT" )
    -- the ride home
    send( "tod_arena", { 0, 3, 10, 3, 3, 0, 0 } )
    assert( wave.alpha == 0 and count.alpha == 0, "a hide fades every row" )
    local wH, cH = #wave.anims, #count.anims
    send( "tod_arena", { 0, 3, 10, 3, 3, 0, 0 } )
    assert( #wave.anims == wH and #count.anims == cH, "a second hide is silent" )
    -- harmless inputs
    send( "tod_arena", {} )
    send( "tod_other", { 1, 2, 3 } )
    assert( wave.alpha == 0, "no args = hide; an unrelated event is ignored" )
    -- the close hook resets the state so a rebuilt widget starts clean
    send( "tod_arena", { 1, 4, 10, 1, 3, 9, 1 } )
    w:close()
    local wC = #wave.anims
    send( "tod_arena", { 1, 4, 10, 1, 3, 9, 0 } )
    assert( #wave.anims == wC + 1, "after close the next show is a fresh fade-in" )
    return true
end

assert( run( source ) )
assert( not string.find( source, "BATTLE ARENA - LEVEL", 1, true ), "the widget no longer names the level: the round badge does (docs/185 v2.2)" )
assert( not string.find( source, '"THE KEEPER"', 1, true ), "the retired Keeper is not named (W2E, 2026-10-05)" )

-- NEGATIVE CONTROL 1: a module that ticks the count on every 2-second re-send must fail
-- (the idempotent guard AND the tick's own "the line changed" test are both removed:
-- the guard alone is not what keeps a re-send still).
local bad1 = string.gsub( source, "if st%.show and line == st%.line and waveLine == st%.wave and not started and not cleared then\n\t\t\treturn", "if false then\n\t\t\treturn", 1 )
bad1 = string.gsub( bad1, "local ticked = st%.show and line ~= st%.line and not started and not cleared", "local ticked = st.show and not started and not cleared", 1 )
assert( bad1 ~= source, "negative control 1 patched the module" )
local ok1, err1 = pcall( run, bad1 )
assert( not ok1 and string.find( tostring( err1 ), "a re-send changes nothing", 1, true ),
    "negative control 1: a re-send that re-animates must be caught (" .. tostring( err1 ) .. ")" )

-- NEGATIVE CONTROL 2 (W2E): a module that names THE KEEPER again on bit 2 must fail.
local bad2 = string.gsub( source, '\t\telseif house then', '\t\telseif hasFlag( flags, 4 ) then\n\t\t\tline, rgb = "THE KEEPER", RED\n\t\telseif house then', 1 )
assert( bad2 ~= source, "negative control 2 patched the module" )
local ok2, err2 = pcall( run, bad2 )
assert( not ok2 and string.find( tostring( err2 ), "stale boss bit", 1, true ),
    "negative control 2: a Keeper line come back must be caught (" .. tostring( err2 ) .. ")" )

-- NEGATIVE CONTROL 3: a module that never names THE DEALER (docs/207) must fail.
local bad3 = string.gsub( source, 'line, rgb = "THE DEALER", RED', 'line, rgb = "THE KEEPER", RED', 1 )
assert( bad3 ~= source, "negative control 3 patched the module" )
local ok3, err3 = pcall( run, bad3 )
assert( not ok3 and string.find( tostring( err3 ), "THE DEALER", 1, true ),
    "negative control 3: a missing dealer line must be caught (" .. tostring( err3 ) .. ")" )

print( "ARENA HUD OK: TodArena.lua shows / flashes / ticks / clears / hides as the server drives it (+ THE DEALER'S HOUSE flags; the Keeper's bit retired); 3 negative controls caught" )
