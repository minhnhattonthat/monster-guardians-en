-- Log GBA DMA0-3 starts whose destination is in DST_LO..DST_HI: frame, channel, src, dst, count, pc, lr.
--   emu.py ... --script tools/lua/dmalog.lua [--var DST_LO=0x06010000 --var DST_HI=0x06017FFF] [--var FROM=400]
local lo, hi, from = DST_LO or 0x06010000, DST_HI or 0x06017FFF, FROM or 0
local function r32(a) return emu.read32(a, emu.memType.gbaMemory) end
L.on_write(0x040000BA, 0x040000DF, function(addr, val)
  if L.frame < from then return end
  local ch = (addr - 0x040000B0) // 12
  local cnt = 0x040000B0 + ch * 12 + 10
  if addr ~= cnt + 1 or (val & 0x80) == 0 then return end   -- high byte of DMAxCNT_H with enable bit
  local src, dst = r32(cnt - 10), r32(cnt - 6)
  if dst < lo or dst > hi then return end
  local s = emu.getState()
  L.log(string.format("f%d dma%d src=%08X dst=%08X n=%X pc=%08X lr=%08X", L.frame, ch, src, dst,
    emu.read16(cnt - 2, emu.memType.gbaMemory), s["cpu.pipeline.execute.address"] or 0, s["cpu.r14"] or 0))
end)
