"""Operator tool: record the packet-level events of a short window of one simulation, for the viewer's Events page.
Usage: make_trace.py NAME "TITLE" "NOTE" [--param=value ...] [--mode=share|cap]
Runs the built program directly (never through tools.run, so nothing reaches runs/index.json or the model) into
~/project/trace/NAME/ with --events (default 6 ms, half a second into the measured time) and lists it in
~/project/trace/index.json. No harness tool reads ~/project/trace/. --mode is not a program option: it is taken out
of the settings here and given to the program as the environment variable TWOHOSTS_SCHED."""
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path.home() / "project"
NS3, TRACE = ROOT / "ns-3.49", ROOT / "trace"
BIN = NS3 / "build/scratch/two-hosts/ns3.49-two-hosts-optimized"

def main():
    name, title, note, extra = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    args = {"duration": "1", "events": "6"}
    args.update(a[2:].split("=", 1) for a in extra)
    mode = args.pop("mode", "share")
    out = TRACE / name
    out.mkdir(parents=True, exist_ok=True)
    cmd = [str(BIN)] + [f"--{k}={v}" for k, v in args.items()] + [f"--out={out}"]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=TRACE, env={"LD_LIBRARY_PATH": str(NS3 / "build/lib"), "TWOHOSTS_SCHED": mode}, capture_output=True, text=True, timeout=900)
    if p.returncode or not (out / "events.csv").exists():
        raise SystemExit((p.stderr or p.stdout)[-800:])
    rows = sum(1 for _ in (out / "events.csv").open()) - 1
    first = (out / "events.csv").read_text().splitlines()[1].split(",")[0]
    entry = {"name": name, "title": title, "note": note, "settings": {k: v for k, v in args.items() if k not in ("events", "duration")} | ({"mode": mode} if any(a.startswith("--mode=") for a in extra) else {}),
             "params": json.loads((out / "params.json").read_text()), "mode": mode,
             "from_ns": int(first), "ms": float(args["events"]), "events": rows, "made": time.strftime("%Y-%m-%d %H:%M"), "seconds": round(time.time() - t0, 1)}
    idx = TRACE / "index.json"
    traces = [t for t in (json.loads(idx.read_text()) if idx.exists() else []) if t["name"] != name] + [entry]
    idx.write_text(json.dumps(traces, indent=1) + "\n")
    print(f"{name}: {rows} events in {args['events']} ms, {(out / 'events.csv').stat().st_size // 1024} kB, {entry['seconds']} s")

if __name__ == "__main__":
    main()
