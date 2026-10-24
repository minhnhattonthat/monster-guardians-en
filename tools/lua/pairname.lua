-- Turn every "Golem" name in EWRAM/IWRAM (old normal codes, from a pre-condense savestate) into the pair codes a fresh
-- game stores ("Mini Golem"), so name drawers can be checked from old states.
--   emu.py ... --script tools/lua/pairname.lua
local mem = emu.memType.gbaMemory
local old = {0x12, 0x34, 0x31, 0x2A, 0x32}
local new = {0x5129, 0x5D89, 0x4027, 0x5DEC, 0x5A2D, 0, 0, 0}
local done = false
L.on_frame(function(f)
  if done then return end
  done = true
  for _, r in ipairs({{0x02000000, 0x0203FFF0}, {0x03000000, 0x03007FF0}}) do
  for a = r[1], r[2], 2 do
    local ok = true
    for i = 1, #old do
      if emu.read16(a + (i - 1) * 2, mem) ~= old[i] then ok = false break end
    end
    if ok then
      for i = 1, #new do emu.write16(a + (i - 1) * 2, new[i], mem) end
      L.log(string.format("name at %08X", a))
    end
  end
  end
end)
