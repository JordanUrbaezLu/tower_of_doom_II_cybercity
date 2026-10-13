-- tools/test_tier_gate_strip.lua - THE CLASS TIER FLOOR-GATE STRIP under the real upgrade menu (PK01, 2026-10-04).
-- Run: python -B tools/run_lua_harness.py tools/test_tier_gate_strip.lua
--
-- The strips i_tod_tier_gate_2 / _3 were re-baked for the descent (TIER 2 AT FLOOR 40 / TIER 3 AT FLOOR 20,
-- tools/artgen/packs/pk01_card_text_rebake.py) and USE_TIER_GATE_ART switched back on. This builds the REAL
-- LUI.createMenu.tod_upgrade with the REAL TodPull + GENERATED TodCardArt manifest (the engine mocks are
-- tools/test_card_pull.lua's, verbatim) as LIVE classes - every one of them draws its cards as THE PULL's layered
-- v2 faces - and proves the panel draws the strip where tod_upgrade.lua's measured layout puts it, ON TOP:
--   * a floor-blocked Archer (CoD.TodTierNeed 10) on an ordinary deal: the tier-2 strip in the left gutter,
--     50..330 x 216..276, under the CLASS badge - and card B's banner left alone;
--   * an Archer whose right card is the locked TIER card (domain 24, tier 3) with need 30, and a Breacher with the
--     tier-2 card and need 10: the strip stamped across card B's illustration, 654..934 x 336..396, the LAST
--     element the menu adds and above card B's layered face (dimmed 0.55, grey-blue), with THE PULL's "NEW TIER"
--     banner (same band, still holding when focus opens) cut the moment the stamp lands;
--   * no strip while the cards are still being revealed, and none for a player who is not blocked.
-- Negative controls (run by hand when this file or the strip code is edited):
--   * the pre-PK01 tod_upgrade.lua (USE_TIER_GATE_ART = not TIER_DESCENT): no strip is ever drawn;
--   * the strip constructed BEFORE CoD.TodPull.Attach (the first PK01 cut): it draws UNDER card B's v2 face;
--   * no CoD.TodPull.BannerOff on the stamp: the NEW TIER banner shows round the strip.

local noop = function() end
local elements = {}
local methods = {}
local function newElement()
    local e = setmetatable( { children = {}, handlers = {}, alpha = 1, rgb = { 1, 1, 1 } }, { __index = function( _, k )
        if methods[ k ] then return methods[ k ] end
        if k:match( '^set' ) or k:match( '^make' ) or k:match( '^subscribe' ) or k:match( '^link' ) or k:match( '^Add' ) then return noop end
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
    assert( not self.closed, 'element closed twice' )
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
function methods:setImage( i ) self.image = i end
function methods:setText( t ) self.text = t end
function methods:completeAnimation() self.anim = nil end
-- every tween is recorded, with the phase it started in (see TWEENS below)
local TWEENS = {}
local PHASE = 'setup'
function methods:beginAnimation( name, ms ) self.anim = { name = name, ms = ms }; TWEENS[ #TWEENS + 1 ] = { name = name, ms = ms, phase = PHASE, el = self } end
function methods:getOwner() return 0 end
function methods:processEvent( e ) if self.handlers[ e.name ] then return self.handlers[ e.name ]( self, e ) end end
function methods:getLocalLeftRight() return true, false, 0, 80 end
function methods:getLocalTopBottom() return true, false, 0, 20 end

-- models: subscribeToModel stores the callback; push() sets a value and fires it
local MODELS, SUBS = {}, {}
function methods:subscribeToModel( m, fn ) SUBS[ m ] = SUBS[ m ] or {}; table.insert( SUBS[ m ], fn ) end
local function push( name, v )
    local key = 'ctrl.' .. name
    MODELS[ key ] = v
    for _, fn in ipairs( SUBS[ key ] or {} ) do fn( key ) end
end

local function enums() return setmetatable( {}, { __index = function( t, k ) local v = enums(); rawset( t, k, v ); return v end } ) end
Enum = enums()
Engine = setmetatable( {
    Localize = function( s ) return s end, GetModelForController = function() return 'ctrl' end,
    GetModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
    CreateModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
    GetModelValue = function( k ) return MODELS[ k ] or 0 end, IsInGame = function() return true end,
    GetCurrentMap = function() return 'zm_tod2_cybercity' end, GetClientNum = function() return 0 end,
}, { __index = function() return noop end } )
DataSources = {}
DataSourceHelpers = { ListSetup = function( _, fn ) return fn end }
function ListHelper_SetupDataSource( _, fn ) return { __build = fn } end
CoD = { Menu = { NewForUIEditor = newElement }, TweenType = { Linear = 0, Bounce = 1 }, isZombie = true, TodOwned = {}, TodClass = 2, TodClassTier = 1 }   -- the Archer: a LIVE class, so card B draws THE PULL's layered v2 face (TodCardArt classes)
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
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodCardArt.lua' )   -- the real GENERATED manifest (FX sprites)
dofile( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodPull.lua' )
dofile( 'ui/uieditor/menus/hud/tod_upgrade.lua' )
do local n = 0; Enum.UIVisibilityBit = setmetatable( {}, { __index = function( t, k ) n = n + 1; rawset( t, k, n ); return n end } ) end

local menu = LUI.createMenu.tod_upgrade( 0 )
local checks = 0
local function ok( cond, msg ) checks = checks + 1; assert( cond, msg ) end
local function strips()
    local hits = {}
    for _, e in ipairs( elements ) do
        if e.image == 'i_tod_tier_gate_2' or e.image == 'i_tod_tier_gate_3' then hits[ #hits + 1 ] = e end
    end
    return hits
end
local function indexIn( parent, e )
    for i, c in ipairs( parent.children ) do if c == e then return i end end
end
-- card B's layered face: the layer that holds the v2 BODY at card B's x (TodPull BuildFace2)
local function faceB()
    for _, e in ipairs( elements ) do
        if e.image == CoD.TodCardArt.body and e.l == 677 and e.parent then return e.parent, e end
    end
end
-- card B's v2 illustration (V2.art starts 29 in from the card's x)
local function art( name )
    for _, e in ipairs( elements ) do if e.image == name and e.l == 677 + 29 then return e end end
end
local hold = 0
local function beat() hold = hold + 1; push( 'todUpgHold', hold ) end
-- the server's reveal order (_tod_upgrade_ui.gsc reveal_deal): both sides cleared, show, a beat per rung, then
-- each slot's domain FLIPS it; bl = card B's level field (for the TIER card the tier code (class-1)*2 + (tier-2))
local function deal( bd, bl )
    hold = 0
    push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 0 ); push( 'todUpgBD', 0 ); push( 'todUpgBR', 0 ); push( 'todUpgBL', bl or 0 ); push( 'todUpgSolo', 0 )
    push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
    beat(); beat(); push( 'todUpgAD', 4 ); beat(); beat(); push( 'todUpgBD', bd ); beat()
end

ok( CoD.TodCardArt and CoD.TodCardArt.body and CoD.TodCardArt.classes and CoD.TodCardArt.classes.assault and CoD.TodCardArt.classes.heavy,
    'the generated card-art manifest lists the Archer and the Breacher as layered classes' )
local layerB = faceB()
ok( layerB ~= nil, 'THE PULL built card B its layered face (the v2 body at x 677)' )

-- 1. an Archer blocked for tier 2 (need 10 = FLOOR 40 on the descent), an ordinary deal: the gutter
CoD.TodClass = 2
CoD.TodTierNeed = 10
deal( 3 )
local h = strips()
ok( #h == 0 or h[ 1 ].alpha == 0, 'no strip while the cards are still being revealed' )
push( 'todUpgFocus', 1 )
h = strips()
ok( #h == 1, 'exactly one strip element, got ' .. #h )
local s = h[ 1 ]
ok( s.image == 'i_tod_tier_gate_2' and s.alpha == 1, 'the tier-2 strip is drawn (image ' .. tostring( s.image ) .. ', alpha ' .. tostring( s.alpha ) .. ')' )
ok( s.l == 50 and s.r == 330 and s.t == 216 and s.b == 276, 'the strip sits in the gutter under the CLASS badge, got ' .. table.concat( { s.l, s.r, s.t, s.b }, ',' ) )
ok( CoD.TodPull.last.banner.alpha == 1, "in the gutter the strip leaves card B's banner alone (nothing of it is covered)" )
push( 'todUpgShow', 0 )

-- 2 + 3. the locked TIER card dealt in slot B: the stamp, over card B's layered face
local function stampCase( cls, need, tier, tierArt )
    local who = 'class ' .. cls .. ' tier ' .. tier .. ': '
    CoD.TodClass = cls
    CoD.TodTierNeed = need
    deal( 24, ( cls - 1 ) * 2 + ( tier - 2 ) )
    ok( s.alpha == 0, who .. 'no stamp while card B is still being revealed' )
    ok( CoD.TodPull.last.banner.alpha == 1, who .. 'THE PULL showed card B its NEW TIER banner at the flip (the control for the cut below)' )
    push( 'todUpgFocus', 1 )
    ok( s.image == 'i_tod_tier_gate_' .. tier and s.alpha == 1, who .. 'the strip is drawn (image ' .. tostring( s.image ) .. ', alpha ' .. tostring( s.alpha ) .. ')' )
    ok( s.l == 654 and s.r == 934 and s.t == 336 and s.b == 396, who .. 'the strip is stamped across card B, got ' .. table.concat( { s.l, s.r, s.t, s.b }, ',' ) )
    local pic = art( tierArt )
    ok( pic ~= nil and pic.alpha > 0 and pic.parent == layerB, who .. 'card B draws its LAYERED tier picture ' .. tierArt .. ' (the v2 face, not the old baked card)' )
    ok( math.abs( layerB.alpha - 0.55 ) < 1e-6 and math.abs( layerB.rgb[ 1 ] - 0.55 ) < 1e-6 and math.abs( layerB.rgb[ 3 ] - 0.72 ) < 1e-6,
        who .. 'the locked v2 face is dimmed 0.55 and tinted grey-blue (alpha ' .. tostring( layerB.alpha ) .. ')' )
    local menuEl = s.parent
    ok( menuEl ~= nil and layerB.parent == menuEl, who .. "the strip and card B's face are siblings in the menu" )
    ok( indexIn( menuEl, s ) > indexIn( menuEl, layerB ),
        who .. "the stamp draws OVER card B's layered face (strip child " .. tostring( indexIn( menuEl, s ) ) .. ', face child ' .. tostring( indexIn( menuEl, layerB ) ) .. ')' )
    ok( menuEl.children[ #menuEl.children ] == s, who .. 'the strip is the LAST element the menu adds (over the banner, shards and flash too)' )
    ok( CoD.TodPull.last.banner.alpha == 0, who .. "the stamp cut card B's NEW TIER banner (it holds in the same band)" )
    push( 'todUpgShow', 0 )
end
stampCase( 2, 30, 3, 'i_tod_card2_art_tier_assault_3' )   -- the Archer, TIER 3 AT FLOOR 20
stampCase( 3, 10, 2, 'i_tod_card2_art_tier_heavy_2' )     -- the Breacher, TIER 2 AT FLOOR 40

-- 4. not blocked: no strip
CoD.TodClass = 2
CoD.TodTierNeed = 0
deal( 3 )
push( 'todUpgFocus', 1 )
ok( s.alpha == 0, 'a player who is not floor-blocked sees no strip' )
push( 'todUpgShow', 0 )

print( 'TIER GATE STRIP OK: ' .. checks .. ' checks (live classes: gutter tier 2 / FLOOR 40; stamp tier 3 / FLOOR 20 and tier 2 / FLOOR 40 over the layered card, banner cut; hidden while revealing and when not blocked)' )
