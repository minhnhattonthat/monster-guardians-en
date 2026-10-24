-- World-map window text (0x0807CBA4, stub_win): log each pair code drawn with DISPCNT, BG0-3 char bases and the
-- pair cache's font address (RAM 0x0203F000) at that moment.
--   emu.py ... --script tools/lua/winlog.lua [--var FROM=0]
local mem = emu.memType.gbaMemory
local n = 0
L.on_exec(0x0807CBA4, 0x0807CBA4, function()
  if L.frame < (FROM or 0) or n >= (MAX or 80) then return end
  local s = emu.getState()
  local code = s["cpu.r5"]
  if code < 0x4000 then return end
  n = n + 1
  local cb = {}
  for i = 0, 3 do cb[#cb + 1] = string.format("%X", (emu.read16(0x04000008 + 2 * i, mem) >> 2) & 3) end
  L.log(string.format("f%d code=%04X dispcnt=%04X cb=%s font=%08X", L.frame, code, emu.read16(0x04000000, mem),
    table.concat(cb, ","), emu.read32(0x0203F000, mem)))
end)
