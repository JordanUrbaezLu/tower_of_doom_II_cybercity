-- tod_telem_probe_chunk.lua - INNER bytecode chunk of the TELEMETRY PROBE (2026-10-04, rev 2).
--
-- Compiled by tools/hksc/hksc.exe into T7 HavokScript bytecode and spliced as a \ddd string
-- into the outer menu file (tod_telem_probe_outer.tpl.lua) by build_probe_lui.js. This file
-- may name io / os / EnableGlobals freely: hksc has no whitelist. The OUTER file may not.
--
-- WHAT IT PROVES, on THIS map's build, on the current game patch:
--   mode "io"  : EnableGlobals() unlocks io/os; a file under players\ can be written, read
--                back byte-exact, appended, and a temp file removed. The trace also records
--                whether os.rename / os.date / os.clock / Engine.GetXUID / Engine.OpenUrl
--                EXIST (type only - nothing is opened, nothing leaves the machine).
--   mode "url" : at game over only, in the armed dev build: calls Engine.OpenUrl once so the
--                tester can see WHERE the page opens (Steam overlay vs. desktop browser).
--
-- REPORTING (rev 2: TWO lanes, because rev 1 came back NO_REPORT with no file written and
-- one lane cannot tell "the Lua never ran" from "the lane is dead"):
--   lane A  Engine.Exec("set tod_telem_probe <trace>")   (the old map's proven console lane)
--   lane B  Engine.SetDvar("tod_telem_probe", <trace>)    (documented LUI call, no console)
-- The trace is pushed EARLY (right after the io/os type check) and again at the end, and the
-- chunk RETURNS the trace so the outer can draw it on screen as a third witness. The io
-- trace is also appended to the probe file itself when io works.
--
-- KNOWN-SAFE SHAPE (do not "improve" without an in-game test): everything runs
-- SYNCHRONOUSLY inside createMenu, every call is pcall-guarded, every value pushed through
-- Exec is sanitized (control chars / quotes / ';' would splatter as console commands), and
-- Engine calls always get a real controller index, never nil (a nil controller crashed the
-- old map's v4 probe to desktop).

local mode0, ctrl = ...

local URL = "@@TOD_TELEM_URL@@"
local FILE = "players/tod2_telem_probe.txt"
local TMP = "players/tod2_telem_probe_tmp.txt"

-- Only [A-Za-z0-9_|:.-] survives; everything else becomes '_'. Capped so a long value can
-- never overflow a console line.
local function san(s)
	s = tostring(s)
	s = string.gsub(s, "[^%w_|:%.%-]", "_")
	if string.len(s) > 220 then s = string.sub(s, 1, 220) end
	return s
end

-- REV 3 lane census (see the outer file's header): every report goes out on five lanes, each to its
-- own dvar, so GSC can log which lane reaches the server. ctrl is the controller the ENGINE handed
-- createMenu (InstanceRef), the same shape as this map's proven Engine.Exec(controller, "map_restart").
local function push(trace)
	local v = san(trace)
	pcall(function() Engine.Exec(ctrl, "set tod_telem_l1 " .. v) end)
	pcall(function() Engine.Exec(0, "set tod_telem_l2 " .. v) end)
	pcall(function() Engine.Exec(Engine.GetLocalClientNum(), "set tod_telem_l3 " .. v) end)
	pcall(function() Engine.SetDvar("tod_telem_l4", v) end)
	pcall(function() Engine.SendMenuResponse(ctrl, "tod_telem_probe", v) end)
end

-- Robust dvar read (the exact T7 Lua signature is unproven, so every form is tried,
-- pcall-guarded, first non-empty wins). Proven on retail by the old map's board/rec chunks.
local function readdvar(name)
	local c = ctrl or 0
	local forms = {
		function() return Engine.DvarString(c, name) end,
		function() return Engine.DvarString(name) end,
		function() return Engine.GetDvarString(c, name) end,
		function() return Engine.GetDvarString(name) end,
		function() return Engine.GetDvar(name) end,
	}
	for i = 1, #forms do
		local ok, v = pcall(forms[i])
		if ok and v ~= nil and tostring(v) ~= "" then return tostring(v) end
	end
	return ""
end

local trace = ""
local function mark(s)
	s = san(s)
	if trace == "" then trace = s else trace = trace .. "|" .. s end
end

-- type() of a value reached through a thunk, so a locked or missing global reads as "nil"
-- instead of throwing.
local function ty(thunk)
	local t = "nil"
	pcall(function() t = type(thunk()) end)
	return t
end

local function count_lines(path)
	local n = -1
	pcall(function()
		local f = io.open(path, "r")
		if f ~= nil then
			local all = f:read("*a") or ""
			f:close()
			local _, c = string.gsub(all, "\n", "\n")
			n = c
		end
	end)
	return n
end

local mode = readdvar("tod_telem_cmd")
if mode == "" then mode = "io" end

-- which report lanes even exist on this game build
mark("chunk_" .. san(mode))
mark("exec_" .. ty(function() return Engine.Exec end) .. "_setdvar_" .. ty(function() return Engine.SetDvar end) .. "_glcn_" .. ty(function() return Engine.GetLocalClientNum end) .. "_smr_" .. ty(function() return Engine.SendMenuResponse end))
mark("ctrl_" .. san(ctrl))
mark("load_" .. ty(function() return load end) .. "_eg_" .. ty(function() return EnableGlobals end))

if mode == "url" then
	local t = ty(function() return Engine.OpenUrl end)
	mark("OpenUrl_" .. t)
	push(trace)
	if t == "function" then
		-- url-only form first; the controller-first form only if the first THREW.
		local ok1 = pcall(function() Engine.OpenUrl(URL) end)
		mark("open1_" .. tostring(ok1))
		if ok1 ~= true then
			local ok2 = pcall(function() Engine.OpenUrl(ctrl or 0, URL) end)
			mark("open2_" .. tostring(ok2))
		end
	end
	mark("done")
	push(trace)
	return trace
end

-- ---- mode "io": the storage channel ------------------------------------------------------
local okE = pcall(function() EnableGlobals() end)
mark("EG_" .. tostring(okE))
mark("io_" .. ty(function() return io end) .. "_os_" .. ty(function() return os end))
push(trace)   -- EARLY report: the libraries' existence is the headline answer

-- a per-run token so a stale file from an earlier run can never read as a pass
local tok = "T0"
pcall(function() tok = "T" .. tostring(os.time()) end)

-- write, then read back byte-exact
local okW = pcall(function()
	local f = io.open(FILE, "w")
	f:write(tok .. "\n")
	f:close()
end)
mark("wr_" .. tostring(okW))

local got = ""
local okR = pcall(function()
	local f = io.open(FILE, "r")
	got = f:read("*l") or ""
	f:close()
end)
mark("rd_" .. tostring(okR) .. "_" .. ((got == tok) and "MATCH" or "MISMATCH"))

-- append a second line (the real feature appends one record per run)
local okA = pcall(function()
	local f = io.open(FILE, "a")
	f:write("second\n")
	f:close()
end)
mark("ap_" .. tostring(okA) .. "_lines_" .. tostring(count_lines(FILE)))

-- temp file write + os.remove + confirm it is gone (cleanup lane for the real feature)
local okT = pcall(function()
	local f = io.open(TMP, "w")
	f:write("x")
	f:close()
end)
local okD = pcall(function() os.remove(TMP) end)
local gone = true
pcall(function()
	local f = io.open(TMP, "r")
	if f ~= nil then gone = false f:close() end
end)
mark("rm_" .. tostring(okT and okD and gone))

-- existence only (type) - nothing below is CALLED in this mode
mark("rename_" .. ty(function() return os.rename end))
mark("date_" .. ty(function() return os.date end))
mark("clock_" .. ty(function() return os.clock end))
mark("xuid_" .. ty(function() return Engine.GetXUID end))
mark("OpenUrl_" .. ty(function() return Engine.OpenUrl end))

mark("done")

-- second witness: the trace goes into the file too (before the globals re-lock)
pcall(function()
	local f = io.open(FILE, "a")
	f:write("trace " .. trace .. "\n")
	f:close()
end)

pcall(function() DisableGlobals() end)

push(trace)
return trace
