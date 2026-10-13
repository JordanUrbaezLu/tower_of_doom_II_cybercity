-- mock_lui_anim.lua - a TIMED LUI mock for render_pull.py (docs/187).
--
-- Like mock_lui.lua it records every element's geometry, image, tint and text so
-- Python can draw the tree with the shipped art. Unlike it, it has a CLOCK:
--   * beginAnimation( name, ms ) snapshots the element's state BEFORE the setters
--     that follow it (the tween's start) and schedules the tween;
--   * ADVANCE( ms ) moves the clock, finishing tweens in time order and firing
--     their "transition_complete_<name>" handlers (so chains - the pip ticker,
--     the banner, the god-ray rotation, the motes - really run);
--   * DUMP( root ) flattens the tree at the CURRENT time, interpolating every
--     running tween linearly between its start and end state.
-- Model subscriptions are stored; PUSH( name, value ) sets a model and fires them.
-- scriptNotify subscriptions (subscribeToGlobalModel) are stored too: NOTIFY( name, data )
-- fires them the way a server LuiNotifyEvent does (render_spin.py drives the Black Market
-- reel this way). setUseStencil( true ) clips an element's children to its rect in DUMP.
-- An approximation of the engine (linear tweens, no blend modes), good enough to
-- judge layout, colour, timing and choreography - not a pixel match.

local noop = function() end
NOW = 0
ALL = {}
local ANIMS = {}          -- running tweens
local SUBS, MODELS = {}, {}
local methods = {}

local function copyState( e )
	return { lr = e.lr and { e.lr[1], e.lr[2], e.lr[3], e.lr[4] } or nil,
	         tb = e.tb and { e.tb[1], e.tb[2], e.tb[3], e.tb[4] } or nil,
	         alpha = e.alpha, zrot = e.zrot or 0,
	         rgb = { e.rgb[1], e.rgb[2], e.rgb[3] } }
end

local function newElement()
	local e = setmetatable( { children = {}, handlers = {}, rgb = { 1, 1, 1 }, alpha = 1, zrot = 0 }, { __index = function( _, k )
		if methods[ k ] then return methods[ k ] end
		if k:match( '^set' ) or k:match( '^make' ) or k:match( '^link' ) or k:match( '^Add' ) or k:match( '^merge' ) or k:match( '^update' ) then return noop end
		return nil
	end } )
	ALL[ #ALL + 1 ] = e
	return e
end

function methods:addElement( e ) self.children[ #self.children + 1 ] = e; e.parent = self end
function methods:setLeftRight( a, b, l, r ) self.lr = { a, b, l, r } end
function methods:setTopBottom( a, b, t, bb ) self.tb = { a, b, t, bb } end
function methods:setImage( img ) self.img = img end
function methods:setText( s ) self.text = s end
function methods:setRGB( r, g, b ) self.rgb = { r, g, b } end
function methods:setAlpha( a ) self.alpha = a end
function methods:setZRot( z ) self.zrot = z end
function methods:setScale( s ) self.scale = s end
function methods:getParent() return self.parent end
function methods:getFirstChild() return self.children[ 1 ] end
function methods:getNextSibling()
	if not self.parent then return nil end
	for i, c in ipairs( self.parent.children ) do if c == self then return self.parent.children[ i + 1 ] end end
end
function methods:close() self._closed = true end
function methods:registerEventHandler( k, v ) self.handlers[ k ] = v end
function methods:processEvent( ev ) local h = self.handlers[ ev.name ]; if h then return h( self, ev ) end end
function methods:getOwner() return 0 end
function methods:getLocalLeftRight() local x = self.lr or { true, false, 0, 80 }; return x[1], x[2], x[3], x[4] end
function methods:getLocalTopBottom() local x = self.tb or { true, false, 0, 20 }; return x[1], x[2], x[3], x[4] end
function methods:restoreState() return true end
function methods:playClip() return false end
function methods:subscribeToModel( m, fn ) SUBS[ m ] = SUBS[ m ] or {}; table.insert( SUBS[ m ], fn ) end
local GSUBS = {}
function methods:subscribeToGlobalModel( inst, group, name, fn )
	GSUBS[ name ] = GSUBS[ name ] or {}
	table.insert( GSUBS[ name ], fn )
end
function methods:setUseStencil( on ) self.stencil = on end
function methods:setAlignment( a ) self.alignEnum = a end

function methods:beginAnimation( name, ms )
	-- one running tween per element: a new one replaces the old (it lands at its end)
	for i = #ANIMS, 1, -1 do if ANIMS[ i ].e == self then table.remove( ANIMS, i ) end end
	ANIMS[ #ANIMS + 1 ] = { e = self, name = name, t0 = NOW, dur = math.max( 1, ms or 0 ), pre = copyState( self ) }
end
function methods:completeAnimation()
	for i = #ANIMS, 1, -1 do if ANIMS[ i ].e == self then table.remove( ANIMS, i ) end end
end

function PUSH( name, v )
	local key = 'ctrl.' .. name
	MODELS[ key ] = v
	for _, fn in ipairs( SUBS[ key ] or {} ) do fn( key ) end
end

-- a server LuiNotifyEvent: the scriptNotify model takes the event's name and every
-- subscriber reads the data through CoD.GetScriptNotifyData
local NOTIFY_DATA = {}
function NOTIFY( name, data )
	MODELS[ 'notify' ] = name
	NOTIFY_DATA = data or {}
	for _, fn in ipairs( GSUBS[ 'scriptNotify' ] or {} ) do fn( 'notify' ) end
end

-- move the clock, completing tweens in order and firing their handlers
function ADVANCE( ms )
	local target = NOW + ms
	while true do
		local nxt, idx = nil, nil
		for i, a in ipairs( ANIMS ) do
			local te = a.t0 + a.dur
			if te <= target and ( not nxt or te < nxt ) then nxt, idx = te, i end
		end
		if not nxt then break end
		local a = table.remove( ANIMS, idx )
		NOW = nxt
		local h = a.e.handlers[ 'transition_complete_' .. a.name ]
		if h then h( a.e, { interrupted = false } ) end
	end
	NOW = target
end

local function enums() return setmetatable( {}, { __index = function( t, k ) local v = enums(); rawset( t, k, v ); return v end } ) end
Enum = enums()
do local n = 0; Enum.UIVisibilityBit = setmetatable( {}, { __index = function( t, k ) n = n + 1; rawset( t, k, n ); return n end } ) end
Engine = setmetatable( {
	Localize = function( s ) return s end, GetModelForController = function() return 'ctrl' end,
	GetModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
	CreateModel = function( m, k ) return tostring( m ) .. '.' .. tostring( k ) end,
	GetModelValue = function( k ) return MODELS[ k ] or 0 end, IsInGame = function() return true end,
	GetCurrentMap = function() return 'zm_tod2_cybercity' end, GetClientNum = function() return 0 end,
	-- RT 2026-10-05: a key per command (a KBM default layout), so a review shows each cap's real name, not 'F' x 8
	GetKeyBindingLocalizedString = function( _, cmd ) return ( { [ '+activate' ] = 'F', [ '+frag' ] = 'G', [ '+smoke' ] = 'Q', [ '+gostand' ] = 'SPACE', [ '+melee' ] = 'V', [ '+reload' ] = 'R', [ '+attack' ] = 'MOUSE1', [ '+speed_throw' ] = 'MOUSE2' } )[ cmd ] or 'F' end,
}, { __index = function() return noop end } )
DataSources = {}
DataSourceHelpers = { ListSetup = function( _, fn ) return fn end }
function ListHelper_SetupDataSource( _, fn ) return { __build = fn } end
CoD = { Menu = { NewForUIEditor = newElement }, TweenType = { Linear = 0, Bounce = 1 }, isZombie = true, TodOwned = {}, TodClass = 2, TodClassTier = 1 }
CoD.Menu.SetButtonLabel = noop; CoD.Menu.UpdateButtonShownState = noop
CoD.GetScriptNotifyData = function() return NOTIFY_DATA end
-- a UIImage with no image draws a SOLID quad in the engine (its RGB tint): so does the dump
local function newImage() local e = newElement(); e.isImage = true; return e end
LUI = { UIElement = { new = newElement }, UIImage = { new = newImage }, UIText = { new = newElement }, UIList = { new = newElement }, UITimer = { new = newElement }, createMenu = {} }
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
-- a flat panel = an element with a white image child (so the dump draws it)
CoD.TextWithBg = { new = function()
	local e = newElement()
	e.Text = newElement(); e.Bg = newElement()
	e.Bg.img = '$white'
	e:addElement( e.Text ); e:addElement( e.Bg )
	return e
end }

-- Flatten the tree at NOW: absolute rects, alpha and colour multiplied down, zRot.
function DUMP( root )
	local out = {}
	local live = {}
	for _, a in ipairs( ANIMS ) do live[ a.e ] = a end
	local function state( e )
		local a = live[ e ]
		if not a then return e.lr, e.tb, e.alpha, e.rgb, e.zrot or 0 end
		local f = ( NOW - a.t0 ) / a.dur
		if f < 0 then f = 0 elseif f > 1 then f = 1 end
		local function lerp4( p, q )
			if not ( p and q ) then return q or p end
			return { q[1], q[2], p[3] + ( q[3] - p[3] ) * f, p[4] + ( q[4] - p[4] ) * f }
		end
		local rgb = { a.pre.rgb[1] + ( e.rgb[1] - a.pre.rgb[1] ) * f, a.pre.rgb[2] + ( e.rgb[2] - a.pre.rgb[2] ) * f, a.pre.rgb[3] + ( e.rgb[3] - a.pre.rgb[3] ) * f }
		return lerp4( a.pre.lr, e.lr ), lerp4( a.pre.tb, e.tb ), a.pre.alpha + ( e.alpha - a.pre.alpha ) * f, rgb, a.pre.zrot + ( ( e.zrot or 0 ) - a.pre.zrot ) * f
	end
	local function rect( lr, tb, px0, py0, px1, py1 )
		local x0, x1, y0, y1 = px0, px1, py0, py1
		if lr then
			local a, b, l, r = lr[1], lr[2], lr[3], lr[4]
			if a and not b then x0, x1 = px0 + l, px0 + r
			elseif a and b then x0, x1 = px0 + l, px1 + r
			elseif b then x0, x1 = px1 + l, px1 + r
			else local c = ( px0 + px1 ) / 2; x0, x1 = c + l, c + r end
		end
		if tb then
			local a, b, t, bb = tb[1], tb[2], tb[3], tb[4]
			if a and not b then y0, y1 = py0 + t, py0 + bb
			elseif a and b then y0, y1 = py0 + t, py1 + bb
			elseif b then y0, y1 = py1 + t, py1 + bb
			else local c = ( py0 + py1 ) / 2; y0, y1 = c + t, c + bb end
		end
		return x0, y0, x1, y1
	end
	local function alignOf( e )
		local A = Enum.LUIAlignment
		if e.alignEnum and A and e.alignEnum == A.LUI_ALIGNMENT_CENTER then return 'center' end
		if e.alignEnum and A and e.alignEnum == A.LUI_ALIGNMENT_RIGHT then return 'right' end
		return e.align or 'left'
	end
	local function walk( e, px0, py0, px1, py1, alpha, pr, pg, pb, clip )
		local lr, tb, al, rgb, zr = state( e )
		local x0, y0, x1, y1 = rect( lr, tb, px0, py0, px1, py1 )
		local a = alpha * ( al or 1 )
		local r, g, b = pr * rgb[1], pg * rgb[2], pb * rgb[3]
		if not e._closed and a > 0.004 then
			local img = e.img or ( e.isImage and '$white' ) or nil
			if img or ( e.text and e.text ~= '' ) then
				local it = { x0 = x0, y0 = y0, x1 = x1, y1 = y1, img = img or '', text = e.text or '',
				             r = r, g = g, b = b, a = a, zrot = zr or 0, align = alignOf( e ) }
				if clip then it.cx0, it.cy0, it.cx1, it.cy1 = clip[1], clip[2], clip[3], clip[4] end
				out[ #out + 1 ] = it
			end
			local cc = clip
			if e.stencil then
				cc = { x0, y0, x1, y1 }
				if clip then cc = { math.max( x0, clip[1] ), math.max( y0, clip[2] ), math.min( x1, clip[3] ), math.min( y1, clip[4] ) } end
			end
			for _, c in ipairs( e.children ) do walk( c, x0, y0, x1, y1, a, r, g, b, cc ) end
		end
	end
	walk( root, 0, 0, 1280, 720, 1, 1, 1, 1, nil )
	return out
end
