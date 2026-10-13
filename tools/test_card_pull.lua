-- tools/test_card_pull.lua — THE PULL (docs/187) under the real upgrade menu.
-- Run: python -B tools/run_lua_harness.py tools/test_card_pull.lua
--
-- Builds the REAL LUI.createMenu.tod_upgrade with TodPull loaded, then plays the
-- exact field sequence _tod_upgrade_ui.gsc reveal_deal pushes (one field per
-- snapshot) and checks what is on screen after each beat: the backs, the climb
-- colour, the ladder, the flip, the live band + pips, the banner, the reset.
-- It also proves the timing contract: no tween the NEXT push can overtake runs
-- longer than the shortest push gap (the hitch x 0.5 = 95 ms).
-- THE REACH + THE HOT STREAK (docs/201): SO CLOSE and BREAK THROUGH on the wire (a second beat at one rung),
-- the warm backs (halo + embers drawn OVER the back), the HUD heat layer, the ONE SEGMENT SHORT line.

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
CoD = { Menu = { NewForUIEditor = newElement }, TweenType = { Linear = 0, Bounce = 1 }, isZombie = true, TodOwned = {}, TodClass = 5, TodClassTier = 1 }   -- an id with no TOD_TCLS key (no layered set), so the first deals exercise the OLD faces (the fallback)
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

-- the REAL manifest: every live class deals the layered cards since docs/193 (2026-09-29)
do
    local cl = CoD.TodCardArt.classes or {}
    for _, k in ipairs( { 'necromancer', 'assault', 'heavy', 'slasher' } ) do
        assert( cl[ k ] == true, 'the installed manifest lists ' .. k .. ' as a layered class' )
    end
    local n = 0
    for k in pairs( cl ) do n = n + 1 end
    assert( n == 4, 'the manifest lists exactly the four live classes (got ' .. n .. ')' )
end
local menu = LUI.createMenu.tod_upgrade( 0 )
local P = CoD.TodPull
local pull = P.last
assert( pull, 'THE PULL was not attached to the upgrade panel' )
local A, B = pull.slot.a, pull.slot.b

local function near( a, b ) return math.abs( a - b ) < 0.002 end
-- the tint of a panel lives on its .Bg, of a sprite on the element itself
local function rgbOf( e ) if e.Bg and e.Bg.rgb then return e.Bg.rgb end return e.rgb end
local function sameRGB( e, col ) local c = rgbOf( e ); return near( c[ 1 ], col[ 1 ] ) and near( c[ 2 ], col[ 2 ] ) and near( c[ 3 ], col[ 3 ] ) end
local GOLD, WHITE, BLUE = { 1.0, 0.761, 0.239 }, { 0.914, 0.933, 0.961 }, { 0.227, 0.659, 1.0 }
-- WHITE WORDS ON A DARK GROUND (user 2026-09-29): the rarity pill and the v2 title label wear a dark
-- shade of the rarity colour (TodPull GROUND_DIM), the title and the rarity word are white
local function shade( col ) local k = P.GROUND_DIM; return { col[ 1 ] * k, col[ 2 ] * k, col[ 3 ] * k } end
local function rowWhite( row ) return row and row.img[ 1 ] and sameRGB( row.img[ 1 ], { 1, 1, 1 } ) end
local checks = 0
local function ok( cond, msg ) checks = checks + 1; assert( cond, msg ) end

-- the ticker / banner chains: run every pending transition to completion
local function settle( s )
    for _ = 1, 20 do
        local h = s.face.ticker.handlers[ 'transition_complete_tod_pull_pip' ]
        if not s.pipsPending then break end
        h( s.face.ticker, { interrupted = false } )
    end
end
local function litPips( s, col )
    local n = 0
    for i = 1, 10 do
        local e = s.face.pips[ i ]
        if e.alpha > 0 and sameRGB( e, col ) then n = n + 1 end
    end
    return n
end

