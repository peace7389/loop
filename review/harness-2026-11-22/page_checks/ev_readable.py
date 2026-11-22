"""The "Done when" checks of ~/project/READABLE_PAGE.md, part by part (parts 1 to 8; name the parts to run, default all
that are written). Chromium at 1500 x 1000, light mode, unless a line says otherwise. Figures are counted here from the
ledgers (read without their draft records), never taken from the page.
The scratch copy must hold s024 (and s006, s007, s014, s018).
usage:  EV_PORT=8611 EV_ROOT=<scratch>/home/project EV_SCRIPT=ev_readable.py ./ev.sh [1 2 ...]"""
import os, re, sys, json, asyncio, pathlib
from playwright.async_api import async_playwright
PORT = os.environ.get('EV_PORT', '8600'); BASE = f"http://127.0.0.1:{PORT}/viewer/index.html"
ROOT = pathlib.Path(os.environ.get('EV_ROOT', str(pathlib.Path.home() / 'project')))
PARTS = [a for a in sys.argv[1:] if not a.startswith('-')] or ['1', '2', '3', '4', '5', '6', '7', '8']
FAILED = []
def ledger(sid): return [r for r in (json.loads(l) for l in (ROOT / 'sessions' / sid / 'ledger.jsonl').read_text().splitlines() if l.strip()) if r['type'] not in ('draft', 'scratch')]
def say(part, ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(f'{part}: {text[:40]}')
async def fresh(b, sid, w=1500, h=1000, store=None, scheme='light', table=True):
    """A new browser profile (nothing remembered) on a session's page; store: what the browser remembers before the page loads.
    table: the table "The same, test by test" open (it is folded under the board in Brief; part 1 looks at the page as it comes)."""
    if table: store = {'ev-find': '1', 'ev-setall': '1', **(store or {})}   # ev-setall: blocks 2 to 7 of the setting shown (absent until asked for since 2026-11-17)
    ctx = await b.new_context(viewport={'width': w, 'height': h}, color_scheme=scheme)
    if store: await ctx.add_init_script("try { const s = %s; for (const k in s) if (localStorage.getItem(k) === null) localStorage.setItem(k, s[k]); } catch (e) {}" % json.dumps(store))
    pg = await ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)[:160])); await go(pg, sid); return pg
async def go(pg, sid):
    await pg.goto(f'{BASE}?session={sid}'); await pg.wait_for_function("(s) => typeof EV !== 'undefined' && EV.M && EV.M.id === s && document.getElementById('ev-head')", arg=sid, timeout=60000); await pg.wait_for_timeout(700)

# ---- what a session's records say (the checks compare the page with these)
def tests_of(led):
    """The tests in the order stated: (experiment, hypothesis, rule), with the check and the labels, as the page derives them."""
    out = []
    for x in [r for r in led if r['type'] == 'experiment']:
        rules = x['body'].get('decision_rules') or x['body'].get('rules') or []; nth = {}
        checks = [c for c in led if c['type'] == 'check' and c.get('parent') == x['id']]
        for r in rules:
            n = nth[r['for']] = nth.get(r['for'], 0) + 1; rule = r.get('decision_rule') or r.get('rule'); same = [c for c in checks if c['body'].get('for') == r['for']]
            chk = next((c for c in same if (c['body'].get('decision_rule') or c['body'].get('rule')) == rule), None) or (same[n - 1] if len(same) >= n else None)
            out.append({'id': f"{x['id']}.{r['for']}" + (f'.{n}' if n > 1 else ''), 'exp': x['id'], 'hyp': r['for'], 'rule': rule, 'check': chk, 'turn': x.get('turn')})
    return out

BOX = r"""() => { const g = id => document.getElementById(id), box = el => { if (!el) return null; const b = el.getBoundingClientRect(); return { top: Math.round(b.top + scrollY), bottom: Math.round(b.bottom + scrollY), h: Math.round(b.height) }; };
  const scrolls = sel => [...document.querySelectorAll(sel)].filter(el => { const c = getComputedStyle(el); if (!el.getClientRects().length || el.closest('details:not([open])')) return false; return (/(auto|scroll)/.test(c.overflowX) && el.scrollWidth > el.clientWidth + 1) || (/(auto|scroll)/.test(c.overflowY) && el.scrollHeight > el.clientHeight + 1); }).map(el => el.id || el.className);
  return { win: innerHeight, doc_w: document.documentElement.scrollWidth, win_w: innerWidth, head: box(g('ev-head')), setting: box(g('s-system')), glance: box(g('s-made')), find: box(g('s-find')), notebook: box(g('s-notebook')), proposes: box(g('s-proposes')), closer: box(g('s-closer')), how: box(g('s-how')),
    inner: scrolls('#ev-head, #ev-head *, #s-system, #s-system *, #s-made, #s-made *, #s-find, #s-find *'), rows: document.querySelectorAll('#s-find tbody tr').length, high: !!g('s-high'),
    level: [...document.querySelectorAll('#ev-head [data-act=level]')].map(x => x.textContent + (x.classList.contains('on') ? '*' : '')), how_open: g('s-how') ? g('s-how').open : null }; }"""
VIEWS = {'best': 's-best', 'knob': 's-knob', 'alone': 's-alone', 'verdicts': 's-verdicts', 'tests': 's-tests', 'flow': 's-work', 'map': 's-map', 'tree': 's-tree'}

async def part1(b):
    print('PART 1  three levels of detail'); P = '1'; sid = 's024'; led = ledger(sid); tests = tests_of(led)
    pg = await fresh(b, sid, store={'ev-read': '1'}, table=False); r = await pg.evaluate(BOX)
    global VIEWS; VIEWS = {k: v for k, v in VIEWS.items() if k in await pg.evaluate("() => EV.CLOSER.map(q => q[0])")}  # the analysis views this tree folds (the hypothesis map became the board of “What it needed to find out”)
    say(P, r['level'] == ['Brief*', 'Full'], f"a reader who has remembered nothing sees the page in Brief; the switch is in the header strip: {r['level']}")
    say(P, r['head']['bottom'] <= r['win'] and r['setting']['bottom'] <= r['win'] and (r['glance'] or r['find'])['top'] <= r['win'] - 120,
        f"{sid}, Brief, 1500 x 1000: the first screen shows the header strip (to {r['head']['bottom']} px), the setting ({r['setting']['top']} to {r['setting']['bottom']} px) and the top of {'the session at a glance' if r['glance'] else 'what it needed to find out (the glance is not drawn since 2026-11-22)'} (from {(r['glance'] or r['find'])['top']} px; the window is {r['win']} px high)")
    say(P, r['doc_w'] <= r['win_w'] and not r['inner'], f"no sideways scrolling ({r['doc_w']} px of content in {r['win_w']} px) and no part of level 1 scrolls inside itself: {r['inner'] or 'none'}")
    say(P, r['find']['bottom'] <= 2 * r['win'] and r['rows'] == min(len(tests), 9), f"“What it needed to find out” is complete within the second screen (it ends at {r['find']['bottom']} px, two screens are {2 * r['win']} px), with {r['rows']} rows for {len(tests)} tests")
    order = [k for k in ('head', 'setting', 'glance', 'find', 'notebook', 'proposes', 'closer', 'how') if r[k]]; tops = [r[k]['top'] for k in order if k != 'head']
    say(P, tops == sorted(tops) and order == ['head', 'setting'] + (['glance'] if r['glance'] else []) + ['find', 'notebook', 'proposes', 'closer', 'how'], f"level 1 stands open at the top (the setting, the session at a glance, what it needed to find out), level 2 below it (the notebook, what it proposes), then “Looking closer” and “How to read this page”: {[(k, r[k]['top']) for k in order if k != 'head']}")
    # every analysis view: folded in Brief, one line saying what it holds, reachable in one click, and the page does not move
    v0 = await pg.evaluate("(V) => ({ rows: [...document.querySelectorAll('#s-closer .lc-row')].map(q => [q.dataset.view, q.querySelector('button').textContent.replace(/^[▸▾]/, '').trim(), (q.querySelector('.sm') || {}).textContent || '']), there: Object.entries(V).filter(([k, id]) => document.getElementById(id)).map(q => q[0]) })", VIEWS)
    say(P, [q[0] for q in v0['rows']] == list(VIEWS) and all(q[1] and len(q[2]) > 15 for q in v0['rows']) and not v0['there'], f"“Looking closer” lists the {len(v0['rows'])} analysis views, each folded, each with one line saying what it holds (e.g. “{v0['rows'][0][1]}: {v0['rows'][0][2]}”); none is drawn in Brief: {v0['there'] or 'none'}")
    opened = {}
    for k, el in VIEWS.items():
        y0 = await pg.evaluate("() => { document.getElementById('s-closer').scrollIntoView(); return scrollY; }"); await pg.click(f'#s-closer .lc-row[data-view={k}] button'); await pg.wait_for_timeout(250)
        opened[k] = await pg.evaluate("([id, y0]) => { const el = document.getElementById(id); return { there: !!el, text: el ? el.innerText.trim().length : 0, moved: Math.abs(scrollY - y0) }; }", [el, y0])
        await pg.click(f'#s-closer .lc-row[data-view={k}] button'); await pg.wait_for_timeout(120)
    bad = {k: v for k, v in opened.items() if not v['there'] or v['text'] < 20 or v['moved'] > 1}
    say(P, not bad, f"every analysis view is reachable in one click on its line, and the click does not move the page ({', '.join(opened)})" + (f": {bad}" if bad else ''))
    still = await pg.evaluate("(V) => Object.entries(V).filter(([k, id]) => document.getElementById(id)).map(q => q[0])", VIEWS)
    say(P, not still, f"a second click folds a view again: {still or 'all folded'}")
    # Full opens them all, and the browser remembers it
    await pg.click('#ev-head [data-act=level][data-id=full]'); await pg.wait_for_timeout(500)
    full = await pg.evaluate("(V) => ({ there: Object.entries(V).filter(([k, id]) => document.getElementById(id)).map(q => q[0]), rows: document.querySelectorAll('#s-find tbody tr').length, how: document.getElementById('s-how').open, clamp: !!document.querySelector('#ov-expl.clamp'), level: [...document.querySelectorAll('#ev-head [data-act=level]')].map(x => x.textContent + (x.classList.contains('on') ? '*' : '')), folds: document.querySelectorAll('#s-system [data-act=sysfold], #s-made [data-act=glfold]').length })", VIEWS)
    say(P, full['there'] == list(VIEWS) and full['rows'] == len(tests) and full['how'] and not full['clamp'] and full['level'] == ['Brief', 'Full*'], f"Full opens every folded section: the {len(full['there'])} analysis views, every row of “What it needed to find out” ({full['rows']}), the explanation in full, “How to read this page”")
    await go(pg, sid); again = await pg.evaluate("(V) => [[...document.querySelectorAll('#ev-head [data-act=level]')].map(x => x.textContent + (x.classList.contains('on') ? '*' : '')), Object.entries(V).filter(([k, id]) => document.getElementById(id)).length]", VIEWS)
    await pg.click('#ev-head [data-act=level][data-id=brief]'); await pg.wait_for_timeout(300); await go(pg, sid); back = await pg.evaluate("(V) => [[...document.querySelectorAll('#ev-head [data-act=level]')].map(x => x.textContent + (x.classList.contains('on') ? '*' : '')), Object.entries(V).filter(([k, id]) => document.getElementById(id)).length]", VIEWS)
    say(P, again == [['Brief', 'Full*'], len(VIEWS)] and back == [['Brief*', 'Full'], 0], f"the browser remembers the switch: after a reload the page is still Full ({again[1]} views open); switched back, it reloads in Brief ({back[1]} open)")
    # nothing of level 3 at levels 1 and 2 except as something to click
    rules = [t['rule'] for t in tests if t['rule']]
    l3 = await pg.evaluate("(rules) => { const ids = ['ev-head', 's-system', 's-made', 's-find', 's-notebook', 's-proposes'], out = { canvas: 0, flow: 0, rules: 0, queue: 0 }; ids.forEach(id => { const el = document.getElementById(id); if (!el) return; out.canvas += el.querySelectorAll('canvas').length; out.flow += el.querySelectorAll('.t-flow').length; out.queue += el.querySelectorAll('.qlist').length; const t = el.innerText; out.rules += rules.filter(q => t.includes(q)).length; }); out.pane = !!document.querySelector('.ev-side #p-detail'); return out; }", rules)
    await pg.evaluate("(id) => { EV.s.sel = { t: 'test', id }; EV.draw(); }", tests[0]['id']); await pg.wait_for_timeout(300)
    pane = await pg.evaluate("(rule) => { const p = document.getElementById('p-detail'); return { flow: p.querySelectorAll('.t-flow, svg').length, rule: p.innerText.includes(rule) || [...p.querySelectorAll('.td-exact code')].some(c => c.textContent === rule) }; }", tests[0]['rule'])
    say(P, l3 == {'canvas': 0, 'flow': 0, 'rules': 0, 'queue': 0, 'pane': True} and pane['flow'] and pane['rule'], f"nothing of level 3 stands at levels 1 and 2: no chart over time, no flow chart, no review queue, and none of the {len(rules)} decision rules in its exact text ({l3}); a click on a test opens them in the detail pane (its flow chart and the exact rule are there)")
    # the highlights are no card: their moments are marks on the notebook's cards and in the rows above
    first_held = next((t['id'] for t in tests if t['check'] and t['check']['body'].get('result') == 'held'), None); rep = next((q for q in led if q['type'] == 'report'), None)
    c1 = (rep['body'].get('claims') or [{}])[0].get('evidence', []) if rep else []; hyps = {q['id']: q for q in led if q['type'] == 'hypothesis'}
    cited = sorted(t['id'] for t in tests if t['check'] and t['check']['id'] in c1)
    # a failed test from which a later hypothesis follows: a hypothesis whose follows_from names its check
    failed_followed = sorted(t['id'] for t in tests if t['check'] and t['check']['body'].get('result') == 'failed' and any(t['check']['id'] in (h['body'].get('follows_from') or []) for h in hyps.values()))
    m = await pg.evaluate("() => ({ high: !!document.getElementById('s-high'), marks: [...document.querySelectorAll('#s-notebook .nb-mark')].map(x => [x.dataset.m, (x.closest('.nb-card') || { dataset: {} }).dataset.id || 'heading', x.textContent.trim()]), rows: [...document.querySelectorAll('#s-find tr')].filter(r => r.querySelector('.fturn')).map(r => r.dataset.id), rules: EV.highlights(EV.M).items.map(q => q.rule) })")
    got = lambda kind: sorted(q[1] for q in m['marks'] if q[0] == kind)
    say(P, not m['high'] and got('first') == [first_held] and set(failed_followed) <= set(got('turned')) and [q for q in cited if q in got('cited')] == cited and len(got('best')) <= 1,
        f"“Highlights” is no card any more; its moments are marks on the notebook: “first test that held” on {got('first')} (the ledger: {first_held}), “changed course here” on {got('turned')} (failed tests a later hypothesis names: {failed_followed}), “cited by claim 1” on {got('cited')} (the ledger: {cited}), “best result” {[q[2] for q in m['marks'] if q[0] == 'best'] or 'not applicable: an open goal'}")
    say(P, set(failed_followed) <= set(m['rows']), f"and in the rows of “What it needed to find out”: “changed course” on {m['rows']}")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

