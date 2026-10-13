-- tools/test_toast.lua - THE TOAST (RT 2026-10-05, the red return; docs/218).
-- Run: python -B tools/run_lua_harness.py tools/test_toast.lua
--
-- User 2026-10-05: "the upgrade and choose class banners should be in our typography". A teammate's LEGENDARY pull,
-- his ON FIRE, and your own tier / re-arm / Archer lines were IPrintLnBold: the stock CenterConsole's bold engine font,
-- dropped across the card deal's banner band. They are one int event now (tod_toast: kind, who, code), drawn by
-- TodToast.lua in our glyph cells on the title plate. This loads the REAL module under BO3's no-new-globals rule on
-- mocked LUI elements and drives it through its scriptNotify subscription exactly as _tod_upgrade_ui.gsc does, and
-- requires:
--   * every kind draws its words (the same words the bold lines said), in our face, in its colour, on the plate;
--   * kinds 1-3 put the RIGHT player's name on top (PlayerList clientNum lookup), "A TEAMMATE" when he is gone;
--   * the plate sits clear of the deal banner (y 122) and the Black Market frame (y 112), inside the 1280 canvas;
--   * one beat chain: drop in -> hold -> fade; a new toast REPLACES the showing one without fading it out first;
--     an interrupted or stale tween never continues the chain (both completeAnimation semantics);
--   * shown over the card deal and the reel, hidden under any other veil owner (the jump cine, the class terminal);
--   * the fail-safe (no TodGlyphText) still draws in OUR face (the TTF), never the engine's default font;
--   * LOCKSTEP: the server half (the precache, the 3-int event, every caller's kind, no bold line left for these
--     moments) and the item names with _tod_shop.gsc item_name.
-- NEGATIVE CONTROLS (each must FAIL): a fail-safe without our TTF, a plate in the banner band, a toast that ignores the
-- veil, one hidden over the card deal, one that fades the old toast out on a replacement, one that names the wrong
-- player, and a server half that still prints the ON FIRE line in the stock font.
local path = "ui/uieditor/widgets/HUD/AetheriumWidgets/TodToast.lua"
local function readFile( p )
    local f = assert( io.open( p, "r" ), p .. " is in the tree" )
    local s = f:read( "*a" )
    f:close()
    return s
end
local source = readFile( path )

local LOUD = false
local function fire( el, interrupted )
    local name = el.running
    el.running = nil
    local h = name and el.handlers[ "transition_complete_" .. name ]
    if h then h( el, { interrupted = interrupted } ) end
end
local function newEl( kind )
    local el = { kind = kind, children = {}, alpha = 1, anims = {}, handlers = {}, rgb = { 1, 1, 1 } }
    local m = {}
    function m.setLeftRight( self, a, b, l, r ) self.lr = { a, b, l, r } end
    function m.setTopBottom( self, a, b, t, bo ) self.tb = { a, b, t, bo } end
    function m.setAlpha( self, a ) self.alpha = a end
    function m.setRGB( self, r, g, b ) self.rgb = { r, g, b } end
    function m.setImage( self, img ) self.image = img end
    function m.setText( self, s ) self.text = s end
    function m.setTTF( self, f ) self.ttf = f end
    function m.addElement( self, c ) table.insert( self.children, c ); c.parent = self end
    function m.beginAnimation( self, name, ms )
        if LOUD and self.running then fire( self, true ) end
        table.insert( self.anims, { name = name, ms = ms } )
        self.running = name
    end
    function m.completeAnimation( self )
        if LOUD and self.running then fire( self, false ) end
        self.running = nil
    end
    function m.registerEventHandler( self, name, fn ) self.handlers[ name ] = fn end
    function m.subscribeToGlobalModel( self, inst, a, b, fn ) self.notify = fn end
    function m.setClass( self ) end
    function m.close( self ) self.closed = true end
    setmetatable( el, { __index = function( t, k )
        if m[ k ] then return m[ k ] end
        if type( k ) == "string" and ( string.find( k, "^set" ) or string.find( k, "^get" ) ) then return function() end end
        return nil
    end } )
    return el
end

