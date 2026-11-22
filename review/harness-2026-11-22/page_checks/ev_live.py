"""The live view of a running session (viewer/evidence_live.js): the empty places, the sentence that says where the work
is, the time, what just arrived, the quick reading. On a SCRATCH copy (EV_PORT, EV_ROOT).
Parts (name those to run; default: play times arrive ended quick layout progress tiles):
  play     a recorded session is played back as if it were running: the page is given its ledger cut after the first K
           lines, for every K, with the session marked as running. At every K the page is compared with a recount made
           here from those same lines: where the work is, the empty places of the glance by kind, the places the work
           can fill next, the rows and cards that are filled and what they hold, the researcher card's words.
  times    the time in the sentence follows the server's two times; "stated N s before its simulations came back"
           equals the records' times
  arrive   what just arrived is named and marked; the page never moves by itself: what the reader looks at stays where it stood,
           a small note under the banner says that simulations started and that a new turn began (its button goes there),
           and the pictures of the simulations that ended stay until the next experiment starts
  ended    after the end: one line that says how it ended, nothing marked as work; ended sessions opened afresh show
           their never-filled places, and no banner
  quick    the page finds new records by itself within five seconds (a HEAD request for the ledger's size)
  layout   nothing scrolls sideways at seven widths while a reply is written and while simulations run; the banner
           stays in view; the detail pane stays below it
  progress while an experiment's simulations run the banner says how many the harness has collected (the runs its index
           lists that no record holds yet); a simulation's detail shows how the simulator was started
  tiles    while an experiment's simulations run there is one tile per simulation (evidence_tiles.js): at every
           experiment of the session the page's recount of which run is whose equals the records written afterwards;
           then one experiment step by step, with the simulator's files staged as they grow: started, samples (the
           curve and the newest values are the file's), ended (the measures of metrics.json), collected
  real     a real session is started from the set-up page with the local model, followed until its second turn begins,
           then stopped: the stages seen, in order; each test's rule on the page before its result (about 5 to 10 minutes)
No draft is read: draft lines stay in the cut ledger for the page (which drops them) and are skipped here by their type.
usage:  EV_PORT=8611 EV_ROOT=<scratch>/home/project EV_SCRIPT=ev_live.py ./ev.sh [parts] [--sessions s024,s006]"""
import os, re, sys, json, time, asyncio, pathlib, email.utils, datetime
from playwright.async_api import async_playwright
PORT = os.environ.get('EV_PORT', '8611'); BASE = f"http://127.0.0.1:{PORT}/viewer/index.html"
ROOT = pathlib.Path(os.environ['EV_ROOT'])
ARGS = sys.argv[1:]; SIDS = (ARGS[ARGS.index('--sessions') + 1] if '--sessions' in ARGS else 's024,s006').split(',')
PARTS = [a for i, a in enumerate(ARGS) if not a.startswith('-') and (i == 0 or ARGS[i - 1] != '--sessions')] or ['play', 'times', 'arrive', 'ended', 'quick', 'layout', 'progress', 'tiles', 'now']
FAILED = []
def say(part, ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(f'{part}: {text[:50]}')

# ---- the records, and what they say (never a draft: a draft line is known here only by its type)
def raw_lines(sid): return [l for l in (ROOT / 'sessions' / sid / 'ledger.jsonl').read_text().splitlines() if l.strip()]
def kind(line): m = re.search(r'"type": ?"(\w+)"', line); return m.group(1) if m else ''
def recs_of(lines): return [json.loads(l) for l in lines if kind(l) not in ('draft', 'scratch')]
def labels(rule): return list(dict.fromkeys(re.findall(r'[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)', str(rule or ''))))
def tests_of(led):
    """The tests in the order stated, as the page derives them: one per decision rule, and one per hypothesis an experiment tests without a rule."""
    out = []; verdicts = {}
    for r in led:
        if r['type'] == 'verdict': verdicts[r['body']['for']] = r
    for x in [r for r in led if r['type'] == 'experiment']:
        rules = x['body'].get('decision_rules') or x['body'].get('rules') or []; nth = {}; own = [s for s in led if s['type'] == 'simulation' and s.get('parent') == x['id']]
        checks = [c for c in led if c['type'] == 'check' and c.get('parent') == x['id']]
        for r in rules:
            n = nth[r['for']] = nth.get(r['for'], 0) + 1; rule = r.get('decision_rule') or r.get('rule'); same = [c for c in checks if c['body'].get('for') == r['for']]; ls = labels(rule)
            chk = next((c for c in same if (c['body'].get('decision_rule') or c['body'].get('rule')) == rule), None) or (same[n - 1] if len(same) >= n else None)
            sims = [next((s for s in own if s['body'].get('label') == l), None) for l in ls] if ls else (own[:] if len(own) == 1 else [])
            out.append({'id': f"{x['id']}.{r['for']}" + (f'.{n}' if n > 1 else ''), 'exp': x['id'], 'x': x, 'hyp': r['for'], 'rule': rule, 'check': chk, 'turn': x.get('turn') or 0, 'sims': [s for s in sims if s]})
        for h in x['body'].get('tests') or []:
            if not any(r['for'] == h for r in rules): out.append({'id': f"{x['id']}.{h}", 'exp': x['id'], 'x': x, 'hyp': h, 'rule': None, 'check': None, 'turn': x.get('turn') or 0, 'sims': []})
    for t in out:
        v = verdicts.get(t['hyp']); vt = (v.get('turn') or 0) if v else None
        t['verdict'] = v if v and vt > t['turn'] and not any(q['hyp'] == t['hyp'] and t['turn'] < q['turn'] < vt for q in out) else None
    return out
def now_of(lines):
    """Where the work is, by the rule the page states: no record, an experiment without its results, a turn's first record, anything else."""
    led = recs_of(lines)
    if not led: return {'phase': 'start', 'turn': 0}
    xs = [r for r in led if r['type'] == 'experiment']; x = xs[-1] if xs else None
    if x and not any(r['type'] == 'evidence' and r.get('parent') == x['id'] for r in led):
        return {'phase': 'baseline' if x['id'] == 'X0' or x.get('by') == 'harness' else 'sims', 'turn': x.get('turn') or 0, 'exp': x['id'], 'n': len(x['body'].get('runs') or [])}
    if led[-1]['type'] == 'turn':
        again = False
        for l in reversed(lines):
            if kind(l) == 'turn': break
            if kind(l) == 'draft': again = True
        return {'phase': 'reply', 'turn': led[-1]['turn'], 'mode': led[-1]['body'].get('last_turn'), 'again': again}
    return {'phase': 'between', 'turn': led[-1].get('turn') or 0}
def places(lines, ended=False):
    """The empty places of the glance by kind, and those the work can fill next, from the records alone."""
    led = recs_of(lines); now = None if ended else now_of(lines); ts = tests_of(led); has_report = any(r['type'] == 'report' for r in led)
    reply = bool(now) and now['phase'] == 'reply'; free = reply and not now.get('mode'); sims = bool(now) and now['phase'] in ('sims', 'baseline')
    xo = next((r for r in led if r['type'] == 'experiment' and now and r['id'] == now.get('exp')), None)
    pend = max(0, (len(xo['body'].get('runs') or []) or 1) - sum(1 for s in led if s['type'] == 'simulation' and s.get('parent') == xo['id'])) if sims and xo else 0
    n = {'hyp': 1 if free else 0, 'rule': 1 if free else 0, 'sim': pend if sims else 1 if free else 0, 'check': sum(1 for t in ts if t['rule'] and not t['check']),
         'verdict': sum(1 for t in ts if not t['verdict']), 'report': 0 if has_report or not led else 1}
    wk = {'hyp': n['hyp'], 'rule': n['rule'], 'sim': n['sim'] if now else 0, 'check': sum(1 for t in ts if t['rule'] and not t['check'] and sims and pend and t['exp'] == now['exp']),
          'verdict': sum(1 for t in ts if not t['verdict'] and t['check'] and reply and now.get('mode') != 'report'), 'report': n['report'] if reply else 0}
    return n, wk, ts, now

# ---- the playback: the page's requests for the session list and the session's files are answered from the scratch copy
async def play(pg, sid, state):
    """state: {'k': lines shown, 'age': seconds the newest record is old, 'running': True}."""
    lines = raw_lines(sid); meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text())
    def body(): return ''.join(l + '\n' for l in lines[:state['k']])
    def reported(): return any(kind(l) == 'report' for l in lines[:state['k']])
    async def status(route):
        r = await route.fetch(); st = await r.json(); done = not state.get('running', True)
        for x in st['sessions']:
            if x['id'] == sid: x.update(running=not done, stoppable=False, records=state['k'], how=meta.get('how') if done else None)
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(st))
    async def ledger(route):
        t = time.time(); b = body()
        await route.fulfill(status=200, body=b, headers={'Content-Type': 'application/octet-stream', 'Date': email.utils.formatdate(t, usegmt=True), 'Last-Modified': email.utils.formatdate(t - state.get('age', 0), usegmt=True), 'Content-Length': str(len(b.encode()))})
    async def session(route):
        done = not state.get('running', True)
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(meta if done else {k: v for k, v in meta.items() if k not in ('ended', 'how', 'report', 'left_open', 'without_verdict', 'turns', 'simulations', 'calls', 'cut_off')}))
    async def report(route):
        if reported(): await route.continue_()
        else: await route.fulfill(status=404, body='')
    index = [l for l in (ROOT / 'sessions' / sid / 'runs' / 'index.json').read_text().splitlines() if l.strip()] if (ROOT / 'sessions' / sid / 'runs' / 'index.json').is_file() else []
    async def runs(route):
        have = {r['body'].get('run_id') for r in recs_of(lines[:state['k']]) if r['type'] == 'simulation'}; shown = [l for l in index if json.loads(l).get('id') in have]; rest = [l for l in index if json.loads(l).get('id') not in have]
        await route.fulfill(status=200, body=''.join(l + '\n' for l in shown + rest[:state.get('done', 0)]), headers={'Content-Type': 'application/json'})
    async def runfile(route):  # the simulator's own files of a run, as far as state['files'] says they are written: {run: {'rows': samples in series.csv, 'ended': metrics.json and params.json are there, 'params': {...} other settings in params.json}}
        if 'files' not in state: return await route.continue_()
        m = re.search(r'/runs/(r\d+)/(series\.csv|metrics\.json|params\.json)', route.request.url); f = state['files'].get(m.group(1)) if m else None; path = ROOT / 'sessions' / sid / 'runs' / m.group(1) / m.group(2) if m else None
        if f is None or not path.is_file() or (m.group(2) != 'series.csv' and not f.get('ended')): return await route.fulfill(status=404, body='')
        body = ''.join(l + '\n' for l in path.read_text().splitlines()[:1 + f['rows']]) if m.group(2) == 'series.csv' else json.dumps({**json.loads(path.read_text()), **f.get('params', {})}) if m.group(2) == 'params.json' else path.read_text()
        await route.fulfill(status=200, body='' if m.group(2) == 'series.csv' and not f['rows'] else body, headers={'Content-Type': 'text/plain'})
    await pg.route(f'**/sessions/{sid}/runs/r*/*', runfile)
    await pg.route(f'**/sessions/{sid}/runs/index.json*', runs)
    await pg.route('**/api/status*', status); await pg.route(f'**/sessions/{sid}/ledger.jsonl*', ledger)
    await pg.route(f'**/sessions/{sid}/session.json*', session); await pg.route(f'**/sessions/{sid}/report.json*', report)
    return lines, meta