HEADS = [('s-system', 'The setting', 'What is this network, what was the AI asked, and what could it see?'), ('s-made', 'The session at a glance', 'What happened overall?'),
         ('s-find', 'What it needed to find out', 'Which hypotheses did it set itself, and what did it learn?'), ('s-notebook', 'The work, step by step', 'How did it test each?'),
         ('s-proposes', 'What it proposes', 'What does it recommend, on what evidence, and where does that stop being true?'), ('s-research', 'How it worked as a researcher', 'Did it work the way a researcher does?'),
         ('s-closer', 'Looking closer', 'How did the search go?'), ('s-how', 'How to read this page', 'What is a turn, a test, a check?')]
SECS = r"""() => { const t = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : null), top = el => Math.round(el.getBoundingClientRect().top + scrollY);
  const head = el => { const h = el.querySelector('h2, summary b'); if (!h) return null; const c = h.cloneNode(true); c.querySelectorAll('small, button, span').forEach(x => x.remove()); return t(c); };
  return { secs: [...document.querySelectorAll('#ev [id^="s-"]')].filter(el => ['s-system', 's-made', 's-find', 's-notebook', 's-proposes', 's-research', 's-closer', 's-how'].includes(el.id)).map(el => ({ id: el.id, head: head(el), q: t(el.querySelector('.sec-q')), top: top(el) })),
    strip: [...document.querySelectorAll('#ev-head .hf')].map(f => [f.dataset.f, t(f.querySelector('span')), t(f.querySelector('b'))]), strip_lines: new Set([...document.querySelectorAll('#ev-head .hf')].map(f => Math.round(f.getBoundingClientRect().top))).size,
    first_card: document.querySelector('#s-notebook .nb-card') ? top(document.querySelector('#s-notebook .nb-card')) : null, report_top: document.getElementById('s-report') ? top(document.getElementById('s-report')) : null, proposes_top: top(document.getElementById('s-proposes')),
    proposes: t(document.getElementById('s-proposes')), none: t(document.getElementById('ov-none')), none_warn: !!document.querySelector('#ov-none .warnc'), nav: [...document.querySelectorAll('.ev-nav button')].map(t), how_open: document.getElementById('s-how').open,
    refused: [...document.querySelectorAll('#s-notebook .nb-refused')].map(el => { let h = el.previousElementSibling; while (h && !h.classList.contains('nb-turn')) h = h.previousElementSibling; return { rec: el.dataset.rec, turn: h ? Number(h.dataset.turn) : null, text: t(el), directly_under: !!h && (() => { let q = h.nextElementSibling; while (q && q !== el) { if (!q.classList.contains('nb-refused') && !q.classList.contains('nb-refsum')) return false; q = q.nextElementSibling; } return true; })() }; }) }; }"""

async def part2(b):
    print('PART 2  the order of the session page'); P = '2'
    pg = await fresh(b, 's024'); r = await pg.evaluate(SECS); want = [h for h in HEADS if any(q['id'] == h[0] for q in r['secs'])]
    got = [(q['id'], q['head'], q['q']) for q in r['secs']]; tops = [q['top'] for q in r['secs']]
    say(P, got == want and tops == sorted(tops) and len(got) >= 7, f"s024: the sections in the sheet's order, each with its heading and under it the reader's question ({len(got)} sections): {[q[1] for q in got]}" + ('' if got == want else f": the page has {got}"))
    missing = [h[1] for h in HEADS if h not in want]
    print(f"   sections of the sheet not on the page yet: {missing or 'none'}")
    say(P, [q[2] for q in got] == [q[2] for q in want] and all(q[2] for q in got), f"every heading has its question: {[q[2] for q in got]}")
    say(P, r['first_card'] is not None and r['first_card'] < r['proposes_top'] and r['first_card'] < r['report_top'], f"s024: the first notebook card ({r['first_card']} px) is reached before any text of the final report (“What it proposes” starts at {r['proposes_top']} px, the final report at {r['report_top']})")
    labels = [q[1] for q in r['strip']]; led = ledger('s024'); rep = next(q for q in led if q['type'] == 'report')['body']; meta = json.loads((ROOT / 'sessions/s024/session.json').read_text())
    say(P, labels == ['Brief', 'Session', 'How it ended', 'Simulations', 'Recommends', 'Detail'] + (['Walk'] if 'Walk' in labels else []) and r['strip_lines'] == 1 and dict((q[0], q[2]) for q in r['strip'])['how'] == meta['how'] and dict((q[0], q[2]) for q in r['strip'])['sims'].startswith(str(meta['simulations'])) and str(rep['recommendation']['weightUdp']) in dict((q[0], q[2]) for q in r['strip'])['rec'],
        f"the header strip, on one line: {[(q[1], q[2]) for q in r['strip']]} (session.json: how “{meta['how']}”, {meta['simulations']} simulations; the report recommends weightUdp {rep['recommendation']['weightUdp']})")
    say(P, r['how_open'] and r['nav'][:2] == ['Home', 'Compare sessions'] and r['nav'][-2:] == ['Session', 'Operator'], f"“How to read this page” is open on a reader's first visit; the Operator and Compare tabs keep their places in the top bar: {r['nav']}")
    await go(pg, 's024'); again = await pg.evaluate("() => document.getElementById('s-how').open")
    say(P, not again, "on the next visit it is folded, at the foot of the page")
    # the stated exceptions to "a click never moves the page": a turn in section 2 and a row in section 3 bring the notebook to that place
    if not await pg.evaluate("() => !!document.getElementById('s-made')"): print("   skipped: a click on a turn of “The session at a glance” (the card is not drawn since 2026-11-22)")
    else:
     await pg.evaluate("() => window.scrollTo(0, 0)"); await pg.click('#s-made a.gt[data-id="2"]'); await pg.wait_for_timeout(500)
     t2 = await pg.evaluate("() => { const el = document.querySelector('#s-notebook .nb-turn[data-turn=\"2\"]'), b = el.getBoundingClientRect(), hd = document.getElementById('ev-head').getBoundingClientRect(); return { top: Math.round(b.top), under_strip: b.top >= hd.bottom - 1, in_view: b.top < innerHeight, pane: document.querySelector('#p-detail h2').innerText.replace(/\\s+/g, ' ').slice(0, 30), y: Math.round(scrollY) }; }")
     say(P, t2['in_view'] and t2['under_strip'] and t2['y'] > 0 and 'turn 2' in t2['pane'], f"a click on “turn 2” in “The session at a glance” brings the notebook to its turn 2 (its heading is {t2['top']} px from the top, below the header strip) and opens the turn's work log beside it (“{t2['pane']}”)")
    tid = tests_of(led)[4]['id']; await pg.evaluate("() => window.scrollTo(0, document.getElementById('s-find').getBoundingClientRect().top + scrollY - 80)"); await pg.click(f'#s-find tr[data-id="{tid}"] td.fq'); await pg.wait_for_timeout(500)
    c5 = await pg.evaluate("(id) => { const el = [...document.querySelectorAll('#s-notebook .nb-card')].find(q => q.dataset.id === id), b = el.getBoundingClientRect(); return { in_view: b.top >= 0 && b.top < innerHeight, sel: el.classList.contains('sel'), pane: document.querySelector('#p-detail h2').innerText.replace(/\\s+/g, ' ').slice(0, 40) }; }", tid)
    say(P, c5['in_view'] and c5['sel'], f"a click on the row of {tid} in “What it needed to find out” opens its notebook card (selected, in view) and its test in the detail pane (“{c5['pane']}”)")
    # a refused answer or part: a line under its turn heading
    for sid in ('s024', 's007', 's014'):
        if sid != 's024': await go(pg, sid); 
        r2 = await pg.evaluate(SECS); l2 = ledger(sid); want_ref = sorted((q['id'], q.get('turn') or 0) for q in l2 if q['type'] == 'malformed' or (q['type'] == 'note' and q['body'].get('part')))
        got_ref = sorted((q['rec'], q['turn']) for q in r2['refused'])
        say(P, got_ref == want_ref and all(q['directly_under'] for q in r2['refused']) and all(q['text'].startswith('refused') for q in r2['refused']), f"{sid}: each refused answer or part is a line under its turn's heading ({len(got_ref)} lines for the {len(want_ref)} refusals of the ledger)" + (f", e.g. “{r2['refused'][0]['text'][:90]}”" if r2['refused'] else ''))
        if sid == 's007':
            m7 = json.loads((ROOT / 'sessions/s007/session.json').read_text())
            say(P, r2['none'] and r2['none'].startswith('No final report.') and m7['how'] in r2['none'] and not r2['none_warn'] and r2['report_top'] is None and [q for q in r2['secs'] if q['id'] == 's-proposes'], f"s007: section 5, “What it proposes”, says “{r2['none']}” in plain words, not in the warning colour")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

BLOCKS = r"""() => [...document.querySelectorAll('#st-blocks .st-b')].map(b => [b.dataset.block, (b.querySelector('.st-t') || {}).textContent || null, b.dataset.comp, (b.querySelector('.st-says') || {}).textContent || (b.querySelector('.st-h') || {}).title || null])"""
LISTS = r"""() => { const L = n => [...document.querySelectorAll(`#st-blocks [data-list=${n}] li, #st-blocks ul[data-list=${n}] li`)], keys = el => (el && el.dataset.keys ? el.dataset.keys.split(',') : []), it = (n, k) => L(n).find(li => li.dataset.it === k);
  const cannot = [...document.querySelectorAll('#st-blocks ul[data-list=cannot] li')].map(li => li.dataset.it);
  return { told: L('told').map(li => li.dataset.it), fixed: keys(it('told', 'fixed')), knobs: keys(it('told', 'knobs')), goal: (it('told', 'goal') || { dataset: {} }).dataset.kind, sims: (it('told', 'limits') || { dataset: {} }).dataset.sims, per: (it('told', 'limits') || { dataset: {} }).dataset.per,
    measures: keys(it('told', 'measures')), not: L('not').map(li => li.dataset.it), not_text: L('not').map(li => li.textContent.trim()), can: L('can').filter(li => !cannot.includes(li.dataset.it) || li.closest('ul').dataset.list !== 'cannot').map(li => li.dataset.it).filter(k => !['change', 'exceed', 'more'].includes(k)), tools: L('can').filter(li => li.dataset.tool).map(li => li.dataset.tool), cannot,
    exact: (document.getElementById('st-given') || {}).textContent || null, exact_says: (document.querySelector('#st-exact summary') || {}).textContent || null }; }"""
# every value the set-up form holds, as a brief and as the flags it will start with
FORM = r"""() => { const b = BRIEF_EDITOR.toBrief(), id = b.id; delete b.id; return { brief: b, id, flags: EV.flags(), policy: EV.nw.policy, changed: Number((document.getElementById('be-changed') || { dataset: { n: '-1' } }).dataset.n), marks: document.querySelectorAll('#new-setup .chg').length,
  state: document.getElementById('be-state').textContent.replace(/\s+/g, ' ').trim(), start: document.getElementById('be-start').textContent, start_off: document.getElementById('be-start').disabled, strip: [...document.querySelectorAll('#be-strip .hf')].map(f => [f.dataset.f, f.querySelector('span').textContent.trim(), f.querySelector('b').textContent.trim()]) }; }"""
