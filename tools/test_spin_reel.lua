-- Lua 5.1 harness for TodSpinReel.lua (docs/188): loads the real module under
-- BO3's no-new-globals rule, builds it on mocked LUI elements, and drives whole
-- spins through its scriptNotify subscription exactly as _tod_shop.gsc does.
-- Asserts: the tile under the needle at the landing step IS the prize, the tease
-- sits one past it, the HUD veil is held for exactly the spin (open -> end, the
-- watchdog, the close hook), chips hide under ANY veil owner, result statuses,
-- nothing drawn outside the panel, filler is luck-weighted, and every event
-- survives missing arguments.
local path = "ui/uieditor/widgets/HUD/AetheriumWidgets/TodSpinReel.lua"
local f = assert( io.open( path, "r" ) )
local source = f:read( "*a" ); f:close()

local function newEl( kind )
    local el = { kind = kind, children = {}, alpha = 1, text = nil, lr = nil, rgb = nil, anims = {}, handlers = {} }
    local m = {}
    function m.setLeftRight( self, a, b, l, r ) self.lr = { l, r } end
    function m.setTopBottom( self, a, b, t, bo ) self.tb = { t, bo } end
    function m.setAlpha( self, a ) self.alpha = a end
    function m.setRGB( self, r, g, b ) self.rgb = { r, g, b } end
    function m.addElement( self, c ) table.insert( self.children, c ); c.parent = self end
    function m.setText( self, t ) self.text = t end
    function m.setImage( self, img ) self.image = img end
    function m.beginAnimation( self, name ) table.insert( self.anims, name ) end
    function m.completeAnimation( self ) end
    function m.registerEventHandler( self, name, fn ) self.handlers[ name ] = fn end
    function m.subscribeToGlobalModel( self, inst, a, b, fn ) self.notify = fn end
    function m.close( self ) if self.onClose then self:onClose() end end
    -- methods resolve to the mock or a no-op; DATA fields (text, lr, rgb ...) stay nil
    setmetatable( el, { __index = function( t, k )
        if m[ k ] then return m[ k ] end
        if type( k ) == "string" and ( string.find( k, "^set" ) or string.find( k, "^get" ) or string.find( k, "^link" ) ) then
            return function() end
        end
        return nil
    end } )
    return el
end