async def page(b, sid=None, state=None, w=1500, h=1000, store=None):
    ctx = await b.new_context(viewport={'width': w, 'height': h})
    await ctx.add_init_script("try { const s = %s; for (const k in s) if (localStorage.getItem(k) === null) localStorage.setItem(k, s[k]); } catch (e) {}" % json.dumps({'ev-read': '1', 'ev-find': '1', **(store or {})}))  # ev-find: the table under the board open (its rows are read here)
    pg = await ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200])); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
    lines = meta = None
    if state is not None: lines, meta = await play(pg, sid, state)
    if sid:
        await pg.goto(f'{BASE}?session={sid}'); await pg.wait_for_function("(s) => typeof EV !== 'undefined' && EV.M && EV.M.id === s && document.getElementById('ev-head')", arg=sid, timeout=60000); await pg.wait_for_timeout(500)
        await pg.evaluate("() => { EV.s.findAll = true; EV.draw(); }")
    return pg, lines, meta
# the page's own tick (every second while a session runs) may be loading the stage before, and finish after this load: it is waited for before and
# after (2026-11-23: on a loaded machine s006's replay found the page one record behind at a different stage each run)
async def reload(pg): await pg.evaluate("async () => { const idle = async () => { for (let i = 0; i < 100 && EV.live && EV.live.busy; i++) await new Promise(r => setTimeout(r, 50)); }; await idle(); EV.sig = ''; await EV.load(); await idle(); }"); await pg.wait_for_timeout(60)

READ = r"""() => { const q = (s, r) => [...(r || document).querySelectorAll(s)], t = el => (el ? el.innerText.replace(/\s+/g, ' ').trim() : null), bar = document.getElementById('live-bar'), by = {}, wk = {};
  q('#s-made table.gl .slot').forEach(el => { const k = el.dataset.slot, n = Number(el.dataset.n || 1); by[k] = (by[k] || 0) + n; if (el.classList.contains('wk')) wk[k] = (wk[k] || 0) + n; });  /* the simulations an experiment waits for: one place that says how many (data-n) */
  const rows = {}; q('#s-find tr.fr').forEach(tr => { rows[tr.id.slice(3)] = { q: t(tr.querySelector('.fq [data-own]')), out: t(tr.querySelector('.fo')), m: t(tr.querySelector('.fm')), now: !!tr.querySelector('.nowp') }; });
  const cards = {}; q('#s-notebook .nb-card[data-id]').forEach(c => { const l = k => c.querySelector(`[data-l="${k}"] .nb-v`); cards[c.dataset.id] = { expected: !!l('expected').querySelector('.rr, code'), result: !!l('result').querySelector('[data-rr=check], [data-rr=void]'), working: !!l('result').querySelector('.nowp'),
    concl: t(l('conclusion')), judge: !!l('conclusion').querySelector('.nowp'), plan: t(l('plan')), when: (w => (w ? { before: w.dataset.before, secs: w.dataset.secs, text: t(w) } : null))(c.querySelector('.nb-when')) }; });
  const rs = {}; q('#s-research tr[data-line]').forEach(tr => { rs[tr.dataset.line] = { word: tr.dataset.word, of: tr.dataset.of, text: t(tr.querySelector('.rs-text')) }; });
  return { recs: EV.M.recs.length, bar: bar ? { phase: bar.dataset.phase, turn: bar.dataset.turn || null, say: t(document.getElementById('live-say')), may: t(document.getElementById('live-may')), arrived: t(document.getElementById('live-arrived')), timer: t(bar.querySelector('.lv-t')), text: t(bar) } : null,
    made: !!document.getElementById('s-made'), slots: by, wk, dots: q('#ev .nowdot').length, glNow: q('#s-made table.gl .nowdot').length, rows, next: !!document.getElementById('fr-next'), cards, nbNext: !!document.getElementById('nb-next'), gl2: !!document.querySelector('#s-made table.gl2'), hasStage: typeof EV.liveStage === 'function', stage: (st => (st ? { big: st.classList.contains('big'), on: [...st.querySelectorAll('.lv-st.on')].map(x => x.dataset.key), timer: !!st.querySelector('.lv-st.on .lv-t'), anim: st.querySelector('.lv-st.on i.sw') ? getComputedStyle(st.querySelector('.lv-st.on i.sw')).animationName : null } : null))(document.querySelector('#s-find .lv-stage')), findNone: !!document.getElementById('find-none'), findText: t(document.getElementById('s-find')), board: !!document.querySelector('#s-find #s-map'), mapNext: !!document.getElementById('map-next'), nbNow: q('#s-notebook .nb-now').map(el => el.dataset.now), last: !!document.querySelector('#s-notebook .nb-last'),
    prSlots: q('#pr-slots .pr-slot').length, none: t(document.getElementById('ov-none')), rs, fresh: q('#ev [data-fresh]').length, y: Math.round(scrollY), key: { slot: t(document.getElementById('gl-slot')), now: t(document.getElementById('gl-now')), form: t(document.getElementById('gl-form')) } }; }"""
def clean(n): return {k: v for k, v in n.items() if v}

