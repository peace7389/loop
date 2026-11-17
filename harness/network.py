"""A network described as data: hosts joined by point-to-point links, UDP and TCP flows between them, and on one
sending side of a link a plain queue or the scheduler. A brief with "topology" is run by the program `net`
(ns-3.49/scratch/net), which builds what the description says; a brief without it is run by `two-hosts`, as before.

    {"hosts": [{"id": "sender"}, {"id": "receiver"}],
     "links": [{"id": "l1", "between": ["sender", "receiver"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10,
                "queue": {"on": "sender", "kind": "scheduler", "length": 100, "parts": {"udp": 0.5, "tcp": 0.5}, "largest_rate": {}}}],
     "flows": [{"id": "udp", "kind": "udp", "from": "sender", "to": "receiver", "rate": "2Gbps", "packet_bytes": 1400},
               {"id": "tcp", "kind": "tcp", "from": "sender", "to": "receiver", "type": "TcpCubic"}]}

A setting of the network has an address, object.property: l1.rate, l1.delay, l1.mtu, l1.device_queue,
l1.queue.length, l1.queue.parts.udp, l1.queue.largest_rate.tcp, udp.rate, udp.packet_bytes, tcp.type. A brief fixes
it (the value in the description) or makes it a knob (an entry of "knobs" under that address).
The measures are made from the network (outputs): per flow, per link, per queue.
How a scheduler divides the link (the scheduling policy) is not part of the description."""
import copy, re

