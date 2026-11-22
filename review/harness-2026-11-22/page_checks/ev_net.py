"""The page shows a session whose brief has a network (TOPOLOGY.md, stage 3; 2026-11-17), on a SCRATCH copy (EV_PORT, EV_ROOT):
    ev_net.py [session ...]        (default n1, the scripted three-host session of harness_checks/test_network.py)
  picture   "The network" is drawn from the session's network: one box for each host, one line group for each link, the
            queue's mark on the link that has one, each flow in the colour of its place in the list; not the fixed
            two-host picture; with a simulation open it shows that simulation's values
  settings  "Who decides what" lists, as fixed, every setting of the network that is not a knob (worked out here with
            harness/network.py) and the simulation's own; as the AI's, the knobs; each by a plain name
  names     nowhere on the page or in the panes of a test, a simulation, an experiment, the report and the brief stands
            a word of the two-host set-up (UDP goodput, ratio, drops_band0, Sender, ...), nor NaN or undefined
  measures  a simulation's pane lists the network's measures (the brief's outputs), and draws its charts over time
            from the columns of its series: a line for each flow in its colour
  told      what the AI was given names the series by the network's columns
  large     a network of eight hosts in a row is drawn inside the card: no sideways scrolling at 1,440 px
  old       a session without a network (EV_OLD, default s024) is as before: the two-host picture, UDP and TCP in the legend
Nothing is written."""
import sys, os, re, json, pathlib
from playwright.sync_api import sync_playwright
PORT = os.environ.get('EV_PORT', '8611'); BASE = f"http://127.0.0.1:{PORT}/viewer/index.html"; ROOT = pathlib.Path(os.environ['EV_ROOT'])
SIDS = [a for a in sys.argv[1:] if not a.startswith('-')] or ['n1']; OLD = os.environ.get('EV_OLD', 's024')
sys.path.insert(0, str(ROOT / 'harness')); import network
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:60])
def session(b, sid, w=1500):
    ctx = b.new_context(viewport={'width': w, 'height': 1000}); pg = ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.goto(f'{BASE}?session={sid}'); pg.wait_for_selector('#s-notebook .nb-group, #s-system', timeout=60000); pg.wait_for_timeout(1500)
    pg.evaluate("() => { localStorage.setItem('ev-setall', '1'); EV.draw(); }"); pg.wait_for_timeout(300); return pg   # blocks 2 to 7 of the setting are absent until asked for (2026-11-17); these checks read them
