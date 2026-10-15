-- Log every charset load (0x0800FA2C) and label draw (0x0800FAAC / 0x0800FB60) with its list pointer and base:
-- "CS f r0 r1 r2", "LA f r0 r1 base", "LF f r0 base". RE helper for script/sys.json.
local seen = {}
local function once(key, s)
  if not seen[key] then seen[key] = true; L.log(s) end
end
L.on_exec(0x0800FA2C, 0x0800FA2C, function()
  local s = emu.getState()
  once("CS" .. s["cpu.r0"], string.format("CS %d %08X %X %X", L.frame, s["cpu.r0"], s["cpu.r1"], s["cpu.r2"]))
end)
L.on_exec(0x0800FAAC, 0x0800FAAC, function()
  local s = emu.getState()
  local base = emu.read32(s["cpu.r13"], emu.memType.gbaMemory)
  once("LA" .. s["cpu.r0"], string.format("LA %d %08X %X %X lr=%08X", L.frame, s["cpu.r0"], s["cpu.r1"], base, s["cpu.r14"]))
end)
L.on_exec(0x0800FB60, 0x0800FB60, function()
  local s = emu.getState()
  once("LF" .. s["cpu.r0"], string.format("LF %d %08X %X lr=%08X", L.frame, s["cpu.r0"], s["cpu.r3"], s["cpu.r14"]))
end)