async def part_play(b):
    P = 'play'; print('PLAY: a recorded session played back as if it were running, record by record')
    for sid in SIDS:
        st = {'k': 0, 'age': 5}; pg, lines, meta = await page(b, sid, st); N = len(lines); led_all = recs_of(lines)
        bad = {k: [] for k in ('phase', 'say', 'slots', 'wk', 'rows', 'cards', 'next', 'research', 'count', 'report', 'stage')}; phases = {}; first = {}; hyps = {}
        for k in range(N + 1):
            st['k'] = k; await reload(pg); r = await pg.evaluate(READ); n, wk, ts, now = places(lines[:k]); led = recs_of(lines[:k]); hyps = {h['id']: h for h in led if h['type'] == 'hypothesis'}
            ended = any(x['type'] == 'report' for x in led)  # the report is in: the page treats the session as ended (the harness is closing it)
            if r['recs'] != len(led): bad['count'].append((k, r['recs'], len(led)))
            if ended:
                if not r['bar'] or r['bar']['phase'] != 'closing' or r['dots'] or r['wk']: bad['phase'].append((k, 'after the report', r['bar'] and r['bar']['phase'], r['dots']))
                continue
            phases[now['phase']] = phases.get(now['phase'], 0) + 1
            if not r['bar'] or r['bar']['phase'] != now['phase'] or (now['turn'] and r['bar']['turn'] != str(now['turn'])): bad['phase'].append((k, now, r['bar'] and (r['bar']['phase'], r['bar']['turn'])))
            s = (r['bar'] or {}).get('say') or ''; want = {'start': ['preparing the session'], 'baseline': ['baseline simulation'], 'sims': [f"Turn {now['turn']}:", f"the {now.get('n')} simulation", f"experiment {now.get('exp')}"],
                                                    'reply': [f"Turn {now['turn']}:", 'the researcher is writing its reply' + (' again' if now.get('again') else '')], 'between': ['preparing the next turn']}[now['phase']]
            if not all(x in s for x in want) or (now['phase'] == 'reply' and not now.get('again') and 'again' in s) or (now['phase'] == 'reply') != bool(r['bar'] and r['bar']['may']): bad['say'].append((k, s, want))
            if r['gl2']: n['rule'] = wk['rule'] = 0  # the glance in names and words has no row of decision rules: a rule stands with its test
            if r['made'] and clean(r['slots']) != clean(n): bad['slots'].append((k, clean(r['slots']), clean(n)))
            if r['made'] and clean(r['wk']) != clean(wk): bad['wk'].append((k, clean(r['wk']), clean(wk)))
            # the filled places hold their records; an unfilled one says so
            for t in ts:
                row, card, h = r['rows'].get(t['id']), r['cards'].get(t['id']), hyps.get(t['hyp'])
                if not row or not card: bad['rows'].append((k, t['id'], 'no row or no card')); continue
                qtext = (h['body'].get('question') or '').strip() if h else ''
                if qtext and row['q'] != ' '.join(qtext.split()): bad['rows'].append((k, t['id'], row['q'], qtext))
                waiting = now['phase'] == 'sims' and t['exp'] == now['exp']
                if bool(t['rule']) != card['expected'] or bool(t['check']) != card['result'] or card['working'] != (waiting and not t['check']) or row['now'] != (waiting and not t['check']): bad['cards'].append((k, t['id'], card, bool(t['check']), waiting))
                if bool(t['verdict']) != bool(card['concl'] and card['concl'].startswith(t['verdict']['id'] if t['verdict'] else '\0')): bad['cards'].append((k, t['id'], 'conclusion', card['concl']))
                if card['judge'] != (now['phase'] == 'reply' and now.get('mode') != 'report' and bool(t['check']) and not t['verdict']): bad['cards'].append((k, t['id'], 'judge mark', card['judge']))
                if t['rule'] and card['expected']: first.setdefault(t['id'], {}).setdefault('expected', k)
                if card['result']: first.setdefault(t['id'], {}).setdefault('result', k)
            free = now['phase'] == 'reply' and not now.get('mode'); rows_free = free and (bool(hyps) or not r['hasStage'])  # since the stage strip: before the first hypothesis the section shows the strip alone
            if r['hasStage']:
                want_on = {'start': 'baseline', 'baseline': 'baseline', 'reply': 'reply', 'sims': 'sims', 'between': 'next'}[now['phase']]; sg = r['stage']   # the track of 2026-11-22: between two turns its last step, "Next turn"
                if not sg or sg['on'] != [want_on] or not sg['anim'] or sg['anim'] == 'none' or sg['big'] != (not hyps) or r['findNone'] != (not hyps) or (not hyps and ('not recorded' in r['findText'] or r['board'])): bad['stage'].append((k, now['phase'], sg, r['findNone']))
            if r['next'] != rows_free or r['nbNext'] != free or r['last'] != (now['phase'] == 'reply' and bool(now.get('mode'))) or (r['board'] and r['mapNext'] != free): bad['next'].append((k, r['next'], r['nbNext'], r['last'], r['mapNext'], now))
            if r['prSlots'] != 6 or 'No final report yet' not in (r['none'] or ''): bad['report'].append((k, r['prSlots'], r['none']))
            if r['rs'].get('limits', {}).get('word') != 'not yet' or r['rs'].get('claims', {}).get('word') != 'not yet' or any(q['word'] == 'absent' and q['of'] == '0' for q in r['rs'].values()) or (not ts and any(q['word'] in ('absent', 'present', 'partly') for q in r['rs'].values())) or (not hyps and any(q['word'] != 'not yet' for q in r['rs'].values())):
                bad['research'].append((k, {a: q['word'] for a, q in r['rs'].items()}))
        say(P, not bad['count'] and not pg.errs, f"{sid}: {N + 1} stages played (after 0 to {N} lines of its ledger); at every stage the page holds exactly the records of that stage; script errors: {pg.errs[:2] or 'none'}" + (f" {bad['count'][:2]}" if bad['count'] else ''))
        say(P, not bad['phase'], f"{sid}: where the work is equals the recount at every stage ({', '.join(f'{v} × {k}' for k, v in phases.items())}); once the report is in, nothing is marked as work" + (f": {bad['phase'][:3]}" if bad['phase'] else ''))
        say(P, not bad['say'], f"{sid}: the sentence names the turn, and the experiment and its number of simulations, from the records; “again” only after a reply that could not be used; what the reply may fill is said while a reply is written, and only then" + (f": {bad['say'][:2]}" if bad['say'] else ''))
        say(P, not bad['slots'], f"{sid}: {'' if r['made'] else '(skipped: the glance is not drawn since 2026-11-22) '}the empty places of the glance, by kind, equal the recount at every stage (checks and verdicts not there yet, simulations an experiment waits for, the final report, the places a reply may fill)" + (f": {bad['slots'][:3]}" if bad['slots'] else ''))
        say(P, not bad['wk'], f"{sid}: the places marked as “the work can fill this next” equal the recount at every stage" + (f": {bad['wk'][:3]}" if bad['wk'] else ''))
        say(P, not bad['rows'], f"{sid}: every test of a stage has its row and its card, and the row's question is the recorded question, word for word" + (f": {bad['rows'][:3]}" if bad['rows'] else ''))
        say(P, not bad['cards'], f"{sid}: a card's Expected is filled once its decision rule is recorded, Result once its check is, Conclusion once its verdict is; before that Result says the simulator is working, Conclusion that the reply may judge it" + (f": {bad['cards'][:3]}" if bad['cards'] else ''))
        order = {t: f for t, f in first.items() if 'result' in f and not f.get('expected', 10 ** 9) < f['result']}
        say(P, not order and any('result' in f for f in first.values()), f"{sid}: for each of the {sum(1 for f in first.values() if 'result' in f)} tests with a result, its decision rule stood on the page at an earlier stage than its result" + (f": {order}" if order else ''))
        say(P, not bad['next'], f"{sid}: while a reply is written that may set up a test, the table has one empty row, the notebook one empty card and the board (where the tree has it) one empty box; in a last turn the notebook says so instead" + (f": {bad['next'][:3]}" if bad['next'] else ''))
        if r['hasStage']: say(P, not bad['stage'], f"{sid}: at every stage “What it needed to find out” has the strip of a turn's steps with exactly one step marked as being worked on, the one the records say, its icon moving; before the first hypothesis the section shows that strip alone, larger, with “No question yet”, no board and no sentence about what is not recorded" + (f": {bad['stage'][:3]}" if bad['stage'] else ''))
        say(P, not bad['report'], f"{sid}: until the report arrives “What it proposes” shows its six parts empty and says “No final report yet”" + (f": {bad['report'][:2]}" if bad['report'] else ''))
        say(P, not bad['research'], f"{sid}: while it runs, the researcher card says “not yet” where there is nothing to count (never “absent” of nothing), and “not yet” for the two lines about the final report" + (f": {bad['research'][:2]}" if bad['research'] else ''))
        await pg.context.close()

def secs(ts): return datetime.datetime.fromisoformat(ts).timestamp()
async def part_times(b):
    P = 'times'; print('TIMES'); sid = SIDS[0]; lines = raw_lines(sid)
    k = next(i for i in range(1, len(lines) + 1) if now_of(lines[:i])['phase'] == 'reply' and now_of(lines[:i])['turn'] >= 2)
    st = {'k': k, 'age': 41}; pg, _, _ = await page(b, sid, st); await reload(pg)
    a = await pg.evaluate(READ); await pg.wait_for_timeout(3200); c = await pg.evaluate(READ); num = lambda s: int(re.match(r'(?:(\d+) min )?(\d+) s', s).group(2)) + 60 * int(re.match(r'(?:(\d+) min )?(\d+) s', s).group(1) or 0)
    say(P, 41 <= num(a['bar']['timer']) <= 44 and 2 <= num(c['bar']['timer']) - num(a['bar']['timer']) <= 5, f"{sid}: the newest record is 41 s old by the server's two times: the sentence says “{a['bar']['timer']}”, and “{c['bar']['timer']}” three seconds later")
    st.update(k=k, age=200); await reload(pg); d = await pg.evaluate(READ)
    say(P, d['bar']['timer'].startswith('3 min 2'), f"{sid}: 200 s old: “{d['bar']['timer']}”")
    st.update(k=len(lines), running=False); await reload(pg); r = await pg.evaluate(READ); led = recs_of(lines); by_id = {x['id']: x for x in led}; bad = []; n = late = 0
    for t in tests_of(led):
        if not t['check']: continue
        first = [by_id[s['body']['same_as']]['ts'] if s['body'].get('same_as') in by_id else s['ts'] for s in t['sims']]; w = r['cards'][t['id']]['when']
        if not t['rule'] or not first: continue
        n += 1; early = [f for f in first if f < t['x']['ts']]; late += bool(early)
        want = {'before': '0', 'secs': ''} if early else {'before': '1', 'secs': str(round(secs(min(first)) - secs(t['x']['ts'])))}
        if not w or w['before'] != want['before'] or w['secs'] != want['secs']: bad.append((t['id'], w, want))
    say(P, not bad and n > 0, f"{sid}: under each of {n} results: how long before its simulations came back the rule was stated, equal to the records' times ({n - late} stated before; {late} name a simulation that had already run, as the researcher card counts)" + (f": {bad[:3]}" if bad else ''))
    ex = next((c['when']['text'] for c in r['cards'].values() if c['when'] and c['when']['before'] == '1'), None); print(f"     e.g. “{ex}”")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

