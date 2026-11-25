"""A network described as data: hosts joined by point-to-point links, UDP and TCP flows between them, and on one
sending side of a link a plain queue or the scheduler. A brief with "topology" is run by the program `net`
(ns-3.49/scratch/net), which builds what the description says; a brief without it is run by `two-hosts`, as before.

    {"hosts": [{"id": "sender"}, {"id": "receiver"}],
     "links": [{"id": "l1", "between": ["sender", "receiver"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10,
                "queue": {"on": "sender", "kind": "scheduler", "length": 100, "parts": {"udp": 0.5, "tcp": 0.5}, "largest_rate": {}}}],
     "flows": [{"id": "udp", "kind": "udp", "from": "sender", "to": "receiver", "rate": "2Gbps", "packet_bytes": 1400},
               {"id": "tcp", "kind": "tcp", "from": "sender", "to": "receiver", "type": "TcpCubic"}]}

A link is a channel and two devices, one on each of its hosts (as in ns-3). Its line gives what the two devices have in
common; where an end differs, or to put a queue on either or both of its sending sides, the link carries "ends":
    "ends": {"a": {"rate": "200Mbps", "device_queue": 20, "queue": {"kind": "scheduler", "length": 100, "parts": {...}}},
             "b": {"queue": {"kind": "fifo", "length": 50}}}
(the older form, "queue" with "on", describes the queue of one side and is read as before; a link may have it and, in "ends", the other side's).
A flow is an ns-3 application and the socket it opens. "kind" is the socket (ns-3: the application's Protocol): udp or
tcp. "app" is the application that sends: "onoff" (OnOffApplication, always on: packets of packet_bytes at a constant
rate) or "bulk" (BulkSendApplication: as fast as the socket accepts, so it needs a TCP socket). Left out, a udp flow is
onoff and a tcp flow is bulk, which is every flow written before 2026-11-18. So a tcp flow may send at a constant rate:
    {"id": "t1", "kind": "tcp", "app": "onoff", "from": "a", "to": "b", "rate": "200Mbps", "packet_bytes": 1400, "type": "TcpCubic"}
A flow may also state its application's times, as ns-3 has them: "start" and "stop" (StartTime and StopTime, seconds of the
simulation; left out: 1 s and the end; the measured seconds begin at 2 s), for OnOff "on_time" and "off_time" (the lengths
of its on and off periods, given together; left out: always on) and "max_bytes" (it stops after that many bytes).
An end of a link may state its device's own "mtu" and its "loss": the part of the packets arriving at that device that it
receives in error and drops (ns-3: a RateErrorModel as the device's ReceiveErrorModel); the measure <link>_lost_<host> counts them.
A queue's kind is the queue disc of that device: one of ns-3's own (QUEUE_DISCS: fifo, pfifofast, codel, fqcodel, red, pie; each with
ns-3's own settings and "length" as its MaxSize) or "scheduler", this project's FlowQueueDisc.
TCP's options are settings of the whole simulation, as ns-3's attribute defaults are: tcpSack and tcpTimestamps (1 or 0), tcpDelAck
(the segments one acknowledgement may wait for), beside tcpInitCwnd and tcpBufBytes.
A scheduler has one queue for each of its parts. A part is named after one flow (that flow has the queue to itself), or
after a class, a group of flows that share the queue: "classes": {"udp": ["u1", "u2"]}.

A setting of the network has an address, object.property: l1.rate, l1.delay, l1.mtu, l1.device_queue,
l1.queue.length, l1.queue.parts.udp, l1.queue.largest_rate.tcp, udp.rate, udp.packet_bytes, tcp.type; of an end,
l1.a.rate, l1.a.device_queue, l1.a.queue.length, l1.a.queue.parts.udp. A brief fixes
it (the value in the description) or makes it a knob (an entry of "knobs" under that address).
The measures are made from the network (outputs): per flow, per link, per queue.
How a scheduler divides the link (the scheduling policy) is not part of the description."""
import copy, re