-- ==== DEAL 1: slot A LEGENDARY (LUCK, id 4, at Lv2), slot B COMMON (BOUNTY, id 3, at Lv0)
local hold = 0
local function beat() hold = hold + 1; push( 'todUpgHold', hold ) end
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 2 )
push( 'todUpgBD', 0 ); push( 'todUpgBR', 0 ); push( 'todUpgBL', 0 ); push( 'todUpgSolo', 0 )
push( 'todUpgFocus', 0 ); push( 'todUpgTime', 15 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
ok( A.back.beat.alpha == 1 and B.back.beat.alpha == 1, 'both backs must be on the table when the deal opens' )
if A.back.art and CoD.TodCardArt.back then
    ok( A.back.art.image == CoD.TodCardArt.back, 'a class without the layered set deals on the OLD back, got ' .. tostring( A.back.art.image ) )
end
ok( A.ladder.layer.alpha == 1 and B.ladder.layer.alpha == 1, 'both ladders must show when the deal opens' )
ok( A.face.band.alpha == 0, 'no band before a card flips' )
ok( CoD.TodHudVeil.Hidden(), 'the HUD veil is up while cards are dealt' )
ok( not sameRGB( A.back.core, WHITE ), 'an unclimbed back is NOT common white (it read as "stayed common")' )

PHASE = 'climb'
beat()                                      -- A starts at COMMON
ok( A.started and A.rung == 1 and sameRGB( A.back.core, WHITE ), 'A starts its climb at COMMON (white)' )
ok( not B.started, 'B must not start while A is climbing' )
beat()                                      -- hitch
push( 'todUpgAR', 1 ); beat()               -- RARE + hitch
ok( A.rung == 2 and sameRGB( A.back.core, BLUE ), 'A climbs to RARE (blue)' )
push( 'todUpgAR', 2 ); beat()               -- EPIC
push( 'todUpgAR', 3 ); beat()               -- LEGENDARY
ok( A.rung == 4 and sameRGB( A.back.core, GOLD ), 'A climbs to LEGENDARY (gold)' )
local g4 = A.ladder.rungs[ 4 ]
ok( ( g4.crest and sameRGB( g4.gem, { 1, 1, 1 } ) and g4.gem.alpha == 1 ) or sameRGB( g4.gem, GOLD ), 'the LEGENDARY rung lights on the ladder (a gold gem, or its crest at full colour)' )
ok( pull.under.dim.alpha > 0.5, 'the room darkens at LEGENDARY' )

PHASE = 'flip'
push( 'todUpgAD', 4 )                       -- LUCK flips
ok( A.back.beat.alpha == 0, 'the back folds away on the flip' )
ok( A.face.band.alpha == 1 and sameRGB( A.face.band, shade( GOLD ) ), 'the live band wears a dark LEGENDARY gold' )
ok( rowWhite( A.face.bandRow ), 'the rarity word is WHITE (contrast)' )
ok( pull.banner.anim and pull.banner.anim.name == 'tod_pull_bn_in', 'the banner stamps in on the flip' )
settle( A )
ok( litPips( A, GOLD ) == 4, 'LEGENDARY on LUCK Lv2 lights exactly 4 new pips in gold, got ' .. litPips( A, GOLD ) )

PHASE = 'climb'
beat()                                      -- B starts
ok( B.started and B.rung == 1, 'B starts after A flips' )
beat()                                      -- hitch, then flip at COMMON
PHASE = 'flip'
push( 'todUpgBD', 3 )
ok( B.face.band.alpha == 1 and sameRGB( B.face.band, shade( WHITE ) ), 'B lands COMMON (a dark grey band)' )
settle( B )
ok( litPips( B, WHITE ) == 1, 'COMMON lights exactly 1 new pip' )

PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 )
ok( A.back.beat.alpha == 0 and B.back.beat.alpha == 0, 'no backs once choosing starts' )
ok( A.face.band.alpha == 1 and B.face.band.alpha == 1, 'the bands stay while the player chooses' )

push( 'todUpgShow', 0 )
ok( A.face.band.alpha == 0 and A.ladder.layer.alpha == 0 and pull.under.dim.alpha == 0, 'panel down: everything back to rest' )
ok( not CoD.TodHudVeil.Hidden(), 'the HUD veil drops the moment the panel closes' )