async def part_arrive(b):
    P = 'arrive'; print('ARRIVE'); sid = SIDS[0]; lines = raw_lines(sid); ph = [now_of(lines[:i]) for i in range(len(lines) + 1)]
    k0 = next(i for i in range(1, len(lines)) if ph[i]['phase'] == 'reply' and ph[i]['turn'] >= 2); k1 = next(i for i in range(k0 + 1, len(lines)) if ph[i]['phase'] == 'sims'); k2 = next(i for i in range(k1 + 1, len(lines)) if ph[i]['phase'] == 'reply')
    st = {'k': k0, 'age': 3}; pg, _, _ = await page(b, sid, st); await reload(pg); await pg.evaluate("() => window.scrollTo(0, 700)"); await pg.wait_for_timeout(200); a = await pg.evaluate(READ)
    st['k'] = k1; await reload(pg); await pg.wait_for_timeout(300); r = await pg.evaluate(READ); new = recs_of(lines[k0:k1]); cnt = lambda t: sum(1 for x in new if x['type'] == t)
    want = [f"{cnt('verdict')} verdict" if cnt('verdict') else None, f"{cnt('hypothesis')} hypothes" if cnt('hypothesis') else None] + [f"experiment {x['id']}" for x in new if x['type'] == 'experiment']
    say(P, r['bar']['arrived'] and all(w in r['bar']['arrived'] for w in want if w), f"{sid}: after the reply of turn {ph[k0]['turn']} arrived, the banner names what arrived, counted here from the new lines: “{r['bar']['arrived']}”")
    say(P, a['fresh'] == 0 and r['fresh'] > 0, f"{sid}: what just arrived is marked on the page ({r['fresh']} marked places; none before)")
    say(P, r['y'] == a['y'] == 700, f"{sid}: the page did not move when the records arrived (it stood at {a['y']} px and stands at {r['y']} px)")
    await pg.wait_for_timeout(2300); await pg.evaluate("() => EV.draw()"); await pg.wait_for_timeout(200); again = await pg.evaluate("() => { const els = [...document.querySelectorAll('#ev [data-fresh]')]; return els.length > 0 && els.every(el => parseFloat(el.style.animationDelay) <= -2); }")
    say(P, again, f"{sid}: drawing the page again two seconds later does not start the marks afresh (each carries its age)")
    # the page never moves by itself: there is no switch that makes it; a small note says that simulations started, and that a new turn began
    NOTE = "() => { const n = document.getElementById('live-note'); return n ? { text: n.innerText.replace(/\\s+/g, ' ').trim(), turn: n.dataset.turn || null, exp: n.dataset.exp || null, fixed: getComputedStyle(n).position, top: Math.round(n.getBoundingClientRect().top), right: Math.round(innerWidth - n.getBoundingClientRect().right), under: Math.round(document.getElementById('live-bar').getBoundingClientRect().bottom) } : null; }"
    n1 = await pg.evaluate(NOTE); x1 = ph[k1]
    say(P, not await pg.evaluate("() => !!document.querySelector('#live-bar input[data-ch=follow]')") and not n1,
        f"{sid}: there is no switch that moves the page; when the simulations of {x1['exp']} started no note popped up (since 2026-11-22, the operator: the banner and the status card say it)")
    # the reader's place: a part in the middle of the notebook is put near the top of the window; records arrive as the page reads them itself (the place is kept for five seconds after)
    await pg.evaluate("() => { const g = [...document.querySelectorAll('#s-notebook .nb-group')]; g[Math.max(0, g.length - 2)].scrollIntoView({ block: 'start' }); window.scrollBy(0, -200); }"); await pg.wait_for_timeout(200)
    place = await pg.evaluate("() => { const a = EV.liveAnchor(); return a ? { sel: a.sel, top: Math.round(a.top), y: Math.round(scrollY), h: document.documentElement.scrollHeight } : null; }")
    st['k'] = k2; await pg.evaluate("() => { EV.live.keepUntil = performance.now() + 5000; }"); await reload(pg); await pg.wait_for_timeout(500)
    after = await pg.evaluate("(sel) => { const el = document.querySelector(sel); return { top: el ? Math.round(el.getBoundingClientRect().top) : null, y: Math.round(scrollY), h: document.documentElement.scrollHeight }; }", place['sel'])
    say(P, after['top'] is not None and abs(after['top'] - place['top']) <= 1, f"{sid}: when the next records arrived (the page grew by {after['h'] - place['h']} px), what the reader was looking at ({place['sel']}) stood where it stood: {place['top']} px from the top of the window before, {after['top']} px after")
    n2 = await pg.evaluate(NOTE); t2 = ph[k2]['turn']
    say(P, not n2 and f'turn {t2}' in (await pg.evaluate("() => (document.getElementById('live-bar') || document.body).innerText.toLowerCase()")), f"{sid}: turn {t2} began: no note popped up, the banner says turn {t2}, and the page stayed where it was")
    # the simulations that have just ended keep their pictures until the next experiment starts
    await pg.wait_for_timeout(700); tl = await pg.evaluate("() => { const el = document.getElementById('live-tiles'); return el ? { exp: el.dataset.exp, live: el.querySelector('.lt-t').dataset.live, n: el.querySelectorAll('.lt').length, states: [...new Set([...el.querySelectorAll('.lt')].map(x => x.dataset.state))], rows: [...el.querySelectorAll('.lt')].map(x => Number(x.dataset.rows)), head: el.querySelector('.lt-t').innerText.slice(0, 60) } : null; }")
    led2 = recs_of(lines[:k2]); ran = [q for q in led2 if q['type'] == 'simulation' and q.get('parent') == x1['exp'] and not q['body'].get('same_as')]
    say(P, tl and tl['exp'] == x1['exp'] and tl['live'] == '0' and tl['n'] == len(ran) and tl['states'] == ['collected'] and all(v > 5 for v in tl['rows']), f"{sid}: after the simulations of {x1['exp']} ended, their {len(ran)} pictures stay (“{tl and tl['head']}”), each with its whole curve ({tl and tl['rows']} samples) and its measures")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

SLOTS = r"""() => { const by = {}, titles = {}; document.querySelectorAll('#s-made table.gl .slot').forEach(el => { const k = el.dataset.slot; by[k] = (by[k] || 0) + 1; (titles[k] = titles[k] || new Set()).add(el.title); });
  return { made: !!document.getElementById('s-made'), by, titles: Object.fromEntries(Object.entries(titles).map(([k, v]) => [k, [...v]])), bar: !!document.getElementById('live-bar'), dots: document.querySelectorAll('#ev .nowdot').length, wk: document.querySelectorAll('#ev .slot.wk').length, key: (document.getElementById('gl-slot') || {}).innerText || null,
    form: (document.getElementById('gl-form') || {}).innerText || null, nows: document.querySelectorAll('#ev .nowp').length, prSlots: document.querySelectorAll('#pr-slots .pr-slot').length }; }"""