local registered, players, veil
local function build( src, glyph )
    registered, veil = {}, { owners = {}, fn = nil }
    players = { [ 0 ] = { cn = 0, name = "Jordan" }, [ 1 ] = { cn = 3, name = "xX_Slayer_Xx" } }
    local CoD = {
        TodUIOwnership = { Attach = function() end },
        GetScriptNotifyData = function( model ) return model.data end,
        TweenType = { Linear = 0 },
        TodHudVeil = { owners = veil.owners, Listen = function( el, fn ) veil.fn = fn; fn( false ) end },
    }
    if glyph then
        CoD.TodGlyphText = { new = function( opts ) local e = newEl( "glyph" ); e.opts = opts; return e end }
    end
    local LUI = { UIElement = { new = function() return newEl( "el" ) end },
                  UIImage = { new = function() return newEl( "img" ) end },
                  UIText = { new = function() return newEl( "text" ) end } }
    local Engine = {
        GetModelValue = function( m ) if m.value ~= nil then return m.value end return m.name end,
        GetModelForController = function() return "root" end,
        GetModel = function( root, key )
            local i, field = string.match( key, "^PlayerList%.(%d+)%.(%a+)$" )
            local p = i and players[ tonumber( i ) ]
            if not p then return nil end
            if field == "clientNum" then return { value = p.cn } end
            if field == "playerName" then return { value = p.name } end
            return nil
        end,
        Localize = function( s ) return s end,
    }
    local env = {
        CoD = CoD, LUI = LUI, Engine = Engine, Enum = { LUIAlignment = { LUI_ALIGNMENT_CENTER = 1 } },
        InheritFrom = function() return {} end,
        RegisterImage = function( name ) registered[ name ] = true; return name end,
        require = function() end,
        pcall = pcall, type = type, pairs = pairs, ipairs = ipairs, string = string, table = table, math = math,
        tostring = tostring, tonumber = tonumber,
    }
    setmetatable( env, { __index = _G, __newindex = function( _, k ) error( "LUI Error: Tried to create global variable " .. k ) end } )
    local chunk = assert( loadstring( src, "@" .. path ) )
    setfenv( chunk, env )
    assert( pcall( chunk ) )
    local w = CoD.TodToast.new( nil, 0 )
    assert( w.notify, "subscribed to scriptNotify" )
    return w, w.todToast.el, w.todToast.st, CoD.TodToast.T
end

