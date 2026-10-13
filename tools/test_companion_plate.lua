-- Lua 5.1 harness for TodCompanionPlate.lua (PK08, 2026-10-05, W2G): THE COMPANION STATUS PLATE.
-- Loads the real module under BO3's no-new-globals rule, builds it on mocked LUI elements and drives it
-- through its scriptNotify subscription exactly as _tod_partners.gsc push_hud does:
--     tod_ptn_hud ( companion + 1, state, value, len, flags )
--       state 0 none / 1 active / 2 rebuilding / 3 deploying; value = health percent (active, deploying) or
--       whole seconds left (rebuilding); len = the rebuild's whole length; flags 1 = frozen with its owner,
--       2 = its owner is dead / spectating
-- Asserts every state's look and every transition: hidden until a companion is held; the gift arrives (slides
-- in, portrait + name, ONLINE in cyan, the ring flashes, the bar powers up from empty); the 3-second
-- HEARTBEAT re-send of the same tuple draws NOTHING; a hit leaves a white ghost that holds then drains to the
-- new health and flicks the ring; at or under 35 % it reads DAMAGED in amber and the ring pulses (a loop that
-- stops when healed); frozen with its owner it reads HOLDING in steel; destroyed it flashes red, shakes, darkens
-- the portrait and reads DESTROYED, then BACK IN <n> while an amber bar fills one second ahead of the clock,
-- honouring the rebuild's own length (QUICK REBOOT); deploying it blinks in violet; back online it flashes
-- and powers up; the owner's death hides it and his respawn brings it back; a swapped companion is a fresh
-- arrival (never a hit); none hides it; garbage arguments are harmless; the ring, plate, bar and portraits are
-- the zoned images; every loop is a transition_complete chain that ignores interrupted tweens.
-- Negative controls (each must FAIL): a plate that redraws on the heartbeat, one that ignores the owner-out
-- flag, one that ignores the rebuild length, one with no DAMAGED tone, one that ignores the frozen flag, one
-- that never shows the damage ghost, and one whose pulse never stops.
local path = "ui/uieditor/widgets/HUD/AetheriumWidgets/TodCompanionPlate.lua"
local f = assert( io.open( path, "r" ), "TodCompanionPlate.lua is in the ui tree" )
local source = f:read( "*a" ); f:close()

-- TWO ENGINE SEMANTICS, both run: "quiet" = completeAnimation snaps a tween to its end silently and a new
-- beginAnimation drops the old one silently; "loud" = completeAnimation FIRES the running tween's
-- transition_complete (not interrupted) and a new beginAnimation fires the old one's as interrupted - the
-- worst case for a handler that reads state, which the plate must survive unchanged.
local LOUD = false
local function fire( el, interrupted )
    local name = el.running
    el.running = nil
    local h = name and el.handlers[ "transition_complete_" .. name ]
    if h then h( el, { interrupted = interrupted } ) end
end

local function newEl( kind )
    local el = { kind = kind, children = {}, alpha = 1, anims = {}, handlers = {}, rgb = { 1, 1, 1 }, completes = 0 }
    local m = {}
    function m.setLeftRight( self, a, b, l, r ) self.lr = { a, b, l, r } end
    function m.setTopBottom( self, a, b, t, bo ) self.tb = { a, b, t, bo } end
    function m.setAlpha( self, a ) self.alpha = a end
    function m.setRGB( self, r, g, b ) self.rgb = { r, g, b } end
    function m.setImage( self, img ) self.image = img end
    function m.setText( self, s ) self.text = s; self.texts = ( self.texts or 0 ) + 1 end
    function m.addElement( self, c ) table.insert( self.children, c ); c.parent = self end
    function m.beginAnimation( self, name, ms )
        if LOUD and self.running then fire( self, true ) end
        table.insert( self.anims, { name = name, ms = ms } )
        self.running = name
    end
    function m.completeAnimation( self )
        self.completes = self.completes + 1
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

