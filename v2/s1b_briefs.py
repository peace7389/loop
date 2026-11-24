"""v2, stage 1b: the briefs three-hosts-2 and three-hosts-link-2 (A2, A3; the old ones stay as the record of s059 and s061), and the chain rule's
refusal says the way that is open for an explanation not yet tried (A8, the narrow form).   python3 v2/s1b_briefs.py"""
import sys, json; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done, ROOT, LOG
def brief(old_id, new_id, edits, change=None, why=""):
    b = json.loads((ROOT / f"briefs/{old_id}.json").read_text()); d0 = b["description"]; d = d0
    for old, new in edits:
        assert d.count(old) == 1, (old_id, old[:60]); d = d.replace(old, new)
    b["id"], b["description"] = new_id, d
    if change: change(b)
    (ROOT / f"briefs/{new_id}.json").write_text(json.dumps(b, indent=1) + "\n"); LOG.append((f"briefs/{new_id}.json (from {old_id})", why, d0, d))
# A3: the sentence that names what is hidden goes; so do "only" and "everything ... must pass it", which say where the limit is
brief("three-hosts", "three-hosts-2", [
    (" How the scheduler behaves when one flow has less to send than its part allows is not described here; finding that out is part of the work.", ""),
    ("Link lc joins r and c and carries only {lc.rate} with a one-way delay of {lc.delay}: everything the two flows send to c must pass it.", "Link lc joins r and c and carries {lc.rate} with a one-way delay of {lc.delay}.")],
    why="A3: three-hosts-2: the description without the sentence that names the hidden behaviour, and without the words that say where the limit is")
# A2: the sentence on routes goes (the harness says it for every brief whose network may change); the limits no longer leave exactly one more link
def limits(b):
    b["structure"]["most"] = {"hosts": 6, "links": 6, "flows": 4}
brief("three-hosts-link", "three-hosts-link-2", [
    (" Each host sends a packet along the route with the fewest links to the packet's destination; the routes are worked out once, before traffic starts, and do not change during a simulation.", "")],
    change=limits, why="A2: three-hosts-link-2: the description without the sentence on routes; its limits allow 6 hosts, 6 links and 4 flows (they were 4, 4 and 2 against the 4, 3 and 2 it has, which left one more link and nothing else)")
# A8, the narrow form: an explanation not yet tried is stated as a competitor of an earlier guess, and may then start from that guess's records. The code allowed it; the refusal did not say so
sub("harness/loop.py", """"; nothing has been learned since your last guess: test what is open, or look with a request, before you guess again")), "harness", None""",
    """"; nothing has been learned since your last guess: test what is open, or look with a request, before you guess again")
                    + (". An explanation not tried yet may be stated without a new record as the competitor of an earlier guess: name that guess in competes_with and cite a record it cites" if COMP["on"] else "")), "harness", None""",
    "A8 (narrow): the refusal of a guess that starts from old records says how an explanation not yet tried may be stated")
done("stage1b", "v2, stage 1b: the briefs three-hosts-2 and three-hosts-link-2, and the chain rule's refusal")
