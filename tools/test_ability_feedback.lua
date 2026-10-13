-- tools/test_ability_feedback.lua - THE TILES REACT (docs/203, 2026-10-02): the actual
-- TodAbilityFeedback.lua under Lua 5.1 with mocked elements. The kit path (every live
-- class): ready flash on the not-ready -> ready edge only, cast pulse on ready -> active /
-- cd, the recharge frame from an INFERRED total, locked / empty never pulse, KitOff clears.
-- Run: python -B tools/run_lua_harness.py tools/test_ability_feedback.lua
CoD = { TweenType = { Linear = 0 } }
local function element()
    local e = { children = {}, anims = 0 }
    function e:setAlpha(a) self.alpha = a end
    function e:setLeftRight(_, __, a, b) self.x1, self.x2 = a, b end
    function e:setTopBottom(_, __, a, b) self.y1, self.y2 = a, b end
    function e:setRGB(...) self.color = { ... } end
    function e:setImage(i) self.image = i end
    function e:addElement(child) self.children[#self.children + 1] = child end
    function e:completeAnimation() self.completed = (self.completed or 0) + 1 end
    function e:beginAnimation(name, ms) self.animation, self.ms = name, ms; self.anims = self.anims + 1; self.alphaAtBegin = self.alpha; self.x1AtBegin, self.y1AtBegin, self.x2AtBegin = self.x1, self.y1, self.x2 end
    return e
end
LUI = { UIImage = { new = element } }
RegisterImage = function(s) return s end
dofile('ui/uieditor/widgets/HUD/AetheriumWidgets/TodAbilityFeedback.lua')
local F = CoD.TodAbilityFeedback
local checks = 0
local function ok(v, m) assert(v, m); checks = checks + 1 end

-- ---- the kit path -----------------------------------------------------------------------
local w = element(); F.Attach(w, 4)
ok(w.todKitX[1] == 1164 and w.todKitX[2] == 1214, 'slot x follows HUD_DX (tactical 1160, lethal 1210)')
local flash, cast = w.todKitFlash, w.todKitCast
local frame = w.todKitFrames
local function fills(slot) local n = 0; for _, f in ipairs(frame[slot].fills) do if f.alpha > 0 then n = n + 1 end end return n end

-- first sight of a READY tile: no flash (nothing became ready, it was ready at join)
F.Kit(w, 2, 'ready', 0)
ok(flash[2].anims == 0, 'a tile first seen ready does not flash')
-- cast: ready -> cd = the cast pulse, the total is the first value seen
F.Kit(w, 2, 'cd', 12); ok(cast[2].anims == 1 and cast[2].animation == 'tod_abfx_cast', 'ready -> cd is a cast pulse')
ok(cast[2].alphaAtBegin == 0.7 and cast[2].x1AtBegin == 1214 - 2 and cast[2].x2AtBegin == 1214 + 46 + 2, 'the cast pulse starts grown ...')
ok(cast[2].x1 == 1214 and cast[2].x2 == 1214 + 46 and cast[2].alpha == 0, '... and tweens back onto the tile, to nothing')
ok(fills(2) == 0, '12 of 12 left: an empty frame')
F.Kit(w, 2, 'cd', 6); ok(fills(2) >= 2, 'half way: the frame half full (inferred total 12)')
F.Kit(w, 2, 'cd', 1); ok(fills(2) == 4, 'nearly back: every edge lit')
-- back to READY: the flash, once
F.Kit(w, 2, 'ready', 0); ok(flash[2].anims == 1 and flash[2].animation == 'tod_abfx_flash' and flash[2].alphaAtBegin == 0.85, 'cd -> ready flashes')
ok(flash[2].x1AtBegin == 1214 - 4 and flash[2].y1AtBegin == 568 - 4 and flash[2].x1 == 1214, 'the flash blooms from a grown tile and settles')
ok(fills(2) == 0 and frame[2].tracks[1].alpha == 0, 'ready: no frame')
F.Kit(w, 2, 'ready', 0); F.Kit(w, 2, 'ready', 0)
ok(flash[2].anims == 1, 'a repeated ready update never re-flashes (the 2 s HUD refresh)')
-- a value that CLIMBS re-bases the total (a second charge spent, a bigger bar)
F.Kit(w, 2, 'cd', 5); F.Kit(w, 2, 'cd', 9)
ok(w.todKit[2].total == 9, 'a climbing value becomes the new total')
-- ready -> active (Bash busy, the cloak on) = the cast pulse; active -> cd = no second pulse
F.Kit(w, 1, 'ready', 0); F.Kit(w, 1, 'active', -1)
ok(cast[1].anims == 1, 'ready -> active is a cast')
F.Kit(w, 1, 'cd', 20); ok(cast[1].anims == 1, 'active -> cd does not pulse again')
ok(w.todKit[1].total == 20, 'the total starts fresh after an active window')
-- locked / empty never pulse, never frame
F.Kit(w, 1, 'locked', -2); F.Kit(w, 1, 'locked', -2)
ok(cast[1].anims == 1 and flash[1].anims == 0 and fills(1) == 0, 'locked: nothing')
F.Kit(w, 1, 'ready', 0); ok(flash[1].anims == 1, 'locked -> ready flashes (the card just landed)')
F.Kit(w, 1, 'empty', 0); ok(fills(1) == 0 and cast[1].anims == 1, 'empty (no charges, no clock): no frame, no pulse')
F.Kit(w, 1, 'ready', 0); ok(flash[1].anims == 2, 'empty -> ready flashes (a charge came back)')
-- KitOff clears every overlay and frame and forgets the history
F.Kit(w, 2, 'cd', 3)
F.KitOff(w)
for s = 1, 2 do
    ok(flash[s].alpha == 0 and cast[s].alpha == 0 and fills(s) == 0, 'KitOff: slot ' .. s .. ' dark')
    ok(w.todKit[s].prev == nil, 'KitOff forgets the previous state')
end
F.Kit(w, 2, 'ready', 0); ok(flash[2].anims == 1, 'after KitOff a ready tile is a first sight again: no flash')
-- PK18 (2026-10-05): THE REFUSED PRESS - a red snap on the pressed tile, nothing else moves
local w2 = element(); F.Attach(w2, 0)
local deny = w2.todKitDeny
ok(deny and deny[1] and deny[2] and deny[1].color[1] == 1 and deny[1].color[2] < 0.3, 'Attach makes a red overlay per tile')
F.Kit(w2, 1, 'cd', 8)
local before = w2.todKit[1].prev
F.Refused(w2, 1)
ok(deny[1].anims == 1 and deny[1].animation == 'tod_abfx_deny' and deny[1].alphaAtBegin == 0.8, 'a refused press snaps the tactical tile red')
ok(deny[1].x1AtBegin == 1160 - 2 and deny[1].x1 == 1160 and deny[1].alpha == 0, 'the snap tightens onto the tile, to nothing')
ok(deny[2].anims == 0, 'only the pressed tile reacts')
ok(w2.todKit[1].prev == before and w2.todKitFlash[1].anims == 0 and w2.todKitCast[1].anims == 0, 'a refusal changes no state and plays no ready / cast pulse')
F.Refused(w2, 2); ok(deny[2].anims == 1, 'the lethal tile snaps on its own refusal')
F.Refused(w2, 3); F.Refused(w2, nil); ok(true, 'an unknown slot is ignored')
F.KitOff(w2); ok(deny[1].alpha == 0 and deny[2].alpha == 0 and deny[1].completed >= 1, 'KitOff clears the red overlays too')
F.Refused({}, 1); ok(true, 'a widget without Attach tolerates a refusal')
local loadout2 = io.open('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua'):read('*a')
ok(loadout2:find('name == "tod_kit_deny"', 1, true) and loadout2:find('CoD.TodAbilityFeedback.Refused( self, d[1] )', 1, true), 'the loadout routes tod_kit_deny to Refused')
local gsc = io.open('scripts/zm/zm_tod2_cybercity/_tod_ability_fx.gsc'):read('*a')
ok(gsc:find('#precache( "eventstring", "tod_kit_deny" )', 1, true) and gsc:find('LuiNotifyEvent( &"tod_kit_deny", 1, slot )', 1, true), 'the server precaches and sends tod_kit_deny with one value')
-- NEGATIVE CONTROL: the shipped feedback before PK18 had no refusal at all (the Mage-only Blocked was retired)
ok(not io.open('ui/uieditor/widgets/HUD/AetheriumWidgets/TodAbilityFeedback.lua'):read('*a'):find('function Feedback.Blocked', 1, true), 'the retired Mage-only Blocked stays retired')
-- a widget without Attach (a bare table) never throws
local bare = {}
F.Kit(bare, 1, 'ready', 0); F.KitOff(bare)
ok(true, 'bare widget tolerated')
-- NEGATIVE CONTROL: the kit path ships in the widget, and its hook lives in the loadout
local old = io.open('ui/uieditor/widgets/HUD/AetheriumWidgets/TodAbilityFeedback.lua'):read('*a')
ok(old:find('function Feedback.Kit', 1, true) and old:find('function Feedback.KitOff', 1, true), 'the kit path ships')
ok(old:find('CoD.TodAbilityFeedback.Kit( self, i, kstate, kval )', 1, true) == nil, 'the hook lives in the loadout, not here')
local loadout = io.open('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua'):read('*a')
ok(loadout:find('CoD.TodAbilityFeedback.Kit( self, i, kstate, kval )', 1, true), 'the loadout calls Kit per slot')
ok(loadout:find('CoD.TodAbilityFeedback.KitOff( self )', 1, true), 'the loadout calls KitOff when the kit view leaves')
print('ABILITY FEEDBACK passed: ' .. checks .. ' checks (ready flash edge, cast pulse, inferred recharge frame, locked/empty silent, KitOff, loadout hooks).')
