"""Reference runs for the several-moves brief (v2, stage 4): the built program, through the v2 harness's own run path, in this scratch folder only.
ref.py CAP POLICY   -> one line per design: fa goodput, fb loss, the condition"""
import sys, json, os
from pathlib import Path
HERE = Path(__file__).resolve().parent; os.environ["HOME"] = str(HERE / "home"); sys.path.insert(0, str(HERE / "home/project/harness"))
cap, policy = sys.argv[1], sys.argv[2]
P = HERE / "home/project"
b = json.loads((P / "briefs/three-hosts-2.json").read_text()); bid = f"moves-{cap.lower()}"
b["id"] = bid; b["limits"] = {"simulations": 20, "simulations_per_experiment": 4}
b["structure"] = {"may_change": True, "most": {"hosts": 6, "links": 6, "flows": 4}, "locked": ["host:a", "host:b", "host:r", "host:c", "flow:fa", "flow:fb", "link:la", "link:lb", "link:lc"], "new_link": {"rate_max": cap, "delay": "1ms"}}
(P / f"briefs/{bid}.json").write_text(json.dumps(b, indent=1) + "\n")
import tools
tools.POLICY = policy; sid = f"ref-{cap.lower()}-{policy}"; tools.open_session(sid, bid)
E = lambda **k: {"do": "", "id": "", "kind": "", "from": "", "to": "", "on": "", "rate": "", "type": "", "app": "", **k}
AC = E(do="add_link", id="ld", **{"from": "a", "to": "c"}, rate=cap); BC = E(do="add_link", id="ld", **{"from": "b", "to": "c"}, rate=cap)
NOQ = E(do="remove", kind="queue", id="lc", on="r"); FQ = [NOQ, E(do="add_queue", id="lc", on="r", kind="fqcodel")]
D = [("given network, defaults", {}, []),
     ("setting: fa's part 0.19", {"lc.queue.parts.fa": 0.19}, []),
     ("new link a-c", {}, [AC]),
     ("new link a-c + fa's part 0.05", {"lc.queue.parts.fa": 0.05}, [AC]),
     ("new link a-c + scheduler removed", {}, [AC, NOQ]),
     ("new link b-c", {}, [BC]),
     ("new link b-c + fa's part 4", {"lc.queue.parts.fa": 4}, [BC]),
     ("new link b-c + scheduler removed", {}, [BC, NOQ]),
     ("scheduler removed (plain queue)", {}, [NOQ]),
     ("scheduler replaced by fqcodel", {}, FQ)]
res = tools.run_many([p for _, p, _ in D], [s for _, _, s in D])
out = []
for (name, p, s), r in zip(D, res):
    m = r.get("metrics") or {}
    if "error" in r: print(f"{name:36s} ERROR {r['error'][-300:]}"); continue
    fa, loss = m.get("fa_goodput_bps"), m.get("fb_loss_frac")
    print(f"{name:36s} fa {fa / 1e6:7.2f} Mbit/s   fb loss {100 * loss:6.2f} %   {'ok' if loss <= 0.1 else 'CONDITION NOT MET'}   ({r['seconds']} s, {r['id']})", flush=True)
    out.append({"design": name, "params": p, "structure": s, "fa_goodput_bps": fa, "fb_loss_frac": loss, "fb_goodput_bps": m.get("fb_goodput_bps"), "run": r["id"]})
(HERE / f"ref_{cap.lower()}_{policy}.json").write_text(json.dumps(out, indent=1) + "\n")