def harness_tools():
    """harness/tools.py of the copy under test, imported with HOME at that copy (it reads its own manifest and sessions)."""
    import importlib; os.environ['HOME'] = str(ROOT.parent); sys.path.insert(0, str(ROOT / 'harness')); return importlib.import_module('tools')

async def part3(b):
    print('PART 3  the setting, and setting up a session, are one design'); P = '3'; sid = 's024'; meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); g = meta['given']; tools = harness_tools()
    pg = await fresh(b, sid, store={'ev-read': '1'})
    # blocks 2 to 4 come folded to one line each (2026-11-17, the operator: hidden by default); "open" shows a block in full, and the lists are read there
    # as the page comes, blocks 2 to 7 are not there at all; one button under the picture shows them in full, and hides them again (2026-11-17, the operator)
    p0 = await fresh(b, sid, table=False)
    f0 = await p0.evaluate("() => ({ blocks: [...document.querySelectorAll('#st-blocks .st-b')].map(x => x.dataset.block), more: (document.querySelector('#st-more [data-act=setall]') || {}).textContent || null, at: (b => [Math.round(b.left), Math.round(b.top + scrollY), Math.round(b.width)])(document.querySelector('#st-more [data-act=setall]').getBoundingClientRect()), one: !!document.querySelector('#st-blocks [data-block=network] .st-n'), lines: document.querySelectorAll('#st-blocks .st-line').length })")
    await p0.click('#st-more [data-act=setall]'); await p0.wait_for_timeout(300)
    f1 = await p0.evaluate("() => ({ blocks: [...document.querySelectorAll('#st-blocks .st-b')].map(x => x.dataset.block), more: (document.querySelector('#st-more [data-act=setall]') || {}).textContent || null, at: (b => [Math.round(b.left), Math.round(b.top + scrollY), Math.round(b.width)])(document.querySelector('#st-more [data-act=setall]').getBoundingClientRect()), one: !!document.querySelector('#st-blocks [data-block=network] .st-n'), lines: document.querySelectorAll('#st-blocks .st-line').length, folds: document.querySelectorAll('#st-blocks [data-act=setfold]').length })")
    await p0.click('#st-more [data-act=setall]'); await p0.wait_for_timeout(300); f2 = await p0.evaluate("() => document.querySelectorAll('#st-blocks .st-b').length"); await p0.context.close()
    say(P, f0['blocks'] == ['network'] and f0['more'] == 'show the rest' and f1['blocks'] == ['network', 'who', 'aim', 'told', 'limits', 'kept', 'runs'] and f1['more'] == 'hide the rest' and not f1['lines'] and not f1['folds'] and f2 == 1 and not f0['one'] and f1['one'] and f0['at'] == f1['at'],
        f"{sid}: as the page comes, “The setting” shows the network alone; one button shows blocks 2 to 7 in full (no block is cut to a line, none has a fold of its own) and hides them again; the button does not move when they come ({f0['at']} and {f1['at']}: left, top, width), and the picture's block has its number 1 only while the others are shown")
    bl = await pg.evaluate(BLOCKS); L = await pg.evaluate(LISTS)
    heads = ['The network', 'Who decides what', 'The aim', 'What the AI is told, is not told, and can do', 'The limits', 'Kept from the AI (operator)', 'How the AI runs']
    say(P, [q[1] for q in bl] == heads and len({q[2] for q in bl}) == 7, f"{sid}: “The setting” has the seven blocks of the sheet, in its order: {[q[1] for q in bl]}")
    # the three lists against session.json and tools.py
    ok_told = (L['told'] == ['task', 'description', 'fixed', 'knobs', 'goal', 'limits'] + (['baseline'] if meta['flags']['baseline'] in (True, 'on') else []) + ['measures', 'record'] and sorted(L['fixed']) == sorted(g['system']) and sorted(L['knobs']) == sorted(g['knobs'])
               and L['goal'] == g['goal']['kind'] and [L['sims'], L['per']] == [str(g['limits']['simulations']), str(g['limits']['simulations_per_experiment'])] and L['measures'] == list(g['outputs']) == list(tools.MANIFEST['outputs']))
    say(P, ok_told, f"“The AI is told” agrees with session.json: the task, the description, its {len(L['fixed'])} fixed settings {sorted(L['fixed'])}, its {len(L['knobs'])} knobs {sorted(L['knobs'])}, the goal ({L['goal']}), the limits ({L['sims']} and {L['per']}), the baseline (flag: {meta['flags']['baseline']}), the {len(L['measures'])} measures (those of harness/manifest.json), its own record")
    say(P, L['not'] == ['policy', 'code', 'operator', 'sessions'] and 'policy' not in json.dumps(g) and 'TWOHOSTS' not in json.dumps(g) and not any(k in json.dumps(g) for k in ('checks/', 'sweep', 'answer key')), f"“The AI is not told”: {L['not_text']}; and what the session was given names none of them (no policy, no path under checks/, no sweep, no answer key in session.json's “given”)")
    say(P, L['tools'] == list(g['tools']) and set(g['tools']) <= set(tools.TOOLS) and L['can'][:2] == ['plan', 'set'] and L['can'][-1] == 'state' and L['cannot'] == ['change', 'exceed', 'more'], f"“The AI can” agrees with tools.py: one line per tool the harness offers {L['tools']} (tools.TOOLS: {list(tools.TOOLS)}), besides planning, setting the knobs and stating its hypotheses, rules, verdicts and report; “It cannot”: {L['cannot']}")
    tools.open_session(sid); want = tools.describe_system()
    try: got = json.loads(L['exact'])
    except Exception: got = None
    say(P, got == want and json.dumps(got) == json.dumps(want) and L['exact_says'] == 'the exact text the AI was given', f"“{L['exact_says']}” equals what describe_system() returns for {sid}, word for word and in the same order ({len(json.dumps(want))} characters, {len(want)} parts: {list(want)[:4]}…)")
    # the policy: nowhere on the Session tab with the operator columns off; named with them on
    pol = json.loads(await pg.evaluate("() => fetch('../api/status').then(r => r.text())"))
    pol = next(x for x in pol['sessions'] if x['id'] == sid)['policy']
    HIDE = r"""(word) => { const re = new RegExp('\\b' + word + '\\b', 'i'), hits = []; document.querySelectorAll('#ev *').forEach(el => { [...el.childNodes].filter(n => n.nodeType === 3 && re.test(n.textContent)).forEach(n => hits.push('text: ' + n.textContent.trim().slice(0, 50)));
      [...el.attributes].filter(a => !['class', 'style', 'd', 'href', 'src'].includes(a.name) && re.test(a.value)).forEach(a => hits.push(a.name + ': ' + a.value.slice(0, 50))); });
      return { hits, mark: (document.getElementById('sy-pol') || {}).textContent || null, kept: document.getElementById('st-kept') ? [document.getElementById('st-kept').dataset.shown, document.getElementById('st-kept').textContent.trim()] : (document.querySelector('[data-block=kept] .st-line') || {}).textContent || null }; }"""
    await pg.evaluate("() => { localStorage.setItem('ev-full', '1'); EV.s.full = true; EV.s.sel = { t: 'session', id: EV.M.id }; EV.draw(); }"); await pg.wait_for_timeout(400); off = await pg.evaluate(HIDE, pol)
    say(P, pol == 'cap' and not off['hits'] and off['mark'] == 'policy not told to the AI' and off['kept'] and off['kept'][0] == '0', f"{sid} (its policy, from control.py: {pol}), operator columns off, every folded part open and the session's summary in the pane: the word “{pol}” stands nowhere on the Session tab, in no text and no hover ({len(off['hits'])} places); the scheduler carries the mark “{off['mark']}”; block 6 says “{off['kept'][1]}”")
    await pg.evaluate("() => { EV.s.op = true; EV.draw(); }"); await pg.wait_for_timeout(300); on = await pg.evaluate(HIDE, pol)
    say(P, on['mark'] == f'policy: {pol} · not told to the AI' and on['kept'][0] == '1' and f'scheduling policy: {pol}' in on['kept'][1], f"with the operator columns on, the mark names it (“{on['mark']}”) and block 6 shows it (“{on['kept'][1][:60]}”)")
    await pg.evaluate("() => { EV.s.op = false; localStorage.setItem('ev-full', '0'); EV.s.full = false; EV.s.sel = null; EV.draw(); }"); await pg.wait_for_timeout(300)
    low = await pg.evaluate("() => ['limits', 'kept', 'runs'].map(k => { const b = document.querySelector(`#st-blocks [data-block=${k}]`); return [k, !!b.querySelector('.st-line'), b.textContent.replace(/\\s+/g, ' ')]; })")
    used = sum(1 for q in ledger(sid) if q['type'] == 'simulation' and not q['body'].get('same_as') and q.get('parent') != 'X0')
    say(P, not any(q[1] for q in low) and str(g['limits']['simulations']) in low[0][2] and str(g['limits']['simulations_per_experiment']) in low[0][2] and str(used) in low[0][2] and str(meta['flags']['temperature']) in low[2][2],
        f"blocks 5 to 7 stand in full like the others: the limits ({g['limits']['simulations']} in all, {g['limits']['simulations_per_experiment']} in one turn, {used} used: the ledger's count), what is kept from the AI, and the options of the session (temperature {meta['flags']['temperature']})")
    # ---- "Start a new session from this setup"
    await pg.click('#s-system [data-act=setagain]'); await pg.wait_for_function("() => document.querySelector('#new-setup #be-start') && document.querySelector('#be-pic svg.sy') && typeof BRIEF_EDITOR !== 'undefined' && BRIEF_EDITOR.s && BRIEF_EDITOR.s.from", timeout=60000); await pg.wait_for_timeout(500)
    f = await pg.evaluate(FORM); mine = {k: g[k] for k in ('description', 'system', 'knobs', 'goal', 'limits')}; fl = meta['flags']   # the task is not a field of the form any more: the harness writes it
    flags_equal = 'budget' not in f['flags'] and f['flags']['draft'] == fl['draft'] and f['flags'].get('max_tokens') == fl['max_tokens'] and f['flags'].get('temperature') == fl['temperature'] and f['flags']['baseline'] == (fl['baseline'] in (True, 'on'))
    same_order = all(list(f['brief'][k]) == list(mine[k]) for k in ('system', 'knobs'))
    say(P, f['brief'] == mine and same_order and flags_equal and f['policy'] == pol and f['changed'] == 0 and f['marks'] == 0, f"“Start a new session from this setup” on {sid} opens the set-up page with every value of the session: the brief's five parts equal session.json's “given” (the settings in the same order too), the flags equal its flags ({f['flags']}), the policy is {f['policy']}; no value is marked as changed: “{f['state'][:70]}”")
    sb = await pg.evaluate(BLOCKS)
    say(P, [q[:3] for q in sb] == [q[:3] for q in bl] and all(q[3] and len(q[3]) > 20 for q in sb), f"the set-up page has the same seven blocks: the same headings, in the same order, each built from the same piece ({[q[2] for q in sb]}); here each says in one sentence what it is for (e.g. “{sb[1][3]}”)")
    await go(pg, sid); strip = await pg.evaluate("() => [...document.querySelectorAll('#ev-head .hf:not(.hf-level):not(.hf-walk)')].map(f => [f.dataset.f, f.querySelector('span').textContent.trim()])"); await pg.go_back(); await pg.wait_for_function("() => document.querySelector('#new-setup #be-start')", timeout=60000); await pg.wait_for_timeout(600); f = await pg.evaluate(FORM)
    say(P, [q[:2] for q in f['strip']] == strip and dict((q[0], q[2]) for q in f['strip'])['sims'] == f"0 of {g['limits']['simulations']}", f"above Start stands the header strip the session's page will have, the same fields in the same order: {[(q[1], q[2]) for q in f['strip']]}")
    # a changed value is marked; a value that is not allowed is refused as it is typed
    await pg.fill('#be-who input[data-f="set.weightUdp.max"]', '2'); await pg.wait_for_timeout(250)
    r1 = await pg.evaluate("() => ({ why: [...document.querySelectorAll('#be-who .be-why')].filter(x => x.textContent).map(x => [x.dataset.why, x.textContent]), bad: document.querySelector('#be-who input[data-f=\"set.weightUdp.max\"]').classList.contains('bad'), start_off: document.getElementById('be-start').disabled, state: document.getElementById('be-state').textContent.trim() })")
    await pg.fill('#be-who input[data-f="set.weightUdp.max"]', '0.9'); await pg.wait_for_timeout(250); f2 = await pg.evaluate(FORM)
    r2 = await pg.evaluate("() => ({ why: [...document.querySelectorAll('#new-setup .be-why')].filter(x => x.textContent).length, chg: [...document.querySelectorAll('#new-setup input.chg')].map(x => x.dataset.f) })")
    say(P, r1['why'] == [['set.weightUdp.max', 'from 0.05 to 0.95']] and r1['bad'] and r1['start_off'] and r2['why'] == 0 and not f2['start_off'], f"a value that is not allowed is refused as it is typed, with the reason in words: the ratio's upper end typed as 2 gives “{r1['why'][0][1] if r1['why'] else None}” beside the field and Start cannot be pressed (“{r1['state'][:60]}”); typed as 0.9 the line goes")
    say(P, f2['changed'] == 1 and set(r2['chg']) == {'set.weightUdp.max'} and f2['brief']['knobs']['weightUdp']['max'] == 0.9, f"a changed value is marked: {f2['changed']} value changed, the field {sorted(set(r2['chg']))} has the mark")
    await pg.fill('#be-who input[data-f="set.weightUdp.max"]', str(g['knobs']['weightUdp']['max'])); await pg.wait_for_timeout(200)
    dflt = await pg.evaluate("() => ({ flags: [...document.querySelectorAll('#be-flags > div')].map(d => d.textContent.replace(/\\s+/g, ' ').trim()), limits: [...document.querySelectorAll('[data-block=limits] small')].map(x => x.textContent), policy: document.getElementById('be-policy').textContent.replace(/\\s+/g, ' '), list: document.getElementById('be-list').textContent })")
    say(P, all('default' in x for x in dflt['flags']) and len(dflt['flags']) == 5 and all('default' in x for x in dflt['limits']) and 'the default' in dflt['policy'] and dflt['list'] == 'all settings as a list', f"every default is shown: the five flags ({[x[-28:] for x in dflt['flags']]}), the limits, the policy (“share … the default”)")
    await pg.click('#be-list'); await pg.wait_for_timeout(300); rows = await pg.evaluate("() => [...document.querySelectorAll('#be-rows .be-row')].map(r => r.dataset.row)"); await pg.click('#be-list')
    say(P, len(rows) == (11 + sum(f"k: '{k}'" in (ROOT / 'viewer' / 'brief_editor.js').read_text() for k in ('tcpInitCwnd', 'tcpBufBytes', 'devQueuePkts'))) and 'weightUdp' in rows, f"the older form stays reachable as “all settings as a list”: {len(rows)} rows, one per setting, each with the line the AI reads")
    # saved unchanged: a brief equal to the session's
    f3 = await pg.evaluate(FORM); new_id = f3['id']; await pg.click('#be-save'); await pg.wait_for_function("() => /Saved as|Not saved/.test((document.getElementById('be-msg') || {}).textContent || '')", timeout=30000); msg = await pg.evaluate("() => document.getElementById('be-msg').textContent.trim()")
    file = ROOT / 'briefs' / f'{new_id}.json'; saved = json.loads(file.read_text()) if file.is_file() else {}
    say(P, 'Saved as' in msg and {k: saved.get(k) for k in mine} == mine and json.dumps({k: saved.get(k) for k in mine}) == json.dumps(mine) and saved.get('id') == new_id != g['id'] and 'task' not in saved, f"saved unchanged, under a new name ({new_id}; the session's brief {g['id']} is not overwritten), it gives a brief equal to the session's in those five parts, with no task of its own (the harness writes it): “{msg}”")
    # ---- a session started from the set-up page shows on its page exactly the values that were entered
    await pg.goto(f'{BASE}?tab=new'); await pg.wait_for_function("() => document.querySelector('#new-setup #be-start') && document.querySelector('#be-pic svg.sy')", timeout=60000); await pg.wait_for_timeout(500)
    await pg.select_option('#be-open', 'two-hosts-udp-demand'); await pg.wait_for_timeout(1200)
    await pg.fill('#be-who input[data-f="set.weightUdp.step"]', '0.01'); await pg.fill('#be-who input[data-f="set.queuePkts.max"]', '500'); await pg.click('#be-who tr[data-row=seed] button[data-to=fixed]'); await pg.wait_for_timeout(200); await pg.fill('#be-who input[data-f="set.seed.value"]', '7')
    await pg.fill('#new-setup input[data-f=sims]', '6'); await pg.fill('#new-setup input[data-f=per]', '3'); await pg.fill('#new-setup input[data-f=tolerance]', '2'); await pg.check('#be-policy input[value=cap]')
    await pg.fill('#be-flags input[data-k=temp]', '0.5'); await pg.select_option('#be-flags select[data-k=draft]', 'off'); await pg.fill('#be-flags input[data-k=tokens]', '4000')
    sname = f"setup-{__import__('time').strftime('%H%M%S')}"; await pg.fill('#new-setup input[data-f=id]', sname); await pg.wait_for_timeout(300); entered = await pg.evaluate(FORM)
    say(P, not entered['start_off'] and entered['start'] == f'Save as {sname} and start the session' and entered['changed'] == 11, f"a set-up written on the page ({entered['changed']} values changed from two-hosts-udp-demand: a ratio step, a queue range, a fixed seed, the limits, a tolerance, the policy, three flags: the budget is no field since 2026-11-22); the button reads “{entered['start']}”")
    await pg.click('#be-start'); await pg.wait_for_function("() => EV.s.view === 'session' && EV.M && document.getElementById('st-blocks')", timeout=120000); new_sid = await pg.evaluate("() => EV.M.id")
    for _ in range(240):  # until its baseline has run: the policy of a session is recorded with its first simulation
        op = ROOT / 'checks/operator.jsonl'
        if (ROOT / 'sessions' / new_sid / 'session.json').is_file() and op.is_file() and f'"{new_sid}"' in op.read_text(): break
        await pg.wait_for_timeout(500)
    await pg.evaluate("(s) => EV.post('../api/stop', { session: s }).catch(() => null)", new_sid); await pg.wait_for_timeout(1500)
    m2 = json.loads((ROOT / 'sessions' / new_sid / 'session.json').read_text()); await go(pg, new_sid); await pg.evaluate("() => { EV.s.op = true; EV.s.full = true; EV.draw(); }"); await pg.wait_for_timeout(500)
    shown = await pg.evaluate("""() => { const t = el => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null); return { who: Object.fromEntries([...document.querySelectorAll('#st-blocks .st-who tr[data-k]')].map(r => [r.dataset.k, [r.dataset.set, ...[...r.cells].slice(1).map(c => t(c))]])), groups: [...document.querySelectorAll('#st-blocks .st-who tr.st-grp')].map(r => [r.dataset.by, t(r)]), aim: t(document.querySelector('#st-blocks [data-block=aim]')), limits: t(document.querySelector('#st-blocks [data-block=limits]')),
      kept: t(document.getElementById('st-kept')), flags: Object.fromEntries([...document.querySelectorAll('#st-blocks .st-flags tr')].map(r => [r.dataset.flag, t(r.cells[1])])), strip: t(document.querySelector('#ev-head [data-f=brief] b')), exact: JSON.parse(document.getElementById('st-given').textContent) }; }""")
    eb = dict(entered['brief']); eb['description'] = re.sub(r'\{(\w+)\}', lambda m: str(eb['system'][m.group(1)]), eb['description']); w = shown['who']  # the harness fills the {names} of the description from the fixed settings
    ok = (m2['brief'] == sname and {k: m2['given'][k] for k in mine} == eb and m2['flags'] == {'budget': m2['given']['limits']['simulations'], 'draft': 'off', 'max_tokens': 4000, 'temperature': 0.5, 'baseline': 'on', 'judge': 'on'}
          and w['weightUdp'] == ['knob', '0.05', '0.95 in steps of 0.01', '0.5'] and w['queuePkts'] == ['knob', '4 packets', '500 packets', '100 packets'] and w['seed'] == ['fixed', '7'] and w['udpRate'] == ['fixed', '300 Mbps']
          and 'largest TCP goodput, while UDP loss <= 1 %' in shown['aim'] and 'Tolerance 2 %' in shown['aim'] and 'set by the operator' in shown['aim'] and '6 simulations in all' in shown['limits'] and '3 in one turn' in shown['limits']
          and 'scheduling policy: cap' in shown['kept'] and shown['flags']['budget'] == str(m2['given']['limits']['simulations']) and shown['flags']['draft'] == 'off' and shown['flags']['max_tokens'] == '4000' and shown['flags']['temperature'] == '0.5' and shown['flags']['baseline'] == 'on' and shown['strip'] == sname and {k: shown['exact'][k] for k in mine} == eb)
    say(P, ok, f"session {new_sid}, started from the set-up page (and stopped once its baseline had run): its session.json holds exactly the brief and the flags entered, and its page shows them: ratio “{' | '.join(w['weightUdp'][1:])}” (lowest, highest, starts at), queue length “{' | '.join(w['queuePkts'][1:])}”, seed fixed at {w['seed'][1]}, the aim “{shown['aim'][11:90]}…”, “{shown['limits'][-60:]}”, “{shown['kept'][:28]}”, the flags {shown['flags']}")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

