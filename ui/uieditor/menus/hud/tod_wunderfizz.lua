-- Staged BO6 Wunderfizz selector. Not zoned or loaded by the shipping map.
-- Server quote: tod_wf_state(seq, floor, cost, ownedMask, availableMask).
-- Replies carry only a quote and roster ID; the server owns every decision.
require("ui.uieditor.widgets.HUD.AetheriumWidgets.TodUIOwnership")
pcall(require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodGlyphText")
pcall(require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodHudVeil")
pcall(require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodKeycap")

local ROSTER = {
    {"JUGGER-NOG", "i_tod_perk_jugg", {"RAISE YOUR MAXIMUM HEALTH", "AND WITHSTAND MORE DAMAGE"}},
    {"SPEED COLA", "i_tod_perk_speed", {"RELOAD YOUR WEAPONS", "SIGNIFICANTLY FASTER"}},
    {"QUICK REVIVE", "i_tod_perk_revive", {"FASTER REVIVES IN CO-OP", "SELF-REVIVE IN SOLO", "THREE PAID SOLO USES"}},
    {"STAMIN-UP", "i_tod_perk_staminup", {"SPRINT FASTER", "AND FOR LONGER"}},
    {"WIDOW'S WINE", "i_tod_perk_widows", {"MELEE AND GRENADE HITS", "SLOW AND WEB ZOMBIES"}},
    {"DEATH PERCEPTION", "i_tod_perk_deathperception", {"SENSE THE HORDE", "THROUGH WALLS"}},
    {"DOUBLE TAP", "i_tod_perk_doubletap", {"YOUR BULLETS", "DEAL DOUBLE DAMAGE"}},
    {"WISP TEA", "i_tod_perk_wisptea", {"HITS MAY SUMMON", "A BOSS-HUNTING WISP", "TWO WISPS MAXIMUM"}},
    {"PHD FLOPPER", "i_tod_perk_phd", {"NO FALL OR SELF-BLAST DAMAGE", "EXPLODE WHEN DOWNED", "YOUR FRAGS BLAST LIKE FLOPS"}},
}
local WHITE = {0.86, 0.90, 0.95}
local DIM = {0.55, 0.62, 0.70}
local RED = {0.95, 0.13, 0.23}
local GOLD = {1.00, 0.84, 0.46}

local function has(mask, id)
    return math.floor(mask / (2 ^ (id - 1))) % 2 == 1
end
local function integer(v, lo, hi)
    return type(v) == "number" and v == math.floor(v) and v >= lo and v <= hi
end

LUI.createMenu.tod_wunderfizz = function(controller)
    local self = CoD.Menu.NewForUIEditor("tod_wunderfizz")
    CoD.TodUIOwnership.Attach(self)
    self:setOwner(controller)
    self:setLeftRight(true, true, 0, 0)
    self:setTopBottom(true, true, 0, 0)
    self:makeFocusable()
    self.soundSet = "default"
    self.buttonModel = Engine.CreateModel(Engine.GetModelForController(controller), "tod_wunderfizz.buttonPrompts")
    local st = {seq = 0, floor = 0, cost = 0, owned = 0, available = 0, focus = 1, pending = false, closed = false, result = ""}
    local veilKey = "wunderfizz_" .. tostring(controller)
    if CoD.TodHudVeil then CoD.TodHudVeil.Set(veilKey, true) end
    -- OpenLUIMenu also opens passive overlays. Native menu callbacks require
    -- the controller's interactive UI route, as in stock gameplay dialogs.
    local inputOwned = false
    self:registerEventHandler("menu_opened", function(_, event)
        if st.closed or event.controller ~= controller then return end
        Engine.LockInput(controller, true)
        Engine.SetUIActive(controller, true)
        inputOwned = true
        return true
    end)
    -- Stock unocclusion invokes updateBlur; its ordinary gameplay path clears
    -- UIActive when there is no occludedMenu. This script-owned selector stays
    -- interactive until its own close, including return from a native popup.
    local nativeUpdateBlur = self.updateBlur
    self.updateBlur = function(element)
        if nativeUpdateBlur then nativeUpdateBlur(element) end
        if inputOwned and not st.closed and not element.occludedBy then
            Engine.LockInput(controller, true)
            Engine.SetUIActive(controller, true)
        end
    end

    local function image(owner, name, l, r, t, b, rgb, alpha)
        local el = LUI.UIImage.new()
        el:setLeftRight(true, false, l, r)
        el:setTopBottom(true, false, t, b)
        el:setImage(RegisterImage(name))
        if rgb then el:setRGB(rgb[1], rgb[2], rgb[3]) end
        if alpha then el:setAlpha(alpha) end
        owner:addElement(el)
        return el
    end
    local function text(owner, value, l, r, t, b, rgb, align)
        local el = LUI.UIText.new()
        el:setLeftRight(true, false, l, r)
        el:setTopBottom(true, false, t, b)
        el:setTTF("fonts/tod_tower1.ttf")
        el:setAlignment(align or Enum.LUIAlignment.LUI_ALIGNMENT_LEFT)
        el:setRGB(rgb[1], rgb[2], rgb[3])
        el:setText(value)
        owner:addElement(el)
        return el
    end
    image(self, "$white", 0, 1280, 0, 720, {0.025, 0.025, 0.04}, 0.74)
    image(self, "i_tod_pm_backdrop", 0, 1280, 0, 720, nil, 0.75)
    image(self, "$white", 225, 1055, 110, 615, {0.05, 0.05, 0.07}, 0.96)
    image(self, "$white", 225, 1055, 110, 112, RED)
    text(self, "DER WUNDERFIZZ", 250, 830, 126, 162, WHITE)
    local floorLabel = text(self, "CONNECTING", 845, 1030, 138, 157, DIM, Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT)
    image(self, "$white", 653, 654, 179, 581, DIM, 0.3)

    local rows = {}
    for id = 1, #ROSTER do
        local y = 178 + (id - 1) * 44
        local row = LUI.UIElement.new()
        row:setLeftRight(true, false, 248, 634)
        row:setTopBottom(true, false, y, y + 40)
        row:setHandleMouse(true)
        CoD.TodUIOwnership.Attach(row)
        self:addElement(row)
        local bg = image(row, "i_tod_pm_btn", 0, 386, 0, 40, nil, 0.7)
        local focus = image(row, "i_tod_pm_btn_focus", 0, 386, 0, 40, nil, 0)
        local icon = image(row, ROSTER[id][2], 7, 41, 3, 37)
        local label = text(row, ROSTER[id][1], 52, 285, 11, 29, WHITE)
        local status = text(row, "", 282, 372, 12, 28, DIM, Enum.LUIAlignment.LUI_ALIGNMENT_RIGHT)
        rows[id] = {el = row, bg = bg, focus = focus, icon = icon, label = label, status = status}
    end
    local bigIcon = image(self, ROSTER[1][2], 687, 775, 192, 280)
    local name = text(self, ROSTER[1][1], 687, 1028, 299, 329, WHITE)
    local desc = {}
    for i = 1, 3 do desc[i] = text(self, "", 687, 1030, 349 + (i - 1) * 26, 369 + (i - 1) * 26, DIM) end
    local price = text(self, "", 687, 1030, 446, 480, GOLD)
    local status = text(self, "CONNECTING", 687, 1030, 495, 519, DIM)
    local rule = text(self, "+500 PER OWNED PERK", 687, 1030, 548, 566, DIM)
    local footer = text(self, "", 248, 1030, 633, 658, WHITE, Enum.LUIAlignment.LUI_ALIGNMENT_CENTER)

    local function draw()
        if st.closed then return end
        floorLabel:setText(st.seq > 0 and ("FLOOR " .. tostring(st.floor)) or "CONNECTING")
        local allOwned = st.owned == 511
        for id = 1, #ROSTER do
            local row = rows[id]
            local owned, available = has(st.owned, id), has(st.available, id)
            local rgb = owned and GOLD or (available and WHITE or DIM)
            row.focus:setAlpha(id == st.focus and 1 or 0)
            row.label:setRGB(rgb[1], rgb[2], rgb[3])
            row.icon:setAlpha((owned or available) and 1 or 0.45)
            row.status:setText(owned and "OWNED" or (available and "" or "LOCKED"))
        end
        local perk = ROSTER[st.focus]
        bigIcon:setImage(RegisterImage(perk[2]))
        name:setText(perk[1])
        for i = 1, 3 do desc[i]:setText(perk[3][i] or "") end
        price:setText(st.seq > 0 and (allOwned and "ALL PERKS OWNED" or ("$" .. tostring(st.cost))) or "")
        local message = "UNAVAILABLE"
        if st.seq == 0 then message = "CONNECTING"
        elseif st.result ~= "" then message = st.result
        elseif st.pending then message = "PLEASE WAIT"
        elseif has(st.owned, st.focus) then message = "ALREADY OWNED"
        elseif has(st.available, st.focus) then message = "CONFIRM TO BUY" end
        status:setText(message)
        rule:setAlpha(allOwned and 0 or 1)
        local pad = CoD.TodPad == true or (CoD.TodKeycap and type(CoD.TodKeycap.PadDevice) == "function" and CoD.TodKeycap.PadDevice() == true)
        footer:setText(pad and "D-PAD SELECT    A BUY    B CLOSE" or "ARROWS SELECT    ENTER BUY    ESC CLOSE")
    end
    local function choose(id)
        if st.closed or st.pending then return true end
        if st.focus ~= id then
            st.focus = id
            st.result = ""
            self:playSound("list_up", controller)
            draw()
        end
        return true
    end
    local function buy()
        if st.closed or st.seq == 0 or st.pending then return true end
        if has(st.owned, st.focus) or not has(st.available, st.focus) then
            self:playSound("uin_alert", controller)
            return true
        end
        st.pending = true
        st.result = ""
        Engine.SendMenuResponse(controller, "tod_wunderfizz", "buy." .. tostring(st.seq) .. "." .. tostring(st.focus))
        self:playSound("menu_select", controller)
        draw()
        return true
    end
    local function dismiss()
        if not st.closed then
            Engine.SendMenuResponse(controller, "tod_wunderfizz", "close." .. tostring(st.seq))
        end
        -- GSC closes the owned menu and releases the session. Do not use pause-menu back navigation.
        return true
    end
    for id = 1, #ROSTER do
        local rowId = id
        local row = rows[id].el
        -- A non-focusable row without stock Over/Focus clips does not emit
        -- mouseenter. Keep one native focus owner and hit-test raw movement.
        row:registerEventHandler("mousemove", function(_, event)
            if event.controller == controller and not self.occludedBy and LUI.UIElement.IsMouseInsideElement(row, event) then
                return choose(rowId)
            end
        end)
        -- Stock sends leftmouseup after press-inside/release-outside too.
        -- Only a release inside this row on its owning controller may buy.
        row:registerEventHandler("leftmouseup", function(_, event)
            if event.controller ~= controller or self.occludedBy or not event.inside then return end
            choose(rowId)
            return buy()
        end)
    end
    local function callback(key, keyboard, fn, label)
        self:AddButtonCallbackFunction(self, controller, key, keyboard, fn,
            function(element, menu)
                CoD.Menu.SetButtonLabel(menu, key, label or "")
                return true
            end, false)
    end
    callback(Enum.LUIButton.LUI_KEY_UP, "UPARROW", function() return choose((st.focus + 7) % 9 + 1) end)
    callback(Enum.LUIButton.LUI_KEY_DOWN, "DOWNARROW", function() return choose(st.focus % 9 + 1) end)
    callback(Enum.LUIButton.LUI_KEY_XBA_PSCROSS, "ENTER", buy, "MENU_SELECT")
    callback(Enum.LUIButton.LUI_KEY_XBB_PSCIRCLE, nil, dismiss, "MENU_BACK")
    callback(Enum.LUIButton.LUI_KEY_NONE, "ESCAPE", dismiss)
    self:subscribeToGlobalModel(controller, "PerController", "scriptNotify", function(model)
        if st.closed then return end
        local event = Engine.GetModelValue(model)
        local d = CoD.GetScriptNotifyData(model) or {}
        if event == "tod_wf_close" then
            if st.seq > 0 and d[1] == st.seq then self:close() end
            return
        end
        if event == "tod_wf_result" then
            if d[1] ~= st.seq then return end
            local messages = {"NOT ENOUGH POINTS", "PRICE UPDATED - TRY AGAIN", "PERK UNAVAILABLE", "CANNOT BUY RIGHT NOW", "PURCHASE CANCELLED", "PLEASE TRY AGAIN"}
            if not integer(d[2], 1, #messages) then return end
            st.pending, st.result = false, messages[d[2]]
            self:playSound("uin_alert", controller)
            draw()
            return
        end
        if event ~= "tod_wf_state" then return end
        if not integer(d[1], 1, 16777215) or not integer(d[2], 1, 50) or
            not integer(d[3], 2000, 6500) or d[3] % 500 ~= 0 or not integer(d[4], 0, 511) or not integer(d[5], 0, 511) then return end
        if d[1] < st.seq then return end
        if d[1] > st.seq then st.result, st.pending = "", false end
        st.seq, st.floor, st.cost, st.owned, st.available = d[1], d[2], d[3], d[4], d[5]
        draw()
    end)
    LUI.OverrideFunction_CallOriginalSecond(self, "close", function()
        st.closed = true
        if inputOwned then
            inputOwned = false
            -- A native popup above us owns the active route until it closes.
            if not self.occludedBy then
                Engine.LockInput(controller, false)
                Engine.SetUIActive(controller, false)
            end
        end
        if CoD.TodHudVeil then CoD.TodHudVeil.Set(veilKey, false) end
        Engine.UnsubscribeAndFreeModel(self.buttonModel)
    end)
    -- The close notification and engine-owned CloseLUIMenu may arrive in either
    -- order. Only the first may free subscriptions, prompts and child elements.
    local ownedClose = self.close
    self.close = function(element)
        if st.closed then return end
        return ownedClose(element)
    end
    draw()
    self:processEvent({name = "menu_loaded", controller = controller})
    self:processEvent({name = "gain_focus", controller = controller})
    self:playSound("menu_open", controller)
    return self
end
