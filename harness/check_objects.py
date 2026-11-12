"""Operator check: does the viewer's picture of the system still say what the scenario does?

viewer/objects.json (the ns-3 objects and their settings, hand-kept) and the picture drawn from it
(viewer/evidence_system.js) state values that the scenario fixes in its source: the UDP packet size, the ports, the
device's queue, the TCP buffers, the scheduler's quantum, the start times. Nothing updates them when the scenario
changes. This reads the scenario source and compares, value by value.

    python3 harness/check_objects.py [--scenario DIR]

DIR defaults to ns-3.49/scratch/two-hosts (the scenario that is built), or scratch/two-hosts (the repository's copy)
where there is no ns-3 tree. It prints one line per value and ends with status 1 if any line is not "ok":
  DIFFERS  the scenario and the viewer state different values: correct viewer/objects.json (or the picture)
  MISSING  the line of the scenario this check reads is no longer there: the scenario changed its form, so the value
           must be compared by hand and the pattern below brought up to date
Run it after every change of the scenario, with the eleven checks. It reads three kinds of file and writes nothing.
Settings that a brief sets (link rate, delay, MTU, UDP rate, queue length, ratio, TCP variant, duration, seed) are not
checked here: the page takes them from each session's own records. Standard library only."""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = []  # (state, what, the scenario says, the other side says, who the other side is)


def find(src, pattern, what):
    """The groups of the first match of pattern in the scenario source, or None (and a MISSING line)."""
    m = re.search(pattern, src, re.S)
    if not m:
        ROWS.append(("MISSING", what, "no line matches " + pattern, "", ""))
    return m.groups() if m else None


def obj(O, host, layer, name):
    """An object of objects.json: by host and layer and name; host None = the link ("channel") or "around"."""
    pool = O["hosts"] if host else []
    for H in pool:
        if H["key"] == host:
            for o in H.get(layer, []):
                if o["name"] == name:
                    return o
    if not host:
        return O["channel"] if layer == "channel" else next((o for o in O.get("around", []) if o["name"] == name), None)
    return None


def row(o, label):
    return next((r[1] for r in (o or {}).get("rows", []) if r[0] == label), None)


def same(what, scenario, other, ok, who="viewer"):
    ROWS.append(("ok" if ok else "DIFFERS", what, str(scenario), "not stated" if other is None else str(other), who))


def size(n):
    """Bytes the way objects.json writes them: 1048576 -> '1 MB'."""
    return f"{n >> 20} MB" if n % (1 << 20) == 0 else f"{n >> 10} kB" if n % (1 << 10) == 0 else f"{n} bytes"