FIND = r"""() => { const t = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : null), col = el => (el ? getComputedStyle(el).color : null);
  const i = document.createElement('i'); document.getElementById('s-find').appendChild(i); const C = v => { i.style.color = `var(${v})`; return getComputedStyle(i).color; }, crit = C('--critical'), warn = C('--warning'); i.remove();
  return { heads: [...document.querySelectorAll('#s-find thead th')].map(t), more: t(document.getElementById('find-more')),
    rows: [...document.querySelectorAll('#s-find tbody tr')].map(r => ({ id: r.dataset.id, hyp: t(r.querySelector('.fh')), q: t(r.querySelector('.fq')).replace(/^H\d+/, '').trim(), cut: !!r.querySelector('.fq .lc2'), lines: r.querySelector('.fq .lc2') ? Math.round(r.querySelector('.fq .lc2').clientHeight / parseFloat(getComputedStyle(r.querySelector('.fq .lc2')).lineHeight)) : null,
      out: t(r.querySelector('.fo')), void: !!r.querySelector('.fo [data-void]'), measured: t(r.querySelector('.fm')), measured_exact: (r.querySelector('.fm .rr') || {}).title || null, led: [...r.querySelectorAll('.fl a')].map(a => a.dataset.id), turned: !!r.querySelector('.fturn'),
      warn: [...r.querySelectorAll('.fm *, .fm')].some(x => [crit, warn].includes(col(x))) })) }; }"""
FIND_REPLAY = r"""async () => { const M = EV.M, n = M.steps.length, bad = [], st = id => M.recStep[id] ?? 0, read = el => !!el && !el.closest('.later') && getComputedStyle(el).visibility !== 'hidden' && el.textContent.trim() !== ''; let rows = 0; EV.s.sel = null;
  for (let k = 0; k < n; k++) { EV.s.step = k; EV.draw(); if (k % 20 === 19) await new Promise(r => setTimeout(r, 0));
    const later = Object.keys(M.recStep).filter(id => st(id) > k), more = document.getElementById('find-more'), recorded = M.tests.filter(T => st(T.exp) <= k).length;
    if (more && !new RegExp('\\b' + recorded + ' tests in all').test(more.textContent)) bad.push({ k, what: 'the line under the table counts tests recorded later', says: more.textContent.trim(), recorded });
    document.querySelectorAll('#s-find tbody tr').forEach(r => { rows++; const T = M.testById[r.dataset.id], fol = EV.followers(T), last = k === n - 1;
      const want = { row: st(T.exp) <= k, outcome: T.check && T.check.void ? st(T.check.id) <= k : T.verdict ? st(T.verdict.id) <= k : last, measured: T.check ? st(T.check.id) <= k : last }, O = r.querySelector('.fo > span'), Mz = r.querySelector('.fm > span');
      const got = { row: read(r.querySelector('.fq')), outcome: read(O), measured: read(Mz) };
      Object.keys(want).forEach(p => { if (want[p] !== got[p]) bad.push({ k, test: T.id, part: p, can_be_read: got[p], recorded_by_this_step: want[p] }); });
      r.querySelectorAll('.fl a').forEach(a => { const h = M.testById[a.dataset.id].hyp; if (read(a) && st(h) > k) bad.push({ k, test: T.id, what: 'a later hypothesis is named in “Led to”', id: h }); }); }); }
  EV.s.step = null; EV.draw(); return { steps: n, rows, problems: bad.length, first: bad.slice(0, 4) }; }"""
def read_words(led):
    """What "Measured" must say, built here from the ledger for the tests whose rule has the simplest form (one comparison of a rate at a label with a number): {test id: words}."""
    out = {}
    for t in tests_of(led):
        m = re.fullmatch(r'\s*(\w+_bps)@(\w+)\s*(<=|>=|<|>)\s*([\d.eE+-]+)\s*', t['rule'] or '')
        if not m or not t['check']: continue
        k, label, op, lim = m.group(1), m.group(2), m.group(3), float(m.group(4)); sim = next((q for q in led if q['type'] == 'simulation' and q.get('parent') == t['exp'] and q['body'].get('label') == label), None)
        if not sim or not sim['body'].get('metrics'): continue
        v = sim['body']['metrics'][k]; held = {'<': v < lim, '<=': v <= lim, '>': v > lim, '>=': v >= lim}[op]; word = {'<': 'under', '<=': 'at most', '>': 'over', '>=': 'at least'}[op]
        out[t['id']] = f"{float(f'{v / 1e6:.3g}'):g} Mbps, {'' if held else 'not '}{word} {lim / 1e6:g} Mbps"
    return out

