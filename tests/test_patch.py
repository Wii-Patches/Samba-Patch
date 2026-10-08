"""Run: python3 tests/test_patch.py  (needs the extracted retail DOLs in work/<id>/sys/main.dol)"""
import os
import struct
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path[:0] = [os.path.join(ROOT, 'tools')]
import sambapatch                                     # noqa: E402
from dol import Dol                                   # noqa: E402
from regions import REGIONS                           # noqa: E402

for r in REGIONS.values():
    src = os.path.join(ROOT, 'work', r.disc_id, 'sys', 'main.dol')
    if not os.path.exists(src):
        print('skip', r)
        continue
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, 'main.dol')
        region, size = sambapatch.patch_dol(src, out, r.disc_id)
        d = Dol(out)
        word = struct.unpack('>I', d.read(r.site, 4))[0]
        assert word >> 26 == 18 and word & 1, 'site is not a bl'
        assert d.read(0x80001820, 4) is not None, 'cave missing'
        assert sambapatch.feature(r).is_applied(d)
        try:
            sambapatch.patch_dol(out, os.path.join(t, 'again.dol'), r.disc_id)
            raise SystemExit('patching twice must fail')
        except SystemExit as e:
            assert 'clean retail' in str(e)
    print('ok', r, size)

# the shipped words exist for every KPADRead address (no toolchain needed at patch time)
import json
pre = json.load(open(os.path.join(ROOT, 'tools', 'prebuilt', 'pads.json')))
for r in REGIONS.values():
    assert '%08X' % r.kpad_read in pre, r
print('ok prebuilt')
