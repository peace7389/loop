"""Byte comparison of the output files of two folders of check runs. usage: compare.py A B [name ...]"""
import sys, hashlib
from pathlib import Path
A, B = Path(sys.argv[1]), Path(sys.argv[2])
names = sys.argv[3:] or sorted(p.name for p in A.iterdir() if p.is_dir() and (B / p.name).is_dir())
FILES = ("metrics.json", "series.csv", "params.json", "flowmon.xml")
bad = 0
for n in names:
    res = []
    for f in FILES:
        a, b = A / n / f, B / n / f
        if not a.is_file() or not b.is_file():
            res.append(f"{f}: missing"); bad += 1; continue
        same = a.read_bytes() == b.read_bytes()
        bad += not same
        res.append(f"{f}: {'identical' if same else 'DIFFERS'}")
    print(f"{n:22}", " | ".join(res))
print(f"{len(names)} runs, {len(names) * len(FILES)} files compared, {bad} not identical")
sys.exit(1 if bad else 0)
