-- Log each distinct text box geometry used by the u16-glyph interpreter: when a glyph object is created
-- (0x08081010, r0 = interpreter), print font struct, left/right bounds (+0x14/+0x18), y (+0x44A) and source ptr.
--   emu.py ... --script tools/lua/boxlog.lua
local seen = {}
local mem = emu.memType.gbaMemory
L.on_exec(0x08081010, 0x08081010, function()
  local s = emu.getState()
  local o = s["cpu.r0"]
  local font, l, r = emu.read32(o + 0x10, mem), emu.read32(o + 0x14, mem), emu.read32(o + 0x18, mem)
  local key = string.format("%08X %d %d", font, l, r)
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d obj=%08X font=%08X left=%d right=%d y=%d src=%08X", L.frame, o, font, l, r,
    emu.read16(o + 0x44A, mem), emu.read32(o + 0x460, mem)))
end)
