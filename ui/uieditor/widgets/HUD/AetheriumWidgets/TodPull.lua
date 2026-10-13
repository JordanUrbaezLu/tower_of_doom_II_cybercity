-- =============================================================================
-- TodPull — THE PULL, the upgrade card reveal (docs/187, user 2026-09-28/29).
--
-- "There's a reason why players love crates in csgo. They always go through the
-- animation but it's the anticipation." / "I really want this system to be
-- perfected and easy to understand and the effects make it intuitive."
--
-- Every card is dealt FACE-DOWN and CLIMBS the rarity ladder one rung at a time
-- (COMMON white, RARE blue, EPIC purple, LEGENDARY gold) until it stops, then
-- flips. Three things teach the system on every deal with no text to read: the
-- COLOUR, the LADDER beside the card (COMMON +1 ... LEGENDARY +4) lighting rung
-- by rung, and the LEVEL PIPS lighting one at a time for the levels you gain.
--
-- PASS 2 (2026-09-29, user: "Looks pretty bland without UI", "doesn't look like
-- the artifact", "change our card design in general"):
--   * every effect is a SPRITE (tools/card_pull/install_card_art.py generates
--     them white; the game tints them): card glow, god rays that turn, diamond
--     shards, an expanding ring, a radial flash, the screen-edge glow, a light
--     sweep, the band pill, round level pips, ladder gems, rising motes;
--   * CARD V2 - the layered card (docs/191): illustration -> body -> rarity
--     frame -> crest -> LIVE text (title, two short lines, the band, the pips).
--     Drawn for an upgrade only when its layers are installed; everything else
--     keeps the old baked card with the live band + pips over it.
-- Every image comes from the GENERATED manifest CoD.TodCardArt (TodCardArt.lua),
-- so a piece that is not installed can never be asked for: it falls back.
--
-- THIS FILE OWNS THE LOOK; THE SERVER OWNS THE CLOCK. _tod_upgrade_ui.gsc
-- reveal_deal pushes one field edge per beat, and tod_upgrade.lua's Render hands
-- every paint to P.Render. Tweens are short and self-contained; every chain
-- treats an interrupted step as "jump to the end state".
--
-- TWEEN RULES: only alpha, rects and zRot are ever tweened; colours are stamped.
-- A tween the NEXT push can overtake stays under the shortest push gap (the
-- hitch, 95 ms at a co-op altar). zRot: the god rays turn by exactly one
-- symmetry period (RAYS_PERIOD, 8-fold art = 45 degrees) per step, so an engine
-- that does not interpolate zRot shows still rays, never a jump.
--
-- BUILT ONCE (pooled). Two build calls, because LUI draws in addElement order:
-- P.AttachUnder BEFORE the cards (dim, edge glow, god rays, card glow, motes),
-- P.Attach AFTER them (backs, ladders, card v2 layers, band + pips, banner,
-- shards, ring, flash).
-- =============================================================================

pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphRow" )
pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodCardArt" )   -- GENERATED manifest

CoD.TodPull = {}
local P = CoD.TodPull

local function Art()
	return CoD.TodCardArt or { fx = {}, art = {}, tier = {} }
end
local function FX( k )
	local a = Art()
	return a.fx and a.fx[ k ] or nil
end

-- ---- layout (card-relative canvas px on the 234 x 351 card) -----------------
-- OLD CARD (baked art): covers over the baked band / pips, measured on the
-- 768x1152 sources and scaled by 234/768.
local BAND_X0, BAND_X1, BAND_Y0, BAND_Y1 = 51, 183, 216, 238
-- 2026-09-29: every LIVE baked face is rarity-NEUTRAL now (the docs/189 drop: an
-- empty band slot, no rarity coin, an empty pip tray), so the dark covers that hid
-- the old baked "REGULAR +1" band and dots are off; the live pill + pips sit in the
-- painted slots. Set false only if a face with a baked band comes back.
local OLD_FACES_NEUTRAL = true
local PIPS_X0, PIPS_X1, PIPS_Y0, PIPS_Y1 = 44, 190, 303, 325
-- CARD V2 (docs/191 layout template x 234/768 - LOCKSTEP with that template)
local V2 = {
	art   = { 29, 54, 205, 190 },
	crest = { 173, 153, 217, 197 },
	band  = { 51, 200, 183, 221 },
	title = { 20, 11, 214, 45 },
	-- the dark label behind the white title, just inside the plate's bevel (the frame art's
	-- inner plate is 73..695 x 44..136 of 768 = 22.2..211.8 x 13.4..41.4 here)
	titleLabel = { 24.5, 15.5, 209.5, 39.5 },
	text  = { 27, 229, 207, 296 },
	pips  = { 56, 303, 178, 325 },
}
-- CARD TEXT SIZE (user 2026-09-29: "the text is too small, so it's a little bit hard to read"):
-- 13 / 9.5 / 10 -> 16 / 12.5 / 12. SetFit still shrinks a line that would outgrow its box.
local TITLE_CAP, LINE_CAP, BAND_CAP = 16, 12.5, 12
-- WHITE CARD TEXT ON A DARK GROUND (user 2026-09-29: "The title name of the upgrade card and
-- I think it's the description. They're both in like black ... make it white text ... check
-- the contrast"). The title and the rarity word were near-black on the light rarity plates;
-- white on those plates is no better (the gold plate is 244,197,95). So the letters are white
-- and what sits right under them is a dark shade of the rarity colour: the title's own label
-- inside the plate, and the rarity pill's fill. WCAG contrast of the white face on each ground
-- (the tod_upgrade.lua RARITY colours x GROUND_DIM): COMMON 8.0, RARE 12.0, EPIC 13.7, LEGENDARY
-- 9.6, all past 7:1; white on the old bright pills would be 1.2 / 2.6 / 3.5 / 1.6. The plates and
-- pills keep their bright rims, so the rarity still reads at a glance.
local TEXT_WHITE = { 1, 1, 1 }
local GROUND_DIM = 0.34
P.TEXT_WHITE, P.GROUND_DIM = TEXT_WHITE, GROUND_DIM   -- read by tools/test_card_pull.lua
local PIP_S, PIP_GAP = 10, 3
local PIP_MAX = 10
local PIP_TICK_MS = 130        -- one level lighting, then the next
local PIP_FIRST_MS = 140       -- the first pip waits for the face to open

-- the ladder beside each card: bottom rung at LAD_Y1, rungs climb upward
local LAD_W, LAD_GEM, LAD_PITCH = 108, 18, 30
local LAD_Y1 = 470
local LAD_GAP = 16
local LAD_CAP = 9

-- per rarity (index 1..4)
local BACK_CORE_A = { 0.18, 0.32, 0.48, 0.66 }   -- the back's inner glow, by rung reached
local EDGE_A      = { 0, 0, 0.32, 0.55 }          -- screen-edge glow while climbing (render_pull: 0.55/0.85 read as a thick border)
local DIM_BASE    = 0.35
local DIM_LEG     = 0.62
local FLASH_PEAK  = { 0, 0.45, 0.75, 1.0 }
local FLASH_SIZE  = { 0, 560, 820, 1300 }
local FLASH_MS    = { 0, 220, 340, 560 }
local RING_TO     = { 0, 300, 420, 620 }
local RING_MS     = { 0, 300, 380, 520 }
local SHARDS_N    = { 0, 6, 8, 10 }
local SHARD_REACH = { 0, 130, 180, 260 }
local SHARD_MS    = 320
local RAYS_A      = { 0, 0, 0.45, 0.85 }        -- the burst at the flip ...
local RAYS_STEADY = { 0, 0, 0.18, 0.34 }        -- ... settling to this while the player chooses
local RAYS_SIZE   = { 0, 0, 560, 760 }
local RAYS_PERIOD = 45        -- LOCKSTEP: fx_rays in install_card_art.py is 8-fold symmetric
local RAYS_MS     = { 0, 0, 3200, 2200 }
local GLOW_PAD    = 40        -- the glow sprite's rect stands this far proud of the card
local MOTES_N     = 6         -- LEGENDARY only
local MOTE_MS     = 1700
local BANNER_HOLD = { 420, 600, 760, 900 }
local BANNER_IN   = 80
local BANNER_OUT  = 160
local BEAT_GROW   = 5
local BEAT_MS     = 45
-- THE REACH (docs/201 section 4): after a heartbeat a card can STRAIN for the next rung - its next ladder gem flickers
-- in that rung's colour, a fill of the colour climbs two thirds up the back and holds, the card lifts and trembles -
-- then comes SO CLOSE (a third beat at the rung: the fill drains, the card sinks back) or BREAKS THROUGH (the climb:
-- the fill bursts, the card climbs on). Every tween fits the gap the next push can arrive in at a co-op altar
-- (x0.5): the reach waits TOD_PULL_REACH 0.62 s (310 ms), SO CLOSE's settle + hitch 0.45 s (225 ms), and a break
-- through's own climb is followed by a beat no sooner than 145 ms (rung 2). LOCKSTEP with _tod_upgrade_ui.gsc.
local REACH_RISE_MS   = 280     -- the fill climbing two thirds up the back
local REACH_FILL_A    = 0.7     -- 0.55 read tan over an EPIC's purple back (rendered 2026-10-02): it must read as the next rung's colour
local REACH_FLICK_MS  = 70      -- the next gem flickers: 4 steps
local REACH_FLICKS    = 4
local TREMBLE_MS      = 40      -- the strain: 6 steps of +-TREMBLE_PX, lifted REACH_LIFT
local TREMBLE_STEPS   = 6
local TREMBLE_PX      = 2
local REACH_LIFT      = 4
local REACH_DRAIN_MS  = 200     -- SO CLOSE: the fill drains ...
local REACH_GEM_OUT   = 140     -- ... the gem's flicker dies ...
local REACH_SINK      = 3       -- ... and the card sinks back onto the table
local REACH_SINK_MS   = 120
local BREAK_MS        = 140     -- BREAK THROUGH: the fill fills the back and bursts, a quick ring
local BREAK_RING      = 140
-- THE HOT STREAK (docs/201 section 5): a hot player's backs arrive warm - an orange halo and embers rising off them
-- (CoD.TodHeat, from tod_upgrade.lua's tod_luck_heat handler); 2 / 4 / 6 embers by heat. The flip ends them.
-- The embers are drawn OVER the back (built with it): the under layer's motes sit behind the opaque card, and the
-- first cut, which used them, showed nothing at all (render_pull 2026-10-02). The halo is the under glow, which
-- stands GLOW_PAD proud of the card: 0.14 + 0.06 x heat read as +20 red on the backdrop, so it is stronger now.
local HEAT_RGB        = { 1, 0.52, 0.14 }
local EMBERS_N        = 6       -- 2 / 4 / 6 by heat
local EMBER_MS        = 1300    -- one ember's rise (x0.7 .. x1.3); it loops while the back is warm
local EMBER_RISE      = 190     -- from the back's lower half up the card (the highest ones leave its top edge)
local EMBER_DRIFT     = 24      -- and a little sideways
local EMBER_A         = 0.9
P.REACH = { RISE = REACH_RISE_MS, DRAIN = REACH_DRAIN_MS, GEM_OUT = REACH_GEM_OUT, SINK = REACH_SINK_MS, BREAK = BREAK_MS,
            FLICK = REACH_FLICK_MS, TREMBLE = TREMBLE_MS, RING = BREAK_RING }   -- read by tools/test_card_pull.lua only
local BACK_FOLD_MS = 70
local V2_OPEN_MS  = { 90, 110, 130, 160 }   -- LOCKSTEP-ish with tod_upgrade.lua REVEAL_FLIP_MS
local SHARD_POOL  = 10

-- ---- small builders ----------------------------------------------------------
local function Panel( parent, HudRef, InstanceRef, x0, y0, x1, y1, rgb, a )
	local e = CoD.TextWithBg.new( HudRef, InstanceRef )
	e:setLeftRight( true, false, x0, x1 )
	e:setTopBottom( true, false, y0, y1 )
	e.Text:setText( "" )
	if rgb then
		e.Bg:setRGB( rgb[ 1 ], rgb[ 2 ], rgb[ 3 ] )
	end
	e.Bg:setAlpha( 1 )
	e:setAlpha( a or 0 )
	parent:addElement( e )
	return e
end

local function Img( parent, name, x0, y0, x1, y1, a )
	local e = LUI.UIImage.new()
	e:setLeftRight( true, false, x0, x1 )
	e:setTopBottom( true, false, y0, y1 )
	if name then
		e:setImage( RegisterImage( name ) )
	end
	e:setAlpha( a or 0 )
	parent:addElement( e )
	return e
end

-- an element whose tint lives on .Bg (panels) or on itself (images)
local function Tint( e, col )
	if e.Bg then
		e.Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
	else
		e:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
	end
end

local function Layer( parent )
	local e = LUI.UIElement.new()
	e:setLeftRight( true, true, 0, 0 )
	e:setTopBottom( true, true, 0, 0 )
	if CoD.TodUIOwnership then
		CoD.TodUIOwnership.Attach( e )
	end
	parent:addElement( e )
	return e
end

local function Row( owner, n )
	if not CoD.TodGlyphRow then
		return nil
	end
	return CoD.TodGlyphRow.make( owner, n )
end

-- WHICH GLYPH SET DRAWS A CHARACTER. The typeface has "+" and "/" ONLY in its
-- DIGIT set (i_tod_hud_dplus / _dslash); TodGlyphRow.nameSet sends every
-- non-number to the LETTER set, where they do not exist, so "EPIC +3" measured -1
-- and hid itself (seen in tools/ui_mockup/render_pull.py, 2026-09-29).
local function Pick( c )
	if ( c >= "0" and c <= "9" ) or c == "+" or c == "/" then
		return "digits"
	end
	return "letters"
end

-- centred text that SHRINKS to fit maxW; false when the typeface cannot draw it
local function SetFit( row, str, cap, cx, baseline, maxW )
	if not row then
		return false
	end
	local picker = Pick
	local w = row.measure( str, cap, picker )
	if w == nil or w < 0 then
		row.hide()
		return false
	end
	if maxW and w > maxW and w > 0 then
		cap = cap * maxW / w
		w = row.measure( str, cap, picker )
	end
	row.set( str, cap, cx + w / 2, baseline, picker )
	return true
end

local function Dim( col, f )
	return { col[ 1 ] * f, col[ 2 ] * f, col[ 3 ] * f }
end

-- the glyph face draws A-Z 0-9 - ' . / + only: upper-case and drop the rest
local function Clean( str )
	str = string.upper( str or "" )
	str = string.gsub( str, "[^A-Z0-9%-'%./%+ ]", " " )
	str = string.gsub( str, "%s+", " " )
	return ( string.gsub( str, "^%s*(.-)%s*$", "%1" ) )
end

-- =============================================================================
-- BUILD
-- =============================================================================

-- BEFORE the cards. rects = { a = { xLo, xHi }, b = { xLo, xHi } }, y0 / y1 = card top / bottom.
function P.AttachUnder( menu, HudRef, InstanceRef, rects, y0, y1 )
	local u = { slot = {} }
	u.dim = Panel( menu, HudRef, InstanceRef, 0, 0, 1280, 720, { 0, 0, 0 }, 0 )
	if FX( "edge" ) then
		u.edge = Img( menu, FX( "edge" ), 0, 0, 1280, 720, 0 )
	else
		u.edges = {
			Panel( menu, HudRef, InstanceRef, 0, 0, 1280, 70, nil, 0 ),
			Panel( menu, HudRef, InstanceRef, 0, 650, 1280, 720, nil, 0 ),
			Panel( menu, HudRef, InstanceRef, 0, 70, 110, 650, nil, 0 ),
			Panel( menu, HudRef, InstanceRef, 1170, 70, 1280, 650, nil, 0 ),
		}
	end
	rects = rects or {}
	for key, r in pairs( rects ) do
		local us = { xLo = r[ 1 ], xHi = r[ 2 ], y0 = y0 or 226, y1 = y1 or 577 }
		us.cx = ( us.xLo + us.xHi ) / 2
		us.cy = ( us.y0 + us.y1 ) / 2
		if FX( "rays" ) then
			us.rays = Img( menu, FX( "rays" ), us.cx - 10, us.cy - 10, us.cx + 10, us.cy + 10, 0 )
		end
		if FX( "glow" ) then
			us.glow = Img( menu, FX( "glow" ), us.xLo - GLOW_PAD, us.y0 - GLOW_PAD, us.xHi + GLOW_PAD, us.y1 + GLOW_PAD, 0 )
		end
		us.motes = {}
		if FX( "pip" ) then
			for i = 1, MOTES_N do
				us.motes[ i ] = Img( menu, FX( "pip" ), 0, 0, 5, 5, 0 )
			end
		end
		u.slot[ key ] = us
	end
	return u
end

-- one card's back: art (when installed) or panels + a placeholder sigil; a glow
-- core that brightens per rung; a sweep of light on every rung. TWO BACKS: the old
-- back (50 px in, the old faces' silhouette) and the card-v2 back (the whole canvas,
-- the layered card's silhouette); BackPick shows the one that matches the faces this
-- player will see, so a card never changes size when it flips.
local function BuildBack( menu, HudRef, InstanceRef, xLo, xHi, y0, y1 )
	local b = { xLo = xLo, xHi = xHi, y0 = y0, y1 = y1 }
	local mid = ( xLo + xHi ) * 0.5
	local art = Art().back or Art().back2
	if art then
		b.art = Img( menu, art, xLo, y0, xHi, y1, 0 )
		b.artOld, b.artV2, b.artNow = Art().back, Art().back2, art
		b.beat = b.art
	else
		b.rim  = Panel( menu, HudRef, InstanceRef, xLo, y0, xHi, y1, { 0.5, 0.5, 0.6 }, 0 )
		b.fill = Panel( menu, HudRef, InstanceRef, xLo + 5, y0 + 5, xHi - 5, y1 - 5, { 0.05, 0.045, 0.09 }, 0 )
		b.beat = b.rim
		local sy = y0 + 70
		b.sigil = {
			Panel( menu, HudRef, InstanceRef, mid - 7, sy, mid + 7, sy + 170, nil, 0 ),
			Panel( menu, HudRef, InstanceRef, mid - 16, sy + 22, mid + 16, sy + 30, nil, 0 ),
			Panel( menu, HudRef, InstanceRef, mid - 48, sy + 84, mid + 48, sy + 88, nil, 0 ),
			Panel( menu, HudRef, InstanceRef, mid - 36, sy + 170, mid + 36, sy + 178, nil, 0 ),
			Panel( menu, HudRef, InstanceRef, mid - 56, sy + 188, mid + 56, sy + 192, nil, 0 ),
		}
	end
	b.sigil = b.sigil or {}
	if FX( "glow" ) then
		b.core = Img( menu, FX( "glow" ), xLo + 10, y0 + 14, xHi - 10, y1 - 14, 0 )
	else
		b.core = Panel( menu, HudRef, InstanceRef, xLo + 28, y0 + 40, xHi - 28, y1 - 60, { 0.5, 0.5, 0.6 }, 0 )
	end
	if FX( "sweep" ) then
		b.sweep = Img( menu, FX( "sweep" ), xLo, y0 + 4, xLo + 40, y1 - 4, 0 )
	else
		b.sweep = Panel( menu, HudRef, InstanceRef, xLo, y0 + 5, xLo + 26, y1 - 5, { 1, 1, 1 }, 0 )
	end
	-- everything that folds away on the flip
	-- NOT ipairs over { b.rim, b.fill, b.art, b.core }: with the art back installed
	-- rim/fill are nil, ipairs stops at the first nil and the back never folded away
	-- (caught by tools/test_card_pull.lua the day the card back landed)
	b.parts = {}
	if b.rim then b.parts[ #b.parts + 1 ] = b.rim end
	if b.fill then b.parts[ #b.parts + 1 ] = b.fill end
	if b.art then b.parts[ #b.parts + 1 ] = b.art end
	b.parts[ #b.parts + 1 ] = b.core
	return b
end

local function BuildLadder( menu, HudRef, InstanceRef, left, xLo, xHi, RARITY )
	local L = { rungs = {} }
	local x0, x1
	if left then
		x1 = xLo - LAD_GAP
		x0 = x1 - LAD_W
	else
		x0 = xHi + LAD_GAP
		x1 = x0 + LAD_W
	end
	L.layer = Layer( menu )
	L.layer:setAlpha( 0 )
	local crest = Art().crest
	for r = 1, 4 do
		local cy = LAD_Y1 - ( r - 1 ) * LAD_PITCH - LAD_GEM / 2
		local gx0 = left and ( x1 - LAD_GEM ) or x0
		local g = { gx0 = gx0, cy = cy }
		if crest then
			g.gem = Img( L.layer, crest[ r ], gx0, cy - LAD_GEM / 2, gx0 + LAD_GEM, cy + LAD_GEM / 2, 1 )
			g.crest = true
		elseif FX( "gem" ) then
			g.gem = Img( L.layer, FX( "gem" ), gx0, cy - LAD_GEM / 2, gx0 + LAD_GEM, cy + LAD_GEM / 2, 1 )
		else
			g.gem = Panel( L.layer, HudRef, InstanceRef, gx0, cy - LAD_GEM / 2, gx0 + LAD_GEM, cy + LAD_GEM / 2, RARITY[ r ].col, 1 )
		end
		g.row = Row( L.layer, 12 )
		g.label = RARITY[ r ].tag .. " +" .. RARITY[ r ].lv
		if g.row then
			local picker = Pick
			local w = g.row.measure( g.label, LAD_CAP, picker )
			if w and w >= 0 then
				local base = cy + LAD_CAP / 2
				if left then
					g.row.set( g.label, LAD_CAP, gx0 - 7, base, picker )
				else
					g.row.set( g.label, LAD_CAP, gx0 + LAD_GEM + 7 + w, base, picker )
				end
			end
		end
		L.rungs[ r ] = g
	end
	return L
end

-- CARD V2 layers (only when the body + the four frames are installed): the
-- illustration, the body, the rarity frame, the crest and the live title +
-- lines. Lives in card.group so it takes every alpha the card takes.
local function BuildFace2( menu, xLo, y0 )
	local A = Art()
	if not ( A.body and A.frame ) then
		return nil
	end
	local f = { xLo = xLo, y0 = y0 }
	f.layer = Layer( menu )
	local function R( r )
		return xLo + r[ 1 ], y0 + r[ 2 ], xLo + r[ 3 ], y0 + r[ 4 ]
	end
	local ax0, ay0, ax1, ay1 = R( V2.art )
	f.art = Img( f.layer, nil, ax0, ay0, ax1, ay1, 0 )
	f.body = Img( f.layer, A.body, xLo, y0, xLo + 234, y0 + 351, 0 )
	f.frame = Img( f.layer, nil, xLo, y0, xLo + 234, y0 + 351, 0 )
	f.frames = {}
	for r = 1, 4 do
		f.frames[ r ] = RegisterImage( A.frame[ r ] )
	end
	local cx0, cy0, cx1, cy1 = R( V2.crest )
	f.crest = Img( f.layer, nil, cx0, cy0, cx1, cy1, 0 )
	f.crests = {}
	if A.crest then
		for r = 1, 4 do
			f.crests[ r ] = RegisterImage( A.crest[ r ] )
		end
	end
	local lx0, ly0, lx1, ly1 = R( V2.titleLabel )
	f.titleLabel = Img( f.layer, FX( "pill" ), lx0, ly0, lx1, ly1, 0 )   -- no pill art: a flat dark quad
	f.text = Layer( f.layer )
	f.title = Row( f.text, 20 )
	f.line1 = Row( f.text, 30 )
	f.line2 = Row( f.text, 30 )
	-- what squashes open on the flip: every image layer, each from the card's spine
	f.opens = {
		{ e = f.art,   r = { ax0, ay0, ax1, ay1 } },
		{ e = f.body,  r = { xLo, y0, xLo + 234, y0 + 351 } },
		{ e = f.frame, r = { xLo, y0, xLo + 234, y0 + 351 } },
		{ e = f.crest, r = { cx0, cy0, cx1, cy1 } },
		{ e = f.titleLabel, r = { lx0, ly0, lx1, ly1 } },
	}
	return f
end

-- the band + pips: over the baked band/pips of an old card, or in the v2
-- card's own slots. Lives in card.group (card alpha, focus dim, lock tint).
local function BuildFace( menu, HudRef, InstanceRef, xLo, y0 )
	local f = { xLo = xLo, y0 = y0 }
	f.layer = Layer( menu )
	f.bandRim = Panel( f.layer, HudRef, InstanceRef, xLo + BAND_X0, y0 + BAND_Y0, xLo + BAND_X1, y0 + BAND_Y1, { 0.02, 0.03, 0.08 }, 0 )
	if FX( "pill" ) then
		f.band = Img( f.layer, FX( "pill" ), xLo + BAND_X0 + 2, y0 + BAND_Y0 + 2, xLo + BAND_X1 - 2, y0 + BAND_Y1 - 2, 0 )
	else
		f.band = Panel( f.layer, HudRef, InstanceRef, xLo + BAND_X0 + 2, y0 + BAND_Y0 + 2, xLo + BAND_X1 - 2, y0 + BAND_Y1 - 2, { 1, 1, 1 }, 0 )
	end
	f.bandText = Layer( f.layer )
	f.bandRow  = Row( f.bandText, 14 )
	f.pipCover = Panel( f.layer, HudRef, InstanceRef, xLo + PIPS_X0, y0 + PIPS_Y0, xLo + PIPS_X1, y0 + PIPS_Y1, { 0.035, 0.05, 0.12 }, 0 )
	f.pips = {}
	for i = 1, PIP_MAX do
		if FX( "pip" ) then
			f.pips[ i ] = Img( f.layer, FX( "pip" ), 0, 0, PIP_S, PIP_S, 0 )
		else
			f.pips[ i ] = Panel( f.layer, HudRef, InstanceRef, 0, 0, PIP_S, PIP_S, { 1, 1, 1 }, 0 )
		end
	end
	f.ticker = Panel( f.layer, HudRef, InstanceRef, 0, 0, 1, 1, { 0, 0, 0 }, 0 )
	return f
end

-- AFTER the cards. cards = { a = CardA, b = CardB }; each carries xLo/xHi and a
-- .group table the face layers join. opts: RARITY, DOMAIN, TIER_DOMAIN,
-- TIER_LADDER, TCLS, y0, y1.
function P.Attach( menu, HudRef, InstanceRef, under, cards, opts )
	local pull = { under = under, opts = opts, slot = {} }
	local RARITY = opts.RARITY
	for key, card in pairs( cards ) do
		local s = { card = card, key = key, under = under.slot and under.slot[ key ] or nil }
		s.back = BuildBack( menu, HudRef, InstanceRef, card.xLo, card.xHi, opts.y0, opts.y1 )
		s.ladder = BuildLadder( menu, HudRef, InstanceRef, key == "a", card.xLo, card.xHi, RARITY )
		s.face2 = BuildFace2( menu, card.xLo, opts.y0 )
		if s.face2 then
			card.group[ #card.group + 1 ] = s.face2.layer
			card.todFace2 = s.face2.layer   -- tod_upgrade.lua tints it for a locked tier card
		end
		s.face = BuildFace( menu, HudRef, InstanceRef, card.xLo, opts.y0 )
		card.group[ #card.group + 1 ] = s.face.layer
		card.todFace = s.face.layer   -- the band + pips: tod_upgrade.lua tones it with the v2 layers
		-- THE REACH (docs/201): the colour that climbs the back, and the flicker over the next ladder gem
		if FX( "glow" ) then
			s.reachFill = Img( menu, FX( "glow" ), card.xLo + 6, opts.y1 - 8, card.xHi - 6, opts.y1 - 4, 0 )
			s.reachGem = Img( menu, FX( "glow" ), 0, 0, 10, 10, 0 )
		else
			s.reachFill = Panel( menu, HudRef, InstanceRef, card.xLo + 6, opts.y1 - 8, card.xHi - 6, opts.y1 - 4, { 1, 1, 1 }, 0 )
			s.reachGem = Panel( menu, HudRef, InstanceRef, 0, 0, 10, 10, { 1, 1, 1 }, 0 )
		end
		-- THE HOT STREAK (docs/201): the embers rising off a warm back - over it, where they can be seen
		s.embers = {}
		for i = 1, EMBERS_N do
			if FX( "pip" ) then
				s.embers[ i ] = Img( menu, FX( "pip" ), 0, 0, 5, 5, 0 )
			else
				s.embers[ i ] = Panel( menu, HudRef, InstanceRef, 0, 0, 4, 4, HEAT_RGB, 0 )
			end
		end
		pull.slot[ key ] = s
	end

	-- shared, on top of everything: shards, the ring, the banner, the flash
	pull.shards = {}
	for i = 1, SHARD_POOL do
		if FX( "shard" ) then
			pull.shards[ i ] = Img( menu, FX( "shard" ), 0, 0, 16, 16, 0 )
		else
			pull.shards[ i ] = Panel( menu, HudRef, InstanceRef, 0, 0, 8, 8, { 1, 1, 1 }, 0 )
		end
	end
	if FX( "ring" ) then
		pull.ring = Img( menu, FX( "ring" ), 0, 0, 10, 10, 0 )
	end
	pull.banner = Layer( menu )
	pull.banner:setAlpha( 0 )
	if Art().banner then
		pull.bannerImg = Img( pull.banner, Art().banner, 0, 0, 10, 10, 1 )
	else
		pull.bannerBg = Panel( pull.banner, HudRef, InstanceRef, 0, 0, 10, 10, { 0, 0, 0 }, 0.72 )
		pull.bannerRule = Panel( pull.banner, HudRef, InstanceRef, 0, 0, 10, 10, { 1, 1, 1 }, 1 )
	end
	pull.bigRow = Row( pull.banner, 10 )
	pull.smallRow = Row( pull.banner, 10 )
	if FX( "flash" ) then
		pull.flash = Img( menu, FX( "flash" ), 0, 0, 10, 10, 0 )
	else
		pull.flash = Panel( menu, HudRef, InstanceRef, 0, 0, 1280, 720, { 1, 1, 1 }, 0 )
	end

	-- ---- chains (transition_complete, the TodHealthTint idiom) -------------
	for _, s in pairs( pull.slot ) do
		local slot = s
		slot.back.beat:registerEventHandler( "transition_complete_tod_pull_beat", function ( element, event )
			P.BeatBack( slot )
		end )
		-- THE REACH's two chains: the strain's tremble, the next gem's flicker
		slot.back.beat:registerEventHandler( "transition_complete_tod_pull_tremble", function ( element, event )
			P.Tremble( slot, event )
		end )
		slot.reachGem:registerEventHandler( "transition_complete_tod_pull_reach_flick", function ( element, event )
			P.ReachFlick( slot, event )
		end )
		for i = 1, #slot.embers do
			local k = i
			slot.embers[ i ]:registerEventHandler( "transition_complete_tod_pull_ember", function ( element, event )
				P.EmberStep( slot, k, event )
			end )
		end
		slot.face.ticker:registerEventHandler( "transition_complete_tod_pull_pip", function ( element, event )
			if event and event.interrupted then
				P.PipsFinish( slot )
			else
				P.PipNext( slot )
			end
		end )
		if slot.face2 then
			slot.face2.body:registerEventHandler( "transition_complete_tod_pull_open", function ( element, event )
				P.Face2Text( pull, slot, true )
			end )
		end
		local us = slot.under
		if us and us.rays then
			us.rays:registerEventHandler( "transition_complete_tod_pull_rays", function ( element, event )
				P.RaysStep( slot )
			end )
		end
		if us and us.motes then
			for i = 1, #us.motes do
				local k = i
				us.motes[ i ]:registerEventHandler( "transition_complete_tod_pull_mote", function ( element, event )
					P.MoteStep( slot, k )
				end )
			end
		end
	end
	pull.banner:registerEventHandler( "transition_complete_tod_pull_bn_in", function ( element, event )
		if event and event.interrupted then
			P.BannerOff( pull )
			return
		end
		pull.banner:beginAnimation( "tod_pull_bn_hold", pull.bannerHold or 500, false, false, CoD.TweenType.Linear )
		pull.banner:setAlpha( 1 )
	end )
	pull.banner:registerEventHandler( "transition_complete_tod_pull_bn_hold", function ( element, event )
		if event and event.interrupted then
			P.BannerOff( pull )
			return
		end
		pull.banner:beginAnimation( "tod_pull_bn_out", BANNER_OUT, false, false, CoD.TweenType.Linear )
		pull.banner:setAlpha( 0 )
	end )

	P.Reset( pull, true )
	P.last = pull   -- the newest instance; read by tools/test_card_pull.lua only
	return pull
end

-- =============================================================================
-- CARD V2 - does this card draw as layers?
-- =============================================================================
local function TierOf( cur )
	return math.floor( cur / 2 ) + 1, ( cur % 2 ) + 2
end

-- CARD V2 IS PER CLASS. A layered card fills its whole canvas and an old baked
-- face sits 50 px in, so one deal must never mix them: a class draws its cards as
-- layered cards only when tools/card_pull/install_card_art.py lists it in
-- CoD.TodCardArt.classes (EVERY card it can be dealt has its art). CoD.TodClass is
-- pushed at the draft and before every deal (_tod_upgrades push_panel_hints).
function P.ClassV2( pull )
	local A = Art()
	local key = pull and pull.opts and pull.opts.TCLS and pull.opts.TCLS[ CoD.TodClass or 0 ]
	return key ~= nil and A.classes ~= nil and A.classes[ key ] == true
end

-- the illustration for this card, or nil (then the old baked card is drawn)
function P.V2Art( pull, dom, cur )
	local A = Art()
	if not ( pull and pull.slot and pull.slot.a and pull.slot.a.face2 ) then
		return nil
	end
	if not P.ClassV2( pull ) then
		return nil
	end
	if dom == pull.opts.TIER_DOMAIN then
		local cls, tier = TierOf( cur or 0 )
		local key = pull.opts.TCLS and pull.opts.TCLS[ cls ]
		local t = key and A.tier and A.tier[ key ]
		return t and t[ tier ] or nil
	end
	return A.art and A.art[ dom ] or nil
end

function P.UsesV2( pull, dom, cur )
	return P.V2Art( pull, dom, cur ) ~= nil
end

-- =============================================================================
-- STATES
-- =============================================================================

-- the back that matches the faces this player will see (see BuildBack)
local function BackPick( pull, s )
	local b = s.back
	if not b.art then
		return
	end
	local want = ( P.ClassV2( pull ) and b.artV2 ) or b.artOld or b.artV2
	if want and want ~= b.artNow then
		b.art:setImage( RegisterImage( want ) )
		b.artNow = want
	end
end

local function BackShow( s, on )
	local b = s.back
	local a = on and 1 or 0
	for _, e in ipairs( b.parts ) do
		e:completeAnimation()
	end
	if b.rim then
		b.rim:setLeftRight( true, false, b.xLo, b.xHi )
		b.rim:setTopBottom( true, false, b.y0, b.y1 )
		b.rim:setAlpha( a )
		b.fill:setLeftRight( true, false, b.xLo + 5, b.xHi - 5 )
		b.fill:setAlpha( a )
	end
	if b.art then
		b.art:setLeftRight( true, false, b.xLo, b.xHi )
		b.art:setTopBottom( true, false, b.y0, b.y1 )
		b.art:setAlpha( a )
	end
	if b.core.Bg then
		b.core:setLeftRight( true, false, b.xLo + 28, b.xHi - 28 )
	else
		b.core:setLeftRight( true, false, b.xLo + 10, b.xHi - 10 )
	end
	b.core:setAlpha( 0 )
	for i = 1, #b.sigil do
		b.sigil[ i ]:setAlpha( on and 0.55 or 0 )
	end
	b.sweep:completeAnimation()
	b.sweep:setAlpha( 0 )
end

-- the back wears rung `r` (1..4); r == 0 = a DIM STEEL neutral before its climb,
-- deliberately NOT the COMMON white (docs/187: an unclimbed back that looked
-- white read as "stayed common")
local NEUTRAL = { 0.30, 0.31, 0.40 }
local function BackTint( s, r, RARITY )
	local b = s.back
	local col = ( r >= 1 ) and RARITY[ r ].col or NEUTRAL
	if b.rim then
		b.rim.Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
	end
	Tint( b.core, col )
	for i = 1, #b.sigil do
		b.sigil[ i ].Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
		b.sigil[ i ]:setAlpha( ( r >= 1 ) and 0.9 or 0.55 )
	end
	-- over the painted card back the glow stays a quarter lighter, so the art reads
	-- through the charge (render_pull: at 0.66 the LEGENDARY gold washed the spire out)
	b.core:setAlpha( ( r >= 1 ) and ( BACK_CORE_A[ r ] * ( b.art and 0.72 or 1 ) ) or 0 )
	-- the halo around the card follows the climb too
	local us = s.under
	if us and us.glow then
		Tint( us.glow, col )
		us.glow:setAlpha( ( r >= 1 ) and ( 0.25 + 0.18 * r ) or 0 )
	end
end

local function LadderPaint( s, lit, won, RARITY )
	for r = 1, 4 do
		local g = s.ladder.rungs[ r ]
		local col = RARITY[ r ].col
		local on = ( r <= lit )
		if g.crest then
			g.gem:setRGB( on and 1 or 0.32, on and 1 or 0.32, on and 1 or 0.38 )
			g.gem:setAlpha( on and 1 or 0.55 )
		elseif g.gem.Bg then
			g.gem.Bg:setRGB( on and col[ 1 ] or 0.08, on and col[ 2 ] or 0.08, on and col[ 3 ] or 0.12 )
			g.gem:setAlpha( on and 1 or 0.6 )
		else
			local c = on and col or Dim( col, 0.28 )
			g.gem:setRGB( c[ 1 ], c[ 2 ], c[ 3 ] )
			g.gem:setAlpha( on and 1 or 0.7 )
		end
		if g.row then
			local c = on and col or Dim( col, 0.32 )
			g.row.setRGB( c[ 1 ], c[ 2 ], c[ 3 ] )
		end
		-- the rung the card STOPPED on stands proud
		local grow = ( r == won ) and 4 or 0
		g.gem:setLeftRight( true, false, g.gx0 - grow, g.gx0 + LAD_GEM + grow )
		g.gem:setTopBottom( true, false, g.cy - LAD_GEM / 2 - grow, g.cy + LAD_GEM / 2 + grow )
	end
end

local function Edges( pull, col, a )
	local u = pull.under
	if u.edge then
		u.edge:completeAnimation()
		if col then u.edge:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] ) end
		u.edge:setAlpha( a )
		return
	end
	for i = 1, #u.edges do
		local e = u.edges[ i ]
		e:completeAnimation()
		if col then e.Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] ) end
		e:setAlpha( a * 0.5 )
	end
end

local function DimTo( pull, a, ms )
	local d = pull.under.dim
	d:completeAnimation()
	if ms and ms > 0 then
		d:beginAnimation( "tod_pull_dim", ms, false, false, CoD.TweenType.Linear )
	end
	d:setAlpha( a )
end

local function FaceHide( s )
	local f = s.face
	f.bandRim:setAlpha( 0 )
	f.band:setAlpha( 0 )
	f.bandText:setAlpha( 0 )
	f.pipCover:setAlpha( 0 )
	for i = 1, PIP_MAX do
		f.pips[ i ]:setAlpha( 0 )
	end
	f.ticker:completeAnimation()
	s.pipsPending = nil
	local f2 = s.face2
	if f2 then
		for _, o in ipairs( f2.opens ) do
			o.e:completeAnimation()
			o.e:setAlpha( 0 )
		end
		f2.text:setAlpha( 0 )
		s.v2 = false
	end
end

function P.BannerOff( pull )
	pull.banner:completeAnimation()
	pull.banner:setAlpha( 0 )
end

-- the god rays + motes behind a card (EPIC and LEGENDARY)
local function AuraStop( s )
	local us = s.under
	s.raysOn = false
	s.motesOn = false
	if not us then return end
	if us.rays then
		us.rays:completeAnimation()
		us.rays:setAlpha( 0 )
	end
	for i = 1, #us.motes do
		us.motes[ i ]:completeAnimation()
		us.motes[ i ]:setAlpha( 0 )
	end
	if us.glow then
		us.glow:setAlpha( 0 )
	end
end

-- THE HOT STREAK: a warm back's embers, gone (the flip, a reset). warm drops FIRST, so an ember's completion
-- handler that fires here never re-launches it.
local function EmbersOff( s )
	s.warm = false
	for i = 1, #( s.embers or {} ) do
		s.embers[ i ]:completeAnimation()
		s.embers[ i ]:setAlpha( 0 )
	end
end

-- everything back to rest; `hard` also clears the per-deal latches
function P.Reset( pull, hard )
	for _, s in pairs( pull.slot ) do
		BackShow( s, false )
		s.ladder.layer:setAlpha( 0 )
		FaceHide( s )
		AuraStop( s )
		P.ReachClear( s )
		EmbersOff( s )
		s.started, s.rung, s.d, s.faceKey, s.rar = false, 0, 0, nil, 0
		s.beatsHere = 0
	end
	for i = 1, SHARD_POOL do
		pull.shards[ i ]:completeAnimation()
		pull.shards[ i ]:setAlpha( 0 )
	end
	if pull.ring then
		pull.ring:completeAnimation()
		pull.ring:setAlpha( 0 )
	end
	P.BannerOff( pull )
	pull.flash:completeAnimation()
	pull.flash:setAlpha( 0 )
	Edges( pull, nil, 0 )
	DimTo( pull, 0, 0 )
	pull.hold = 0
	pull.wasRev = false
end

-- ---- the beats --------------------------------------------------------------

function P.BeatBack( s )
	local b = s.back
	if s.beatOut then
		s.beatOut = false
		b.beat:beginAnimation( "tod_pull_beat_in", BEAT_MS, false, false, CoD.TweenType.Linear )
		b.beat:setLeftRight( true, false, b.xLo, b.xHi )
		b.beat:setTopBottom( true, false, b.y0, b.y1 )
	end
end

local function Beat( s )
	local b = s.back
	b.beat:completeAnimation()
	s.beatOut = true
	b.beat:beginAnimation( "tod_pull_beat", BEAT_MS, false, false, CoD.TweenType.Linear )
	b.beat:setLeftRight( true, false, b.xLo - BEAT_GROW, b.xHi + BEAT_GROW )
	b.beat:setTopBottom( true, false, b.y0 - BEAT_GROW, b.y1 + BEAT_GROW )
end

-- ---- THE REACH (docs/201 section 4) ---------------------------------------------
-- the back's art (or rim) to its rest rect, offset by dx / dy
local function BackAt( b, dx, dy )
	b.beat:setLeftRight( true, false, b.xLo + dx, b.xHi + dx )
	b.beat:setTopBottom( true, false, b.y0 + dy, b.y1 + dy )
end

-- everything the reach drew, gone at once (a flip that arrives while still reaching, a reset)
function P.ReachClear( s )
	s.reaching = false
	s.trembleN = 0
	if s.reachFill then
		s.reachFill:completeAnimation()
		s.reachFill:setAlpha( 0 )
	end
	if s.reachGem then
		s.reachGem:completeAnimation()
		s.reachGem:setAlpha( 0 )
	end
end

-- the card STRAINS for the next rung: its gem flickers in that rung's colour, the colour climbs two thirds up the
-- back and holds, the room leans toward it, the card lifts and trembles. The next edge resolves it.
local function Reach( pull, s )
	local RARITY = pull.opts.RARITY
	local nxt = math.min( 4, ( s.rung or 1 ) + 1 )
	local col = RARITY[ nxt ].col
	local b = s.back
	s.reaching = true
	local g = s.ladder.rungs[ nxt ]
	if s.reachGem and g then
		local e = s.reachGem
		e:completeAnimation()
		Tint( e, col )
		e:setLeftRight( true, false, g.gx0 - 10, g.gx0 + LAD_GEM + 10 )
		e:setTopBottom( true, false, g.cy - LAD_GEM / 2 - 10, g.cy + LAD_GEM / 2 + 10 )
		s.reachFlick = 0
		e:setAlpha( 0.25 )
		e:beginAnimation( "tod_pull_reach_flick", REACH_FLICK_MS, false, false, CoD.TweenType.Linear )
		e:setAlpha( 0.85 )
	end
	if s.reachFill then
		local e = s.reachFill
		e:completeAnimation()
		Tint( e, col )
		e:setLeftRight( true, false, b.xLo + 6, b.xHi - 6 )
		e:setTopBottom( true, false, b.y1 - 8, b.y1 - 4 )
		e:setAlpha( REACH_FILL_A )
		e:beginAnimation( "tod_pull_reach_rise", REACH_RISE_MS, false, false, CoD.TweenType.Linear )
		e:setTopBottom( true, false, b.y1 - ( b.y1 - b.y0 ) * 0.66, b.y1 - 4 )
	end
	Edges( pull, col, ( EDGE_A[ nxt ] or 0 ) * 0.6 + 0.12 )
	s.trembleN = TREMBLE_STEPS
	b.beat:completeAnimation()
	b.beat:beginAnimation( "tod_pull_tremble", TREMBLE_MS, false, false, CoD.TweenType.Linear )
	BackAt( b, -TREMBLE_PX, -REACH_LIFT )
end

-- the strain's tremble: +-TREMBLE_PX while it lasts, then it holds lifted (until the reach resolves)
function P.Tremble( s, event )
	if ( event and event.interrupted ) or not s.reaching or ( s.trembleN or 0 ) <= 0 then
		return
	end
	s.trembleN = s.trembleN - 1
	local off = ( s.trembleN % 2 == 0 ) and TREMBLE_PX or -TREMBLE_PX
	if s.trembleN == 0 then
		off = 0
	end
	s.back.beat:beginAnimation( "tod_pull_tremble", TREMBLE_MS, false, false, CoD.TweenType.Linear )
	BackAt( s.back, off, -REACH_LIFT )
end

-- the next gem's flicker: it tries to light, REACH_FLICKS times, then glows on half-lit while the reach holds
function P.ReachFlick( s, event )
	if ( event and event.interrupted ) or not s.reaching or not s.reachGem then
		return
	end
	s.reachFlick = ( s.reachFlick or 0 ) + 1
	if s.reachFlick > REACH_FLICKS then
		s.reachGem:setAlpha( 0.6 )
		return
	end
	s.reachGem:beginAnimation( "tod_pull_reach_flick", REACH_FLICK_MS, false, false, CoD.TweenType.Linear )
	s.reachGem:setAlpha( ( s.reachFlick % 2 == 1 ) and 0.3 or 0.9 )
end

-- SO CLOSE: the fill drains, the flicker dies, the room falls back to the rung it reached, the card sinks back
local function Deflate( pull, s )
	local b = s.back
	s.reaching = false
	s.trembleN = 0
	if s.reachGem then
		s.reachGem:completeAnimation()
		s.reachGem:beginAnimation( "tod_pull_reach_out", REACH_GEM_OUT, false, false, CoD.TweenType.Linear )
		s.reachGem:setAlpha( 0 )
	end
	if s.reachFill then
		s.reachFill:completeAnimation()
		s.reachFill:beginAnimation( "tod_pull_reach_drain", REACH_DRAIN_MS, false, false, CoD.TweenType.Linear )
		s.reachFill:setTopBottom( true, false, b.y1 - 8, b.y1 - 4 )
		s.reachFill:setAlpha( 0 )
	end
	local r = math.max( 1, s.rung or 1 )
	Edges( pull, pull.opts.RARITY[ r ].col, EDGE_A[ r ] or 0 )
	b.beat:completeAnimation()
	BackAt( b, 0, REACH_SINK )
	b.beat:beginAnimation( "tod_pull_sink", REACH_SINK_MS, false, false, CoD.TweenType.Bounce )
	BackAt( b, 0, 0 )
end

-- BREAK THROUGH (before the climb it resolves into): the colour fills the whole back and bursts, a quick ring
-- snaps off the card, the card drops back to rest - and Climb takes it to the new rung
local function BreakThrough( pull, s, r )
	local col = pull.opts.RARITY[ r ].col
	local b = s.back
	s.reaching = false
	s.trembleN = 0
	if s.reachGem then
		s.reachGem:completeAnimation()
		s.reachGem:setAlpha( 0 )
	end
	if s.reachFill then
		local e = s.reachFill
		e:completeAnimation()
		Tint( e, col )
		e:setTopBottom( true, false, b.y0 + 4, b.y1 - 4 )
		e:setAlpha( 0.9 )
		e:beginAnimation( "tod_pull_reach_burst", BREAK_MS, false, false, CoD.TweenType.Linear )
		e:setAlpha( 0 )
	end
	if pull.ring then
		local cx = ( b.xLo + b.xHi ) / 2
		local cy = ( b.y0 + b.y1 ) / 2
		local e = pull.ring
		e:completeAnimation()
		Tint( e, col )
		e:setLeftRight( true, false, cx - 40, cx + 40 )
		e:setTopBottom( true, false, cy - 40, cy + 40 )
		e:setAlpha( 1 )
		e:beginAnimation( "tod_pull_break_ring", BREAK_RING, false, false, CoD.TweenType.Linear )
		e:setLeftRight( true, false, cx - 200, cx + 200 )
		e:setTopBottom( true, false, cy - 200, cy + 200 )
		e:setAlpha( 0 )
	end
	b.beat:completeAnimation()
	BackAt( b, 0, 0 )
end

-- THE HOT STREAK (docs/201 section 5): the backs arrive WARM - an orange halo and 2 / 4 / 6 embers rising off them
-- by heat - until the climb takes the halo and the flip ends the embers
local function Warm( pull, s, heat )
	local us = s.under
	EmbersOff( s )
	heat = math.min( 3, tonumber( heat ) or 0 )
	if heat <= 0 then
		return
	end
	s.warm = true
	if us and us.glow then
		Tint( us.glow, HEAT_RGB )
		us.glow:setAlpha( 0.22 + 0.08 * heat )
	end
	local n = math.min( #s.embers, 2 * heat )
	for i = 1, #s.embers do
		Tint( s.embers[ i ], HEAT_RGB )
		if i <= n then
			P.EmberStep( s, i )
		end
	end
end

-- climb to rarity r (1..4): the back takes the rung's colour, a light sweeps
-- across it, the ladder lights the rung, and the room reacts at EPIC and above
local function Climb( pull, s, r )
	local RARITY = pull.opts.RARITY
	s.rung = r
	s.beatsHere = 0   -- THE REACH counts the beats at each rung (docs/201)
	BackTint( s, r, RARITY )
	LadderPaint( s, r, 0, RARITY )
	local b = s.back
	b.sweep:completeAnimation()
	Tint( b.sweep, { 1, 1, 1 } )
	b.sweep:setLeftRight( true, false, b.xLo, b.xLo + 40 )
	b.sweep:setAlpha( 0.7 )
	b.sweep:beginAnimation( "tod_pull_sweep", 85, false, false, CoD.TweenType.Linear )
	b.sweep:setLeftRight( true, false, b.xHi - 40, b.xHi )
	b.sweep:setAlpha( 0 )
	if r >= 3 then
		Edges( pull, RARITY[ r ].col, EDGE_A[ r ] )
	end
	if r >= 4 then
		DimTo( pull, DIM_LEG, 80 )
	end
end

-- ---- the god rays + motes (after the flip, EPIC and LEGENDARY) ---------------
function P.RaysStep( s )
	local us = s.under
	if not ( s.raysOn and us and us.rays ) then return end
	us.rays:setZRot( 0 )
	us.rays:beginAnimation( "tod_pull_rays", RAYS_MS[ s.rar ] or 3000, false, false, CoD.TweenType.Linear )
	us.rays:setZRot( RAYS_PERIOD )
	us.rays:setAlpha( RAYS_STEADY[ s.rar ] or 0.3 )   -- the first turn fades the burst down to the steady glow
end

-- a fixed scatter (no random number source: none has run in this map's menu Lua)
local MOTE_T = { 0.13, 0.71, 0.42, 0.88, 0.27, 0.59, 0.05, 0.94, 0.36, 0.66, 0.18, 0.81, 0.49, 0.23, 0.77 }
local function Jit( s )
	s.moteN = ( ( s.moteN or 0 ) % #MOTE_T ) + 1
	return MOTE_T[ s.moteN ]
end

function P.MoteStep( s, i )
	local us = s.under
	if not ( s.motesOn and us and us.motes[ i ] ) then return end
	local e = us.motes[ i ]
	local x = us.xLo + 20 + Jit( s ) * ( us.xHi - us.xLo - 40 )
	local y = us.y1 - 30 - Jit( s ) * 90
	local sz = 3 + Jit( s ) * 3
	e:setLeftRight( true, false, x, x + sz )
	e:setTopBottom( true, false, y, y + sz )
	e:setAlpha( 0.9 )
	e:beginAnimation( "tod_pull_mote", MOTE_MS * ( 0.7 + Jit( s ) * 0.6 ), false, false, CoD.TweenType.Linear )
	e:setTopBottom( true, false, y - 150, y - 150 + sz )
	e:setAlpha( 0 )
end

-- THE HOT STREAK (docs/201): one ember over a warm back - it rises from the back's lower half, drifting a little and
-- fading, and its completion launches the next one while the back stays warm
function P.EmberStep( s, i, event )
	if ( event and event.interrupted ) or not s.warm or not s.embers or not s.embers[ i ] then
		return
	end
	local e = s.embers[ i ]
	local b = s.back
	local x = b.xLo + 14 + Jit( s ) * ( b.xHi - b.xLo - 28 )
	local y = b.y1 - 40 - Jit( s ) * ( ( b.y1 - b.y0 ) * 0.4 )
	local dx = ( Jit( s ) - 0.5 ) * EMBER_DRIFT
	local sz = 3 + Jit( s ) * 3
	e:setLeftRight( true, false, x, x + sz )
	e:setTopBottom( true, false, y, y + sz )
	e:setAlpha( EMBER_A )
	e:beginAnimation( "tod_pull_ember", math.floor( EMBER_MS * ( 0.7 + Jit( s ) * 0.6 ) ), false, false, CoD.TweenType.Linear )
	e:setLeftRight( true, false, x + dx, x + dx + sz )
	e:setTopBottom( true, false, y - EMBER_RISE, y - EMBER_RISE + sz )
	e:setAlpha( 0 )
end

local function AuraStart( pull, s, rar )
	local us = s.under
	local col = pull.opts.RARITY[ rar ].col
	s.rar = rar
	if not us then return end
	if us.glow then
		Tint( us.glow, col )
		us.glow:setAlpha( 0.35 + 0.15 * rar )
	end
	if us.rays and ( RAYS_A[ rar ] or 0 ) > 0 then
		local h = RAYS_SIZE[ rar ] / 2
		us.rays:completeAnimation()
		Tint( us.rays, col )
		us.rays:setLeftRight( true, false, us.cx - h, us.cx + h )
		us.rays:setTopBottom( true, false, us.cy - h, us.cy + h )
		us.rays:setAlpha( RAYS_A[ rar ] )
		s.raysOn = true
		P.RaysStep( s )
	end
	if rar >= 4 and #us.motes > 0 then
		s.motesOn = true
		for i = 1, #us.motes do
			Tint( us.motes[ i ], col )
			P.MoteStep( s, i )
		end
	end
end

-- ---- the pips ----------------------------------------------------------------
local function PipsLayout( s, rect, max, cur, gain, col )
	local f = s.face
	if max > PIP_MAX then max = PIP_MAX end
	local w = max * PIP_S + ( max - 1 ) * PIP_GAP
	local cx = f.xLo + ( rect[ 1 ] + rect[ 3 ] ) / 2
	local cy = f.y0 + ( rect[ 2 ] + rect[ 4 ] ) / 2
	local x = cx - w / 2
	s.pipMax, s.pipCur, s.pipGain, s.pipCol, s.pipLit = max, cur, gain, col, 0
	s.pipX, s.pipCy = x, cy
	for i = 1, PIP_MAX do
		local e = f.pips[ i ]
		e:completeAnimation()
		if i <= max then
			local px = x + ( i - 1 ) * ( PIP_S + PIP_GAP )
			e:setLeftRight( true, false, px, px + PIP_S )
			e:setTopBottom( true, false, cy - PIP_S / 2, cy + PIP_S / 2 )
			-- RT 2026-10-05: an unlit pip is the theme's dim steel (synthwave navy 0.14 / 0.17 / 0.30; r3 CODE_TINTS pins it)
			Tint( e, ( i <= cur ) and { 0.80, 0.84, 0.94 } or { 0.20, 0.21, 0.26 } )
			e:setAlpha( 1 )
		else
			e:setAlpha( 0 )
		end
	end
end

local function PipLight( s, i, grow )
	local e = s.face.pips[ i ]
	if not e then return end
	Tint( e, s.pipCol )
	e:setAlpha( 1 )
	e:completeAnimation()
	local x0 = s.pipX + ( i - 1 ) * ( PIP_S + PIP_GAP )
	if grow then
		e:setLeftRight( true, false, x0 - 4, x0 + PIP_S + 4 )
		e:setTopBottom( true, false, s.pipCy - PIP_S / 2 - 4, s.pipCy + PIP_S / 2 + 4 )
		e:beginAnimation( "tod_pull_pip_pop", 90, false, false, CoD.TweenType.Linear )
	end
	e:setLeftRight( true, false, x0, x0 + PIP_S )
	e:setTopBottom( true, false, s.pipCy - PIP_S / 2, s.pipCy + PIP_S / 2 )
end

function P.PipNext( s )
	if not s.pipsPending then return end
	s.pipLit = s.pipLit + 1
	local i = s.pipCur + s.pipLit
	if s.pipLit > s.pipGain or i > s.pipMax then
		s.pipsPending = nil
		return
	end
	PipLight( s, i, true )
	if s.pipLit < s.pipGain and i < s.pipMax then
		s.face.ticker:beginAnimation( "tod_pull_pip", PIP_TICK_MS, false, false, CoD.TweenType.Linear )
		s.face.ticker:setAlpha( 0 )
	else
		s.pipsPending = nil
	end
end

function P.PipsFinish( s )
	if not s.pipsPending then return end
	for k = s.pipLit + 1, s.pipGain do
		local i = s.pipCur + k
		if i <= s.pipMax then
			PipLight( s, i, false )
		end
	end
	s.pipLit = s.pipGain
	s.pipsPending = nil
end

-- ---- card v2 -----------------------------------------------------------------
-- the two short lines under the picture: the DOMAIN row's `face` lines, else the
-- desc cleaned to the typeface and split in two
local function FaceLines( pull, dom, cur )
	local o = pull.opts
	if dom == o.TIER_DOMAIN then
		local cls, tier = TierOf( cur )
		local lad = o.TIER_LADDER and o.TIER_LADDER[ cls ]
		-- a promotion KEEPS every card (no live card is gun-scoped) and hands the new
		-- weapon back unpacked (_tod_classes pap_tier_forget): say both, never "reset"
		return { ( lad and lad[ tier ] ) or "NEW WEAPON", "CARDS KEPT - PACK IT AGAIN" }
	end
	local d = o.DOMAIN[ dom ]
	if d and d.face then
		return { d.face[ 1 ], d.face[ 2 ] }
	end
	local words = {}
	for w in string.gmatch( Clean( d and d.desc or "" ), "%S+" ) do
		words[ #words + 1 ] = w
	end
	local half = math.ceil( #words / 2 )
	return { table.concat( words, " ", 1, math.min( half, #words ) ), table.concat( words, " ", half + 1, #words ) }
end

local function TitleOf( pull, dom, cur )
	if dom == pull.opts.TIER_DOMAIN then
		local _, tier = TierOf( cur )
		return "TIER " .. tier
	end
	local d = pull.opts.DOMAIN[ dom ]
	return d and d.name or ""
end

function P.Face2Text( pull, s, on )
	local f2 = s.face2
	if not f2 then return end
	f2.text:setAlpha( on and 1 or 0 )
end

-- paint the layered card; `animate` = the flip (each layer opens from the spine)
local function Face2Paint( pull, s, dom, rar, cur, animate )
	local f2 = s.face2
	local art = P.V2Art( pull, dom, cur )
	s.v2 = true
	f2.art:setImage( RegisterImage( art ) )
	f2.frame:setImage( f2.frames[ rar ] or f2.frames[ 1 ] )
	if f2.crests[ rar ] then
		f2.crest:setImage( f2.crests[ rar ] )
	end
	-- live text: WHITE, on a dark shade of the rarity colour (TEXT_WHITE above)
	local R = pull.opts.RARITY[ rar ] or pull.opts.RARITY[ 1 ]
	Tint( f2.titleLabel, Dim( R.col, GROUND_DIM ) )
	local tx0, ty0, tx1, ty1 = f2.xLo + V2.titleLabel[ 1 ], f2.y0 + V2.titleLabel[ 2 ], f2.xLo + V2.titleLabel[ 3 ], f2.y0 + V2.titleLabel[ 4 ]
	if f2.title then
		f2.title.setRGB( TEXT_WHITE[ 1 ], TEXT_WHITE[ 2 ], TEXT_WHITE[ 3 ] )
		SetFit( f2.title, Clean( TitleOf( pull, dom, cur ) ), TITLE_CAP, ( tx0 + tx1 ) / 2, ( ty0 + ty1 ) / 2 + TITLE_CAP / 2, ( tx1 - tx0 ) - 18 )
	end
	local lines = FaceLines( pull, dom, cur )
	local lx0, ly0, lx1, ly1 = f2.xLo + V2.text[ 1 ], f2.y0 + V2.text[ 2 ], f2.xLo + V2.text[ 3 ], f2.y0 + V2.text[ 4 ]
	local lcx = ( lx0 + lx1 ) / 2
	local two = ( lines[ 2 ] and lines[ 2 ] ~= "" )
	local mid = ( ly0 + ly1 ) / 2
	-- the pair is centred on the panel: line 1 (white) over line 2 (a pale blue, 0.95 size)
	if f2.line1 then
		f2.line1.setRGB( TEXT_WHITE[ 1 ], TEXT_WHITE[ 2 ], TEXT_WHITE[ 3 ] )
		SetFit( f2.line1, Clean( lines[ 1 ] ), LINE_CAP, lcx, two and ( mid - 2.5 ) or ( mid + LINE_CAP / 2 ), ( lx1 - lx0 ) - 12 )
	end
	if f2.line2 then
		f2.line2.setRGB( 0.74, 0.80, 0.93 )
		if two then
			SetFit( f2.line2, Clean( lines[ 2 ] ), LINE_CAP * 0.95, lcx, mid + LINE_CAP * 0.95 + 4, ( lx1 - lx0 ) - 12 )
		else
			f2.line2.hide()
		end
	end
	-- the layers: open from the spine on the flip, or just be there
	local spine = f2.xLo + 117
	for _, o in ipairs( f2.opens ) do
		local e, r = o.e, o.r
		-- the crest matches the frame on EVERY card, the tier card too (its socket is
		-- painted into the body: hiding the crest left an empty dark hole)
		local show = ( e ~= f2.crest ) or ( f2.crests[ rar ] ~= nil )
		e:completeAnimation()
		if animate and show then
			-- squash to the spine; a short layer (the title label) never pinches past zero height
			local pinch = math.min( 20, ( r[ 4 ] - r[ 2 ] ) / 2 - 1 )
			e:setLeftRight( true, false, spine - 2, spine + 2 )
			e:setTopBottom( true, false, r[ 2 ] + pinch, r[ 4 ] - pinch )
			e:setAlpha( 1 )
			e:beginAnimation( "tod_pull_open", V2_OPEN_MS[ rar ] or 100, false, false, CoD.TweenType.Bounce )
		end
		e:setLeftRight( true, false, r[ 1 ], r[ 3 ] )
		e:setTopBottom( true, false, r[ 2 ], r[ 4 ] )
		e:setAlpha( show and 1 or 0 )
	end
	-- the words arrive when the card has opened (the body's open tween fires it)
	P.Face2Text( pull, s, not animate )
end

-- the live face for a dealt card: band "EPIC +3" in the rarity colour + pips,
-- over the old baked art or in the v2 card's own slots.
local function FacePaint( pull, s, dom, rar, cur, animate )
	local o = pull.opts
	local f = s.face
	local d = o.DOMAIN[ dom ]
	local isTier = ( dom == o.TIER_DOMAIN )
	local v2 = s.face2 and P.UsesV2( pull, dom, cur )
	if d == nil and not isTier then
		FaceHide( s )
		return
	end
	if isTier and not v2 then
		FaceHide( s )   -- the old tier art names the promotion itself; no band
		return
	end
	if v2 then
		Face2Paint( pull, s, dom, rar, cur, animate )
	elseif s.face2 then
		for _, op in ipairs( s.face2.opens ) do
			op.e:setAlpha( 0 )
		end
		s.face2.text:setAlpha( 0 )
		s.v2 = false
	end
	local R = o.RARITY[ rar ] or o.RARITY[ 1 ]
	local col = R.col
	local band = v2 and V2.band or { BAND_X0, BAND_Y0, BAND_X1, BAND_Y1 }
	local pips = v2 and V2.pips or { PIPS_X0, PIPS_Y0, PIPS_X1, PIPS_Y1 }
	local bx0, by0, bx1, by1 = f.xLo + band[ 1 ], f.y0 + band[ 2 ], f.xLo + band[ 3 ], f.y0 + band[ 4 ]
	f.bandRim:setLeftRight( true, false, bx0, bx1 )
	f.bandRim:setTopBottom( true, false, by0, by1 )
	f.bandRim:setAlpha( ( v2 or OLD_FACES_NEUTRAL ) and 0 or 1 )   -- the face paints its own slot
	f.band:setLeftRight( true, false, bx0 + 2, bx1 - 2 )
	f.band:setTopBottom( true, false, by0 + 2, by1 - 2 )
	Tint( f.band, Dim( col, GROUND_DIM ) )   -- dark ground under the white rarity word (the rim stays bright)
	f.band:setAlpha( 1 )
	f.bandText:setAlpha( 1 )
	local max = ( d and d.max ) or 5
	local gain = R.lv
	if cur + gain > max then gain = max - cur end
	if gain < 0 then gain = 0 end
	if f.bandRow then
		f.bandRow.setRGB( TEXT_WHITE[ 1 ], TEXT_WHITE[ 2 ], TEXT_WHITE[ 3 ] )
		local word = isTier and "PROMOTION" or ( R.tag .. " +" .. gain )
		SetFit( f.bandRow, word, BAND_CAP, ( bx0 + bx1 ) / 2, ( by0 + by1 ) / 2 + BAND_CAP / 2, ( bx1 - bx0 ) - 16 )
	end
	f.pipCover:setLeftRight( true, false, f.xLo + pips[ 1 ], f.xLo + pips[ 3 ] )
	f.pipCover:setTopBottom( true, false, f.y0 + pips[ 2 ], f.y0 + pips[ 4 ] )
	f.pipCover:setAlpha( ( v2 or OLD_FACES_NEUTRAL or s.card.imgLive == false ) and 0 or 1 )
	if isTier then
		-- a PROMOTION fills the tray with the class's TIERS: the ones already held
		-- (white) and the one this card gives (the card's colour) - "tier 2 of 3" at
		-- a glance, never an empty tray (the tier count is TIER_LADDER's)
		local cls, tier = TierOf( cur )
		local lad = o.TIER_LADDER and o.TIER_LADDER[ cls ]
		max = tier
		for k in pairs( lad or {} ) do
			if type( k ) == "number" and k > max then max = k end
		end
		cur, gain = tier - 1, 1
	end
	PipsLayout( s, pips, max, cur, gain, col )
	if animate and gain > 0 then
		s.pipsPending = true
		s.pipLit = 0
		f.ticker:completeAnimation()
		f.ticker:beginAnimation( "tod_pull_pip", PIP_FIRST_MS, false, false, CoD.TweenType.Linear )
		f.ticker:setAlpha( 0 )
	else
		s.pipLit = 0
		s.pipsPending = true
		P.PipsFinish( s )
	end
end

local function Banner( pull, s, rar, gain, word )
	local R = pull.opts.RARITY[ rar ] or pull.opts.RARITY[ 1 ]
	local col = R.col
	local cx = ( s.card.xLo + s.card.xHi ) / 2
	local y = pull.opts.y0 + 110
	local big = word or R.tag
	local small = ( gain == nil ) and "" or ( "+" .. gain .. ( ( gain == 1 ) and " LEVEL" or " LEVELS" ) )
	if gain ~= nil and gain <= 0 then small = "MAX" end
	local bigCap = ( rar >= 4 ) and 30 or ( ( rar >= 3 ) and 27 or 24 )
	local okBig = false
	if pull.bigRow then
		-- RT 2026-10-05: the stamp (r10 pull_banner) is dark glass, so the word is the rarity's own light (the synthwave
		-- ribbon was light, with dark ink on it: 0.06 / 0.06 / 0.10 when the art drew); r3 CODE_TINTS pins it
		pull.bigRow.setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
		okBig = SetFit( pull.bigRow, big, bigCap, cx, y + bigCap, 260 )
	end
	if pull.smallRow then
		if small ~= "" then
			pull.smallRow.setRGB( 1, 1, 1 )
			SetFit( pull.smallRow, small, 13, cx, y + bigCap + 22, 240 )
		else
			pull.smallRow.hide()
		end
	end
	if not okBig then return end
	local half = 150
	if pull.bannerImg then
		Tint( pull.bannerImg, col )
		pull.bannerImg:setLeftRight( true, false, cx - 170, cx + 170 )
		pull.bannerImg:setTopBottom( true, false, y - 14, y + bigCap + 38 )
	else
		pull.bannerBg:setLeftRight( true, false, cx - half, cx + half )
		pull.bannerBg:setTopBottom( true, false, y - 8, y + bigCap + 30 )
		pull.bannerRule.Bg:setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )
		pull.bannerRule:setLeftRight( true, false, cx - half, cx + half )
		pull.bannerRule:setTopBottom( true, false, y - 10, y - 7 )
	end
	pull.bannerHold = BANNER_HOLD[ rar ] or 500
	pull.banner:completeAnimation()
	pull.banner:setAlpha( 0 )
	pull.banner:beginAnimation( "tod_pull_bn_in", BANNER_IN, false, false, CoD.TweenType.Linear )
	pull.banner:setAlpha( 1 )
end

local function Shards( pull, s, rar )
	local n = SHARDS_N[ rar ] or 0
	local reach = SHARD_REACH[ rar ] or 0
	local col = pull.opts.RARITY[ rar ].col
	local cx = ( s.card.xLo + s.card.xHi ) / 2
	local cy = ( pull.opts.y0 + pull.opts.y1 ) / 2
	local sprite = ( FX( "shard" ) ~= nil )
	for i = 1, SHARD_POOL do
		local e = pull.shards[ i ]
		e:completeAnimation()
		if i <= n then
			local ang = ( i / n ) * 6.2832 + 0.35
			local dx = math.cos( ang ) * reach
			local dy = math.sin( ang ) * reach * 1.25
			local sz = sprite and ( ( rar >= 4 ) and 14 or 11 ) or ( ( rar >= 4 ) and 9 or 7 )
			Tint( e, col )
			e:setLeftRight( true, false, cx - sz, cx + sz )
			e:setTopBottom( true, false, cy - sz, cy + sz )
			e:setAlpha( 1 )
			e:beginAnimation( "tod_pull_shard", SHARD_MS, false, false, CoD.TweenType.Linear )
			e:setLeftRight( true, false, cx + dx - 4, cx + dx + 4 )
			e:setTopBottom( true, false, cy + dy - 4, cy + dy + 4 )
			e:setAlpha( 0 )
		else
			e:setAlpha( 0 )
		end
	end
end

local function Ring( pull, s, rar )
	if not pull.ring or ( RING_TO[ rar ] or 0 ) == 0 then return end
	local col = pull.opts.RARITY[ rar ].col
	local cx = ( s.card.xLo + s.card.xHi ) / 2
	local cy = ( pull.opts.y0 + pull.opts.y1 ) / 2
	local e = pull.ring
	e:completeAnimation()
	Tint( e, col )
	e:setLeftRight( true, false, cx - 40, cx + 40 )
	e:setTopBottom( true, false, cy - 40, cy + 40 )
	e:setAlpha( 1 )
	e:beginAnimation( "tod_pull_ring", RING_MS[ rar ], false, false, CoD.TweenType.Linear )
	local h = RING_TO[ rar ] / 2
	e:setLeftRight( true, false, cx - h, cx + h )
	e:setTopBottom( true, false, cy - h, cy + h )
	e:setAlpha( 0 )
end

local function Flash( pull, s, rar )
	local peak = FLASH_PEAK[ rar ] or 0
	if peak <= 0 then return end
	local col = pull.opts.RARITY[ rar ].col
	if rar >= 4 then
		col = { 1, 0.93, 0.72 }
	end
	local e = pull.flash
	e:completeAnimation()
	Tint( e, col )
	if not e.Bg then   -- the sprite: a burst centred on the card, bigger the rarer
		local cx = ( s.card.xLo + s.card.xHi ) / 2
		local cy = ( pull.opts.y0 + pull.opts.y1 ) / 2
		local h = FLASH_SIZE[ rar ] / 2
		e:setLeftRight( true, false, cx - h, cx + h )
		e:setTopBottom( true, false, cy - h, cy + h )
	end
	e:setAlpha( e.Bg and peak * 0.6 or peak )
	e:beginAnimation( "tod_pull_flash", FLASH_MS[ rar ], false, false, CoD.TweenType.Linear )
	e:setAlpha( 0 )
end

-- the flip: the back folds into its spine, the face opens out of it, and the
-- rarity pays for itself
local function Flip( pull, s, dom, rar, cur )
	local RARITY = pull.opts.RARITY
	local b = s.back
	local mid = ( b.xLo + b.xHi ) / 2
	-- THE REACH / THE HOT STREAK (docs/201): a reach still drawn goes (its SO CLOSE beat was lost); the warm embers
	-- end with the back (a LEGENDARY's own gold motes start again in AuraStart below)
	if s.reaching then
		P.ReachClear( s )
	end
	EmbersOff( s )
	for _, e in ipairs( b.parts ) do
		e:completeAnimation()
		e:beginAnimation( "tod_pull_fold", BACK_FOLD_MS, false, false, CoD.TweenType.Linear )
		e:setLeftRight( true, false, mid - 2, mid + 2 )
		e:setAlpha( 0 )
	end
	for i = 1, #b.sigil do
		b.sigil[ i ]:setAlpha( 0 )
	end
	b.sweep:completeAnimation()
	b.sweep:setAlpha( 0 )

	LadderPaint( s, rar, rar, RARITY )
	Flash( pull, s, rar )
	Ring( pull, s, rar )
	if rar >= 2 then
		Shards( pull, s, rar )
	end
	AuraStart( pull, s, rar )
	-- the room settles back after the moment
	Edges( pull, nil, 0 )
	DimTo( pull, DIM_BASE, 120 )

	FacePaint( pull, s, dom, rar, cur, true )
	local d = pull.opts.DOMAIN[ dom ]
	if dom == pull.opts.TIER_DOMAIN then
		Banner( pull, s, rar, nil, "NEW TIER" )
		return
	end
	local gain = RARITY[ rar ].lv
	if d and d.max and cur + gain > d.max then gain = d.max - cur end
	Banner( pull, s, rar, gain )
end

-- =============================================================================
-- RENDER — called at the END of tod_upgrade.lua's Render, every paint.
-- st: the decoded panel state (ar/br = rarity 1..4, 0 = no card in B).
-- =============================================================================
function P.Render( pull, st, revealing )
	if st.show == 0 then
		if pull.wasRev or pull.slot.a.started or pull.slot.a.d ~= 0 or pull.slot.a.raysOn or pull.slot.b.raysOn then
			P.Reset( pull, true )
		end
		return
	end

	local A, B = pull.slot.a, pull.slot.b
	local two = ( st.br or 0 ) >= 1

	-- THE DEAL OPENS: both backs on the table, the ladders dim, the room dims
	if revealing and not pull.wasRev then
		P.Reset( pull, true )
		BackPick( pull, A )
		BackPick( pull, B )
		BackShow( A, true )
		BackTint( A, 0, pull.opts.RARITY )
		A.ladder.layer:setAlpha( 1 )
		LadderPaint( A, 0, 0, pull.opts.RARITY )
		if two then
			BackShow( B, true )
			BackTint( B, 0, pull.opts.RARITY )
			B.ladder.layer:setAlpha( 1 )
			LadderPaint( B, 0, 0, pull.opts.RARITY )
		end
		DimTo( pull, DIM_BASE, 90 )
		pull.hold = st.hold or 0
		pull.wasRev = true
		-- THE HOT STREAK (docs/201): a hot player's backs arrive warm
		local heat = tonumber( CoD.TodHeat ) or 0
		Warm( pull, A, heat )
		if two then
			Warm( pull, B, heat )
		end
	end

	if revealing then
		-- FLIPS (the domain edge) — read before the active slot moves on
		if A.d == 0 and ( st.ad or 0 ) ~= 0 then
			A.d = st.ad
			Flip( pull, A, st.ad, st.ar, st.al or 0 )
		end
		if two and B.d == 0 and ( st.bd or 0 ) ~= 0 then
			B.d = st.bd
			Flip( pull, B, st.bd, st.br, st.bl or 0 )
		end

		local act = nil
		if ( st.ad or 0 ) == 0 then
			act = A
		elseif two and ( st.bd or 0 ) == 0 then
			act = B
		end

		-- BEATS (todUpgHold rising). THE REACH (docs/201): a SECOND beat at the same rung with no climb between is
		-- the card straining for the next rung; a beat while it strains resolves it SO CLOSE (a climb resolves it
		-- BREAK THROUGH, below). Beats that share one snapshot are played in order, never merged.
		local h = st.hold or 0
		if h > pull.hold then
			local n = math.min( h - pull.hold, 4 )
			pull.hold = h
			if act then
				for _ = 1, n do
					if not act.started then
						act.started = true
						-- a heat that reached the HUD a moment after the deal opened still warms this back
						if not act.warm and ( tonumber( CoD.TodHeat ) or 0 ) > 0 then
							Warm( pull, act, tonumber( CoD.TodHeat ) )
						end
						Climb( pull, act, 1 )
					else
						act.beatsHere = ( act.beatsHere or 0 ) + 1
						if act.reaching then
							Deflate( pull, act )
						elseif act.beatsHere >= 2 then
							Reach( pull, act )
						else
							Beat( act )
						end
					end
				end
			end
		end

		-- CLIMBS (the active slot's rarity rising)
		if act and act.started then
			local r = ( act == A ) and ( st.ar or 1 ) or ( st.br or 1 )
			if r > act.rung then
				if act.reaching then
					BreakThrough( pull, act, r )
				end
				Climb( pull, act, r )
			end
		end
		P.GlowFollow( pull )
		return
	end

	-- CHOOSING (and after): keep the faces painted in their end state (a
	-- re-present after a takeover, or a deal that skipped the show)
	if pull.wasRev then
		pull.wasRev = false
		BackShow( A, false )
		BackShow( B, false )
		Edges( pull, nil, 0 )
		DimTo( pull, DIM_BASE * 0.6, 150 )
	end
	for _, pair in ipairs( { { A, st.ad, st.ar, st.al }, { B, st.bd, st.br, st.bl } } ) do
		local s, dom, rar, cur = pair[ 1 ], pair[ 2 ] or 0, pair[ 3 ] or 1, pair[ 4 ] or 0
		if dom ~= 0 and ( s == A or two ) then
			local key = dom .. ":" .. rar .. ":" .. cur
			if s.faceKey ~= key then
				s.faceKey = key
				if s.d ~= dom then
					-- never flipped in front of us: paint the end state
					s.d = dom
					FacePaint( pull, s, dom, rar, cur, false )
					s.ladder.layer:setAlpha( 1 )
					LadderPaint( s, rar, rar, pull.opts.RARITY )
					if not s.raysOn then
						AuraStart( pull, s, rar )
					end
				end
			end
		elseif s.d ~= 0 or s.faceKey then
			FaceHide( s )
			AuraStop( s )
			s.faceKey = nil
			s.d = 0
			s.ladder.layer:setAlpha( 0 )
		end
	end
	P.GlowFollow( pull )
end

-- the card glow follows the card it belongs to: full on the focused card, dimmed
-- on the passed-over one (tod_upgrade.lua's glowMul), gone before the flip. It
-- REPLACES tod_upgrade.lua's flat Glow rectangle, which is held at 0 here.
function P.GlowFollow( pull )
	for _, s in pairs( pull.slot ) do
		local us = s.under
		if us and us.glow and s.card.Glow then
			s.card.Glow:setAlpha( 0 )
			if ( s.d or 0 ) ~= 0 then
				us.glow:setAlpha( ( 0.35 + 0.15 * ( s.rar or 1 ) ) * ( s.card.glowMul or 1 ) )
			end
		end
	end
end