ID = r"[a-z][a-z0-9]{0,11}"
LIMITS = {"hosts": 8, "links": 12, "flows": 8}     # the most a network may hold
TCP_TYPES = ("TcpCubic", "TcpNewReno", "TcpLinuxReno", "TcpBbr", "TcpVegas", "TcpBic")
QUEUE_DISCS = {"fifo": "FifoQueueDisc", "pfifofast": "PfifoFastQueueDisc", "codel": "CoDelQueueDisc", "fqcodel": "FqCoDelQueueDisc", "red": "RedQueueDisc", "pie": "PieQueueDisc"}   # a queue's kind -> ns-3's queue disc (scheduler: the project's FlowQueueDisc)
QUEUE_KINDS = (*QUEUE_DISCS, "scheduler")
FLOW_TIMES = ("start", "stop", "on_time", "off_time", "max_bytes")   # what a flow may state of its application's times, in this order
RUN = ("duration", "seed", "tcpInitCwnd", "tcpBufBytes", "tcpSack", "tcpTimestamps", "tcpDelAck")   # settings of a simulation that belong to no object (as in two-hosts)
DEFAULT = {"hosts": [{"id": "sender"}, {"id": "receiver"}],
           "links": [{"id": "l1", "between": ["sender", "receiver"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10,
                      "queue": {"on": "sender", "kind": "scheduler", "length": 100, "parts": {"udp": 0.5, "tcp": 0.5}, "largest_rate": {}}}],
           "flows": [{"id": "udp", "kind": "udp", "from": "sender", "to": "receiver", "rate": "2Gbps", "packet_bytes": 1400},
                     {"id": "tcp", "kind": "tcp", "from": "sender", "to": "receiver", "type": "TcpCubic"}]}


def app(f):
    """The ns-3 application of a flow: 'onoff' (a constant rate) or 'bulk' (as fast as TCP accepts). Not stated: udp is onoff, tcp is bulk."""
    return f.get("app") or ("onoff" if f.get("kind") == "udp" else "bulk")


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
    if last[-1] in ("start", "stop", "on_time", "off_time", "loss"):
        return "number"
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
        word = address.split(".")[-1]
        if k == "number":   # a part and an on period are above 0; a time may be 0; a loss is a part of the packets
            return type(v) in (int, float) and (0 <= v <= 1 if word == "loss" else v >= 0 if word in ("start", "stop", "off_time") else v > 0)
        if word in ("tcpSack", "tcpTimestamps"):
            return v in (0, 1) and type(v) is int
        least = {"mtu": 576, "packet_bytes": 64, "tcpBufBytes": 4096}.get(word, 1)
        return type(v) is int and v >= least
    except (TypeError, ValueError):
        return False


KEPT = ("duration", "seed", "queue", "parts", "ends", "classes", "largest_rate", "length", "rate", "delay", "mtu", "device_queue", "type", "packet_bytes", "start", "stop", "on_time", "off_time", "max_bytes", "loss")   # no object is named so: they are words of an address


def ends(l):
    """The two ends of a link as ns-3 has them: {host: {"rate", "device_queue", "queue"}}: the device of that host on the link (its rate and its
    transmit queue: the link's, unless the end states its own) and the queue in front of it (None: not described, a plain queue of 100 packets)."""
    e, q, out = l.get("ends") or {}, l.get("queue"), {}
    for h in l["between"]:
        x = e.get(h) or {}
        out[h] = {"rate": x.get("rate", l.get("rate")), "device_queue": x.get("device_queue", l.get("device_queue")), "mtu": x.get("mtu", l.get("mtu")), "loss": x.get("loss"),
                  "queue": x["queue"] if "queue" in x else ({k: v for k, v in q.items() if k != "on"} if isinstance(q, dict) and q.get("on") == h else None)}
    return out


def queues(t):
    """Every described queue of the network: [(link, host, queue, address)]; address is where its settings stand: <link>.queue in the older form, <link>.<host>.queue."""
    out = []
    for l in t["links"]:
        for h in l["between"]:
            if "queue" in ((l.get("ends") or {}).get(h) or {}):
                out.append((l, h, l["ends"][h]["queue"], f"{l['id']}.{h}.queue"))
            elif isinstance(l.get("queue"), dict) and l["queue"].get("on") == h:
                out.append((l, h, l["queue"], f"{l['id']}.queue"))
    return out


def members(q, name):
    """The flows that wait in the queue of a scheduler's part: the class's flows, or the one flow the part is named after."""
    return list((q.get("classes") or {}).get(name, [name]))


def through(t):
    """For each described queue, the flows whose packets wait in it (its host sends them on its link): {(link id, host): [flow ids]}."""
    out = {(l["id"], h): [] for l, h, q, a in queues(t)}
    for f in t["flows"]:
        for link, sender in path(t, f) or []:
            if (link, sender) in out:
                out[(link, sender)].append(f["id"])
    return out


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
    """For each link that has a queue in the older form: the ids of the flows whose packets wait in it (they are sent on that link by the queue's host)."""
    th = through(t)
    return {l["id"]: th[(l["id"], l["queue"]["on"])] for l in t["links"] if l.get("queue")}


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
    bad += [f"the id {i} is kept for a setting of the simulation" for i in ids if i in KEPT]
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
        e = l.get("ends")
        if e is not None:   # a link whose two ends are described each by itself
            if not isinstance(e, dict) or set(e) - set(b) or not all(isinstance(x, dict) and not set(x) - {"rate", "device_queue", "mtu", "loss", "queue"} for x in e.values()) \
                    or (isinstance(l.get("queue"), dict) and "queue" in (e.get(l["queue"].get("on")) or {})):
                bad.append(f"link {l['id']}: ends describes its two devices by their hosts ({b[0]}, {b[1]}), each with rate, device_queue, mtu, loss and queue where it has its own; one side has one queue (the older queue, or its end's)")
                continue
            for h, x in e.items():
                bad += [f"link {l['id']}, the device of {h}: {p} = {x[p]!r} is not a value the program accepts" for p in ("rate", "device_queue", "mtu", "loss") if p in x and not ok(f"{l['id']}.{h}.{p}", x[p])]
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
        if app(f) not in ("onoff", "bulk"):
            bad.append(f"flow {f['id']}: app must be onoff (ns-3's OnOffApplication: a constant rate) or bulk (BulkSendApplication: as fast as TCP accepts)")
            continue
        if app(f) == "bulk" and f["kind"] == "udp":
            bad.append(f"flow {f['id']}: ns-3's BulkSendApplication needs a TCP socket; over UDP an application sends at a constant rate (app onoff)")
            continue
        if app(f) == "onoff":
            mtu = min(min(x["mtu"] for x in ends(next(l for l in t["links"] if l["id"] == link)).values()) for link, _ in way)
            if not ok(f"{f['id']}.rate", f.get("rate")):
                bad.append(f"flow {f['id']}: rate = {f.get('rate')!r} is not a rate")
            if type(f.get("packet_bytes")) is not int or not 64 <= f["packet_bytes"] <= mtu - 28:
                bad.append(f"flow {f['id']}: packet_bytes must be a whole number from 64 to {mtu - 28} (the smallest MTU on its way less 28 bytes of headers)")
        if f["kind"] == "tcp" and f.get("type") not in TCP_TYPES:
            bad.append(f"flow {f['id']}: type must be one of {', '.join(TCP_TYPES)}")
        bad += [f"flow {f['id']}: {p} = {f[p]!r} is not a value the program accepts" for p in FLOW_TIMES if p in f and not ok(f"{f['id']}.{p}", f[p])]
        if ("on_time" in f) != ("off_time" in f):
            bad.append(f"flow {f['id']}: on_time and off_time are given together (the lengths of the on and the off period)")
        elif "on_time" in f and app(f) != "onoff":
            bad.append(f"flow {f['id']}: ns-3's BulkSendApplication has no on and off periods; they belong to OnOff (app onoff)")
        if all(type(f.get(p)) in (int, float) for p in ("start", "stop")) and f["stop"] <= f["start"]:
            bad.append(f"flow {f['id']}: it stops (stop = {f['stop']}) before it starts (start = {f['start']})")
    if bad:
        return bad
    for l in t["links"]:   # the older form names the side of its queue
        q = l.get("queue")
        if q is not None and not (isinstance(q, dict) and q.get("on") in l["between"]):
            bad.append(f"the queue of link {l['id']} needs on (one of its two hosts), kind ({', '.join(QUEUE_KINDS[:-1])} or scheduler) and length (packets, at least 1)")
    if bad:
        return bad
    waits, named = through(t), {}
    for l, h, q, a in queues(t):
        of = f"the queue of link {l['id']}" + (f" on the side of {h}" if a.count(".") == 2 else "")
        if not isinstance(q, dict) or q.get("kind") not in QUEUE_KINDS or type(q.get("length")) is not int or q["length"] < 1:
            bad.append(f"{of} needs " + ("on (one of its two hosts), " if a.count(".") == 1 else "") + f"kind ({', '.join(QUEUE_KINDS[:-1])} or scheduler) and length (packets, at least 1)")
            continue
        if q["kind"] != "scheduler":
            continue
        sch, flows = of.replace("the queue", "the scheduler"), waits[(l["id"], h)]
        parts, largest, classes = q.get("parts"), q.get("largest_rate") or {}, q.get("classes") or {}
        if not isinstance(parts, dict) or not all(type(v) in (int, float) and v > 0 for v in parts.values()):
            bad.append(f"{sch} needs parts: a number above 0 for each flow that passes it")
            continue
        if not isinstance(classes, dict) or not all(isinstance(k, str) and re.fullmatch(ID, k) and k not in KEPT and isinstance(v, list) and v and all(isinstance(f, str) for f in v) for k, v in classes.items()) \
                or set(classes) - set(parts) or any(k in {f["id"] for f in t["flows"]} for k in classes):
            bad.append(f"{sch}: classes names groups of flows that share one of its queues: a name of its own (not a flow's) that has a part, and the flows in it")
            continue
        held = [f for name in parts for f in members(q, name)]   # the flows the parts hold, through a class or by their own name
        missing, extra, twice = [f for f in flows if f not in held], [f for f in dict.fromkeys(held) if f not in flows], sorted({f for f in held if held.count(f) > 1})
        if missing:
            bad.append(f"{sch} has no part for {', '.join(missing)}, which pass it")
        if extra:
            bad.append(f"{sch} has a part for {', '.join(extra)}, which do not pass it ({h} does not send them on this link)")
        if twice:
            bad.append(f"{sch}: {', '.join(twice)} would wait in two of its queues")
        if not flows:
            bad.append(f"no flow passes {sch}: a scheduler divides its link between the flows that pass it on that side")
        if not isinstance(largest, dict) or set(largest) - set(parts) or not all(ok(f"{a}.largest_rate.{f}", v) for f, v in largest.items()):
            bad.append(f"{sch}: largest_rate gives a rate above 0 for some of the parts")
        again = sorted(set(parts) & named.setdefault(l["id"], set()))   # the measures of a link are named by its parts: a name stands once on a link
        if again:
            bad.append(f"link {l['id']}: the part {', '.join(again)} is named on both of its sides; give the two classes different names")
        named[l["id"]] |= set(parts)
    return bad


def settings(t):
    """Every setting of the network by its address, in the order of the description: {address: value}."""
    out = {}
    for l in t["links"]:
        for p in ("rate", "delay", "mtu", "device_queue"):
            out[f"{l['id']}.{p}"] = l[p]
        for h, x in (l.get("ends") or {}).items():   # what an end states of its own device
            for p in ("rate", "device_queue", "mtu", "loss"):
                if p in x:
                    out[f"{l['id']}.{h}.{p}"] = x[p]
        for _, h, q, a in ((x for x in queues(t) if x[0] is l)):
            out[f"{a}.length"] = q["length"]
            for f, v in (q.get("parts") or {}).items():
                out[f"{a}.parts.{f}"] = v
            for f, v in (q.get("largest_rate") or {}).items():
                out[f"{a}.largest_rate.{f}"] = v
    for f in t["flows"]:
        if app(f) == "onoff":
            out[f"{f['id']}.rate"], out[f"{f['id']}.packet_bytes"] = f["rate"], f["packet_bytes"]
        if f["kind"] == "tcp":
            out[f"{f['id']}.type"] = f["type"]
        for p in FLOW_TIMES:   # what the flow states of its application's times (left out: the program's, and no setting)
            if p in f:
                out[f"{f['id']}.{p}"] = f[p]
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
        if keys[0] in (x.get("ends") or {}):   # a setting of one end of a link: <link>.<host>....
            x, keys = x["ends"][keys[0]], keys[1:]
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
        e = ends(l)
        out[f"{l['id']}_util"] = f"bits sent on link {l['id']} from {a} to {b}, divided by the " + ("link's rate" if e[a]["rate"] == l["rate"] else f"rate of {a}'s device")
        out[f"{l['id']}_util_back"] = f"the same from {b} to {a}" + ("" if e[b]["rate"] == l["rate"] else f", divided by the rate of {b}'s device")
        for h in (a, b):
            if e[h]["loss"] is not None:
                out[f"{l['id']}_lost_{h}"] = f"packets the device of {h} on link {l['id']} received in error and dropped (its loss)"
        # the drops, named as the program names them: a scheduler's by its parts; a plain queue's <link>_drops, and <link>_drops_back for the
        # side that is not described (or, where both sides have a described plain queue, for the side of the second host)
        given, front, back = [e[h]["queue"] is not None for h in (a, b)], {}, {}
        for side, h in enumerate((a, b)):
            q = e[h]["queue"]
            if q and q["kind"] == "scheduler":
                for name in q["parts"]:
                    who = members(q, name)
                    front[f"{l['id']}_drops_{name}"] = (f"packets of flow {name} dropped from its queue in the scheduler of link {l['id']}" if who == [name]
                                                       else f"packets of the flows {', '.join(who)} dropped from the queue they share (class {name}) in the scheduler of link {l['id']} on the side of {h}")
            elif q:
                (back if all(given) and side == 1 else front)[f"{l['id']}_drops" + ("_back" if all(given) and side == 1 else "")] = f"packets dropped from the queue in front of link {l['id']} on the side of {h}"
            elif any(given) or side == 1:
                back[f"{l['id']}_drops_back"] = f"packets dropped from the plain queue in front of link {l['id']} on the side of {h}"
            else:
                front[f"{l['id']}_drops"] = f"packets dropped from the queue in front of link {l['id']} on the side of {h}"
        out.update(front)
        out.update(back)
    return out


EDIT = ("do", "id", "kind", "from", "to", "on", "rate", "type", "app")   # the fields of one change, all stated every time ("" where one does not apply)
DOES = ("add_host", "add_link", "add_flow", "add_queue", "remove")


def record_columns(t):
    """Every column a simulation of this network records over time: the series (a sample every 0.1 s) and the probe (a finer record that only
    listens), named as the program `net` names them."""
    series, fine = [], []
    for f in t["flows"]:
        series.append(f"{f['id']}_bps")
        fine.append(f"{f['id']}_bps")
        if f["kind"] == "tcp":
            series.append(f"{f['id']}_cwnd")
            fine += [f"{f['id']}_{k}" for k in ("cwnd", "ssthresh", "inflight", "rwnd", "rtt_ms", "rto_ms")]
    for l in t["links"]:
        e = ends(l)
        both = all(e[h]["queue"] is not None for h in l["between"])
        for side, h in enumerate(l["between"]):
            q = e[h]["queue"]
            if q and q["kind"] == "scheduler":
                for name in q["parts"]:
                    series += [f"{l['id']}_q_{name}", f"{l['id']}_drops_{name}"]
                    fine += [f"{l['id']}_wait_{name}_ms", f"{l['id']}_q_{name}"]
            elif q:
                back = "_back" if both and side == 1 else ""
                series += [f"{l['id']}_q{back}", f"{l['id']}_drops{back}"]
                fine += [f"{l['id']}_wait{back}_ms", f"{l['id']}_q{back}"]
            fine.append(f"{l['id']}_devq" + ("_back" if side == 1 else ""))
    return series, fine


def sync(t):
    """After a change: every scheduler has a part for exactly the flows that pass it. A flow that is new there gets a queue of its own with the
    mean of the parts that stand (0.5 where there is none); a flow that no longer passes leaves its queue, and a part (with its largest rate, and
    its class) that holds no flow any more is dropped."""
    try:
        waits = through(t)
    except (ValueError, KeyError, StopIteration):
        return t   # a flow with two ways, or one that names a host that is gone: problems() says so
    for l, h, q, a in queues(t):
        if isinstance(q, dict) and q.get("kind") == "scheduler":
            flows, old, classes = waits[(l["id"], h)], q.get("parts") or {}, {}
            for name, fl in (q.get("classes") or {}).items():
                left = [f for f in fl if f in flows]
                if left and name in old:
                    classes[name] = left
            held = {f for fl in classes.values() for f in fl}
            fill = round(sum(old.values()) / len(old), 6) if old else 0.5
            parts = {name: v for name, v in old.items() if name in classes}
            parts.update({f: old.get(f, fill) for f in flows if f not in held})
            q["parts"] = {k: parts[k] for k in list(old) + [k for k in parts if k not in old] if k in parts}   # the order that stood, new ones after
            q["largest_rate"] = {f: v for f, v in (q.get("largest_rate") or {}).items() if f in q["parts"]}
            if classes or "classes" in q:
                q["classes"] = classes
                if not classes:
                    q.pop("classes")
    return t


NEW_LINK = {"rate": "1Gbps", "delay": "50us"}   # a link a change adds, where the brief's structure says nothing of new links


def apply(t, edits, new_link=None):
    """The network with a list of changes made, in order (a simulation's "structure"). Each change states every field of
    EDIT; `do` is one of DOES:
      add_host   id
      add_link   id, from, to (the two hosts), rate (empty: 1Gbps, or the brief's cap); delay 50us, or the brief's; MTU 1500, a device
                 queue of 10 packets. new_link: the brief's structure.new_link ({rate_max, delay}, 2026-11-23): an empty rate is the cap,
                 and the delay is the brief's. Its two hosts stand in the order of the network's hosts, so that a link written from b
                 to c and the same written from c to b are one network (and its measures name the same direction)
      add_flow   id, kind (udp or tcp), from, to, and rate for udp (empty: 100Mbps) or type for tcp (empty: TcpCubic)
      add_queue  id (the link), on (the host whose sending side it is), kind (scheduler or fifo; empty: scheduler); 100 packets.
                 A link may have one on each of its two sides.
      remove     kind (host, link, flow or queue) and id (a queue's id is its link's; on: its side, where the link has two).
                 A host goes with its links and with the flows that start or end at it.
    ValueError with the reason if a change cannot be made. Whether the result can be built is for problems()."""
    t = copy.deepcopy(t)
    nl = {"rate": (new_link or {}).get("rate_max") or NEW_LINK["rate"], "delay": (new_link or {}).get("delay") or NEW_LINK["delay"]}
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
            order = [h["id"] for h in t["hosts"]]
            if not e.get("rate"):   # v2: stated, never filled in (left empty it was the brief's cap, the best value there is)
                raise ValueError(f"{n}: a new link states its rate")
            t["links"].append({"id": oid, "between": sorted([e["from"], e["to"]], key=order.index), "rate": e["rate"], "delay": nl["delay"], "mtu": 1500, "device_queue": 10})
        elif do == "add_flow":
            if e.get("kind") not in ("udp", "tcp") or e.get("from") not in hosts or e.get("to") not in hosts:
                raise ValueError(f"{n}: a flow needs a kind (udp or tcp) and two hosts of the network (from, to)")
            if e.get("app") not in (None, "", "onoff", "bulk") or (e.get("app") == "bulk" and e["kind"] == "udp"):
                raise ValueError(f"{n}: app is onoff (a constant rate), bulk (always has data: tcp only) or empty (udp: onoff, tcp: bulk)")
            t["flows"].append({"id": oid, "kind": "udp", "from": e["from"], "to": e["to"], "rate": e.get("rate") or "100Mbps", "packet_bytes": 1400} if e["kind"] == "udp"
                              else {"id": oid, "kind": "tcp", "app": "onoff", "from": e["from"], "to": e["to"], "rate": e.get("rate") or "100Mbps", "packet_bytes": 1400, "type": e.get("type") or "TcpCubic"} if e.get("app") == "onoff"
                              else {"id": oid, "kind": "tcp", "from": e["from"], "to": e["to"], "type": e.get("type") or "TcpCubic"})
        elif do == "add_queue":
            link = next((l for l in t["links"] if l["id"] == oid), None)
            if link is None or e.get("on") not in link["between"] or ends(link)[e["on"]]["queue"] is not None:
                raise ValueError(f"{n}: a queue is put on a side of a link that has none there (id: the link; on: one of its two hosts)")
            if e.get("kind") not in QUEUE_KINDS:   # v2: stated, never filled in (an empty or unknown kind became a scheduler)
                raise ValueError(f"{n}: a new queue states its kind: one of {', '.join(sorted(QUEUE_KINDS))}")
            new = {"kind": e["kind"], "length": 100, "parts": {}, "largest_rate": {}}
            if not any(x["queue"] is not None for x in ends(link).values()):
                link["queue"] = {"on": e["on"], **new}   # the first queue of a link: the older form, as before
            else:   # the other side's: in the link's ends (the first keeps its place and its addresses)
                link.setdefault("ends", {}).setdefault(e["on"], {})["queue"] = new
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
            elif kind == "queue" and any(l["id"] == oid and any(x["queue"] is not None for x in ends(l).values()) for l in t["links"]):
                link = next(l for l in t["links"] if l["id"] == oid)
                sides = [h for h, x in ends(link).items() if x["queue"] is not None]
                side = e.get("on") if e.get("on") in sides else sides[0] if len(sides) == 1 else None
                if side is None:
                    raise ValueError(f"{n}: link {oid} has a queue on each side: say which one (on: {sides[0]} or {sides[1]})")
                if "queue" in ((link.get("ends") or {}).get(side) or {}):
                    link["ends"][side].pop("queue")
                    link["ends"] = {h: x for h, x in link["ends"].items() if x}
                    if not link["ends"]:
                        link.pop("ends")
                else:
                    link.pop("queue")
            else:
                raise ValueError(f"{n}: there is no {kind} {oid!r} to remove (kind: host, link, flow or queue; a queue's id is its link's)")
    return sync(t)


def objects(t):
    """The objects of a network as "kind:id" (a queue by its link's id; where the link's ends are described each by itself, by link.host)."""
    return ({f"host:{h['id']}" for h in t["hosts"]} | {f"link:{l['id']}" for l in t["links"]} | {f"flow:{f['id']}" for f in t["flows"]}
            | {f"queue:{l['id']}" if a.count(".") == 1 else f"queue:{l['id']}.{h}" for l, h, q, a in queues(t)})


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
    nl = st.get("new_link")   # 2026-11-23: the fastest link a change may add, and the delay every new link has
    if nl is not None and not (isinstance(nl, dict) and set(nl) == {"rate_max", "delay"} and ok("new.rate", nl["rate_max"]) and ok("new.delay", nl["delay"])):
        bad.append("structure.new_link gives rate_max (the fastest link a change may add, as 100Mbps) and delay (the one-way delay of every new link, as 1ms)")
    return bad


def changed_problems(t0, t1, st, goal, outs_needed=()):
    """Why a changed network (t1, from the session's t0) may not be simulated, beyond what problems() says of it: a
    locked object is gone, a limit of the brief is passed, or a measure the aim names would not exist."""
    most = {**LIMITS, **(st.get("most") or {})}
    bad = [f"{len(t1[k])} {k}: this brief allows at most {most[k]}" for k in LIMITS if len(t1[k]) > most[k]]
    nl = st.get("new_link") or {}
    def as_given(kind, x):
        """An object as the brief states it, in a form that is equal exactly when it is the same object: a link without its queues (a queue is an
        object of its own), a flow whole, a queue by its kind and its classes; rates by value."""
        if x is None:
            return None
        num = lambda v: rate_bps(v) if ok("x.rate", v) else v
        if kind == "link":
            ends_ = {h: {k: (num(v) if k == "rate" else v) for k, v in e.items() if k != "queue"} for h, e in (x.get("ends") or {}).items()}
            return {**{k: v for k, v in x.items() if k not in ("queue", "ends", "between", "rate")}, "between": sorted(x["between"]), "rate": num(x.get("rate")), "ends": {h: e for h, e in ends_.items() if e}}
        if kind == "flow":
            return {**{k: v for k, v in x.items() if k != "rate"}, **({"rate": num(x["rate"])} if "rate" in x else {})}
        return {"kind": x.get("kind"), "classes": x.get("classes") or {}}
    def named(t, key):
        kind, oid = key.split(":", 1)
        if kind == "queue":   # a queue is named by its link, or by link.host where the link's ends are described each by itself
            return next((q for l, h, q, a in queues(t) if (f"{l['id']}" if a.count(".") == 1 else f"{l['id']}.{h}") == oid), None)
        return next((x for x in t.get({"host": "hosts", "link": "links", "flow": "flows"}.get(kind, ""), []) if x["id"] == oid), None)
    if nl.get("rate_max"):   # 2026-11-23: a link a change adds carries at most the brief's cap. 2026-11-24: a link of the brief taken out and put back with other values is a new link too
        brief_links = [as_given("link", l) for l in t0["links"]]
        bad += [f"link {l['id']} carries {l['rate']}: this brief allows at most {nl['rate_max']} for a new link" for l in t1["links"]
                if as_given("link", l) not in brief_links and ok(f"{l['id']}.rate", l["rate"]) and rate_bps(l["rate"]) > rate_bps(nl["rate_max"])]
    locked = set(st.get("locked") or [])
    gone = sorted(locked & (objects(t0) - objects(t1)))
    if gone:
        bad.append(f"{', '.join(g.replace(':', ' ') for g in gone)} may not be removed (the operator keeps it)")
    # 2026-11-24: a locked object is the operator's as the brief states it. Removed and added again under its id with other values (a flow at another rate, a
    # link at another rate) it was "still there" for the test above, and a fixed setting could be changed that way
    replaced = sorted(k for k in locked & objects(t0) & objects(t1) if k.split(":", 1)[0] != "host" and as_given(k.split(":", 1)[0], named(t0, k)) != as_given(k.split(":", 1)[0], named(t1, k)))
    if replaced:
        bad.append(f"{', '.join(g.replace(':', ' ') for g in replaced)} may not be replaced: the operator keeps it as the brief states it (it was taken out and put back with other values; a setting of it that is a knob is set by its knob)")
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
                      "described queue the packets waiting at the sample time (<link>_q_<flow> for a scheduler's queue, named after its flow or its class; <link>_q for a plain queue) and the packets dropped "
                      "since traffic began (<link>_drops_<flow>, <link>_drops) (at most 100 rows; the measured seconds begin at t = 2)")
    told["measure"] = ("measure(run_id, of, stat, t_from, t_to, level): a measurement you define, computed from what a simulation recorded over time (nothing is simulated again, and it costs no simulation). "
                       "of: a column or arithmetic over columns of one record, by the names of this network (for example <column_a> + <column_b> or <column_a> / <column_b>; the probe's columns too, once the simulation has its probe); stat: mean, min, max, std, first, last, p05, p50, p95, slope (change per second), rate ((last - first) / seconds, for a column that counts up), "
                       "time_above, time_below (seconds spent above or below level), first_time_above, first_time_below; t_from, t_to: the window in seconds (left out: the measured seconds, from 2 s to the end)")
    told["probe"] = ("probe(run_id, every): a finer look at a simulation you already ran. The harness runs the same simulation again (same settings, same seed) with trace sinks that only listen, and keeps their record only "
                     "if the result is byte for byte the same: no result can change by it, and it costs no simulation. Sampled every `every` seconds (left out: 0.01), it records, for each flow, <flow>_bps, and for a TCP flow <flow>_cwnd, "
                     "<flow>_ssthresh, <flow>_inflight (bytes sent and not yet acknowledged), <flow>_rwnd (the receiver's window as the sender knows it), <flow>_rtt_ms and <flow>_rto_ms; for each described queue the longest time a packet "
                     "waited in it since the last sample (<link>_wait_<flow or class>_ms for a scheduler's queue, <link>_wait_ms for a plain one) and the packets waiting; for each link the packets in its devices' transmit queues "
                     "(<link>_devq, <link>_devq_back). It answers with the columns it recorded; read them with measure, or with series(run_id, every_n, probe=true)")
    return told