async def part_ended(b):
    P = 'ended'; print('ENDED'); sid = SIDS[0]; lines = raw_lines(sid)
    st = {'k': len(lines) - 3, 'age': 3}; pg, _, meta = await page(b, sid, st); await reload(pg)
    st.update(k=len(lines), running=False); await reload(pg); await pg.wait_for_timeout(200); r = await pg.evaluate(READ); s = await pg.evaluate(SLOTS)
    say(P, r['bar'] and r['bar']['phase'] == 'ended' and meta['how'] in r['bar']['text'] and not s['dots'] and not s['wk'] and not s['nows'], f"{sid}: when the session ends on a page that saw it running, one line says so: “{r['bar'] and r['bar']['text'][:90]}”; nothing is marked as work any more")
    await pg.context.close()
    for q in dict.fromkeys(SIDS + ['s006', 's007', 's014']):
        if not (ROOT / 'sessions' / q).is_dir(): continue
        pg, _, _ = await page(b, q); s = await pg.evaluate(SLOTS); n, wk, ts, _ = places(raw_lines(q), ended=True)
        ok = (clean(s['by']) == clean(n) or not s['made']) and not s['bar'] and not s['dots'] and not s['wk'] and not s['nows'] and not s['prSlots']
        say(P, ok, f"{q} (ended), opened afresh: no banner, nothing marked as work; the places never filled are drawn empty and equal the recount: {clean(n) or 'none'}" + ('' if ok else f" (the page: {clean(s['by'])}, banner {s['bar']}, dots {s['dots']})"))
        if n['report'] and s['made']: say(P, s['titles'].get('report') == ['No final report was given'], f"{q}: its empty final report says “{(s['titles'].get('report') or ['?'])[0]}”")
        if n['verdict'] and s['made']: say(P, all(t.lower().endswith(('no verdict was given', 'the hypothesis was tested again first')) for t in s['titles'].get('verdict', [])) and 'never given' in (s['key'] or ''), f"{q}: its {n['verdict']} empty verdicts say {sorted(s['titles'].get('verdict', []))}; the key: “{(s['key'] or '').strip()}”")
        say(P, 'harness' in (s['form'] or '') and 'AI' in s['form'], f"{q}: the glance says whose form it is: “{s['form']}”") if q == SIDS[0] and s['made'] else None
        say(P, not pg.errs, f"{q}: script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

async def part_quick(b):
    P = 'quick'; print('QUICK'); sid = SIDS[0]; lines = raw_lines(sid); st = {'k': 12, 'age': 3}; pg, _, _ = await page(b, sid, st); heads = []
    pg.on('request', lambda q: heads.append(q.url) if q.method == 'HEAD' and 'ledger.jsonl' in q.url else None); await reload(pg); n0 = await pg.evaluate("() => EV.M.recs.length")
    st['k'] = 20; t0 = time.time(); took = None
    for _ in range(50):
        await pg.wait_for_timeout(100)
        if await pg.evaluate("() => EV.M.recs.length") != n0: took = time.time() - t0; break
    say(P, took is not None and took <= 5 and heads, f"{sid}: new records were on the page {took and round(took, 1)} s after they were written, found by a HEAD request for the ledger's size ({len(heads)} such requests seen), without the reader doing anything")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

async def part_layout(b):
    P = 'layout'; print('LAYOUT'); sid = SIDS[0]; lines = raw_lines(sid); ph = [now_of(lines[:i]) for i in range(len(lines) + 1)]
    ks = {'a reply is written': max(i for i in range(len(lines)) if ph[i]['phase'] == 'reply' and not ph[i].get('mode')), 'simulations run': max(i for i in range(len(lines)) if ph[i]['phase'] == 'sims' and kind(lines[i - 1]) == 'experiment')}
    for name, k in ks.items():
        wide = []
        for w in (900, 1100, 1280, 1440, 1500, 1680, 1800):
            st = {'k': k, 'age': 75}; pg, _, _ = await page(b, sid, st, w=w); await reload(pg); await pg.wait_for_timeout(200)
            m = await pg.evaluate("""() => { const bar = document.getElementById('live-bar'), over = [...document.querySelectorAll('#live-bar, #s-made .gl-scroll, #s-find, #s-notebook')].filter(el => el.scrollWidth > el.clientWidth + 1).map(el => el.id || el.className);
              window.scrollTo(0, 1800); const b = bar.getBoundingClientRect(), hd = document.getElementById('ev-head').getBoundingClientRect(), side = document.querySelector('.ev-side').getBoundingClientRect();
              return { doc: document.documentElement.scrollWidth, win: innerWidth, over, barTop: Math.round(b.top), barBottom: Math.round(b.bottom), headBottom: Math.round(hd.bottom), sideTop: Math.round(side.top), barH: Math.round(b.height) }; }""")
            if m['doc'] > m['win'] or m['over'] or not (m['headBottom'] - 2 <= m['barTop'] <= m['headBottom'] + 12) or (w >= 1100 and m['sideTop'] < m['barBottom']): wide.append((w, m))
            if pg.errs: wide.append((w, pg.errs[:2]))
            await pg.context.close()
        say(P, not wide, f"{sid}, while {name}: at 900 to 1,800 px nothing scrolls sideways; scrolled down, the banner stays just under the header strip and the detail pane starts below it" + (f": {wide[:3]}" if wide else ''))

async def part_progress(b):
    P = 'progress'; print('PROGRESS'); sid = SIDS[0]; lines = raw_lines(sid); ph = [now_of(lines[:i]) for i in range(len(lines) + 1)]
    k = max(i for i in range(len(lines)) if ph[i]['phase'] == 'sims' and kind(lines[i - 1]) == 'experiment'); st = {'k': k, 'age': 4, 'done': 3}; pg, _, _ = await page(b, sid, st)
    if not await pg.evaluate("() => typeof EV.liveDone === 'function'"): print('     (this tree has no count of collected simulations)'); await pg.context.close(); return
    await reload(pg); a = await pg.evaluate("() => { const el = document.getElementById('live-done'); return el ? { n: el.dataset.n, of: el.dataset.of, text: el.innerText } : null; }")
    st['done'] = 5; got = None
    for _ in range(50):
        await pg.wait_for_timeout(100); got = await pg.evaluate("() => { const el = document.getElementById('live-done'); return el ? { n: el.dataset.n, text: el.innerText } : null; }")
        if got and got['n'] == '5': break
    say(P, a and a['n'] == '3' and a['of'] == str(ph[k]['n']) and got and got['n'] == '5' and '5' in got['text'], f"{sid}: while the {ph[k]['n']} simulations of {ph[k]['exp']} run, the banner says how many the harness has collected: “{a and a['text']}”, then, two more runs later and without a reload, “{got and got['text']}”")
    st.update(k=len(lines), running=False); await reload(pg); led = recs_of(lines); sim = next(r for r in led if r['type'] == 'simulation' and r.get('parent') != 'X0' and not r['body'].get('same_as'))
    await pg.evaluate("(id) => { EV.s.sel = { t: 'sim', id }; EV.draw(); }", sim['id']); await pg.wait_for_timeout(500)
    line = await pg.evaluate("() => { const c = document.getElementById('sim-cmd-line'); return c ? c.textContent.replace(/\\s+/g, ' ').trim() : null; }")
    run = next(json.loads(l) for l in (ROOT / 'sessions' / sid / 'runs' / 'index.json').read_text().splitlines() if l.strip() and json.loads(l).get('id') == sim['body']['run_id'])
    prog = json.loads((ROOT / 'viewer' / 'objects.json').read_text())['program']['name']; tools = (ROOT / 'harness' / 'tools.py').read_text(); built = re.search(r'^BIN = NS3 / "([^"]+)"', tools, re.M).group(1).split('/')[-1]
    want = prog + ' ' + ' '.join(f'--{k}={json.dumps(v) if isinstance(v, bool) else v}' for k, v in run['params'].items()) + " --out=<the run's folder>"
    say(P, line == want and prog == built, f"{sid}: the detail of {sim['id']} shows how the simulator was started, the program's name as harness/tools.py has it and the options run {sim['body']['run_id']} recorded: “{(line or '')[:110]}…”" + ('' if line == want else f" (expected “{want[:110]}”)"))
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

TILES = r"""() => { const t = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : ''), box = document.getElementById('live-tiles'); if (!box) return null;
  return { exp: box.dataset.exp, note: t(box.querySelector('.lt-note')), head: t(box.querySelector('.lt-t')), wide: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    tiles: [...box.querySelectorAll('.lt')].map(n => ({ run: n.dataset.run, label: n.dataset.label, name: t(n.querySelector('.lt-h b')), state: n.dataset.state, hyps: (n.dataset.hyps || '').split(' ').filter(Boolean), forr: t(n.querySelector('[data-row=for]')), rows: +n.dataset.rows, says: t(n.querySelector('.lt-state')), badge: t(n.querySelector('.lt-h .lt-badge')), prog: +(n.querySelector('.lt-prog') || { dataset: {} }).dataset.p, labs: [...n.querySelectorAll('.lt-lab')].map(t), set: t(n.querySelector('.lt-set')), n_set: n.querySelectorAll('.lt-set b').length,
      lines: [...n.querySelectorAll('polyline.lt-ln')].map(p => p.getAttribute('points').trim().split(/\s+/).length), dots: n.querySelectorAll('circle.lt-dot').length, vals: [...n.querySelectorAll('.lt-vals b')].map(t), read: t(n.querySelector('.lt-read')), animated: getComputedStyle(n.querySelector('.lt-ico i')).animationName })) }; }"""
def v4(k, v): return ('%.4g' % (v / 1e9) + ' Gbps' if abs(v) >= 1e9 else '%.4g' % (v / 1e6) + ' Mbps') if k.endswith('_bps') else '%.4g' % (100 * v) + ' %'
def numkey(v): m = re.fullmatch(r'([\d.]+)\s*([kMG]?)bps', str(v)); return float(m.group(1)) * {'': 1, 'k': 1e3, 'M': 1e6, 'G': 1e9}[m.group(2)] if m else v
async def part_tiles(b):
    P = 'tiles'; print('TILES: the simulations of the experiment being run, one tile each, read from the simulator\'s own files')
    for sid in SIDS:
        lines = raw_lines(sid); led = recs_of(lines); st = {'k': 0, 'age': 3, 'done': 0, 'files': {}}; pg, _, _ = await page(b, sid, st)
        if not await pg.evaluate("() => typeof EV.tilesHtml === 'function'"): print('     (this tree has no tiles)'); await pg.context.close(); return
        brief = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()).get('brief_content') or await pg.evaluate("() => EV.M.brief"); kn = brief.get('knobs') or {}
        # 1. at every experiment of the session, staged as just recorded: the page's recount of which run is whose equals the records written afterwards
        bad = []; n_x = n_t = n_re = 0; exps = [(i + 1, json.loads(l)) for i, l in enumerate(lines) if kind(l) == 'experiment']; deep = None; n_for = [0, 0]; hover = None
        for k, x in exps:
            sims = [r['body'] for r in led if r['type'] == 'simulation' and r.get('parent') == x['id']]
            if not sims or any('run_id' not in q for q in sims): continue
            fresh = [(q['label'], q['run_id']) for q in sims if not q.get('same_as')]; reused = [q['label'] for q in sims if q.get('same_as')]
            st.update(k=k, done=0, files={}); await reload(pg); r = await pg.evaluate(TILES); n_x += 1; n_t += len(fresh); n_re += len(reused)
            if not fresh:
                if r: bad.append((x['id'], 'tiles for an experiment that ran nothing'))
                continue
            if not r or r['exp'] != x['id'] or [(q['label'], q['run']) for q in r['tiles']] != fresh or any(q['state'] != 'waiting' for q in r['tiles']): bad.append((x['id'], fresh[:3], r and [(q['label'], q['run'], q['state']) for q in r['tiles']][:3])); continue
            if reused and not all(l in r['note'] for l in reused): bad.append((x['id'], 'reused', reused, r['note']))
            params = {q['label']: q.get('params') or {} for q in x['body']['runs']}
            for q in r['tiles']:
                differ = [kk for kk in kn if numkey({**{a: c['default'] for a, c in kn.items()}, **params[q['label']]}[kk]) != numkey(kn[kk]['default'])]
                if q['n_set'] != len(differ) or (not differ and 'default' not in q['set']): bad.append((x['id'], q['label'], 'settings', q['set'], differ))
            # what each simulation is for: the hypotheses whose decision rule names it or whose need lists it (the ledger's experiment record), said on the tile
            for q in r['tiles']:
                rules = x['body'].get('decision_rules') or x['body'].get('rules') or []; one = len(x['body']['runs']) == 1
                want = sorted({d['for'] for d in rules if q['label'] in re.findall(r'@([A-Za-z0-9_]+)', d.get('decision_rule') or d.get('rule') or '') or (one and not re.findall(r'@([A-Za-z0-9_]+)', d.get('decision_rule') or d.get('rule') or ''))}
                              | {nd['for'] for nd in x['body'].get('needs') or [] if q['label'] in (nd.get('simulations') or [])})
                if sorted(q['hyps']) != want or not q['forr'].startswith('for') or any(h not in q['forr'] for h in want) or (not want and 'no hypothesis' not in q['forr']): bad.append((x['id'], q['label'], 'for', q['hyps'], want, q['forr'])); n_for[1] += 1
                n_for[0] += bool(want)
            if hover is None and any(q['hyps'] for q in r['tiles']):
                hover = await pg.evaluate("""async () => { const el = document.querySelector('#live-tiles .lt[data-hyps]:not([data-hyps=""])'), want = el.dataset.hyps.split(' '), y0 = scrollY, r = el.getBoundingClientRect();
                  el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: r.left + 5, clientY: r.top + 5 })); await new Promise(z => setTimeout(z, 120));
                  const hyp = x => (x.dataset.t === 'hyp' ? x.dataset.id : (EV.M.testById[x.dataset.id] || {}).hyp), hot = [...document.querySelectorAll('.hyp-hot')].map(x => [(x.closest('[id^=s-]') || {}).id, hyp(x)]);
                  document.getElementById('ev').dispatchEvent(new MouseEvent('mouseover', { bubbles: true })); await new Promise(z => setTimeout(z, 120));
                  return { want, hot, wrong: hot.filter(h => !want.includes(h[1])).length, after: document.querySelectorAll('.hyp-hot').length, moved: Math.abs(scrollY - y0) }; }""")
            if deep is None or len(fresh) > len(deep[2]): deep = (k, x, fresh, reused)
        say(P, not bad and n_t > 0, f"{sid}: at each of its {n_x} experiments, staged as just recorded, the page has one tile per simulation the harness had to run ({n_t} in all), each named by its design and with the run the records written afterwards give it; the {n_re} reused designs get no tile and are named in a line; each tile lists exactly the settings that differ from the brief's defaults" + (f": {bad[:3]}" if bad else ''))
        say(P, n_for[1] == 0 and (hover is None or (hover['hot'] and not hover['wrong'] and not hover['after'] and hover['moved'] < 1)), f"{sid}: each tile says which hypothesis its simulation is for, as the experiment's record ties them ({n_for[0]} tiles with one; the others say that no hypothesis names them or that the experiment explores); pointing at a tile marks that hypothesis where it stands ({sorted({h[0] for h in hover['hot']}) if hover else 'no test experiment here'}), nothing else, and it goes when the pointer leaves; the page did not move {hover if hover and (hover['wrong'] or hover['after'] or not hover['hot']) else ''}")
        if sid != SIDS[0] or not deep: await pg.context.close(); continue
        # 2. one experiment step by step, as the simulator's files grow
        k, x, fresh, reused = deep; rid0, rid1 = fresh[0][1], fresh[min(1, len(fresh) - 1)][1]; csv0 = [l.split(',') for l in (ROOT / 'sessions' / sid / 'runs' / rid0 / 'series.csv').read_text().splitlines()[1:]]
        async def until(js, ms=7000):
            try: await pg.wait_for_function(js, timeout=ms); return True
            except Exception: return False
        st.update(k=k, done=0, files={rid: {'rows': 0} for _, rid in fresh}); await reload(pg); ok = await until("() => [...document.querySelectorAll('#live-tiles .lt')].every(n => n.dataset.state === 'started')"); r = await pg.evaluate(TILES)
        say(P, ok and all(q['says'].startswith('started') and not q['lines'] and q['animated'] != 'none' for q in r['tiles']) and r['note'].startswith(f'0 of {len(fresh)} ended'), f"{sid} {x['id']}: every simulation has started and written no sample yet: {len(fresh)} tiles say “{r['tiles'][0]['says']}”, each with its moving icon; “{r['note'][:40]}”")
        st['files'][rid0] = {'rows': 30}; st['files'][rid1] = {'rows': 12 if rid1 != rid0 else 30}
        ok = await until(f"() => (document.querySelector('#live-tiles .lt[data-run={rid0}]') || {{ dataset: {{}} }}).dataset.rows === '30'"); r = await pg.evaluate(TILES); t0 = next(q for q in r['tiles'] if q['run'] == rid0); row = csv0[29]
        dur = {**{a: c['default'] for a, c in kn.items()}, **next(q.get('params') or {} for q in x['body']['runs'] if q['label'] == fresh[0][0])}.get('duration')
        say(P, ok and t0['state'] == 'running' and t0['lines'] == [30, 30] and t0['dots'] == 2 and t0['says'] == f"measured second {float(row[0]) - 1:.1f} of {dur}" and t0['badge'] == 'running' and 0 < t0['prog'] < 100 and t0['labs'] == ['for', 'set', 'now'] and t0['vals'] == [v4('udp_bps', float(row[1])), v4('tcp_bps', float(row[2])), '–'],
            f"{sid} {x['id']}: without a reload, as {rid0}'s series.csv grows to 30 samples its tile draws them (two curves of {t0['lines']} points) and says “{t0['says']}”, with the newest sample's own values: UDP {t0['vals'][:1]}, TCP {t0['vals'][1:2]} (the file: {row[1]}, {row[2]} bps), and a dash in the place of the loss, which is known at the end")
        box = await pg.evaluate(f"() => {{ const el = document.querySelector('#live-tiles .lt[data-run={rid0}] svg.lt-plot'); el.scrollIntoView({{ block: 'center' }}); const b = el.getBoundingClientRect(); return [b.left, b.top, b.width, b.height, scrollY]; }}")
        await pg.mouse.move(box[0] + box[2] * 0.12, box[1] + box[3] / 2); await pg.wait_for_timeout(150)
        h = await pg.evaluate(f"() => document.querySelector('#live-tiles .lt[data-run={rid0}] .lt-read').textContent.replace(/\\s+/g, ' ').trim()")
        if os.environ.get('EV_TILES_SHOT'):  # a picture of the tiles at this step, light and dark
            await pg.screenshot(path=os.environ['EV_TILES_SHOT'])
            await pg.emulate_media(color_scheme='dark'); await pg.wait_for_timeout(200); await pg.screenshot(path=os.environ['EV_TILES_SHOT'].replace('.png', '_dark.png')); await pg.emulate_media(color_scheme='light')
        m = re.match(r'at ([\d.]+) s: UDP (.+?) · TCP (.+)$', h); near = m and next((q for q in csv0[:30] if abs(float(q[0]) - 1 - float(m.group(1))) < 0.051), None)
        await pg.mouse.move(3, 3); await pg.wait_for_timeout(150); h2 = await pg.evaluate(f"() => document.querySelector('#live-tiles .lt[data-run={rid0}] .lt-read').textContent.trim()")
        say(P, bool(near) and m.group(2) == v4('udp_bps', float(near[1])) and m.group(3) == v4('tcp_bps', float(near[2])) and h2 == 'the newest sample', f"{sid} {x['id']}: pointing at the curve reads the sample under the pointer in words (“{h}”, the file's row at that time), and the line goes back to “{h2}” when the pointer leaves")
        st['files'][rid0] = {'rows': len(csv0), 'ended': True}; ok = await until(f"() => (document.querySelector('#live-tiles .lt[data-run={rid0}]') || {{ dataset: {{}} }}).dataset.state === 'ended'"); r = await pg.evaluate(TILES); t0 = next(q for q in r['tiles'] if q['run'] == rid0)
        met = json.loads((ROOT / 'sessions' / sid / 'runs' / rid0 / 'metrics.json').read_text())
        say(P, ok and t0['vals'] == [v4('udp_goodput_bps', met['udp_goodput_bps']), v4('tcp_goodput_bps', met['tcp_goodput_bps']), v4('udp_loss_frac', met['udp_loss_frac'])] and t0['animated'] == 'none' and r['note'].startswith(f'1 of {len(fresh)} ended') and t0['badge'] == 'ended' and t0['says'] == '' and t0['prog'] == 100 and t0['labs'] == ['for', 'set', 'measured'],
            f"{sid} {x['id']}: when {rid0} has ended its tile shows the measures of its metrics.json ({', '.join(t0['vals'])}) under “measured”, apart from what was set; it stops moving, its badge says “{t0['badge']}”, its strip is full, and no line repeats that it ended; the line above counts “{r['note'][:16]}”")
        st['done'] = 1; ok = await until(f"() => (document.querySelector('#live-tiles .lt[data-run={rid0}]') || {{ dataset: {{}} }}).dataset.state === 'collected'")
        say(P, ok, f"{sid} {x['id']}: once the harness's index lists {rid0}, the tile says it was collected")
        if rid1 != rid0:
            other = next(a for a in kn if a != 'seed' and 'choices' not in kn[a] and isinstance(kn[a]['default'], (int, float))); used = json.loads((ROOT / 'sessions' / sid / 'runs' / rid1 / 'params.json').read_text())
            st['files'][rid1] = {'rows': 200, 'ended': True, 'params': {other: used[other] + 1}}; ok = await until(f"() => (document.querySelector('#live-tiles .lt[data-run={rid1}]') || {{ dataset: {{}} }}).dataset.state === 'ended'"); r = await pg.evaluate(TILES); t1 = next(q for q in r['tiles'] if q['run'] == rid1)
            say(P, ok and t1['label'] == '' and t1['name'] == rid1 and 'its own file says' in t1['set'], f"{sid} {x['id']}: a run whose own params.json names other settings than the design the page expected (staged: {other} one more) is named by its run, not by a design, and its tile shows the file's settings: “{t1['set'][:70]}”")
        nxt = 'r%03d' % (max(int(rid[1:]) for _, rid in fresh) + 1)
        if (ROOT / 'sessions' / sid / 'runs' / nxt / 'series.csv').is_file():
            st['files'][nxt] = {'rows': 0}; st['k'] = k; await reload(pg); ok = await until("() => /more runs than this page expected/.test((document.querySelector('#live-tiles .lt-note') || {}).textContent || '')", 9000); r = await pg.evaluate(TILES)
            say(P, ok and all(q['label'] == '' and q['name'] == q['run'] for q in r['tiles']), f"{sid} {x['id']}: when one more run exists than the page's recount expects (staged: {nxt}), the line says so and every tile is named by its run alone")
        say(P, not r['wide'], f"{sid}: nothing scrolls sideways with the tiles shown")
        st.update(k=len(lines), running=False); await reload(pg); await pg.wait_for_timeout(300)
        say(P, await pg.evaluate("() => !document.getElementById('live-tiles')"), f"{sid}: when the session has ended there are no tiles: its simulations are in the notebook and the tables")
        say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

