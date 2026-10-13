-- Lua 5.1 harness for TodJumpCine.lua (docs/196, the first jump's opening scene):
-- loads the real module under BO3's no-new-globals rule, builds it on mocked LUI
-- elements, and drives it through its scriptNotify subscription exactly as
-- _tod_jumppad.gsc does (tod_jump_cine 1 / 0). Asserts: the HUD veil key "jump" is
-- held for exactly the scene (on -> off, the watchdog, the close hook), an
-- INTERRUPTED watchdog is ignored, repeats are idempotent, other events and missing
-- arguments are harmless, and the bars tween to BAR_H (2.35:1) and back to 0.
-- Negative controls: a module that never releases the veil, and one that ignores
-- the watchdog, must both FAIL this harness.
local path = "ui/uieditor/widgets/HUD/AetheriumWidgets/TodJumpCine.lua"
local f = assert( io.open( path, "r" ) )
local source = f:read( "*a" ); f:close()

local function newEl( kind )
    local el = { kind = kind, children = {}, alpha = 1, anims = {}, handlers = {} }
    local m = {}
    function m.setLeftRight( self, a, b, l, r ) self.lr = { a, b, l, r } end
    function m.setTopBottom( self, a, b, t, bo ) self.tb = { a, b, t, bo } end
    function m.setAlpha( self, a ) self.alpha = a end
    function m.setRGB( self, r, g, b ) self.rgb = { r, g, b } end
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
    local owners = {}
    local CoD = {
        TodUIOwnership = { Attach = function() end },
        GetScriptNotifyData = function( model ) return model.data end,
        TweenType = { Linear = 0 },
        TodHudVeil = { Set = function( key, on ) owners[ key ] = on or nil end },
    }
    local LUI = { UIElement = { new = function() return newEl( "el" ) end },
                  UIImage = { new = function() return newEl( "img" ) end },
                  OverrideFunction_CallOriginalSecond = function( el, fname, fn ) el.onClose = function( self ) fn( self ) end end }
    local env = {
        CoD = CoD, LUI = LUI,
        Engine = { GetModelValue = function( m ) return m.name end },
        InheritFrom = function() return {} end,
        require = function() end,
        pcall = pcall, type = type, pairs = pairs, ipairs = ipairs, string = string, table = table,
    }
    setmetatable( env, { __index = _G, __newindex = function( _, k ) error( "LUI Error: Tried to create global variable " .. k ) end } )
    local chunk = assert( loadstring( src, "@" .. path ) )
    setfenv( chunk, env )
    assert( pcall( chunk ) )
    local w = CoD.TodJumpCine.new( nil, 0 )
    assert( w.notify, "subscribed to scriptNotify" )
    local byId = {}
    for i, c in ipairs( w.children ) do
        if c.id then byId[ c.id ] = c; c.index = i end
    end
    local top, bot, watch, flash = byId.TodJumpCineTop, byId.TodJumpCineBot, byId.TodJumpCineWatch, byId.TodJumpCineFlash
    assert( top and bot and watch and flash, "two bars, a watchdog and the flash layer" )
    local function send( name, data ) w.notify( { name = name, data = data } ) end
    return w, owners, top, bot, watch, send, flash
end

local function lastAnim( el ) return el.anims[ #el.anims ] and el.anims[ #el.anims ].name end

-- THE IMPACT FLASH (tod_jump_cine 2; the first-jump crash scene): in, a HOLD at white, out
local function checkFlash( src )
    local w, owners, top, bot, watch, send, flash = build( src )
    assert( flash.index < top.index and flash.index < bot.index, "the flash draws UNDER the letterbox bars" )
    assert( flash.alpha == 0, "the flash starts invisible" )
    send( "tod_jump_cine", { 2 } )
    assert( flash.alpha == 0 and #flash.anims == 0, "an impact with no scene up never flashes a free screen" )

    send( "tod_jump_cine", { 1 } )
    send( "tod_jump_cine", { 2 } )
    assert( owners.jump == true, "the impact does NOT end the scene (the veil stays held)" )
    assert( top.tb[ 4 ] == 86, "the bars stay closed through the impact" )
    assert( lastAnim( flash ) == "tod_jump_flash_in" and flash.alpha == 1, "the impact flashes in to full white" )
    assert( flash.rgb[ 1 ] >= 0.9 and flash.rgb[ 2 ] >= 0.9, "the flash starts white-hot" )
    -- an interrupted step never advances the chain
    flash.handlers[ "transition_complete_tod_jump_flash_in" ]( flash, { interrupted = true } )
    assert( lastAnim( flash ) == "tod_jump_flash_in", "an interrupted flash-in does not advance" )
    flash.handlers[ "transition_complete_tod_jump_flash_in" ]( flash, {} )
    assert( lastAnim( flash ) == "tod_jump_flash_hold" and flash.alpha == 1, "the flash holds at white (nothing can be seen)" )
    flash.handlers[ "transition_complete_tod_jump_flash_hold" ]( flash, {} )
    assert( lastAnim( flash ) == "tod_jump_flash_out" and flash.alpha == 0, "then it clears" )
    assert( flash.rgb[ 1 ] == 1 and flash.rgb[ 2 ] < 0.7 and flash.rgb[ 3 ] < 0.4, "burning out through orange" )

    -- a second impact restarts the white-out; a stale step of the first cannot cut it short
    send( "tod_jump_cine", { 2 } )
    flash.handlers[ "transition_complete_tod_jump_flash_hold" ]( flash, { interrupted = true } )
    assert( lastAnim( flash ) == "tod_jump_flash_in" and flash.alpha == 1, "an interrupted hold step leaves the new flash at white" )

    -- the scene ending mid-flash stops the flash at once (a card deal, the flight ending)
    send( "tod_jump_cine", { 2 } )
    send( "tod_jump_cine", { 0 } )
    assert( not owners.jump and flash.alpha == 0, "OFF mid-flash clears the flash and releases the veil" )
    flash.handlers[ "transition_complete_tod_jump_flash_in" ]( flash, {} )
    assert( flash.alpha == 0 and lastAnim( flash ) ~= "tod_jump_flash_hold", "a late flash step after OFF stays dark" )
    return true
end

local function check( src )
    local w, owners, top, bot, watch, send = build( src )
    assert( top.rgb[ 1 ] == 0 and top.rgb[ 2 ] == 0 and top.rgb[ 3 ] == 0 and top.alpha == 1, "the top bar is solid black" )
    assert( top.tb[ 3 ] == 0 and top.tb[ 4 ] == 0 and bot.tb[ 3 ] == 0 and bot.tb[ 4 ] == 0, "the bars start closed (0 tall)" )
    assert( top.tb[ 1 ] == true and top.tb[ 2 ] == false and bot.tb[ 1 ] == false and bot.tb[ 2 ] == true, "anchored to the top / bottom edges" )
    assert( not owners.jump, "no veil before the scene" )

    send( "tod_spin_open", { 1 } )
    send( "tod_jump_cine_other", { 1 } )
    assert( not owners.jump, "other events are ignored" )

    send( "tod_jump_cine", { 1 } )
    assert( owners.jump == true, "the scene holds the veil" )
    assert( top.tb[ 4 ] == 86 and bot.tb[ 3 ] == -86, "the bars close to 86 of 720 (2.35:1), got " .. tostring( top.tb[ 4 ] ) )
    assert( watch.anims[ #watch.anims ].name == "tod_jump_watch", "the watchdog starts with the scene" )
    send( "tod_jump_cine", { 1 } )
    assert( #top.anims == 1, "a repeated ON does not restart the bars" )

    send( "tod_jump_cine", { 0 } )
    assert( not owners.jump, "OFF releases the veil" )
    assert( top.tb[ 4 ] == 0 and bot.tb[ 3 ] == 0, "the bars open back to 0" )
    assert( watch.anims[ #watch.anims ].name == "tod_jump_watch_off", "the watchdog is stopped" )

    -- an interrupted watchdog completion is not a timeout
    send( "tod_jump_cine", { 1 } )
    watch.handlers[ "transition_complete_tod_jump_watch" ]( watch, { interrupted = true } )
    assert( owners.jump == true, "an interrupted watchdog keeps the scene" )
    -- a real timeout (the OFF was lost) gives the HUD back
    watch.handlers[ "transition_complete_tod_jump_watch" ]( watch, {} )
    assert( not owners.jump, "the watchdog releases a lost scene" )
    assert( top.tb[ 4 ] == 0, "and opens the bars" )

    -- missing / junk arguments read as OFF, never as an error
    send( "tod_jump_cine", { 1 } )
    send( "tod_jump_cine", nil )
    assert( not owners.jump, "a missing argument reads as OFF" )
    send( "tod_jump_cine", { "x" } )
    assert( not owners.jump, "a junk argument reads as OFF" )

    -- the HUD closing mid-scene (death -> spectate) releases the veil
    send( "tod_jump_cine", { 1 } )
    w:close()
    assert( not owners.jump, "closing the HUD releases the veil" )
    return true
end

check( source )
checkFlash( source )

-- NEGATIVE CONTROLS: the harness must catch a module that forgets the veil on OFF,
-- and one that ignores its watchdog.
local bad1, n1 = string.gsub( source, "veilSet%( on %)", "if on then veilSet( on ) end", 1 )
assert( n1 == 1, "negative control 1 applies" )
assert( not pcall( check, bad1 ), "NEGATIVE CONTROL: a module that never releases the veil must fail" )
local bad2, n2 = string.gsub( source, "\t\tsetOn%( false %)\n\tend %)", "\tend )", 1 )
assert( n2 == 1, "negative control 2 applies" )
assert( not pcall( check, bad2 ), "NEGATIVE CONTROL: a module that ignores its watchdog must fail" )

-- the module is zoned (a require of an unzoned rawfile fails SILENTLY in game)
local zf = assert( io.open( "zone_source/zm_tod2_cybercity.zone", "r" ) )
local zone = zf:read( "*a" ); zf:close()
assert( string.find( zone, "\nrawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodJumpCine.lua", 1, true ), "TodJumpCine.lua is zoned" )
-- and the HUD builds it LAST (over every HUD piece) and the server precaches its event
local hf = assert( io.open( "ui/uieditor/menus/hud/AetheriumHud.lua", "r" ) )
local hud = hf:read( "*a" ); hf:close()
assert( string.find( hud, "CoD.TodJumpCine.new( self, controller )", 1, true ), "AetheriumHud builds the letterbox" )
local gf = assert( io.open( "scripts/zm/zm_tod2_cybercity/_tod_jumppad.gsc", "r" ) )
local gsc = gf:read( "*a" ); gf:close()
assert( string.find( gsc, '#precache( "eventstring", "tod_jump_cine" );', 1, true ), "_tod_jumppad.gsc precaches tod_jump_cine" )
assert( select( 2, string.gsub( gsc, 'LuiNotifyEvent%( &"tod_jump_cine", 1, 1 %)', "" ) ) == 1, "exactly one ON sender" )
assert( select( 2, string.gsub( gsc, 'LuiNotifyEvent%( &"tod_jump_cine", 1, 0 %)', "" ) ) == 1, "exactly one OFF sender (cine_end, every exit path)" )
print( "jump cine harness passed: veil held for exactly the scene (on/off/watchdog/interrupted/close), bars 0 -> 86 -> 0, bad args, 2 negative controls, zoned + built + precached." )

-- NEGATIVE CONTROL 3: the pre-crash handler read every value but 1 as OFF; an impact
-- (2) would have dropped the whole scene mid-shot. The flash harness must catch it.
local bad3, n3 = string.gsub( source, "if d%[ 1 %] == 2 then", "if false then", 1 )
assert( n3 == 1, "negative control 3 applies" )
assert( not pcall( checkFlash, bad3 ), "NEGATIVE CONTROL: an impact that ends the scene must fail" )
print( "test_jump_cine OK" )
