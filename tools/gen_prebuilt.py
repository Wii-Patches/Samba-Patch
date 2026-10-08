#!/usr/bin/env python3
"""Assemble src/pads.s (needs devkitPPC) for every KPADRead address and write
tools/prebuilt/pads.json, which the patcher and GUI ship instead of a toolchain.
With --check, fail if the shipped words are stale."""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'src')]
import gen_pads                                       # noqa: E402
from regions import REGIONS                           # noqa: E402

out = {}
for k in sorted({r.kpad_read for r in REGIONS.values()}):
    blob = gen_pads.code_blob(k, rebuild=True)
    out['%08X' % k] = ['%08X' % w for w in struct.unpack('>%dI' % (len(blob) // 4), blob)]
path = gen_pads.prebuilt_path()
if '--check' in sys.argv:
    sys.exit(0 if json.load(open(path)) == out else 'tools/prebuilt/pads.json is stale: run tools/gen_prebuilt.py')
os.makedirs(os.path.dirname(path), exist_ok=True)
json.dump(out, open(path, 'w'), indent=0)
print('wrote', os.path.relpath(path), {k: len(v) * 4 for k, v in out.items()})