async def part_real(b):
    P = 'real'; print('REAL: a session started from the set-up page with the local model, on the scratch copy')
    pg, _, _ = await page(b); await pg.goto(BASE); await pg.wait_for_timeout(2000)
    await pg.click('[data-act=new]'); await pg.wait_for_function("() => document.querySelector('#new-setup #be-start') && document.querySelector('#be-pic svg.sy')", timeout=60000); await pg.wait_for_timeout(500)
    await pg.select_option('#be-open', 'two-hosts-open'); await pg.wait_for_timeout(1200); await pg.click('#be-start')
    await pg.wait_for_url('**session=**', timeout=40000); sid = pg.url.split('session=')[1].split('&')[0]; print(f'     started {sid}', flush=True)
    seen = []; first = {}; t0 = time.time(); stages = []; replies = 0; tiles = {}; shot = False; has_tiles = await pg.evaluate("() => typeof EV.tilesHtml === 'function'")
    while time.time() - t0 < 900:
        await pg.wait_for_timeout(1000)
        try: r = await pg.evaluate(READ)
        except Exception: continue
        ph = r['bar'] and r['bar']['phase']
        if not seen or seen[-1][0] != ph: seen.append((ph, r['bar'] and r['bar']['turn'], round(time.time() - t0), r['recs'])); print('    ', seen[-1], r['bar'] and r['bar']['say'], flush=True)
        stages.append((ph, r['recs']))
        try: tl = await pg.evaluate(TILES) if has_tiles else None
        except Exception: tl = None
        for q in (tl or {}).get('tiles', []):  # each tile as it was seen: its states in order, and the numbers of samples it showed while its simulation ran
            f = tiles.setdefault((tl['exp'], q['run']), {'label': q['label'], 'states': [], 'rows': []})
            if not f['states'] or f['states'][-1] != q['state']: f['states'].append(q['state'])
            if q['state'] == 'running' and (not f['rows'] or f['rows'][-1] != q['rows']): f['rows'].append(q['rows'])
        if tl and not shot and os.environ.get('EV_TILES_SHOT') and any(q['state'] == 'running' and q['rows'] >= 12 for q in tl['tiles']):
            shot = True; await pg.evaluate("() => document.getElementById('live-tiles').scrollIntoView({ block: 'start' })"); await pg.wait_for_timeout(100); await pg.screenshot(path=os.environ['EV_TILES_SHOT'].replace('.png', '_real.png')); await pg.evaluate("() => scrollTo(0, 0)")
        for tid, c in r['cards'].items():
            f = first.setdefault(tid, {})
            if c['expected'] and 'expected' not in f: f['expected'] = len(stages)
            if c['working'] and 'working' not in f: f['working'] = len(stages)
            if c['result'] and 'result' not in f: f['result'] = len(stages)
        done = [f for f in first.values() if 'result' in f]
        if ph == 'reply' and done: break  # the turn after the first results has begun
    order = [p for p, *_ in seen]; led = recs_of(raw_lines(sid)); ts = tests_of(led)
    say(P, order[:2] in (['baseline', 'reply'], ['start', 'baseline']) and 'reply' in order and 'sims' in order and order.index('reply') < order.index('sims'), f"{sid}: the stages the page showed, in order: {' → '.join(str(p) for p in order)}")
    watched = {t: f for t, f in first.items() if 'result' in f}
    ran = {x['id'] for x in led if x['type'] == 'experiment' and any(q['type'] == 'simulation' and q.get('parent') == x['id'] and not q['body'].get('same_as') for q in led)}  # the experiments that had a simulation to run
    waited = {t: f for t, f in watched.items() if t.split('.')[0] in ran}; at_once = {t: f for t, f in watched.items() if t not in waited}  # a test whose simulations were all returned from earlier ones has its result with its record
    say(P, watched and all('expected' in f and f['expected'] < f['result'] for f in waited.values()) and all('expected' in f and f['expected'] <= f['result'] for f in at_once.values()),
        f"{sid}: {len(watched)} tests were watched to their result: each of the {len(waited)} whose experiment had a simulation to run showed its decision rule before its result ({sum(1 for f in waited.values() if 'working' in f)} were seen with “the simulator is working on its simulations” in between); the {len(at_once)} whose simulations were all returned from earlier ones had rule and result together")
    if has_tiles:
        sims = {(x.get('parent'), x['body'].get('run_id')): x['body']['label'] for x in led if x['type'] == 'simulation' and not x['body'].get('same_as')}
        known = {k: f for k, f in tiles.items() if k in sims}; grew = [k for k, f in known.items() if len(f['rows']) >= 3 and f['rows'] == sorted(f['rows'])]; order_ok = all(f['states'] == [q for q in ('waiting', 'started', 'running', 'ended', 'collected') if q in f['states']] for f in known.values())
        say(P, known and all(sims[k] == f['label'] for k, f in known.items()) and grew and order_ok,
            f"{sid}: {len(known)} simulations were watched on their tiles while the simulator ran them: each tile carried the label its record got afterwards; {len(grew)} were seen growing sample by sample (e.g. {known[grew[0]]['rows'][:8] if grew else None} samples); the states came in order (e.g. {next(iter(known.values()))['states']})" + ('' if grew else f": {[(k, f['states'], f['rows'][:6]) for k, f in list(known.items())[:3]]}"))
    await pg.click('[data-act=stop]')
    for _ in range(30):
        await pg.wait_for_timeout(1500); r = await pg.evaluate(READ)
        if r['bar'] and r['bar']['phase'] == 'ended': break
    say(P, r['bar'] and r['bar']['phase'] == 'ended' and 'stopped' in r['bar']['text'], f"{sid}: stopped from the banner: “{r['bar'] and r['bar']['text'][:80]}”")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

