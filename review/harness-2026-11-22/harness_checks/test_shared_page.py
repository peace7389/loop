"""The shared page (the operator's word of 2026-11-17: every account of the lab server may use the page as the owner
does, with the least safety measure). The control server is run here inside this test, on a scratch copy, with the
account of each request chosen by the test (control.peer_uid is replaced) and with a stand-in loop.py that only makes
its session folder and waits, so no model and no simulation is needed:
  - a POST from another account is carried out, and noted with that account in checks/people.jsonl;
  - a request whose account cannot be found is refused;
  - one session at a time: while one runs, a start is refused and says which runs and who started it, whether it was
    started through the page or from a terminal; /api/status and the session's row say who started it;
  - only the account that started a session, or the owner, stops it;
  - drafts.jsonl is given to nobody (GET, HEAD, and with the dot written as %2E); the ledger is.
  - looking from the network (--network on): a request through the machine's network address can read the page's own
    material and nothing else, and every POST is refused; the same server reached through 127.0.0.1 is as before.
  - a personal link (harness/invite.py): a visitor from the network who shows its key is that person by name and uses
    the page as the owner does (saves a brief, starts a session, stops any session); the key goes into a cookie and out
    of the address; a wrong key is view-only; the file of the keys is given to nobody; a link taken out ends at once.
    python3 test_shared_page.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new."""
import http.server, json, os, pwd, shutil, subprocess, sys, threading, time, urllib.request, urllib.error
from pathlib import Path
REAL = Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR) or "hs_" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs")
# the stand-in loop: its session folder, a ledger of one line, a drafts file, then it waits to be stopped
(P / "harness/loop.py").write_text('''import sys, time, json
from pathlib import Path
a = sys.argv; sid = a[a.index("--session") + 1]; d = Path.home() / "project/sessions" / sid; d.mkdir(parents=True, exist_ok=True)
(d / "session.json").write_text(json.dumps({"brief": a[a.index("--brief") + 1] if "--brief" in a else None}))
(d / "ledger.jsonl").write_text(json.dumps({"id": "U1", "type": "turn", "turn": 1, "ts": "2026-11-17T00:00:00", "body": {}}) + "\\n")
(d / "drafts.jsonl").write_text("{}\\n")
print("session", sid, flush=True); time.sleep(600)
''')
os.environ["HOME"] = str(SCR / "home")
sys.path.insert(0, str(P / "harness"))
import control
assert control.ROOT == P, control.ROOT
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:60])

ME = os.getuid(); OWNER = pwd.getpwuid(ME).pw_name
others = [u for u in pwd.getpwall() if u.pw_uid != ME and u.pw_name != OWNER][:2]
A, B = others[0], others[1]
WHO = {"uid": ME}
control.peer_uid = lambda *a: WHO["uid"]
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), control.Handler); PORT = srv.server_address[1]; control.SERVING["port"] = PORT
threading.Thread(target=srv.serve_forever, daemon=True).start()