-- ==== DEAL 2: ONE card (todUpgSolo), a RARE ===================================
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 0 ); push( 'todUpgBD', 0 ); push( 'todUpgBR', 0 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
ok( A.back.beat.alpha == 1 and B.back.beat.alpha == 0, 'a one-card deal deals ONE back' )
PHASE = 'climb'
beat(); beat(); push( 'todUpgAR', 1 ); beat()
PHASE = 'flip'
push( 'todUpgAD', 3 )
settle( A )
ok( litPips( A, BLUE ) == 2, 'RARE lights 2 new pips' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )

-- ==== DEAL 3: a TEXT card (QUICK DRAW, id 35, no baked art) still wears its band
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 1 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
PHASE = 'climb'
beat(); beat(); push( 'todUpgAR', 1 ); beat(); push( 'todUpgAR', 2 ); beat()
PHASE = 'flip'
push( 'todUpgAD', 35 )
settle( A )
local PURPLE = { 0.710, 0.361, 1.0 }
ok( A.face.band.alpha == 1 and sameRGB( A.face.band, shade( PURPLE ) ), 'a text card lands EPIC with its dark purple band' )
ok( litPips( A, PURPLE ) == 3, 'EPIC on a text card lights 3 new pips' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )

-- ==== DEAL 4: THE REACH, SO CLOSE (docs/201): an EPIC strains for gold and falls back
local HEAT = { 1, 0.52, 0.14 }
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 1 ); push( 'todUpgBD', 0 ); push( 'todUpgBR', 0 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
ok( not A.warm, 'a cold player\'s backs are plain (no heat yet)' )
PHASE = 'climb'
beat(); beat(); push( 'todUpgAR', 1 ); beat(); push( 'todUpgAR', 2 ); beat()   -- EPIC + its hitch
ok( A.rung == 3 and not A.reaching and A.beatsHere == 1, 'at EPIC, one beat at the rung is only the heartbeat' )
PHASE = 'reach'
beat()                                       -- the REACH beat: a second beat at this rung
ok( A.reaching, 'a second beat at the same rung, no climb between, is THE REACH' )
ok( A.reachGem.alpha > 0 and sameRGB( A.reachGem, GOLD ), 'the next gem flickers in GOLD' )
ok( A.reachFill.alpha > 0 and sameRGB( A.reachFill, GOLD ), 'gold climbs the back' )
ok( math.abs( A.reachFill.t - ( A.back.y1 - ( A.back.y1 - A.back.y0 ) * 0.66 ) ) < 0.01, 'two thirds of the way up, and it holds there' )
ok( A.back.beat.anim and A.back.beat.anim.name == 'tod_pull_tremble', 'the card strains (trembles)' )
for _ = 1, 10 do A.back.beat.handlers[ 'transition_complete_tod_pull_tremble' ]( A.back.beat, {} ) end
ok( A.back.beat.t == A.back.y0 - 4 and A.back.beat.l == A.back.xLo, 'the tremble ends holding the card lifted and centred' )
for _ = 1, 10 do A.reachGem.handlers[ 'transition_complete_tod_pull_reach_flick' ]( A.reachGem, {} ) end
ok( math.abs( A.reachGem.alpha - 0.6 ) < 0.01, 'the gem stays half-lit while the reach holds' )
local g4r = A.ladder.rungs[ 4 ]
ok( g4r.gem.alpha < 1, 'the LEGENDARY rung itself never lights during a reach (it only flickers over it)' )
PHASE = 'deflate'
beat()                                       -- SO CLOSE: a beat while it strains
ok( not A.reaching and A.reachFill.alpha == 0 and A.reachGem.alpha == 0, 'SO CLOSE: the fill drains, the flicker dies' )
ok( A.back.beat.anim and A.back.beat.anim.name == 'tod_pull_sink' and A.back.beat.t == A.back.y0, 'the card sinks back onto the table' )
ok( A.rung == 3, 'it stays EPIC' )
PHASE = 'flip'
push( 'todUpgAD', 35 )
ok( A.face.band.alpha == 1 and sameRGB( A.face.band, shade( PURPLE ) ), 'and flips EPIC' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )

-- ==== DEAL 5: THE REACH, BREAK THROUGH: an EPIC strains for gold and gets there
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 2 ); push( 'todUpgBD', 0 ); push( 'todUpgBR', 0 ); push( 'todUpgBL', 0 ); push( 'todUpgSolo', 0 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
PHASE = 'climb'
beat(); beat(); push( 'todUpgAR', 1 ); beat(); push( 'todUpgAR', 2 ); beat()
PHASE = 'reach'
beat()
ok( A.reaching and sameRGB( A.reachFill, GOLD ), 'the EPIC strains for gold' )
PHASE = 'break'
push( 'todUpgAR', 3 )                        -- the climb resolves it
ok( not A.reaching and A.rung == 4 and sameRGB( A.back.core, GOLD ), 'BREAK THROUGH: it climbs on to LEGENDARY' )
ok( A.reachFill.anim and A.reachFill.anim.name == 'tod_pull_reach_burst' and A.reachFill.t == A.back.y0 + 4, 'the gold fills the whole back and bursts' )
ok( pull.ring.anim and pull.ring.anim.name == 'tod_pull_break_ring', 'a ring snaps off the card' )
ok( A.back.beat.t == A.back.y0, 'the card is back at rest for the climb' )
PHASE = 'climb'
beat()                                       -- the LEGENDARY rung's own hitch
ok( not A.reaching and A.beatsHere == 1, 'the beat after a break through is a plain heartbeat (beats count afresh at each rung)' )
PHASE = 'flip'
push( 'todUpgAD', 4 )
ok( A.face.band.alpha == 1 and sameRGB( A.face.band, shade( GOLD ) ), 'and flips LEGENDARY' )
PHASE = 'climb'
beat(); beat()
PHASE = 'flip'
push( 'todUpgBD', 3 )
ok( not B.reaching and B.face.band.alpha == 1, 'the other card reveals plainly (one reach a deal)' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )

-- ==== DEAL 6: THE HOT STREAK's warm backs, beats that share a snapshot, a lost SO CLOSE beat
CoD.TodHeat = 3
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 0 ); push( 'todUpgBD', 0 ); push( 'todUpgBR', 0 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
local usA = pull.under.slot.a
-- an ember is a RUNNING rise: the mock applies a tween's end alpha at once, so count the live tween, not the alpha
ok( A.warm and usA.glow.alpha > 0.4 and sameRGB( usA.glow, HEAT ), 'ON FIRE: the backs arrive warm, an orange halo' )
local function liveEmbers( s, tint )
    local n = 0
    for i = 1, #s.embers do local m = s.embers[ i ]; if m.anim and m.anim.name == 'tod_pull_ember' and ( not tint or sameRGB( m, tint ) ) then n = n + 1 end end
    return n
end
local embers = liveEmbers( A, HEAT )
ok( embers == 6, 'ON FIRE: six embers rise off the back, got ' .. embers )
-- THEY MUST BE SEEN: drawn AFTER (over) the back's art in the same parent, and rising inside the card's columns.
-- The first cut used the under layer's motes, which draw BEHIND the opaque card: render_pull showed no ember at all
local function indexIn( e ) for i, c in ipairs( e.parent.children ) do if c == e then return i end end end
local backTop = A.back.art or A.back.fill or A.back.rim
ok( backTop and A.embers[ 1 ].parent == backTop.parent and indexIn( A.embers[ 1 ] ) > indexIn( backTop ), 'the embers draw OVER the card back, not under it' )
local inside = true
for i = 1, 6 do local m = A.embers[ i ]; if not ( m.l >= A.back.xLo - 30 and m.r <= A.back.xHi + 30 and m.t < A.back.y1 ) then inside = false end end
ok( inside, 'every ember rises over the card itself' )
PHASE = 'climb'
hold = hold + 2; push( 'todUpgHold', hold )  -- the start and the hitch land in ONE snapshot
ok( A.started and A.rung == 1 and A.beatsHere == 1 and not A.reaching, 'two beats in one snapshot play as two (the start, then the hitch), never merged' )
PHASE = 'reach'
beat()
ok( A.reaching, 'then the reach' )
PHASE = 'flip'
push( 'todUpgAD', 3 )                        -- its SO CLOSE beat never arrived
ok( not A.reaching and A.reachFill.alpha == 0 and A.reachGem.alpha == 0, 'a flip that lands mid-reach clears it (nothing is left straining)' )
ok( not A.warm, 'the flip ends the warm back' )
embers = liveEmbers( A )
local shown = 0
for i = 1, #A.embers do if A.embers[ i ].alpha > 0 then shown = shown + 1 end end
ok( embers == 0 and shown == 0, 'no ember outlives the flip of a COMMON card' )
-- a completion that fires after the flip (the engine reports a finished tween late) never relaunches an ember
A.embers[ 1 ].handlers[ 'transition_complete_tod_pull_ember' ]( A.embers[ 1 ], {} )
ok( liveEmbers( A ) == 0 and A.embers[ 1 ].alpha == 0, 'a late completion after the flip stays dark' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )
CoD.TodHeat = 1
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 0 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
embers = liveEmbers( A )
ok( A.warm and embers == 2, 'WARM: two embers, got ' .. embers )
-- a running ember's completion launches the next rise while the back is warm (the loop)
A.embers[ 1 ].handlers[ 'transition_complete_tod_pull_ember' ]( A.embers[ 1 ], {} )
ok( A.embers[ 1 ].anim and A.embers[ 1 ].anim.name == 'tod_pull_ember', 'a warm ember rises again when its last rise ends' )
local emberTop = A.embers[ 1 ].t
A.embers[ 1 ].handlers[ 'transition_complete_tod_pull_ember' ]( A.embers[ 1 ], { interrupted = true } )
ok( A.embers[ 1 ].t == emberTop, 'an interrupted rise is not relaunched by its own completion' )
PHASE = 'climb'
beat(); beat()
PHASE = 'flip'
push( 'todUpgAD', 3 )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )
CoD.TodHeat = 0

