#!/usr/bin/env python3
"""Add GameCube controller and Classic Controller support to Samba de Amigo (Wii).

    sambapatch.py dol  <main.dol> <out.dol>       patch an extracted main.dol
    sambapatch.py disc <game.iso|wbfs|rvz> <out>  patch a whole disc (needs wit)
    sambapatch.py riivolution                     (re)write riivolution/sd

The hook is one extra DOL text section at 0x80001820 plus one rewritten
`bl KPADRead` (src/pads.s, src/gen_pads.py).
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))

import gen_pads                                       # noqa: E402
from dol import Dol                                   # noqa: E402
from ops import apply_static                          # noqa: E402
from regions import REGIONS                           # noqa: E402

CHOICES = (('GameCube controller + Classic Controller', 'both', 3),
           ('GameCube controller', 'gc', 1),
           ('Classic Controller', 'cc', 2))


def feature(region, flags=3):
    return gen_pads.make(region.disc_id, region.site, region.kpad_read, flags)


def detect_region(dol, disc_id=None):
    for r in ([REGIONS[disc_id]] if disc_id else REGIONS.values()):
        if not feature(r).check_pristine(dol):
            return r
    raise SystemExit('not a clean retail Samba de Amigo main.dol (other build, or already patched)')


def patch_dol(src, dst, disc_id=None, flags=3):
    dol = Dol(src)
    region = detect_region(dol, disc_id)
    size = apply_static(dol, [feature(region, flags)])
    dol.save(dst)
    return region, size


def write_riivolution():
    base = os.path.join(ROOT, 'riivolution')
    shutil.rmtree(base, ignore_errors=True)
    os.makedirs(os.path.join(base, 'riivolution'))
    names = {'R3BE8P': 'USA', 'R3BP8P': 'Europe', 'R3BJ8P': 'Japan'}
    letter = {'R3BE8P': 'E', 'R3BP8P': 'P', 'R3BJ8P': 'J'}
    for r in REGIONS.values():
        x = ['<wiidisc version="1">', '  <id game="R3B"><region type="%s" /></id>' % letter[r.disc_id],
             '  <options>', '    <section name="Samba de Amigo">', '      <option name="Controllers" default="1">']
        for title, key, _ in CHOICES:
            x.append('        <choice name="%s"><patch id="sda_%s" /></choice>' % (title, key))
        x += ['      </option>', '    </section>', '  </options>']
        for _, key, flags in CHOICES:
            x.append('  <patch id="sda_%s">' % key)
            x += ['    ' + m for m in feature(r, flags).memory_elements()]
            x.append('  </patch>')
        x.append('</wiidisc>')
        p = os.path.join(base, 'riivolution', 'SambaPatch_%s.xml' % names[r.disc_id])
        open(p, 'w').write('\n'.join(x) + '\n')
        print(os.path.relpath(p, ROOT))


def patch_disc(src, dst, flags=3):
    wit = shutil.which('wit') or sys.exit('wit (Wiimms ISO Tools) is required for disc patching')
    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(dst))) as t:
        ex = os.path.join(t, 'x')
        subprocess.run([wit, 'extract', src, ex, '--psel', 'data', '-q'], check=True)
        d = os.path.join(ex, 'sys', 'main.dol')
        region, size = patch_dol(d, d, flags=flags)
        kind = os.path.splitext(dst)[1].lstrip('.').lower()
        fmt = {'wbfs': '--wbfs', 'iso': '--iso', 'rvz': '--rvz'}.get(kind) or sys.exit('output must be .iso, .wbfs or .rvz')
        subprocess.run([wit, 'copy', ex, dst, fmt, '--overwrite', '-q'], check=True)
    return region, size


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['dol'] and len(a) == 3:
        print('%s: injected %d bytes' % patch_dol(a[1], a[2]))
    elif a[:1] == ['disc'] and len(a) == 3:
        print('%s: injected %d bytes' % patch_disc(a[1], a[2]))
    elif a == ['riivolution']:
        write_riivolution()
    else:
        sys.exit(__doc__)
