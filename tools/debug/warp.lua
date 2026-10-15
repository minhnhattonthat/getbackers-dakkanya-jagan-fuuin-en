-- Cold-boot warp for GetBackers Dakkanya - Jagan Fuuin! (GBA). Appended after the emu.py driver (uses L.*).
-- Globals (--var):
--   SCENE  = "title" | "newgame" | "script"     (default "script")
--   TARGET = ROM address (0x08xxxxxx) of a PAC3 script in THIS rom: replaces the first script the game starts
--            after NEW GAME (Act 1 intro, start_script 0x0804C3B4 r0), so any script plays from a cold boot.
--   NTH    = replace the NTH script start instead of the first (default 1)
--   AFTER  = route string run once arrived ("30 -;6 a;60 -")
-- Logs "ARRIVED <frame>" and "SCRIPT <addr>" for every script start.
local SCENE_KIND = SCENE or "script"
local nth = NTH or 1
local starts = 0
local arrived = false

local function arrive()
  if arrived then return end
  arrived = true
  L.log("ARRIVED " .. L.frame)
  if AFTER then for step in AFTER:gmatch("[^;]+") do
    local n, spec = step:match("^%s*(%d+)%s+(%S+)%s*$")
    L.press(spec, tonumber(n))
  end end
end

local GAME_FROM = 1000   -- scripts started before this frame belong to the attract intro, not the game
L.on_exec(0x0804C3B4, 0x0804C3B4, function()
  local s = emu.getState()
  local r0 = s["cpu.r0"]
  if L.frame < GAME_FROM then
    L.log(string.format("SCRIPT %08X f=%d (intro)", r0, L.frame))
    return
  end
  starts = starts + 1
  if SCENE_KIND == "script" and TARGET and starts == nth then
    emu.setState({ ["cpu.r0"] = TARGET })
    r0 = TARGET
    arrive()
  elseif SCENE_KIND == "newgame" and starts == 1 then
    arrive()
  end
  L.log(string.format("SCRIPT %08X f=%d", r0, L.frame))
end)

-- title: logos are skipped with START; the title menu (NEW GAME / LOAD) takes A on NEW GAME.
-- Title screen shows after ~700 frames of START presses; then A starts a new game.
local t0 = nil
emu.addEventCallback(L.safe(function()
  if arrived or L.frame < 200 then return end
  if SCENE_KIND == "title" then
    if L.frame >= 900 then arrive() end
    if L.frame % 60 < 6 then emu.setInput({ start = true }, 0) end
    return
  end
  if starts > 0 then return end
  local f = L.frame
  if f < GAME_FROM then
    if f % 60 < 6 then emu.setInput({ start = true }, 0) end
  elseif f % 40 < 6 then
    emu.setInput({ a = true }, 0)
  end
end), emu.eventType.inputPolled)
