-- Log every u16-glyph string the interpreter loads (0x08081450, r0 = interpreter; src at +0x460) and how many glyph
-- objects it created (0x08081010) before the next load / the end of the run. Lines: "f<frame> src=<ptr> drawn=<n>".
-- tools/textcheck.py compares drawn counts with the built strings (truncated intro text, missing pages).
--   emu.py ... --script tools/lua/textlog.lua
local mem = emu.memType.gbaMemory
local cur = {}  -- interpreter -> {src, frame, n}
local function report(o)
  local c = cur[o]
  if c then L.log(string.format("f%d src=%08X drawn=%d obj=%08X", c.frame, c.src, c.n, o)) end
end
L.on_exec(0x08081450, 0x08081450, function()
  local o = emu.getState()["cpu.r0"]
  report(o)
  cur[o] = { src = emu.read32(o + 0x1C, mem), frame = L.frame, n = 0 }
end)
L.on_exec(0x08081010, 0x08081010, function()
  local c = cur[emu.getState()["cpu.r0"]]
  if c then c.n = c.n + 1 end
end)
L.on_frame(function(n)
  if n == (TEXTLOG_END or -1) then for o in pairs(cur) do report(o) end end
end)
