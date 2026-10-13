-- tools/test_health_tint.lua - the actual TodHealthTint.lua under Lua 5.1 with mocked elements
-- (trimmed 2026-10-04 from the retired class's tint test, which archived with it): the tint is
-- white at rest and red while downed, the HAVEN BLEED MASK sets the bleed-out bar's duration per
-- player and never repaints, a roster rebind never leaks a subscription, the fill's own
-- health / bleedout animation is never touched, and close releases everything once.
-- Run: python -B tools/run_lua_harness.py tools/test_health_tint.lua   (native rendering still needs BO3)
CoD = { TweenType = { Linear = 0 } }
Engine = { GetModelValue = function(m) return m.value end }
CoD.GetScriptNotifyData = function(m) return m.data end
LUI = { UIElement = {} }
local function element()
    local e = { handlers = {}, animations = 0, completed = 0, children = {} }
    function e:setLeftRight(...) self.left = {...} end
    function e:setTopBottom(...) self.top = {...} end
    function e:setRGB(r,g,b) self.rgb = {r,g,b} end
    function e:addElement(child) self.children[#self.children+1] = child; child.parent=self end
    function e:getFirstChild() return self.children[1] end
    function e:getNextSibling()
        if not self.parent then return nil end
        for i,c in ipairs(self.parent.children) do if c==self then return self.parent.children[i+1] end end
    end
    function e:registerEventHandler(name, fn) self.handlers[name] = fn end
    function e:beginAnimation(...) self.animations = self.animations + 1 end
    function e:completeAnimation() self.completed = self.completed + 1 end
    function e:close()
        assert(not self.closed, 'double close')
        self.closed = true
        if self.parent then
            for i,c in ipairs(self.parent.children) do if c==self then table.remove(self.parent.children,i); break end end
            self.parent=nil
        end
    end
    function e:linkToElementModel(_, _, _, fn) self.bind = fn end
    function e:subscribeToGlobalModel(controller, _, _, fn)
        self.controller = controller; self.receive = fn; self.subs = (self.subs or 0) + 1
    end
    return e
end
LUI.UIElement.new = element
LUI.OverrideFunction_CallOriginalSecond = function(e, name, fn)
    local old = e[name]
    e[name] = function(self) fn(self); old(self) end
end
dofile('ui/uieditor/widgets/HUD/AetheriumWidgets/TodHealthTint.lua')
local function widget(controller, id, isLocal)
    local w = element(); w.health_fill = element(); w.currentPlayerState = 0
    CoD.TodHealthTint.Attach(w, controller, isLocal)
    w.bind({value=id}); return w
end
local function white(w) local c = w.health_tint.rgb; return c and c[1]==1 and c[2]==1 and c[3]==1 end
local checks = 0
local function ok(v, m) assert(v, m); checks = checks + 1 end

-- AT REST: white, for every controller / player pairing, and the fill is never animated
for controller=0,3 do
    for id=0,3 do
        local w=widget(controller,id,id==controller)
        ok(w.todHealthMode=='normal' and white(w), 'a fresh bar is white (normal)')
        ok(w.health_fill.animations==0 and w.health_fill.completed==0, 'the health animation was changed')
        w:close()
        ok(w.health_fill.closed and w.health_tint.closed, 'closing the tint must also close the remaining fill')
    end
end

-- A RETIRED EVENT CHANGES NOTHING: no server sends tod_arch_bars any more; a stale one is ignored
do
    local w=widget(0,1,false); local rgb=table.concat(w.health_tint.rgb,','); local anims=w.health_tint.animations
    w.receive({value='tod_arch_bars',data={2}})
    ok(w.todHealthMode=='normal' and table.concat(w.health_tint.rgb,',')==rgb and w.health_tint.animations==anims,
       'a tod_arch_bars notify must not repaint or animate the bar')
    w:close()
end

-- DOWN IS RED, REVIVED IS WHITE AGAIN
local w=widget(0,1,false)
w.currentPlayerState=1; CoD.TodHealthTint.Paint(w)
ok(w.todHealthMode=='down', 'a downed player paints down')
local c=w.health_tint.rgb; ok(c[1]==1 and c[2]==0.2 and c[3]==0.2, 'down is red')
w.currentPlayerState=0; CoD.TodHealthTint.Paint(w)
ok(w.todHealthMode=='normal' and white(w), 'revived returns to white')
local done=w.health_tint.completed; CoD.TodHealthTint.Paint(w)
ok(w.health_tint.completed==done, 'an unchanged mode never repaints')

-- ROSTER REBIND: one subscription per widget lifetime
for i=1,20 do w.bind({value=i%4}) end
ok(w.subs==1, 'roster rebinding leaked subscriptions')

-- THE HAVEN BLEED MASK (docs/202 v3, tweak #3): the bar's duration follows the server's mask, per player
local function bleed(b, mask) b.receive({value='tod_haven_bleed',data={mask}}) end
for mask=0,15 do
    for id=0,3 do
        local b=widget(0,id,id==0); local before=b.todHealthMode; bleed(b,mask)
        local expected=math.floor(mask/2^id)%2==1
        ok(CoD.TodHealthTint.BleedoutMs(b,30000)==(expected and 45000 or 30000),'bleed bar duration wrong for mask '..mask..' id '..id)
        ok(b.todHealthMode==before,'the bleed mask must never repaint the tint')
        b:close()
    end
end
local nb=widget(0,2,false); ok(CoD.TodHealthTint.BleedoutMs(nb,30000)==30000,'no mask = stock duration')
nb.receive({value='tod_haven_bleed',data={'x'}}); ok(CoD.TodHealthTint.BleedoutMs(nb,30000)==30000,'a non-number mask is ignored')
nb:close()

-- CLOSE: once, everything released, a later paint does nothing
local mode=w.todHealthMode; w:close()
ok(w.health_tint.closed and w.health_fill.closed, 'close releases the tint and the fill')
w.currentPlayerState=1; CoD.TodHealthTint.Paint(w)
ok(w.todHealthMode==mode, 'a closed widget never repaints')
ok(w.health_fill.animations==0 and w.health_fill.completed==0,'health/bleedout animation was touched')
print('Health tint passed: '..checks..' checks (white at rest, down red, revive white, a retired notify ignored, rebind, haven bleed mask, cleanup).')