-- ==== THE TIMING CONTRACT =====================================================
-- A tween started during the CLIMB can be overtaken by the next push, whose gap
-- is at least the hitch x TOD_REVEAL_LIVE_SCALE = 0.19 x 0.5 = 95 ms.
for _, t in ipairs( TWEENS ) do
    if t.phase == 'climb' and t.name:match( '^tod_pull' ) then
        ok( t.ms <= 95, 'climb tween ' .. t.name .. ' runs ' .. t.ms .. ' ms, over the 95 ms push floor' )
    end
end
-- THE REACH's tweens fit their own gaps at a co-op altar, read from the server's own waits (LOCKSTEP): the reach
-- holds TOD_PULL_REACH, SO CLOSE's settle + hitch is the next gap, and a break through's climb is followed by its
-- rung's dwell less the hitch (rung 2 the shortest) - a beat that touches neither the fill nor the ring.
do
    local gf = assert( io.open( 'scripts/zm/zm_tod2_cybercity/_tod_upgrade_ui.gsc', 'r' ) )
    local g = gf:read( '*a' ); gf:close()
    local function def( n ) return tonumber( string.match( g, '#define ' .. n .. '%s+([%d%.]+)' ) ) end
    local live, reach, settleW, hitch, rung2 = def( 'TOD_REVEAL_LIVE_SCALE' ), def( 'TOD_PULL_REACH' ), def( 'TOD_PULL_REACH_SETTLE' ), def( 'TOD_PULL_HITCH' ), def( 'TOD_PULL_RUNG_2' )
    ok( live and reach and settleW and hitch and rung2, 'the server\'s reach waits are readable' )
    local bound = { reach = reach * live * 1000, deflate = ( settleW + hitch ) * live * 1000, ['break'] = ( rung2 - hitch ) * live * 1000 }
    local seen = { reach = 0, deflate = 0, ['break'] = 0 }
    for _, t in ipairs( TWEENS ) do
        local b = bound[ t.phase ]
        if b and t.name:match( '^tod_pull' ) then
            seen[ t.phase ] = seen[ t.phase ] + 1
            ok( t.ms <= b + 0.5, t.phase .. ' tween ' .. t.name .. ' runs ' .. t.ms .. ' ms, past its ' .. b .. ' ms gap' )
        end
    end
    ok( seen.reach > 0 and seen.deflate > 0 and seen['break'] > 0, 'every reach phase ran tweens' )
