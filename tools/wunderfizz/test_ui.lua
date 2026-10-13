-- Execute the installed menu with engine-shaped LUI mocks under Lua 5.1.
-- Checks quote ordering, per-controller replies, click/keyboard input and ownership.
local noop = function() end
local elements, callbacks, replies, freed, locks, active = {}, {}, {}, {}, {}, {}
local methods = {}
local function newElement()
    local el = setmetatable({children = {}, handlers = {}, alpha = 1}, {__index = function(_, k)
        if methods[k] then return methods[k] end
        if k:match('^set') or k:match('^make') then return noop end
    end})
    elements[#elements + 1] = el
    return el
end
function methods:addElement(child) self.children[#self.children + 1] = child; child.parent = self end
function methods:getFirstChild() return self.children[1] end
function methods:getNextSibling()
    if not self.parent then return end
    for i, child in ipairs(self.parent.children) do if child == self then return self.parent.children[i + 1] end end
end
function methods:close()
    assert(not self.closed, 'double close')
    self.closed = true
    if self.parent then
        for i, child in ipairs(self.parent.children) do if child == self then table.remove(self.parent.children, i); break end end
        self.parent = nil
    end
end
function methods:setAlpha(v) self.alpha = v end
function methods:setText(v) self.text = v end
function methods:setRGB(r,g,b) self.rgb = {r,g,b} end
function methods:setImage(v) self.image = v end
function methods:setLeftRight(a,b,l,r) self.lr = {l,r} end
function methods:setTopBottom(a,b,t,bt) self.tb = {t,bt} end
function methods:setOwner(v) self.owner = v end
function methods:makeFocusable() self.m_focusable = true end
function methods:setHandleMouse(v) self.handleMouseMove, self.handleMouseButton = v, v end
function methods:isVisible() return not self.closed and self.alpha > 0 end
function methods:hasClip() return false end
function methods:dispatchEventToChildren(event)
    for _, el in ipairs(self.children) do if el:processEvent(event) then return true end end
end
function methods:registerEventHandler(name, fn) self.handlers[name] = fn end
function methods:processEvent(event)
    if self.handlers[event.name] then return self.handlers[event.name](self,event) end
    if event.name == 'mousedown' or event.name == 'mouseup' then return LUI.UIElement.MouseButtonEvent(self,event) end
    return self:dispatchEventToChildren(event)
end
function methods:playSound(s) self.lastSound = s end
function methods:subscribeToGlobalModel(c,a,b,fn) self.notify = fn end
function methods:AddButtonCallbackFunction(el,c,key,keyboard,fn)
    self.buttons = self.buttons or {}; self.buttons[key] = fn
    self.keyboards = self.keyboards or {}; if keyboard then self.keyboards[keyboard] = fn end
    assert(el == self and c == self.owner, 'callbacks stay on native menu focus owner')
end
CoD = {Menu = {NewForUIEditor = newElement, SetButtonLabel = noop}, GetScriptNotifyData = function(m) return m.data end}
LUI = {UIElement = {new = newElement}, UIImage = {new = newElement}, UIText = {new = newElement}, createMenu = {}}
function LUI.UIElement.IsMouseInsideElement(el,event)
    local x,y = event.x,event.y
    if not x or not y then return false end
    local lr,tb = el.lr or {0,1280},el.tb or {0,720}
    return x >= lr[1] and x <= lr[2] and y >= tb[1] and y <= tb[2],x,y
end
function LUI.OverrideFunction_CallOriginalSecond(el,key,fn)
    local old = el[key]; el[key] = function(...) fn(...); return old(...) end
end
Engine = {
    GetModelForController = function(c) return 'ctrl' .. c end,
    CreateModel = function(m,k) return m .. '.' .. k end,
    UnsubscribeAndFreeModel = function(m) freed[#freed + 1] = m end,
    GetModelValue = function(m) return m.name end,
    SendMenuResponse = function(c,m,r) replies[#replies + 1] = {c,m,r} end,
    LockInput = function(c,v) locks[c] = v end,
    SetUIActive = function(c,v) active[c] = v end,
}
Enum = {LUIButton = {LUI_KEY_UP = 1,LUI_KEY_DOWN = 2,LUI_KEY_XBA_PSCROSS = 3,LUI_KEY_XBB_PSCIRCLE = 4,LUI_KEY_NONE = 5},
    LUIAlignment = {LUI_ALIGNMENT_LEFT = 0,LUI_ALIGNMENT_RIGHT = 1,LUI_ALIGNMENT_CENTER = 2}}
require = noop
function RegisterImage(s) return s end
-- Execute stock's actual dispatch function, including its unusual handler
-- receiver table and inside=false release event. Do not mimic that edge case.
local f = assert(io.open('tmp/wunderfizz/ui/stock/LUIElement.lua','r'))
local native = f:read('*a'); f:close()
local first = assert(native:find('LUI.UIElement.MouseButtonEvent = function',1,true))
local after = assert(native:find('LUI.UIElement.AcceptGamePadButtonInput = function',first,true))
assert(loadstring(native:sub(first,after-1)))()
local originalNew = newElement
newElement = function()
    local el = originalNew()
    el.m_eventHandlers = el.handlers
    el.handlers.leftmousedown = noop
    return el
end
LUI.UIElement.new, LUI.UIImage.new, LUI.UIText.new = newElement,newElement,newElement
CoD.Menu.NewForUIEditor = function()
    local el = newElement()
    el.updateBlur = function(owner) Engine.LockInput(owner.owner,false); Engine.SetUIActive(owner.owner,false) end
    return el
end
dofile('ui/uieditor/widgets/HUD/AetheriumWidgets/TodUIOwnership.lua')
dofile('ui/uieditor/widgets/HUD/AetheriumWidgets/TodHudVeil.lua')
dofile('ui/uieditor/menus/hud/tod_wunderfizz.lua')
local checks = 0
local function check(v,msg) assert(v,msg); checks = checks + 1 end
local function drive(menu,event,data) menu.notify({name = event,data = data}) end
local function textOf(menu,s)
    local function find(owner)
        for _, el in ipairs(owner.children) do if el.text == s then return el end; local hit = find(el); if hit then return hit end end
    end
    return find(menu)
end
local function live() local n=0; for _, el in ipairs(elements) do if not el.closed then n=n+1 end end; return n end
local menu = LUI.createMenu.tod_wunderfizz(2)
menu:processEvent({name='menu_opened',controller=2})
check(menu.m_focusable and locks[2] and active[2], 'native root focus and interactive route activate on engine menu_opened')
check(menu.keyboards.UPARROW and menu.keyboards.DOWNARROW and menu.keyboards.ENTER and menu.keyboards.ESCAPE, 'stock keyboard names registered alongside pad callbacks')
check(textOf(menu,'CONNECTING') ~= nil,'late hydration shows connecting')
menu.buttons[3]()
check(#replies == 0,'no buy before a server quote')
drive(menu,'unrelated',{9,50,2000,0,511})
drive(menu,'tod_wf_state',{1,50,2000,0})
check(textOf(menu,'$2000') == nil,'unrelated and malformed events ignored')
drive(menu,'tod_wf_state',{1,50,2000,0,511})
check(textOf(menu,'$2000') ~= nil and textOf(menu,'FLOOR 50') ~= nil,'complete quote hydrates')
menu.keyboards.UPARROW()
check(textOf(menu,'NO FALL OR SELF-BLAST DAMAGE') ~= nil,'up wraps to PhD')
menu.keyboards.DOWNARROW()
menu.keyboards.ENTER()
check(replies[1][1] == 2 and replies[1][2] == 'tod_wunderfizz' and replies[1][3] == 'buy.1.1','reply includes only own quote and perk ID')
menu.buttons[3]()
check(#replies == 1 and textOf(menu,'PLEASE WAIT') ~= nil,'confirm cannot repeat while pending')
drive(menu,'tod_wf_state',{1,50,2000,0,511})
menu.keyboards.ENTER()
check(#replies == 1 and textOf(menu,'PLEASE WAIT') ~= nil,'same-quote heartbeat preserves pending and cannot repeat confirm')
drive(menu,'tod_wf_result',{1,1})
check(textOf(menu,'NOT ENOUGH POINTS') ~= nil,'server denial feedback visible')
drive(menu,'tod_wf_state',{1,50,2000,0,511})
check(textOf(menu,'NOT ENOUGH POINTS') ~= nil,'heartbeat does not erase denial')
drive(menu,'tod_wf_state',{2,50,2500,1,510})
menu.buttons[3]()
check(#replies == 1 and textOf(menu,'ALREADY OWNED') ~= nil,'owned perk cannot submit')
drive(menu,'tod_wf_state',{1,50,2000,0,511})
check(textOf(menu,'$2500') ~= nil,'older quote cannot overwrite price or ownership')
menu.buttons[2]()
menu.buttons[3]()
check(replies[2][3] == 'buy.2.2','new buy uses latest quote')
drive(menu,'tod_wf_state',{3,50,6500,511,0})
check(textOf(menu,'ALL PERKS OWNED') ~= nil,'all owned state')
menu.buttons[3]()
check(#replies == 2,'all owned sends no buy')
drive(menu,'tod_wf_close',{2})
check(not menu.closed,'stale close ignored')
drive(menu,'tod_wf_close',{3})
check(menu.closed and not CoD.TodHudVeil.Hidden(),'server close releases menu and veil')
check(live() == 0 and #freed == 1,'all children and button model freed')
check(locks[2] == false and active[2] == false,'close releases owned interactive controller route')
menu:close()
check(#freed == 1,'engine close after notify is idempotent')
for pass = 1, 25 do
    local m = LUI.createMenu.tod_wunderfizz(pass % 4)
    m:processEvent({name='menu_opened',controller=pass % 4})
    drive(m,'tod_wf_state',{pass + 10,pass,2000,0,511})
    local count = #elements
    for heartbeat = 1, 20 do drive(m,'tod_wf_state',{pass + 10,pass,2000,0,511}) end
    check(#elements == count,'heartbeats create no elements')
    for _, el in ipairs(m.children) do
        if el.handlers.mousemove then
            check(not el.m_focusable, 'rows retain sole native menu focus owner')
            local e = {controller=pass % 4,rootName='UIRoot',x=300,y=195,button='left'}
            e.name='mousemove'; el:processEvent(e)
            e.name='mousedown'; el:processEvent(e)
            e.name='mouseup'; el:processEvent(e)
            break
        end
    end
    check(replies[#replies][3] == 'buy.' .. (pass + 10) .. '.1','mouse selection confirms row')
    m.buttons[5]()
    check(replies[#replies][3] == 'close.' .. (pass + 10),'escape closes owned quote')
    m:close()
    check(live() == 0 and not CoD.TodHudVeil.Hidden(),'repeated visits leak nothing')
end
local m = LUI.createMenu.tod_wunderfizz(0)
m:processEvent({name='menu_opened',controller=0})
drive(m,'tod_wf_state',{100,10,2000,0,511})
local row
for _,el in ipairs(m.children) do if el.handlers.mousemove and el.tb[1] == 266 then row=el; break end end
local n = #replies
row:processEvent({name='mousemove',controller=0,rootName='UIRoot',x=300,y=280})
check(textOf(m,'THREE PAID SOLO USES') ~= nil,'raw native mouse movement selects Quick Revive without focus clips')
row:processEvent({name='mousedown',controller=0,rootName='UIRoot',x=300,y=280,button='left'})
row:processEvent({name='mouseup',controller=0,rootName='UIRoot',x=900,y=280,button='left'})
check(#replies == n,'native press-inside/release-outside cannot buy')
row:processEvent({name='mouseup',controller=0,rootName='UIRoot',x=300,y=280,button='left'})
check(#replies == n,'release without a matching pressed row cannot buy')
row:processEvent({name='mousedown',controller=1,rootName='UIRoot',x=300,y=280,button='left'})
row:processEvent({name='mouseup',controller=1,rootName='UIRoot',x=300,y=280,button='left'})
check(#replies == n,'another controller mouse event cannot submit a purchase')
m.occludedBy = {menuName='native_popup'}
row:processEvent({name='mousedown',controller=0,rootName='UIRoot',x=300,y=280,button='left'})
row:processEvent({name='mouseup',controller=0,rootName='UIRoot',x=300,y=280,button='left'})
check(#replies == n,'occluded menu cannot buy through native popup')
m.occludedBy = nil
m:updateBlur()
check(locks[0] and active[0],'native unocclusion preserves selector interaction')
CoD.TodPad=true; drive(m,'tod_wf_state',{100,10,2000,0,511})
check(textOf(m,'D-PAD SELECT    A BUY    B CLOSE') ~= nil,'footer uses established server pad latch')
CoD.TodPad=false; CoD.TodKeycap={PadDevice=function() return true end}; drive(m,'tod_wf_state',{100,10,2000,0,511})
check(textOf(m,'D-PAD SELECT    A BUY    B CLOSE') ~= nil,'footer uses established keycap device read')
CoD.TodKeycap.PadDevice=function() return false end; drive(m,'tod_wf_state',{100,10,2000,0,511})
check(textOf(m,'ARROWS SELECT    ENTER BUY    ESC CLOSE') ~= nil,'keyboard device footer remains readable')
row:processEvent({name='mousedown',controller=0,rootName='UIRoot',x=300,y=280,button='left'})
row:processEvent({name='mouseup',controller=0,rootName='UIRoot',x=300,y=280,button='left'})
check(replies[#replies][3] == 'buy.100.3','stock mouse dispatcher confirms the hovered roster ID')
m:close()
check(live() == 0 and not locks[0] and not active[0],'native mouse visit frees all UI and owned input')
print('Wunderfizz UI passed: ' .. checks .. ' checks; late hydration, quote ordering, input, denials and 25 clean visits.')
