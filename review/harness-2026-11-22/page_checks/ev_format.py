"""The page checks of ~/project/FORMAT_FIX.md. Part "q" (Part 1, item 5): a hypothesis's question is shown where the
hypothesis stands in short, its first 30 words with "more"; a session that recorded no question shows the hypothesis
text in its place. Part "void" (Part 3): see below. The scratch copy must hold the scripted sessions t1 and t3
(EV_EXTRA of ev_all.sh): t1 has questions, t3 is t1 with one question of 40 words.
usage:  EV_PORT=8611 EV_ROOT=<scratch>/home/project EV_SCRIPT=ev_format.py ./ev.sh [q] [void]"""
import os, re, sys, json, asyncio, pathlib
from playwright.async_api import async_playwright
PORT = os.environ.get('EV_PORT', '8600'); BASE = f"http://127.0.0.1:{PORT}/viewer/index.html"
ROOT = pathlib.Path(os.environ.get('EV_ROOT', str(pathlib.Path.home() / 'project')))
FAILED = []
def ledger(sid): return [r for r in (json.loads(l) for l in (ROOT / 'sessions' / sid / 'ledger.jsonl').read_text().splitlines() if l.strip()) if r['type'] not in ('draft', 'scratch')]
SESS = sorted(p.name for p in (ROOT / 'sessions').iterdir() if p.is_dir() and (p / 'ledger.jsonl').is_file() and re.fullmatch(r's0(0\d|1\d)', p.name))
def say(part, ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(part)
async def fresh(b, url, w=1500, h=1000):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, color_scheme='light'); await ctx.add_init_script("try { if (localStorage.getItem('ev-find') === null) localStorage.setItem('ev-find', '1'); if (localStorage.getItem('ev-setall') === null) localStorage.setItem('ev-setall', '1'); if (localStorage.getItem('ev-qlist') === null) localStorage.setItem('ev-qlist', '1'); if (localStorage.getItem('ev-cites') === null) localStorage.setItem('ev-cites', '1'); if (localStorage.getItem('ev-closer') === null) localStorage.setItem('ev-closer', 'best,knob,alone,verdicts,tests,flow,map,tree'); if (localStorage.getItem('ev-chain') === null) localStorage.setItem('ev-chain', '1'); if (localStorage.getItem('ev-alt') === null) localStorage.setItem('ev-alt', 'list'); } catch (e) {}"); pg = await ctx.new_page(); await pg.add_init_script("try { if (localStorage.getItem('ev-find') === null) localStorage.setItem('ev-find', '1'); if (localStorage.getItem('ev-setall') === null) localStorage.setItem('ev-setall', '1'); if (localStorage.getItem('ev-qlist') === null) localStorage.setItem('ev-qlist', '1'); if (localStorage.getItem('ev-cites') === null) localStorage.setItem('ev-cites', '1'); if (localStorage.getItem('ev-closer') === null) localStorage.setItem('ev-closer', 'best,knob,alone,verdicts,tests,flow,map,tree'); if (localStorage.getItem('ev-chain') === null) localStorage.setItem('ev-chain', '1'); if (localStorage.getItem('ev-alt') === null) localStorage.setItem('ev-alt', 'list'); } catch (e) {}"); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:160])); await pg.goto(url)
    await pg.wait_for_function("() => typeof EV !== 'undefined' && EV.st && (EV.s.view === 'home' || EV.s.view === 'compare' || (EV.M && EV.M.id === EV.s.sid))", timeout=60000); await pg.wait_for_timeout(1200); return pg
async def go(pg, sid, extra=''):
    await pg.goto(f'{BASE}?session={sid}{extra}'); await pg.wait_for_function("(s) => typeof EV !== 'undefined' && EV.M && EV.M.id === s", arg=sid, timeout=60000); await pg.wait_for_timeout(500)

