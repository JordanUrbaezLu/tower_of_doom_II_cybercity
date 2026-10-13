-- Pause menu RUNTIME harness (2026-09-26, the build-15b "UI Error 8939" boxes).
-- test_ui_lifetimes builds and closes the menu, but its mocks turn every
-- subscription and handler into a no-op, so a nil index inside a CALLBACK can
-- never fire there. This harness records every subscribeToModel /
-- subscribeToGlobalModel / linkToElementModel callback, every event handler and
-- every button callback, and FIRES them with realistic, nil and odd values;
-- runs every datasource item's action; flips the settings page both ways; and
-- rebuilds with 0 / 1 / 12 / 20 owned rows for each class and tier, dark rows,
-- the tier row, missing CoD.TodOwned and nil sync fields - under a guard that
-- makes any NEW GLOBAL an error (UI Error 87927 was exactly that).
-- 2026-09-26 (after build 16): the ListHelper mock returns a TABLE like the
-- engine (my first cut returned the function, which hid the settings-page crash),
-- every button's models.action runs, and every list rebuilds after each action
-- (the lead's realistic variant, folded in). THE OLD-CODE NEGATIVE CONTROL at the
-- bottom restores the exact build-15b line and must fail with "attempt to call a
-- table" - so a mock can never hide that crash again.
-- Run: python -c "import lupa.lua51 as l; L=l.LuaRuntime(); L.execute(open('tools/test_pause_menu_runtime.lua').read())"
local noop = function() end
local elements, methods = {}, {}
local subs, handlers, btncbs = {}, {}, {}
local function newElement()
    local e = setmetatable({ children = {}, handlers = {} }, { __index = function(_, k)
        if methods[k] then return methods[k] end
        if type(k) == "string" and (k:match('^set') or k:match('^make') or k:match('^Add') or k:match('^link') == nil and k:match('^subscribe')) then return noop end
    end })
    elements[#elements + 1] = e
    return e
end
function methods:addElement(e) self.children[#self.children + 1] = e; e.parent = self end
function methods:getParent() return self.parent end
function methods:getFirstChild() return self.children[1] end
function methods:getNextSibling()
    if not self.parent then return nil end
    for i, e in ipairs(self.parent.children) do if e == self then return self.parent.children[i + 1] end end
end
function methods:close()
    self.closed = true
    if self.parent then
        for i, e in ipairs(self.parent.children) do if e == self then table.remove(self.parent.children, i); break end end
        self.parent = nil
    end
end
function methods:registerEventHandler(k, v) self.handlers[k] = v; handlers[#handlers + 1] = { el = self, name = k, fn = v } end
function methods:subscribeToModel(model, fn) subs[#subs + 1] = { el = self, model = model, fn = fn } end
function methods:subscribeToGlobalModel(ctrl, a, b, fn) subs[#subs + 1] = { el = self, model = tostring(a) .. '.' .. tostring(b), fn = fn } end
function methods:linkToElementModel(el, name, imm, fn) subs[#subs + 1] = { el = self, model = 'elem.' .. tostring(name), fn = fn } end
function methods:AddButtonCallbackFunction(el, ctrl, key, label, fn) btncbs[#btncbs + 1] = { el = el, fn = fn } end
function methods:completeAnimation() end
function methods:restoreState() return true end
function methods:playSound() end
function methods:getOwner() return 0 end
function methods:processEvent(e) if self.handlers[e.name] then return self.handlers[e.name](self, e) end end
function methods:getLocalLeftRight() return true, false, 0, 80 end
function methods:getLocalTopBottom() return true, false, 0, 20 end
function methods:beginAnimation(name, ms) self.anim = { name = name, ms = ms } end
function methods:mergeStateConditions() end
function methods:updateDataSource() end
function methods:getModel() return 'elmodel' end
function methods:isInFocus() return false end
function methods:navigateItemDown() end
function methods:navigateItemUp() end
methods.super = { gain_focus = function() end, lose_focus = function() end }
setmetatable(methods.super, { __index = function() return function() end end })
local function enums() return setmetatable({}, { __index = function(t, k) local v = enums(); rawset(t, k, v); return v end }) end
Enum = enums()
local MODELVAL = 0
Engine = setmetatable({
    Localize = function(s) assert(s ~= nil, 'Engine.Localize(nil)'); return s end,
    GetModelForController = function() return 'ctrl' end,
    GetModel = function(m, k) return tostring(m) .. '.' .. tostring(k) end,
    CreateModel = function(m, k) return tostring(m) .. '.' .. tostring(k) end,
    GetModelValue = function() return MODELVAL end, IsInGame = function() return true end,
    GetCurrentMap = function() return 'zm_tod2_cybercity' end, GetClientNum = function() return 0 end,
    GetKeyBindingLocalizedString = function(c, cmd) return 'G OR MIDDLE MOUSE' end,
    DvarString = function() return '' end,
}, { __index = function() return noop end })
DataSources = {}
OpenPopup = OpenPopup or function() end
IsPC = IsPC or function() return true end
OpenOverlay = OpenOverlay or function() end
DataSourceHelpers = { ListSetup = function(_, fn) return fn end }
function ListHelper_SetupDataSource(_, fn) return { __build = fn } end   -- REALISTIC: the engine returns a TABLE
CoD = { Menu = { NewForUIEditor = newElement }, TweenType = { Linear = 0 }, isZombie = true, TodClass = 1, TodClassTier = 1 }
CoD.Menu.SetButtonLabel = noop; CoD.Menu.UpdateButtonShownState = noop
CoD.GetScriptNotifyData = function() return {} end
LUI = { UIElement = { new = newElement }, UIImage = { new = newElement }, UIText = { new = newElement }, UIList = { new = newElement }, UITimer = { new = newElement }, createMenu = {} }
function LUI.OverrideFunction_CallOriginalSecond(e, key, fn)
    local old = e[key]; e[key] = function(...) fn(...); if old then return old(...) end end
end
function InheritFrom() return {} end
function RegisterImage(s) assert(type(s) == 'string' and s ~= '', 'RegisterImage(' .. tostring(s) .. ')'); return s end
function IsPC() return true end
function IsGamepad() return false end
function IsInGame() return true end
function RegisterOpenedMenu() end
function IsPrimaryController() return true end
function IsModelValueEqualTo() return false end
function PlayClip(e, name) end
function GoBack() end
function ProcessListAction() end
function RefreshLobbyRoom() end
function StartMenuGoBack() end
function StartMenuGoBack_ListElement() end
function CloseStartMenu() end
function Close() end
require = function() end
methods.playClip = function() return false end
methods.setupElementClipCounter = noop
methods.childClipFinished = noop
methods.clipFinished = noop
LUI.UIElement.clipFinished = noop

-- The REAL level-aware text: tod_upgrade.lua's top half (DOMAIN / DETAIL /
-- TodDomainDesc), cut before the HUD construction.
do
    local f = assert(io.open('ui/uieditor/menus/hud/tod_upgrade.lua', 'r')); local src = f:read('*a'); f:close()
    local cut = src:find('\nlocal USE_TITLE_ART', 1, true)   -- R5: USE_FRAME_ART left with the composite card lane
    assert(cut, 'cut point moved')
    assert(loadstring(src:sub(1, cut), '@tod_upgrade.lua(top)'))()
end
assert(CoD.TodDomainDesc and CoD.TodDomainInfo, 'domain text not loaded')

-- From here on a NEW GLOBAL is the native error.
setmetatable(_G, { __newindex = function(_, k) error('LUI Error: Tried to create global variable ' .. tostring(k), 2) end })
local f = assert(io.open('ui/uieditor/menus/StartMenu/AetheriumStartMenu.lua', 'r')); local SRC_NOW = f:read('*a'); f:close()

local function RUN(SRC)
    DataSources = {}
    assert(loadstring(SRC, '@AetheriumStartMenu.lua'))()

    local fails, runs = {}, 0
    local function try(label, fn, ...)
        runs = runs + 1
        local ok, err = pcall(fn, ...)
        if not ok then fails[#fails + 1] = label .. ' -> ' .. tostring(err) end
    end
    local VALUES = { 0, 1, 5, 42, -1, '', 'i_tod_pm_gly_settings', 'MENU_RESUME', true, false }

    local ownedSets = { none = false, empty = {}, one = { [2] = { lvl = 1, max = 5 } } }
    local twelve, twenty, weird = {}, {}, {}
    for id = 1, 12 do twelve[id] = { lvl = (id % 5) + 1, max = 5, safe = (id % 2 == 0), dark = (id % 3 == 0) } end
    for id = 1, 63 do twenty[id] = { lvl = 3, max = 10, dark = (id % 4 == 0) } end
    twenty[24] = { lvl = 3, max = 3 }          -- tier row at the top tier
    weird[5] = { lvl = 2 }                       -- max nil
    weird[7] = { lvl = 12, max = 5 }             -- over max
    weird[9] = { lvl = 1, max = 0, safe = false }
    weird[62] = { lvl = 1, max = 1 }             -- unknown / text-row ids
    weird[63] = { lvl = 1, max = 1, dark = true }
    ownedSets.twelve, ownedSets.twenty, ownedSets.weird = twelve, twenty, weird

    for _, cls in ipairs({ 0, 1, 2, 3, 4, 5 }) do   -- 5 = a stale id (the retired class's): every lookup must stay nil-safe
        for _, tier in ipairs({ 1, 2, 3 }) do
            for setName, owned in pairs(ownedSets) do
                CoD.TodOwned = owned or nil; CoD.TodClass = cls; CoD.TodClassTier = tier
                subs, handlers, btncbs = {}, {}, {}
                local label = string.format('class %d tier %d rows %s', cls, tier, setName)
                local menu
                try(label .. ' construct', function() menu = LUI.createMenu.StartMenu_Main(0) end)
                if menu then
                    for _, s in ipairs(subs) do
                        local numeric = tostring(s.model):find('gameScore', 1, true) or tostring(s.model):find('time', 1, true)
                        for _, v in ipairs(VALUES) do
                            if numeric and type(v) ~= 'number' then v = 7 end
                            MODELVAL = v
                            try(label .. ' sub ' .. tostring(s.model) .. ' = ' .. tostring(v), s.fn, s.model)
                        end
                        MODELVAL = nil
                        try(label .. ' sub ' .. tostring(s.model) .. ' = nil', s.fn, s.model)
                    end
                    MODELVAL = 0
                    for _, h in ipairs(handlers) do
                        try(label .. ' handler ' .. h.name, h.fn, h.el, { name = h.name, controller = 0, button = 'down', menu = menu })
                    end
                    for _, b in ipairs(btncbs) do
                        try(label .. ' button cb', b.fn, b.el, menu, 0, 'model')
                    end
                    for dsName, ds in pairs(DataSources) do
                        local items
                        try(label .. ' datasource ' .. dsName, function() items = ds.__build(0) end)
                        for i, it in ipairs(items or {}) do
                            if type(it.properties) == 'table' and type(it.properties.action) == 'function' then
                                local nm = it.models and (it.models.displayText or it.models.icon) or i
                                if not tostring(nm):lower():find('quit') and not tostring(nm):lower():find('restart') and not tostring(nm):lower():find('leave') then
                                    try(label .. ' action ' .. dsName .. ' ' .. tostring(nm), it.properties.action, menu, menu, 0, nil, menu)
                                end
                            end
                        end
                    end
                    for dsName, ds in pairs(DataSources) do
                        local its; try(label .. ' ds2 ' .. dsName, function() its = ds.__build(0) end)
                        for i, it in ipairs(its or {}) do
                            local mo = it.models or {}
                            local nm = tostring(mo.displayText or mo.icon or i):lower()
                            if type(mo.action) == 'function' and not nm:find('quit') and not nm:find('restart') and not nm:find('leave') and not nm:find('end game') then
                                try(label .. ' models.action ' .. dsName .. ' ' .. nm, mo.action, menu, menu, 0, nil, menu)
                                for d2, ds2 in pairs(DataSources) do try(label .. ' after ' .. nm .. ' rebuild ' .. d2, function() ds2.__build(0) end) end
                            end
                        end
                    end
                    for dsName, ds in pairs(DataSources) do try(label .. ' rebuild ' .. dsName, function() ds.__build(0) end) end
                    try(label .. ' close', function() menu:close() end)
                end
                elements = {}
            end
        end
    end
    return fails, runs
end

local fails, runs = RUN(SRC_NOW)
if #fails > 0 then
    local seen, uniq = {}, {}
    for _, m in ipairs(fails) do local k = m:gsub('^class %d tier %d rows %w+ ', '') if not seen[k] then seen[k] = true; uniq[#uniq + 1] = m end end
    print(#fails .. ' failures in ' .. runs .. ' runs; ' .. #uniq .. ' distinct:')
    for i = 1, math.min(#uniq, 40) do print('  ' .. uniq[i]) end
    error('pause menu runtime harness FAILED')
end

-- NEGATIVE CONTROL: the build-15b settings-page call, restored verbatim.
local OLD_A = "if USE_PAUSE_V2 and TodV2Settings[ controller ] and TodOptionsBuild then"
local OLD_B = "return TodOptionsBuild( controller )"
local s15 = SRC_NOW
local na, nb
s15, na = s15:gsub(OLD_A:gsub('%p', '%%%0'), ("if USE_PAUSE_V2 and TodV2Settings[ controller ] and DataSources.AetheriumOptionsButtons then"):gsub('%%', '%%%%'), 1)
s15, nb = s15:gsub(OLD_B:gsub('%p', '%%%0'), ("return DataSources.AetheriumOptionsButtons( controller )"):gsub('%%', '%%%%'), 1)
assert(na == 1 and nb == 1, 'negative control: the fixed lines moved; update OLD_A / OLD_B')
local oldFails = RUN(s15)
local caught = false
for _, m in ipairs(oldFails) do if m:find('attempt to call', 1, true) and m:find('table', 1, true) then caught = true; break end end
assert(caught, 'negative control FAILED: the build-15b settings call no longer errors under this mock')
print('pause menu runtime harness passed: ' .. runs .. ' runs clean; negative control: the build-15b settings call fails (' .. #oldFails .. ' failures)')
