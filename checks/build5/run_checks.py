"""Run the operator's check commands with a given program, each into OUT/<name>/, all at once.
usage: run_checks.py BIN OUT [name=policy:options ...]   (no names: the commands of checks/build3 and build4's b1)"""
import subprocess, sys, time, re
from pathlib import Path
ROOT = Path.home() / "project"
BIN, OUT = sys.argv[1], Path(sys.argv[2])
jobs = []
if len(sys.argv) > 3:
    for a in sys.argv[3:]:
        name, rest = a.split("=", 1); pol, opts = rest.split(":", 1)
        jobs.append((name, pol, opts.split()))
else:
    for d in sorted((ROOT / "checks/build3").glob("c*")) + [ROOT / "checks/build4/b1-was-negative"]:
        if d.name.endswith("-pcap"):
            continue
        line = (d / "command.txt").read_text().splitlines()[0]
        pol = re.match(r"TWOHOSTS_SCHED=(\w+)", line).group(1)
        opts = [o for o in line.split()[2:] if not o.startswith("--out=")]
        jobs.append((d.name, pol, opts))
procs = []
for name, pol, opts in jobs:
    o = OUT / name; o.mkdir(parents=True, exist_ok=True)
    cmd = [BIN] + opts + [f"--out={o}"]
    (o / "command.txt").write_text(f"TWOHOSTS_SCHED={pol} two-hosts " + " ".join(opts + [f"--out={o}"]) + "\n")
    procs.append((name, o, time.time(), subprocess.Popen(cmd, cwd=o, env={"LD_LIBRARY_PATH": str(ROOT / "ns-3.49/build/lib"), "TWOHOSTS_SCHED": pol}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
for name, o, t0, p in procs:
    said = p.communicate()[0]
    with (o / "command.txt").open("a") as f:
        f.write(f"exit {p.returncode}, {time.time() - t0:.1f} s\n")
    print(name, "exit", p.returncode, (said or "").strip()[-200:])
