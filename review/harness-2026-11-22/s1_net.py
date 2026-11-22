"""Stage 1, item 14 (the coherence audit, 2026-11-22): the link line written for the program has no space inside a value: "1 Gbps" and "50 us" pass the
brief's check (rate_bps and seconds read them), and the program stopped on the token "Gbps", so every simulation of such a brief failed (only " Mbps"
was joined). Usage: s1_net.py NETWORK_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
a = '''        lines.append(f"link {l['id']} {l['between'][0]} {l['between'][1]} rate={l['rate']} delay={l['delay']} mtu={l['mtu']} devq={l['device_queue']}".replace(" Mbps", "Mbps"))'''
b = '''        nos = lambda v: str(v).replace(" ", "")   # no space inside a value: the program reads "1Gbps", not "1 Gbps" (the coherence audit, 2026-11-22)
        lines.append(f"link {l['id']} {l['between'][0]} {l['between'][1]} rate={nos(l['rate'])} delay={nos(l['delay'])} mtu={nos(l['mtu'])} devq={nos(l['device_queue'])}")'''
assert s.count(a) == 1, s.count(a)
p.write_text(s.replace(a, b)); print("patched", p)