# ================================================================== the hypothesis's question
QJS = r"""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)), M = EV.M, t = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : null), words = s => (s || '').split(/\s+/).filter(Boolean).length;
  const rows = [...document.querySelectorAll('#s-tests tr.pick[data-t=test]')].map(tr => { const T = M.testById[tr.dataset.id], h = M.hypById[T.hyp], q = tr.querySelector('.hq'), head = tr.querySelector('.tt-h');
    return { test: T.id, hyp: h.id, recorded: h.question, shown: q ? t(q) : null, head: t(head), more: q && q.querySelector('[data-act=qmore]') ? t(q.querySelector('[data-act=qmore]')) : null, text_shown: t(head).includes(h.text.replace(/\s+/g, ' ').slice(0, 30)) }; });
  EV.s.alt = 'tree'; EV.s.sel = null; EV.draw(); const tree = [...document.querySelectorAll('#s-tree .tr a.tl[data-t=test]')].map(a => t(a.closest('.tr')));
  EV.s.left = 'map'; EV.draw(); const map = [...document.querySelectorAll('#s-map .ev-map g[data-act=open] small')].map(t); EV.s.left = 'lanes'; EV.s.alt = 'list'; EV.draw();
  const T0 = M.tests[0]; EV.s.sel = { t: 'test', id: T0.id }; EV.draw(); await wait(50); const p = document.querySelector('#p-detail .hq-line'), h0 = M.hypById[T0.hyp], panel = { question: t(p), text: t(document.getElementById('p-detail')).includes(h0.text.replace(/\s+/g, ' ').slice(0, 40)) };
  EV.s.sel = { t: 'hyp', id: h0.id }; EV.draw(); await wait(50); const hyp = { question: t(document.querySelector('#p-detail .hq-line')), text: t(document.getElementById('p-detail')).includes(h0.text.replace(/\s+/g, ' ').slice(0, 40)) };
  EV.s.sel = { t: 'log', id: h0.turn }; EV.draw(); await wait(50); const card = t(document.getElementById('p-detail')); EV.s.sel = null; EV.draw();
  return { rows, tree, map, panel, hyp, card_has_question: !!h0.question && card.includes('its question: ' + h0.question), h0: { q: h0.question, text: h0.text } }; }"""
