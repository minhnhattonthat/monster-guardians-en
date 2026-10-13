"""GBA BIOS LZ77 (type 0x10): decompress, compress (VRAM-safe), and scan a ROM for blocks.

    python -X utf8 tools/lz.py scan ROM OUT_DIR [--min 256]   # every plausible block -> OUT_DIR/<offset>.bin
    python -X utf8 tools/lz.py --selftest
"""
import argparse
import struct
import sys
from pathlib import Path


def decompress(data, off=0):
    """-> (bytes, compressed length). Raises ValueError on a malformed block."""
    if data[off] != 0x10:
        raise ValueError('not LZ77')
    size = struct.unpack_from('<I', data, off)[0] >> 8
    out = bytearray()
    i = off + 4
    while len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = data[i], data[i + 1]
                i += 2
                n = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                if disp > len(out):
                    raise ValueError('bad back-reference')
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(data[i])
                i += 1
    return bytes(out[:size]), i - off


def compress(src):
    """LZ77 type 0x10 with disp >= 2 (safe for 16-bit VRAM writes). Greedy, longest match."""
    out = bytearray(struct.pack('<I', len(src) << 8 | 0x10))
    i = 0
    while i < len(src):
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= len(src):
                break
            best_len, best_disp = 0, 0
            for disp in range(2, min(i, 4096) + 1):
                n = 0
                while n < 18 and i + n < len(src) and src[i + n] == src[i + n - disp]:
                    n += 1
                if n > best_len:
                    best_len, best_disp = n, disp
                    if n == 18:
                        break
            if best_len >= 3:
                flags |= 0x80 >> bit
                d = best_disp - 1
                out += bytes([((best_len - 3) << 4) | (d >> 8), d & 0xFF])
                i += best_len
            else:
                out.append(src[i])
                i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def lzss_decompress(src):
    """Konami/Okumura LZSS used by the game (decoder 0x08081B48): 4 KB ring (zeroed) starting at 0xFEE, flag
    byte LSB first (1 = literal), match = pos 12 bits (b0 | (b1 & 0xF0) << 4), length (b1 & 0xF) + 3.
    The caller passes the compressed length; output length is whatever the stream produces."""
    ring = bytearray(4096)
    r = 0xFEE
    out = bytearray()
    i = 0
    while i < len(src):
        flags = src[i]
        i += 1
        for bit in range(8):
            if i >= len(src):
                break
            if flags >> bit & 1:
                c = src[i]
                i += 1
                out.append(c)
                ring[r] = c
                r = (r + 1) & 0xFFF
            else:
                if i + 1 >= len(src):
                    i = len(src)
                    break
                b0, b1 = src[i], src[i + 1]
                i += 2
                pos = b0 | (b1 & 0xF0) << 4
                for k in range((b1 & 0xF) + 3):
                    c = ring[(pos + k) & 0xFFF]
                    out.append(c)
                    ring[r] = c
                    r = (r + 1) & 0xFFF
    return bytes(out)


def lzss_compress(data):
    """Inverse of lzss_decompress (greedy longest match against the ring, zero-initialised like the decoder)."""
    ring = bytearray(4096)
    r = 0xFEE
    out = bytearray()
    i = 0
    hist = bytearray(4096)  # mirror: what the decoder's ring holds
    while i < len(data):
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= len(data):
                break
            best_len, best_pos = 0, 0
            maxlen = min(18, len(data) - i)
            if maxlen >= 3:
                # candidate positions: anywhere in the ring (zeros count, matching the zeroed initial ring)
                for pos in range(4096):
                    n = 0
                    while n < maxlen:
                        # decoder copies byte by byte, so overlapping copies see bytes just written
                        rp = (pos + n) & 0xFFF
                        if (rp - r) & 0xFFF < n:  # inside what this match writes
                            src_b = data[i + ((rp - r) & 0xFFF)]
                        else:
                            src_b = ring[rp]
                        if src_b != data[i + n]:
                            break
                        n += 1
                    if n > best_len:
                        best_len, best_pos = n, pos
                        if n == maxlen:
                            break
            if best_len >= 3:
                out += bytes([best_pos & 0xFF, (best_pos >> 4) & 0xF0 | (best_len - 3)])
                for k in range(best_len):
                    ring[r] = data[i + k]
                    r = (r + 1) & 0xFFF
                i += best_len
            else:
                flags |= 1 << bit
                out.append(data[i])
                ring[r] = data[i]
                r = (r + 1) & 0xFFF
                i += 1
        out[flag_pos] = flags
    return bytes(out)


def scan(rom, minsize=256):
    """-> [(offset, decompressed bytes)] for 4-aligned 0x10 headers that decompress cleanly to minsize..256 KB."""
    found = []
    for off in range(0, len(rom) - 4, 4):
        if rom[off] != 0x10:
            continue
        size = struct.unpack_from('<I', rom, off)[0] >> 8
        if not minsize <= size <= 0x40000:
            continue
        try:
            data, n = decompress(rom, off)
        except (ValueError, IndexError):
            continue
        if n <= size:  # compressed smaller than output: plausible
            found.append((off, data))
    return found


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        import os
        for s in (b'', b'abc' * 100, os.urandom(500), bytes(range(256)) * 9):
            assert decompress(compress(s))[0] == s
        print('selftest ok')
        sys.exit()
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['scan'])
    ap.add_argument('rom')
    ap.add_argument('out')
    ap.add_argument('--min', type=int, default=256)
    a = ap.parse_args()
    rom = Path(a.rom).read_bytes()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = scan(rom, a.min)
    for off, data in blocks:
        (out / f'{off:06X}.bin').write_bytes(data)
    print(len(blocks), 'blocks')
