-- Actual Lua 5.1 UI helpers with mocked elements/models; no screenshot claims.
CoD = { TweenType = { Linear = 0 } }
Enum = { LUIAlignment = { LUI_ALIGNMENT_LEFT = 0 } }
local function element()
    local e = { children = {} }
    function e:setAlpha(a) self.alpha=a end
    function e:setLeftRight(_,__,a,b) self.x1,self.x2=a,b end
    function e:setTopBottom(_,__,a,b) self.y1,self.y2=a,b end
    function e:setRGB(...) self.color={...} end
    function e:setText(t) self.text=t end
    function e:setImage(i) self.image=i end
    function e:setTTF(t) end
    function e:setAlignment(a) end
    function e:addElement(child) self.children[#self.children+1]=child end
    function e:completeAnimation() self.completed=true end
    function e:beginAnimation(name,ms) self.animation,self.ms=name,ms end
    function e:subscribeToModel(_,f) self.model=f end
    function e:subscribeToGlobalModel(_,__,___,f) self.notify=f end
    return e
end
LUI={UIImage={new=element},UIText={new=element}}
RegisterImage=function(s) return s end
Engine={GetModelForController=function(c) return c end,GetModel=function(_,s) return s end,GetModelValue=function(v) return v end}
local data
CoD.GetScriptNotifyData=function() return data end
dofile('ui/uieditor/widgets/HUD/ZM_CursorHint/Prompts/TodTeleportFeedback.lua')
local p=element();CoD.TodTeleportFeedback.Attach(p,0)
local label,track,fill=p.children[1],p.children[2],p.children[3]
local function notify(s,pct) data={s,pct};track.notify('tod_tp_recharge') end
label.model('^5TELEPORTER^7 - ^1recharging...');notify(30,50)
assert(label.alpha==1 and label.text=='Ready in 30s' and fill.x2==693.5)
label.model('^5AMMO CRATE^7 - buy ammo');assert(label.alpha==0 and fill.alpha==0)
label.model('^5TELEPORTER^7 - power required');assert(label.alpha==0)
label.model('^5TELEPORTER^7 - destination locked');assert(label.alpha==0)
label.model('^5TELEPORTER^7 - recharging...');notify(1,98);assert(label.text=='Ready in 1s')
notify(0,0);assert(label.alpha==0 and track.alpha==0)
notify(10,75);label.model('');assert(label.alpha==0)
print('Player feedback Lua: teleporter prompt/countdown visibility passes.')
