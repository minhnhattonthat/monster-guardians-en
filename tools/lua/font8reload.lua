-- After loading a savestate made with another build: copy the 8x8 menu font (ROM 0x0BEDF0, 512 tiles) into BG
-- char block 1 (VRAM 0x06004000), where menus keep it, so condensed pair tiles match this build.
--   emu.py BUILD --state-in work/states/X.mss --script tools/lua/font8reload.lua ...
local done = false
L.on_frame(function(n)
  if done or n < (FONT8_AT or 2) then return end
  done = true
  local mem = emu.memType.gbaMemory
  local dst = FONT8_VRAM or 0x06004000  -- menus; other screens keep the font elsewhere (check before using)
  for i = 0, 0x3FFF, 4 do
    emu.write32(dst + i, emu.read32(0x080BEDF0 + i, mem), mem)
  end
end)