local registered
local function build( src )
    registered = {}
    local CoD = {
        TodUIOwnership = { Attach = function() end },
        GetScriptNotifyData = function( model ) return model.data end,
        TweenType = { Linear = 0 },
        TodGlyphText = { new = function( opts ) local e = newEl( "glyph" ); e.opts = opts; return e end },
    }
    local LUI = { UIElement = { new = function() return newEl( "el" ) end },
                  UIImage = { new = function() return newEl( "img" ) end },
                  UIText = { new = function() return newEl( "text" ) end } }
    local env = {
        CoD = CoD, LUI = LUI, Enum = { LUIAlignment = {} },
        Engine = { GetModelValue = function( m ) return m.name end },
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
    local w = CoD.TodCompanionPlate.new( nil, 0 )
    assert( w.notify, "subscribed to scriptNotify" )
    assert( w.todCP and w.todCP.el and w.todCP.st, "the harness handle" )
    return w, w.todCP.el, w.todCP.st, CoD.TodCompanionPlate.CP
end

local function last( el ) return el.anims[ #el.anims ] and el.anims[ #el.anims ].name end
local function nanims( el ) return #el.anims end
local function finish( el )   -- the running tween reaches its end (the engine's transition_complete)
    local a = el.anims[ #el.anims ]
    el.running = nil
    local h = a and el.handlers[ "transition_complete_" .. a.name ]
    if h then h( el, { interrupted = false } ) end
end
local function near( a, b ) return math.abs( a - b ) < 0.001 end
local function same( rgb, want ) return rgb and near( rgb[ 1 ], want[ 1 ] ) and near( rgb[ 2 ], want[ 2 ] ) and near( rgb[ 3 ], want[ 3 ] ) end

local function run( src )
    local w, el, st, CP = build( src )
    local function send( d ) w.notify( { name = "tod_ptn_hud", data = d } ) end
    local function barX( frac ) return CP.BAR[ 1 ] + ( CP.BAR[ 3 ] - CP.BAR[ 1 ] ) * frac end
    local function total()
        local n = 0
        for _, e in pairs( el ) do n = n + nanims( e ) end
        return n
    end

    -- the zoned images, by literal
    for _, name in ipairs( { "i_tod_h2_comp_plate", "i_tod_h2_comp_ring", "i_tod_h2_hp_fill", "i_tod_h2_hp_frame" } ) do
        assert( registered[ name ], "registers " .. name )
    end
    assert( el.back.image == "i_tod_h2_comp_plate" and el.ring.image == "i_tod_h2_comp_ring" and el.flash.image == "i_tod_h2_comp_ring",
        "the plate and the ring wear their zoned art" )
    assert( el.track.image == "i_tod_h2_hp_fill" and el.fill.image == "i_tod_h2_hp_fill" and el.frame.image == "i_tod_h2_hp_frame",
        "the bar is the player's own health-bar art" )
    assert( el.plate.lr[ 3 ] == CP.X0 and el.plate.lr[ 4 ] == CP.X0 + CP.W and el.plate.tb[ 3 ] == CP.Y0, "the plate sits at CP" )
    assert( el.plate.alpha == 0, "hidden until a companion is held" )
    -- the glyph pools are a hard length cut in TodGlyphText: every name and every tag (a 3-digit countdown too)
    -- must fit its pool, or the plate would draw "BACK IN 10" for 100 seconds
    for _, n in ipairs( CP.NAMES ) do assert( #n <= CP.NAME_POOL, "the name pool holds " .. n ) end
    for _, t in ipairs( { "ONLINE", "DAMAGED", "DESTROYED", "BACK IN 100", "DEPLOYING", "HOLDING" } ) do
        assert( #t <= CP.TAG_POOL, "the tag pool holds " .. t )
    end
    assert( el.name.opts.pool == CP.NAME_POOL and el.tag.opts.pool == CP.TAG_POOL, "the glyph rows are built with those pools" )

    -- unrelated events and none held: nothing
    w.notify( { name = "tod_ptn_state", data = { 2, 1, 100, 2 } } )
    send( { 0, 0, 0, 0, 0 } )
    assert( el.plate.alpha == 0 and total() == 0, "none held / another event: hidden, nothing animates" )

    -- THE GIFT: TALON arrives at full health
    send( { 2, CP.ACTIVE, 100, 0, 0 } )
    assert( last( el.plate ) == "tod_cp_in" and el.plate.alpha == 1 and el.plate.lr[ 3 ] == CP.X0, "the plate slides in" )
    assert( el.port.image == "i_tod_spin_ico_comp_talon" and registered[ "i_tod_spin_ico_comp_talon" ], "the TALON portrait" )
    assert( el.name.text == "TALON", "the name in the typeface" )
    assert( el.tag.text == "ONLINE" and same( el.tag.rgb, CP.CYAN ), "ONLINE in cyan" )
    assert( same( el.ring.rgb, CP.CYAN ) and same( el.fill.rgb, CP.CYAN ), "the ring and the bar are cyan" )
    assert( last( el.flash ) == "tod_cp_flash" and last( el.fill ) == "tod_cp_fill" and near( el.fill.lr[ 4 ], barX( 1 ) ), "it arrives: the ring flashes, the bar powers up to full" )

    -- THE HEARTBEAT: the same tuple 3 s later draws nothing
    local n0, t0, g0 = total(), el.tag.texts, el.name.texts
    for _ = 1, 5 do send( { 2, CP.ACTIVE, 100, 0, 0 } ) end
    assert( total() == n0 and el.tag.texts == t0 and el.name.texts == g0, "a same-tuple re-send draws nothing" )

    -- A HIT: 100 -> 80 leaves a ghost that holds, then drains
    send( { 2, CP.ACTIVE, 80, 0, 0 } )
    assert( el.ghost.alpha > 0.5 and near( el.ghost.lr[ 4 ], barX( 1 ) ) and last( el.ghost ) == "tod_cp_ghost_hold", "the ghost keeps the lost health" )
    assert( near( el.fill.lr[ 4 ], barX( 0.8 ) ), "the bar drops to 80" )
    assert( last( el.flash ) == "tod_cp_flash", "the ring flicks" )
    send( { 2, CP.ACTIVE, 70, 0, 0 } )   -- a second hit inside the hold: the ghost keeps the top of the burst
    assert( near( el.ghost.lr[ 4 ], barX( 1 ) ) and near( st.ghost, 1 ), "a burst keeps one ghost from the top" )
    finish( el.ghost )
    assert( last( el.ghost ) == "tod_cp_ghost" and el.ghost.alpha == 0 and near( el.ghost.lr[ 4 ], barX( 0.7 ) ), "then it drains to the bar" )
    assert( el.tag.text == "ONLINE", "70 is still ONLINE" )

    -- DAMAGED: at or under LOW the tone turns amber and the ring pulses
    send( { 2, CP.ACTIVE, 30, 0, 0 } )
    assert( el.tag.text == "DAMAGED" and same( el.tag.rgb, CP.AMBER ) and same( el.ring.rgb, CP.AMBER ) and same( el.fill.rgb, CP.AMBER ), "DAMAGED in amber" )
    assert( last( el.ring ) == "tod_cp_pulse", "the ring pulses" )
    local p0 = nanims( el.ring )
    finish( el.ring )
    assert( nanims( el.ring ) == p0 + 1 and last( el.ring ) == "tod_cp_pulse", "the pulse is a loop" )
    send( { 2, CP.ACTIVE, 40, 0, 0 } )   -- NANO REPAIR heals it past LOW
    assert( el.tag.text == "ONLINE" and same( el.ring.rgb, CP.CYAN ), "healed past 35: ONLINE again" )
    assert( last( el.fill ) == "tod_cp_fill" and near( el.fill.lr[ 4 ], barX( 0.4 ) ), "a heal moves the bar up" )
    local p1 = nanims( el.ring )
    finish( el.ring )
    assert( nanims( el.ring ) == p1, "the pulse stops when healed" )
    assert( el.ring.alpha == 1, "and the ring is fully lit again" )

    -- HOLDING: frozen with its owner
    send( { 2, CP.ACTIVE, 40, 0, CP.F_FROZEN } )
    assert( el.tag.text == "HOLDING" and same( el.tag.rgb, CP.STEEL ) and same( el.ring.rgb, CP.STEEL ), "frozen: HOLDING in steel" )
    assert( el.port.alpha < 1, "the portrait dims while it holds" )
    send( { 2, CP.ACTIVE, 30, 0, CP.F_FROZEN } )
    assert( el.tag.text == "HOLDING" and not st.pulsing, "a frozen companion never pulses" )
    send( { 2, CP.ACTIVE, 30, 0, 0 } )
    assert( el.tag.text == "DAMAGED" and st.pulsing and el.port.alpha == 1, "thawed: DAMAGED again" )

    -- DESTROYED: the moment, then the countdown
    local shakes, flashes = nanims( el.portBox ), nanims( el.flash )
    send( { 2, CP.REBUILD, 45, 45, 0 } )
    assert( el.tag.text == "DESTROYED" and same( el.tag.rgb, CP.RED ) and same( el.ring.rgb, CP.RED ), "DESTROYED in red" )
    assert( nanims( el.portBox ) == shakes + 1 and last( el.portBox ) == "tod_cp_shake", "the portrait shakes" )
    assert( nanims( el.flash ) == flashes + 1 and same( el.flash.rgb, CP.RED ), "the ring flashes red" )
    assert( same( el.port.rgb, CP.DEAD_PORT ), "the portrait goes dark red" )
    assert( not st.pulsing, "no pulse once it is dead" )
    assert( same( el.fill.rgb, CP.AMBER ) and last( el.fill ) == "tod_cp_count" and near( el.fill.lr[ 4 ], barX( 1 / 45 ) ), "an amber bar, one second ahead" )
    assert( el.ghost.alpha == 0, "no ghost over the countdown" )
    for _ = 1, 12 do finish( el.portBox ) end
    assert( el.portBox.lr[ 3 ] == CP.PORT[ 1 ], "the shake settles where it started" )
    finish( el.hold )
    assert( el.tag.text == "BACK IN 45" and same( el.tag.rgb, CP.AMBER ), "then BACK IN 45" )
    shakes, flashes = nanims( el.portBox ), nanims( el.flash )
    send( { 2, CP.REBUILD, 44, 45, 0 } )
    assert( el.tag.text == "BACK IN 44" and near( el.fill.lr[ 4 ], barX( 2 / 45 ) ), "the countdown ticks, the bar runs ahead" )
    assert( nanims( el.portBox ) == shakes and nanims( el.flash ) == flashes, "a tick never re-plays the death" )
    -- QUICK REBOOT socketed mid-rebuild: the server shortens it; the bar honours the new length
    send( { 2, CP.REBUILD, 5, 10, 0 } )
    assert( el.tag.text == "BACK IN 5" and near( el.fill.lr[ 4 ], barX( 6 / 10 ) ), "the rebuild's own length (QUICK REBOOT)" )

    -- DEPLOYING: on its way, blinking violet
    send( { 2, CP.DEPLOYING, 100, 0, 0 } )
    assert( el.tag.text == "DEPLOYING" and same( el.tag.rgb, CP.VIOLET ) and same( el.ring.rgb, CP.VIOLET ), "DEPLOYING in violet" )
    assert( last( el.port ) == "tod_cp_blink" and not same( el.port.rgb, CP.DEAD_PORT ), "the portrait blinks, lit again" )
    local b0 = nanims( el.port )
    finish( el.port )
    assert( nanims( el.port ) == b0 + 1, "the blink is a loop" )
    send( { 2, CP.DEPLOYING, 100, 0, CP.F_FROZEN } )
    assert( el.tag.text == "HOLDING" and not st.blinking, "a deploy held by a spin reads HOLDING, still" )

    -- BACK ONLINE
    flashes = nanims( el.flash )
    send( { 2, CP.ACTIVE, 100, 0, 0 } )
    assert( el.tag.text == "ONLINE" and nanims( el.flash ) == flashes + 1 and not st.blinking, "back online: the ring flashes, the blink stops" )
    assert( near( el.fill.lr[ 4 ], barX( 1 ) ) and same( el.fill.rgb, CP.CYAN ) and el.fill.alpha == 1, "the bar powers up, cyan" )

    -- THE OWNER DIES: hidden; his respawn brings it back
    send( { 2, CP.DEPLOYING, 100, 0, CP.F_OUT } )
    assert( last( el.plate ) == "tod_cp_out" and el.plate.alpha == 0, "the owner is dead: the plate fades away" )
    local h0 = total()
    send( { 2, CP.DEPLOYING, 100, 0, CP.F_OUT + CP.F_FROZEN } )
    assert( total() == h0, "while he is out nothing draws" )
    send( { 2, CP.ACTIVE, 100, 0, 0 } )
    assert( last( el.plate ) == "tod_cp_in" and el.plate.alpha == 1 and el.tag.text == "ONLINE" and el.name.text == "TALON", "respawned: back, as a fresh arrival" )

    -- A SWAPPED COMPANION (a tester's bench): a fresh arrival, never a hit
    send( { 4, CP.ACTIVE, 60, 0, 0 } )
    assert( el.port.image == "i_tod_spin_ico_comp_cerberus" and el.name.text == "CERBERUS", "the new portrait and name" )
    assert( el.ghost.alpha == 0, "never a ghost on a swap" )
    send( { 1, CP.ACTIVE, 100, 0, 0 } )
    assert( el.name.text == "PROTECTOR" and el.port.image == "i_tod_spin_ico_comp_protector", "the short name fits: PROTECTOR" )
    send( { 3, CP.ACTIVE, 100, 0, 0 } )
    assert( el.name.text == "R.A.P.S." and el.port.image == "i_tod_spin_ico_comp_raps", "R.A.P.S." )

    -- NONE: hidden
    send( { 0, CP.NONE, 0, 0, 0 } )
    assert( el.plate.alpha == 0 and not st.shown, "none held: hidden" )

    -- garbage
    send( {} ); send( { "x" } ); send( { 9, 1, 50, 0, 0 } ); send( { 2, 7, 50, 0, 0 } ); send( { 2, -1, 50, 0, 0 } )
    assert( el.plate.alpha == 0, "unknown companions / states stay hidden, no error" )

    -- interrupted tweens never continue a loop
    send( { 2, CP.ACTIVE, 20, 0, 0 } )
    local i0 = nanims( el.ring )
    el.ring.handlers[ "transition_complete_tod_cp_pulse" ]( el.ring, { interrupted = true } )
    assert( nanims( el.ring ) == i0, "an interrupted pulse stops" )
    return true
end

assert( run( source ), "the plate (quiet completeAnimation)" )
LOUD = true
assert( run( source ), "the plate (loud completeAnimation: old completions fire mid-call)" )
LOUD = false
print( "companion plate harness passed (both completeAnimation semantics): hidden until held, the gift's arrival, the heartbeat draws nothing, hit ghost hold + drain (one per burst), DAMAGED pulse loop and its stop, HOLDING when frozen (no pulse, deploy held), DESTROYED flash + shake + dark portrait then BACK IN n with the bar one second ahead, QUICK REBOOT's length, DEPLOYING blink loop, back online, owner death hides + respawn returns, swaps are arrivals, every short name, none hides, garbage, interrupted loops stop." )

-- NEGATIVE CONTROLS: each mutation must FAIL the run.
local mutants = {
    { "redraws on the heartbeat",        "if key == st.key then",                                     "if false then" },
    { "ignores the owner-out flag",      "if out or not known then",                                  "if not known then" },
    { "ignores the rebuild length",      "local total = ( len >= value and len > 0 ) and len or value", "local total = 45" },
    { "has no DAMAGED tone",             "elseif st.value <= CP.LOW then",                            "elseif false then" },
    { "ignores the frozen flag",         "st.frozen = ( flags % 2 == 1 )",                            "st.frozen = false" },
    { "never shows the damage ghost",    "if was == CP.ACTIVE and value < wasValue then",             "if false then" },
    { "never stops its pulse",           "if ( event and event.interrupted ) or not st.pulsing then", "if ( event and event.interrupted ) then" },
    { "cuts a 3-digit countdown",        "TAG_POOL = 11",                                             "TAG_POOL = 10" },
}
-- (loud = run under the loud completeAnimation semantics: an ordering bug only shows there)
mutants[ #mutants + 1 ] = { "arms its ghost before completeAnimation", "st.ghostHolding = false\n                    el.ghost:completeAnimation()\n                    st.ghost = top\n                    st.ghostHolding = true",
    "st.ghost = top\n                    st.ghostHolding = true\n                    el.ghost:completeAnimation()", loud = true }
for _, m in ipairs( mutants ) do
    local s, n = string.gsub( source, m[ 2 ]:gsub( "%p", "%%%0" ), ( m[ 3 ]:gsub( "%%", "%%%%" ) ), 1 )
    assert( n == 1, "negative control '" .. m[ 1 ] .. "' found its line" )
    LOUD = m.loud or false
    local ok = pcall( run, s )
    LOUD = false
    assert( not ok, "NEGATIVE CONTROL PASSED (the harness is blind): a plate that " .. m[ 1 ] )
end
print( "companion plate negative controls: " .. #mutants .. " mutants, every one caught." )