def text(t, run):
    """The description as the program `net` reads it (network.txt). run: duration, seed and, if set, tcpInitCwnd and tcpBufBytes."""
    lines = [f"host {h['id']}" for h in t["hosts"]]
    for l in t["links"]:
        nos = lambda v: str(v).replace(" ", "")   # no space inside a value: the program reads "1Gbps", not "1 Gbps" (the coherence audit, 2026-11-22)
        lines.append(f"link {l['id']} {l['between'][0]} {l['between'][1]} rate={nos(l['rate'])} delay={nos(l['delay'])} mtu={nos(l['mtu'])} devq={nos(l['device_queue'])}")
        for h, x in (l.get("ends") or {}).items():   # a device that differs from its link's line
            own = [f"{k}={str(x[p]).replace(' ', '')}" for k, p in (("rate", "rate"), ("devq", "device_queue"), ("mtu", "mtu")) if p in x and x[p] != l[p]] + ([f"loss={x['loss']}"] if "loss" in x else [])
            if own:
                lines.append(f"dev {l['id']} {h} " + " ".join(own))
        for _, h, q, a in (x for x in queues(t) if x[0] is l):
            s = f"queue {l['id']} {h} kind={q['kind']} length={q['length']}"
            if q["kind"] == "scheduler":
                s += " parts=" + ",".join(f"{f}:{v}" for f, v in q["parts"].items())
                if q.get("largest_rate"):
                    s += " largest=" + ",".join(f"{f}:{str(v).replace(' ', '')}" for f, v in q["largest_rate"].items())
                if q.get("classes"):
                    s += " classes=" + ",".join(f"{k}:{'+'.join(v)}" for k, v in q["classes"].items())
            lines.append(s)
    for f in t["flows"]:
        sends = f" rate={str(f['rate']).replace(' ', '')} packet={f['packet_bytes']}" if app(f) == "onoff" else ""
        sends += "".join(f" {k}={f[p]}" for k, p in (("start", "start"), ("stop", "stop"), ("on", "on_time"), ("off", "off_time"), ("maxbytes", "max_bytes")) if p in f)
        lines.append(f"flow {f['id']} udp {f['from']} {f['to']}{sends}" if f["kind"] == "udp"   # app= is written only where it is not the kind's own (tcp with onoff), so every older network gives the same file
                     else f"flow {f['id']} tcp {f['from']} {f['to']} type={f['type']}" + (" app=onoff" + sends if app(f) == "onoff" else sends))
    tcp = [f"{k}={run[n]}" for k, n in (("initcwnd", "tcpInitCwnd"), ("buf", "tcpBufBytes"), ("delack", "tcpDelAck")) if run.get(n)] + [f"{k}={run[n]}" for k, n in (("sack", "tcpSack"), ("timestamps", "tcpTimestamps")) if run.get(n) in (0, 1)]
    if tcp:
        lines.append("tcp " + " ".join(tcp))
    lines.append(f"run duration={run['duration']} seed={run['seed']}")
    return "\n".join(lines) + "\n"
