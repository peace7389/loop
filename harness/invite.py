"""Operator tool: personal links to the page (control.py started with --network on).
    python3 harness/invite.py NAME          make a link for NAME and print it (a second link for a name replaces the first)
    python3 harness/invite.py --list        the names that have a link
    python3 harness/invite.py --remove NAME end NAME's link at once
Whoever opens the link in a browser, on a computer or a phone that reaches this machine, uses the page as the owner
does: starts and stops sessions, saves briefs, reviews. The link holds a long key; the browser keeps it in a cookie.
The keys are in checks/access.json (readable by the owner only; not in git, not in an export, never given over HTTP).
The key travels over plain HTTP: give a link only to somebody you would let work under your account."""
import json, os, secrets, socket, subprocess, sys
import tools

ACCESS = tools.ROOT / "checks/access.json"


def main():
    a = sys.argv[1:]
    links = json.loads(ACCESS.read_text()) if ACCESS.is_file() else {}
    if a == ["--list"]:
        print("\n".join(sorted(set(links.values()))) or "no personal link")
        return
    if len(a) == 2 and a[0] == "--remove":
        left = {k: v for k, v in links.items() if v != a[1]}
        print(f"{len(links) - len(left)} link(s) of {a[1]} ended")
        links = left
    elif len(a) == 1 and not a[0].startswith("-") and 1 <= len(a[0]) <= 40:
        links = {k: v for k, v in links.items() if v != a[0]}
        key = secrets.token_urlsafe(24)
        links[key] = a[0]
        ips = [x for x in subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split() if "." in x and not x.startswith(("127.", "172.", "10."))]
        print(f"A personal link for {a[0]}. Open it once in the browser that is to use the page:")
        for host in [socket.getfqdn()] + ips[:1]:
            print(f"  http://{host}:8600/viewer/?key={key}")
    else:
        sys.exit(__doc__)
    ACCESS.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(ACCESS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps(links, indent=1) + "\n")
    os.chmod(ACCESS, 0o600)


if __name__ == "__main__":
    main()