async def part_q(b):
    print('THE QUESTION  (Part 1, item 5)'); P = 'q'; pg = await fresh(b, f'{BASE}?session=t1'); r = await pg.evaluate(QJS)
    led = {h['id']: h['body'] for h in ledger('t1') if h['type'] == 'hypothesis'}
    say(P, all(x['recorded'] == led[x['hyp']].get('question') and x['shown'] == x['recorded'] and not x['more'] and not x['text_shown'] for x in r['rows']) and len(r['rows']) >= 3, f"t1, the tests list: each of the {len(r['rows'])} rows shows its hypothesis's question as the ledger holds it, in place of the hypothesis text: {[(x['hyp'], x['shown']) for x in r['rows']]}")
    say(P, r['panel']['question'] == r['h0']['q'] and r['panel']['text'] and r['hyp']['text'] and r['card_has_question'], f"t1: the test's panel shows the question (“{r['panel']['question']}”) above the hypothesis text, the hypothesis's card quotes the hypothesis (its design since 2026-11-22), and the work-log card names the question")
    say(P, any(r['h0']['q'][:30] in x for x in r['tree']) and any(r['h0']['q'][:30] in x for x in r['map']), f"t1: the tree's row and the hypothesis map's node show the question: “{r['tree'][0][:70]}” · “{next(x for x in r['map'] if r['h0']['q'][:30] in x)}”")
    await go(pg, 't3'); row = (await pg.query_selector_all('#s-tests tr.pick[data-t=test]'))[1]; q = await row.query_selector('.hq')
    before = await q.evaluate("e => ({ words: e.dataset.words, text: e.firstChild.textContent.trim(), more: e.querySelector('[data-act=qmore]').textContent })")
    await pg.evaluate("() => window.scrollTo(0, document.getElementById('s-tests').getBoundingClientRect().top + scrollY - 80)"); await pg.wait_for_timeout(200); y = await pg.evaluate('scrollY'); sel = await pg.evaluate('JSON.stringify(EV.s.sel)')
    await (await row.query_selector('[data-act=qmore]')).click(); await pg.wait_for_timeout(300)
    row = (await pg.query_selector_all('#s-tests tr.pick[data-t=test]'))[1]; after = await (await row.query_selector('.hq')).evaluate("e => ({ text: e.firstChild.textContent.trim(), more: e.querySelector('[data-act=qmore]').textContent })"); y2 = await pg.evaluate('scrollY'); sel2 = await pg.evaluate('JSON.stringify(EV.s.sel)')
    say(P, before['words'] == '40' and len(before['text'].split()) == 31 and before['text'].endswith('word30 …') and before['more'] == 'more' and len(after['text'].split()) == 40 and after['more'] == 'less' and y == y2 and sel == sel2,
        f"t3, a question of {before['words']} words: its first 30 words are shown, then “{before['more']}”; a click shows all {len(after['text'].split())} and “{after['more']}”, the page moved {y2 - y} px and nothing else was opened")
    wrong = []
    for s in SESS:
        await go(pg, s); r = await pg.evaluate(QJS)
        if any(x['recorded'] or x['shown'] or not x['text_shown'] for x in r['rows']) or r['panel']['question'] or not r['hyp']['text'] or (r['rows'] and not r['panel']['text']): wrong.append((s, [x for x in r['rows'] if x['shown'] or not x['text_shown']][:2], r['panel']))
    n = sum(1 for s in SESS for h in ledger(s) if h['type'] == 'hypothesis' and h['body'].get('question'))
    say(P, not wrong and n == 0, f"the {len(SESS)} old sessions record no question ({n} in their ledgers): every row of their tests lists, the test's panel and the hypothesis's card show the hypothesis text in its place" + (f": {wrong[:2]}" if wrong else ''))
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== void checks (Part 3)
def void_of(sid):
    """Counted here from the ledger, apart from the page and from harness/session_figures.py: the void checks (the rule
    names two or more labels, at least two of them the same run of that experiment), those whose labels are all one
    run, and the verdicts that rest only on void checks (the checks of the hypothesis in the last experiment that
    tested it before the verdict are all void)."""
    recs = ledger(sid); run = {(r['parent'], r['body'].get('label')): r['body'].get('run_id') for r in recs if r['type'] == 'simulation'}
    void, strict, made, rests, res = [], [], {}, [], {'held': 0, 'failed': 0, 'other': 0}
    for i, r in enumerate(recs):
        if r['type'] == 'check':
            labels = list(dict.fromkeys(re.findall(r'[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)', str(r['body'].get('decision_rule') or r['body'].get('rule') or ''))))
            ids = [run.get((r['parent'], l)) for l in labels]; known = [x for x in ids if x]; v = len(labels) >= 2 and len(set(known)) < len(known)
            if v: void.append(r['id'])
            if v and len(set(ids)) == 1: strict.append(r['id'])
            if not v: res[r['body'].get('result') if r['body'].get('result') in ('held', 'failed') else 'other'] += 1
            made.setdefault(r['body'].get('for'), []).append((i, r['parent'], r['id']))
        elif r['type'] == 'verdict':
            cs = [c for c in made.get(r['body'].get('for'), []) if c[0] < i]; last = [c[2] for c in cs if c[1] == cs[-1][1]] if cs else []
            if last and all(c in void for c in last): rests.append(r['id'])
    return {'void': void, 'strict': strict, 'rests': rests, 'held': res['held'], 'failed': res['failed'], 'checks': sum(r['type'] == 'check' for r in recs)}