local function run( withGlyph, withVeil, art, withFx )
    local veilOwners = {}
    local veilCalls = {}
    local CoD = {
        TodUIOwnership = { Attach = function() end },
        GetScriptNotifyData = function( model ) return model.data end,
        TweenType = { Linear = 0 },
    }
    if withGlyph then
        CoD.TodGlyphText = { new = function( o ) local e = newEl( "glyph" ); e.opts = o; return e end }
    end
    -- the card reveal's generated FX sprites (TodCardArt.lua): pass 3's ring, shards,
    -- edge glow, rail runners and luck motes only exist when the manifest is loaded
    if withFx then
        CoD.TodCardArt = { fx = { ring = "i_tod_pull_ring", shard = "i_tod_pull_shard", edge = "i_tod_pull_edge", pip = "i_tod_pull_pip" } }
    end
    local listeners = {}
    if withVeil then
        CoD.TodHudVeil = {
            Set = function( key, on ) veilOwners[ key ] = on or nil; table.insert( veilCalls, key .. "=" .. tostring( on ) )
                local h = false; for _, v in pairs( veilOwners ) do if v then h = true end end
                for _, fn in pairs( listeners ) do fn( h ) end end,
            Listen = function( el, fn ) listeners[ el ] = fn; local h = false; for _, v in pairs( veilOwners ) do if v then h = true end end; fn( h ) end,
            Hidden = function() for _, v in pairs( veilOwners ) do if v then return true end end return false end,
        }
    end
    local LUI = { UIElement = { new = function() return newEl( "el" ) end },
                  UIImage = { new = function() return newEl( "img" ) end },
                  UIText = { new = function() return newEl( "text" ) end },
                  OverrideFunction_CallOriginalSecond = function( el, fname, fn ) el.onClose = function( self ) fn( self ) end end }
    local env = {
        CoD = CoD, LUI = LUI,
        Enum = { LUIAlignment = { LUI_ALIGNMENT_CENTER = 1, LUI_ALIGNMENT_RIGHT = 2 } },
        Engine = { GetModelValue = function( m ) return m.name end, Localize = function( s ) return s end },
        InheritFrom = function() return {} end,
        RegisterImage = function( name ) return name end,
        require = function() end,
        pcall = pcall, math = math, type = type, tonumber = tonumber, tostring = tostring, string = string, table = table,
        pairs = pairs, ipairs = ipairs,
    }
    setmetatable( env, { __index = _G, __newindex = function( _, k ) error( "LUI Error: Tried to create global variable " .. k ) end } )
    local src = source
    if not art then
        local n
        src, n = string.gsub( source, "local USE_SPIN_ART = true", "local USE_SPIN_ART = false" )
        assert( n == 1, "the art flag is one literal line" )
    end
    local chunk = assert( loadstring( src, "@" .. path ) )
    setfenv( chunk, env )
    assert( pcall( chunk ) )
    local reel = CoD.TodSpinReel.new( nil, 0 )
    assert( reel.notify, "subscribed to scriptNotify" )
    local function send( name, data ) reel.notify( { name = name, data = data } ) end

    -- find the strip (the 9 recycled tiles), the panel, the chips, the watchdog
    local strip, panel, chips, watch
    local function walk( e ) if #e.children == 9 then strip = e end for _, c in ipairs( e.children ) do walk( c ) end end
    walk( reel )
    panel, watch = reel.children[ 1 ], nil
    for _, c in ipairs( reel.children ) do
        if c.handlers[ "transition_complete_tod_spin_watch" ] then watch = c end
        if #c.children == 3 and c ~= panel then chips = c end
    end
    assert( strip and panel and watch and chips, "strip, panel, watchdog and chips found" )

    -- nothing the panel draws may stick out past the panel (x 100..1180)
    for _, c in ipairs( panel.children ) do
        if c.kind == "img" and c.lr then
            assert( c.lr[ 1 ] >= 100 and c.lr[ 2 ] <= 1180, "panel quad inside the panel: " .. c.lr[ 1 ] .. ".." .. c.lr[ 2 ] )
        end
    end

    local LAND = 30
    local prize = 6 * 4 + 3        -- ARC CHAIN, LEGENDARY
    send( "tod_ptn_items", { 1 * 4 + 3, 0, 7 * 4 + 1, 2 } )
    assert( chips.alpha == 1, "chips show with a loadout" )
    if art then
        assert( chips.children[ 1 ].Icon.image == "i_tod_spin_ico_plating" and chips.children[ 3 ].Icon.image == "i_tod_spin_ico_salvage", "chips carry the item icons" )
        assert( chips.children[ 2 ].alpha < 1, "an empty chip is dimmed" )
    end
    send( "tod_spin_open", { 4242, prize, 0, 80 * 64 + LAND } )
    if withVeil then
        assert( veilOwners.spin == true, "the spin holds the HUD veil while open" )
        assert( chips.alpha == 0, "the chips hide under the veil" )
    end
    assert( watch.anims[ #watch.anims ] == "tod_spin_watch", "the watchdog starts with the spin" )
    for k = 1, LAND do send( "tod_spin_step", { k, 50 } ) end
    local under
    for _, t in ipairs( strip.children ) do
        if t.lr and strip.lr[ 1 ] + t.lr[ 1 ] + 70 == 500 then under = t end
    end
    assert( under, "a tile sits under the needle at the landing step" )
    assert( under.Name.text == "ARC CHAIN", "landing tile shows the prize, got " .. tostring( under.Name.text ) )
    if art then
        assert( under.Img.image == "i_tod_spin_tile_legendary", "landing tile wears the LEGENDARY tile art, got " .. tostring( under.Img.image ) )
        assert( under.Icon.image == "i_tod_spin_ico_arc", "landing tile shows the ARC CHAIN icon" )
        assert( under.Icon.rgb and under.Icon.rgb[ 1 ] == 1 and under.Icon.rgb[ 3 ] < 0.3, "the icon is tinted gold" )
    else
        assert( under.Rar.text == "LEGENDARY", "landing tile rarity" )
    end

    -- results: mode 2 names the slot, mode 3 names the luck paid back
    -- the status line is the text element in the band y 400..418
    local status
    for _, c in ipairs( panel.children ) do
        local top = ( c.opts and c.opts.top ) or ( c.tb and c.tb[ 1 ] )
        if top == 396 then status = c end
    end
    assert( status, "status line found" )
    local function findStatus() return status.text end
    send( "tod_spin_land", { prize, 1 } )
    assert( findStatus() == "SOCKETED", "auto-socket status" )
    if art then
        local banner, rays
        for _, c in ipairs( panel.children ) do
            if c.image == "i_tod_spin_banner_legendary" then banner = c end
            if c.image == "i_tod_spin_rays" then rays = c end
        end
        assert( banner and banner.alpha == 1, "the LEGENDARY banner stamps in" )
        assert( banner.anims[ #banner.anims ] == "tod_spin_stamp", "the banner pops (stamp tween)" )
        assert( rays and rays.anims[ #rays.anims ] == "tod_spin_rays", "a LEGENDARY throws the light rays" )
        assert( rays.lr[ 1 ] >= 100 and rays.lr[ 2 ] <= 1180 and rays.tb[ 1 ] >= 112 and rays.tb[ 2 ] <= 548, "the ray burst ends inside the panel" )
    end
    send( "tod_spin_slots", { prize, 0, 0, 0 * 10 + 2 } )
    assert( findStatus() == "SOCKETED IN SLOT 1", "result names the slot, got " .. tostring( findStatus() ) )
    send( "tod_spin_land", { prize, 2 } )
    send( "tod_spin_slots", { 0, prize, 0, 1 * 10 + 2 } )
    assert( findStatus() == "UPGRADED IN SLOT 2", "upgrade result, got " .. tostring( findStatus() ) )
    send( "tod_spin_land", { prize, 3 } )
    send( "tod_spin_slots", { 4, 8, 12, 5 * 100 + 2 * 10 + 1 } )
    send( "tod_spin_slots", { 4, 8, 12, 35 * 100 + 30 + 3 } )
    assert( findStatus() == "SCRAPPED FOR 35 LUCK", "scrap result, got " .. tostring( findStatus() ) )

    send( "tod_spin_end", {} )
    if withVeil then
        assert( veilOwners.spin == nil, "the veil drops at the end" )
        assert( chips.alpha == 1, "the chips come back with the HUD" )
    end
    assert( watch.anims[ #watch.anims ] == "tod_spin_watch_off", "the watchdog stops at the end" )

    -- the watchdog: an interrupted completion never closes a live spin; a real one does
    send( "tod_spin_open", { 7, 4, 0, 0 * 64 + 12 } )
    watch.handlers[ "transition_complete_tod_spin_watch" ]( watch, { interrupted = true } )
    if withVeil then assert( veilOwners.spin == true, "an interrupted watchdog tween is ignored" ) end
    watch.handlers[ "transition_complete_tod_spin_watch" ]( watch, { interrupted = false } )
    if withVeil then assert( veilOwners.spin == nil, "the watchdog releases a lost spin" ) end
    assert( panel.alpha == 0, "the watchdog drops the panel" )

    -- a card deal holding the veil keeps the chips hidden even with no spin
    if withVeil then
        CoD.TodHudVeil.Set( "cards", true )
        assert( chips.alpha == 0, "chips hide under the cards owner too" )
        CoD.TodHudVeil.Set( "cards", false )
        assert( chips.alpha == 1, "chips return when the cards owner drops" )
    end

    -- PK08 (W2G 2026-10-05): the chips sit on the COMPANION STATUS PLATE's top edge and go with it - the
    -- plate's own event (tod_ptn_hud: companion + 1, state, value, len, flags; flags 2 = its owner is dead)
    send( "tod_ptn_hud", { 2, 1, 100, 0, 2 } )
    assert( chips.alpha == 0, "the owner is dead: the plate hides and its chips with it" )
    send( "tod_ptn_hud", { 2, 1, 100, 0, 0 } )
    assert( chips.alpha == 1, "respawned: the chips are back on the plate" )
    send( "tod_ptn_hud", { 2, 1, 100, 0, 1 } )
    assert( chips.alpha == 1, "frozen with its owner the plate stays (HOLDING), so do the chips" )
    send( "tod_ptn_hud", { 0, 0, 0, 0, 0 } )
    assert( chips.alpha == 0, "no companion: no chips" )
    send( "tod_ptn_hud", { 2, 1, 100, 0, 0 } )
    send( "tod_ptn_hud", {} )
    assert( chips.alpha == 0, "a garbage plate event reads as no companion" )
    send( "tod_ptn_hud", { 2, 1, 100, 0, 0 } )
    assert( chips.alpha == 1, "and the next real one restores them" )
    local c1 = chips.children[ 3 ]
    assert( c1.lr and c1.lr[ 2 ] == -90 and c1.tb and c1.tb[ 2 ] == -200, "the chips' right edge is the plate's (x 1190), their foot 4 above its top (y 520)" )

    -- tease: a second run with a tease one past the prize
    send( "tod_spin_open", { 99, 1 * 4 + 1, 2 * 4 + 3, 0 * 64 + 12 } )
    for k = 1, 12 do send( "tod_spin_step", { k, 50 } ) end
    local found = false
    for _, t in ipairs( strip.children ) do
        if t.lr and t.lr[ 1 ] == 13 * 150 then
            assert( t.Name.text == "OVERCLOCK", "tease one past the prize" )
            if art then assert( t.Img.image == "i_tod_spin_tile_legendary", "the tease wears the LEGENDARY tile" )
            else assert( t.Rar.text == "LEGENDARY", "tease rarity" ) end
            found = true
        end
    end
    assert( found, "tease tile placed" )

    -- THE DEALER'S HOUSE (docs/207): THE LAST ROLL lands on CURSED (tile 60, code 9: LOCKSTEP _tod_shop.gsc) - the
    -- tile under the needle wears the cursed art and the mask, HOUSE WINS where the prize's name goes, the cursed
    -- banner stamps, no slot row, nothing paid; the tease before it is the LEGENDARY the reel hung on
    send( "tod_spin_open", { 777, 60, 1 * 64 + 39, 100 * 64 + LAND } )
    for k = 1, LAND do send( "tod_spin_step", { k, 50 } ) end
    local cursed
    for _, t in ipairs( strip.children ) do
        if t.lr and strip.lr[ 1 ] + t.lr[ 1 ] + 70 == 500 then cursed = t end
    end
    assert( cursed and cursed.alpha == 1, "a tile sits under the needle at the cursed landing" )
    assert( cursed.Name.text == "CURSED", "the landing tile reads CURSED, got " .. tostring( cursed.Name.text ) )
    if art then
        assert( cursed.Img.image == "i_tod_spin_tile_cursed" and cursed.Icon.image == "i_tod_spin_ico_cursed", "the cursed tile wears its own art and the mask" )
    else
        assert( cursed.Rar.text == "CURSED", "the flat lane names the curse" )
    end
    local tease
    for _, t in ipairs( strip.children ) do
        if t.lr and t.lr[ 1 ] == ( LAND + 1 ) * 150 then tease = t end
    end
    assert( tease and tease.Name.text == "LUCKY CHARM", "the hang before the curse is on a LEGENDARY LUCKY CHARM" )
    send( "tod_spin_land", { 60, 9 } )
    assert( findStatus() == "", "a cursed landing has no socket status" )
    local prizeName
    for _, c in ipairs( panel.children ) do
        if c.text == "HOUSE WINS" then prizeName = c end
    end
    assert( prizeName, "HOUSE WINS where the prize's name goes" )
    if art then
        local cb
        for _, c in ipairs( panel.children ) do
            if c.image == "i_tod_spin_banner_cursed" then cb = c end
        end
        assert( cb and cb.alpha == 1 and cb.anims[ #cb.anims ] == "tod_spin_stamp", "the cursed banner stamps in" )
    end
    for b = 1, 4 do
        -- no slot box shows: a curse is socketed nowhere
    end
    send( "tod_spin_end", {} )

    -- ==== THE DEALER'S GIFT (docs/209): a player with no companion is GIVEN one. The reel runs the four companions
    -- (tiles 45..48 = 44 + companion: LOCKSTEP _tod_shop.gsc TOD_GIFT_TILE_BASE), lands with code 8, shows the luck
    -- UNSPENT (no pour, no odds bar), punches the companion into the window that waited empty, and the slot row says
    -- SPIN TO FILL (mode 4). Driven exactly as _tod_shop.gsc gift() sends it.
    do
        local fx = reel.p3
        local st = fx.st
        local G = { base = 44, code = 8, mode = 4 }
        local SHORT = { "PROTECTOR", "TALON", "R.A.P.S.", "CERBERUS" }
        local NAMES = { "PROTECTOR", "TALON", "R.A.P.S.", "CERBERUS" }   -- W3E 2026-10-05: one name per companion (was CIVIL PROTECTOR here only)
        local PORTRAIT = { "i_tod_spin_comp_protector", "i_tod_spin_comp_talon", "i_tod_spin_comp_raps", "i_tod_spin_comp_cerberus" }
        local ICON = { "i_tod_spin_ico_comp_protector", "i_tod_spin_ico_comp_talon", "i_tod_spin_ico_comp_raps", "i_tod_spin_ico_comp_cerberus" }
        local function byTop( top )
            for _, c in ipairs( panel.children ) do
                local tp = ( c.opts and c.opts.top ) or ( c.tb and c.tb[ 1 ] )
                if tp == top then return c end
            end
        end
        local function isShort( s )
            for _, n in ipairs( SHORT ) do if s == n then return true end end
            return false
        end
        local prizeName, prizeFx = byTop( 342 ), byTop( 374 )
        assert( prizeName and prizeFx, "the prize name and effect lines found" )
        send( "tod_ptn_items", { 0, 0, 0, 0 } )                               -- he has no companion yet
        for comp = 1, 4 do
            local prize = G.base + comp
            send( "tod_spin_open", { 600 + comp, prize, 0, 64 * 64 + LAND } )   -- luck 64, the land at 30
            assert( st.gift and st.heat == 0 and st.nearKind == 0, "a companion tile as the prize opens a GIFT reel" )
            -- THE USER'S RULE: no luck is spent - nothing pours, the box keeps his bar
            assert( not st.pouring and fx.luckText.text == "LUCK 64", "the gift never pours the luck: " .. tostring( fx.luckText.text ) )
            for _ = 1, 40 do fx.tick.handlers[ "transition_complete_tod_spin_count" ]( fx.tick, {} ) end
            assert( fx.luckText.text == "LUCK 64", "a stray count tick never drains a gift's luck box" )
            assert( fx.oddsBack.alpha == 0, "no odds bar on a gift (nothing is rolled against the luck)" )
            for r = 0, 3 do assert( fx.odds[ r ].alpha == 0, "odds segment " .. r .. " hidden on a gift" ) end
            assert( fx.oddsCap.text == "THE DEALER'S GIFT - ON THE HOUSE" and fx.forText.text == "YOUR LUCK STAYS YOURS", "the gift's two lines: " .. tostring( fx.oddsCap.text ) .. " / " .. tostring( fx.forText.text ) )
            assert( fx.heatText.alpha == 0, "no heat chip on a gift" )
            if fx.comp then assert( fx.comp.clip.alpha == 0 and fx.comp.frame.alpha == 0, "the companion window waits empty until the reel lands" ) end
            -- THE POOL (mode 5) rides the open: the four companions the reel chooses from, one per box (box 4 a socket)
            send( "tod_spin_slots", { 0, 0, 0, 5 } )
            for b = 1, 4 do
                local bx = fx.boxes[ b ]
                assert( bx.Name.text == SHORT[ b ] and bx.Label.text == "COMPANION" and bx.Focus.alpha == 0, "the pool's box " .. b .. " is companion " .. b .. ", got " .. tostring( bx.Name.text ) )
                if art then
                    assert( bx.Sock.alpha == 1 and bx.Icon.alpha == 1 and bx.Icon.image == ICON[ b ], "the pool's box " .. b .. " shows its portrait" )
                    if b == 4 then assert( bx.Sock.image == "i_tod_spin_socket", "box 4 wears a socket in the pool, never SCRAP" ) end
                else
                    assert( bx.Plate.alpha > 0, "the pool's box " .. b .. " is drawn" )
                end
            end
            for k = 1, LAND do send( "tod_spin_step", { k, 50 } ) end
            -- every tile on the strip is a companion tile, and the one under the needle is HIS
            local under
            for _, tl in ipairs( strip.children ) do
                if tl.idx and tl.alpha == 1 then
                    assert( isShort( tl.Name.text ), "a gift reel's tile names a companion, got " .. tostring( tl.Name.text ) )
                    if art then assert( tl.Img.image == "i_tod_spin_tile_gift", "a gift tile wears the COMPANION tile" ) end
                end
                if tl.lr and strip.lr[ 1 ] + tl.lr[ 1 ] + 70 == 500 then under = tl end
            end
            assert( under and under.Name.text == SHORT[ comp ], "the tile under the needle is companion " .. comp .. ", got " .. tostring( under and under.Name.text ) )
            if art then
                assert( under.Icon.image == ICON[ comp ], "its portrait sits in the window" )
                assert( under.Icon.rgb[ 1 ] == 1 and under.Icon.rgb[ 2 ] == 1 and under.Icon.rgb[ 3 ] == 1, "a portrait is never tinted" )
            else
                assert( under.Rar.text == "COMPANION", "the flat lane's foot says COMPANION" )
            end
            send( "tod_spin_land", { prize, G.code } )
            assert( prizeName.text == NAMES[ comp ] and findStatus() == "IT FOLLOWS YOU NOW", "the landing names the companion: " .. tostring( prizeName.text ) )
            assert( prizeFx.text and #prizeFx.text > 0, "what it does is said under its name" )
            assert( not prizeFx.opts or #prizeFx.text <= prizeFx.opts.pool, "the role line fits its pool: " .. prizeFx.text )
            if art then
                local gb
                for _, c in ipairs( panel.children ) do if c.image == "i_tod_spin_banner_gift" then gb = c end end
                assert( gb and gb.alpha == 1 and gb.anims[ #gb.anims ] == "tod_spin_stamp", "ON THE HOUSE stamps in" )
                assert( fx.dealer.pic.image == "i_tod_spin_dealer_grin", "the dealer grins at his gift" )
                assert( fx.comp.clip.alpha == 1 and fx.comp.pic.image == PORTRAIT[ comp ] and fx.comp.name.text == NAMES[ comp ], "the companion punches into the window that waited" )
                local function punches() local n = 0 for _, a in ipairs( fx.comp.pic.anims ) do if a == "tod_spin_pose" then n = n + 1 end end return n end
                local p1 = punches()
                send( "tod_spin_land", { prize, G.code } )   -- a resume repaint
                assert( punches() == p1, "the companion's arrival plays once per gift" )
            end
            assert( fx.oddsBack.alpha == 0 and fx.forText.alpha == 0, "the gift's lines give way to the companion" )
            -- its three item slots, EMPTY, saying what the counter is for next time; nothing ringed, no SCRAP
            send( "tod_spin_slots", { 0, 0, 0, G.mode } )
            for b = 1, 3 do
                assert( fx.boxes[ b ].Name.text == "SPIN TO FILL" and fx.boxes[ b ].Label.text == "SLOT " .. b, "slot " .. b .. " says SPIN TO FILL" )
                assert( fx.boxes[ b ].Focus.alpha == 0, "the gift's slot row rings nothing" )
            end
            local sb = fx.boxes[ 4 ]
            assert( ( art and sb.Sock.alpha == 0 ) or ( not art and sb.Plate.alpha == 0 ), "no SCRAP on a gift" )
            assert( sb.Name.text == "" and sb.Label.text == "", "the pool's fourth companion leaves box 4 at the landing" )
            if art then assert( sb.Icon.alpha == 0, "box 4's portrait goes with it" ) end
            send( "tod_spin_end", {} )
        end
        -- NEGATIVE CONTROLS: the next ordinary spin is untouched by a gift before it - it pours, its filler is items,
        -- its odds bar is back; and mode 0 still says EMPTY
        send( "tod_ptn_items", { 0, 0, 0, 2 } )
        send( "tod_spin_open", { 700, 3 * 4 + 1, 0, 64 * 64 + LAND } )
        assert( not st.gift and st.pouring and fx.oddsCap.text == "YOUR LUCK SETS THE ODDS", "an item spin after a gift pours and shows its odds" )
        assert( fx.oddsBack.alpha > 0, "the odds bar is back on a spin" )
        for k = 1, 6 do send( "tod_spin_step", { k, 50 } ) end
        for _, tl in ipairs( strip.children ) do
            if tl.idx and tl.alpha == 1 then
                assert( not isShort( tl.Name.text ), "an item reel shows no companion tiles, got " .. tostring( tl.Name.text ) )
                if art then assert( tl.Img.image ~= "i_tod_spin_tile_gift", "an item reel never wears the COMPANION tile" ) end
            end
        end
        send( "tod_spin_slots", { 0, 0, 0, 0 } )
        assert( fx.boxes[ 1 ].Name.text == "EMPTY", "an ordinary empty slot still says EMPTY" )
        -- after a gift's pool, a full-slots choice shows box 4 as the SCRAP box again (its art, its own colour)
        send( "tod_spin_slots", { 4, 8, 12, 0 * 100 + 3 * 10 + 1 } )
        if art then
            local sb = fx.boxes[ 4 ]
            assert( sb.Sock.alpha == 1 and sb.Sock.image == "i_tod_spin_scrap" and sb.Sock.rgb[ 1 ] == 1 and sb.Sock.rgb[ 2 ] == 1 and sb.Icon.alpha == 0, "box 4 is the SCRAP box again after a gift" )
        end
        send( "tod_spin_end", {} )
        -- values just outside the gift range are never companions (and never throw)
        send( "tod_spin_land", { G.base, G.code } ); send( "tod_spin_land", { G.base + 5, G.code } )
        -- GLYPH POOLS: every gift line fits the row that draws it (a pool is a HARD character limit that clips silently)
        if prizeName.opts then
            for _, n in ipairs( NAMES ) do assert( #n <= prizeName.opts.pool, "prize name pool " .. prizeName.opts.pool .. " holds " .. n ) end
            assert( #"THE DEALER'S GIFT - ON THE HOUSE" <= fx.oddsCap.opts.pool, "the caption fits its pool " .. fx.oddsCap.opts.pool )
            assert( #"YOUR LUCK STAYS YOURS" <= fx.forText.opts.pool, "the luck line fits its pool" )
            assert( #"IT FOLLOWS YOU NOW" <= byTop( 396 ).opts.pool, "the status fits its pool" )
            assert( #"SPIN TO FILL" <= fx.boxes[ 1 ].Name.opts.pool, "SPIN TO FILL fits a slot's pool" )
            for _, tl in ipairs( strip.children ) do
                for _, n in ipairs( SHORT ) do assert( #n <= tl.Name.opts.pool, "tile name pool holds " .. n ) end
                break
            end
            if fx.comp then for _, n in ipairs( NAMES ) do assert( #n <= fx.comp.name.opts.pool, "the companion plate holds " .. n ) end end
        end
    end

    -- the menu closing mid-spin never leaves the veil held
    reel:close()
    if withVeil then assert( veilOwners.spin == nil, "closing the reel mid-spin releases the veil" ) end

    -- ==== PASS 3 (docs/188): the machine comes alive =====================================
    if withFx then
        local fx = reel.p3
        assert( fx and fx.st and fx.boxes and fx.luckText, "the pass-3 test hook is exposed" )
        -- the LOCKSTEP mirror of _tod_shop.gsc roll_rarity (written independently here):
        -- the line, then 50+ luck lifts COMMON to RARE, 100 lifts COMMON / RARE to EPIC (25 in 100 LEGENDARY)
        local function gscOdds( L )
            local c, r, e = 56 - 0.20 * L, 27 + 0.09 * L, 13 + 0.07 * L
            local l = 100 - c - r - e
            if L >= 100 then return { 0, 0, e + ( c + r ) * 0.75, l + ( c + r ) * 0.25 } end
            if L >= 50 then return { 0, r + c, e, l } end
            return { c, r, e, l }
        end
        local function tickAll()
            for _ = 1, 40 do fx.tick.handlers[ "transition_complete_tod_spin_count" ]( fx.tick, {} ) end
        end
        local W = 830 - 450
        for _, L in ipairs( { 0, 20, 49, 50, 80, 99, 100 } ) do
            send( "tod_ptn_items", { 5, 0, 33, 2 } )                    -- the TALON (companion id 1 + 1)
            send( "tod_spin_open", { 11, 4 * 4 + 2, 0, L * 64 + LAND } )
            send( "tod_spin_slots", { 5, 0, 33, 0 } )                   -- the server sends the slots with the open
            assert( fx.dim.alpha == 0.55, "the room dims behind the machine" )
            assert( fx.forText.text == "FOR YOUR TALON", "who the spin is for, got " .. tostring( fx.forText.text ) )
            local shown = ( art and fx.boxes[ 1 ].Sock.alpha == 1 ) or ( not art and fx.boxes[ 1 ].Plate.alpha > 0 )
            assert( shown and fx.boxes[ 1 ].Name.text == "PLATING", "the slots show from the open" )
            local o = gscOdds( L )
            for r = 0, 3 do
                local seg = fx.odds[ r ]
                local w = seg.lr[ 2 ] - seg.lr[ 1 ]
                assert( math.abs( w - W * o[ r + 1 ] / 100 ) < 0.01, "odds bar at luck " .. L .. ": segment " .. r .. " is " .. w .. " wide, the roll says " .. W * o[ r + 1 ] / 100 )
                assert( ( seg.alpha == 1 ) == ( w > 0.5 ), "an empty odds segment is hidden (luck " .. L .. ", rarity " .. r .. ")" )
            end
            assert( fx.st.pouring and fx.luckText.text == "LUCK " .. L, "the pour starts from the bar the player paid in" )
            tickAll()
            assert( fx.luckText.text == "LUCK 0", "the pour drains the counter to 0, got " .. tostring( fx.luckText.text ) )
            -- docs/201 section 6: a bar one segment under a guarantee says which one it missed
            local cap = ( L >= 100 and "FULL LUCK - EPIC OR BETTER" ) or ( L >= 90 and "ONE SEGMENT FROM AN EPIC" ) or ( L >= 50 and "RARE OR BETTER GUARANTEED" )
                        or ( L >= 40 and "ONE SEGMENT FROM A RARE" ) or "YOUR LUCK SETS THE ODDS"
            assert( fx.oddsCap.text == cap, "the caption names the guarantee (or the one segment it missed) at luck " .. L .. ", got " .. tostring( fx.oddsCap.text ) )
        end
        -- a step lands the pour at once (a resume after a card deal jumps straight in)
        send( "tod_spin_open", { 12, 4 * 4 + 2, 0, 70 * 64 + LAND } )
        send( "tod_spin_step", { 1, 50 } )
        assert( not fx.st.pouring and fx.luckText.text == "LUCK 0", "a step finishes the pour" )
        fx.tick.handlers[ "transition_complete_tod_spin_count" ]( fx.tick, {} )
        assert( fx.luckText.text == "LUCK 0", "a late tick after the cut never restarts the count" )
        -- the needle kicks and the rail runners hop, one per tile
        if art then assert( fx.needle and fx.needle.anims[ #fx.needle.anims ] == "tod_spin_needle", "the needle kicks on a step" ) end
        assert( #fx.runners == 4 and fx.runners[ 1 ].el.anims[ #fx.runners[ 1 ].el.anims ] == "tod_spin_run", "the rail lights run" )
        -- THE STOP: the last (slow) step runs past the prize, then settles back onto it
        for k = 2, LAND - 1 do send( "tod_spin_step", { k, 50 } ) end
        send( "tod_spin_step", { LAND, 700 } )
        local stripX = 500 - 70 - LAND * 150
        assert( strip.anims[ #strip.anims ] == "tod_spin_over" and strip.lr[ 1 ] == stripX - 26, "the reel overshoots the prize" )
        strip.handlers[ "transition_complete_tod_spin_over" ]( strip, { interrupted = false } )
        assert( strip.anims[ #strip.anims ] == "tod_spin_settle" and strip.lr[ 1 ] == stripX, "and settles back onto it" )
        -- the celebration plays ONCE though tod_spin_land comes again when the choice starts
        local leg = 5 * 4 + 3
        send( "tod_spin_land", { leg, 3 } )
        local rings = 0
        for _, a in ipairs( fx.ring.anims ) do if a == "tod_spin_ring" then rings = rings + 1 end end
        send( "tod_spin_land", { leg, 3 } )
        local rings2 = 0
        for _, a in ipairs( fx.ring.anims ) do if a == "tod_spin_ring" then rings2 = rings2 + 1 end end
        assert( rings2 == rings and rings >= 1, "one ring per spin, not one per land event" )
        assert( fx.edge.anims[ #fx.edge.anims ] == "tod_spin_edge" and fx.dim.anims[ #fx.dim.anims ] == "tod_spin_flash", "a LEGENDARY glows the screen edge and flashes" )
        assert( panel.anims[ #panel.anims ] == "tod_spin_shake", "a LEGENDARY shakes the machine" )
        assert( fx.oddsBack.alpha == 0 and fx.forText.alpha == 0, "the spin info gives way to the prize" )
        -- THE SOCKET: the prize flies into slot 2, whose icon appears (and flashes) on arrival
        send( "tod_spin_slots", { 5, leg, 33, 1 * 10 + 2 } )
        if art then
            assert( fx.flyer.anims[ #fx.flyer.anims ] == "tod_spin_fly" and fx.flyer.image == "i_tod_spin_ico_nano", "the prize flies to its slot" )
            assert( fx.boxes[ 2 ].Icon.alpha == 0, "the slot waits for it" )
            fx.flyer.handlers[ "transition_complete_tod_spin_fly" ]( fx.flyer, {} )
            assert( fx.boxes[ 2 ].Icon.alpha == 1 and fx.boxFlash.anims[ #fx.boxFlash.anims ] == "tod_spin_boxflash", "it lands and the slot flashes" )
            local flies = #fx.flyer.anims
            send( "tod_spin_slots", { 5, leg, 33, 1 * 10 + 2 } )   -- a repaint after a pause never flies again
            assert( #fx.flyer.anims == flies, "one flight per spin" )
        end
        -- the chip of the new item pulses once the HUD comes back
        send( "tod_spin_end", {} )
        if withVeil and art then
            local chip = chips.children[ 2 ]
            assert( chip.Flash and chip.Flash.anims[ #chip.Flash.anims ] == "tod_spin_chip", "the new item's chip pulses when the HUD returns" )
        end
        -- THE SCRAP: luck back into the counter
        send( "tod_spin_open", { 13, 2 * 4, 0, 20 * 64 + LAND } )
        send( "tod_spin_land", { 2 * 4, 3 } )
        send( "tod_spin_slots", { 5, 26, 33, 10 * 100 + 30 + 3 } )
        tickAll()
        assert( fx.luckText.text == "LUCK 10", "a scrap counts its luck back up, got " .. tostring( fx.luckText.text ) )
        send( "tod_spin_end", {} )
    end

    -- ==== PASS 3 ART (docs/195): the dealer reacts, the companion gets it, the speed ====
    if art then
        local fx = reel.p3
        assert( fx.dealer and fx.comp and fx.streaks, "the art lane builds both portraits and the streaks" )
        local function punches( p ) local n = 0 for _, a in ipairs( p.pic.anims ) do if a == "tod_spin_pose" then n = n + 1 end end return n end
        -- both frames sit inside the panel and the dealer's plate names him
        assert( fx.dealer.frame.lr[ 1 ] == 144 and fx.comp.frame.lr[ 2 ] == 1136, "the portrait frames sit where docs/195 put them" )
        assert( fx.dealer.name.text == "THE DEALER", "the dealer's plate names him" )
        send( "tod_ptn_items", { 5, 0, 33, 4 } )                         -- the CERBERUS (companion id 3 + 1)
        send( "tod_spin_open", { 21, 2 * 4 + 3, 0, 60 * 64 + LAND } )    -- an OVERCLOCK LEGENDARY
        assert( fx.dealer.pic.image == "i_tod_spin_dealer_idle", "the dealer waits at the open, got " .. tostring( fx.dealer.pic.image ) )
        assert( fx.comp.pic.image == "i_tod_spin_comp_cerberus" and fx.comp.name.text == "CERBERUS", "the right window shows the companion that gets the item" )
        assert( fx.comp.clip.alpha == 1 and fx.comp.frame.alpha == 1, "the companion window is up" )
        assert( fx.streaks.alpha == 0, "no streaks before the reel moves" )
        send( "tod_spin_step", { 1, 50 } )
        assert( math.abs( fx.streaks.alpha - 0.55 ) < 0.001, "a fast tile draws the streaks at full strength, got " .. fx.streaks.alpha )
        send( "tod_spin_step", { 2, 190 } )
        assert( fx.streaks.alpha > 0 and fx.streaks.alpha < 0.55, "a slowing reel thins the streaks" )
        for k = 3, LAND - 5 do send( "tod_spin_step", { k, 400 } ) end
        assert( fx.streaks.alpha == 0, "the slow crawl has no streaks" )
        assert( fx.dealer.pic.image == "i_tod_spin_dealer_idle", "the dealer holds idle until the last tiles" )
        local p0 = punches( fx.dealer )
        send( "tod_spin_step", { LAND - 4, 500 } )
        assert( fx.dealer.pic.image == "i_tod_spin_dealer_watch" and punches( fx.dealer ) == p0 + 1, "he leans in for the last slow tiles" )
        for k = LAND - 3, LAND - 1 do send( "tod_spin_step", { k, 600 } ) end
        assert( punches( fx.dealer ) == p0 + 1, "a pose he holds never punches twice" )
        send( "tod_spin_step", { LAND, 700 } )
        send( "tod_spin_land", { 2 * 4 + 3, 3 } )
        assert( fx.dealer.pic.image == "i_tod_spin_dealer_jackpot" and punches( fx.dealer ) == p0 + 2, "a LEGENDARY is his jackpot" )
        assert( fx.dealer.flash.rgb[ 1 ] == 1 and fx.dealer.flash.rgb[ 3 ] < 0.3, "his window flashes the prize's gold" )
        send( "tod_spin_land", { 2 * 4 + 3, 3 } )                          -- re-sent when the choice starts
        assert( punches( fx.dealer ) == p0 + 2, "the reaction plays once per spin" )
        send( "tod_spin_slots", { 5, 2 * 4 + 3, 33, 1 * 10 + 2 } )
        if fx.flyer then
            local c0 = punches( fx.comp )
            fx.flyer.handlers[ "transition_complete_tod_spin_fly" ]( fx.flyer, {} )
            assert( punches( fx.comp ) == c0 + 1 and fx.comp.flash.rgb[ 1 ] == 1 and fx.comp.flash.rgb[ 3 ] < 0.3, "the power flows into the companion in the prize's colour" )
        end
        send( "tod_spin_end", {} )
        -- the plain prizes: a shrug for COMMON, a grin for RARE / EPIC
        for _, c in ipairs( { { 0, "i_tod_spin_dealer_shrug" }, { 1, "i_tod_spin_dealer_grin" }, { 2, "i_tod_spin_dealer_grin" } } ) do
            send( "tod_spin_open", { 30 + c[ 1 ], 4 * 4 + c[ 1 ], 0, 10 * 64 + 12 } )
            assert( fx.dealer.pic.image == "i_tod_spin_dealer_idle", "every spin starts him idle" )
            send( "tod_spin_land", { 4 * 4 + c[ 1 ], 1 } )
            assert( fx.dealer.pic.image == c[ 2 ], "rarity " .. c[ 1 ] .. " gets " .. c[ 2 ] .. ", got " .. tostring( fx.dealer.pic.image ) )
            send( "tod_spin_end", {} )
        end
        -- no loadout known: the companion window stays hidden (never an empty frame)
        send( "tod_ptn_items", { 0, 0, 0, 0 } )
        send( "tod_spin_open", { 40, 4, 0, 0 * 64 + 12 } )
        assert( fx.comp.clip.alpha == 0 and fx.comp.frame.alpha == 0 and fx.comp.name.alpha == 0, "no companion known: its window is hidden" )
        send( "tod_spin_end", {} )
    end

    -- ==== THE NEAR MISS + THE HOT STREAK (docs/201): the packed tease (heat * 256 + kind * 64 + tile), both
    -- endings through the real tween chains, the heated odds, the chip, the embers ==============================
    do
        local fx = reel.p3
        local st = fx.st
        local function sx( k ) return 430 - k * 150 end           -- the module's stripX: CENTRE 500 - TILE_W / 2 - k * PITCH
        local function tileAt( left ) for _, t in ipairs( strip.children ) do if t.lr and t.lr[ 1 ] == left then return t end end end
        local function glowCx() return ( fx.nearGlow.lr[ 1 ] + fx.nearGlow.lr[ 2 ] ) / 2 end
        local function last( e ) return e.anims[ #e.anims ] end
        -- STOPPED SHORT: the better tile waits one past the prize; the last step runs to the seam, hangs, settles back
        send( "tod_spin_open", { 51, 2 * 4 + 1, 1 * 64 + ( 6 * 4 + 3 ), 30 * 64 + 12 } )   -- an OVERCLOCK RARE; ARC CHAIN LEGENDARY teased
        assert( st.nearKind == 1 and st.tease == 6 * 4 + 3 and st.heat == 0, "the packed tease decodes: kind 1, the tile, no heat" )
        for k = 1, 11 do send( "tod_spin_step", { k, 50 } ) end
        send( "tod_spin_step", { 12, 1100 } )
        assert( last( strip ) == "tod_spin_nearrun" and strip.lr[ 1 ] == sx( 12 ) - 62, "STOPPED SHORT runs 62 past the prize to the seam, got " .. tostring( last( strip ) ) .. " at " .. strip.lr[ 1 ] )
        local teased = tileAt( 13 * 150 )
        assert( teased and teased.Name.text == "ARC CHAIN", "the better tile sits one past the prize" )
        if art then assert( teased.Img.image == "i_tod_spin_tile_legendary", "it wears the LEGENDARY tile" ) end
        strip.handlers[ "transition_complete_tod_spin_nearrun" ]( strip, { interrupted = true } )
        assert( last( strip ) == "tod_spin_nearrun", "an interrupted run never starts the hang" )
        strip.handlers[ "transition_complete_tod_spin_nearrun" ]( strip, {} )
        assert( last( strip ) == "tod_spin_hang" and strip.lr[ 1 ] == sx( 12 ) - 66, "it HANGS on the seam, still creeping (never a stop)" )
        assert( fx.nearGlow.alpha > 0.5 and fx.nearGlow.rgb[ 1 ] == 1 and fx.nearGlow.rgb[ 3 ] < 0.3, "the LEGENDARY on the seam glows gold" )
        assert( glowCx() == 640 + 150 - 66, "the glow sits on the teased tile, got " .. glowCx() )
        if fx.needle then assert( last( fx.needle ) == "tod_spin_lean", "the needle strains after it" ) end
        strip.handlers[ "transition_complete_tod_spin_hang" ]( strip, {} )
        assert( last( strip ) == "tod_spin_settle" and strip.lr[ 1 ] == sx( 12 ), "and falls back onto the prize" )
        local under = nil
        for _, t in ipairs( strip.children ) do if t.lr and strip.lr[ 1 ] + t.lr[ 1 ] + 70 == 500 then under = t end end
        assert( under and under.Name.text == "OVERCLOCK", "the prize is what lands under the needle" )
        send( "tod_spin_land", { 2 * 4 + 1, 1 } )
        assert( fx.nearGlow.alpha == 0 and last( fx.nearGlow ) == "tod_spin_neardrain", "the land lets the glow go" )
        if art then
            assert( fx.dealer.pic.image == "i_tod_spin_dealer_shrug", "he shrugs at what you nearly had, got " .. tostring( fx.dealer.pic.image ) )
            assert( fx.dealer.flash.rgb[ 1 ] == 1 and fx.dealer.flash.rgb[ 3 ] < 0.3, "his window flashes the gold he nearly paid" )
        end
        send( "tod_spin_end", {} )
        -- SLIPPED PAST: the jackpot is the tile BEFORE the prize; the last step creeps across it, then crawls off
        send( "tod_spin_open", { 52, 5 * 4 + 1, 2 * 64 + ( 2 * 4 + 3 ), 0 * 64 + 12 } )   -- a NANO REPAIR RARE; OVERCLOCK LEGENDARY slips past
        for k = 1, 11 do send( "tod_spin_step", { k, 50 } ) end
        under = nil
        for _, t in ipairs( strip.children ) do if t.lr and strip.lr[ 1 ] + t.lr[ 1 ] + 70 == 500 then under = t end end
        assert( under and under.Name.text == "OVERCLOCK", "SLIPPED PAST: the jackpot reaches the needle one step before the prize" )
        send( "tod_spin_step", { 12, 1550 } )
        assert( last( strip ) == "tod_spin_creep" and strip.lr[ 1 ] == sx( 11 ) - 14, "it creeps across the jackpot (never a stop), got " .. tostring( last( strip ) ) )
        -- the creep holds the strip at the jackpot, so the reel's left tile is tile 8 (= k - 4), on screen at -34..106 for
        -- the whole creep: the window must still hold it. It ran to k + 5 until 2026-10-02 - ten tiles into nine slots -
        -- and k + 5 took k - 4's slot: an empty gap at the reel's left edge for most of a second
        local held = {}
        for _, t in ipairs( strip.children ) do if t.idx then held[ t.idx ] = ( held[ t.idx ] or 0 ) + 1 end end
        for i = 12 - 4, 12 + 4 do assert( held[ i ] == 1, "the tile window holds tile " .. i .. " exactly once (k-4..k+4), got " .. tostring( held[ i ] ) ) end
        local leftTile = nil
        for _, t in ipairs( strip.children ) do if t.idx == 8 then leftTile = t end end
        assert( leftTile and leftTile.alpha == 1 and leftTile.lr[ 1 ] == 8 * 150, "the left tile stays painted and in place while the jackpot creeps under the needle" )
        assert( fx.nearGlow.alpha > 0.4 and glowCx() == 640 and fx.nearGlow.rgb[ 1 ] == 1, "the jackpot under the needle glows gold" )
        strip.handlers[ "transition_complete_tod_spin_creep" ]( strip, {} )
        assert( last( strip ) == "tod_spin_slip" and strip.lr[ 1 ] == sx( 12 ), "then crawls on to the prize" )
        assert( fx.nearGlow.alpha == 0, "its glow goes with it" )
        if fx.needle then assert( last( fx.needle ) == "tod_spin_needle", "the needle kicks as the jackpot leaves it" ) end
        send( "tod_spin_land", { 5 * 4 + 1, 1 } )
        send( "tod_spin_end", {} )
        -- a resume after a card deal re-sends the last step at 50 ms: straight to the prize, no near miss replayed
        send( "tod_spin_open", { 52, 5 * 4 + 1, 2 * 64 + ( 2 * 4 + 3 ), 0 * 64 + 12 } )
        send( "tod_spin_step", { 12, 50 } )
        assert( last( strip ) == "tod_spin_step" and strip.lr[ 1 ] == sx( 12 ), "a resume jumps straight to the prize" )
        send( "tod_spin_end", {} )
        -- THE HOT STREAK: a spin rolled ON FIRE at 30 luck draws the heated true odds, names the heat, pours embers
        local function hotOdds( L, hm )   -- written independently of the module: _tod_shop.gsc roll_rarity's line
            local c, r, e = 56 - 0.20 * L, 27 + 0.09 * L, 13 + 0.07 * L
            local l = 100 - c - r - e
            c = c - ( e * hm - e ) - ( l * hm - l )
            e, l = e * hm, l * hm
            if L >= 100 then return { 0, 0, e + ( c + r ) * 0.75, l + ( c + r ) * 0.25 } end
            if L >= 50 then return { 0, r + c, e, l } end
            return { c, r, e, l }
        end
        for _, case in ipairs( { { 30, 3, 1.5 }, { 30, 1, 1.15 }, { 60, 2, 1.30 }, { 100, 3, 1.5 } } ) do
            local L, h, hm = case[ 1 ], case[ 2 ], case[ 3 ]
            send( "tod_spin_open", { 53, 4 * 4 + 2, h * 256, L * 64 + 12 } )
            assert( st.heat == h and st.nearKind == 0, "heat " .. h .. " decodes with no near miss" )
            local o = hotOdds( L, hm )
            for r = 0, 3 do
                local w = fx.odds[ r ].lr[ 2 ] - fx.odds[ r ].lr[ 1 ]
                assert( math.abs( w - 380 * o[ r + 1 ] / 100 ) < 0.01, "heated odds bar at luck " .. L .. " heat " .. h .. ": segment " .. r .. " is " .. w .. ", the roll says " .. 380 * o[ r + 1 ] / 100 )
            end
            assert( fx.heatText.alpha == 1 and fx.heatText.text == ( { "WARM", "HEATING UP", "ON FIRE" } )[ h ], "the chip names heat " .. h .. ", got " .. tostring( fx.heatText.text ) )
            if #fx.motes > 0 then assert( fx.motes[ 1 ].rgb[ 1 ] == 1 and fx.motes[ 1 ].rgb[ 2 ] < 0.6, "a hot player's luck pours in as embers" ) end
            for _ = 1, 40 do fx.tick.handlers[ "transition_complete_tod_spin_count" ]( fx.tick, {} ) end
            if L < 40 then assert( fx.oddsCap.text == "HOT STREAK - BETTER ODDS", "the caption says the streak is heating the odds, got " .. tostring( fx.oddsCap.text ) ) end
            send( "tod_spin_end", {} )
        end
        -- the spin's own result moves the streak: the chip follows while the panel is up (a pulse on a rise)
        send( "tod_spin_open", { 54, 4 * 4 + 2, 1 * 256, 20 * 64 + 12 } )
        send( "tod_luck_heat", { 3, 4, 1 } )
        assert( fx.heatText.text == "ON FIRE" and last( fx.heatText ) == "tod_spin_heat", "a rise pulses the chip to ON FIRE" )
        send( "tod_luck_heat", { 0, 0, 2 } )
        assert( fx.heatText.alpha == 0, "a streak that ends hides the chip" )
        send( "tod_luck_heat", {} ); send( "tod_luck_heat", { "x", "y" } )
        assert( fx.heatText.alpha == 0, "garbage heat args read as cold" )
        send( "tod_spin_end", {} )
        send( "tod_luck_heat", { 2, 3, 1 } )   -- the panel is down: nothing to draw, nothing thrown
        -- cold: no chip, green luck motes
        send( "tod_spin_open", { 55, 4 * 4 + 2, 0, 30 * 64 + 12 } )
        assert( fx.heatText.alpha == 0, "cold: no chip" )
        if #fx.motes > 0 then assert( fx.motes[ 1 ].rgb[ 2 ] == 1, "cold luck pours in green" ) end
        send( "tod_spin_end", {} )
        -- the reel itself runs hotter: count the EPIC+ filler tiles the module paints, cold vs ON FIRE, same seeds
        local function epicPlus( h )
            local n = 0
            for seed = 1, 40 do
                send( "tod_spin_open", { seed, 4 * 4, h * 256, 0 * 64 + 30 } )
                for k = 1, 30 do
                    send( "tod_spin_step", { k, 50 } )
                    for _, t in ipairs( strip.children ) do
                        if t.idx and t.idx ~= 30 and t.idx == k + 4 and t.alpha == 1 then
                            local rr = ( art and t.Img.image ) or ( t.Rar and t.Rar.text )
                            if rr == "i_tod_spin_tile_epic" or rr == "i_tod_spin_tile_legendary" or rr == "EPIC" or rr == "LEGENDARY" then n = n + 1 end
                        end
                    end
                end
                send( "tod_spin_end", {} )
            end
            return n
        end
        local cold, fire = epicPlus( 0 ), epicPlus( 3 )
        assert( fire > cold * 1.25, "ON FIRE puts clearly more EPIC+ tiles on the reel (" .. cold .. " vs " .. fire .. ")" )
    end

    -- ==== THE AI COMPANION ROW (user 2026-09-29: "wire it all up. Make sure the upgrades are there as
    -- well"): the reel records every companion's loadout + the held companion's state, and ONE describe
    -- says the pause menu / scoreboard row. Tiles = item * 4 + rarity.
    do
        local D = CoD.TodCompanionDescribe
        assert( type( D ) == "function" and CoD.TodCompanionInfo and CoD.TodCompanion, "the companion row's describe + tables exist" )
        send( "tod_ptn_items", { 3 * 4 + 3, 8 * 4 + 2, 9 * 4 + 1, 1 } )   -- the PROTECTOR: HOLLOW POINT L, QUICK REBOOT E, LUCKY CHARM R
        send( "tod_ptn_state", { 1, 2, 45, 15 } )                          -- destroyed, 45 s, all four built
        local d = D()
        assert( d.held and d.name == "PROTECTOR" and d.portrait == "i_tod_spin_comp_protector", "the held companion + its portrait" )
        assert( d.items == "HOLLOW, QUICK REBOOT, LUCKY CHARM", "past 35 characters the longest name gives way to its chip label: " .. d.items )
        assert( d.status == "DESTROYED - BACK IN 45 sec" and d.short == "BACK IN 45 sec" and d.tone == "hot", "destroyed: " .. d.status )
        assert( d.slots[ 1 ].icon == "i_tod_spin_ico_hollow" and d.slots[ 1 ].rgb == CoD.TodCompanionInfo.rarity[ 3 ].col, "slot 1 = HOLLOW POINT, gold" )
        assert( d.slots[ 2 ].rgb == CoD.TodCompanionInfo.rarity[ 2 ].col and d.slots[ 3 ].rgb == CoD.TodCompanionInfo.rarity[ 1 ].col, "slots 2 / 3 = epic purple / rare blue" )
        send( "tod_ptn_state", { 1, 1, 85, 15 } ); d = D()
        assert( d.status == "ACTIVE - HEALTH 85%" and d.short == "HEALTH 85%" and d.tone == "good", "active: " .. d.status )
        send( "tod_ptn_state", { 1, 3, 0, 15 } ); d = D()
        assert( d.status == "ON ITS WAY" and d.tone == "idle", "deploying: " .. d.status )
        -- each companion keeps its own loadout through a swap
        send( "tod_ptn_items", { 1 * 4 + 0, 0, 0, 4 } ); send( "tod_ptn_state", { 4, 1, 100, 15 } ); d = D()
        assert( d.name == "CERBERUS" and d.items == "PLATING" and d.slots[ 1 ] and d.slots[ 2 ] == false and d.slots[ 3 ] == false, "the CERBERUS: one COMMON item, two empty slots" )
        send( "tod_ptn_state", { 1, 1, 100, 15 } ); d = D()
        assert( d.name == "PROTECTOR" and d.items == "HOLLOW, QUICK REBOOT, LUCKY CHARM", "back to the PROTECTOR: its own three items" )
        send( "tod_ptn_items", { 0, 0, 0, 2 } ); send( "tod_ptn_state", { 2, 3, 0, 15 } ); d = D()
        assert( d.name == "TALON" and d.items == "NO ITEMS - SPIN AT THE BLACK MARKET", "no items yet: where to get them" )
        -- nothing held: THE DEALER'S GIFT (docs/209) - the row says where a free one waits, whatever the owned mask
        -- says (the partner benches and parts are retired: "build one at a partner bench" may never come back)
        send( "tod_ptn_items", { 0, 0, 0, 0 } ); send( "tod_ptn_state", { 0, 0, 0, 5 } ); d = D()
        assert( not d.held and d.name == "AI COMPANION" and d.items == "NONE YET" and d.status == "the Black Market dealer gives you one free", "none held (two owned): the gift line, got " .. tostring( d.items ) .. " / " .. tostring( d.status ) )
        send( "tod_ptn_state", { 0, 0, 0, 0 } ); d = D()
        assert( d.items == "NONE YET" and d.status == "the Black Market dealer gives you one free", "none owned: the gift line" )
        assert( not string.find( string.lower( d.status .. " " .. d.items ), "bench", 1, true ), "no row ever sends a player to a partner bench again" )
        send( "tod_ptn_state", { 9, 1, 50, 0 } ); d = D()
        assert( not d.held, "an unknown companion id never draws a row it cannot name" )
        send( "tod_ptn_state", {} ); send( "tod_ptn_state", { "x" } ); d = D()
        assert( not d.held, "garbage state args read as nothing held" )
        -- the line never outgrows 35 characters, whatever three items are held
        local ITEMS = CoD.TodCompanionInfo.items
        for a = 1, 9 do for b = 1, 9 do for c = 1, 9 do
            if a ~= b and b ~= c and a ~= c then
                send( "tod_ptn_items", { a * 4, b * 4 + 1, c * 4 + 3, 3 } ); send( "tod_ptn_state", { 3, 1, 100, 4 } )
                local line = D().items
                assert( #line <= 35, "item line fits: " .. line )
            end
        end end end
        send( "tod_ptn_state", { 0, 0, 0, 0 } )
    end
    send( "tod_ptn_items", { 0, 0, 0, 0 } )
    -- missing / garbage arguments must never throw
    send( "tod_spin_open", {} ); send( "tod_spin_step", {} ); send( "tod_spin_land", {} )
    send( "tod_spin_land", { 999, 1 } ); send( "tod_spin_slots", {} ); send( "tod_ptn_items", {} )
    send( "some_other_event", { 1 } )
    return veilCalls
end

run( false, false, true )   -- no glyph face, no veil module: still works, HUD simply never hides
run( true, false, true )
run( true, true, false )    -- the flat lane (USE_SPIN_ART false) still stands
local calls = run( true, true, true )
run( true, true, true, true )    -- pass 3 with the card reveal's FX sprites loaded
run( true, true, false, true )   -- ... and on the flat lane

-- every image the module names is zoned (GATE A says so too; this keeps the
-- harness honest on its own)
local zf = assert( io.open( "zone_source/zm_tod2_cybercity.zone", "r" ) )
local zone = zf:read( "*a" ); zf:close()
local zoned = {}
for line in string.gmatch( zone, "[^\r\n]+" ) do
    local img = string.match( line, "^image,(i_tod_spin_[a-z0-9_]+)%s*$" )
    if img then zoned[ img ] = true end
end
local named = 0
for img in string.gmatch( source, '"(i_tod_spin_[a-z0-9_]+)"' ) do
    named = named + 1
    assert( zoned[ img ], "zoned: " .. img )
end
assert( named == 46, "the module names all 46 spin images (docs/190's 26 + docs/195's 11 + docs/207's 3 + docs/209's 6), got " .. named )
assert( #calls >= 4, "the veil was driven" )

-- Filler odds: luck puts more colour on the strip (same LCG + line as the module).
local function lcg( seed, i ) local x = ( seed * 7 + ( i + 1000 ) * 131 ) % 65537 for _ = 1, 3 do x = ( x * 75 + 74 ) % 65537 end return x end
local function rar( r, L ) local c, rr, e = 56 - 0.2 * L, 27 + 0.09 * L, 13 + 0.07 * L if r < c then return 0 elseif r < c + rr then return 1 elseif r < c + rr + e then return 2 end return 3 end
local lo, hi = 0, 0
for seed = 1, 200 do for i = 0, 40 do
    if rar( lcg( seed, i ) % 100, 0 ) > 0 then lo = lo + 1 end
    if rar( lcg( seed, i ) % 100, 100 ) > 0 then hi = hi + 1 end
end end
assert( hi > lo * 1.2, "a full luck bar puts clearly more non-common tiles on the reel (" .. lo .. " vs " .. hi .. ")" )
print( "spin reel harness passed: prize under the needle, tease, HUD veil (open/end/watchdog/close), chips under any veil, result statuses, panel bounds, bad args, luck-weighted filler (" .. lo .. " -> " .. hi .. " of 8200); pass 3: room dim, slots + FOR YOUR <companion> from the open, odds bar = the roll at 7 luck values, the pour, needle, rail lights, overshoot stop, one celebration per spin, socket flight, chip pulse, scrap count-up; pass 3 art: the dealer idle / watch / reaction once per spin, the companion window (hidden when unknown), speed streaks by reel speed, the power flash; THE AI COMPANION ROW: loadouts per companion, state lines, the 35-character item line over all 504 loadouts, garbage args; THE NEAR MISS + THE HOT STREAK (docs/201): STOPPED SHORT (run, hang on the seam, settle back) and SLIPPED PAST (creep, slip) through the real tween chains, the k-4..k+4 tile window, a resume never replays one, the heated odds + caption, the heat chip, hotter filler." )