local function finish( el )
    local a = el.anims[ #el.anims ]
    el.running = nil
    local h = a and el.handlers[ "transition_complete_" .. a.name ]
    if h then h( el, { interrupted = false } ) end
end
local function count( el, name )
    local n = 0
    for _, a in ipairs( el.anims ) do if a.name == name then n = n + 1 end end
    return n
end
local function near( a, b ) return math.abs( a - b ) < 0.001 end
local function same( rgb, want ) return rgb and near( rgb[ 1 ], want[ 1 ] ) and near( rgb[ 2 ], want[ 2 ] ) and near( rgb[ 3 ], want[ 3 ] ) end

local function run( src )
    local w, el, st, T = build( src, true )
    local P = el.plate
    local function send( k, who, code ) w.notify( { name = "tod_toast", data = { k, who, code } } ) end
    local function words()
        if el.one.alpha > 0 then return el.one.text, nil end
        return el.line1.text, el.line2.text
    end

    -- the plate: the zoned title plate, clear of the deal banner (122) and the Black Market frame (112)
    assert( registered[ "i_tod_title_plate" ] and el.back.image == "i_tod_title_plate", "the plate wears the zoned title plate" )
    assert( P.lr[ 3 ] >= 0 and P.lr[ 4 ] <= 1280 and P.tb[ 3 ] >= 0, "inside the 1280 x 720 canvas" )
    assert( P.tb[ 4 ] <= 112, "the plate ends above the Black Market frame (112) and the deal banner (122)" )
    assert( P.alpha == 0, "hidden until a toast" )
    for _, t in ipairs( { el.line1, el.line2, el.one } ) do
        assert( t.kind == "glyph" and t.opts.align == "center", "every line is our glyph face, centred" )
    end
    assert( el.line1.opts.fallbackTTF == "fonts/tod_tower1.ttf", "a name we cannot draw falls back to OUR face's TTF" )
    assert( el.line1.opts.pool >= #"ARCHER - HOLD YOUR TACTICAL TO GRAPPLE", "the top pool holds the Archer's first line" )
    assert( el.line2.opts.pool >= #"NO FALL DAMAGE - EARN HELL'S RETRIEVER FROM A CARD", "the second pool holds the Archer's second line" )
    assert( el.line2.opts.pool >= #( "PULLED A LEGENDARY " .. "QUICK REBOOT" ), "the second pool holds the longest market line" )

    -- unrelated events and garbage: nothing
    w.notify( { name = "tod_ptn_hud", data = { 1, 3, 0 } } )
    send( 0, 0, 0 ); send( 99, 0, 0 ); w.notify( { name = "tod_toast", data = {} } ); send( "x", nil, nil )
    assert( P.alpha == 0 and #P.anims == 0, "unknown kinds draw nothing, no error" )

    -- 1: a card LEGENDARY, the right player's name (client 3 is PlayerList row 1)
    send( 1, 3, 0 )
    local a, b = words()
    assert( a == "xX_Slayer_Xx" and b == "PULLED A LEGENDARY", "kind 1: his name over PULLED A LEGENDARY, got " .. tostring( a ) .. " / " .. tostring( b ) )
    assert( same( el.line1.rgb, T.WHITE ) and same( el.line2.rgb, T.GOLD ), "the name in white, the moment in LEGENDARY gold" )
    assert( P.alpha == 1 and P.anims[ #P.anims ].name == "tod_toast_in" and P.tb[ 3 ] == T.Y0, "it drops in" )
    finish( P )
    assert( P.anims[ #P.anims ].name == "tod_toast_hold" and P.anims[ #P.anims ].ms == T.HOLD_MS and P.alpha == 1, "then holds" )
    finish( P )
    assert( P.anims[ #P.anims ].name == "tod_toast_out" and P.alpha == 0, "then fades" )
    finish( P )
    assert( st.phase == 0 and not st.shown, "and is done" )

    -- 2: the Black Market, every item by name (LOCKSTEP _tod_shop.gsc item_name)
    for i, n in ipairs( T.ITEMS ) do
        send( 2, 0, i )
        a, b = words()
        assert( a == "Jordan" and b == "PULLED A LEGENDARY " .. n, "kind 2 names item " .. i )
    end
    send( 2, 0, 42 )
    a, b = words()
    assert( b == "PULLED A LEGENDARY", "an unknown item still announces the pull" )
    -- 3: ON FIRE in the heat's orange; a player who left reads A TEAMMATE
    send( 3, 9, 0 )
    a, b = words()
    assert( a == "A TEAMMATE" and b == "IS ON FIRE" and same( el.line2.rgb, T.HEAT ), "kind 3 (and a missing player)" )
    -- 4 / 5 / 6: the tier lines and the re-arm, the words the bold lines said
    send( 4, 0, 3 * 1000 + 20 )
    a, b = words()
    assert( a == "CLASS TIER 3 UNLOCKS AT FLOOR 20" and b == nil and same( el.one.rgb, T.AMBER ) and el.line1.alpha == 0, "kind 4: one line, amber" )
    send( 5, 0, 2 * 1000 + 40 )
    a, b = words()
    assert( a == "FLOOR 40 REACHED - CLASS TIER 2 UNLOCKED" and b == nil, "kind 5, packed: one line" )
    send( 5, 0, 100000 + 2 * 1000 + 40 )
    a, b = words()
    assert( a == "FLOOR 40 REACHED - CLASS TIER 2 UNLOCKED" and b == "PACK-A-PUNCH TO PROMOTE" and same( el.line2.rgb, T.AMBER ), "kind 5, dry: + PACK-A-PUNCH TO PROMOTE" )
    assert( el.one.alpha == 0, "the one-line slot is cleared under a two-line toast" )
    send( 6, 0, 0 )
    a, b = words()
    assert( a == "NEW WEAPONS ARE NOT PACK-A-PUNCHED" and b == nil, "kind 6" )
    -- 7: the Archer, two lines, held longer
    send( 7, 0, 0 )
    a, b = words()
    assert( a == "ARCHER - HOLD YOUR TACTICAL TO GRAPPLE" and b == "NO FALL DAMAGE - EARN HELL'S RETRIEVER FROM A CARD", "kind 7" )
    finish( P )
    assert( P.anims[ #P.anims ].ms == T.HOLD_LONG_MS, "the Archer's line holds longer" )

    -- a REPLACEMENT mid-hold: the new words drop in, the old toast never fades out first
    local outs = count( P, "tod_toast_out" )
    send( 1, 0, 0 )
    assert( count( P, "tod_toast_out" ) == outs and P.anims[ #P.anims ].name == "tod_toast_in" and P.alpha == 1,
        "a new toast replaces the showing one (no fade-out in between)" )
    -- an interrupted or stale tween never continues the chain
    local n = #P.anims
    P.handlers[ "transition_complete_tod_toast_in" ]( P, { interrupted = true } )
    assert( #P.anims == n, "an interrupted drop-in stops" )
    P.handlers[ "transition_complete_tod_toast_out" ]( P, { interrupted = false } )
    assert( st.phase == 1 and st.shown, "a stale fade's completion does not end a live toast" )
    finish( P ); finish( P ); finish( P )

    -- the veil: over the card deal and the reel it shows; under any other owner it hides
    veil.owners.cards = true; veil.fn( true )
    assert( w.alpha == 1, "shown over the card deal" )
    veil.owners.spin = true; veil.fn( true )
    assert( w.alpha == 1, "shown over the Black Market" )
    veil.owners.jump = true; veil.fn( true )
    assert( w.alpha == 0, "hidden under the jump cine" )
    veil.owners.jump = nil; veil.owners.cls_term = true; veil.fn( true )
    assert( w.alpha == 0, "hidden under the class terminal" )
    veil.owners.cls_term = nil; veil.owners.cards = nil; veil.owners.spin = nil; veil.fn( false )
    assert( w.alpha == 1, "back when the veil drops" )

    -- the fail-safe (no TodGlyphText): still OUR face, as the TTF
    local w2, el2 = build( src, false )
    for _, t in ipairs( { el2.line1, el2.line2, el2.one } ) do
        assert( t.kind == "text" and t.ttf == "fonts/tod_tower1.ttf", "the fail-safe draws in our face's TTF, never the engine font" )
    end
    return true
end

-- ---------------------------------------------------------------- the server half (LOCKSTEP), code only
local function code( p )
    local s = readFile( p )
    s = string.gsub( s, "/%*.-%*/", "" )
    s = string.gsub( s, "//[^\n]*", "" )
    return s
end
local function serverProblems( files )
    local bad = {}
    local ui = files.ui
    if not string.find( ui, '#precache( "eventstring", "tod_toast" );', 1, true ) then bad[ #bad + 1 ] = "tod_toast not precached" end
    if not string.find( ui, 'LuiNotifyEvent( &"tod_toast", 3, kind, who, code );', 1, true ) then bad[ #bad + 1 ] = "the 3-int event" end
    if not string.find( ui, 'self team_toast( 1, 0, "tod_pull_alert" );', 1, true ) then bad[ #bad + 1 ] = "kind 1 (announce_legendary)" end
    if not string.find( files.shop, 'self tod_upgrade_ui::team_toast( 2, item, "tod_pull_alert" );', 1, true ) then bad[ #bad + 1 ] = "kind 2 (the market)" end
    if not string.find( files.luck, 'self tod_upgrade_ui::team_toast( 3, 0, "tod_pull_alert" );', 1, true ) then bad[ #bad + 1 ] = "kind 3 (on fire)" end
    for _, k in ipairs( { "self_toast( 4,", "self_toast( 5, code );", "player tod_upgrade_ui::self_toast( 6, 0 );" } ) do
        if not string.find( files.upg, k, 1, true ) then bad[ #bad + 1 ] = "the upgrades' " .. k end
    end
    if not string.find( files.arch, "self tod_upgrade_ui::self_toast( 7, 0 );", 1, true ) then bad[ #bad + 1 ] = "kind 7 (the Archer)" end
    for name, s in pairs( files ) do
        for _, t in ipairs( { "PULLED A LEGENDARY", "IS ON FIRE", "UNLOCKS AT FLOOR", "NEW WEAPONS ARE NOT", "HOLD YOUR TACTICAL TO GRAPPLE", "REACHED - CLASS TIER" } ) do
            if string.find( s, t, 1, true ) then bad[ #bad + 1 ] = name .. " still prints '" .. t .. "' in the stock font" end
        end
    end
    local names = string.match( files.shop, 'names = array%( "", ([^)]*)%);' )
    local want = {}
    for n in string.gmatch( names or "", '"([^"]*)"' ) do want[ #want + 1 ] = n end
    local T = { ITEMS = {} }
    local items = string.match( source, "ITEMS = (%b{})" )
    for n in string.gmatch( items or "", '"([^"]*)"' ) do T.ITEMS[ #T.ITEMS + 1 ] = n end
    if #want ~= 9 or #T.ITEMS ~= #want then bad[ #bad + 1 ] = "item names: shop " .. #want .. ", toast " .. #T.ITEMS end
    for i = 1, #want do
        if want[ i ] ~= T.ITEMS[ i ] then bad[ #bad + 1 ] = "item " .. i .. ": shop " .. want[ i ] .. ", toast " .. tostring( T.ITEMS[ i ] ) end
    end
    return bad
end
local D = "scripts/zm/zm_tod2_cybercity/"
local files = { ui = code( D .. "_tod_upgrade_ui.gsc" ), shop = code( D .. "_tod_shop.gsc" ), luck = code( D .. "_tod_luck.gsc" ),
                upg = code( D .. "_tod_upgrades.gsc" ), arch = code( D .. "_tod_archer.gsc" ) }
local sp = serverProblems( files )
assert( #sp == 0, "the server half: " .. table.concat( sp, "; " ) )

assert( run( source ), "the toast (quiet completeAnimation)" )
LOUD = true
assert( run( source ), "the toast (loud completeAnimation: old completions fire mid-call)" )
LOUD = false
print( "toast harness passed (both completeAnimation semantics): 7 kinds in our face and their colours, the right name (and A TEAMMATE), the plate clear of the deal banner and the reel, drop-in / hold / fade, replacement without a fade, interrupted and stale tweens stop, shown over cards + spin, hidden under the jump cine + class terminal, the fail-safe in our TTF; server half LOCKSTEP (precache, the 3-int event, kinds 1-7, no bold line left, item names)." )

-- NEGATIVE CONTROLS: each mutation must FAIL.
local mutants = {
    { "has a fail-safe in the engine font",   "            t:setTTF( T.TTF )\n",                   "" },
    { "sits in the deal banner band",          "X0 = 352, Y0 = 38,",                                  "X0 = 352, Y0 = 122," },
    { "ignores the veil",                      "if on and not T.VEIL_OK[ key ] then",                 "if false then" },
    { "hides over the card deal",              "VEIL_OK = { cards = true, spin = true },",            "VEIL_OK = { spin = true }," },
    { "fades the old toast out on a replacement", "        st.phase = 0                       -- the old chain is dead before its tween is cut (a loud completion is ignored)\n",
      "        if st.phase == 2 then fadeOut() end\n" },
    { "names the wrong player",                "if cm and Engine.GetModelValue( cm ) == who then",   "if cm then" },
}
for _, m in ipairs( mutants ) do
    local s, n = string.gsub( source, m[ 2 ]:gsub( "%p", "%%%0" ), ( m[ 3 ]:gsub( "%%", "%%%%" ) ), 1 )
    assert( n == 1, "negative control '" .. m[ 1 ] .. "' found its line" )
    local ok = pcall( run, s )
    assert( not ok, "NEGATIVE CONTROL PASSED (the harness is blind): a toast that " .. m[ 1 ] )
end
local bold = {}
for k, v in pairs( files ) do bold[ k ] = v end
bold.luck = string.gsub( bold.luck, 'self tod_upgrade_ui::team_toast%( 3, 0, "tod_pull_alert" %);', 'p IPrintLnBold( self.playername + " IS ON FIRE" );' )
assert( #serverProblems( bold ) > 0, "NEGATIVE CONTROL PASSED (the harness is blind): the stock-font ON FIRE line" )
print( "toast negative controls: " .. ( #mutants + 1 ) .. " mutants, every one caught." )