async def part4(b):
    print('PART 4  what it needed to find out'); P = '4'
    sid = 's024'; led = ledger(sid); tests = tests_of(led); hy = {q['id']: q['body'] for q in led if q['type'] == 'hypothesis'}; ver = {q['body']['for']: q for q in led if q['type'] == 'verdict'}
    pg = await fresh(b, sid, store={'ev-read': '1'}); r = await pg.evaluate(FIND)
    say(P, r['heads'] == ['The hypothesis', 'Outcome', 'Measured', 'Led to'] and [x['id'] for x in r['rows']] == [t['id'] for t in tests][:9] and len(r['rows']) == 9, f"{sid}: one row per test, in the order stated ({len(r['rows'])} rows for {len(tests)} tests), with the four columns {r['heads']}")
    say(P, all(x['q'] == hy[x['hyp']]['question'] for x in r['rows']), f"the nine questions equal the records word for word (e.g. {r['rows'][0]['hyp']}: “{r['rows'][0]['q']}”)")
    say(P, all(x['out'] == ver[x['hyp']]['body']['result'] for x in r['rows'] if x['hyp'] in ver) and len([x for x in r['rows'] if x['hyp'] in ver]) == 9, f"Outcome is each hypothesis's verdict: {[x['out'] for x in r['rows']]}")
    chk = {t['id']: t['check']['body'] for t in tests if t['check']}; failed = [x for x in r['rows'] if chk[x['id']]['result'] == 'failed']
    say(P, all(x['measured'] and x['measured_exact'] == f"{chk[x['id']]['with_numbers']} : {chk[x['id']]['result']}" for x in r['rows']) and failed and not any(x['warn'] for x in r['rows']), f"Measured is the check's numbers written for reading, the exact text on hover; the {len(failed)} failed checks are in the neutral colour (e.g. “{failed[0]['measured']}”)")
    words = {}
    for s2 in ('s004', 's005', 's006', 's008', 's011', 's012', 's018'):
        await go(pg, s2); await pg.evaluate("() => { EV.s.findAll = true; EV.draw(); }"); await pg.wait_for_timeout(300); rr = await pg.evaluate(FIND); ww = read_words(ledger(s2)); words[s2] = [(k, v, next(x['measured'] for x in rr['rows'] if x['id'] == k)) for k, v in ww.items()]
    flat = [(s2, *q) for s2, qs in words.items() for q in qs]
    say(P, len(flat) >= 2 and all(q[2] == q[3] for q in flat), f"the words are the check's own numbers: for the {len(flat)} tests of seven sessions whose rule is one comparison of a rate with a number, the page's text equals the text built here from the ledger (e.g. {flat[0][0]} {flat[0][1]}: “{flat[0][3]}”)" + ('' if all(q[2] == q[3] for q in flat) else f": {[q for q in flat if q[2] != q[3]][:2]}"))
    await go(pg, 's018'); l18 = ledger('s018'); r18 = await pg.evaluate(FIND); h18 = {q['id']: q['body'] for q in l18 if q['type'] == 'hypothesis'}
    say(P, all(x['cut'] and x['lines'] <= 2 and h18[x['hyp']]['text'].startswith(x['q'][:30]) for x in r18['rows']) and 'more' in (r18['more'] or '') and len(r18['rows']) == 9, f"s018 records no questions: each row shows the hypothesis text, cut to two lines; nine rows are shown, then “{r18['more']}”")
    await pg.click('#find-more button'); await pg.wait_for_timeout(300); n18 = await pg.evaluate("() => document.querySelectorAll('#s-find tbody tr').length")
    say(P, n18 == len(tests_of(l18)), f"“n more” shows them all ({n18} rows for the {len(tests_of(l18))} tests of s018)")
    # led to: a mark for each later hypothesis that follows from the test, going to that row
    await go(pg, sid); r = await pg.evaluate(FIND); first_row = {}
    for t in tests: first_row.setdefault(t['hyp'], t['id'])
    want_led = {t['id']: sorted(first_row[h] for h, hb in hy.items() if h in first_row and t['check'] and (t['check']['id'] in (hb.get('follows_from') or []) or (ver.get(t['hyp']) and ver[t['hyp']]['id'] in (hb.get('follows_from') or [])))) for t in tests}
    got_led = {x['id']: sorted(x['led']) for x in r['rows']}; named = {k: v for k, v in want_led.items() if v}
    say(P, all(set(v) <= set(got_led[k]) for k, v in named.items()) and any(got_led.values()), f"Led to: a mark for each later hypothesis that follows from the test ({ {k: v for k, v in got_led.items() if v} }; hypotheses whose follows_from names the test's check or verdict: {named})")
    src = next(k for k, v in got_led.items() if v); dst = got_led[src][0]; await pg.evaluate("() => window.scrollTo(0, document.getElementById('s-find').getBoundingClientRect().top + scrollY - 70)")
    await pg.click(f'#s-find tr[data-id="{src}"] .fl a'); await pg.wait_for_timeout(250); fl = await pg.evaluate("(id) => { const r = document.getElementById('fr-' + id), b = r.getBoundingClientRect(); return { flash: r.classList.contains('flash'), in_view: b.top >= 0 && b.bottom <= innerHeight }; }", dst)
    say(P, fl['flash'] and fl['in_view'], f"a click on the mark of {src} goes to the row of {dst}, which is in view and lit for a moment")
    # each row opens its card
    opened = []
    for x in r['rows']:
        await pg.evaluate("() => window.scrollTo(0, document.getElementById('s-find').getBoundingClientRect().top + scrollY - 70)"); await pg.click(f'#s-find tr[data-id="{x["id"]}"] td.fo'); await pg.wait_for_timeout(250)
        opened.append(await pg.evaluate("(id) => { const c = [...document.querySelectorAll('#s-notebook .nb-card')].find(q => q.dataset.id === id), b = c.getBoundingClientRect(); return c.classList.contains('sel') && b.top >= 0 && b.top < innerHeight && EV.s.sel.t === 'test' && EV.s.sel.id === id; }", x['id']))
    say(P, all(opened) and len(opened) == 9, f"each of the nine rows opens its notebook card: selected and in view ({sum(opened)} of {len(opened)})")
    # s014: its void tests marked
    await go(pg, 's014'); await pg.evaluate("() => { EV.s.findAll = true; EV.draw(); }"); await pg.wait_for_timeout(400); r14 = await pg.evaluate(FIND); l14 = ledger('s014')
    run = {(q.get('parent'), q['body'].get('label')): q['body'].get('run_id') for q in l14 if q['type'] == 'simulation'}; void = set()
    for q in l14:
        if q['type'] == 'check':
            ls = list(dict.fromkeys(re.findall(r'[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)', str(q['body'].get('decision_rule') or '')))); ids = [z for z in (run.get((q.get('parent'), l)) for l in ls) if z]
            if len(ls) >= 2 and len(set(ids)) < len(ids): void.add(q['id'])
    t14 = tests_of(l14); want_void = sorted(t['id'] for t in t14 if t['check'] and t['check']['id'] in void); got_void = sorted(x['id'] for x in r14['rows'] if x['void'])
    say(P, got_void == want_void and len(got_void) > 0 and all(x['out'].startswith('void') and x['measured'] == 'compared a simulation with itself' for x in r14['rows'] if x['void']), f"s014: its {len(got_void)} void tests are marked “void” in Outcome (the {len(want_void)} tests whose check compared a simulation with itself, counted here from the ledger), with “compared a simulation with itself” under Measured")
    # the replay
    for s in ('s024', 's014'):
        await go(pg, s); rp = await pg.evaluate(FIND_REPLAY)
        say(P, not rp['problems'], f"replay of {s}: at each of {rp['steps']} steps a row can be read from the step of its experiment, its Outcome from the step of its verdict, its Measured from the step of its check; a later row is a grey bar ({rp['rows']} rows read)" + (f": {rp['first']}" if rp['problems'] else ''))
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

PROP = r"""() => { const t = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : null), P = document.getElementById('s-proposes'), blk = k => P.querySelector(`[data-pr=${k}]`);
  const i = document.createElement('i'); P.appendChild(i); i.style.color = 'var(--warning)'; const warn = getComputedStyle(i).color; i.style.color = 'var(--critical)'; const crit = getComputedStyle(i).color; i.remove();
  const claims = el => (el ? [...el.querySelectorAll('button.claim')].map(b => ({ n: Number(b.dataset.id), role: b.dataset.role, text: t(b.querySelector('.ct')) })) : []);
  const order = k => { const out = []; if (!blk(k)) return out; [...blk(k).children].forEach(c => { if (c.classList.contains('pr-role')) out.push('role:' + c.dataset.role); else if (c.classList.contains('claims')) out.push(...[...c.querySelectorAll('button.claim')].map(b => 'claim ' + b.dataset.id)); else if (c.classList.contains('ov-when')) out.push(...[...c.querySelectorAll('h4')].map(t)); }); return out; };
  return { blocks: [...P.querySelectorAll('[data-pr]')].map(b => [b.dataset.pr, t(b.querySelector('h3')).replace(/^\d/, '')]), aim: t(blk('aim')), aim_by: blk('aim') ? [...blk('aim').querySelectorAll('.st-by')].map(x => [x.dataset.by, t(x)]) : [], goal: t(document.getElementById('ov-goal')),
    adjust: t(document.getElementById('ov-rec')), rest: t(document.getElementById('ov-def')), expected: [...document.querySelectorAll('#ov-exp-top tr')].map(r => [r.dataset.k, t(r.cells[1])]), more: t(document.getElementById('ov-exp-more')),
    diagnosis: order('diagnosis'), because: order('because'), but: order('but'), diagnosis_claims: claims(blk('diagnosis')), because_claims: claims(blk('because')), but_claims: claims(blk('but')), noroles: t(document.getElementById('pr-noroles')), holds: blk('but') ? [...blk('but').querySelectorAll('.ov-when p')].map(t) : [],
    expl_open: blk('explanation') ? blk('explanation').open : null, expl: t(document.getElementById('ov-expl')), counts: t(document.getElementById('claim-counts')), counts_data: (document.getElementById('claim-counts') || { dataset: {} }).dataset.counts,
    warn: [...P.querySelectorAll('#pr-counts *, .claims *')].filter(x => [warn, crit].includes(getComputedStyle(x).color) && !x.closest('.rs')).length, none: t(document.getElementById('ov-none')) }; }"""
def kinds_of(led):
    """How many claims of a report cite only held checks, held and failed, only failed, no check, nothing: counted from the ledger (void checks as the page counts them are left to ev_format.py)."""
    rep = next((q for q in led if q['type'] == 'report'), None); res = {q['id']: q['body'].get('result') for q in led if q['type'] == 'check'}; out = [0, 0, 0, 0, 0]
    for c in (rep['body'].get('claims') or []) if rep else []:
        cs = [res[i] for i in c.get('evidence', []) if i in res]; h, f = 'held' in cs, 'failed' in cs
        out[4 if not c.get('evidence') else 3 if not cs else 1 if h and f else 2 if f else 0 if h else 3] += 1
    return out

