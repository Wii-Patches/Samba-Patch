"""Builds the pad hook for one release: the routine, its tables, and the one
instruction in the game that gets redirected to it.

Run directly it prints a summary; tools/gen_prebuilt.py calls make().
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
from layout import CAVE_BASE, CFG, STATE, STATE_END
from ops import Blob, Feature, Patch, b_insn

# Wii Remote button bits
WM_LEFT, WM_RIGHT, WM_DOWN, WM_UP, WM_PLUS = 0x0001, 0x0002, 0x0004, 0x0008, 0x0010
WM_TWO, WM_ONE, WM_B, WM_A, WM_MINUS, WM_HOME = 0x0100, 0x0200, 0x0400, 0x0800, 0x1000, 0x8000

# GameCube pad word (SIC0INBUFH) -> Wii Remote
GC_MAP = [
    (0x01000000, WM_A), (0x02000000, WM_B), (0x04000000, WM_ONE), (0x08000000, WM_TWO),
    (0x10000000, WM_PLUS), (0x00100000, WM_HOME),
    (0x00080000, WM_UP), (0x00040000, WM_DOWN), (0x00020000, WM_RIGHT), (0x00010000, WM_LEFT),
]
# Classic Controller hold -> Wii Remote
CC_MAP = [
    (0x0010, WM_A), (0x0040, WM_B), (0x0008, WM_ONE), (0x0020, WM_TWO),
    (0x0400, WM_PLUS), (0x1000, WM_MINUS), (0x0800, WM_HOME),
    (0x0001, WM_UP), (0x4000, WM_DOWN), (0x8000, WM_RIGHT), (0x0002, WM_LEFT),
]

# The rings: 0-2 the left column top to bottom, 3-5 the right column.  The game's pose
# classifier (USA 0x8011702C) negates x for both hands, then reads the vector through
# per-hand tables, so the same orientation is a different ring for each hand.  These are
# vectors it reads as each ring, in the space the hook writes (before the negation):
#   z < 0 top of the hand's own side, -y middle, z > 0 bottom; x far out with z near 0
#   the middle of a side, tilted in z for that side's top (z < 0) or the opposite low ring.
RING_VECTORS = (
    # left hand (the Nunchuk)
    [(0.0, 0.0, -1.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0),
     (-0.8, 0.0, -0.6), (-1.0, 0.0, 0.0), (0.8, 0.0, 0.6)],
    # right hand (the remote)
    [(0.8, 0.0, -0.6), (1.0, 0.0, 0.0), (-0.8, 0.0, 0.6),
     (0.0, 0.0, -1.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)],
)
# stick cell (up-left, up, up-right, left, centre, right, down-left, down, down-right) -> ring;
# up/centre/down pick the row, left/right the column, a centred stick the hand's own column
RINGMAP = (
    [0, 0, 3, 1, 1, 4, 2, 2, 5],
    [0, 3, 3, 1, 4, 4, 2, 5, 5],
)

OFF = dict(SPIKE=0x3C, THRESH=0x40, SPEED=0x44, DEADZONE=0x48, INV1000=0x4C, SCALE=0x50,
           FLAGS=0x54, MAGIC_D=0x58, GCMAP=0x60, CCMAP=0xC0, CONNOFF=0x120, CONNST=0x124, ONE=0x128, VECS=0x130, RINGMAP=0x1C0)
MAGIC = 0x53444131          # 'SDA1'


def cfg_blob(conn_off, conn_state, flags=3, spike=2.6, thresh=50, speed=60, deadzone=15,
             vectors=RING_VECTORS, ringmap=RINGMAP):
    b = bytearray(STATE - CFG)
    for h in range(2):
        for i, v in enumerate(vectors[h]):
            struct.pack_into('>3f', b, OFF['VECS'] + h * 72 + i * 12, *v)
        b[OFF['RINGMAP'] + h * 12:OFF['RINGMAP'] + h * 12 + 9] = bytes(ringmap[h])
    struct.pack_into('>f', b, OFF['SPIKE'], spike)
    struct.pack_into('>i', b, OFF['THRESH'], thresh)
    struct.pack_into('>i', b, OFF['SPEED'], speed)
    struct.pack_into('>i', b, OFF['DEADZONE'], deadzone)
    struct.pack_into('>f', b, OFF['INV1000'], 0.001)
    struct.pack_into('>f', b, OFF['ONE'], 1.0)
    struct.pack_into('>f', b, OFF['SCALE'], 100.0)
    struct.pack_into('>I', b, OFF['FLAGS'], flags)
    struct.pack_into('>i', b, OFF['CONNOFF'], conn_off)
    struct.pack_into('>I', b, OFF['CONNST'], conn_state)
    struct.pack_into('>Q', b, OFF['MAGIC_D'], 0x4330000080000000)
    for base, m in ((OFF['GCMAP'], GC_MAP), (OFF['CCMAP'], CC_MAP)):
        for i, (src, dst) in enumerate(m):
            struct.pack_into('>II', b, base + 8 * i, src, dst)
    return bytes(b)


def prebuilt_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'tools', 'prebuilt', 'pads.json')
    return os.path.join(HERE, '..', 'tools', 'prebuilt', 'pads.json')


def code_blob(kpad_read, rebuild=False):
    """The assembled hook for a KPADRead address: the shipped words, or (devkitPPC) a fresh build."""
    if not rebuild:
        try:
            words = json.load(open(prebuilt_path()))['%08X' % kpad_read]
            return struct.pack('>%dI' % len(words), *[int(w, 16) for w in words])
        except (OSError, KeyError):
            pass
    import asm
    consts = dict(CFG=CFG, STATE=STATE, MAGIC=MAGIC, **OFF)
    src = open(os.path.join(HERE, 'pads.s')).read()
    return asm.assemble(src, CAVE_BASE, syms=dict(KPADREAD=kpad_read), consts=consts)


def make(region, site, kpad_read, conn_off, conn_state, flags=3, **cfg):
    """Operations that wire the pad hook into one release.

    `site` is the `bl KPADRead` in the input manager; `kpad_read` its target.
    """
    code = code_blob(kpad_read)
    assert CAVE_BASE + len(code) <= CFG, 'pad hook too big: 0x%X' % len(code)
    orig = b_insn(kpad_read, site, link=True)
    ops = [
        Patch(site, struct.pack('>I', b_insn(CAVE_BASE, site, link=True)),
              struct.pack('>I', orig), 'KPADRead call in the input manager -> pad hook'),
        Blob(CAVE_BASE, code, 'pad hook'),
        Blob(CFG, cfg_blob(conn_off, conn_state, flags, **cfg) + bytes(STATE_END - STATE), 'pad hook tables and state'),
    ]
    return Feature('pads', 'GameCube / Classic Controller', region, ops)


if __name__ == '__main__':
    f = make('R3BE8P', 0x80116DAC, 0x802F5948, -22479, 0x803F8518)
    for op in f.ops:
        print(type(op).__name__, hex(op.addr), len(getattr(op, 'data', getattr(op, 'new', b''))))
