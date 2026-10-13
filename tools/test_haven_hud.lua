-- Lua 5.1 harness for TodHaven.lua (docs/202, the safe zones' screen effect): loads the
-- real module under BO3's no-new-globals rule, builds it on mocked LUI elements, and
-- drives it through its scriptNotify subscription exactly as _tod_haven.gsc does:
--     tod_haven ( inside, flags, state, left )   flags bit 0 = a crossing pulse, bit 1 = the hint lines;
--                                                state 1 = CORRUPTED, 2 = SAFE; left = guardians to kill
--     tod_haven_hit ( 1 )
--     tod_haven_state ( kind, floor, left )      1 = the guardians rise, 3 = a guardian down, 2 = secured
-- Asserts (v3, the two states): entering a SAFE field tints the edges cyan to the idle alpha
-- and pulses, SAFE ZONE rises (with the hint lines only when asked), the 2-second RE-SEND
-- changes nothing (no re-pulse), a hit inside flickers and a hit outside or mid-pulse does
-- not, leaving drains the tint (pulsing only on a real crossing, never on a teleport /
-- death); entering a CORRUPTED field tints the edges RED with CORRUPTED HAVEN and the
-- guardians-left line, a changed count re-shows the line without a pulse, a hit inside a
-- corrupted field never flickers, and the cleanse under your feet turns the tint cyan in
-- place; the three banners carry the floor number and the count; unrelated events and
-- missing arguments are harmless; the image is the zoned i_tod_haven_vignette; the close
-- hook resets the state. v4 THE DARKNESS: entering a CORRUPTED field takes the screen with
-- the near-black veil (i_tod_haven_darkness, under the tint), which then breathes (lo / hi) while
-- you stay, a re-send never restarts it, and it lifts at the cleanse and on the way out; a
-- SAFE field is never dark. v5 THE PURIFICATION: standing inside when the last guardian falls,
-- the convulsion banner (kind 4) GRIPS the veil to full (the breath stops) and flickers red,
-- every strobe (kind 6) flickers red again, the collapse (kind 5) blacks the screen out for the
-- void (in -> hold -> out, a plain fill) and clears the banner, the SECURED banner with the
-- near flag (left = 1) is the full white-cyan flash and the safe state lifts the darkness; on
-- the floor but outside the dome the banners show and nothing grips, flickers or blacks out;
-- far away SECURED is the ordinary pulse. Negative controls: a module that re-pulses on every
-- re-send, one that flickers on hits outside the field, one that flickers inside a CORRUPTED
-- field, one whose darkness survives the cleanse, one that darkens a SAFE field, one without
-- the house's drain cut, one whose collapse never blacks out and one that blacks out a player
-- OUTSIDE the dome must all FAIL.
local path = "ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua"
local f = io.open( path, "r" )
if not f then
	-- before the wire step the widget waits in art/haven/staged/ (outside the build's ui tree)
	path = "art/haven/staged/TodHaven.lua"
	f = assert( io.open( path, "r" ) )
end
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

local registered = {}
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
        RegisterImage = function( name ) registered[ name ] = true; return name end,
        require = function() end,
        pcall = pcall, type = type, pairs = pairs, ipairs = ipairs, string = string, table = table, math = math, tostring = tostring,
    }
    setmetatable( env, { __index = _G, __newindex = function( _, k ) error( "LUI Error: Tried to create global variable " .. k ) end } )
    local chunk = assert( loadstring( src, "@" .. path ) )
    setfenv( chunk, env )
    assert( pcall( chunk ) )
    local w = CoD.TodHaven.new( nil, 0 )
    assert( w.notify, "subscribed to scriptNotify" )
    local byId, glyphs = {}, {}
    for i, c in ipairs( w.children ) do
        c.index = i
        if c.id then byId[ c.id ] = c end
        if c.kind == "glyph" then table.insert( glyphs, c ) end
    end
    local tint, pulse, dark, void = byId.TodHavenTint, byId.TodHavenPulse, byId.TodHavenDark, byId.TodHavenVoid
    assert( tint and pulse, "a tint layer and a pulse layer" )
    assert( dark, "a darkness layer (v4)" )
    assert( void, "a void layer (v5)" )
    assert( #glyphs == 3, "the label + the two lines" )
    local function send( name, data ) w.notify( { name = name, data = data } ) end
    -- complete the last tween of an element (the engine's transition_complete)
    local function finish( el )
        local a = el.anims[ #el.anims ]
        local h = a and el.handlers[ "transition_complete_" .. a.name ]
        if h then h( el, { interrupted = false } ) end
    end
    return w, tint, pulse, glyphs[ 1 ], glyphs[ 2 ], send, finish, glyphs[ 3 ], dark, void
end

local function lastAnim( el ) return el.anims[ #el.anims ] and el.anims[ #el.anims ].name end
local function isRed( rgb ) return rgb and rgb[ 1 ] > 0.9 and rgb[ 2 ] < 0.6 end
local function isCyan( rgb ) return rgb and rgb[ 3 ] > 0.9 and rgb[ 1 ] < 0.9 end

local function isNearBlack( rgb ) return rgb and rgb[ 1 ] < 0.1 and rgb[ 2 ] < 0.1 and rgb[ 3 ] < 0.1 end

local function run( src )
    local w, tint, pulse, label, hint, send, finish, hint2, dark, void = build( src )
    assert( registered[ "i_tod_haven_vignette" ], "the tint art is the zoned i_tod_haven_vignette" )
    assert( registered[ "i_tod_haven_darkness" ] and dark.image == "i_tod_haven_darkness", "the darkness wears the zoned i_tod_haven_darkness" )
    assert( isNearBlack( dark.rgb ), "the darkness is tinted near-black" )
    assert( tint.image == "i_tod_haven_vignette" and pulse.image == "i_tod_haven_vignette", "both layers wear the vignette" )
    assert( void.image == nil and isNearBlack( void.rgb ), "the void is a plain black fill (no image: a bare UIImage draws solid)" )
    assert( tint.alpha == 0 and pulse.alpha == 0 and label.alpha == 0 and hint.alpha == 0 and hint2.alpha == 0 and dark.alpha == 0 and void.alpha == 0, "everything starts hidden" )
    assert( tint.index < pulse.index, "the pulse draws over the tint" )
    assert( dark.index < tint.index, "the darkness draws under the tint (the red lattice reads over the veil)" )
    assert( void.index > pulse.index and void.index < label.index, "the void draws over the tint and the pulse, under the text" )
    assert( label.opts.pool >= 23 and hint.opts.pool >= 31, "the label and line pools hold the longest banner (FLOOR 40 GUARDIANS RISE / DEFEAT THEM TO SECURE THE HAVEN)" )

    -- a hit outside the field never flickers
    send( "tod_haven_hit", { 1 } )
    assert( #pulse.anims == 0, "no flicker outside the field" )
    send( "tod_house_cut", { 1 } )
    assert( #pulse.anims == 0, "no drain cut outside the field (docs/207)" )

    -- ENTER a SAFE field, first time: cyan tint, pulse + both hint lines
    send( "tod_haven", { 1, 3, 2, 0 } )
    assert( dark.alpha == 0 and #dark.anims == 0, "a safe field is never dark" )
    assert( tint.alpha > 0.2 and tint.alpha < 0.5, "the idle tint (" .. tostring( tint.alpha ) .. ")" )
    assert( isCyan( tint.rgb ), "a safe field tints the edges cyan" )
    assert( lastAnim( pulse ) == "tod_haven_pulse_in" and pulse.alpha > 0.6, "the crossing pulse" )
    assert( label.text == "SAFE ZONE" and label.alpha == 1, "SAFE ZONE rises" )
    assert( hint.text == "ENEMIES SLOWED - DAMAGE REDUCED" and hint.alpha > 0.5, "the first hint line" )
    assert( hint2.text == "KILLS PAY 25 PERCENT" and hint2.alpha > 0.5, "the second hint line: the cost of sitting inside (the typeface has no percent sign)" )
    -- the pulse finishes: in -> out
    finish( pulse )
    assert( lastAnim( pulse ) == "tod_haven_pulse_out" and pulse.alpha == 0, "the pulse fades out" )
    finish( pulse )

    -- the label chain: in -> hold -> out
    finish( label )
    assert( lastAnim( label ) == "tod_haven_label_hold", "the label holds" )
    finish( label )
    assert( label.alpha == 0 and hint.alpha == 0 and hint2.alpha == 0, "the label and both hint lines fade away" )

    -- THE RE-SEND (every 2 s): nothing moves
    local tintAnims, pulseAnims = #tint.anims, #pulse.anims
    send( "tod_haven", { 1, 0, 2, 0 } )
    send( "tod_haven", { 1, 0, 2, 0 } )
    assert( #tint.anims == tintAnims and #pulse.anims == pulseAnims, "a re-send never re-pulses or re-tints" )

    -- a hit inside a safe field: a flicker; a second hit mid-flicker does not stack
    send( "tod_haven_hit", { 1 } )
    assert( lastAnim( pulse ) == "tod_haven_pulse_in" and pulse.alpha > 0.2 and pulse.alpha < 0.7, "a hit flickers the edges" )
    local n = #pulse.anims
    send( "tod_haven_hit", { 1 } )
    assert( #pulse.anims == n, "no stacked flicker mid-pulse" )
    finish( pulse ); finish( pulse )

    -- unrelated events / missing args
    send( "tod_jump_cine", { 1 } )
    send( "tod_haven", {} )
    assert( tint.alpha == 0, "tod_haven with no args = outside (a silent drain)" )
    send( "tod_haven", { 1, 1 } )
    assert( tint.alpha > 0.2 and isCyan( tint.rgb ), "re-entered; a missing state reads as safe" )
    finish( pulse ); finish( pulse )
    assert( hint.alpha == 0 and hint2.alpha == 0, "no hint lines when not asked" )

    -- EXIT through the field: drain + a last pulse
    send( "tod_haven", { 0, 1, 0, 0 } )
    assert( tint.alpha == 0 and lastAnim( tint ) == "tod_haven_tint", "the tint drains" )
    assert( lastAnim( pulse ) == "tod_haven_pulse_in" and pulse.alpha > 0.3, "leaving pulses once" )
    finish( pulse ); finish( pulse )

    -- a teleport / death exit: drain, no pulse
    send( "tod_haven", { 1, 1, 2, 0 } ); finish( pulse ); finish( pulse )
    local p = #pulse.anims
    send( "tod_haven", { 0, 0, 0, 0 } )
    assert( tint.alpha == 0 and #pulse.anims == p, "a silent exit never pulses" )

    -- ===== THE CORRUPTED STATE (v3) + THE DARKNESS (v4) =====
    send( "tod_haven", { 1, 1, 1, 3 } )
    assert( lastAnim( dark ) == "tod_haven_dark_in" and dark.alpha == 1, "the darkness takes the screen inside a corrupted field (" .. tostring( lastAnim( dark ) ) .. ")" )
    finish( dark )
    assert( lastAnim( dark ) == "tod_haven_dark_breathe" and dark.alpha > 0.7 and dark.alpha < 0.9, "then it breathes out (" .. tostring( dark.alpha ) .. ")" )
    finish( dark )
    assert( lastAnim( dark ) == "tod_haven_dark_breathe" and dark.alpha == 1, "and in again" )
    assert( tint.alpha > 0.2 and isRed( tint.rgb ), "a corrupted field tints the edges red (" .. tostring( tint.rgb and tint.rgb[ 1 ] ) .. ")" )
    assert( isRed( pulse.rgb ) and lastAnim( pulse ) == "tod_haven_pulse_in", "the crossing pulse is red" )
    assert( label.text == "CORRUPTED HAVEN" and label.alpha == 1, "CORRUPTED HAVEN rises (got " .. tostring( label.text ) .. ")" )
    assert( hint.text == "DEFEAT THE GUARDIANS - 3 LEFT" and hint.alpha > 0.5, "the guardians-left line (got " .. tostring( hint.text ) .. ")" )
    assert( hint2.alpha == 0, "no safe lines in a corrupted field" )
    finish( pulse ); finish( pulse )
    -- a hit inside a corrupted field never flickers (the field cuts nothing)
    local pc = #pulse.anims
    send( "tod_haven_hit", { 1 } )
    assert( #pulse.anims == pc, "no flicker inside a corrupted field" )
    -- a re-send with the same count: nothing; a changed count: the line follows, no pulse
    local la, da = #label.anims, #dark.anims
    send( "tod_haven", { 1, 0, 1, 3 } )
    assert( #label.anims == la and #pulse.anims == pc, "a corrupted re-send with the same count moves nothing" )
    assert( #dark.anims == da, "a corrupted re-send never restarts the darkness" )
    send( "tod_haven", { 1, 0, 1, 2 } )
    assert( hint.text == "DEFEAT THE GUARDIANS - 2 LEFT" and #label.anims > la and #pulse.anims == pc, "a changed count re-shows the line without a pulse" )
    send( "tod_haven", { 1, 0, 1, 0 } )
    assert( hint.text == "DEFEAT ITS GUARDIANS", "no count yet: DEFEAT ITS GUARDIANS" )
    -- THE DEALER'S HOUSE (docs/207): one bite of the drain, inside his corrupted dome: a red flicker
    local pcut = #pulse.anims
    send( "tod_house_cut", { 1 } )
    assert( #pulse.anims == pcut + 1 and lastAnim( pulse ) == "tod_haven_pulse_in" and isRed( pulse.rgb ), "the house's drain cut flickers red inside a corrupted field" )
    send( "tod_house_cut", { 1 } )
    assert( #pulse.anims == pcut + 1, "a second cut mid-flicker does not stack" )
    finish( pulse ); finish( pulse )
    -- THE CLEANSE under your feet: the server sends the safe state with a pulse; the tint turns cyan in place
    local lb = #label.anims
    send( "tod_haven_state", { 2, 30, 0 } )
    assert( label.text == "FLOOR 30 HAVEN SECURED" and hint.text == "SAFE ZONE ONLINE" and hint2.text == "ENEMIES SLOWED - DAMAGE REDUCED", "the SECURED banner (got " .. tostring( label.text ) .. ")" )
    assert( isCyan( pulse.rgb ) and lastAnim( pulse ) == "tod_haven_pulse_in", "the banner pulses cyan" )
    local lbAfter = #label.anims
    send( "tod_haven", { 1, 3, 2, 0 } )
    assert( isCyan( tint.rgb ) and tint.alpha > 0.2, "the tint turns cyan in place" )
    assert( lastAnim( dark ) == "tod_haven_dark_out" and dark.alpha == 0, "the cleanse lifts the darkness (" .. tostring( lastAnim( dark ) ) .. ")" )
    local dn = #dark.anims
    finish( dark )
    assert( #dark.anims == dn, "a lifted darkness never breathes again" )
    assert( #label.anims == lbAfter and label.text == "FLOOR 30 HAVEN SECURED", "the state change keeps the SECURED banner (no SAFE ZONE over it)" )
    finish( pulse ); finish( pulse )
    send( "tod_haven_hit", { 1 } )
    assert( lastAnim( pulse ) == "tod_haven_pulse_in", "hits flicker again once safe" )
    finish( pulse ); finish( pulse )
    local psafe = #pulse.anims
    send( "tod_house_cut", { 1 } )
    assert( #pulse.anims == psafe, "a drain cut in a safe field flickers nothing (docs/207)" )
    send( "tod_haven", { 0, 1, 0, 0 } ); finish( pulse ); finish( pulse )

    -- the other two banners, from outside any field
    send( "tod_haven_state", { 1, 40, 3 } )
    assert( label.text == "FLOOR 40 GUARDIANS RISE" and hint.text == "DEFEAT THEM TO SECURE THE HAVEN" and isRed( label.rgb ), "the WAKE banner (got " .. tostring( label.text ) .. ")" )
    assert( isRed( pulse.rgb ), "the wake pulses red" )
    finish( pulse ); finish( pulse )
    send( "tod_haven_state", { 3, 40, 2 } )
    assert( label.text == "GUARDIAN DOWN" and hint.text == "2 LEFT", "the GUARDIAN DOWN banner (got " .. tostring( hint.text ) .. ")" )
    send( "tod_haven_state", { 3, 40, 1 } )
    assert( hint.text == "ONE LEFT", "the last one reads ONE LEFT" )
    send( "tod_haven_state", {} )   -- a banner with no data is harmless
    assert( tint.alpha == 0, "banners never tint the edges" )
    assert( dark.alpha == 0, "banners never darken the screen" )

    -- the darkness lifts on the way out of a corrupted field, crossing or not
    send( "tod_haven", { 1, 1, 1, 2 } )
    assert( dark.alpha == 1, "dark again in a corrupted field" )
    send( "tod_haven", { 0, 0, 0, 0 } )
    assert( lastAnim( dark ) == "tod_haven_dark_out" and dark.alpha == 0, "leaving lifts the darkness" )
    finish( pulse ); finish( pulse )

    -- ===== THE PURIFICATION (v5), standing inside a corrupted field: the grip, the strobes, the void, the near flash =====
    send( "tod_haven", { 1, 1, 1, 1 } )
    finish( pulse ); finish( pulse )
    finish( dark )
    assert( lastAnim( dark ) == "tod_haven_dark_breathe" and dark.alpha < 0.9, "breathing out before the purification (" .. tostring( dark.alpha ) .. ")" )
    send( "tod_haven_state", { 4, 10, 0 } )          -- the convulsion begins
    assert( lastAnim( dark ) == "tod_haven_dark_grip" and dark.alpha == 1, "the convulsion grips the veil to full (" .. tostring( lastAnim( dark ) ) .. ")" )
    local dg = #dark.anims
    dark.handlers[ "transition_complete_tod_haven_dark_breathe" ]( dark, { interrupted = false } )
    assert( #dark.anims == dg, "a gripped veil never breathes again" )
    assert( label.text == "FLOOR 10 PURIFYING" and hint.text == "THE LAST GUARDIAN HAS FALLEN" and isRed( label.rgb ), "the PURIFYING banner (got " .. tostring( label.text ) .. ")" )
    assert( lastAnim( pulse ) == "tod_haven_pulse_in" and isRed( pulse.rgb ) and pulse.alpha > 0.4, "the convulsion flickers the edges red" )
    local ps = #pulse.anims
    send( "tod_haven_state", { 6, 10, 1 } )          -- one strobe of the dome
    assert( #pulse.anims == ps + 1 and lastAnim( pulse ) == "tod_haven_pulse_in" and isRed( pulse.rgb ), "each strobe flickers red, interrupting the last" )
    finish( pulse ); finish( pulse )
    assert( void.alpha == 0, "no void before the collapse" )
    send( "tod_haven_state", { 5, 10, 0 } )          -- the collapse
    assert( lastAnim( void ) == "tod_haven_void_in" and void.alpha == 1, "the collapse blacks the screen out (" .. tostring( lastAnim( void ) ) .. ")" )
    assert( label.alpha == 0, "the PURIFYING banner clears for the void" )
    finish( void )
    assert( lastAnim( void ) == "tod_haven_void_hold" and void.alpha == 1, "black holds for the void" )
    finish( void )
    assert( lastAnim( void ) == "tod_haven_void_out" and void.alpha == 0, "then clears into the bloom" )
    send( "tod_haven_state", { 2, 10, 1 } )          -- SECURED, and you are on its floor
    assert( label.text == "FLOOR 10 HAVEN SECURED" and lastAnim( pulse ) == "tod_haven_pulse_in" and pulse.alpha == 1 and isCyan( pulse.rgb ), "on the floor: the full white-cyan flash (" .. tostring( pulse.alpha ) .. ")" )
    send( "tod_haven", { 1, 1, 2, 0 } )              -- the safe state under your feet
    assert( lastAnim( dark ) == "tod_haven_dark_out" and dark.alpha == 0, "the bloom lifts the darkness" )
    finish( pulse ); finish( pulse )
    send( "tod_haven", { 0, 1, 0, 0 } ); finish( pulse ); finish( pulse )
    -- on the floor but OUTSIDE the dome: the banners only - no grip, no flicker, no void; far away SECURED = the ordinary pulse
    local da2, pa2, va2 = #dark.anims, #pulse.anims, #void.anims
    send( "tod_haven_state", { 4, 20, 0 } )
    assert( label.text == "FLOOR 20 PURIFYING" and #dark.anims == da2 and #pulse.anims == pa2, "outside the dome: the PURIFYING banner, no grip, no flicker" )
    send( "tod_haven_state", { 6, 20, 2 } )
    assert( #pulse.anims == pa2, "outside the dome: a strobe flickers nothing" )
    send( "tod_haven_state", { 5, 20, 0 } )
    assert( #void.anims == va2 and void.alpha == 0, "outside the dome: the collapse blacks nothing out" )
    send( "tod_haven_state", { 2, 20, 0 } )
    assert( lastAnim( pulse ) == "tod_haven_pulse_in" and pulse.alpha > 0.5 and pulse.alpha < 0.8 and isCyan( pulse.rgb ), "far away: the ordinary SECURED pulse (" .. tostring( pulse.alpha ) .. ")" )
    finish( pulse ); finish( pulse )

    -- close resets: the next HUD's first state is applied fresh
    send( "tod_haven", { 1, 0, 2, 0 } )
    w:close()
    return true
end

-- the shipping module passes
assert( run( source ) )

-- NEGATIVE CONTROL 1: a module that re-applies its state on every re-send must fail
local bad1 = string.gsub( source, "if not st.inside then\n%s+%-%- a crossing in", "if true then\n\t\t\t\t-- a crossing in", 1 )
assert( bad1 ~= source, "negative control 1 patched the module" )
local ok1, err1 = pcall( run, bad1 )
assert( not ok1 and string.find( tostring( err1 ), "re-send never re-pulses", 1, true ),
	"NEGATIVE CONTROL 1: a re-pulsing module must fail on the re-send check (got: " .. tostring( err1 ) .. ")" )

-- NEGATIVE CONTROL 2: a module that flickers on hits outside the field must fail
local bad2 = string.gsub( source, "if st.inside and st.state == STATE_SAFE and not st.pulsing then", "if not st.pulsing then", 1 )
assert( bad2 ~= source, "negative control 2 patched the module" )
local ok2, err2 = pcall( run, bad2 )
assert( not ok2 and string.find( tostring( err2 ), "no flicker outside the field", 1, true ),
	"NEGATIVE CONTROL 2: a flicker outside the field must fail on that check (got: " .. tostring( err2 ) .. ")" )

-- NEGATIVE CONTROL 3: a module that flickers on hits inside a CORRUPTED field must fail
local bad3 = string.gsub( source, "if st.inside and st.state == STATE_SAFE and not st.pulsing then", "if st.inside and not st.pulsing then", 1 )
assert( bad3 ~= source, "negative control 3 patched the module" )
local ok3, err3 = pcall( run, bad3 )
assert( not ok3 and string.find( tostring( err3 ), "no flicker inside a corrupted field", 1, true ),
	"NEGATIVE CONTROL 3: a flicker inside a corrupted field must fail on that check (got: " .. tostring( err3 ) .. ")" )

-- NEGATIVE CONTROL 4: a module whose darkness survives the cleanse must fail
local bad4 = string.gsub( source, "(darkness lifts%.\n.-)darkTo%( state == STATE_CORRUPT %)", "%1darkTo( true )", 1 )
assert( bad4 ~= source, "negative control 4 patched the module" )
local ok4, err4 = pcall( run, bad4 )
assert( not ok4 and string.find( tostring( err4 ), "the cleanse lifts the darkness", 1, true ),
	"NEGATIVE CONTROL 4: a darkness that survives the cleanse must fail on that check (got: " .. tostring( err4 ) .. ")" )

-- NEGATIVE CONTROL 5: a module that darkens a SAFE field must fail
local bad5 = string.gsub( source, "(no pulse flag, the tint still rises%)\n.-)darkTo%( state == STATE_CORRUPT %)", "%1darkTo( true )", 1 )
assert( bad5 ~= source, "negative control 5 patched the module" )
local ok5, err5 = pcall( run, bad5 )
assert( not ok5 and string.find( tostring( err5 ), "a safe field is never dark", 1, true ),
	"NEGATIVE CONTROL 5: a dark safe field must fail on that check (got: " .. tostring( err5 ) .. ")" )

-- NEGATIVE CONTROL 6: a module without the house's drain cut (docs/207) must fail
local bad6 = string.gsub( source, 'elseif name == "tod_house_cut" then', 'elseif name == "tod_house_cut_never" then', 1 )
assert( bad6 ~= source, "negative control 6 patched the module" )
local ok6, err6 = pcall( run, bad6 )
assert( not ok6 and string.find( tostring( err6 ), "the house's drain cut flickers", 1, true ),
	"NEGATIVE CONTROL 6: a missing drain cut must fail on that check (got: " .. tostring( err6 ) .. ")" )

-- NEGATIVE CONTROL 7: a module whose collapse never blacks the screen out must fail
local bad7 = string.gsub( source, "if insideCorrupt then\n%s+voidIn%(%)", "if false then\n\t\t\t\tvoidIn()", 1 )
assert( bad7 ~= source, "negative control 7 patched the module" )
local ok7, err7 = pcall( run, bad7 )
assert( not ok7 and string.find( tostring( err7 ), "the collapse blacks the screen out", 1, true ),
	"NEGATIVE CONTROL 7: a collapse without the void must fail on that check (got: " .. tostring( err7 ) .. ")" )

-- NEGATIVE CONTROL 8: a module that blacks out a player OUTSIDE the dome must fail
local bad8 = string.gsub( source, "if insideCorrupt then\n%s+voidIn%(%)", "if true then\n\t\t\t\tvoidIn()", 1 )
assert( bad8 ~= source, "negative control 8 patched the module" )
local ok8, err8 = pcall( run, bad8 )
assert( not ok8 and string.find( tostring( err8 ), "outside the dome: the collapse blacks nothing out", 1, true ),
	"NEGATIVE CONTROL 8: a void outside the dome must fail on that check (got: " .. tostring( err8 ) .. ")" )

print( "test_haven_hud: OK (the shipping module, two states + banners + the darkness + the house's drain cut + the purification, 8 negative controls)" )