end

-- ==== LIFETIME: the whole menu closes with nothing left open ================
local function live() local n = 0; for _, e in ipairs( elements ) do if not e.closed then n = n + 1 end end; return n end
menu:close()
ok( live() == 0, 'the upgrade menu with THE PULL leaked ' .. live() .. ' elements on close' )


-- ==== CARD V2: a manifest with every layer installed (docs/191) ==============
for k in pairs( SUBS ) do SUBS[ k ] = nil end
local FXREAL = CoD.TodCardArt.fx
CoD.TodCardArt = {
    fx = FXREAL,
    body = "i_tod_card2_body",
    back = "i_tod_card_back",
    back2 = "i_tod_card2_back",
    frame = { "i_tod_card2_frame_common", "i_tod_card2_frame_rare", "i_tod_card2_frame_epic", "i_tod_card2_frame_legendary" },
    crest = { "i_tod_card2_crest_common", "i_tod_card2_crest_rare", "i_tod_card2_crest_epic", "i_tod_card2_crest_legendary" },
    art = { [ 4 ] = "i_tod_card2_art_luck", [ 3 ] = "i_tod_card2_art_bounty" },
    tier = { assault = { [ 2 ] = "i_tod_card2_art_tier_assault_2" } },
    classes = { assault = true },
}
CoD.TodClass = 2   -- the Archer: TOD_TCLS[ 2 ] = "assault", listed in classes
local menu2 = LUI.createMenu.tod_upgrade( 0 )
local pull2 = P.last
local A2, B2 = pull2.slot.a, pull2.slot.b
ok( A2.face2 ~= nil, 'card v2 layers are built when the body + frames are installed' )
ok( sameRGB( A2.ladder.rungs[ 1 ].gem, { 0.32, 0.32, 0.38 } ) or A2.ladder.rungs[ 1 ].crest, 'the ladder uses the crest art when installed' )
hold = 0
local function beat2() hold = hold + 1; push( 'todUpgHold', hold ) end
-- slot A: LUCK (v2 art) LEGENDARY at Lv2; slot B: the Archer TIER 2 card (class 2, tier 2 -> code 2)
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 2 )
push( 'todUpgBD', 0 ); push( 'todUpgBR', 0 ); push( 'todUpgBL', 2 ); push( 'todUpgSolo', 0 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
ok( A2.back.art and A2.back.art.image == 'i_tod_card2_back' and B2.back.art.image == 'i_tod_card2_back', 'a layered class deals on the v2 back (the layered card\'s silhouette)' )
PHASE = 'climb'
beat2(); beat2(); push( 'todUpgAR', 1 ); beat2(); push( 'todUpgAR', 2 ); beat2(); push( 'todUpgAR', 3 ); beat2()
PHASE = 'flip'
push( 'todUpgAD', 4 )
local f2 = A2.face2
ok( A2.card.CardImg.alpha == 0, 'a v2 card hides the old baked image' )
ok( f2.body.alpha == 1 and f2.art.alpha == 1 and f2.frame.alpha == 1, 'the v2 layers open on the flip' )
ok( f2.art.image == 'i_tod_card2_art_luck', 'the LUCK illustration is drawn' )
ok( f2.frame.image == 'i_tod_card2_frame_legendary', 'a LEGENDARY wears the legendary frame' )
ok( f2.crest.image == 'i_tod_card2_crest_legendary' and f2.crest.alpha == 1, 'and the legendary crest' )
ok( f2.text.alpha == 0, 'the words wait for the card to open' )
f2.body.handlers[ 'transition_complete_tod_pull_open' ]( f2.body, { interrupted = false } )
ok( f2.text.alpha == 1, 'the words arrive when it has opened' )
ok( sameRGB( A2.face.band, shade( GOLD ) ) and A2.face.band.l == A2.face.xLo + 51 + 2, 'the band sits in the v2 slot, dark gold' )
ok( rowWhite( f2.title ) and f2.titleLabel.alpha == 1 and sameRGB( f2.titleLabel, shade( GOLD ) ), 'the v2 title is WHITE on its dark gold label' )
ok( rowWhite( f2.line1 ), 'the first line on a v2 card is white' )
ok( A2.card.v2 == true and A2.card.Top.Bg.alpha == 0 and A2.card.Bot.Bg.alpha == 0, 'no leftover rarity strips on the layered card' )
ok( A2.raysOn, 'a LEGENDARY turns its god rays' )
settle( A2 )
ok( litPips( A2, GOLD ) == 4, 'the v2 card lights 4 new pips' )
PHASE = 'climb'
beat2(); beat2(); push( 'todUpgBR', 1 ); beat2(); push( 'todUpgBR', 2 ); beat2()
PHASE = 'flip'
push( 'todUpgBD', 24 )
local g2 = B2.face2
ok( g2.art.image == 'i_tod_card2_art_tier_assault_2' and g2.art.alpha == 1, 'the Archer TIER 2 card draws its v2 illustration' )
ok( g2.crest.alpha == 1 and g2.crest.image == 'i_tod_card2_crest_epic', 'a tier card wears its frame\'s crest (never an empty socket)' )
settle( B2 )
ok( B2.face.band.alpha == 1 and B2.face.pips[ 3 ].alpha == 1 and B2.face.pips[ 4 ].alpha == 0, 'a tier card: PROMOTION band + a 3-pip TIER tray' )
-- RT 2026-10-05: the unlit pip's tint is the THEME's (r3 CODE_TINTS pins the literal in TodPull.lua); this checks the
-- held / new / to-come STATES, so it reads that literal rather than carrying a second copy
local UNLIT_PIP = ( function()
    local fh = assert( io.open( 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodPull.lua', 'r' ) )
    local src = fh:read( '*a' ); fh:close()
    local r, g, b = string.match( src, 'and { 0%.80, 0%.84, 0%.94 } or { ([%d.]+), ([%d.]+), ([%d.]+) } %)' )
    assert( r, 'TodPull.lua: the pip tint line (held / unlit) was not found' )
    return { tonumber( r ), tonumber( g ), tonumber( b ) }
end )()
ok( sameRGB( B2.face.pips[ 1 ], { 0.80, 0.84, 0.94 } ) and sameRGB( B2.face.pips[ 2 ], PURPLE ) and sameRGB( B2.face.pips[ 3 ], UNLIT_PIP ),
    'TIER 2 of 3: tier 1 held (white), tier 2 new (the card colour), tier 3 still to come' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )
ok( f2.body.alpha == 0 and not A2.raysOn, 'panel down: the v2 layers and the rays are gone' )
-- a card with NO v2 art keeps the old baked card (GRAPPLE, id 41, is not in this manifest)
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 0 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
beat2(); beat2()
PHASE = 'flip'
push( 'todUpgAD', 41 )
ok( f2.body.alpha == 0 and A2.face.band.alpha == 1, 'an upgrade without v2 art keeps the old card + the live band' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )
-- CARD V2 IS PER CLASS: one design per deal
CoD.TodClass = 4   -- the Warrior: no layered set
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 1 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
ok( A2.back.art.image == 'i_tod_card_back', 'a class without the layered set deals on the OLD back' )
beat2(); beat2()
PHASE = 'flip'
push( 'todUpgAD', 4 )
ok( f2.body.alpha == 0 and A2.card.imgLive == true, 'LUCK has v2 art, but a Warrior\'s LUCK stays an old card (never one of each in a deal)' )
ok( not CoD.TodPull.UsesV2( pull2, 4, 1 ), 'UsesV2 answers per class' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )
CoD.TodClass = 2
hold = 0
PHASE = 'open'
push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgAL', 1 ); push( 'todUpgSolo', 1 )
push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
ok( A2.back.art.image == 'i_tod_card2_back', 'back to the Archer: the v2 back again' )
beat2(); beat2()
PHASE = 'flip'
push( 'todUpgAD', 4 )
ok( f2.body.alpha == 1 and f2.art.image == 'i_tod_card2_art_luck', 'and the Archer\'s LUCK is a layered card' )
PHASE = 'choose'
push( 'todUpgHold', 0 ); push( 'todUpgFocus', 1 ); push( 'todUpgShow', 0 )
menu2:close()
ok( live() == 0, 'the v2 menu leaked ' .. live() .. ' elements on close' )

-- ==== THE HOT STREAK on the HUD + ONE SEGMENT SHORT on the panel (docs/201) ======================
-- A fresh menu whose scriptNotify listener is captured, so tod_luck_heat runs through the REAL handler.
for k in pairs( SUBS ) do SUBS[ k ] = nil end
local GLOBAL = {}
function methods:subscribeToGlobalModel( inst, a, b, fn ) GLOBAL[ #GLOBAL + 1 ] = fn end
local NOTE = nil
local oldNotify = CoD.GetScriptNotifyData
CoD.GetScriptNotifyData = function( m ) return NOTE end
local function notify( name, data )
    MODELS[ 'notify' ] = name
    NOTE = data
    for _, fn in ipairs( GLOBAL ) do fn( 'notify' ) end
end
local menu3 = LUI.createMenu.tod_upgrade( 0 )
local function withText( t ) local n = 0; for _, e in ipairs( elements ) do if not e.closed and e.text == t and e.alpha > 0 then n = n + 1 end end; return n end
local function liveEmbers() local n = 0; for _, e in ipairs( elements ) do if not e.closed and e.anim and e.anim.name == 'tod_heat_ember' then n = n + 1 end end; return n end
ok( #GLOBAL > 0, 'the HUD listens to scriptNotify' )
notify( 'tod_luck_heat', { 3, 4, 1 } )
ok( CoD.TodHeat == 3, 'the HUD records the heat for the card reveal (CoD.TodHeat)' )
ok( withText( 'ON FIRE' ) == 1, 'the luck plate\'s chip says ON FIRE' )
ok( liveEmbers() == 6, 'ON FIRE: six embers rise off the luck bar, got ' .. liveEmbers() )
ok( withText( 'HOT STREAK - ON FIRE' ) == 1, 'the card panel\'s line says it too' )
push( 'todUpgLuck', 5 )
local hot = 0
for _, e in ipairs( elements ) do if not e.closed and e.image == 'i_tod_h2_luck_on' and near( e.rgb[ 2 ], 0.62 ) then hot = hot + 1 end end
ok( hot == 5, 'ON FIRE runs the five lit segments orange, got ' .. hot )
notify( 'tod_luck_heat', { 1, 2, 2 } )
ok( withText( 'WARM' ) == 1 and liveEmbers() == 2, 'WARM: the chip and two embers' )
hot = 0
for _, e in ipairs( elements ) do if not e.closed and e.image == 'i_tod_h2_luck_on' and near( e.rgb[ 2 ], 0.62 ) then hot = hot + 1 end end
ok( hot == 0, 'below ON FIRE the segments wear their own colour again' )
notify( 'tod_luck_heat', { 0, 0, 2 } )
ok( CoD.TodHeat == 0 and withText( 'WARM' ) == 0 and liveEmbers() == 0 and withText( 'HOT STREAK - WARM' ) == 0, 'a streak that ends clears the chip, the embers and the panel line' )
notify( 'tod_luck_heat', {} ); notify( 'tod_luck_heat', { 'x' } )
ok( CoD.TodHeat == 0 and liveEmbers() == 0, 'garbage heat args read as cold' )
-- ONE SEGMENT SHORT: the panel names the guarantee a bar one segment under it just missed (the deal's own luck)
local function dealAt( tens )
    push( 'todUpgShow', 0 )
    push( 'todUpgAD', 0 ); push( 'todUpgAR', 0 ); push( 'todUpgSolo', 1 ); push( 'todUpgLuck', tens )
    push( 'todUpgFocus', 0 ); push( 'todUpgHold', 0 ); push( 'todUpgShow', 1 )
end
dealAt( 9 ); ok( withText( 'ONE SEGMENT FROM AN EPIC' ) == 1, 'a 90..99 bar: ONE SEGMENT FROM AN EPIC' )
dealAt( 4 ); ok( withText( 'ONE SEGMENT FROM A RARE' ) == 1, 'a 40..49 bar: ONE SEGMENT FROM A RARE' )
dealAt( 6 ); ok( withText( 'ONE SEGMENT FROM AN EPIC' ) == 0 and withText( 'ONE SEGMENT FROM A RARE' ) == 0, 'any other bar says nothing' )
push( 'todUpgShow', 0 )
menu3:close()
ok( live() == 0, 'the menu with the heat layer leaked ' .. live() .. ' elements on close' )
CoD.GetScriptNotifyData = oldNotify

print( 'THE PULL: ' .. checks .. ' checks passed (legendary + common deal, one-card deal, 95 ms tween floor, card v2 per class, THE REACH so close / break through / lost beat / shared snapshot + its own tween gaps, warm backs, the HUD heat layer, ONE SEGMENT SHORT, zero leaks).' )