VJS = r"""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)), M = EV.M, t = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : null), tally = el => (el ? [el.dataset.held, el.dataset.failed, el.dataset.void].map(Number) : null);
  EV.s.sel = { t: 'session', id: M.id }; EV.s.alt = 'list'; EV.s.step = null; M.turns.forEach(q => { EV.s.tree['turn:' + q.n] = true; }); EV.draw(); await wait(60);
  const rows = [...document.querySelectorAll('#s-tests tr.pick[data-t=test]')].map(tr => { const T = M.testById[tr.dataset.id]; return { test: T.id, check: T.check && T.check.id, mark: !!tr.querySelector('.tt-k [data-void]'), word: t(tr.querySelector('.tt-k')), note: t(tr.querySelector('.vd-note')), margin: !!tr.querySelector('.mgc .mg-n, .mgc svg, .mgc .mg'), margin_text: t(tr.querySelector('.mgc')),
    rests: !!tr.querySelector('.tt-v [data-rests]'), rests_text: t(tr.querySelector('.tt-v [data-rests]')), verdict: T.verdict && T.verdict.id }; });
  const out = { page_void: [...M.voidIds], rows, strip: tally(document.querySelector('#s-made .tally')), intro: t(document.querySelector('.ev-intro p')),
    summary: { line: t(document.getElementById('vc-void')), seq_void: Number((document.querySelector('#vc-seq .sq') || { dataset: {} }).dataset.void || 0), seq_marks: document.querySelectorAll('#vc-seq [data-m=void]').length, seq_drawn: document.querySelectorAll('#vc-seq .sq [data-m]').length,
      table: Object.fromEntries([...document.querySelectorAll('#vc-session table.vc tbody tr')].map(tr => [t(tr.cells[0]), [...tr.cells].slice(1).map(c => Number(c.textContent))])), note: t(document.querySelector('#vc-session table.vc + p')) },
    made: { drawn: !!document.getElementById('s-made'), marks: document.querySelectorAll('#s-made table.gl a.gm[data-m=void], #s-made table.gl:not(.gl2) [data-m=void]:not(a .gk)').length, key: t([...document.querySelectorAll('#s-made .gl-key > *')].find(x => x.querySelector && x.querySelector('[data-m=void]')) || null) },
    tree: (() => { EV.s.alt = 'tree'; EV.draw(); const o = { rests: document.querySelectorAll('#s-tree [data-rests]').length, void: document.querySelectorAll('#s-tree .ts [data-void="1"]').length, tallies: [...document.querySelectorAll('#s-tree .tally')].map(tally) }; EV.s.alt = 'list'; EV.draw(); return o; })(),
    map_box: t([...document.querySelectorAll('#s-how *')].find(x => /\d+ held/.test(x.textContent) && x.children.length === 0) || null), words_void: (document.getElementById('ev').innerText.match(/\bvoid\b/g) || []).length - ((document.getElementById('s-research') || { innerText: '' }).innerText.match(/\bvoid\b/g) || []).length };  /* “How it worked as a researcher” says “0 void tests” by its rule (READABLE_PAGE.md, Part 6) */
  const T = M.tests.find(q => q.check && q.check.void);
  if (T) { EV.s.sel = { t: 'test', id: T.id }; EV.draw(); EV.flowFit && EV.flowFit(); await wait(120); const p = document.getElementById('p-detail');
    out.panel = { test: T.id, diamond: t([...p.querySelectorAll('.t-flow svg g')].find(g => /did the rule hold/.test(g.textContent)) || null), under: t(p.querySelector('.t-flow [data-void]')), note: t(p.querySelector('.void-note')), check_line: !!p.querySelector('p [data-void="1"]'),
      verdict_rests: T.verdict ? !!p.querySelector('.t-flow [data-rests], h3 [data-rests]') : null, verdict_void_only: T.verdict ? T.verdict.voidOnly : null, chart_margin: null }; }
  EV.s.sel = null; EV.draw(); return out; }"""
VREPLAY = r"""async () => { const M = EV.M, n = M.steps.length, bad = []; EV.s.sel = { t: 'session', id: M.id };
  for (let k = 0; k < n; k++) { EV.s.step = k; EV.draw(); if (k % 20 === 19) await new Promise(r => setTimeout(r, 0));
    const by = id => (M.recStep[id] ?? 0) <= k, want = M.checks.filter(c => c.void && by(c.id)).length, ta = document.querySelector('#s-made .tally'), glance = !!document.getElementById('s-made'), strip = ta ? Number(ta.dataset.void) : want;
    const rowsV = [...document.querySelectorAll('#s-tests tr.pick[data-t=test]')].filter(tr => { const q = tr.querySelector('.tt-k [data-void]'); return q && !q.closest('.later') && getComputedStyle(q).visibility !== 'hidden'; }).length;
    const rests = [...document.querySelectorAll('#s-tests .tt-v [data-rests]')].filter(q => !q.closest('.later') && getComputedStyle(q).visibility !== 'hidden').length, wantR = M.tests.filter(T => T.verdict && T.verdict.voidOnly && by(T.verdict.id)).length;
    const line = document.getElementById('vc-void'), ln = line ? Number(line.dataset.void) : 0, made = document.querySelectorAll('#s-made table.gl a.gm[data-m=void], #s-made table.gl:not(.gl2) [data-m=void]:not(a .gk)').length;
    if (strip !== want || ln !== want || rowsV !== M.tests.filter(T => T.check && T.check.void && by(T.check.id)).length || rests !== wantR || (glance && made !== M.tests.filter(T => T.check && T.check.void && by(T.check.id)).length)) bad.push({ k, recorded_by_k: want, strip, summary_line: ln, list_rows: rowsV, made_marks: made, rests, rests_recorded_by_k: wantR }); }
  EV.s.step = null; EV.s.sel = null; EV.draw(); return { steps: n, problems: bad.length, first: bad.slice(0, 2) }; }"""