def call(uid, path, body=None, method=None):
    WHO["uid"] = uid
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=None if body is None else json.dumps(body).encode(), method=method,
                                 headers={} if body is None else {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(); return r.status, (json.loads(raw) if raw[:1] in (b"{", b"[") else raw)
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, (json.loads(raw) if raw[:1] == b"{" else raw)
people = lambda: [json.loads(l) for l in (P / "checks/people.jsonl").read_text().splitlines()] if (P / "checks/people.jsonl").is_file() else []

try:
    # ---- another account may use the page, and is noted
    brief = json.loads((P / "briefs/two-hosts-open.json").read_text()); brief["id"] = "by-a"
    c, r = call(A.pw_uid, "/api/brief", {"brief": brief})
    say(c == 200 and r.get("saved") == "by-a" and (P / "briefs/by-a.json").is_file() and people()[-1]["account"] == A.pw_name and people()[-1]["did"] == "/api/brief" and people()[-1]["id"] == "by-a",
        f"a brief saved by another account ({A.pw_name}) is saved, and checks/people.jsonl notes it: {people()[-1] if people() else None}")
    c, r = call(None, "/api/brief", {"brief": {**brief, "id": "by-nobody"}})
    say(c == 403 and not (P / "briefs/by-nobody.json").exists() and len(people()) == 1, f"a request whose account cannot be found is refused ({c}: “{str(r.get('error'))[:70]}…”) and nothing is written")
    c, st = call(B.pw_uid, "/api/status")
    say(c == 200 and st["you"] == B.pw_name and st["owner"] == OWNER and st["running_now"] == [] and st["one_at_a_time"] is True and st["share"]["port"] == PORT and st["share"]["host"],
        f"/api/status says who asks ({st.get('you')}), who runs the page ({st.get('owner')}), that nothing is running, that one session runs at a time, and how the page is reached ({st.get('share')})")

    # ---- one session at a time; who started it
    c, r1 = call(A.pw_uid, "/api/session", {"brief": "two-hosts-open"}); s1 = r1.get("id")
    c2, st = call(B.pw_uid, "/api/status"); row = next((x for x in st["sessions"] if x["id"] == s1), {})
    say(c == 200 and s1 and st["running_now"] == [{"id": s1, "by": A.pw_name}] and row.get("running") and row.get("by") == A.pw_name and row.get("can_stop") is False,
        f"{A.pw_name} starts session {s1}: the status and the session's row say it is running and that {A.pw_name} started it; {B.pw_name}, who asks, may not stop it")
    rowA = next(x for x in call(A.pw_uid, "/api/sessions")[1] if x["id"] == s1); rowO = next(x for x in call(ME, "/api/sessions")[1] if x["id"] == s1)
    say(rowA["can_stop"] is True and rowO["can_stop"] is True, f"asked by {A.pw_name} and by the owner ({OWNER}), the row says each may stop it")
    c, r = call(B.pw_uid, "/api/session", {"brief": "two-hosts-open"})
    say(c == 409 and s1 in r["error"] and A.pw_name in r["error"] and "one session runs at a time" in r["error"] and sorted(p.name for p in (P / "sessions").iterdir()) == [s1],
        f"while it runs, a start by {B.pw_name} is refused and says which session runs and who started it (“{r.get('error')}”); no folder is made")
    c, r = call(ME, "/api/session", {"brief": "two-hosts-open"})
    say(c == 409 and A.pw_name in r["error"], f"the owner's start is refused in the same way ({c})")
    c, r = call(B.pw_uid, "/api/stop", {"session": s1})
    say(c == 403 and A.pw_name in r["error"] and OWNER in r["error"] and control.STARTED[s1]["proc"].poll() is None, f"{B.pw_name} cannot stop it (“{r.get('error')}”), and it goes on running")
    c, r = call(A.pw_uid, "/api/stop", {"session": s1})
    say(c == 200 and r == {"stopped": s1} and control.STARTED[s1]["proc"].poll() is not None and call(ME, "/api/status")[1]["running_now"] == [], f"{A.pw_name} stops it: {r}; nothing is running")
    c, r2 = call(B.pw_uid, "/api/session", {"brief": "two-hosts-open"}); s2 = r2.get("id")
    c3, r = call(ME, "/api/stop", {"session": s2})
    say(c == 200 and s2 and s2 != s1 and c3 == 200 and r == {"stopped": s2}, f"now {B.pw_name} can start one ({s2}), and the owner can stop a session somebody else started: {r}")
    row1 = next(x for x in call(B.pw_uid, "/api/sessions")[1] if x["id"] == s1)
    say(row1["by"] == A.pw_name and not row1["running"] and not row1["can_stop"], f"an ended session keeps who started it ({row1['by']})")
    say([(p["account"], p["did"], p["id"]) for p in people()[1:]] == [(A.pw_name, "/api/session", s1), (A.pw_name, "/api/stop", s1), (B.pw_name, "/api/session", s2), (OWNER, "/api/stop", s2)],
        f"checks/people.jsonl holds the starts and stops that were carried out, and no refused one: {[(p['account'], p['did'], p['id']) for p in people()[1:]]}")

    # ---- a session started from a terminal counts too, as the owner's
    t = subprocess.Popen([sys.executable, "loop.py", "--session", "term1"], cwd=P / "harness", env={**os.environ}, stdout=subprocess.DEVNULL, start_new_session=True); time.sleep(1.5)
    c, st = call(A.pw_uid, "/api/status"); c2, r = call(A.pw_uid, "/api/session", {"brief": "two-hosts-open"}); row = next((x for x in st["sessions"] if x["id"] == "term1"), {})
    say(st["running_now"] == [{"id": "term1", "by": OWNER}] and row.get("by") == OWNER and row.get("can_stop") is False and c2 == 409 and "term1" in r["error"] and OWNER in r["error"],
        f"a session started from a terminal (term1) is running, as the owner's ({OWNER}); a start from the page is refused meanwhile (“{r.get('error')}”); the page cannot stop it")
    t.kill(); t.wait(); time.sleep(0.3)
    say(call(A.pw_uid, "/api/status")[1]["running_now"] == [], "after it ended nothing is running")

    # ---- the files
    g = [call(B.pw_uid, f"/sessions/{s1}/drafts.jsonl")[0], call(B.pw_uid, f"/sessions/{s1}/drafts.jsonl", method="HEAD")[0], call(ME, f"/sessions/{s1}/drafts%2Ejsonl")[0], call(ME, f"/sessions/{s1}/DRAFTS.jsonl?x=1")[0]]
    led = call(B.pw_uid, f"/sessions/{s1}/ledger.jsonl")
    say(g == [404, 404, 404, 404] and led[0] == 200 and led[1].get("id") == "U1" and (P / "sessions" / s1 / "drafts.jsonl").is_file(), f"drafts.jsonl is given to nobody, the owner included (GET, HEAD, with %2E, in capitals: {g}); the ledger is given ({led[0]})")
    # ---- looking from the network (--network on): a second server on every address of this machine; a request that
    # reaches it through the machine's network address is a visitor from the network, one through 127.0.0.1 is not
    import socket
    ip = next((x for x in subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split() if "." in x and not x.startswith("127.")), None)
    srv2 = http.server.ThreadingHTTPServer(("0.0.0.0", 0), control.Handler); P2 = srv2.server_address[1]
    threading.Thread(target=srv2.serve_forever, daemon=True).start(); control.SERVING.update(port=P2, network=True)
    def far(path, body=None, method=None, host=None):
        req = urllib.request.Request(f"http://{host or ip}:{P2}{path}", data=None if body is None else json.dumps(body).encode(), method=method, headers={} if body is None else {"Content-Type": "application/json"})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k): return None
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as r:
                raw = r.read(); return r.status, (json.loads(raw) if raw[:1] in (b"{", b"[") else raw), dict(r.headers)
        except urllib.error.HTTPError as e:
            raw = e.read(); return e.code, (json.loads(raw) if raw[:1] == b"{" else raw), dict(e.headers)
    say(bool(ip), f"this machine has a network address to try with ({ip})")
    (P / "viewer").mkdir(exist_ok=True); (P / "viewer/index.html").write_text("<html>page</html>"); (P / "README.md").write_text("not for the network"); (P / "checks/exports").mkdir(exist_ok=True); (P / "checks/exports/x.zip").write_text("z")
    st = far("/api/status")
    say(st[0] == 200 and st[1]["view_only"] is True and st[1]["you"] is None and st[1]["share"]["network"] is True and all(not x["can_stop"] for x in st[1]["sessions"]),
        f"from the network /api/status answers, says view_only, names nobody as “you”, and no session can be stopped by the one who asks ({len(st[1]['sessions'])} sessions listed)")
    got = {k: far(k)[0] for k in ("/viewer/index.html", f"/sessions/{s1}/ledger.jsonl", "/briefs/two-hosts-open.json", "/api/sessions", "/checks/people.jsonl", "/checks/exports/x.zip", "/README.md", "/harness/control.py", f"/sessions/{s1}/drafts.jsonl", "/sessions/", "/checks/")}
    say([got[k] for k in ("/viewer/index.html", f"/sessions/{s1}/ledger.jsonl", "/briefs/two-hosts-open.json", "/api/sessions")] == [200] * 4 and all(got[k] == 404 for k in ("/checks/people.jsonl", "/checks/exports/x.zip", "/README.md", "/harness/control.py", f"/sessions/{s1}/drafts.jsonl", "/sessions/", "/checks/")),
        f"it is given the page, a session's ledger, a brief and the list of sessions; not the list of accounts, an export, a file outside the page's folders, the harness, the drafts, or the listing of a folder: {got}")
    root = far("/")
    say(root[0] == 302 and root[2].get("Location") == "/viewer/", "the bare address leads to the page")
    n_briefs, n_people = len(list((P / "briefs").glob("*.json"))), len(people())
    posts = {k: far(k, b) for k, b in (("/api/brief", {"brief": {**brief, "id": "from-far"}}), ("/api/session", {"brief": "two-hosts-open"}), ("/api/stop", {"session": s1}), ("/api/review", {"session": s1, "item": "x", "tick": True, "note": ""}))}
    say(all(v[0] == 403 and "view only" in v[1]["error"] for v in posts.values()) and len(list((P / "briefs").glob("*.json"))) == n_briefs and len(people()) == n_people and not (P / "checks/reviews").exists() and call(ME, "/api/status")[1]["running_now"] == [],
        f"every POST from the network is refused (“{posts['/api/session'][1]['error'][:70]}…”): no brief saved, no session started, no mark made, nothing noted")
    WHO["uid"] = A.pw_uid; near = far("/api/status", host="127.0.0.1"); c9, r9 = far("/api/brief", {"brief": {**brief, "id": "from-here"}}, host="127.0.0.1")[:2]; lst = far("/sessions/", host="127.0.0.1")[0]
    say(near[1]["view_only"] is False and near[1]["you"] == A.pw_name and c9 == 200 and r9.get("saved") == "from-here" and lst == 200, f"the same server reached from this machine itself (127.0.0.1) is as before: {A.pw_name} is named, a brief is saved, a folder is listed")
    # ---- a personal link (harness/invite.py): a visitor from the network who shows its key is that person and uses the page fully
    KEY = "k" * 32; (P / "checks/access.json").write_text(json.dumps({KEY: "the professor"}))
    def far2(path, body=None, key=None):
        req = urllib.request.Request(f"http://{ip}:{P2}{path}", data=None if body is None else json.dumps(body).encode(), headers={**({} if body is None else {"Content-Type": "application/json"}), **({"Cookie": f"th_key={key}"} if key else {})})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k): return None
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as r:
                raw = r.read(); return r.status, (json.loads(raw) if raw[:1] in (b"{", b"[") else raw), dict(r.headers)
        except urllib.error.HTTPError as e:
            raw = e.read(); return e.code, (json.loads(raw) if raw[:1] == b"{" else raw), dict(e.headers)
    first = far2(f"/viewer/?session=x&key={KEY}"); wrong = far2("/viewer/?key=" + "z" * 32)
    say(first[0] == 302 and f"th_key={KEY}" in first[2].get("Set-Cookie", "") and "HttpOnly" in first[2]["Set-Cookie"] and first[2]["Location"] == "/viewer/?session=x" and wrong[0] == 302 and "Set-Cookie" not in wrong[2] and wrong[2]["Location"] == "/viewer/",
        f"opening a personal link puts its key into a cookie of that browser and takes it out of the address (to {first[2].get('Location')}); a key that does not hold gets no cookie")
    st = far2("/api/status", key=KEY)[1]; st0 = far2("/api/status", key="z" * 32)[1]
    say(st["view_only"] is False and st["by_link"] is True and st["you"] == "the professor (by link)" and st0["view_only"] is True and st0["you"] is None, f"with the key the visitor is “{st['you']}” and not view-only; with a wrong key, or none, view-only as before")
    c, r = far2("/api/brief", {"brief": {**brief, "id": "by-prof"}}, key=KEY)[:2]; cw = far2("/api/brief", {"brief": {**brief, "id": "by-wrong"}}, key="z" * 32)[0]
    say(c == 200 and r.get("saved") == "by-prof" and people()[-1] == {**people()[-1], "account": "the professor (by link)", "did": "/api/brief", "id": "by-prof"} and cw == 403 and not (P / "briefs/by-wrong.json").exists(),
        f"a brief saved through the link is saved and noted with the name ({people()[-1]['account']}); with a wrong key it is refused")
    c, r = far2("/api/session", {"brief": "two-hosts-open"}, key=KEY)[:2]; s3 = r.get("id"); row = next((x for x in far2("/api/sessions", key=KEY)[1] if x["id"] == s3), {})
    WHO["uid"] = B.pw_uid; cb = call(B.pw_uid, "/api/session", {"brief": "two-hosts-open"})
    say(c == 200 and s3 and row.get("by") == "the professor (by link)" and row.get("can_stop") is True and cb[0] == 409 and "the professor (by link)" in cb[1]["error"],
        f"through the link a session is started ({s3}), and it counts like any other: a start by {B.pw_name} meanwhile is refused and names who started it (“{cb[1].get('error', '')[:90]}…”)")
    c, r = far2("/api/stop", {"session": s3}, key=KEY)[:2]
    c2, r2 = call(A.pw_uid, "/api/session", {"brief": "two-hosts-open"}); s4 = r2.get("id"); c3, r3 = far2("/api/stop", {"session": s4}, key=KEY)[:2]
    say(c == 200 and r == {"stopped": s3} and c2 == 200 and c3 == 200 and r3 == {"stopped": s4}, f"the one with the link stops its own session and, like the owner, a session somebody else started ({s4}, started by {A.pw_name})")
    hid = [far2("/checks/access.json", key=KEY)[0], far2("/checks/access.json")[0], call(ME, "/checks/access.json")[0], far2("/harness/control.py", key=KEY)[0]]
    say(hid == [404, 404, 404, 404], f"the file of the keys is given to nobody, not even to the owner or to one who has a key; with a key the visitor still gets the page's own material only: {hid}")
    (P / "checks/access.json").write_text("{}"); gone = far2("/api/status", key=KEY)[1]
    say(gone["view_only"] is True and far2("/api/brief", {"brief": {**brief, "id": "after"}}, key=KEY)[0] == 403, "a link taken out of the file stops working at once: the same browser is view-only again")
    srv2.shutdown()
finally:
    for x in control.STARTED.values():
        if x["proc"].poll() is None: x["proc"].kill()
    srv.shutdown()
print("RESULT:", f"FAIL {len(FAILED)}" if FAILED else "PASS"); [print("  FAILED", f) for f in FAILED]
