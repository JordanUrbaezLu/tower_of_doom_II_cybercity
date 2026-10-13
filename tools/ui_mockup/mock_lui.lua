-- tools/ui_mockup/mock_lui.lua — a GEOMETRY-RECORDING LUI mock (2026-09-28).
-- Loaded by render_menus.py (lupa, Lua 5.1). Every element remembers its anchors,
-- offsets, image, text, colour and alpha, so the Python side can draw the menu the
-- way the engine lays it out: the real art from source_data/tod_ui_images/_images and
-- the real map font. It is a LAYOUT proof, not a shader: no animations, no clips.
local noop = function() end
-- NIL-ISH: an unknown field reads as a callable, indexable nothing, so both e:someMethod() and
-- e.someChild:setAlpha( 0 ) are harmless no-ops.
local NIL = setmetatable({}, { __call = function() end })
getmetatable(NIL).__index = function() return NIL end
ALL = {}
local methods = {}
local function newElement()
    local e = setmetatable({ children = {}, handlers = {}, rgb = { 1, 1, 1 }, alpha = 1 }, { __index = function(_, k)
        if methods[k] then return methods[k] end
        -- data fields the dump reads must read nil when unset; every other name is a no-op method
        if k == 'img' or k == 'text' or k == 'lr' or k == 'tb' or k == '_closed' or k == 'ttf' or k == 'align' or k == 'parent' then return nil end
        return NIL
    end })
    ALL[#ALL + 1] = e
    return e
end
function methods:addElement(e) self.children[#self.children + 1] = e; e.parent = self end
function methods:setLeftRight(a, b, l, r) self.lr = { a, b, l, r } end
function methods:setTopBottom(a, b, t, bb) self.tb = { a, b, t, bb } end
function methods:setImage(img) self.img = img end
function methods:setText(s) self.text = s end
function methods:setRGB(r, g, b) self.rgb = { r, g, b } end
function methods:setAlpha(a) self.alpha = a end
function methods:setTTF(f) self.ttf = f end
function methods:setAlignment(a) self.align = a end
function methods:setScale(s) self.scale = s end
function methods:getParent() return self.parent end
function methods:getFirstChild() return self.children[1] end
function methods:getNextSibling()
    if not self.parent then return nil end
    for i, e in ipairs(self.parent.children) do if e == self then return self.parent.children[i + 1] end end
end
function methods:close() self._closed = true end
function methods:registerEventHandler(k, v) self.handlers[k] = v end
function methods:restoreState() return true end
function methods:getOwner() return 0 end
function methods:getLocalLeftRight() local x = self.lr or { true, false, 0, 80 }; return x[1], x[2], x[3], x[4] end
function methods:getLocalTopBottom() local x = self.tb or { true, false, 0, 20 }; return x[1], x[2], x[3], x[4] end
function methods:getModel() return 'elmodel' end
function methods:isInFocus() return false end
function methods:playClip() return false end
methods.super = setmetatable({}, { __index = function() return noop end })
local function enums() return setmetatable({}, { __index = function(t, k) local v = enums(); rawset(t, k, v); return v end }) end
Enum = enums()
Enum.UIVisibilityBit = setmetatable({}, { __index = function(_, k) return 7 end })
Enum.LUIAlignment = { LUI_ALIGNMENT_LEFT = 'left', LUI_ALIGNMENT_RIGHT = 'right', LUI_ALIGNMENT_CENTER = 'center' }
MODELVAL = 12
Engine = setmetatable({
    Localize = function(s) return s end,
    GetModelForController = function() return 'ctrl' end,
    GetModel = function(m, k) return tostring(m) .. '.' .. tostring(k) end,
    CreateModel = function(m, k) return tostring(m) .. '.' .. tostring(k) end,
    GetModelValue = function() return MODELVAL end, IsInGame = function() return true end,
    GetCurrentMap = function() return 'zm_tod2_cybercity' end, GetClientNum = function() return 0 end,
    -- RT 2026-10-05: a key per command (a KBM default layout), so a review shows each cap's real name
    GetKeyBindingLocalizedString = function( _, cmd ) return ( { [ '+activate' ] = 'F', [ '+frag' ] = 'G', [ '+smoke' ] = 'Q', [ '+gostand' ] = 'SPACE', [ '+melee' ] = 'V', [ '+reload' ] = 'R', [ '+attack' ] = 'MOUSE1', [ '+speed_throw' ] = 'MOUSE2' } )[ cmd ] or 'F' end,
    DvarString = function() return '' end,
}, { __index = function() return noop end })
DataSources = {}
DataSourceHelpers = { ListSetup = function(_, fn) return fn end }
function ListHelper_SetupDataSource(_, fn) return { __build = fn } end
CoD = { Menu = { NewForUIEditor = newElement }, TweenType = { Linear = 0 }, isZombie = true, TodClass = 2, TodClassTier = 1 }
CoD.Menu.SetButtonLabel = noop; CoD.Menu.UpdateButtonShownState = noop
CoD.GetScriptNotifyData = function() return {} end
CoD.TodUIOwnership = { Attach = noop }
CoD.TodDarkPlate = function( id ) return 'i_tod_pm_row_violet', { 1, 1, 1 }, false end
LUI = { UIElement = { new = newElement }, UIImage = { new = newElement }, UIText = { new = newElement }, UIList = { new = newElement }, UITimer = { new = newElement }, createMenu = {} }
function LUI.OverrideFunction_CallOriginalSecond(e, key, fn) end
function InheritFrom() return {} end
function RegisterImage(s) return s end
function IsPC() return true end
function IsGamepad() return false end
function IsInGame() return true end
function RegisterOpenedMenu() end
function IsPrimaryController() return true end
function IsModelValueEqualTo() return false end
function PlayClip() end
function GoBack() end
function OpenPopup() end
function OpenOverlay() end
require = function() end
LUI.UIElement.clipFinished = noop

-- the real level-aware card text (tod_upgrade.lua's top half), as the runtime harness does
do
    local f = assert(io.open('ui/uieditor/menus/hud/tod_upgrade.lua', 'r')); local src = f:read('*a'); f:close()
    local cut = src:find('\nlocal USE_TITLE_ART', 1, true)   -- R5: USE_FRAME_ART left with the composite card lane
    assert(cut, 'cut point moved')
    assert(loadstring(src:sub(1, cut), '@tod_upgrade.lua(top)'))()
end

-- Flatten the tree for Python: absolute rects, draw order.
function DUMP(root)
    local out = {}
    local function rect(e, px0, py0, px1, py1)
        local x0, x1, y0, y1 = px0, px1, py0, py1
        if e.lr then
            local a, b, l, r = e.lr[1], e.lr[2], e.lr[3], e.lr[4]
            if a and not b then x0, x1 = px0 + l, px0 + r
            elseif a and b then x0, x1 = px0 + l, px1 + r
            elseif b then x0, x1 = px1 + l, px1 + r
            else local c = (px0 + px1) / 2; x0, x1 = c + l, c + r end
        end
        if e.tb then
            local a, b, t, bb = e.tb[1], e.tb[2], e.tb[3], e.tb[4]
            if a and not b then y0, y1 = py0 + t, py0 + bb
            elseif a and b then y0, y1 = py0 + t, py1 + bb
            elseif b then y0, y1 = py1 + t, py1 + bb
            else local c = (py0 + py1) / 2; y0, y1 = c + t, c + bb end
        end
        return x0, y0, x1, y1
    end
    local function walk(e, px0, py0, px1, py1, alpha)
        local x0, y0, x1, y1 = rect(e, px0, py0, px1, py1)
        local a = alpha * (e.alpha or 1)
        if not e._closed and a > 0.01 then
            if e.img or e.text then
                out[#out + 1] = { x0 = x0, y0 = y0, x1 = x1, y1 = y1, img = e.img or '', text = e.text or '',
                                  r = e.rgb[1], g = e.rgb[2], b = e.rgb[3], a = a, ttf = e.ttf or '', align = e.align or 'left' }
            end
            for _, c in ipairs(e.children) do walk(c, x0, y0, x1, y1, a) end
        end
    end
    walk(root, 0, 0, 1280, 720, 1)
    return out
end