OPEN_LOG = """(n) => { const a = document.createElement('a'); a.dataset.act = 'open'; a.dataset.t = 'log'; a.dataset.id = String(n); document.getElementById('ev').appendChild(a); a.click(); a.remove(); }"""

async def part_now(b):
    """A click on a step of the stage track. "Reply" opens what the researcher wrote in that step, its tokens (the operator, 2026-11-22: "When user
    clicks past or ongoing stage here they should be able to see tokens directly"); the turn's work log, opened by its link, begins with what is
    happening now; every figure of that block is counted again here from the records up to that line. EV_NOW_SHOT=<folder> also keeps a picture."""
    P = 'now'; print('NOW: a click on a step of the strip opens what is happening, beside the page')
    NOW = r"""() => { const p = document.getElementById('p-detail'), n = p && p.querySelector('#lg-now'), t = el => (el ? el.innerText.replace(/\s+/g, ' ').trim() : null), d = k => (n ? n.querySelector(`[data-ln="${k}"]`) : null), a = (k, at) => { const el = d(k) && d(k).querySelector(`[${at}]`); return el ? el.getAttribute(at) : null; };
      return { sel: EV.s.sel, now: n ? { phase: n.dataset.phase, turn: n.dataset.turn, head: t(n.querySelector('h3')), timer: !!n.querySelector('[data-live-t]'), labels: [...n.querySelectorAll('dt')].map(x => x.textContent), fresh: a('given', 'data-new'), given: t(d('given')), ck: a('given', 'data-ck'), wait: a('wait', 'data-wait'), may: t(d('may')), left: a('left', 'data-left'), took: a('took', 'data-took'), tookText: t(d('took')), whole: t(d('whole')), done: a('done', 'data-n') } : null,
        waiting: p ? p.querySelectorAll('[data-wait-reply]').length : 0, say: (g => (g ? g.innerText.replace(/\s+/g, ' ').trim() : null))(document.getElementById('gl-say')), voids: [...EV.M.voidIds], recs: EV.M.recs.length, first: p && p.querySelector('h2') && p.querySelector('h2').nextElementSibling === n, y: Math.round(scrollY),
        made: !!document.getElementById('s-made'), col: (() => { const cs = [...document.querySelectorAll('#s-made table.gl2 td.gl-nowc')], tr = c => c.parentElement, at = c => [...tr(c).children].indexOf(c); return { n: cs.length, rows: document.querySelectorAll('#s-made table.gl2 td.gl-nowc').length ? new Set(cs.map(tr)).size : 0, cols: [...new Set(cs.map(at))].length, head: (h => (h ? h.innerText.replace(/\s+/g, ' ').trim() : null))(document.querySelector('#s-made table.gl2 thead td.gl-nowc')), tint: cs.length ? getComputedStyle(cs[0]).backgroundColor : null, round: cs.length ? [getComputedStyle(cs[0]).borderTopLeftRadius, getComputedStyle(cs[0]).borderTopRightRadius, getComputedStyle(cs[cs.length - 1]).borderBottomLeftRadius, getComputedStyle(cs[cs.length - 1]).borderBottomRightRadius, (document.getElementById('map-now') || { getAttribute: () => null }).getAttribute('rx')] : null, board: (b => (b ? [b.dataset.turn, getComputedStyle(b).fill] : null))(document.getElementById('map-now')) }; })(),
        steps: [...document.querySelectorAll('#s-find .lv-stage .lv-st[data-key]')].map(x => [x.dataset.key, x.dataset.act || '', x.dataset.t || '', x.dataset.id || '']), inPane: !!n && n.getBoundingClientRect().right <= innerWidth + 1 }; }"""
    for sid in SIDS:
        st = {'k': 0, 'age': 7}; pg, lines, meta = await page(b, sid, st); N = len(lines); bad = []; tried = {'reply': 0, 'sims': 0, 'between': 0}; shot = os.environ.get('EV_NOW_SHOT')
        ks = [k for k in range(1, N) if now_of(lines[:k])['phase'] == 'reply' and now_of(lines[:k])['turn'] > 0]
        if not ks:  # a session recorded before turn records existed: the page cannot tell when a reply was being written
            say(P, True, f"{sid}: its ledger has no turn records, so no moment of it reads as “Reply”, the first step of the track,: nothing to click"); say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close(); continue
        badc = []
        for k in ks:
            st['k'] = k; await reload(pg); led = recs_of(lines[:k]); now = now_of(lines[:k]); U = led[-1]
            await pg.evaluate("() => { EV.s.sel = null; EV.draw(); window.scrollTo(0, document.getElementById('s-find').getBoundingClientRect().top + scrollY - 160); }"); await pg.wait_for_timeout(120); y0 = await pg.evaluate("Math.round(scrollY)")
            await pg.click('#s-find .lv-stage .lv-st[data-key=reply]'); await pg.wait_for_timeout(250); r0 = await pg.evaluate("() => ({ sel: EV.s.sel, y: Math.round(scrollY), h: (document.querySelector('#p-detail h2') || {}).textContent || '' })")
            if (r0['sel'] or {}).get('t') != 'calls' or r0['sel'].get('id') != f"{now['turn']}:reply" or r0['y'] != y0 or 'reply' not in r0['h'].lower(): bad.append((k, 'a click on Reply opens what the researcher wrote', r0))
            await pg.evaluate(OPEN_LOG, now['turn']); await pg.wait_for_timeout(250); r = await pg.evaluate(NOW); n = r['now']; tried['reply'] += 1
            if shot and tried['reply'] in (1, 2): await pg.locator('#p-detail').screenshot(path=f"{shot}/now_{sid}_{now['turn']}.png")
            if not n or (r['sel'] or {}).get('t') != 'log' or r['sel'].get('id') != now['turn'] or n['phase'] != 'reply' or n['turn'] != str(now['turn']) or not r['first'] or r['y'] != y0 or not n['timer'] or not r['inPane']: bad.append((k, 'the card', r['sel'], n and (n['head'], n['phase'], n['turn'], n['timer']), r['first'], r['inPane'], r['y'], y0)); continue
            added = [q for q in led if q['id'] in set(U['body'].get('added') or [])]; cks = [q for q in added if q['type'] == 'check']; void = sum(1 for q in cks if q['id'] in r['voids']); held = sum(1 for q in cks if q['id'] not in r['voids'] and q['body'].get('result') == 'held')
            fresh = sum(1 for q in added if q['type'] == 'evidence') + (1 if cks else 0) + (1 if any(q['type'] == 'result' for q in added) else 0) + (1 if any(q['type'] == 'note' for q in added) else 0)
            if int(n['fresh']) != fresh or (n['ck'] or None) != (f'{held},{len(cks) - void - held},{void}' if cks else None) or f'{len(led)} record' not in n['given']: bad.append((k, 'what it was given', n['fresh'], fresh, n['ck'], n['given'][:80]))
            state = {h['id']: 'open' for h in led if h['type'] == 'hypothesis'}
            for q in led:
                if q['type'] in ('verdict', 'drop'): state[q['body']['for']] = 'closed'
            wait = [h for h in state if state[h] == 'open' and any(c['type'] == 'check' and c['body'].get('for') == h for c in led)]
            if (n['wait'] or '').split(',') != (wait or ['']) and sorted(filter(None, (n['wait'] or '').split(','))) != sorted(wait): bad.append((k, 'waiting for a verdict', n['wait'], wait))
            took = []
            for i, q in enumerate(led):
                if q['type'] == 'turn' and 1 <= q['turn'] < now['turn']:
                    nx = next((z for z in led[i + 1:] if z.get('turn') == q['turn']), None)
                    if nx and nx.get('ts') and q.get('ts'): took.append(f"{q['turn']}:{int((datetime.datetime.fromisoformat(nx['ts']) - datetime.datetime.fromisoformat(q['ts'])).total_seconds() * 1000)}")
            if (n['took'] or '') != ','.join(took) or (not took and 'first reply' not in n['tookText']): bad.append((k, 'earlier replies', n['took'], took))
            if str(U['body'].get('simulations_left')) != n['left'] or 'arrives whole' not in n['whole'] or n['labels'] != ['It was given', 'Waiting for its verdict', 'This reply', 'Simulations left', 'Its earlier replies took', 'While it writes']: bad.append((k, 'left / labels', n['left'], n['labels']))
            if r['waiting'] != (0 if now.get('again') and any(q.get('turn') == now['turn'] and q['type'] != 'turn' for q in led) else 2): bad.append((k, 'the two parts the reply fills say that it is being written', r['waiting']))
            c = r['col']
            if r['made']:
                hyps_now = any(q['type'] == 'hypothesis' for q in led)  # the board is drawn once a hypothesis exists
                if c['n'] != 6 or c['rows'] != 6 or c['cols'] != 1 or not (c['head'] or '').startswith(f"turn {now['turn']} · now") or (hyps_now and (not c['board'] or c['board'][0] != str(now['turn']))) or c['tint'] in (None, 'rgba(0, 0, 0, 0)') or c['round'][:4] != ['10px'] * 4 or (hyps_now and c['round'][4] != '10'): badc.append((k, c))
                if not any(q.get('turn') == now['turn'] and q['type'] != 'turn' for q in led) and (r['say'] is None or 'the researcher is writing its reply' not in r['say'] or 'nothing the harness could use' in r['say']): badc.append((k, 'the sentence under the glance', r['say']))
                if shot and tried['reply'] == 2: await pg.locator('#s-made').screenshot(path=f"{shot}/glance_{sid}_{now['turn']}.png")
            if [x for x in r['steps'] if x[0] == 'reply'] != [['reply', 'open', 'calls', f"{now['turn']}:reply"]] or any(x[1] for x in r['steps'] if x[0] == 'checks'): bad.append((k, 'steps', r['steps']))
            # the reply arrives: the card of the same turn says what was decided, and no longer that it is being written
            k2 = next((j for j in range(k + 1, N + 1) if now_of(lines[:j])['phase'] != 'reply' or now_of(lines[:j])['turn'] != now['turn']), None)
            if k2:
                st['k'] = k2; await reload(pg); r2 = await pg.evaluate(NOW); now2 = now_of(lines[:k2]) if k2 < N else None
                if (r2['sel'] or {}).get('t') != 'log' or r2['sel'].get('id') != now['turn'] or r2['waiting'] or (r2['now'] and r2['now']['phase'] == 'reply'): bad.append((k2, 'after the reply arrived', r2['sel'], r2['waiting'], r2['now'] and r2['now']['phase']))
        say(P, tried['reply'] > 0 and not bad, f"{sid}: at each of the {tried['reply']} moments the AI was writing a reply, a click on “Reply”, the first step of the track, opens what the researcher wrote in that step, and that turn's work log beside the page, which does not move; it begins with “Now”, with the time running, and says what the AI was given (the count of records, what is new to it, the checks held / failed / void), which hypotheses wait for its verdict, how many simulations are left and how long its earlier replies took, each as counted here from the records; the two parts the reply will fill say that it is being written, and say what was decided once it has arrived" + (f": {bad[:3]}" if bad else ''))
        st['k'] = N; st['running'] = False; await reload(pg); await pg.wait_for_timeout(300); end = await pg.evaluate(NOW); st['running'] = True
        say(P, not badc and tried['reply'] > 0 and end['col']['n'] == 0, f"{sid}: at each of those moments the column of the turn being worked on stands out in “The session at a glance” as it does on the board: its six cells, from the turn's name to the final report, have a tinted ground with an edge, round at the top and at the foot by the radius of the board's band, and its name says “now”; the board's band, once the board is drawn, is on the same turn; the sentence under the glance says that the reply is being written; once the session has ended no column stands out" + (f": {badc[:2]}" if badc else '') + ('' if end['col']['n'] == 0 else f"; after the end: {end['col']}"))
        # the simulations and the checks: the step opens the turn's experiment
        bad = []; ks = [k for k in range(1, N) if now_of(lines[:k])['phase'] == 'sims'][:3] + [k for k in range(1, N) if now_of(lines[:k])['phase'] == 'between' and now_of(lines[:k])['turn'] > 0 and any(q['type'] == 'experiment' and q.get('turn') == now_of(lines[:k])['turn'] for q in recs_of(lines[:k]))][:3]
        for k in ks:
            st['k'] = k; await reload(pg); now = now_of(lines[:k]); led = recs_of(lines[:k]); x = [q for q in led if q['type'] == 'experiment' and q.get('turn') == now['turn']][-1]; key = 'sims' if now['phase'] == 'sims' else 'checks'
            await pg.evaluate("() => { EV.s.sel = null; EV.draw(); window.scrollTo(0, document.getElementById('s-find').getBoundingClientRect().top + scrollY - 160); }"); await pg.wait_for_timeout(120); y0 = await pg.evaluate("Math.round(scrollY)")
            await pg.click(f'#s-find .lv-stage .lv-st[data-key={key}]'); await pg.wait_for_timeout(250); r = await pg.evaluate(NOW); tried[now['phase']] += 1
            if r['sel'] is None or r['sel'].get('t') != 'exp' or r['sel'].get('id') != x['id'] or r['y'] != y0: bad.append((k, key, r['sel'], x['id'], r['y'], y0))
            await pg.evaluate(OPEN_LOG, now['turn']); await pg.wait_for_timeout(250); r = await pg.evaluate(NOW)
            if not r['now'] or r['now']['phase'] != now['phase'] or (now['phase'] == 'sims' and (x['id'] not in r['now']['head'] or r['now']['done'] is None)) or r['waiting']: bad.append((k, 'the work log while ' + now['phase'], r['now']))
        say(P, not bad and tried['sims'] + tried['between'] > 0, f"{sid}: while ns-3 runs the simulations ({tried['sims']} moments tried) and while the harness prepares the next turn ({tried['between']}), the step of the simulations or of the checks opens the turn's experiment beside the page; the turn's work log then begins with what is happening now (the experiment and how many simulations are collected)" + (f": {bad[:3]}" if bad else ''))
        say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for part, f in (('play', part_play), ('times', part_times), ('arrive', part_arrive), ('ended', part_ended), ('quick', part_quick), ('layout', part_layout), ('progress', part_progress), ('tiles', part_tiles), ('now', part_now), ('real', part_real)):
            if part in PARTS: await f(b)
        await b.close()
    print('RESULT:', 'PASS' if not FAILED else 'FAIL ' + ' | '.join(FAILED))
asyncio.run(main())
