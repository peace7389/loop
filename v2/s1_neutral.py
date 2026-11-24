"""v2, stage 1: neutral texts in both arms ("describe, never suggest"). Audit items A1, A2 (the harness's part), A7, A10, A11, C29.
Run once, from the tree's root:  python3 v2/s1_neutral.py"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
L, N, P, S, M = "harness/loop.py", "harness/network.py", "harness/prompt.txt", "harness/schema.json", "harness/manifest.json"

# ---- A1, A2: the paragraph on changes of the network: every kind of change with the same depth, the queue kinds in alphabetical order with a line each
sub(L, """   - do add_host: id, a new name (at most 12 lower-case letters and digits, beginning with a letter).
   - do add_link: id, from and to (the two hosts it joins), rate (for example 1Gbps). One link for each two hosts.
   - do add_flow: id, kind (udp or tcp: the socket), from, to, and rate for udp (for example 100Mbps) or type for tcp (for example TcpCubic). app is the application that sends: "" for the usual one (udp: packets at a constant rate; tcp: always has data, as fast as TCP accepts), or onoff with kind tcp for a TCP flow that sends at the constant rate you state in rate. A flow needs one shortest way from its sender to its receiver.
   - do add_queue: id (the link), on (the host whose sending side of the link it is), kind (scheduler, fifo, or another of ns-3's queue discs: pfifofast, codel, fqcodel, red, pie). A scheduler gives each flow that passes it a part of the link; fifo is one queue for all, first in, first out. A link may have a queue on each of its two sides.
   - do remove: kind (host, link, flow or queue) and id (a queue's id is its link's; where the link has a queue on each side, on says which). A host goes with its links and with the flows that start or end at it.
""", """   - do add_host: id, a new name (at most 12 lower-case letters and digits, beginning with a letter). A new host has no link and no flow until a change adds them; a host with more than one link forwards packets.
   - do add_link: id, from and to (the two hosts it joins) and rate (state it, for example 1Gbps). One link for each two hosts. A new link has a one-way delay of 50us, packets of at most 1500 bytes, a device queue of 10 packets and, on each of its two sides, a plain queue of 100 packets, first in, first out.
   - do add_flow: id, kind (udp or tcp: the socket), from, to, and rate for udp (left empty: 100Mbps) or type for tcp (left empty: TcpCubic). app is the application that sends: "" for the usual one (udp: packets of 1400 bytes at a constant rate; tcp: always has data, as fast as TCP accepts), or onoff with kind tcp for a TCP flow that sends at the constant rate you state in rate.
   - do add_queue: id (the link), on (the host whose sending side of the link it is) and kind (state it). A new queue holds 100 packets, and a link may have a queue on each of its two sides. The kinds, each ns-3's queue disc of that name except the scheduler: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.
   - do remove: kind (host, link, flow or queue) and id (a queue's id is its link's; where the link has a queue on each side, on says which). A host goes with its links and with the flows that start or end at it. Where a queue is removed, a plain queue of 100 packets, first in, first out, stands in its place.
Packets take the way with the fewest links from their sender to their receiver; the ways are worked out once, before traffic starts, and a flow needs exactly one such way.
""", "A1, A2: the changes of the network, each with the same depth; the queue kinds alphabetical, a line each; how packets find their way said here for every brief (it stood in one brief's description)")
sub(L, """    old = "   - do add_link: id, from and to (the two hosts it joins), rate (for example 1Gbps). One link for each two hosts."
    assert STRUCTURE.count(old) == 1
    return STRUCTURE.replace(old, f"   - do add_link: id, from and to (the two hosts it joins), rate (at most {nl['rate_max']} in this brief; left empty: {nl['rate_max']}). One link for each two "
                                  f"hosts. A new link has a one-way delay of {nl['delay']} in this brief, packets of at most 1500 bytes, a device queue of 10 packets and, on each of its two "
                                  "sides, a plain queue of 100 packets, first in, first out.")""",
    """    # v2: the line on a new link is the same in every brief; a brief that caps new links has its numbers in it (it had a longer line of its own, and an empty rate gave the cap)
    old, old2 = "rate (state it, for example 1Gbps)", "A new link has a one-way delay of 50us,"
    assert STRUCTURE.count(old) == 1 and STRUCTURE.count(old2) == 1
    return STRUCTURE.replace(old, f"rate (state it; at most {nl['rate_max']} in this brief)").replace(old2, f"A new link has a one-way delay of {nl['delay']} in this brief,")""",
    "A2: a brief that caps new links changes two numbers of the same line, no more")
sub(L, """    caps, delays = re.findall(r"rate \\(at most (\\S+) in this brief", text), re.findall(r"a one-way delay of (\\S+) in this brief", text)""",
    """    caps, delays = re.findall(r"rate \\(state it; at most (\\S+) in this brief\\)", text), re.findall(r"a one-way delay of (\\S+) in this brief", text)""", "A2: the check of the stated cap reads the new line")
# an added link states its rate and an added queue its kind: nothing is filled in with the best value (C29: an empty kind became a scheduler, an empty rate the brief's cap)
sub(N, """            t["links"].append({"id": oid, "between": sorted([e["from"], e["to"]], key=order.index), "rate": e.get("rate") or nl["rate"], "delay": nl["delay"], "mtu": 1500, "device_queue": 10})""",
    """            if not e.get("rate"):   # v2: stated, never filled in (left empty it was the brief's cap, the best value there is)
                raise ValueError(f"{n}: a new link states its rate (for example 1Gbps)")
            t["links"].append({"id": oid, "between": sorted([e["from"], e["to"]], key=order.index), "rate": e["rate"], "delay": nl["delay"], "mtu": 1500, "device_queue": 10})""",
    "C29, A2: a new link states its rate")
sub(N, """            new = {"kind": e.get("kind") if e.get("kind") in QUEUE_KINDS else "scheduler", "length": 100, "parts": {}, "largest_rate": {}}""",
    """            if e.get("kind") not in QUEUE_KINDS:   # v2: stated, never filled in (an empty or unknown kind became a scheduler)
                raise ValueError(f"{n}: a new queue states its kind: one of {', '.join(sorted(QUEUE_KINDS))}")
            new = {"kind": e["kind"], "length": 100, "parts": {}, "largest_rate": {}}""",
    "C29, A1: a new queue states its kind")

# ---- A7: examples that name one cause become placeholders
sub(L, "Each has name (lower-case, for example rwnd_max), of", "Each has name (lower-case, for example <column>_max), of", "A7: the example name of a measurement")
sub(L, "probe makes a finer record of such a simulation (TCP's round-trip time, the receiver's window, the bytes in flight, the time packets wait in each queue) by running it again with taps that only listen.",
    "probe makes a finer record of such a simulation (the brief's text of the tool probe lists every column it records) by running it again with taps that only listen.", "A7: four of the probe's columns were named in the instructions; the brief's tool text lists all of them")
sub(P, "for example rwnd_mean), of (a column", "for example <column>_mean), of (a column", "A7 (the arms hypotheses and plain): the example name of a measurement")
sub(P, "is named the same way, for example rwnd_mean@label)", "is named the same way, for example <column>_mean@label)", "A7 (the arms hypotheses and plain): the example of a measurement in a rule")
sub(P, "probe makes a finer record of a simulation you already ran (TCP's round-trip time, the receiver's window, the bytes in flight, the time packets wait in each queue) by running it again with taps that only listen.",
    "probe makes a finer record of a simulation you already ran (the brief's text of the tool probe lists every column it records) by running it again with taps that only listen.", "A7 (the arms hypotheses and plain): the probe's columns")
sub(S, '"description": "a name of its own: lower-case letters, digits and _, for example rwnd_mean"', '"description": "a name of its own: lower-case letters, digits and _, for example <column>_mean"', "A7: the answer format's example name")
sub(S, '"description": "a column a simulation records over time, or arithmetic over columns of one record, for example rwnd or inflight / rwnd"', '"description": "a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>"', "A7: the answer format's example formula")
sub(N, """of: a column or arithmetic over columns of one record, by the names of this network (the bits per second of two flows added, or, once the simulation has its probe, a flow's bytes in flight divided by "
                       "its receiver's window: <flow>_inflight / <flow>_rwnd); stat:""",
    """of: a column or arithmetic over columns of one record, by the names of this network (for example <column_a> + <column_b> or <column_a> / <column_b>; the probe's columns too, once the simulation has its probe); stat:""", "A7: the example formulas of the tool measure (a network)")
sub(M, """(for example \\"udp_bps + tcp_bps\\", \\"cwnd / 1448\\", or, once the simulation has its probe, \\"inflight / rwnd\\"); stat:""",
    """(for example \\"<column_a> + <column_b>\\" or \\"<column_a> / <column_b>\\"; the probe's columns too, once the simulation has its probe); stat:""", "A7: the example formulas of the tool measure (the two-host briefs)")

# ---- A10: no example of a finding's name; A11: no "Usually empty"
sub(L, '"description": "at most 5 words, to show it by (for example: TCP gets nothing)"', '"description": "at most 5 words, to show it by"', "A10: the example name of a finding")
sub(L, "(id, and why in one sentence). Usually empty.\n", "(id, and why in one sentence).\n", "A11: drop")
sub(L, "and because (the numbers it overlooked). Usually empty.\n", "and because (the numbers it overlooked).\n", "A11: objections")
done("stage1", "v2, stage 1: neutral texts")