async def part_void(b):
    print('VOID CHECKS  (Part 3)'); P = 'void'; W = {s: void_of(s) for s in SESS}
    tot = {k: sum(len(W[s][k]) for s in SESS if s != 's001') for k in ('void', 'strict', 'rests')}; nchk = sum(W[s]['checks'] for s in SESS if s != 's001')
    briefs = {s: (json.loads((ROOT / 'sessions' / s / 'session.json').read_text()).get('brief') if (ROOT / 'sessions' / s / 'session.json').is_file() else None) for s in SESS}
    by = {b: sum(len(W[s]['void']) for s in SESS if briefs[s] == b) for b in set(briefs.values()) if b}
    say(P, nchk == 337 and tot['void'] == 107 and by == {'two-hosts-open': 106, 'two-hosts-udp-demand': 1} and tot['strict'] == 96, f"counted here from the ledgers of s002 to s019: {nchk} checks, {tot['void']} void ({by}), {tot['strict']} whose labels are all one simulation; {tot['rests']} verdicts rest only on void checks")
    aud = {s: json.loads((ROOT / 'checks/audit' / f'{s}.json').read_text()) for s in SESS if (ROOT / 'checks/audit' / f'{s}.json').is_file()}
    say(P, len(aud) == 18 and all(sorted(c['id'] for c in a['checks'] if c['void']) == sorted(W[s]['void']) and sorted(c['id'] for c in a['checks'] if c['one_simulation']) == sorted(W[s]['strict']) and sorted(v['id'] for v in a['verdicts'] if v['rests_only_on_void_checks']) == sorted(W[s]['rests']) for s, a in aud.items())
        and aud['s014']['counts']['designs_whose_label_names_a_weight_without_weightUdp'] == 97 and aud['s017']['counts']['designs_whose_label_names_a_weight_without_weightUdp'] == 107,
        f"checks/audit/ holds {len(aud)} files (s002 to s019); in each the void checks, the stricter ones and the verdicts that rest only on void checks are the ones counted here; designs whose label names a weight without weightUdp: s014 {aud.get('s014', {}).get('counts', {}).get('designs_whose_label_names_a_weight_without_weightUdp')}, s017 {aud.get('s017', {}).get('counts', {}).get('designs_whose_label_names_a_weight_without_weightUdp')}")
    pg = await fresh(b, BASE); await pg.wait_for_timeout(1500)
    home = await pg.evaluate("""() => ({ head: [...document.querySelectorAll('#home-rows thead th, table thead th')].map(th => th.textContent.trim()).filter(x => /void/.test(x)), rows: Object.fromEntries([...document.querySelectorAll('#home-rows tr[data-id]')].map(tr => [tr.dataset.id, { void: (tr.querySelector('td[data-col=void]') || {}).textContent, of: (tr.querySelector('td[data-col=void]') || { dataset: {} }).dataset.of, tip: (tr.querySelector('td[data-col=void]') || {}).title || (tr.querySelector('td[data-col=void] [title]') || {}).title || '', tally: (() => { const q = tr.querySelector('td[data-col=seq] .tally'); return q ? [Number(q.dataset.held), Number(q.dataset.failed)] : null; })(), marks: tr.querySelectorAll('td[data-col=seq] .sq [data-m=void]').length, drawn: tr.querySelectorAll('td[data-col=seq] .sq [data-m]').length }])), status: Object.fromEntries(EV.st.sessions.map(x => [x.id, x.void])) })""")
    wrong = [(s, home['rows'].get(s), W[s]) for s in SESS if s != 's001' and (home['rows'][s]['void'].strip() != str(len(W[s]['void'])) or home['rows'][s]['of'] != str(W[s]['checks']) or home['status'][s] != [len(W[s]['void']), W[s]['checks']] or (home['rows'][s]['tally'] or [0, 0]) != [W[s]['held'], W[s]['failed']])]
    say(P, home['head'] == ['void checks'] and not wrong and home['rows']['s001']['void'].strip() == '–' and 'not recorded' in home['rows']['s001']['tip'] and home['rows']['s014']['tip'].startswith('44 of the 91 checks'), f"Home has the column “void checks”; in every row it is the count made here, with “of all its checks” on hover (s014: {home['rows']['s014']['void']} [{home['rows']['s014']['tip'][:19]}], s017: {home['rows']['s017']['void']}, s004: {home['rows']['s004']['void']}, s006: {home['rows']['s006']['void']}; s001, the first format: “{home['rows']['s001']['void']}”, {home['rows']['s001']['tip'][:12]}), and held and failed beside the marks leave the void ones out" + (f": {wrong[:2]}" if wrong else ''))
    await pg.click('th a[data-act=sort][data-id=void]'); await pg.wait_for_timeout(300); await pg.click('th a[data-act=sort][data-id=void]'); await pg.wait_for_timeout(400); top = await pg.evaluate("() => [...document.querySelectorAll('#home-rows tr[data-id]')].slice(0, 3).map(tr => tr.dataset.id)")
    say(P, top == ['s014', 's017', 's019'], f"sorted by that column, largest first: {top}")
    await go(pg, 's014'); r = await pg.evaluate(VJS); w = W['s014']
    vr = [x for x in r['rows'] if x['mark']]; nv = [x for x in r['rows'] if not x['mark']]
    say(P, sorted(r['page_void']) == sorted(w['void']) and sorted(x['check'] for x in vr) == sorted(w['void']) and all(x['word'] == 'check void' and x['note'] == 'this decision rule compared a simulation with itself' and not x['margin'] for x in vr) and all(not x['note'] and 'void' not in (x['word'] or '') for x in nv),
        f"s014, the tests list: the {len(vr)} rows of void checks (the {len(w['void'])} counted here) say “{vr[0]['word']}” and “{vr[0]['note']}” and have no margin; the other {len(nv)} rows do not")
    say(P, sorted(x['verdict'] for x in r['rows'] if x['rests']) == sorted(x['verdict'] for x in r['rows'] if x['verdict'] in w['rests']) and all(x['rests_text'] == '· rests on void checks' for x in r['rows'] if x['rests']) and len({x['verdict'] for x in r['rows'] if x['rests']}) == len(w['rests']),
        f"s014: a verdict whose checks were all void is marked “rests on void checks” ({len({x['verdict'] for x in r['rows'] if x['rests']})} verdicts, the {len(w['rests'])} counted here), and no other verdict is")
    # the introduction above the Overview is gone since READABLE_PAGE.md (Part 1): the header strip states the three counts
    say(P, (r['strip'] == [w['held'], w['failed'], len(w['void'])] or r['strip'] is None) and r['intro'] is None, f"s014, the tally of the checks in “The session at a glance” (None: the card is not drawn since 2026-11-22): held, failed, void = {r['strip']} (here: {w['held']}, {w['failed']}, {len(w['void'])}); the introduction that repeated them is no longer on the page")
    sm = r['summary']
    say(P, sm['line'] and sm['line'].startswith(f"{len(w['void'])} void: this decision rule compared a simulation with itself") and sm['seq_void'] == len(w['void']) and sm['table'].get('void') == [0, 15, 0, 0] and sum(sum(v) for v in sm['table'].values()) == 31 and 'rests on void checks' in sm['note'],
        f"s014, the session's summary: “{sm['line']}”; the checks in order hold {sm['seq_void']} void ({sm['seq_marks']} among the {sm['seq_drawn']} drawn); verdicts against checks has the row void: {sm['table'].get('void')} of {sum(sum(v) for v in sm['table'].values())} verdicts")
    say(P, (not r['made']['drawn'] or (r['made']['marks'] == len(w['void']) and r['made']['key'] and 'compared a simulation with itself' in r['made']['key'])) and r['tree']['void'] == len(w['void']) and sum(x[2] for x in r['tree']['tallies']) == len(w['void']) and sum(x[0] for x in r['tree']['tallies']) == w['held'] and sum(x[1] for x in r['tree']['tallies']) == w['failed'],
        f"s014: “What this session is made of” draws {r['made']['marks'] if r['made']['drawn'] else '(not drawn since 2026-11-22)'} void marks and names the sign in its key; the tree marks {r['tree']['void']} void tests, and its experiments' counts add up to {[sum(x[i] for x in r['tree']['tallies']) for i in range(3)]}")
    p = r['panel']
    say(P, p and 'void' in p['diamond'] and p['under'] == 'void: this decision rule compared a simulation with itself' and p['note'] and 'are one simulation' in p['note'] and p['check_line'] and (p['verdict_rests'] == p['verdict_void_only']), f"s014, test {p and p['test']} as a flow chart: the diamond says “{p and p['diamond']}”, under it “{p and p['under']}”; below: “{p and p['note'][:150]}”")
    rp = await pg.evaluate(VREPLAY)
    say(P, not rp['problems'], f"s014, the replay: at each of {rp['steps']} steps the strip, the summary, the tests list, the card and the verdicts' marks show only the void checks recorded by then" + (f": {rp['first']}" if rp['problems'] else ''))
    for s, strip in (('s006', [11, 7, 0]), ('s011', [10, 2, 0])):
        await go(pg, s); r = await pg.evaluate(VJS)
        say(P, (r['strip'] == strip or r['strip'] is None) and not r['page_void'] and r['words_void'] == 0 and not [x for x in r['rows'] if x['mark'] or x['rests']], f"{s}: its counts are unchanged ({'the glance is not drawn' if r['strip'] is None else str(r['strip'][0]) + ' held, ' + str(r['strip'][1]) + ' failed'}) and the word “void” stands nowhere on its page")
    await go(pg, 's004'); r = await pg.evaluate(VJS)
    say(P, (r['strip'] == [W['s004']['held'], W['s004']['failed'], 1] or r['strip'] is None) and [x['check'] for x in r['rows'] if x['mark']] == W['s004']['void'], f"s004, the one void check of the given-goal brief: {[x['check'] for x in r['rows'] if x['mark']]}; the strip now says {r['strip']} (before: 6 held, 5 failed)")
    wrong = []
    for s in SESS:
        await go(pg, s); g = await pg.evaluate("() => ({ v: [...EV.M.voidIds].sort(), strip: (() => { const q = document.querySelector('#s-made .tally'); return q ? [q.dataset.held, q.dataset.failed, q.dataset.void].map(Number) : null; })(), rests: EV.M.hyps.filter(h => h.verdict && h.verdict.voidOnly).map(h => h.verdict.id).sort() })")
        if g['v'] != sorted(W[s]['void']) or g['rests'] != sorted(W[s]['rests']) or (g['strip'] and g['strip'] != [W[s]['held'], W[s]['failed'], len(W[s]['void'])]): wrong.append((s, g['strip'], len(g['v']), len(W[s]['void'])))
    say(P, not wrong, f"all {len(SESS)} sessions: the page's void checks, its verdicts that rest only on them, and the strip's three counts are the ones counted here" + (f": {wrong[:3]}" if wrong else ''))
    await pg.goto(f'{BASE}?tab=compare&brief=two-hosts-open'); await pg.wait_for_timeout(2500)
    cmp_ = await pg.evaluate("() => ({ table: Object.fromEntries([...document.querySelectorAll('#cmp-vc table.vc[data-vc=brief] tbody tr')].map(tr => [tr.cells[0].textContent.trim(), [...tr.cells].slice(1).map(c => Number(c.textContent))])), note: document.querySelector('#cmp-vc').innerText.includes('rests on void checks') })")
    wantv = sum(len(W[s]['rests']) for s in SESS if briefs[s] == 'two-hosts-open')
    say(P, sum(cmp_['table'].get('void', [0])) == wantv and cmp_['note'], f"Compare, brief two-hosts-open: verdicts against checks has the row void with {sum(cmp_['table'].get('void', [0]))} verdicts (counted here: {wantv})")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

PARTS = {'q': part_q, 'void': part_void}
async def main():
    want = [a for a in sys.argv[1:] if a in PARTS] or list(PARTS)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for k in want: await PARTS[k](b)
        await b.close()
    print('RESULT:', 'PASS' if not FAILED else 'FAIL ' + ', '.join(sorted(set(FAILED))))
asyncio.run(main())
