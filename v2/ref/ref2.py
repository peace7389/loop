"""More reference runs for the candidate brief moves-90mbps (new link at most 90 Mbit/s): the edges of each move, seeds and a longer time."""
import sys, json, os
from pathlib import Path
HERE = Path(__file__).resolve().parent; os.environ["HOME"] = str(HERE / "home"); sys.path.insert(0, str(HERE / "home/project/harness"))
import tools
tools.POLICY = "share"; tools.open_session("ref2b-90", "moves-90mbps")
E = lambda **k: {"do": "", "id": "", "kind": "", "from": "", "to": "", "on": "", "rate": "", "type": "", "app": "", **k}
L = lambda a, b, rate: E(do="add_link", id="ld", **{"from": a, "to": b}, rate=rate)
NOQ = E(do="remove", kind="queue", id="lc", on="r"); Q = lambda k: [NOQ, E(do="add_queue", id="lc", on="r", kind=k)]
D = [(f"setting: fa's part {p}", {"lc.queue.parts.fa": p}, []) for p in (0.15, 0.17, 0.18)]
D += [(f"new link b-c at {r}", {}, [L("b", "c", r)]) for r in ("70Mbps", "75Mbps", "80Mbps", "85Mbps")]
D += [(f"new link b-c at 90Mbps, fa {t}", {"fa.type": t}, [L("b", "c", "90Mbps")]) for t in ("TcpNewReno", "TcpBbr", "TcpVegas")]
D += [(f"new link a-c at 90Mbps, fa {t}", {"fa.type": t}, [L("a", "c", "90Mbps")]) for t in ("TcpBbr",)]
D += [(f"queue at r replaced by {k}", {}, Q(k)) for k in ("codel", "red", "pie", "pfifofast")]
D += [("both new links (a-c, b-c), scheduler removed", {}, [L("a", "c", "90Mbps"), {**L("b", "c", "90Mbps"), "id": "le"}, NOQ])]
res = []
for i in range(0, len(D), 8): res += tools.run_many([p for _, p, _ in D[i:i + 8]], [s for _, _, s in D[i:i + 8]])
out = []
for (name, p, s), r in zip(D, res):
    m = r.get("metrics") or {}
    if "error" in r: print(f"{name:42s} ERROR {r['error'][-200:]}"); continue
    print(f"{name:42s} fa {m['fa_goodput_bps'] / 1e6:7.2f} Mbit/s   fb loss {100 * m['fb_loss_frac']:6.2f} %   {'ok' if m['fb_loss_frac'] <= 0.1 else 'CONDITION NOT MET'}", flush=True)
    out.append({"design": name, "params": p, "structure": s, "fa_goodput_bps": m["fa_goodput_bps"], "fb_loss_frac": m["fb_loss_frac"], "run": r["id"]})
(HERE / "ref2_90.json").write_text(json.dumps(out, indent=1) + "\n")