async def part5(b):
    print('PART 5  what it proposes, as one argument'); P = '5'
    pg = await fresh(b, 'r1', store={'ev-read': '1'}); r = await pg.evaluate(PROP); rep = next(q for q in ledger('r1') if q['type'] == 'report')['body']
    say(P, [q[0] for q in r['blocks']] == ['aim', 'adjust', 'expected', 'diagnosis', 'because', 'but', 'explanation'] and [q[1] for q in r['blocks']] == ['The aim', 'The proposed adjustment', 'The expected result', 'Its diagnosis', 'Because', 'But', 'The explanation'], f"section 5 reads in the sheet's order: {[q[1] for q in r['blocks']]}")
    roles = [c['role'] for c in rep['claims']]; n = lambda role: [f'claim {i + 1}' for i, q in enumerate(roles) if q == role]
    say(P, r['diagnosis'] == ['role:background'] + n('background') and r['because'] == ['role:supports'] + n('supports') and r['but'] == ['role:limits'] + n('limits') + ['Holds when', 'Breaks when'],
        f"r1, a scripted report with roles ({roles}): “Its diagnosis” holds the claims that say how the system behaves ({r['diagnosis']}), Because the claims that support the recommendation ({r['because']}); But holds the claims that say when it would change, then “holds when” and “breaks when” ({r['but']})")
    say(P, [c['text'] for c in r['diagnosis_claims']] + [c['text'] for c in r['because_claims']] + [c['text'] for c in r['but_claims']] == [c['text'] for c in sorted(rep['claims'], key=lambda c: ['background', 'supports', 'limits'].index(c['role']))] and r['holds'] == [rep['holds_when'], rep['breaks_when']], "each claim is the model's own sentence, and “holds when” and “breaks when” are the report's texts, word for word")
    await pg.click('#s-proposes button.claim[data-id="1"]'); await pg.wait_for_timeout(400); ev = await pg.evaluate("() => ({ on: document.querySelector('#s-proposes button.claim[data-id=\"1\"]').classList.contains('on'), pane: document.querySelector('#p-detail h2').innerText.replace(/\\s+/g, ' ').slice(0, 30), sel: EV.s.sel })")
    say(P, ev['on'] and ev['sel'] and ev['sel']['t'] == 'test' and 'Test of H1' in ev['pane'], f"a claim opens its evidence: claim 1 (it cites C1) opens “{ev['pane']}” in the detail pane")
    say(P, r['aim_by'] == [['model', 'chosen by the AI']] and rep['goal'] in r['aim'] and r['expl_open'] is False and r['expl'] == rep['explanation'], f"the aim is the one the AI states, marked “chosen by the AI” (the brief left it open); the explanation is folded")
    # s024: recorded without roles
    await go(pg, 's024'); r = await pg.evaluate(PROP); rep = next(q for q in ledger('s024') if q['type'] == 'report')['body']
    say(P, [q[1] for q in r['blocks']] == ['The aim', 'The proposed adjustment', 'The expected result', 'Its claims', 'But', 'The explanation'] and r['because'] == [f'claim {i + 1}' for i in range(len(rep['claims']))] and r['noroles'] and r['but'] == ['Holds when', 'Breaks when'],
        f"s024, recorded without roles: its {len(rep['claims'])} claims in one list, in the report's order, under “Its claims” (“{r['noroles']}”); But holds “holds when” and “breaks when”")
    say(P, r['adjust'] == 'ratio 0.5 → 0.497' and r['rest'].startswith('everything else unchanged'), f"s024, the proposed adjustment: “{r['adjust']}”; “{r['rest']}”")
    # s006: the sheet's line
    await go(pg, 's006'); r = await pg.evaluate(PROP); l6 = ledger('s006'); rep = next(q for q in l6 if q['type'] == 'report')['body']; g6 = json.loads((ROOT / 'sessions/s006/session.json').read_text())['given']
    say(P, r['adjust'] == 'ratio 0.5 → 0.30295, queue length 100 → 200', f"s006, the adjustment line reads “{r['adjust']}” (the report recommends {rep['recommendation']}; the brief's defaults: ratio {g6['knobs']['weightUdp']['default']}, queue length {g6['knobs']['queuePkts']['default']})")
    rest = [k for k, v in rep['recommendation'].items() if v == g6['knobs'][k]['default']]
    say(P, r['rest'].startswith('everything else unchanged') and all(w in r['rest'] for w in ('TCP type Cubic', 'measured time 10 s', 'seed 1')) and len(rest) == 3, f"and one line for the rest: “{r['rest']}” (the {len(rest)} knobs the report leaves at the brief's default: {rest})")
    target = g6['goal']['target']['measure']; conds = [c.split()[0] for c in g6['goal']['conditions']]
    say(P, [q[0] for q in r['expected']] == [target] + conds and r['more'] == f"{len(rep['expected']) - 1 - len(conds) - len([k for k in rep['expected'] if k in ('link_rate_bps', 'weight_udp')])} more in the final report" and r['aim_by'] == [['operator', 'set by the operator']] and 'largest TCP goodput, while UDP loss <= 1 %' in r['aim'],
        f"s006: the aim “{r['aim'][:60]}…” is marked “set by the operator”; the expected result shows the target's measure and those the conditions name ({r['expected']}), then “{r['more']}”")
    # the counts: worded neutrally, none in the warning colour
    words = ['cite only checks that held', 'cite checks that held and failed', 'cite only checks that failed', 'cite no check', 'cite nothing']; bad = []
    for s2 in ('s004', 's006', 's011', 's014', 's018', 's024', 'r1'):
        await go(pg, s2); q = await pg.evaluate(PROP); k = kinds_of(ledger(s2)); want = f"{sum(k)} claim{'' if sum(k) == 1 else 's'} · " + ' · '.join(f'{n} {w}' for n, w in zip(k, words))
        if s2 == 's014': want = q['counts']  # its void checks change the kinds (ev_format.py counts them); here only the wording is read
        if q['counts'] != want or q['warn'] or not all(w in q['counts'] for w in words): bad.append((s2, q['counts'], want, q['warn']))
    say(P, not bad, f"the counts of claims are worded neutrally and none is in the warning colour, on seven sessions (e.g. s006: “{(await pg.evaluate(PROP))['counts'] if False else 'see below'}”)" + (f": {bad[:2]}" if bad else ''))
    await go(pg, 's006'); print(f"     s006: “{(await pg.evaluate(PROP))['counts']}”")
    none = await pg.evaluate("""() => { const M = EV.M, c = M.claims[0], keep = [c.evidence, c.cites, c.kind]; c.evidence = []; c.cites = []; c.kind = 'none'; EV.draw(); const b = document.querySelector('#s-proposes button.claim[data-id="1"] .cl-ev'), i = document.createElement('i'); document.body.appendChild(i); i.style.color = 'var(--warning)'; const w = getComputedStyle(i).color; i.remove();
      const out = { says: b.textContent.trim(), warn: [...b.querySelectorAll('*')].some(x => getComputedStyle(x).color === w), line: document.getElementById('claim-counts').textContent.split(' · ').pop() }; [c.evidence, c.cites, c.kind] = keep; EV.draw(); return out; }""")
    say(P, none == {'says': 'cites nothing', 'warn': False, 'line': '1 cite nothing'}, f"a claim with no evidence (scripted on the page) says “{none['says']}” in the ordinary colour, and the line counts it as “{none['line']}”")
    await pg.evaluate("() => { localStorage.setItem('ev-full', '1'); EV.s.full = true; EV.draw(); }"); full = (await pg.evaluate(PROP))['expl_open']; await pg.evaluate("() => { localStorage.setItem('ev-full', '0'); EV.s.full = false; EV.draw(); }")
    say(P, full is True, "Full opens the explanation")
    await go(pg, 's007'); q = await pg.evaluate(PROP)
    say(P, q['none'] and q['none'].startswith('No final report.') and not q['blocks'], f"s007: “{q['none']}”")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

RS = r"""() => { const t = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : null), C = document.getElementById('s-research'); if (!C) return null;
  const i = document.createElement('i'); C.appendChild(i); i.style.color = 'var(--warning)'; const warn = getComputedStyle(i).color; i.style.color = 'var(--critical)'; const crit = getComputedStyle(i).color; i.remove();
  const calc = Object.fromEntries(EV.research(EV.M, EV.seen, EV.s.op ? { row: EV.files.row, random: null } : null).map(q => [q.key, { n: q.n, of: q.of, word: q.word, held: q.held, failed: q.failed, void: q.void, returned: q.returned, varied: q.varied }]));
  return { small: t(C.querySelector('h2 small')), heads: [...C.querySelectorAll('thead th')].map(t), calc,
    rows: [...C.querySelectorAll('tbody tr')].map(r => ({ key: r.dataset.line, does: t(r.querySelector('.rs-does')), rule: r.querySelector('.rs-does').title, text: t(r.querySelector('.rs-text')), word: t(r.querySelector('.rs-w')), n: r.dataset.n == null ? null : Number(r.dataset.n), of: r.dataset.of == null ? null : Number(r.dataset.of),
      op: r.dataset.by === 'operator', links: [...r.querySelectorAll('.rs-links a')].map(a => [a.dataset.act, a.dataset.t || '', a.dataset.id]), review: !!r.querySelector('.review input[type=checkbox]'), warn: [...r.querySelectorAll('.rs-w, .rs-text, .rs-text *')].some(x => [warn, crit].includes(getComputedStyle(x).color)) })),
    words: t(C) }; }"""

async def part6(b):
    print('PART 6  how it worked as a researcher'); P = '6'; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import research_recount as RR
    sid = 's024'; pg = await fresh(b, sid, store={'ev-read': '1'}); r = await pg.evaluate(RS); want = RR.recount(ROOT, sid); rows = {q['key']: q for q in r['rows']}; c = r['calc']
    say(P, [q['does'] for q in r['rows']] == ['States each hypothesis in plain words', 'Commits to a prediction first', 'Makes predictions that could fail', 'Accepts a result against its expectation', 'Changes course because of evidence', 'Looks beyond the obvious setting', 'Does not repeat itself', 'States the limits of its answer', 'Supports each claim']
        and r['small'] == 'counted by the page from the records; for a person to judge' and all(q['rule'] and q['review'] for q in r['rows']), f"{sid}: one card with the sheet's nine lines, its small heading “{r['small']}”; each line has its rule on hover and a reviewer's tick and note")
    eq = {'question': (rows['question']['n'], rows['question']['of']) == (want['question']['n'], want['question']['of']), 'first': (rows['first']['n'], rows['first']['of']) == (want['first']['n'], want['first']['of']),
          'rival': (rows['rival']['n'], rows['rival']['of'], c['rival']['held'], c['rival']['failed'], c['rival']['void']) == (want['rival']['n'], want['rival']['of'], want['rival']['held'], want['rival']['failed'], want['rival']['void']),
          'accepts': (rows['accepts']['n'], rows['accepts']['of']) == (want['accepts']['n'], want['accepts']['of']), 'course': rows['course']['n'] == want['course']['n'], 'beyond': (rows['beyond']['n'], rows['beyond']['of'], c['beyond']['varied']) == (want['beyond']['n'], want['beyond']['of'], want['beyond']['varied']),
          'repeat': (c['repeat']['void'], c['repeat']['returned']) == (want['repeat']['void'], want['repeat']['returned']), 'limits': (rows['limits']['n'], rows['limits']['of']) == (want['limits']['n'], want['limits']['of']), 'claims': (rows['claims']['n'], rows['claims']['of']) == (want['claims']['n'], want['claims']['of'])}
    say(P, all(eq.values()), f"{sid}: every count equals the recount made by research_recount.py from the ledger alone ({sum(eq.values())} of 9 lines)" + ('' if all(eq.values()) else f": differ {[k for k, v in eq.items() if not v]}"))
    for q in r['rows']: print(f"     {q['does']:42} {q['word']:8} {q['text']}")
    print(f"     research_recount.py {sid}: {json.dumps(want)}")
    say(P, all(q['word'] in ('present', 'partly', 'absent', 'not recorded', 'not applicable') for q in r['rows']) and not any(q['warn'] for q in r['rows']) and 'overall' not in r['words'].replace('no overall verdict', '') and not re.search(r'\bscore\b|\bgrade\b|\bpass(ed)?\b', r['words']),
        f"each line has a word ({sorted({q['word'] for q in r['rows']})}); “partly” and “absent” are in the neutral colour; the card states no overall verdict")
    # what a click opens
    say(P, rows['question']['links'] == [['goto', '', 's-find']] and rows['limits']['links'] == [['goto', '', 's-proposes']] and rows['claims']['links'] == [['goto', '', 's-proposes']] and rows['beyond']['links'] == [['goto', '', 's-knob|knob']]
        and sorted(q[2] for q in rows['rival']['links']) == sorted(k for k, v in want['accepts']['judged']) and rows['first']['links'][0][:2] == ['open', 'test'] and [q[2] for q in rows['course']['links']] == want['course']['from'],
        f"each line links to its evidence: section 3; the first test's order; the tests that failed {[q[2] for q in rows['rival']['links']]}; the hypotheses that follow {[q[2] for q in rows['course']['links']]}; the simulations along each setting; section 5")
    await pg.click('#s-research tr[data-line=first] .rs-links a'); await pg.wait_for_timeout(400); o = await pg.evaluate("() => { const p = document.getElementById('t-order'); return p ? { text: p.textContent.replace(/\\s+/g, ' ').trim(), rule: p.dataset.rule, first: p.dataset.first, before: p.dataset.before } : null; }")
    l24 = ledger(sid); x1 = next(q for q in l24 if q['type'] == 'experiment' and q.get('by') != 'harness')
    say(P, o and o['rule'] == x1['ts'] and o['first'] >= o['rule'] and o['before'] == '1' and 'the decision rule was recorded at' in o['text'], f"“Commits to a prediction first” opens the first test, whose order line reads “{o and o['text'][:120]}” (the ledger: {x1['id']} recorded {x1['ts']})")
    await pg.click('#s-research tr[data-line=beyond] .rs-links a'); await pg.wait_for_timeout(400); kv = await pg.evaluate("() => !!document.getElementById('s-knob')")
    say(P, kv, "“Looks beyond the obvious setting” opens the view of the simulations along one setting")
    # a reviewer's tick and note on a line, stored with the review
    await pg.evaluate("() => document.getElementById('s-research').scrollIntoView()"); await pg.check('#s-research tr[data-line=first] .review input[type=checkbox]'); await pg.wait_for_timeout(500)
    await pg.fill('#s-research tr[data-line=first] .review input[type=text]', 'the baseline was known'); await pg.press('#s-research tr[data-line=first] .review input[type=text]', 'Tab'); await pg.wait_for_timeout(700)
    rv = ROOT / 'checks/reviews' / f'{sid}.json'; marks = json.loads(rv.read_text()) if rv.is_file() else {}
    await go(pg, sid); kept = await pg.evaluate("() => { const r = document.querySelector('#s-research tr[data-line=first] .review'); return [r.querySelector('input[type=checkbox]').checked, r.querySelector('input[type=text]').value]; }")
    say(P, marks.get('rs:first', {}).get('tick') is True and marks['rs:first'].get('note') == 'the baseline was known' and kept == [True, 'the baseline was known'], f"a reviewer's tick and note on a line are stored with the review (checks/reviews/{sid}.json, item rs:first: {marks.get('rs:first')}) and are there after a reload")
    await pg.evaluate("(s) => fetch('../api/review', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session: s, item: 'rs:first', tick: false, note: '' }) })", sid); await pg.wait_for_timeout(400)
    # s014: its void tests; s006: fields that were not recorded, and the operator's lines
    await go(pg, 's014'); r14 = await pg.evaluate(RS); w14 = RR.recount(ROOT, 's014'); rep = next(q for q in r14['rows'] if q['key'] == 'repeat')
    say(P, r14['calc']['repeat']['void'] == w14['repeat']['void'] == 44 and rep['text'].startswith('44 void tests') and rep['word'] == 'partly' and len([q for q in rep['links'] if q[1] == 'test']) >= 6, f"s014, “Does not repeat itself”: “{rep['text']}” ({rep['word']}; the recount: {w14['repeat']}), with links to the void tests")
    await go(pg, 's006'); r6 = await pg.evaluate(RS); w6 = RR.recount(ROOT, 's006'); k6 = {q['key']: q for q in r6['rows']}
    say(P, k6['question']['word'] == 'not recorded' and k6['course']['word'] == 'not recorded' and w6['question'] == {'word': 'not recorded'} and (k6['first']['n'], k6['first']['of']) == (w6['first']['n'], w6['first']['of']) and not any(q['op'] for q in r6['rows']) and len(r6['rows']) == 9,
        f"s006, recorded before hypotheses had a question or said what they follow from: those two lines say “{k6['question']['text'][:40]}…”; with the operator columns off there are {len(r6['rows'])} lines and no operator line")
    await pg.evaluate("() => { EV.s.op = true; EV.draw(); }"); await pg.wait_for_function("() => { const r = document.querySelector('#s-research tr[data-line=random] .rs-text'); return r && !/reading the sweep/.test(r.textContent); }", timeout=60000); await pg.wait_for_timeout(300); r6o = await pg.evaluate(RS); ops = [q for q in r6o['rows'] if q['op']]
    best = await pg.evaluate("() => { EV.s.closer.best = true; EV.draw(); return new Promise(ok => setTimeout(() => ok((document.getElementById('rnd-says') || {}).textContent || null), 600)); }")
    pol6 = next(x for x in json.loads(await pg.evaluate("() => fetch('../api/status').then(r => r.text())"))['sessions'] if x['id'] == 's006')['policy']
    say(P, [q['key'] for q in ops] == ['policy', 'random'] and [q['does'] for q in ops] == ['Identified the scheduling policy', 'Against choosing at random'] and f'the policy was {pol6}' in ops[0]['text'] and best and ops[1]['text'].replace(' ', '') == best.replace(' ', '').strip(),
        f"s006 with the operator columns on: two more lines, “{ops[0]['does']}” (“{ops[0]['text'][:90]}”) and “{ops[1]['does']}”, which is the sentence the best-so-far chart computes (“{ops[1]['text'][:80]}…”)")
    await pg.evaluate("() => { EV.s.op = false; EV.draw(); }"); await go(pg, 's024'); await pg.evaluate("() => { EV.s.op = true; EV.draw(); }"); await pg.wait_for_timeout(400); r24o = await pg.evaluate(RS); o24 = {q['key']: q for q in r24o['rows']}
    say(P, o24['random']['word'] == 'not applicable' and 'not applicable' in o24['random']['text'] and 'H1' in o24['policy']['text'], f"s024 (an open goal): “Against choosing at random” says “{o24['random']['text']}”; “Identified the scheduling policy”: “{o24['policy']['text']}”")
    await pg.evaluate("() => { EV.s.op = false; EV.draw(); }")
    # Compare: the lines as columns, agreeing with each session's card
    cards = {}
    for s2 in ('s020', 's024'):
        await go(pg, s2); q = await pg.evaluate(RS); cards[s2] = {x['key']: [x['word'], x['n'], x['of']] for x in q['rows']}
    await pg.goto(f'{BASE}?tab=compare&brief=two-hosts-open'); await pg.wait_for_function("() => typeof EV !== 'undefined' && EV.st && document.querySelector('input[data-ch=tick]')", timeout=60000)
    for s2 in ('s020', 's024'): await pg.evaluate("(s) => { const el = document.querySelector(`input[data-ch=tick][data-id=${s}]`); if (!el.checked) el.click(); }", s2); await pg.wait_for_timeout(300)
    await pg.wait_for_function("() => document.querySelectorAll('#cmp-research tbody tr').length === 2", timeout=60000)
    cmp = await pg.evaluate("() => ({ heads: [...document.querySelectorAll('#cmp-research thead th')].map(x => x.textContent.trim()), rows: Object.fromEntries([...document.querySelectorAll('#cmp-research tbody tr')].map(r => [r.dataset.s, Object.fromEntries([...r.querySelectorAll('td[data-line]')].map(c => [c.dataset.line, [c.dataset.word, c.dataset.n == null ? null : Number(c.dataset.n), c.dataset.of == null ? null : Number(c.dataset.of)]]))])) })")
    say(P, cmp['rows'] == cards and len(cmp['heads']) == 10 and cmp['heads'][1] == 'States each hypothesis in plain words', f"the Compare tab has the nine lines as columns ({cmp['heads'][1:4]}…), one row per ticked session, and each cell agrees with that session's card (s020: {list(cmp['rows']['s020'].values())[:3]}…; s024: {list(cmp['rows']['s024'].values())[:3]}…)")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ---- Part 7: the design rules, read from the page as it is drawn
