"""The same designs with three seeds at five times the measured time (25 s): does the order of the moves hold, and do the designs near the condition stay inside it?"""
import sys, json, os
from pathlib import Path
HERE = Path(__file__).resolve().parent; os.environ["HOME"] = str(HERE / "home"); sys.path.insert(0, str(HERE / "home/project/harness"))
P = HERE / "home/project"; out = []
import tools
E = lambda **k: {"do": "", "id": "", "kind": "", "from": "", "to": "", "on": "", "rate": "", "type": "", "app": "", **k}
L = lambda a, b, rate: E(do="add_link", id="ld", **{"from": a, "to": b}, rate=rate)
D = [("setting: fa's part 0.17", {"lc.queue.parts.fa": 0.17}, []), ("new link a-c at 90Mbps", {}, [L("a", "c", "90Mbps")]), ("new link b-c at 90Mbps", {}, [L("b", "c", "90Mbps")]), ("new link b-c at 75Mbps", {}, [L("b", "c", "75Mbps")]),
     ("scheduler removed (plain queue)", {}, [E(do="remove", kind="queue", id="lc", on="r")])]
rows = {n: [] for n, _, _ in D}
for seed in (1, 2, 3):
    b = json.loads((P / "briefs/moves-90mbps.json").read_text()); b["id"] = f"moves-90mbps-long-s{seed}"; b["system"] = {"seed": seed, "duration": 25}
    (P / f"briefs/{b['id']}.json").write_text(json.dumps(b, indent=1) + "\n")
    tools.SESSION = tools.BRIEF = None; tools.open_session(f"ref3-s{seed}", b["id"])
    for (name, p, s), r in zip(D, tools.run_many([p for _, p, _ in D], [s for _, _, s in D])):
        m = r.get("metrics") or {}; rows[name].append((m.get("fa_goodput_bps"), m.get("fb_loss_frac"), r.get("error")))
for name, v in rows.items():
    print(f"{name:34s} fa " + " / ".join(f"{x[0] / 1e6:6.2f}" if x[0] is not None else "error" for x in v) + " Mbit/s   fb loss " + " / ".join(f"{100 * x[1]:5.2f}" if x[1] is not None else "error" for x in v) + " %")
    out.append({"design": name, "seeds": [1, 2, 3], "duration": 25, "fa_goodput_bps": [x[0] for x in v], "fb_loss_frac": [x[1] for x in v]})
(HERE / "ref3_90.json").write_text(json.dumps(out, indent=1) + "\n")
