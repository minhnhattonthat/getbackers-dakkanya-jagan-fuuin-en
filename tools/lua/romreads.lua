-- Log ROM reads per PC in a frame window: pc, count, min/max address, first addresses.
--   emu.py ... --script tools/lua/romreads.lua --var FROM=100 --var TO=160
local from, to = FROM or 0, TO or math.huge
local stats = {}
L.on_read(0x08000000, 0x09FFFFFF, function(addr)
  if L.frame < from or L.frame > to then return end
  local pc = L.pc()
  if pc >= 0x08000000 and addr >= pc - 0x40 and addr <= pc + 0x40 then return end -- instruction fetch-ish
  local s = stats[pc]
  if not s then s = { n = 0, lo = addr, hi = addr, first = {} }; stats[pc] = s end
  s.n = s.n + 1
  if addr < s.lo then s.lo = addr end
  if addr > s.hi then s.hi = addr end
  if #s.first < 12 then s.first[#s.first + 1] = string.format("%07X", addr & 0x1FFFFFF) end
end)
L.on_frame(function(f)
  if f == to + 1 then
    for pc, s in pairs(stats) do
      L.log(string.format("pc=%08X n=%d lo=%08X hi=%08X  %s", pc, s.n, s.lo, s.hi, table.concat(s.first, " ")))
    end
  end
end)