# the parts of the page that are levels 1 and 2 (the detail pane is level 3; "Looking closer" and "How to read" are neither)
L12 = "['ev-head', 'ev-legend', 's-system', 's-made', 's-find', 's-notebook', 's-proposes', 's-research', 'new-setup']"
# a text that the page did not write: the model's, the harness's or the operator's own recorded words, or a name they gave. It is marked data-own on the page.
SCAN = r"""(ids) => { const out = { fields: [], numbers: [], texts: 0, nums: 0 }, FIELD = /\b(?:[a-z]+[A-Z][A-Za-z]*|[a-z]+(?:_[a-z0-9]+)+)\b/g, UNIT = /^\s*(?:%|Mbps|Gbps|kbps|bps|µs|ms|s\b|packets?|bytes|simulations?|tests?|turns?|claims?|checks?|hypothes[ie]s|values?|settings?|knobs?|measures|steps?|lines?|rows?|of\b|to\b|left\b|more\b|used\b|in\b|×|→|:|,|\.|;|\)|$)/i;
  const own = el => !!el.closest('[data-own], input, textarea, select, option, code, pre, title, script, style, .noscan'), vis = el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden' && !el.closest('.later') && !el.closest('details:not([open]) > :not(summary)');
  ids.forEach(id => { const root = document.getElementById(id); if (!root) return; const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let t;
    while ((t = w.nextNode())) { const el = t.parentElement, s = t.textContent; if (!s.trim() || !vis(el) || own(el)) continue; out.texts++;
      (s.match(FIELD) || []).forEach(f => !/^(kB|MB|GB|kbps|Mbps|Gbps)$/.test(f) && out.fields.push({ id, field: f, at: s.trim().slice(0, 60) }));
      // numbers: at most four significant digits (a whole number is a count and is shown whole), and a decimal has its unit beside it
      const re = /(?<![A-Za-z0-9_.])(\d[\d,]*\.?\d*(?:e[+-]?\d+)?)/g; let m;
      while ((m = re.exec(s))) { const raw = m[1].replace(/,/g, ''), n = Number(raw); if (!isFinite(n)) continue; out.nums++; const digits = raw.replace(/e.*$/, '').replace('.', '').replace(/^0+/, '').length, whole = /^\d+$/.test(raw), after = s.slice(m.index + m[1].length) + (t.nextSibling && t.nextSibling.textContent ? ' ' + t.nextSibling.textContent : '');
        const exact = !!el.closest('[data-exact]');  // a setting's value, shown as it was recorded
        if (!whole && digits > 4 && !exact) out.numbers.push({ id, what: 'more than four significant digits', n: m[1], at: s.trim().slice(0, 60) });
        else if (!whole && !exact && !UNIT.test(after) && !el.closest('[data-unit]')) out.numbers.push({ id, what: 'no unit', n: m[1], at: s.trim().slice(0, 60) }); } } });
  return out; }"""
ICONS = r"""() => { const lg = [...document.querySelectorAll('#ev-legend i.sw[data-icon]')]; if (!lg.length) return null;
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true }), rgba = c => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; }, sat = c => { const mx = Math.max(c[0], c[1], c[2]), mn = Math.min(c[0], c[1], c[2]); return mx === 0 ? 0 : (mx - mn) / mx; };
  const sw = [...document.querySelectorAll('#ev i.sw:not([style])')].filter(el => el.getClientRects().length && el.closest('[data-by]')), bad = [], by = {}, kinds = new Set();
  sw.forEach(el => { const s = getComputedStyle(el), m = s.maskImage || s.webkitMaskImage || '', who = el.closest('[data-by]').dataset.by; by[who] = (by[who] || 0) + 1; kinds.add(m);
    if (!/^url\(/.test(m) || rgba(s.backgroundColor)[3] < 0.5) bad.push([who, m.slice(0, 20), s.backgroundColor, (el.parentElement.id || el.parentElement.className || '').toString().slice(0, 30)]); });
  return { legend: lg.map(el => el.dataset.icon), n: sw.length, by: Object.keys(by), kinds: kinds.size, bad }; }"""
CONTRAST7 = r"""(ids) => { const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true });
  const rgba = c => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (top, under) => { const a = top[3]; return [0, 1, 2].map(i => top[i] * a + under[i] * (1 - a)).concat(1); }, lum = c => { const [r, g, b] = c.slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const ground = el => { const stack = []; for (let q = el; q && q.nodeType === 1; q = q.parentElement) { const c = rgba(getComputedStyle(q).backgroundColor); if (c[3] > 0) stack.push(c); if (c[3] >= 1) break; } let g = rgba(getComputedStyle(document.getElementById('ev')).backgroundColor); for (let i = stack.length - 1; i >= 0; i--) g = over(stack[i], g); return g; };
  const bad = [], seen = new Set(); let n = 0;
  ids.forEach(id => { const root = document.getElementById(id); if (!root) return; const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let t;
    while ((t = w.nextNode())) { const el = t.parentElement; if (!t.textContent.trim() || !el.getClientRects().length || el.closest('svg, .later, input, textarea, select, option, details:not([open]) > :not(summary)') || getComputedStyle(el).visibility === 'hidden' || Number(getComputedStyle(el).opacity) < 1 || el.closest('button:disabled')) continue;
      const g = ground(el), f = over(rgba(getComputedStyle(el).color), g), a = lum(f), b = lum(g), r = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); n++;
      if (r < 4.5) { const k = getComputedStyle(el).color + '|' + g.map(Math.round).join(','); if (!seen.has(k)) { seen.add(k); bad.push({ id, ratio: +r.toFixed(2), color: getComputedStyle(el).color, ground: g.slice(0, 3).map(Math.round).join(','), text: t.textContent.trim().slice(0, 40), cls: el.className && String(el.className).slice(0, 30) }); } } } });
  return { n, bad }; }"""
# every chromatic colour drawn on the page: of a text, a ground, an edge, a mark's fill or stroke
COLOURS = r"""() => { const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true }), root = document.getElementById('ev');
  const rgba = c => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const sat = c => { const mx = Math.max(c[0], c[1], c[2]), mn = Math.min(c[0], c[1], c[2]); return mx === 0 ? 0 : (mx - mn) / mx; }, hue = c => { const [r, g, b] = c.map(v => v / 255), mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if (!d) return 0; const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return Math.round(((h * 60) + 360) % 360); };
  const legend = {}; document.querySelectorAll('#ev-legend [data-col]').forEach(el => { const c = rgba(getComputedStyle(el).backgroundColor); legend[el.dataset.col] = hue(c); });
  const used = {}; const note = (c, el, prop) => { const q = rgba(c); if (q[3] < 0.08 || sat(q) < 0.25) return; const h = hue(q), name = Object.keys(legend).find(k => Math.abs(legend[k] - h) <= 8 || Math.abs(legend[k] - h) >= 352); const key = name || 'hue ' + h; (used[key] = used[key] || { n: 0, known: !!name, first: (el.id || el.className && String(el.className.baseVal ?? el.className).slice(0, 30) || el.tagName) + ' ' + prop + ' ' + c }).n++; };
  root.querySelectorAll('*').forEach(el => { if (!el.getClientRects().length || el.closest('#ev-print')) return; const s = getComputedStyle(el);
    if ([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) note(s.color, el, 'color'); note(s.backgroundColor, el, 'background');
    ['Top', 'Left', 'Right', 'Bottom'].forEach(k => { if (parseFloat(s['border' + k + 'Width']) > 0 && s['border' + k + 'Style'] !== 'none') note(s['border' + k + 'Color'], el, 'border'); });
    if (el instanceof SVGElement && !(el instanceof SVGSVGElement)) { if (s.fill && s.fill !== 'none') note(s.fill, el, 'fill'); if (s.stroke && s.stroke !== 'none' && parseFloat(s.strokeWidth) > 0) note(s.stroke, el, 'stroke'); }
    if (s.boxShadow && s.boxShadow !== 'none') { const m = s.boxShadow.match(/rgba?\([^)]+\)|color\([^)]+\)/g); (m || []).forEach(c => note(c, el, 'shadow')); } });
  return { legend, used }; }"""