SCAN = r"""() => { const bad = /UDP goodput|TCP goodput|UDP loss|UDP queue|TCP queue|UDP share|\bratio\b|UDP blue|udp_goodput|tcp_goodput|udp_loss|drops_band|link_util\b|Sender|Receiver|weightUdp|udpRate|two computers|\bNaN\b|undefined/; const out = [];
  const w = document.createTreeWalker(document.getElementById('ev'), NodeFilter.SHOW_TEXT); let n;
  while ((n = w.nextNode())) { const t = n.textContent.replace(/\s+/g, ' ').trim(); if (!t || !bad.test(t)) continue; const el = n.parentElement; if (el.closest('[data-own], script, style, #s-how, option, #st-given') || !el.getClientRects().length) continue;
    out.push(((el.closest('.ev-card, #p-detail') || {}).id || '?') + ': ' + t.slice(0, 70)); }
  return [...new Set(out)].slice(0, 8); }"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for sid in SIDS:
        meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); g = meta['given']; t = g['topology']; kn = g['knobs']
        pg = session(b, sid)
        r = pg.evaluate("""() => { const S = document.getElementById('net-pic'), q = (s, f) => S ? [...S.querySelectorAll(s)].map(f) : [];
          return { hosts: q('[data-host]', x => x.dataset.host), links: q('.nl[data-link]', x => x.dataset.link), queues: q('.nq', x => x.dataset.queue), old: !!document.querySelector('#s-system svg.sy:not(.net)'),
            lines: q('.nl line[data-flow]', x => [x.dataset.flow, x.getAttribute('stroke')]), dots: q('.nh g[data-flow] circle', x => x.getAttribute('fill')), legend: [...document.querySelectorAll('#lg-flows .lg')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()),
            side: [...document.querySelectorAll('#net-side tr[data-flow], #net-side tr[data-link]')].map(x => x.dataset.flow || x.dataset.link) }; }""")
        col = {f['id']: f"var(--series-{i % 8 + 1})" for i, f in enumerate(t['flows'])}
        say(not r['old'] and sorted(r['hosts']) == sorted(h['id'] for h in t['hosts']) and sorted(r['links']) == sorted(l['id'] for l in t['links']) and sorted(r['queues']) == sorted(l['id'] for l in t['links'] if l.get('queue'))
            and all(c == col[f] for f, c in r['lines']) and {f for f, _ in r['lines']} == set(col) and r['side'] == [f['id'] for f in t['flows']] + [l['id'] for l in t['links']],
            f"{sid}: the picture is drawn from the network: hosts {r['hosts']}, links {sorted(r['links'])}, a queue's mark on {r['queues']}, each flow's lines in its own colour; beside it the flows and the links in words; not the two-host picture")
        # since 2026-11-22 15:33 (the operator): a flow named after its kind is named once ("UDP"), the others "fa · TCP"
        say(r['legend'] == [f['kind'].upper() if str(f['id']).lower() == str(f['kind']).lower() else f"{f['id']} · {f['kind'].upper()}" for f in t['flows']], f"{sid}: the legend's flows are the network's: {r['legend']}")
        w = pg.evaluate("""() => { const rows = k => [...document.querySelectorAll(`#s-system table.st-who:not(.nt) tr[data-set=${k}]`)].map(x => [x.dataset.k, x.querySelector('td').textContent.trim(), (x.querySelector('[data-c=value]') || {}).textContent || '']); return { fixed: rows('fixed'), knob: rows('knob') }; }""")
        have = network.settings(t); fixed = [k for k in have if k not in kn] + [k for k in g.get('system', {})]
        say(sorted(k for k, _, _ in w['fixed']) == sorted(fixed) and [k for k, _, _ in w['knob']] and sorted(k for k, _, _ in w['knob']) == sorted(kn) and all(name and name != k for k, name, _ in w['fixed'] + w['knob'] if '.' in k),
            f"{sid}: “Who decides what” lists the {len(fixed)} fixed settings (the network's own that are no knob, and the simulation's) and the {len(kn)} knobs, each by a plain name (“{w['knob'][0][1]}” for {w['knob'][0][0]})")
        pg.evaluate("() => { EV.s.full = true; EV.draw(); }"); pg.wait_for_timeout(900); found = {'page': pg.evaluate(SCAN)}
        for kind, js in (('test', "EV.s.sel = { t: 'test', id: EV.M.tests[EV.M.tests.length - 1].id }"), ('simulation', "EV.s.sel = { t: 'sim', id: EV.M.sims[EV.M.sims.length - 1].id }"), ('report', "EV.s.sel = { t: 'report', id: 'report' }"), ('experiment', "EV.s.sel = { t: 'exp', id: EV.M.exps[EV.M.exps.length - 1].id }"), ('brief', "EV.s.sel = { t: 'brief', id: 'brief' }")):
            pg.evaluate("() => { " + js + "; EV.draw(); }"); pg.wait_for_timeout(1200); found[kind] = [x for x in pg.evaluate(SCAN) if x.startswith('p-detail')]
        say(not any(found.values()), f"{sid}: no word of the two-host set-up, no NaN and no “undefined” on the page or in the panes of a test, a simulation, the report, an experiment and the brief: {dict((k, v[:3]) for k, v in found.items() if v) or 'none'}")
        pg.evaluate("() => { EV.s.sel = { t: 'sim', id: EV.M.sims[EV.M.sims.length - 1].id }; EV.draw(); }"); pg.wait_for_timeout(3000)
        m = pg.evaluate("""() => { const P = document.getElementById('p-detail'), names = Object.keys(EV.M.meta.given.outputs), rows = [...P.querySelectorAll('table')].flatMap(x => [...x.querySelectorAll('tbody tr td:first-child')].map(c => c.textContent.trim()));
          const C = TASK_VIEW._charts, tput = C.tput ? C.tput.data.datasets.map(d => [d.name, d.borderColor]) : null; const css = n => getComputedStyle(document.querySelector('.ev')).getPropertyValue(n).trim();
          return { listed: names.filter(n => rows.includes(TH_DATA.PLAIN[n] || n)).length, of: names.length, charts: [...P.querySelectorAll('canvas')].map(c => c.id), tput, c1: css('--series-1'), c2: css('--series-2'), head: P.querySelector('#sim-cmd') ? 1 : 0 }; }""")
        own = pg.evaluate("() => { const q = EV.M.sims[EV.M.sims.length - 1]; return q.topology || null; }") or t   # a simulation that changed the structure has its own network, and its measures
        say(m['listed'] == m['of'] == len(network.outputs(t)) and m['charts'][:2] == ['th-c-tput', 'th-c-cwnd'] and m['tput'] and [n for n, _ in m['tput']] == [f['id'] for f in own['flows']] and [c for _, c in m['tput']][:2] == [m['c1'], m['c2']][:len(m['tput'])],
            f"{sid}: a simulation's pane lists the network's {m['of']} measures and draws its charts over time from its series ({m['charts']}): a line for each flow in its colour ({[n for n, _ in m['tput']] if m['tput'] else None})")
        picked = pg.evaluate("() => { const s = EV.M.sims[EV.M.sims.length - 1], S = document.getElementById('net-side'); return { params: s.params, side: S ? S.innerText.replace(/\\s+/g, ' ') : '', head: document.querySelector('#s-system h2 small').textContent }; }")
        change = next(((k, v) for k, v in picked['params'].items() if k in kn and 'choices' in kn[k] and v != kn[k]['default']), None) or next(((k, v) for k, v in picked['params'].items() if k in have and v != kn.get(k, {}).get('default')), None)
        say('simulation' in picked['head'] and (change is None or str(change[1]).replace('Tcp', '') in picked['side']), f"{sid}: with a simulation open the picture and the words beside it show that simulation's values ({change[0]} = {change[1]})" if change else f"{sid}: with a simulation open the heading says so")
        changed = pg.evaluate("() => EV.M.sims.filter(q => q.structure && q.structure.length && q.topology).map(q => q.id)")
        if changed:   # a session in which the AI changed the structure (TOPOLOGY.md, stage 5): a simulation's own network is drawn, with its changes in words
            got = pg.evaluate("""(id) => { EV.s.sel = { t: 'sim', id }; EV.draw(); const q = EV.M.simById[id], S = document.getElementById('net-pic'); return { flows: [...new Set([...S.querySelectorAll('.nh g[data-flow]')].map(x => x.dataset.flow))].sort(), queues: [...S.querySelectorAll('.nq')].map(x => x.dataset.queue).sort(),
              want: { flows: q.topology.flows.map(f => f.id).sort(), queues: q.topology.links.filter(l => l.queue).map(l => l.id).sort() }, says: (document.getElementById('net-changed') || {}).textContent || '', base: EV.M.brief.topology.flows.length }; }""", changed[-1]); pg.wait_for_timeout(400)
            say(got['flows'] == got['want']['flows'] and got['queues'] == got['want']['queues'] and 'changed the structure' in got['says'], f"{sid}: a simulation that changed the structure ({changed[-1]}) is drawn on its own network (flows {got['flows']}, queues on {got['queues']}), and the page says the change in words: “{got['says'][:90]}”")
        told = pg.evaluate("() => { const d = document.querySelector('#st-given'); if (d && d.tagName === 'DETAILS') d.open = true; return d ? d.textContent : ''; }")
        say('<flow>_bps' in json.dumps(g['tools']) and 'drops_band0' not in json.dumps(g['tools']), f"{sid}: what the AI was given describes the series by the network's columns, not by those of two-hosts")
        big = {'hosts': [{'id': f'h{i}'} for i in range(8)], 'links': [{'id': f'l{i}', 'between': [f'h{i}', f'h{i + 1}'], 'rate': '1Gbps', 'delay': '50us', 'mtu': 1500, 'device_queue': 10} for i in range(7)],
               'flows': [{'id': 'f1', 'kind': 'tcp', 'from': 'h0', 'to': 'h7', 'type': 'TcpCubic'}, {'id': 'f2', 'kind': 'udp', 'from': 'h3', 'to': 'h7', 'rate': '10Mbps', 'packet_bytes': 1400}]}
        assert not network.problems(big)
        pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.wait_for_timeout(300)
        L = pg.evaluate("(t) => { const box = document.querySelector('#s-system .ev-scroll'); box.innerHTML = EV.netSvg({ id: 'big', topology: t, knobs: {} }, {}); const s = box.querySelector('svg'); return { hosts: s.querySelectorAll('[data-host]').length, w: Math.round(s.getBoundingClientRect().width), box: box.clientWidth, scroll: box.scrollWidth, doc: document.documentElement.scrollWidth - innerWidth }; }", big)
        say(L['hosts'] == 8 and L['scroll'] <= L['box'] + 1 and L['doc'] <= 0, f"a network of eight hosts in a row is drawn inside the card at 1,440 px ({L['w']} px wide in {L['box']}), with no sideways scrolling")
        say(not pg.errs, f"{sid}: script errors: {pg.errs[:3] or 'none'}"); pg.context.close()
    if (ROOT / 'sessions' / OLD).is_dir():
        pg = session(b, OLD); r = pg.evaluate("() => ({ old: !!document.querySelector('#s-system svg.sy:not(.net)'), net: !!document.getElementById('net-pic'), legend: [...document.querySelectorAll('#lg-flows .lg')].map(x => x.textContent.trim()), fixed: document.querySelectorAll('#s-system table.st-who tr[data-set=fixed]').length })")
        sysn = len(json.loads((ROOT / 'sessions' / OLD / 'session.json').read_text())['given']['system'])
        say(r['old'] and not r['net'] and r['legend'] == ['UDP', 'TCP'] and r['fixed'] == sysn and not pg.errs, f"{OLD}, a session without a network, is as before: the two-host picture, UDP and TCP in the legend, its {sysn} fixed settings; script errors: {pg.errs[:2] or 'none'}")
        pg.context.close()
    b.close()
print('RESULT:', f'FAIL {len(FAILED)}' if FAILED else 'PASS'); [print('  FAILED', f) for f in FAILED]