def main():
    ap = argparse.ArgumentParser(description="Compare viewer/objects.json and the picture of the system with the scenario source.")
    ap.add_argument("--scenario", help="folder with two-hosts.cc and link-queue-disc.cc")
    a = ap.parse_args()
    built = ROOT / "ns-3.49/scratch/two-hosts"
    d = Path(a.scenario) if a.scenario else built if (built / "two-hosts.cc").is_file() else ROOT / "scratch/two-hosts"
    cc, disc = (d / "two-hosts.cc").read_text(), (d / "link-queue-disc.cc").read_text()
    O = json.loads((ROOT / "viewer/objects.json").read_text())
    picture = (ROOT / "viewer/evidence_system.js").read_text() if (ROOT / "viewer/evidence_system.js").is_file() else None
    S, R = lambda layer, name: obj(O, "sender", layer, name), lambda layer, name: obj(O, "receiver", layer, name)

    # ---- the applications
    g = find(cc, r"udp\.SetConstantRate\(DataRate\(udpRate\), (\d+)\)", "UDP packet payload")
    if g:
        v = row(S("apps", "UDP source"), "Packet payload"); same("UDP packet payload", f"{g[0]} bytes", v, v == f"{g[0]} bytes")
    for flow, helper, source, sink in (("UDP", "OnOffHelper udp", "UDP source", "UDP sink"), ("TCP", "BulkSendHelper tcp", "TCP source", "TCP sink")):
        g = find(cc, re.escape(helper) + r'\("ns3::\w+", InetSocketAddress\(dst, (\d+)\)\)', f"{flow} port")
        if g:
            v = row(S("apps", source), "To"); same(f"{flow} port, at the source", g[0], v, bool(v) and v.endswith(f"port {g[0]}"))
            v = row(R("apps", sink), "Port"); same(f"{flow} port, at the sink", g[0], v, v == g[0])
            w = find(cc, r"PacketSinkHelper " + flow.lower() + r'SinkH\("ns3::\w+", InetSocketAddress\(Ipv4Address::GetAny\(\), (\d+)\)\)', f"{flow} sink's port")
            if w:
                same(f"{flow} port, source against sink in the scenario", g[0], w[0], g[0] == w[0], "the sink")
    g = find(cc, r"uint32_t udpTos = (0x[0-9a-fA-F]+|\d+);", "UDP TOS")
    if g:
        tos = int(g[0], 0); v = row(S("apps", "UDP source"), "Priority mark")
        same("UDP TOS byte", f"0x{tos:02x}", v, bool(v) and f"TOS 0x{tos:02x}" in v.lower().replace("tos", "TOS"))
        # ns-3 maps the TOS byte to a socket priority (Socket::IpTos2Priority in src/network/model/socket.cc, read from
        # ns-3.49): bits 1 to 4 choose best effort 0, bulk 2, interactive 6 or interactive bulk 4
        prio = [0, 0, 0, 0, 2, 2, 2, 2, 6, 6, 6, 6, 4, 4, 4, 4][(tos >> 1) & 0x0F]
        same("the priority that TOS gives (ns-3's table)", f"priority {prio}", v, bool(v) and v.startswith(f"priority {prio} "))
        b = find(disc, r"band = \(prio == (\d+)\) \? 0 : 1", "the priority the scheduler puts in the UDP queue")
        if b:
            v = row(S("tc", "UDP queue"), "Takes"); same("priority taken by the UDP queue", f"priority {b[0]}", v, bool(v) and v.endswith(f"priority {b[0]}"))
            same("the UDP sender's priority is the one the UDP queue takes", prio, b[0], str(prio) == b[0], "the scheduler takes")
    g = find(cc, r'tcp\.SetAttribute\("Tos", UintegerValue\((\d+)\)\)', "TCP TOS")
    if g:
        v = row(S("apps", "TCP source"), "Priority mark"); same("TCP TOS byte", f"TOS {g[0]}", v, bool(v) and f"(TOS {g[0]})" in v)
    g, s = find(cc, r"const double tStart = ([\d.]+);", "start of traffic"), find(cc, r"offset->GetValue\(0\.0, ([\d.]+)\)", "largest start offset")
    if g and s:
        want = f"{float(g[0]):g} s + 0–{float(s[0]) * 1000:g} ms"
        for name in ("UDP source", "TCP source"):
            v = row(S("apps", name), "Starts"); same(f"when the {name} starts", want, v, v == want)
        v = row(obj(O, None, "around", "Clock"), "Traffic starts"); same("traffic starts", f"at {float(g[0]):g} s", v, v == f"at {float(g[0]):g} s")
        v = row(obj(O, None, "around", "Random numbers"), "Used for"); same("start offset, under Random numbers", f"0–{float(s[0]) * 1000:g} ms", v, bool(v) and f"0–{float(s[0]) * 1000:g} ms" in v)

    # ---- the internet stack
    g = find(cc, r'"ns3::TcpSocket::SegmentSize", UintegerValue\(mtu - (\d+)\)', "TCP segment size")
    if g:
        same("TCP segment = mtu - N, in objects.json's description", f"mtu - {g[0]}", "mtu - " + (re.search(r"mtu - (\d+)", O["about"]) or [0, "?"])[1], f"mtu - {g[0]}" in O["about"])
        if picture is not None:
            same("TCP segment = mtu - N, in the picture's script", f"mtu - {g[0]}", (re.search(r"v\.mtu - \d+", picture) or ["not found"])[0], f"v.mtu - {g[0]}" in picture)
    for attr, label, places in (("SndBufSize", "Send buffer", [(S, "sender")]), ("RcvBufSize", "Receive buffer", [(S, "sender"), (R, "receiver")])):
        g = find(cc, r'"ns3::TcpSocket::' + attr + r'", UintegerValue\(1 << (\d+)\)', f"TCP {label.lower()}")
        for side, who in places if g else []:
            v = row(side("stack", "TCP socket"), label); same(f"TCP {label.lower()}, {who}", size(1 << int(g[0])), v, v == size(1 << int(g[0])))
    g = find(cc, r'addr\.SetBase\("(\d+\.\d+\.\d+)\.0", "255\.255\.255\.0"\)', "addresses")
    if g:
        for n, H in enumerate(O["hosts"], 1):
            same(f"address of the {H['key']}", f"{g[0]}.{n}", H.get("sub"), H.get("sub") == f"{g[0]}.{n}")
            v = row(obj(O, H["key"], "stack", "IPv4"), "Address"); same(f"address of the {H['key']}, under IPv4", f"{g[0]}.{n} / 24", v, v == f"{g[0]}.{n} / 24")
    for attr, label in (("InitialCwnd", "First window"), ("MinRto", "Shortest resend timer"), ("DelAckCount", "Sends ACK"), ("Sack", "TCP options"), ("Timestamp", "TCP options")):
        if re.search(r'"ns3::Tcp\w+::' + attr + '"', cc):  # objects.json calls these ns-3 defaults; they are, as long as the scenario does not set them
            ROWS.append(("DIFFERS", f"{label}: an ns-3 default in objects.json", f"the scenario now sets {attr}", "flagged ns3", "viewer"))

    # ---- traffic control and the device
    g = find(disc, r'AddAttribute\("Quantum",.*?UintegerValue\((\d+)\)', "the scheduler's quantum")
    if g:
        v = row(S("tc", "Scheduler"), "Turn size"); same("the scheduler's quantum", f"{g[0]} bytes", v, bool(v) and v.startswith(f"{g[0]} bytes"))
    g = find(cc, r'SetRootQueueDisc\("ns3::(\w+)"', "the scheduler's class")
    if g:
        same("the scheduler's class", g[0], (S("tc", "Scheduler") or {}).get("cls"), (S("tc", "Scheduler") or {}).get("cls") == g[0])
    kids = re.findall(r'AddChildQueueDisc\(h, cids\[(\d+)\], "ns3::(\w+)"', cc)
    queues = [o for o in next(H for H in O["hosts"] if H["key"] == "sender")["tc"] if "queue" in o["name"].lower()]
    same("queues in front of the scheduler", len(kids), len(queues), len(kids) == len(queues) and len(kids) > 0)
    for (band, cls), o in zip(kids, queues):
        same(f"class and band of the {o['name']}", f"{cls} · band {band}", o["cls"], o["cls"] == f"{cls} · band {band}")
    g = find(cc, r'p2p\.SetQueue\("ns3::(\w+)<Packet>", "MaxSize", StringValue\("(\d+)p"\)\)', "the device's transmit queue")
    if g:
        for side, who in ((S, "sender"), (R, "receiver")):
            v = row(side("dev", "Point-to-point device"), "Transmit queue"); same(f"transmit queue of the {who}'s device", f"{g[1]} packets ({g[0]})", v, v == f"{g[1]} packets ({g[0]})")
        if picture is not None:
            same("the device's queue, written in the picture", f"queue {g[1]}", (re.search(r"'queue \d+'", picture) or ["not found"])[0].strip("'"), f"'queue {g[1]}'" in picture)
    g = find(disc, r"MakeDoubleChecker<double>\(([\d.]+), ([\d.]+)\)", "the range of the ratio")
    for p in sorted((ROOT / "briefs").glob("*.json")) if g else []:
        k = json.loads(p.read_text()).get("knobs", {}).get("weightUdp")
        if k:
            same(f"range of weightUdp in brief {p.stem}", f"{g[0]} to {g[1]}", f"{k['min']} to {k['max']}", float(g[0]) <= k["min"] and k["max"] <= float(g[1]))

    # ---- around the network
    g = find(cc, r"double warmup = ([\d.]+);", "warm-up")
    if g:
        v = row(obj(O, None, "around", "Clock"), "Warm-up, not measured"); same("warm-up, not measured", f"{float(g[0]):g} s", v, v == f"{float(g[0]):g} s")
    g = find(cc, r"RngSeedManager::SetSeed\((\d+)\)", "the seed")
    if g:
        v = row(obj(O, None, "around", "Random numbers"), "Seed"); same("the seed (the run number is the knob)", g[0], v, v == g[0])
    g = find(cc, r"double period = ([\d.]+);", "the sampling period")
    if g:
        m = obj(O, None, "around", "Measurement"); label = f"Every {float(g[0]):g} s"
        same("how often series.csv is sampled", label, next((r[0] for r in (m or {}).get("rows", []) if r[0].startswith("Every")), None), row(m, label) is not None)

    # ---- the structure: what the picture is drawn for
    g = find(cc, r"nodes\.Create\((\d+)\)", "the number of nodes")
    if g:
        same("computers", g[0], len(O["hosts"]), int(g[0]) == len(O["hosts"]))
    for what, helpers, host in (("sending applications", r"OnOffHelper|BulkSendHelper", "sender"), ("receiving applications", r"PacketSinkHelper", "receiver")):
        made, shown = len(re.findall(r"\b(?:" + helpers + r") \w+\(", cc)), len(next(H for H in O["hosts"] if H["key"] == host)["apps"])
        same(what, made, shown, made == shown)
    if picture is not None:  # every object the picture draws must be in objects.json under that host, layer and name, and every object in the path drawn
        drawn = set(re.findall(r"id\('(\w+)', '(\w+)', '([^']+)'\)", picture))
        for host, layer, name in sorted(drawn):
            if obj(O, host, layer, name) is None:
                ROWS.append(("DIFFERS", f"the picture draws “{name}” ({host}, {layer})", "", "not in objects.json under that name", "viewer"))
        listed = {(H["key"], L["key"], o["name"]) for H in O["hosts"] for L in O["layers"] for o in H.get(L["key"], [])}
        same("objects of objects.json that the picture draws", len(listed), len(listed & drawn), listed <= drawn)
        for host, layer, name in sorted(listed - drawn):
            ROWS.append(("DIFFERS", f"“{name}” ({host}, {layer}) is in objects.json", "", "the picture does not draw it", "viewer"))

    wide = max(len(r[1]) for r in ROWS)
    print(f"scenario: {d}\n")
    for state, what, scenario, other, who in ROWS:
        print(f"{state:8} {what:{wide}}  {scenario}" + (f"   |   {who}: {other}" if state == "DIFFERS" else ""))
    bad = [r for r in ROWS if r[0] != "ok"]
    print(f"\n{len(ROWS)} values compared: {len(ROWS) - len(bad)} ok" + (f", {sum(r[0] == 'DIFFERS' for r in bad)} differ, {sum(r[0] == 'MISSING' for r in bad)} could not be read from the scenario" if bad else ""))
    print("Not compared: what objects.json flags as ns-3 defaults (they change only with the ns-3 version), and the wording of each row.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