async def part7(b):
    print('PART 7  design rules, for both pages'); P = '7'; L = json.loads(L12.replace("'", '"'))
    for scheme in ('light', 'dark'):
        pg = await fresh(b, 's024', store={'ev-read': '1'}, scheme=scheme)
        for sid in ('s024', 's006', 's014', 'setup'):
            if sid == 'setup': await pg.goto(f'{BASE}?tab=new&from=s024'); await pg.wait_for_function("() => document.querySelector('#new-setup #be-start') && document.querySelector('#be-pic svg.sy')", timeout=60000); await pg.wait_for_timeout(500)
            elif sid != 's024' or scheme == 'dark': await go(pg, sid)
            name = 'the set-up page' if sid == 'setup' else sid
            r = await pg.evaluate(SCAN, L)
            say(P, not r['fields'], f"{name}, {scheme}: no field name stands as a label at levels 1 and 2 ({r['texts']} texts of the page read; the model's, the harness's and the operator's own recorded words are not the page's labels)" + (f": {len(r['fields'])} found, e.g. {r['fields'][:4]}" if r['fields'] else ''))
            say(P, not r['numbers'], f"{name}, {scheme}: no number at levels 1 and 2 has more than four significant digits or stands without a unit ({r['nums']} numbers read; a whole number is a count, a setting's value is shown as recorded)" + (f": {len(r['numbers'])} found, e.g. {r['numbers'][:4]}" if r['numbers'] else ''))
            c = await pg.evaluate(CONTRAST7, L)
            if sid != 'setup':  # the same with an item selected, and with the pointer on items of each kind
                await pg.evaluate("() => { const T = EV.M.tests[0]; if (T) EV.s.sel = { t: 'test', id: T.id }; if (EV.M.claims.length) EV.s.claim = 1; EV.draw(); }"); await pg.wait_for_timeout(250); c2 = await pg.evaluate(CONTRAST7, L + ['p-detail']); c['n'] += c2['n']; c['bad'] += [dict(q, state='selected') for q in c2['bad']]
                for sel in ('#s-find tbody tr', '#s-notebook .nb-card', '#s-notebook .nb-head', '#s-proposes button.claim', '#s-made a.gm', '#s-research tbody tr', '#ev-head [data-act=level]:not(.on)', '#st-more [data-act=setall]'):
                    el = await pg.query_selector(sel)
                    if not el: continue
                    await el.scroll_into_view_if_needed(); box = await el.bounding_box()
                    if not box: continue
                    await pg.mouse.move(box['x'] + min(box['width'] / 2, 60), box['y'] + min(box['height'] / 2, 12)); await pg.wait_for_timeout(120); c3 = await pg.evaluate(CONTRAST7, L); c['n'] += c3['n']; c['bad'] += [dict(q, state='pointed at ' + sel) for q in c3['bad']]
                await pg.mouse.move(2, 2); await pg.evaluate("() => { EV.s.sel = null; EV.s.claim = null; EV.draw(); window.scrollTo(0, 0); }"); await pg.wait_for_timeout(150)
            uniq = {(q['color'], q['ground']): q for q in c['bad']}
            say(P, not uniq, f"{name}, {scheme}: contrast at least 4.5 for every text at levels 1 and 2, also with an item selected and with the pointer on items of each kind ({c['n']} texts measured)" + (f": {len(uniq)} pairs below, e.g. {list(uniq.values())[:3]}" if uniq else ''))
            col = await pg.evaluate(COLOURS); odd = {k: v for k, v in col['used'].items() if not v['known']}
            ic = await pg.evaluate(ICONS)  # null: a tree from before the icons, where who produced an item was a colour
            say(P, not odd and len(col['legend']) >= (5 if ic else 8), f"{name}, {scheme}: every colour used is named in the one legend ({sorted(k for k, v in col['used'].items() if v['known'])} of the legend's {sorted(col['legend'])})" + (f": not in the legend: {odd}" if odd else ''))
            if ic: say(P, sorted(ic['legend']) == ['harness', 'model', 'operator', 'simulator'] and ic['n'] > 0 and not ic['bad'] and ic['kinds'] == len(ic['by']), f"{name}, {scheme}: who produced an item is said by an icon: {ic['n']} icons of {ic['kinds']} kinds ({', '.join(sorted(ic['by']))}), each in its own toned-down colour (since 2026-11-15), each kind named in the legend" + (f": {ic['bad'][:3]}" if ic['bad'] else ''))
        await pg.context.close()
    # no sideways scrolling from 900 to 1,800 px
    wide = []
    for w in (900, 1000, 1100, 1200, 1340, 1500, 1800):
        pg = await fresh(b, 's024', w=w, h=1000, store={'ev-read': '1'})
        for sid in ('s024', 's006', 's014', 'setup'):
            if sid == 'setup': await pg.goto(f'{BASE}?tab=new&from=s024'); await pg.wait_for_function("() => document.querySelector('#new-setup #be-start') && document.querySelector('#be-pic svg.sy')", timeout=60000); await pg.wait_for_timeout(400)
            elif sid != 's024': await go(pg, sid)
            q = await pg.evaluate("() => { const W = innerWidth, out = [...document.querySelectorAll('#ev *')].filter(el => { const c = getComputedStyle(el); return /(auto|scroll)/.test(c.overflowX) && el.scrollWidth > el.clientWidth + 1 && el.getClientRects().length && !el.closest('details:not([open]) > :not(summary)'); }).map(el => (el.id || String(el.className).slice(0, 24)) + ' ' + el.scrollWidth + '>' + el.clientWidth); return { doc: document.documentElement.scrollWidth, W, inner: out.slice(0, 4) }; }")
            if q['doc'] > q['W'] or q['inner']: wide.append((w, sid, q['doc'], q['inner']))
        await pg.context.close()
    say(P, not wide, f"no sideways scrolling from 900 to 1,800 px: s024, s006, s014 and the set-up page at 900, 1000, 1100, 1200, 1340, 1500 and 1800 px, the page itself and every part that could scroll inside it" + (f": {wide[:5]}" if wide else ''))

def sig4(x): return f"{float(f'{x:.4g}'):g}"
def walk_wants(sid):
    """The numbers each sentence of the walk must quote, counted here from the session's files."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import research_recount as RR
    led = ledger(sid); meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); g = meta['given']; tests = tests_of(led); rep = next((q for q in led if q['type'] == 'report'), None)
    run = {(q.get('parent'), q['body'].get('label')): q['body'] for q in led if q['type'] == 'simulation'}; void = set()
    for q in led:
        if q['type'] == 'check':
            ls = list(dict.fromkeys(re.findall(r'[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)', str(q['body'].get('decision_rule') or '')))); ids = [run[(q.get('parent'), l)].get('run_id') for l in ls if (q.get('parent'), l) in run]
            if len(ls) >= 2 and len(set(ids)) < len(ids): void.add(q['id'])
    checks = [q for q in led if q['type'] == 'check']; held = sum(1 for q in checks if q['id'] not in void and q['body'].get('result') == 'held'); failed = sum(1 for q in checks if q['id'] not in void and q['body'].get('result') == 'failed')
    want = {'s-system': [str(len(g['knobs'])), str(len(g['system'])), str(g['limits']['simulations'])],
            's-made': [str(len({q.get('turn') for q in led if (q.get('turn') or 0) > 0})), str(sum(1 for q in led if q['type'] == 'hypothesis')), str(sum(1 for q in led if q['type'] == 'simulation')), str(held), str(failed)] + ([str(len(void))] if void else []),
            's-find': [str(len(tests))]}
    # the test the walk speaks of: the first failed test a later hypothesis follows from; else the first failed; else the first checked
    rc = RR.recount(ROOT, sid); hy = [q for q in led if q['type'] == 'hypothesis']; ver = {q['body']['for']: q for q in led if q['type'] == 'verdict'}
    fl = [t for t in tests if t['check'] and t['check']['id'] not in void and t['check']['body'].get('result') == 'failed']
    follows = lambda t: any(t['check']['id'] in (h['body'].get('follows_from') or []) or (ver.get(t['hyp']) and ver[t['hyp']]['id'] in (h['body'].get('follows_from') or [])) for h in hy)
    T = next((t for t in fl if follows(t)), None) or (fl[0] if fl else next((t for t in tests if t['check']), None))
    if T:
        m = re.match(r'\s*\(*\s*(\w+)@(\w+)\s*(<=|>=|<|>)\s*([\d.eE+-]+)', T['rule']); want['s-notebook'] = [str(T['turn'])]
        if m:
            k, label, lim = m.group(1), m.group(2), float(m.group(4)); v = run[(T['exp'], label)]['metrics'][k]; f = (lambda x: sig4(x / 1e6) + ' Mbps') if k.endswith('_bps') else (lambda x: sig4(100 * x) + ' %') if k in ('udp_loss_frac', 'link_util') else sig4
            want['s-notebook'] += [f(lim), f(v)]
    if rep:
        rec = rep['body']['recommendation']; dif = [(k, v) for k, v in rec.items() if k in g['knobs'] and str(v) != str(g['knobs'][k]['default'])]; claims = rep['body'].get('claims') or []
        cited = sum(1 for c in claims if any(i in {q['id'] for q in checks} for i in c.get('evidence', [])))
        want['s-proposes'] = [f"{g['knobs'][k]['default']} → {v}" for k, v in dif] + [f'{cited} of its {len(claims)} claim']
    w = RR.words(rc); want['s-research'] = [f"{sum(1 for v in w.values() if v == 'present')} as present", f"{sum(1 for v in w.values() if v == 'partly')} as partly", f"{sum(1 for v in w.values() if v == 'absent')} as absent"]
    return want

async def part8(b):
    print('PART 8  a guided walk for a first-time reader'); P = '8'
    WALK = "() => { const b = document.getElementById('walk-box'); return b ? { i: Number(b.dataset.i), of: Number(b.dataset.of), sec: b.dataset.sec, inside: !!b.closest('#' + b.dataset.sec), say: document.getElementById('walk-say').textContent.trim(), head: b.querySelector('.walk-n').textContent.trim(), top: Math.round(document.getElementById(b.dataset.sec).getBoundingClientRect().top), box_top: Math.round(b.getBoundingClientRect().top), on: document.getElementById(b.dataset.sec).classList.contains('walk-on'), back: !b.querySelector('[data-id=\"-1\"]').disabled, next: !b.querySelector('[data-id=\"1\"]').disabled, win: innerHeight } : null; }"
    STATE = "() => ({ y: Math.round(scrollY), sel: JSON.stringify(EV.s.sel), step: EV.s.step, box: !!document.getElementById('walk-box'), on: document.querySelectorAll('.walk-on').length, level: EV.s.full, btn: document.querySelector('#ev-head [data-act=walk]').textContent })"
    for sid, n_steps in (('s024', 6), ('s018', 6), ('s007', 5)):
        pg = await fresh(b, sid, store={'ev-read': '1'}); want = walk_wants(sid); made = await pg.evaluate("() => !!document.getElementById('s-made')"); has_rep = n_steps == 6; n_steps -= 0 if made else 1  # no step for the glance while it is not drawn (since 2026-11-22)
        await pg.evaluate("() => { const T = EV.M.tests[1]; EV.s.sel = { t: 'test', id: T.id }; EV.draw(); window.scrollTo(0, 700); }"); await pg.wait_for_timeout(300); before = await pg.evaluate(STATE)
        say(P, before['btn'] == 'Walk me through this session', f"{sid}: the header strip has “{before['btn']}”") if sid == 's024' else None
        await pg.click('#ev-head [data-act=walk]'); await pg.wait_for_timeout(350); steps = []; left_ok = []
        for i in range(n_steps):
            w = await pg.evaluate(WALK); steps.append(w)
            # leave at this step: the page is as it was; then come back to the same step
            await pg.click('#walk-box [data-act=walkend]'); await pg.wait_for_timeout(250); after = await pg.evaluate(STATE); left_ok.append(after == before)
            await pg.click('#ev-head [data-act=walk]'); await pg.wait_for_timeout(250)
            for _ in range(i + 1 if i < n_steps - 1 else i): await pg.click('#walk-box [data-act=walkgo][data-id="1"]'); await pg.wait_for_timeout(200)
            if i == n_steps - 1: break
        last = await pg.evaluate(WALK)
        secs = [w['sec'] for w in steps]; exp = ['s-system'] + (['s-made'] if made else []) + ['s-find', 's-notebook'] + (['s-proposes'] if has_rep else []) + ['s-research']
        say(P, len(steps) == n_steps and secs == exp and all(w['of'] == n_steps and w['inside'] and w['on'] and 0 <= w['box_top'] < w['win'] for w in steps) and not steps[0]['back'] and steps[0]['next'] and not last['next'],
            f"{sid}: the walk has {len(steps)} steps, one per section ({'all of them' if has_rep else 'all but “what it proposes”: this session has no final report'}{'' if made else '; none for the glance, not drawn since 2026-11-22'}), each with its box at the head of its section and in view, with “back” and “next”")
        bad = {s2: (w['say'], want.get(s2)) for s2, w in zip(secs, steps) if not all(x in w['say'] for x in want.get(s2, ['?']))}
        say(P, not bad, f"{sid}: each sentence quotes numbers that equal the records (counted here from the ledger and session.json)" + (f": {bad}" if bad else ''))
        for w in steps: print(f"     {w['head']}: {w['say']}")
        say(P, all(left_ok) and len(left_ok) == n_steps, f"{sid}: it can be left at any step, and leaving it leaves the page as it was: the same place, the same open item, no box ({sum(left_ok)} of {len(left_ok)} steps tried)")
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200); esc = await pg.evaluate(STATE)
        say(P, esc == before, f"{sid}: the Escape key leaves it too") if sid == 's024' else None
        say(P, all(len(w['say'].split()) <= 25 for w in steps), f"{sid}: no sentence of the walk is longer than 25 words (the longest: {max(len(w['say'].split()) for w in steps)})")
        say(P, not pg.errs, f"{sid}: script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for part, f in (('1', part1), ('2', part2), ('3', part3), ('4', part4), ('5', part5), ('6', part6), ('7', part7), ('8', part8)):
            if part in PARTS: await f(b)
        await b.close()
    print('RESULT:', 'PASS' if not FAILED else 'FAIL ' + ' | '.join(FAILED))
asyncio.run(main())
