-- =============================================================================
-- test_class_terminal_ui.lua - THE CROWN'S CLASS TERMINAL, the panel half (2026-10-01).
--
-- _tod_class_terminal.gsc reopens the class draft's panel (tod_class_select.lua)
-- mid-game with todClsShow 3. This runs the REAL menu under Lua 5.1 (lupa, via
-- tools/run_lua_harness.py, every build) with engine-shaped mocks, and drives its
-- four model fields exactly the way the server writes them, then proves:
--   * show 3 is the choosing state with the TERMINAL chrome: the baked banner
--     ("PERMANENT FOR THIS RUN") hidden, SWITCH CLASS + its two lines set in the
--     map's typeface and centred, a CURRENT tag centred over the player's own card
--     (CoD.TodClass -> its draft slot), the clock line reading CLOSES IN;
--   * the whole HUD is veiled (CoD.TodHudVeil key "cls_term") while a visit is up,
--     through its confirm flash (show 2), and unveiled at show 0;
--   * THE DRAFT IS UNTOUCHED: show 1 keeps the banner, veils nothing, sets no
--     terminal rows;
--   * a panel CLOSED mid-visit (the server closes the menu after every visit, and
--     a death closes it) drops the veil - with a NEGATIVE CONTROL: the same menu
--     built without its close hook leaves the HUD hidden;
--   * no glyph rows (TodGlyphRow failed to load) = the plain LUI title, restored
--     to the draft's state after the visit;
--   * 25 terminal visits leak no element and close nothing twice.
-- =============================================================================
local noop = function() end
local elements = {}
local methods = {}
local function newElement()
    local e = setmetatable( { children = {}, handlers = {}, alpha = 1, text = nil }, { __index = function( _, k )
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
    assert( not self.closed, 'element closed twice: ' .. tostring( self.id ) )
    self.closed = true
    if self.parent then
        for i, e in ipairs( self.parent.children ) do if e == self then table.remove( self.parent.children, i ); break end end
        self.parent = nil
    end
end
function methods:setAlpha( a ) self.alpha = a end
function methods:setText( t ) self.text = t end
function methods:setImage( i ) self.image = i end
function methods:setTopBottom( a, b, t, bt ) self.top, self.bottom = t, bt end
function methods:setLeftRight( a, b, l, r ) self.left, self.right = l, r end
function methods:registerEventHandler( k, v ) self.handlers[ k ] = v end
function methods:completeAnimation() end
function methods:beginAnimation() end
function methods:playSound() end
function methods:getOwner() return 0 end
function methods:processEvent( e ) if self.handlers[ e.name ] then return self.handlers[ e.name ]( self, e ) end end
local subs, values = {}, {}
function methods:subscribeToModel( m, fn ) subs[ m ] = fn end
local function enums() return setmetatable( {}, { __index = function( t, k ) local v = enums(); rawset( t, k, v ); return v end } ) end
Enum = enums()
Engine = setmetatable( {
    Localize = function( s ) return s end, GetModelForController = function() return 'ctrl' end,
    CreateModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
    GetModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
    GetModelValue = function( m ) return values[ m ] or 0 end,
}, { __index = function() return noop end } )
CoD = { Menu = { NewForUIEditor = newElement }, TweenType = { Linear = 0 }, TodClass = 3 }
LUI = { UIElement = { new = newElement }, UIImage = { new = newElement }, UIText = { new = newElement }, createMenu = {} }
local closeHooks = true
function LUI.OverrideFunction_CallOriginalSecond( e, key, fn )
    if not closeHooks then return end
    local old = e[ key ]; e[ key ] = function( ... ) fn( ... ); if old then return old( ... ) end end
end
function InheritFrom() return {} end
function RegisterImage( s ) return s end
require = function() end
local function live() local n = 0; for _, e in ipairs( elements ) do if not e.closed then n = n + 1 end end; return n end

dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodUIOwnership.lua' )
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodHudVeil.lua' )
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodGlyphMetrics.lua' )
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodGlyphRow.lua' )
CoD.TextWithBg = { new = function()
    local e = newElement()
    CoD.TodUIOwnership.Attach( e )
    e.Text = newElement(); e.Bg = newElement()
    e:addElement( e.Text ); e:addElement( e.Bg )
    return e
end }

-- every glyph row the menu makes, with what it last drew
local rows = {}
local realMake = CoD.TodGlyphRow.make
CoD.TodGlyphRow.make = function( owner, n )
    local r = realMake( owner, n )
    local rec = { shown = false }
    rows[ #rows + 1 ] = rec
    local set, hide = r.set, r.hide
    r.set = function( s, cap, rightX, base, picker )
        local w = set( s, cap, rightX, base, picker )
        rec.str, rec.cap, rec.cx, rec.base, rec.shown = s, cap, rightX - w / 2, base, w > 0
        return w
    end
    r.hide = function() hide(); rec.shown = false end
    return r
end
local function rowOf( s ) for _, r in ipairs( rows ) do if r.str == s and r.shown then return r end end end
local function anyTermRowShown()
    for _, r in ipairs( rows ) do
        if r.shown and ( r.str == 'SWITCH CLASS' or r.str == 'CURRENT' or ( r.str or '' ):find( 'CARDS STAY', 1, true ) or ( r.str or '' ):find( 'LOCK YOUR OWN', 1, true ) ) then return true end
    end
    return false
end

dofile( 'ui/uieditor/menus/hud/tod_class_select.lua' )

local function drive( show, focus, time, hold )
    values[ 'ctrl.todUpgFocus' ] = focus; if subs[ 'ctrl.todUpgFocus' ] then subs[ 'ctrl.todUpgFocus' ]( 'ctrl.todUpgFocus' ) end
    values[ 'ctrl.todUpgTime' ] = time;   if subs[ 'ctrl.todUpgTime' ] then subs[ 'ctrl.todUpgTime' ]( 'ctrl.todUpgTime' ) end
    values[ 'ctrl.todUpgHold' ] = hold;   if subs[ 'ctrl.todUpgHold' ] then subs[ 'ctrl.todUpgHold' ]( 'ctrl.todUpgHold' ) end
    values[ 'ctrl.todClsShow' ] = show;   if subs[ 'ctrl.todClsShow' ] then subs[ 'ctrl.todClsShow' ]( 'ctrl.todClsShow' ) end
end
local function banner()
    for _, e in ipairs( elements ) do if not e.closed and e.image == 'i_tod_banner_choose_class' then return e end end
end
local function textOf( needle )
    for _, e in ipairs( elements ) do if not e.closed and type( e.text ) == 'string' and e.text:find( needle, 1, true ) then return e end end
end
local passes = 0
local function check( ok, msg ) assert( ok, 'FAIL ' .. msg ); passes = passes + 1 end

-- the card geometry the Lua derives (4 classes: 210 wide, 298 apart, the row starting at 88)
local CARD_W, CARD_PITCH, CARD_X0 = 210, 298, 88

-- ---- a terminal visit ---------------------------------------------------------
local menu = LUI.createMenu.tod_class_select( 0 )
check( CoD.TodHudVeil.Hidden() == false, 'the HUD is not veiled while the panel sits hidden' )
CoD.TodClass = 3   -- the player is a BREACHER (draft slot 3)
drive( 3, 3, 8, 0 )
check( CoD.TodHudVeil.Hidden() == true, 'show 3 veils the whole HUD (key cls_term)' )
check( banner() ~= nil and banner().alpha == 0, 'the baked PERMANENT FOR THIS RUN banner hides for the terminal' )
local t = rowOf( 'SWITCH CLASS' )
check( t ~= nil and math.abs( t.cx - 640 ) < 0.01 and t.cap == 24, 'SWITCH CLASS is set in the typeface, centred on the screen' )
check( rowOf( 'TIER AND CARDS STAY - NEW WEAPON STARTS UNPACKED' ) ~= nil, 'the carry-over line is drawn (every glyph exists)' )
check( rowOf( 'LOCK YOUR OWN CLASS TO CLOSE' ) ~= nil, 'the how-to-close line is drawn' )
local cur = rowOf( 'CURRENT' )
check( cur ~= nil and math.abs( cur.cx - ( CARD_X0 + 2 * CARD_PITCH + CARD_W / 2 ) ) < 0.01, 'CURRENT is centred over the player\'s own card (slot 3)' )
check( cur.base <= 207 and cur.base - cur.cap >= 196, 'CURRENT sits between the title block and the card top' )
check( textOf( 'RANDOM IN' ) == nil, 'nothing says RANDOM: the terminal never picks for the player' )

-- the focus moves; the CURRENT tag stays on the player's class
drive( 3, 1, 7, 0 )
cur = rowOf( 'CURRENT' )
check( cur ~= nil and math.abs( cur.cx - ( CARD_X0 + 2 * CARD_PITCH + CARD_W / 2 ) ) < 0.01, 'moving the focus does not move the CURRENT tag' )

-- the confirm flash keeps the terminal chrome and the veil
drive( 2, 1, 0, 15 )
check( CoD.TodHudVeil.Hidden() == true and banner().alpha == 0 and rowOf( 'SWITCH CLASS' ) ~= nil, 'the confirm flash (show 2) keeps the terminal chrome and the veil' )

-- the visit ends
drive( 0, 0, 0, 0 )
check( CoD.TodHudVeil.Hidden() == false, 'show 0 drops the veil' )
check( not anyTermRowShown(), 'show 0 hides every terminal row' )
check( banner().alpha == 1, 'the banner is back for the next draft-shaped use' )

-- ---- THE DRAFT IS UNTOUCHED ----------------------------------------------------
drive( 1, 1, 15, 0 )
check( CoD.TodHudVeil.Hidden() == false, 'the draft (show 1) veils nothing' )
check( banner().alpha == 1 and not anyTermRowShown(), 'the draft keeps its banner and draws no terminal rows' )
drive( 2, 1, 0, 15 )
check( CoD.TodHudVeil.Hidden() == false and not anyTermRowShown(), 'the draft\'s confirm flash stays draft-shaped' )
drive( 0, 0, 0, 0 )

-- ---- the tag follows the class ---------------------------------------------------
CoD.TodClass = 1   -- now a NECROMANCER (slot 1)
drive( 3, 1, 8, 0 )
cur = rowOf( 'CURRENT' )
check( cur ~= nil and math.abs( cur.cx - ( CARD_X0 + CARD_W / 2 ) ) < 0.01, 'CURRENT follows CoD.TodClass to slot 1' )

-- ---- CLOSED MID-VISIT: the close hook drops the veil -------------------------------
menu:close()
check( CoD.TodHudVeil.Hidden() == false, 'a panel closed mid-visit (the server closes it; a death closes it) drops the veil' )
-- NEGATIVE CONTROL: the same panel without its close hook leaves the HUD hidden
closeHooks = false
local bare = LUI.createMenu.tod_class_select( 0 )
closeHooks = true
drive( 3, 3, 8, 0 )
check( CoD.TodHudVeil.Hidden() == true, 'negative control: a hookless panel veils the HUD' )
bare:close()
check( CoD.TodHudVeil.Hidden() == true, 'negative control: without the close hook the HUD stays hidden after the close (the hook is load-bearing)' )
CoD.TodHudVeil.Set( 'cls_term', false )

-- ---- no glyph rows: the plain LUI title ---------------------------------------------
local gr = CoD.TodGlyphRow
CoD.TodGlyphRow = nil
local plain = LUI.createMenu.tod_class_select( 0 )
CoD.TodGlyphRow = gr
drive( 3, 2, 8, 0 )
check( textOf( 'SWITCH CLASS' ) ~= nil, 'no typeface: the title falls back to LUI text' )
drive( 0, 0, 0, 0 )
check( textOf( 'SWITCH CLASS' ) == nil, 'no typeface: the fallback title clears after the visit (the banner draft shows its own art)' )
plain:close()

-- ---- 25 visits, no leaks ---------------------------------------------------------------
elements = {}
for pass = 1, 25 do
    local before = live()
    local m = LUI.createMenu.tod_class_select( 0 )
    drive( 3, ( pass % 4 ) + 1, 8, pass % 16 )
    drive( 2, ( pass % 4 ) + 1, 0, 15 )
    if pass % 2 == 0 then drive( 0, 0, 0, 0 ) end   -- half closed after show 0, half mid-visit
    m:close()
    check( live() == before, 'terminal visit ' .. pass .. ' leaked ' .. ( live() - before ) .. ' elements' )
    check( CoD.TodHudVeil.Hidden() == false, 'terminal visit ' .. pass .. ' left the HUD veiled' )
end

print( 'Class terminal panel passed: ' .. passes .. ' checks (terminal chrome, CURRENT tag, HUD veil + its close hook with a negative control, the draft untouched, the text fallback, 25 leak-free visits).' )
