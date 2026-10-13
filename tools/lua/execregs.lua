-- Log r0-r3, sp, lr each time EXEC_AT runs (after FROM, at most MAX times).
--   emu.py ... --script tools/lua/execregs.lua --var EXEC_AT=0x0807D2E8 [--var FROM=700 --var MAX=50]
local n = 0
L.on_exec(EXEC_AT, EXEC_AT, function()
  if L.frame < (FROM or 0) or n >= (MAX or 50) then return end
  n = n + 1
  local s = emu.getState()
  L.log(string.format("f%d r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r5=%08X r6=%08X r7=%08X sp=%08X lr=%08X",
    L.frame, s["cpu.r0"], s["cpu.r1"], s["cpu.r2"], s["cpu.r3"], s["cpu.r4"], s["cpu.r5"], s["cpu.r6"],
    s["cpu.r7"], s["cpu.r13"], s["cpu.r14"]))
end)