ID = r"[a-z][a-z0-9]{0,11}"
LIMITS = {"hosts": 8, "links": 12, "flows": 8}     # the most a network may hold
TCP_TYPES = ("TcpCubic", "TcpNewReno", "TcpLinuxReno", "TcpBbr", "TcpVegas", "TcpBic")
RUN = ("duration", "seed", "tcpInitCwnd", "tcpBufBytes")   # settings of a simulation that belong to no object (as in two-hosts)
DEFAULT = {"hosts": [{"id": "sender"}, {"id": "receiver"}],
           "links": [{"id": "l1", "between": ["sender", "receiver"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10,
                      "queue": {"on": "sender", "kind": "scheduler", "length": 100, "parts": {"udp": 0.5, "tcp": 0.5}, "largest_rate": {}}}],
           "flows": [{"id": "udp", "kind": "udp", "from": "sender", "to": "receiver", "rate": "2Gbps", "packet_bytes": 1400},
                     {"id": "tcp", "kind": "tcp", "from": "sender", "to": "receiver", "type": "TcpCubic"}]}


def rate_bps(s):
    m = re.fullmatch(r"\s*([0-9.]+)\s*([kMG]?)bps\s*", str(s))
    if not m:
        raise ValueError(f"bad rate {s!r}")
    return float(m.group(1)) * {"": 1, "k": 1e3, "M": 1e6, "G": 1e9}[m.group(2)]


def seconds(s):
    m = re.fullmatch(r"\s*([0-9.]+)\s*(ns|us|ms|s)\s*", str(s))
    if not m:
        raise ValueError(f"bad time {s!r}")
    return float(m.group(1)) * {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0}[m.group(2)]


def kind(address):
    """What kind of value a setting holds, by its address: rate, time, int, number or choice."""
    last = address.split(".")
    if address in RUN:
        return "number" if address == "duration" else "int"
    if "largest_rate" in last or last[-1] == "rate":
        return "rate"
    if last[-1] == "delay":
        return "time"
    if "parts" in last:
        return "number"
    if last[-1] == "type":
        return "choice"
    return "int"


def ok(address, v):
    """Whether the program can be started with this setting at this value."""
    try:
        k = kind(address)
        if k == "rate":
            return rate_bps(v) >= 1   # a link's rate, a largest rate and a flow's rate are above 0 (a UDP flow that sends nothing is a flow to remove)
        if k == "time":
            return seconds(v) >= 0
        if k == "choice":
            return v in TCP_TYPES
        if k == "number":
            return type(v) in (int, float) and v > 0
        least = {"mtu": 576, "packet_bytes": 64, "tcpBufBytes": 4096}.get(address.split(".")[-1], 1)
        return type(v) is int and v >= least
    except (TypeError, ValueError):
        return False


def _adjacent(t):
    adj = {h["id"]: [] for h in t["hosts"]}
    for l in t["links"]:
        a, b = l["between"]
        adj[a].append((b, l["id"]))
        adj[b].append((a, l["id"]))
    return adj


def path(t, flow):
    """The way of a flow from its sender to its receiver: [(link id, the host that sends on it)], the shortest in links.
    None if there is no way; ValueError if two ways are equally short (the simulator would choose one of them itself)."""
    adj, src, dst = _adjacent(t), flow["from"], flow["to"]
    dist, count, prev, frontier = {src: 0}, {src: 1}, {}, [src]
    while frontier:
        nxt = []
        for h in frontier:
            for other, link in adj[h]:
                if other not in dist:
                    dist[other], count[other], prev[other] = dist[h] + 1, count[h], (h, link)
                    nxt.append(other)
                elif dist[other] == dist[h] + 1:
                    count[other] += count[h]
        frontier = nxt
    if dst not in dist:
        return None
    if count[dst] > 1:
        raise ValueError(f"flow {flow['id']} has {count[dst]} equally short ways from {src} to {dst}")
    way, h = [], dst
    while h != src:
        h, link = prev[h]
        way.append((link, h))
    return way[::-1]


def passes(t):
    """For each link that has a queue: the ids of the flows whose packets wait in it (they are sent on that link by the queue's host)."""
    out = {l["id"]: [] for l in t["links"] if l.get("queue")}
    for f in t["flows"]:
        for link, sender in path(t, f) or []:
            q = next(l for l in t["links"] if l["id"] == link).get("queue")
            if q and q["on"] == sender:
                out[link].append(f["id"])
    return out


def problems(t, limits=None):
    """Every reason a network cannot be built, or an empty list."""
    limits, bad = {**LIMITS, **(limits or {})}, []
    if not isinstance(t, dict) or not all(isinstance(t.get(k), list) for k in ("hosts", "links", "flows")):
        return ["a network has three lists: hosts, links and flows"]
    for k in ("hosts", "links", "flows"):
        if not all(isinstance(x, dict) and isinstance(x.get("id"), str) and re.fullmatch(ID, x["id"]) for x in t[k]):
            bad.append(f"every one of the {k} needs an id of at most 12 lower-case letters and digits that begins with a letter")
        if len(t[k]) > limits[k]:
            bad.append(f"{len(t[k])} {k}: a network holds at most {limits[k]}")
    if bad:
        return bad
    ids = [x["id"] for k in ("hosts", "links", "flows") for x in t[k]]
    bad += [f"the id {i} is used twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
    bad += [f"the id {i} is kept for a setting of the simulation" for i in ids if i in ("duration", "seed", "queue", "parts")]
    hosts = {h["id"] for h in t["hosts"]}
    if len(hosts) < 2 or not t["links"] or not t["flows"]:
        bad.append("a network needs at least two hosts, one link and one flow")
    pairs = set()
    for l in t["links"]:
        b = l.get("between")
        if not (isinstance(b, list) and len(b) == 2 and b[0] != b[1] and set(b) <= hosts):
            bad.append(f"link {l['id']} must join two different hosts of the network")
            continue
        if frozenset(b) in pairs:
            bad.append(f"link {l['id']}: {b[0]} and {b[1]} are joined by a link already (one link for each two hosts)")
        pairs.add(frozenset(b))
        for p in ("rate", "delay", "mtu", "device_queue"):
            if not ok(f"{l['id']}.{p}", l.get(p)):
                bad.append(f"link {l['id']}: {p} = {l.get(p)!r} is not a value the program accepts")
    if bad:
        return bad
    for f in t["flows"]:
        if f.get("kind") not in ("udp", "tcp") or f.get("from") not in hosts or f.get("to") not in hosts or f.get("from") == f.get("to"):
            bad.append(f"flow {f['id']} needs a kind (udp or tcp) and two different hosts of the network, from and to")
            continue
        try:
            way = path(t, f)
        except ValueError as e:
            bad.append(str(e) + ": remove a link so that there is one way")
            continue
        if way is None:
            bad.append(f"flow {f['id']}: there is no way from {f['from']} to {f['to']} (no chain of links joins them)")
            continue
        if f["kind"] == "udp":
            mtu = min(next(l for l in t["links"] if l["id"] == link)["mtu"] for link, _ in way)
            if not ok(f"{f['id']}.rate", f.get("rate")):
                bad.append(f"flow {f['id']}: rate = {f.get('rate')!r} is not a rate")
            if type(f.get("packet_bytes")) is not int or not 64 <= f["packet_bytes"] <= mtu - 28:
                bad.append(f"flow {f['id']}: packet_bytes must be a whole number from 64 to {mtu - 28} (the smallest MTU on its way less 28 bytes of headers)")
        elif f.get("type") not in TCP_TYPES:
            bad.append(f"flow {f['id']}: type must be one of {', '.join(TCP_TYPES)}")
    if bad:
        return bad
    through = passes(t)
    for l in t["links"]:
        q = l.get("queue")
        if q is None:
            continue
        if not isinstance(q, dict) or q.get("on") not in l["between"] or q.get("kind") not in ("fifo", "scheduler") or type(q.get("length")) is not int or q["length"] < 1:
            bad.append(f"the queue of link {l['id']} needs on (one of its two hosts), kind (fifo or scheduler) and length (packets, at least 1)")
            continue
        if q["kind"] == "scheduler":
            parts, largest = q.get("parts"), q.get("largest_rate") or {}
            if not isinstance(parts, dict) or not all(type(v) in (int, float) and v > 0 for v in parts.values()):
                bad.append(f"the scheduler of link {l['id']} needs parts: a number above 0 for each flow that passes it")
                continue
            missing, extra = [f for f in through[l["id"]] if f not in parts], [f for f in parts if f not in through[l["id"]]]
            if missing:
                bad.append(f"the scheduler of link {l['id']} has no part for {', '.join(missing)}, which pass it")
            if extra:
                bad.append(f"the scheduler of link {l['id']} has a part for {', '.join(extra)}, which do not pass it ({q['on']} does not send them on this link)")
            if not through[l["id"]]:
                bad.append(f"no flow passes the scheduler of link {l['id']}: put it on the side that sends, or use a plain queue")
            if not isinstance(largest, dict) or set(largest) - set(parts) or not all(ok(f"{l['id']}.queue.largest_rate.{f}", v) for f, v in largest.items()):
                bad.append(f"the scheduler of link {l['id']}: largest_rate gives a rate above 0 for some of the flows that have a part")
    return bad


def settings(t):
    """Every setting of the network by its address, in the order of the description: {address: value}."""
    out = {}
    for l in t["links"]:
        for p in ("rate", "delay", "mtu", "device_queue"):
            out[f"{l['id']}.{p}"] = l[p]
        q = l.get("queue")
        if q:
            out[f"{l['id']}.queue.length"] = q["length"]
            for f, v in (q.get("parts") or {}).items():
                out[f"{l['id']}.queue.parts.{f}"] = v
            for f, v in (q.get("largest_rate") or {}).items():
                out[f"{l['id']}.queue.largest_rate.{f}"] = v
    for f in t["flows"]:
        if f["kind"] == "udp":
            out[f"{f['id']}.rate"], out[f"{f['id']}.packet_bytes"] = f["rate"], f["packet_bytes"]
        else:
            out[f"{f['id']}.type"] = f["type"]
    return out


def with_values(t, values):
    """A copy of the network with those settings (by address) at those values; an address that is not one of its settings is an error."""
    t, have = copy.deepcopy(t), settings(t)
    for address, v in values.items():
        if address not in have:
            raise ValueError(f"{address} is not a setting of this network")
        obj, rest = address.split(".", 1)
        x = next(x for k in ("links", "flows") for x in t[k] if x["id"] == obj)   # (an address that is in settings(t) names an object that is there)
        keys = rest.split(".")
        if keys[0] == "queue":
            x, keys = x["queue"], keys[1:]
        if len(keys) == 2:
            x[keys[0]][keys[1]] = v
        else:
            x[keys[0]] = v
    return t


def outputs(t):
    """The measures a simulation of this network gives, with what each is: {name: meaning}."""
    out = {}
    for f in t["flows"]:
        out[f"{f['id']}_goodput_bps"] = f"payload bits per second delivered to the receiver of flow {f['id']} ({f['to']})"
        if f["kind"] == "udp":
            out[f"{f['id']}_loss_frac"] = f"fraction of the packets flow {f['id']} sent that never arrived"
        else:
            out[f"{f['id']}_retrans"] = f"TCP segments the sender of flow {f['id']} sent again"
    for l in t["links"]:
        a, b = l["between"]
        q = l.get("queue")
        back = a if q and q["on"] == b else b   # the side that has no described queue
        out[f"{l['id']}_util"] = f"bits sent on link {l['id']} from {a} to {b}, divided by the link's rate"
        out[f"{l['id']}_util_back"] = f"the same from {b} to {a}"
        if q and q["kind"] == "scheduler":
            for f in q["parts"]:
                out[f"{l['id']}_drops_{f}"] = f"packets of flow {f} dropped from its queue in the scheduler of link {l['id']}"
        else:
            out[f"{l['id']}_drops"] = f"packets dropped from the queue in front of link {l['id']} on the side of {q['on'] if q else a}"
        out[f"{l['id']}_drops_back"] = f"packets dropped from the plain queue in front of link {l['id']} on the side of {back}"
    return out


EDIT = ("do", "id", "kind", "from", "to", "on", "rate", "type")   # the fields of one change, all stated every time ("" where one does not apply)
DOES = ("add_host", "add_link", "add_flow", "add_queue", "remove")


def sync(t):
    """After a change: every scheduler has a part for exactly the flows that pass it. A flow that is new there gets the
    mean of the parts that stand (0.5 where there is none); the part and the largest rate of a flow that no longer
    passes are dropped."""
    try:
        through = passes(t)
    except (ValueError, KeyError, StopIteration):
        return t   # a flow with two ways, or one that names a host that is gone: problems() says so
    for l in t["links"]:
        q = l.get("queue")
        if q and q.get("kind") == "scheduler":
            old = q.get("parts") or {}
            fill = round(sum(old.values()) / len(old), 6) if old else 0.5
            q["parts"] = {f: old.get(f, fill) for f in through[l["id"]]}
            q["largest_rate"] = {f: v for f, v in (q.get("largest_rate") or {}).items() if f in q["parts"]}
    return t


def apply(t, edits):
    """The network with a list of changes made, in order (a simulation's "structure"). Each change states every field of
    EDIT; `do` is one of DOES:
      add_host   id
      add_link   id, from, to (the two hosts), rate (empty: 1Gbps); delay 50us, MTU 1500, a device queue of 10 packets
      add_flow   id, kind (udp or tcp), from, to, and rate for udp (empty: 100Mbps) or type for tcp (empty: TcpCubic)
      add_queue  id (the link), on (the host whose sending side it is), kind (scheduler or fifo; empty: scheduler); 100 packets
      remove     kind (host, link, flow or queue) and id (a queue's id is its link's). A host goes with its links and
                 with the flows that start or end at it.
    ValueError with the reason if a change cannot be made. Whether the result can be built is for problems()."""
    t = copy.deepcopy(t)
    ids = lambda: {x["id"] for k in ("hosts", "links", "flows") for x in t[k]}
    for i, e in enumerate(edits or []):
        n = f"change {i + 1}"
        if not isinstance(e, dict) or e.get("do") not in DOES:
            raise ValueError(f"{n}: do must be one of {', '.join(DOES)}")
        do, oid = e["do"], e.get("id")
        if do != "remove" and do != "add_queue" and (not isinstance(oid, str) or not re.fullmatch(ID, oid) or oid in ids()):
            raise ValueError(f"{n}: a new object needs an id of its own: at most 12 lower-case letters and digits that begin with a letter, not used yet (got {oid!r})")
        hosts = {h["id"] for h in t["hosts"]}
        if do == "add_host":
            t["hosts"].append({"id": oid})
        elif do == "add_link":
            if e.get("from") not in hosts or e.get("to") not in hosts:
                raise ValueError(f"{n}: a link joins two hosts of the network (from, to)")
            t["links"].append({"id": oid, "between": [e["from"], e["to"]], "rate": e.get("rate") or "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10})
        elif do == "add_flow":
            if e.get("kind") not in ("udp", "tcp") or e.get("from") not in hosts or e.get("to") not in hosts:
                raise ValueError(f"{n}: a flow needs a kind (udp or tcp) and two hosts of the network (from, to)")
            t["flows"].append({"id": oid, "kind": "udp", "from": e["from"], "to": e["to"], "rate": e.get("rate") or "100Mbps", "packet_bytes": 1400} if e["kind"] == "udp"
                              else {"id": oid, "kind": "tcp", "from": e["from"], "to": e["to"], "type": e.get("type") or "TcpCubic"})
        elif do == "add_queue":
            link = next((l for l in t["links"] if l["id"] == oid), None)
            if link is None or link.get("queue") or e.get("on") not in link["between"]:
                raise ValueError(f"{n}: a queue is put on a link that has none (id: the link), on the side of one of its two hosts (on)")
            link["queue"] = {"on": e["on"], "kind": e.get("kind") if e.get("kind") in ("scheduler", "fifo") else "scheduler", "length": 100, "parts": {}, "largest_rate": {}}
        else:
            kind = e.get("kind")
            if kind == "host" and oid in hosts:
                t["hosts"] = [h for h in t["hosts"] if h["id"] != oid]
                t["links"] = [l for l in t["links"] if oid not in l["between"]]
                t["flows"] = [f for f in t["flows"] if oid not in (f["from"], f["to"])]
            elif kind == "link" and any(l["id"] == oid for l in t["links"]):
                t["links"] = [l for l in t["links"] if l["id"] != oid]
            elif kind == "flow" and any(f["id"] == oid for f in t["flows"]):
                t["flows"] = [f for f in t["flows"] if f["id"] != oid]
            elif kind == "queue" and any(l["id"] == oid and l.get("queue") for l in t["links"]):
                next(l for l in t["links"] if l["id"] == oid).pop("queue")
            else:
                raise ValueError(f"{n}: there is no {kind} {oid!r} to remove (kind: host, link, flow or queue; a queue's id is its link's)")
    return sync(t)


def objects(t):
    """The objects of a network as "kind:id" (a queue by its link's id)."""
    return {f"host:{h['id']}" for h in t["hosts"]} | {f"link:{l['id']}" for l in t["links"]} | {f"flow:{f['id']}" for f in t["flows"]} | {f"queue:{l['id']}" for l in t["links"] if l.get("queue")}


def structure_problems(st, t=None):
    """Every reason a brief's "structure" cannot be used (with t, the brief's network): {"may_change": bool, "most": {hosts, links, flows}, "locked": ["kind:id", ...]}."""
    if not isinstance(st, dict) or type(st.get("may_change")) is not bool:
        return ["structure needs may_change: true or false (whether the AI may add and remove objects)"]
    most, locked, bad = st.get("most") or {}, st.get("locked") or [], []
    if not isinstance(most, dict) or set(most) - set(LIMITS) or not all(type(v) is int and 1 <= v <= LIMITS[k] for k, v in most.items()):
        bad.append(f"structure.most gives whole numbers for hosts, links and flows, at most {LIMITS['hosts']}, {LIMITS['links']} and {LIMITS['flows']}")
    elif t and any(len(t[k]) > most.get(k, LIMITS[k]) for k in LIMITS):
        bad.append("structure.most is smaller than the network the session starts from")
    if not isinstance(locked, list) or not all(isinstance(x, str) for x in locked) or (t and set(locked) - objects(t)):
        bad.append("structure.locked names objects of the network as kind:id (host, link, flow, or queue with its link's id)")
    return bad


def changed_problems(t0, t1, st, goal, outs_needed=()):
    """Why a changed network (t1, from the session's t0) may not be simulated, beyond what problems() says of it: a
    locked object is gone, a limit of the brief is passed, or a measure the aim names would not exist."""
    most = {**LIMITS, **(st.get("most") or {})}
    bad = [f"{len(t1[k])} {k}: this brief allows at most {most[k]}" for k in LIMITS if len(t1[k]) > most[k]]
    gone = sorted(set(st.get("locked") or []) & (objects(t0) - objects(t1)))
    if gone:
        bad.append(f"{', '.join(g.replace(':', ' ') for g in gone)} may not be removed (the operator keeps it)")
    have = outputs(t1) if not problems(t1) else {}
    aim = [m for m in outs_needed if have and m not in have]
    if aim:
        bad.append(f"the aim is about {', '.join(aim)}, which this network would not have: what the aim measures cannot be removed")
    return bad


def tools_told(tools):
    """What a session on a network is told about its tools: the manifest's lines, with the series described by the
    columns `net` writes (two-hosts has others) and without the search of a packet trace (`net` writes none)."""
    told = {k: v for k, v in tools.items() if k != "grep_trace"}
    told["series"] = ("series(run_id, every_n): per-100ms samples of a run: t, then for each flow <flow>_bps (and <flow>_cwnd for a TCP flow), then for each "
                      "described queue the packets waiting at the sample time (<link>_q_<flow> for a scheduler, <link>_q for a plain queue) and the packets dropped "
                      "since traffic began (<link>_drops_<flow>, <link>_drops) (at most 100 rows; the measured seconds begin at t = 2)")
    return told


def text(t, run):
    """The description as the program `net` reads it (network.txt). run: duration, seed and, if set, tcpInitCwnd and tcpBufBytes."""
    lines = [f"host {h['id']}" for h in t["hosts"]]
    for l in t["links"]:
        lines.append(f"link {l['id']} {l['between'][0]} {l['between'][1]} rate={l['rate']} delay={l['delay']} mtu={l['mtu']} devq={l['device_queue']}".replace(" Mbps", "Mbps"))
        q = l.get("queue")
        if q:
            s = f"queue {l['id']} {q['on']} kind={q['kind']} length={q['length']}"
            if q["kind"] == "scheduler":
                s += " parts=" + ",".join(f"{f}:{v}" for f, v in q["parts"].items())
                if q.get("largest_rate"):
                    s += " largest=" + ",".join(f"{f}:{str(v).replace(' ', '')}" for f, v in q["largest_rate"].items())
            lines.append(s)
    for f in t["flows"]:
        lines.append(f"flow {f['id']} udp {f['from']} {f['to']} rate={str(f['rate']).replace(' ', '')} packet={f['packet_bytes']}" if f["kind"] == "udp"
                     else f"flow {f['id']} tcp {f['from']} {f['to']} type={f['type']}")
    tcp = [f"{k}={run[n]}" for k, n in (("initcwnd", "tcpInitCwnd"), ("buf", "tcpBufBytes")) if run.get(n)]
    if tcp:
        lines.append("tcp " + " ".join(tcp))
    lines.append(f"run duration={run['duration']} seed={run['seed']}")
    return "\n".join(lines) + "\n"
