#!/bin/bash
# GUI patch routine on a copy of each region, then boot it and check the hook
cd "$(dirname "$0")/.."
for n in USA EU JP; do
  python3 - "$n" <<'P'
import sys; sys.path[:0]=['tools','src']
import gui
n=sys.argv[1]; r={}
gui.run_patch('work/e2e/%s.wbfs'%n, 3, print, lambda ok,m: r.update(ok=ok,m=m))
sys.exit(0 if r['ok'] else 1)
P
  echo "== boot $n"; (cd lab && python3 t_static.py ../work/e2e/$n.wbfs 2>&1 | tail -8)
done
