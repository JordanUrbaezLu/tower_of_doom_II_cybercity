-- tools/test_keycap_resolve.lua - THE CARD PANELS' KEYCAPS ARE SET IN OUR TYPEFACE (RT 2026-10-05).
-- Run: python -B tools/run_lua_harness.py tools/test_keycap_resolve.lua
--
-- User 2026-10-05: "the upgrade and choose class banners should be in our typography". The banners are baked in our
-- glyph cells; the one ENGINE-FONT text a keyboard player saw on those two screens was the keycaps (the SWITCH pair and
-- the HOLD-TO-LOCK plate), because CoD.TodKeycap.Name read the key through Engine.Localize, which in the live game
-- returns byte 21 + the UNEXPANDED token + byte 20 (docs/145): "[" has no glyph cell, so every cap fell back to a
-- UIText the engine filled with its own font and key picture. This drives the REAL TodKeycap (+ TodGlyphRow and the
-- generated metrics) with the engine's live answers and requires the key to be drawn by the glyph row:
--   +frag  -> "G OR MIDDLE MOUSE" -> one glyph, G     +gostand -> "SPACE" -> five glyphs
--   an unresolvable bind (GetKeyBindingLocalizedString returns nothing) still degrades to the old fallback text
--   a pad picture (a high byte) is still refused inside a cap (v18.32's backstop)
--   PadDevice() is unchanged (a keyboard read stays keyboard)
-- NEGATIVE CONTROL: the pre-RT Name (Localize only) must fall back to the engine-font text and be caught.

local noop = function() end
local methods = {}
local function newElement()
    return setmetatable( { children = {}, alpha = 1 }, { __index = function( _, k )
        if methods[ k ] then return methods[ k ] end
        if type( k ) == 'string' and ( k:match( '^set' ) or k:match( '^make' ) ) then return noop end
    end } )
end
function methods:addElement( e ) self.children[ #self.children + 1 ] = e; e.parent = self end
function methods:close() self.closed = true end
function methods:setAlpha( a ) self.alpha = a end
function methods:setImage( i ) self.image = i end
function methods:setText( t ) self.text = t end
function methods:setTTF( f ) self.ttf = f end

local BIND = { ['+frag'] = 'G OR MIDDLE MOUSE', ['+gostand'] = 'SPACE', ['+smoke'] = 'Q' }
local LOCALIZED = function( s ) return string.char( 21 ) .. s .. string.char( 20 ) end   -- the live engine (docs/145)
local GAMEPAD = false                                       -- Engine.IsGamepadEnabled's answer for the case under test
Engine = setmetatable( {
    Localize = function( s ) return LOCALIZED( s ) end,
    IsGamepadEnabled = function( c ) return GAMEPAD end,
    GetKeyBindingLocalizedString = function( c, cmd, i, a, b )
        assert( c == 7, 'the keycap must resolve on its own controller (got ' .. tostring( c ) .. ')' )
        assert( i == 0 and a == false and b == false, 'GetKeyBindingLocalizedString call shape changed' )
        return BIND[ cmd ]
    end,
}, { __index = function() return noop end } )
LUI = { UIElement = { new = newElement }, UIImage = { new = newElement } }
CoD = {}
function RegisterImage( s ) return s end

local function load( path )
    local f = assert( io.open( path, 'r' ) )
    local src = f:read( '*a' )
    f:close()
    return src
end
function require( mod )
    local path = mod:gsub( '%.', '/' ) .. '.lua'
    assert( loadstring( load( path ), path ) )()
end
require( 'ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphMetrics' )
require( 'ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphRow' )
local KEYCAP = 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodKeycap.lua'
local live = load( KEYCAP )

local function lit( kc )
    local n = 0
    for _, e in ipairs( kc.row.img ) do if e.alpha > 0 then n = n + 1 end end
    return n
end

local function cap( src, token )
    CoD.TodKeycap = nil
    assert( loadstring( src, KEYCAP ) )()
    local owner, text = newElement(), newElement()
    local kc = CoD.TodKeycap.make( owner, text, 7 )
    local s = kc.paint( 100, 100, 44, 22, token, 1 )
    return kc, text, s
end

local fails = {}
local function want( c, m ) if not c then fails[ #fails + 1 ] = m end end

local kc, text, s = cap( live, '[{+frag}]' )
want( s == 'G', '+frag resolved to ' .. tostring( s ) .. ', not G' )
want( lit( kc ) == 1 and text.alpha == 0, '+frag: the glyph row did not draw the cap alone (glyphs ' .. lit( kc ) .. ', fallback alpha ' .. tostring( text.alpha ) .. ')' )
want( text.ttf == 'fonts/tod_tower1.ttf', 'the fallback text is not set in the map typeface' )
kc, text, s = cap( live, '[{+gostand}]' )
want( s == 'SPACE' and lit( kc ) == 5 and text.alpha == 0, '+gostand: wanted SPACE in 5 glyphs, got ' .. tostring( s ) .. ' / ' .. lit( kc ) )
kc, text, s = cap( live, '[{+nothing}]' )
want( lit( kc ) == 0 and text.alpha == 1, 'an unresolvable bind must still degrade to the fallback text' )
BIND[ '+frag' ] = string.char( 200 ) .. 'LT'
kc, text, s = cap( live, '[{+frag}]' )
want( s == nil and lit( kc ) == 0 and text.alpha == 0, 'a pad picture was drawn inside a keycap' )
BIND[ '+frag' ] = 'G OR MIDDLE MOUSE'
want( CoD.TodKeycap.PadDevice() == false, 'PadDevice() turned a keyboard into a pad' )

-- A PAD IS NEVER TOLD A KEYBOARD KEY: with a gamepad enabled the cap keeps the engine's own expansion (the right
-- button) even though GetKeyBindingLocalizedString would answer with the keyboard's G.
GAMEPAD = true
kc, text, s = cap( live, '[{+frag}]' )
want( s ~= 'G' and lit( kc ) == 0 and text.alpha == 1, 'a gamepad-enabled client was shown the KEYBOARD key ' .. tostring( s ) )
GAMEPAD = false

-- the negative control: the pre-RT Name read Localize only
local old = live:gsub( 'local r = %( not CoD%.TodKeycap%.GamepadMaybe%( controller %) %) and CoD%.TodKeycap%.Resolve%( token, controller %)',
                       'local r = nil', 1 )
assert( old ~= live, 'negative control: the live Name no longer has the gated Resolve line this test plants out' )
kc, text, s = cap( old, '[{+frag}]' )
want( lit( kc ) == 0 and text.alpha == 1, 'NEGATIVE CONTROL: the Localize-only Name was NOT caught falling back to the engine font' )
-- the second negative control: an ungated Resolve (the first RT cut) tells a pad the keyboard key
local ungated = live:gsub( 'local r = %( not CoD%.TodKeycap%.GamepadMaybe%( controller %) %) and CoD%.TodKeycap%.Resolve%( token, controller %)',
                           'local r = CoD.TodKeycap.Resolve( token, controller )', 1 )
GAMEPAD = true
kc, text, s = cap( ungated, '[{+frag}]' )
want( s == 'G', 'NEGATIVE CONTROL: the ungated Resolve was NOT caught naming the keyboard key to a pad' )
GAMEPAD = false

if #fails > 0 then error( 'KEYCAP RESOLVE FAILED:\n  ' .. table.concat( fails, '\n  ' ) ) end
print( 'keycap resolve: +frag -> G and +gostand -> SPACE drawn in our glyph cells on the caller\'s controller; unresolved binds fall back (in our TTF); pad pictures refused; PadDevice unchanged; the Localize-only control is caught.' )
