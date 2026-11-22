"""The "Done when" checks of ~/PAGE_POLISH.md, part by part, with each part's replay check. Chromium at 1440 x 900, light mode,
a fresh profile where "first visit" matters. Counts are made here from the ledgers (read without their draft records).
usage:  EV_PORT=8611 EV_ROOT=<scratch>/home/project EV_SCRIPT=ev_polish.py ./ev.sh [1 2 ...]   (no part named: all that exist)"""
import os, re, sys, json, asyncio, pathlib, collections
from playwright.async_api import async_playwright
PORT = os.environ.get('EV_PORT', '8600'); BASE = f"http://127.0.0.1:{PORT}/viewer/index.html"
ROOT = pathlib.Path(os.environ.get('EV_ROOT', str(pathlib.Path.home() / 'project')))
FAILED = []
def ledger(sid): return [r for r in (json.loads(l) for l in (ROOT / 'sessions' / sid / 'ledger.jsonl').read_text().splitlines() if l.strip()) if r['type'] not in ('draft', 'scratch')]
SESS = sorted(p.name for p in (ROOT / 'sessions').iterdir() if p.is_dir() and (p / 'ledger.jsonl').is_file() and re.fullmatch(r's0(0\d|1\d)', p.name))  # the 19 real sessions (a scratch copy may hold test sessions too)
L = {s: ledger(s) for s in SESS}
def say(part, ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(part)
async def fresh(b, url, w=1440, h=900, setall='1'):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, color_scheme='light'); await ctx.add_init_script("try { if (localStorage.getItem('ev-find') === null) localStorage.setItem('ev-find', '1'); if (localStorage.getItem('ev-setall') === null) localStorage.setItem('ev-setall', '" + setall + "'); if (localStorage.getItem('ev-qlist') === null) localStorage.setItem('ev-qlist', '1'); if (localStorage.getItem('ev-cites') === null) localStorage.setItem('ev-cites', '1'); if (localStorage.getItem('ev-closer') === null) localStorage.setItem('ev-closer', 'best,knob,alone,verdicts,tests,flow,map,tree'); if (localStorage.getItem('ev-chain') === null) localStorage.setItem('ev-chain', '1'); if (localStorage.getItem('ev-alt') === null) localStorage.setItem('ev-alt', 'list'); } catch (e) {}"); pg = await ctx.new_page(); await pg.add_init_script("try { if (localStorage.getItem('ev-find') === null) localStorage.setItem('ev-find', '1'); if (localStorage.getItem('ev-setall') === null) localStorage.setItem('ev-setall', '" + setall + "'); if (localStorage.getItem('ev-qlist') === null) localStorage.setItem('ev-qlist', '1'); if (localStorage.getItem('ev-cites') === null) localStorage.setItem('ev-cites', '1'); if (localStorage.getItem('ev-closer') === null) localStorage.setItem('ev-closer', 'best,knob,alone,verdicts,tests,flow,map,tree'); if (localStorage.getItem('ev-chain') === null) localStorage.setItem('ev-chain', '1'); if (localStorage.getItem('ev-alt') === null) localStorage.setItem('ev-alt', 'list'); } catch (e) {}"); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:160])); await pg.goto(url)
    await pg.wait_for_function("() => typeof EV !== 'undefined' && EV.st && (EV.s.view === 'home' || EV.s.view === 'compare' || (EV.M && EV.M.id === EV.s.sid))", timeout=30000); await pg.wait_for_timeout(1200); return pg
async def go(pg, sid, extra=''):
    await pg.goto(f'{BASE}?session={sid}{extra}'); await pg.wait_for_function("(s) => typeof EV !== 'undefined' && EV.M && EV.M.id === s", arg=sid, timeout=30000); await pg.wait_for_timeout(500)

# what every part must keep: no sign written as a character of a font, and the colour of held and failed on the sign only
SIGNS = r"""() => { const bad = [], col = v => { const i = document.createElement('i'); i.style.color = `var(${v})`; document.getElementById('ev').appendChild(i); const c = getComputedStyle(i).color; i.remove(); return c; }, good = col('--good'), crit = col('--critical');
  const w = document.createTreeWalker(document.getElementById('ev'), NodeFilter.SHOW_TEXT); let t, texts = 0;
  while ((t = w.nextNode())) { const p = t.parentElement, s = t.textContent; if (!s.trim() || p.closest('title, option, script, style, #ev-print') || !p.getClientRects().length) continue; texts++;
    const m = s.match(/[✓✗✕✔✘▲▼■◇○⚠△▽□●◆]/); if (m) bad.push({ what: 'a sign written as a character', sign: m[0], at: s.trim().slice(0, 50) });
    const c = getComputedStyle(p).color; if (/\b(held|failed|supported|refuted)\b/.test(s) && (c === good || c === crit)) bad.push({ what: 'a result word in the colour of held or failed', at: s.trim().slice(0, 50) }); }
  return { texts, marks: document.querySelectorAll('#ev [data-m]').length, problems: bad.length, first: bad.slice(0, 4) }; }"""
async def signs(pg, part, where):
    r = await pg.evaluate(SIGNS); say(part, not r['problems'], f"{where}: no sign is a character of a font, and no result word is green or red ({r['texts']} texts, {r['marks']} drawn marks)" + (f": {r['first']}" if r['problems'] else ''))

# ================================================================== Part 1: a failed check is a result, not a warning
KINDS = ['held', 'both', 'failed', 'nocheck', 'none']
def claims_of(sid):
    """Each claim of the session's final report: the checks it cites itself, in order, and its kind."""
    recs = L[sid]; rep = next((r for r in recs if r['type'] == 'report'), None); res = {r['id']: r['body']['result'] for r in recs if r['type'] == 'check'}; out = []
    for c in (rep['body'].get('claims') or []) if rep else []:
        ev = c.get('evidence') or []; cs = [(i, res[i]) for i in ev if i in res]; rs = {r for _, r in cs}
        out.append((cs, 'none' if not ev else 'nocheck' if not cs else 'both' if rs == {'held', 'failed'} else 'held' if rs == {'held'} else 'failed'))
    return out if rep else None
CLAIMS = r"""() => ({ counts: (document.getElementById('claim-counts') || { dataset: {} }).dataset.counts || null, line: (document.getElementById('claim-counts') || {}).textContent || null,
  claims: [...document.querySelectorAll('#s-report button.claim')].map(b => ({ kind: b.dataset.kind, marks: [...b.querySelectorAll('.cm [data-check]')].map(s => [s.dataset.check, s.querySelector('[data-m]').dataset.m]), text: b.querySelector('.cl-ev').textContent.trim(),
    full: b.querySelector('.ct').scrollHeight <= b.querySelector('.ct').clientHeight + 1, stripe: getComputedStyle(b).borderLeftWidth + ' ' + getComputedStyle(b).borderLeftColor === getComputedStyle(b).borderTopWidth + ' ' + getComputedStyle(b).borderTopColor ? '' : 'a left border of its own',
    warn: !!b.querySelector('.cl-ev .warnc') })) })"""
async def part1(b):
    print('PART 1  a failed check is a result, not a warning'); P = '1'; pg = await fresh(b, f'{BASE}?session=s011')
    got = await pg.evaluate(CLAIMS); want = claims_of('s011')
    marks = [' '.join(('held ' if m == 'held' else 'failed ') + i for i, m in c['marks']) for c in got['claims']]
    say(P, [[(i, r) for i, r in c['marks']] for c in got['claims']] == [[(i, r) for i, r in cs] for cs, _ in want] and marks == ['held C1', 'held C6', 'held C9 held C12', 'held C4 failed C7 held C8', 'failed C5'],
        f"s011 shows the sheet's marks, in the order cited: {' | '.join(marks)}")
    say(P, all(not c['stripe'] and c['full'] for c in got['claims']), "s011: no claim has a coloured stripe, and every claim's sentence is shown in full")
    tot = collections.Counter(); wrong = []; n_rep = 0
    for s in SESS:
        w = claims_of(s)
        if w is None: continue
        n_rep += 1; await go(pg, s); g = await pg.evaluate(CLAIMS); mine = [sum(k == x for _, x in w) for k in KINDS]
        if g['counts'] != ','.join(map(str, mine)) or [c['kind'] for c in g['claims']] != [k for _, k in w]: wrong.append((s, g['counts'], mine))
        tot.update(k for _, k in w)
        if s == 's006': say(P, mine == [2, 3, 1, 0, 0] and g['counts'] == '2,3,1,0,0', f"s006: {g['line']}")
    say(P, not wrong and n_rep == 15 and [tot[k] for k in KINDS] == [52, 11, 10, 8, 0] and sum(tot.values()) == 81,
        f"the {n_rep} sessions with a final report: {sum(tot.values())} claims; {tot['held']} cite held checks only, {tot['both']} held and failed, {tot['failed']} failed only, {tot['nocheck']} cite no check, {tot['none']} with no evidence; every page's line equals the count from its ledger" + (f": {wrong[:2]}" if wrong else ''))
    await go(pg, 's011')
    scripted = await pg.evaluate("""() => { const q = EV.M.claims[1], keep = [q.evidence, q.cites, q.kind]; q.evidence = []; q.cites = []; q.kind = 'none'; EV.draw(); const b = document.querySelectorAll('#s-report button.claim')[1], w = b.querySelector('.cl-ev .cm[data-kind=none]'), i = document.createElement('i'); i.style.color = 'var(--warning)'; b.appendChild(i);
      const out = { says: w ? w.textContent.trim() : null, warning_colour: !!w && getComputedStyle(w).color === getComputedStyle(i).color, line: document.getElementById('claim-counts').textContent.split(' · ').pop() };
      [q.evidence, q.cites, q.kind] = keep; EV.draw(); return out; }""")
    say(P, scripted['says'] == 'cites nothing' and not scripted['warning_colour'] and scripted['line'] == '1 cite nothing', f"a scripted claim with no evidence says so in plain words, not in the warning colour (READABLE_PAGE.md, Part 5: the counts of claims are neutral): {scripted}")
    nocheck = next((s for s in SESS if claims_of(s) and any(k == 'nocheck' for _, k in claims_of(s))), None); await go(pg, nocheck); g = await pg.evaluate(CLAIMS); c = next(c for c in g['claims'] if c['kind'] == 'nocheck')
    say(P, c['text'].startswith('no check cited') and not c['warn'], f"a claim that cites no check ({nocheck}) says so in the ordinary text colour: “{c['text'][:40]}”")
    await go(pg, 's011', '&item=C5'); await pg.wait_for_timeout(600); await signs(pg, P, 'a session with a test open')
    for name, url in (('Home', BASE), ('the Compare tab', f'{BASE}?tab=compare&brief=two-hosts-open'), ('the Operator tab', f'{BASE}?session=s011&tab=operator')):
        await pg.goto(url); await pg.wait_for_timeout(2500); await signs(pg, P, name)
    for s in ('s014', 's001'): await go(pg, s); await signs(pg, P, f'{s} (session page)')
    for s in ('s011', 's014'):
        await go(pg, s); r = await pg.evaluate("""() => { const M = EV.M, n = M.steps.length, bad = [], rk = M.repRec ? M.recStep[M.repRec.id] : Infinity; EV.s.sel = null;
          for (let k = 0; k < n; k++) { EV.s.step = k; EV.draw(); const ov = document.querySelector('#s-report [data-pr=adjust]'), shown = !!ov && !ov.classList.contains('later') && getComputedStyle(ov).visibility !== 'hidden';
            if (shown !== (k >= rk) || !!document.getElementById('s-report') !== (k >= rk)) bad.push({ k, report_shown: shown, card: !!document.getElementById('s-report'), recorded: k >= rk });
            document.querySelectorAll('#s-report .cm [data-check]').forEach(s => { if ((M.recStep[s.dataset.check] ?? 0) > k) bad.push({ k, later_check: s.dataset.check }); }); }
          EV.s.step = null; EV.draw(); return { steps: n, problems: bad.length, first: bad.slice(0, 2) }; }""")
        say(P, not r['problems'], f"replay {s}: at each of {r['steps']} steps the claims and their marks can be read only from the step of the final report, and no later check is drawn" + (f": {r['first']}" if r['problems'] else ''))
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== Part 2: the top of the session page
def void_ids(recs):
    """This script's own count of the void checks: the decision rule names two or more labels, and at least two of them are the same run of that experiment."""
    run = {(r.get('parent'), r['body'].get('label')): r['body'].get('run_id') for r in recs if r['type'] == 'simulation'}; out = set()
    for r in recs:
        if r['type'] == 'check':
            ls = list(dict.fromkeys(re.findall(r'[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)', str(r['body'].get('decision_rule') or r['body'].get('rule') or '')))); ids = [x for x in (run.get((r.get('parent'), l)) for l in ls) if x]
            if len(ls) >= 2 and len(set(ids)) < len(ids): out.add(r['id'])
    return out
def counts_of(sid):
    recs = L[sid]; n = lambda ty: sum(r['type'] == ty for r in recs); void = void_ids(recs); res = collections.Counter(r['body'].get('result') for r in recs if r['type'] == 'check' and r['id'] not in void)  # held and failed: without the void checks
    return {'turn': n('turn') or None, 'hyp': n('hypothesis'), 'check': n('check'), 'held': res['held'], 'failed': res['failed'], 'sim': n('simulation') or sum(r['type'] == 'evidence' and r['id'] != 'E0' for r in recs)}
TOP = r"""() => { const box = el => { if (!el) return null; const b = el.getBoundingClientRect(); return { top: Math.round(b.top + scrollY), bottom: Math.round(b.bottom + scrollY), width: Math.round(b.width) }; }, g = id => document.getElementById(id);
  // where the PAGE states the recommendation (the model's own sentences, in the explanation and the claims, are the report's content and are not counted)
  const w = document.createTreeWalker(document.getElementById('ev'), NodeFilter.SHOW_TEXT); let t; const says = [];
  while ((t = w.nextNode())) { const p = t.parentElement; if (!/recommend/i.test(t.textContent) || p.closest('title, option, script, style, #ev-print, #ov-expl, #ov-goal, .ov-when, .claims, #s-how') || !p.getClientRects().length) continue; const b = p.getBoundingClientRect(); if (b.top < innerHeight && b.bottom > 0) says.push(t.textContent.trim().slice(0, 60)); }
  const ex = g('ov-expl'), lh = ex ? parseFloat(getComputedStyle(ex).lineHeight) : 0;
  return { order: [...document.querySelectorAll('#ev > [id]')].map(x => x.id).filter(i => ['ev-head', 's-overview', 's-system', 's-made', 's-find'].includes(i)), answer_after_work: !!g('s-report') && !!(g('s-notebook').compareDocumentPosition(g('s-report')) & 4) && !!g('s-report').closest('#s-proposes'), card: box(g('s-report')), expl_open: g('pr-expl') ? g('pr-expl').open : null, parts: [...document.querySelectorAll('#s-report [data-pr]')].map(x => x.dataset.pr), page: document.getElementById('ev').clientWidth, tally: (() => { const q = document.querySelector('#s-made .tally'); return q ? [q.dataset.held, q.dataset.failed, q.dataset.void] : null; })(),
    goal: box(g('ov-goal')), rec: box(g('ov-rec')), exp: box(g('ov-exp')), expTop: box(g('ov-exp-top')), counts: box(g('pr-counts')), sys: box(g('s-system')), madeBox: box(g('s-made')), rep: box(g('s-report')), expl: box(ex), lines: ex ? Math.round(ex.clientHeight / lh) : null, cut: ex ? ex.scrollHeight > ex.clientHeight + 1 : null, says, intro: (document.querySelector('.ev-intro p') || {}).textContent || '',
    fields: [...document.querySelectorAll('#ev-head .hf')].map(f => ({ f: f.dataset.f, label: f.querySelector('span').textContent.trim(), value: f.querySelector('b').textContent.replace(/\s+/g, ' ').trim(), top: f.offsetTop })),
    knobs: [...document.querySelectorAll('#ov-rec .rk')].map(k => [k.dataset.knob, k.querySelector('b').textContent.trim()]), defaults: (g('ov-def') || {}).textContent || '',
    rows: [...document.querySelectorAll('#ov-exp-top tr')].map(r => [r.dataset.k, r.cells[0].firstChild.textContent.trim(), r.cells[1].textContent.trim(), (r.cells[0].querySelector('.sm') || {}).textContent || '', getComputedStyle(r.cells[1]).textAlign, getComputedStyle(r.cells[1]).fontVariantNumeric]),
    when: [...document.querySelectorAll('#s-report .ov-when > h4')].map(d => box(d)), claims: document.querySelectorAll('#s-report button.claim').length, none: (g('ov-none') || {}).textContent || null,
    made: g('gl-fold') ? { counts: g('gl-fold').dataset.counts, text: g('gl-fold').textContent.replace(/\s+/g, ' ').trim(), button: g('s-made').querySelector('button').textContent } : null,
    system: g('s-system') ? { head: g('s-system').querySelector('h2 small').textContent.replace(/\s+/g, ' ').trim(), button: g('s-system').querySelector('h2 button.noprint, h2 button[data-act=sysfold]').textContent, picture: !!g('s-system').querySelector('svg.sy, .sy-row') } : null }; }"""
REPLAY2 = r"""async () => { const M = EV.M, n = M.steps.length, bad = [], rk = M.repRec ? M.recStep[M.repRec.id] : Infinity, by = (ty, k, f) => M.recs.filter(r => r.type === ty && (M.recStep[r.id] ?? 0) <= k && (!f || f(r))).length;
  const voidOf = recs => { const run = {}, out = new Set(); recs.forEach(r => { if (r.type === 'simulation') run[r.parent + '|' + r.body.label] = r.body.run_id; });
      recs.forEach(r => { if (r.type !== 'check') return; const ls = [...new Set([...String(r.body.decision_rule || r.body.rule || '').matchAll(/[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)/g)].map(m => m[1]))], ids = ls.map(l => run[r.parent + '|' + l]).filter(Boolean); if (ls.length >= 2 && new Set(ids).size < ids.length) out.add(r.id); }); return out; }, VOID = voidOf(EV.M.recs);
  const rep = M.report || {}, words = [rep.goal, rep.explanation, rep.holds_when, rep.breaks_when].flat().filter(x => typeof x === 'string' && x.length > 12).map(x => x.slice(0, 40)), keep = [EV.glFolded, EV.store('ev-sys')];
  EV.glFolded = true; EV.store('ev-sys', '1'); EV.s.sel = { t: 'session', id: M.id };
  for (let k = 0; k < n; k++) { EV.s.step = k; EV.draw(); if (k % 20 === 19) await new Promise(r => setTimeout(r, 0));
    const top = document.getElementById('ev-head').textContent + ' ' + document.getElementById('s-proposes').textContent, f = id => document.querySelector(`#ev-head [data-f=${id}] b`), ta = document.querySelector('#s-made .tally');
    if (k < rk) { if (document.getElementById('s-report') || document.querySelector('#ev button.claim')) bad.push({ k, what: 'the overview of the report, or the card “The final report”, is drawn before its step' });
      words.forEach(x => { if (top.includes(x)) bad.push({ k, what: 'a sentence of the report before its step', x }); }); if (rk < Infinity && !/no recommendation yet/.test(f('rec').textContent)) bad.push({ k, what: 'the strip names a recommendation before the report', says: f('rec').textContent }); }
    else if (M.report && !document.getElementById('s-report')) bad.push({ k, what: 'the report is recorded and the overview or the card “The final report” does not show it' });
    if (ta && (Number(ta.dataset.held) !== by('check', k, r => r.body.result === 'held' && !VOID.has(r.id)) || Number(ta.dataset.failed) !== by('check', k, r => r.body.result === 'failed' && !VOID.has(r.id)) || Number(ta.dataset.void) !== by('check', k, r => VOID.has(r.id)))) bad.push({ k, what: 'the tally of the checks (in “The session at a glance”, since READABLE_PAGE.md) counts checks recorded later', strip: [ta.dataset.held, ta.dataset.failed] });
    const fold = document.getElementById('gl-fold'), c = fold ? fold.dataset.counts.split(',').map(Number) : [], want = [by('hypothesis', k), by('check', k), by('check', k, r => r.body.result === 'held' && !VOID.has(r.id)), by('check', k, r => r.body.result === 'failed' && !VOID.has(r.id))];
    if (document.getElementById('s-made') && (!fold || String(c.slice(1, 5)) !== String(want) || (M.recs.some(r => r.type === 'simulation') && c[5] !== by('simulation', k)) || (M.recs.some(r => r.type === 'turn') && c[0] !== by('turn', k)))) bad.push({ k, what: 'the folded line counts something recorded later', line: c, records: want });   /* the glance's folded line, where the glance is drawn (it is not, since 2026-11-22) */
    const kv = document.getElementById('sum-kv'); if (kv && k < n - 1 && /duration|model calls|replies cut off/.test(kv.textContent)) bad.push({ k, what: 'the summary shows a figure written at the end of the session' }); }
  EV.s.step = null; EV.s.sel = null; EV.glFolded = !!keep[0]; EV.store('ev-sys', keep[1] || '0'); EV.draw(); return { steps: n, report_at: rk === Infinity ? null : rk, problems: bad.length, first: bad.slice(0, 3) }; }"""
async def part2(b):
    print('PART 2  the top of the session page'); P = '2'; pg = await fresh(b, f'{BASE}?session=s011'); t = await pg.evaluate(TOP)
    MB = lambda q: q['madeBox'] or {'top': q['sys']['bottom'], 'bottom': q['sys']['bottom']}  # “The session at a glance” is not drawn since 2026-11-22: a box of no height where it stood
    # READABLE_PAGE.md replaces decision 1 of PAGE_POLISH.md ("the Overview comes first"): the page now shows the question before the answer.
    # At full width, in this order: the header strip, the setting, the session at a glance, what it needed to find out; the answer (the band that was the Overview) stands after the notebook, in "What it proposes".
    say(P, t['order'] == ['ev-head', 's-system'] + (['s-made'] if t['madeBox'] else []) + ['s-find'] and t['answer_after_work'], f"the order at full width (READABLE_PAGE.md, in place of “the Overview comes first”): {t['order']}; the band of the answer stands after the notebook, in “What it proposes”: {t['answer_after_work']}")
    # 2026-11-17, the operator: blocks 2 to 7 of "The setting" are hidden altogether or shown in full. As the page comes it shows the network alone, and that is
    # what has to stand on the first screen; shown in full (as every other line of this check opens it) the seven blocks may end below it.
    pg0 = await fresh(b, f'{BASE}?session=s011', setall='0'); t0 = await pg0.evaluate(TOP); await pg0.context.close()
    first = t0['sys']['bottom'] <= 900 and MB(t0)['top'] >= t0['sys']['bottom'] and t['goal']['top'] > MB(t)['bottom']  # the top of "The session at a glance" on the first screen is checked at 1500 x 1000, the window READABLE_PAGE.md names (ev_readable.py, part 1)
    say(P, first, f"s011, first visit, 1440 x 900: on the first screen is “The setting” as the page comes, the network alone (ends at {t0['sys']['bottom']} px; with its seven blocks shown in full it ends at {t['sys']['bottom']}); “The session at a glance” follows (starts at {MB(t0)['top']}); the goal, the recommended settings, the expected result and the claims in numbers come after the work (the goal starts at {t['goal']['top']} px); the explanation is in “The final report” (starts at {t['expl']['top']}, {t['lines']} lines shown)")
    say(P, len(t['says']) <= 2 and 'recommend' not in t['intro'].lower(), f"the page states the recommendation on the first screen {len(t['says'])} times: {t['says']} (the model's own sentences in the explanation and the claims are not counted)")
    say(P, t['expl_open'] is False and t['parts'] == ['aim', 'adjust', 'expected', 'because', 'but', 'explanation'], f"the final report reads as one argument ({t['parts']}); its explanation is folded (READABLE_PAGE.md, Part 5, in place of “six lines, then more”)")
    f = {x['f']: x for x in t['fields']}
    say(P, [x['label'] for x in t['fields']] in (['Brief', 'Session', 'How it ended', 'Simulations', 'Recommends', 'Detail'], ['Brief', 'Session', 'How it ended', 'Simulations', 'Recommends', 'Detail', 'Walk']) and len({x['top'] for x in t['fields']}) == 1 and f['rec']['value'] == 'ratio 0.303' and f['sims']['value'] == '39 of 40' and (t['tally'] == ['10', '2', '0'] or not t['madeBox']),
        f"the header strip (READABLE_PAGE.md, Part 2: brief, session, how it ended, simulations used, the recommendation in one line, the switch): {[(x['label'], x['value']) for x in t['fields']]}; the checks' tally stands in “The session at a glance”: held, failed, void = {t['tally']}")
    brief = json.loads((ROOT / 'briefs' / 'two-hosts-udp-demand.json').read_text()); dflt = {k: v.get('default') for k, v in brief['knobs'].items()}
    say(P, dflt == {'weightUdp': 0.5, 'queuePkts': 100, 'tcpVariant': 'TcpCubic', 'duration': 10, 'seed': 1} and t['knobs'] == [['weightUdp', '0.5 → 0.303']] and all(w in t['defaults'] for w in ('100', 'Cubic', '10', '1')) and t['defaults'].startswith("everything else unchanged:"),
        f"decision 3 (yes): the brief's defaults are {dflt}; the recommendation differs in {t['knobs']}; then “{t['defaults']}”")
    rows = {r[0]: r for r in t['rows']}; want = {'tcp_goodput_bps': ('671.5 Mbps',), 'udp_loss_frac': ('0.009815', '0.9815 %')}  # the fraction is written in per cent since Part 7
    rep11 = next(r for r in L['s011'] if r['type'] == 'report')['body']['expected']
    say(P, list(rows) == ['tcp_goodput_bps', 'udp_loss_frac'] and all(rows[k][2] in want[k] for k in rows) and all(r[4] == 'right' and 'tabular-nums' in r[5] for r in rows.values())
        and ('udp_loss_frac <= 0.01' in rows['udp_loss_frac'][3] or 'UDP loss <= 1 %' in rows['udp_loss_frac'][3]), f"the expected result in short (the target's measure and the one the condition names; the other {len(rep11) - 2 - len(set(rep11) & {'link_rate_bps', 'weight_udp'})} are in the full final report), name left and value right, in tabular figures: {[(r[1], r[2]) for r in t['rows']]}; beside UDP loss: “{rows['udp_loss_frac'][3]}”")
    say(P, len(t['when']) == 2 and t['when'][0]['top'] < t['when'][1]['top'] and t['claims'] == 5 and t['rep']['top'] >= MB(t)['bottom'], f"in “What it proposes” (the report starts at {t['rep']['top']} px, after the work): the {t['claims']} claims, then when it holds ({t['when'][0]['top']} px) and when it breaks ({t['when'][1]['top']} px)")
    y = await pg.evaluate("async () => { window.scrollTo(0, document.getElementById('pr-expl').getBoundingClientRect().top + scrollY - 400); const y = scrollY; document.querySelector('#pr-expl summary').click(); await new Promise(r => setTimeout(r, 150)); const ex = document.getElementById('ov-expl'); return [y, scrollY, document.getElementById('pr-expl').open && ex.getClientRects().length > 0]; }")
    say(P, y[0] == y[1] and y[2], f"a click on “The explanation” shows the whole explanation and the page does not move: {y}"); await pg.evaluate("() => { document.querySelector('#pr-expl summary').click(); window.scrollTo(0, 0); }")
    # a folded card's line carries its content
    await pg.evaluate("() => { EV.glFolded = true; EV.store('ev-sys', '1'); EV.draw(); }"); t = await pg.evaluate(TOP); c = counts_of('s011')
    if not t['made']: print('   skipped: the folded line of “The session at a glance” (the card is not drawn since 2026-11-22)')
    else: say(P, t['made']['counts'] == '5,12,12,10,2,44' and t['made']['text'] == '5 turns · 12 hypotheses · 12 checks, 10 2 · 44 simulations' and t['made']['button'] == 'unfold', f"folded, “What this session is made of” says: {t['made']['text']} (the two figures after “checks,” stand beside the drawn signs of held and failed)")
    say(P, 'folded' not in t['system']['head'] and t['system']['head'].startswith("the picture shows the brief's defaults") and t['system']['button'] == 'unfold' and not t['system']['picture'], f"folded, “The setting” says what its heading says, without the word “folded”: “{t['system']['head']}”")
    wrong = []; GL = t['made'] is not None
    for s in (SESS if GL else []):
        await go(pg, s); await pg.evaluate("() => { EV.glFolded = true; EV.draw(); }"); g = await pg.evaluate("() => ({ c: document.getElementById('gl-fold').dataset.counts.split(',').map(Number), turns: EV.M.turns.filter(q => q.n > 0).length, text: document.getElementById('gl-fold').textContent })"); w = counts_of(s)
        if g['c'][1:] != [w['hyp'], w['check'], w['held'], w['failed'], w['sim']] or g['c'][0] != (w['turn'] if w['turn'] is not None else g['turns']) or (not w['check'] and 'not recorded' not in g['text'] and '0 checks' not in g['text']): wrong.append((s, g['c'], w))
    say(P, not wrong, f"the folded line's counts equal the ledger's in all {len(SESS)} sessions{'' if GL else ' (skipped: the glance is not drawn since 2026-11-22)'}" + (f": {wrong[:3]}" if wrong else ''))
    await go(pg, 's011'); await pg.evaluate("() => { EV.glFolded = true; EV.draw(); }"); await signs(pg, P, 's011 with both cards folded')
    # a session without a final report; the session's summary
    await pg.evaluate("() => { EV.store('ev-sys', '0'); }"); await go(pg, 's007'); t = await pg.evaluate(TOP); f = {x['f']: x for x in t['fields']}
    say(P, t['none'] and t['none'].startswith('No final report.') and '3 turns in a row without a usable answer' in t['none'] and f['rec']['value'] == 'no recommendation' and not t['claims'], f"a session without a final report (s007) says: “{t['none']}”; the strip: Recommends “{f['rec']['value']}”")
    await go(pg, 's011', '&item=session:s011'); kv = await pg.evaluate("() => [...document.querySelectorAll('#sum-kv > div > span')].map(s => s.textContent.trim())"); more = await pg.evaluate("() => ({ seq: !!document.querySelector('#p-detail .sq, #p-detail [id^=sq]'), vc: !!document.querySelector('#p-detail table.vc') })")
    say(P, kv and kv[0] == 'model' and not any(re.search(r'simulations|how it ended', k) for k in kv) and more['vc'], f"the session's summary does not repeat the strip (simulations used, how it ended) and names the model, which left the strip with READABLE_PAGE.md: its fields are {kv}; it keeps the checks in order and the verdicts against checks: {more}")
    await pg.evaluate("() => { EV.s.op = true; EV.draw(); }"); t = await pg.evaluate(TOP)
    labs = [x['label'] for x in t['fields']]; i_op = labs.index('Scheduling policy') if 'Scheduling policy' in labs else -9
    say(P, labs[i_op:i_op + 3] == ['Scheduling policy', 'Gap to the best', 'Detail'] and len({x['top'] for x in t['fields']}) == 1, f"with the operator columns on the strip adds, before the Brief / Full switch: {[(x['label'], x['value']) for x in t['fields']][i_op:i_op + 2]}"); await pg.evaluate("() => { EV.s.op = false; EV.draw(); }")
    for s in ('s011', 's014', 's007'):
        await go(pg, s); r = await pg.evaluate(REPLAY2)
        say(P, not r['problems'], f"replay {s}: at each of {r['steps']} steps nothing of the report is shown before its step ({r['report_at']}), the strip and a folded line count only what was recorded by that step, the summary shows no end-of-session figure" + (f": {r['first']}" if r['problems'] else ''))
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== Part 3: the detail pane fits its width
WIDE = r"""() => { const side = document.querySelector('.ev-side'), p = document.getElementById('p-detail'), bad = [], name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.getAttribute('class') ? '.' + el.getAttribute('class').trim().split(/\s+/)[0] : '');
  [side, ...side.querySelectorAll('*')].forEach(el => { if (el.tagName === 'svg' || el.tagName === 'CANVAS') { const w = el.getBoundingClientRect().width, c = el.parentElement.clientWidth; if (c && w > c + 1) bad.push({ el: name(el), room: c, content: Math.round(w) }); return; }
    if (el instanceof SVGElement || !el.clientWidth) return; if (el.scrollWidth > el.clientWidth + 1) bad.push({ el: name(el), room: el.clientWidth, content: el.scrollWidth }); });
  const fl = p.querySelector('.t-flow, .ev-scroll'), sv = fl && fl.querySelector('svg'), tb = p.querySelector('table.tt') || [...p.querySelectorAll('h3')].filter(h => /simulations this rule names/i.test(h.textContent)).map(h => h.parentElement.querySelector('table'))[0];
  const ys = sv ? [...new Set([...sv.querySelectorAll('rect.bx, polygon.bx')].map(r => Math.round(r.getBBox().y / 10)))].length : 0, clipped = sv ? [...sv.querySelectorAll('rect.bx, polygon.bx')].filter(r => r.getBBox().x + r.getBBox().width > sv.getBoundingClientRect().width + 1).length : 0;
  return { pane: p.clientWidth, elements: side.querySelectorAll('*').length, bad: bad.slice(0, 6), n_bad: bad.length, flow: fl ? { room: fl.clientWidth, content: Math.max(fl.scrollWidth, sv ? Math.round(sv.getBoundingClientRect().width) : 0), boxes: sv ? sv.querySelectorAll('rect.bx, polygon.bx').length : 0, rows: ys, clipped } : null,
    table: tb ? { room: tb.parentElement.clientWidth, content: Math.max(tb.scrollWidth, Math.round(tb.getBoundingClientRect().width)), rows: tb.tBodies[0].rows.length, columns: tb.tHead.rows[0].cells.length, sims: [...tb.querySelectorAll('[data-t=sim]')].map(a => a.dataset.id) } : null,
    hyp_box: sv ? (sv.querySelector('g[data-t=hyp] .bt') || {}).textContent : null, rule_lines: (() => { const s = sv && sv.querySelector('small.lc2'); return s ? Math.round(s.clientHeight / parseFloat(getComputedStyle(s).lineHeight)) : null; })(),
    above: (() => { const h = EV.M.hypById[(EV.M.testById[(p.querySelector('.t-flow') || { dataset: {} }).dataset.test] || {}).hyp]; return !!h && p.textContent.indexOf(h.text) >= 0 && p.textContent.indexOf(h.text) < p.textContent.indexOf('did the rule hold?'); })(), rule_full: !!p.querySelector('code') }; }"""
async def part3(b):
    print('PART 3  the detail pane fits its width'); P = '3'
    cases = [('s011', 'C5'), ('s011', 'C9'), ('s006', None), ('s014', None)]  # None: the test with the most simulations of that session
    for w in (1440, 1024):
        pg = await fresh(b, f'{BASE}?session=s011', w=w)
        for sid, item in cases:
            await go(pg, sid, f'&item={item}' if item else '')
            if not item: item = await pg.evaluate("() => { const T = EV.M.tests.reduce((a, q) => (q.sims.length > a.sims.length ? q : a)); EV.s.sel = { t: 'test', id: T.id }; EV.draw(); return (T.check ? T.check.id : T.id) + ', the test with the most simulations (' + T.sims.length + ')'; }")
            await pg.wait_for_timeout(700); r = await pg.evaluate(WIDE); T = await pg.evaluate("() => { const T = EV.M.testById[(EV.s.sel || {}).id]; return T ? { sims: T.sims.map(q => q.id), rule: T.rule } : null; }")
            ok = T and not r['n_bad'] and r['flow'] and r['flow']['content'] <= r['flow']['room'] + 1 and not r['flow']['clipped'] and r['flow']['boxes'] == 7 and r['table'] and r['table']['content'] <= r['table']['room'] + 1 and r['table']['sims'] == T['sims'] and r['table']['rows'] == len(T['sims'])
            say(P, ok, f"{w} px wide · {sid} {item}: pane {r['pane']} px; of its {r['elements']} elements {r['n_bad']} have content wider than themselves; the flow chart {r['flow']['content']} px in {r['flow']['room']} ({r['flow']['boxes']} boxes in {r['flow']['rows']} row{'s' if r['flow']['rows'] != 1 else ''}); the table {r['table']['content']} px in {r['table']['room']}, {r['table']['rows']} rows (one per simulation) by {r['table']['columns']} columns" + (f": {r['bad']}" if r['n_bad'] else ''))
            if (sid, item, w) == ('s011', 'C5', 1440):
                say(P, ''.join(r['hyp_box'].split()) == 'H5refuted' and r['above'] and r['rule_lines'] <= 2 and r['rule_full'], f"the hypothesis box shows the id and the state only (“{r['hyp_box'].strip()}”), its text stands above the chart; the decision-rule box shows {r['rule_lines']} lines, the rule in full stays below")
        say(P, not pg.errs, f"script errors at {w} px: {pg.errs[:3] or 'none'}"); await pg.context.close()
    # under 700 px the chart continues on a second row; nothing is cut off; a click in it does not move the page
    for w in (1150, 760, 560):
        pg = await fresh(b, f'{BASE}?session=s011&item=C5', w=w); await pg.wait_for_timeout(500); r = await pg.evaluate(WIDE)
        say(P, r['flow']['content'] <= r['flow']['room'] + 1 and not r['flow']['clipped'] and r['flow']['boxes'] == 7 and r['flow']['rows'] >= 2 and not r['n_bad'], f"{w} px wide: the chart has {r['flow']['room']} px and continues over {r['flow']['rows']} rows, all {r['flow']['boxes']} boxes inside it; {r['n_bad']} elements of the pane wider than themselves" + (f": {r['bad'][:3]}" if r['n_bad'] else ''))
        await pg.context.close()
    pg = await fresh(b, f'{BASE}?session=s011&item=C5'); await pg.evaluate("() => window.scrollTo(0, 400)")
    moved = await pg.evaluate("""async () => { const y = scrollY, out = []; for (const q of ['.t-flow g[data-t=sim]', '.t-flow g[data-t=hyp]']) { EV.s.sel = EV.selOf(EV.M, 'C5'); EV.s.inset = null; EV.draw(); const g = document.querySelector(q); g.dispatchEvent(new MouseEvent('click', { bubbles: true })); await new Promise(r => setTimeout(r, 150)); out.push([q, EV.s.sel.t === 'test' && EV.s.inset ? EV.s.inset.t : EV.s.sel.t, scrollY === y]); } return out; }""")
    say(P, all(m[2] for m in moved) and [m[1] for m in moved] in (['sim', 'hyp'], ['sim', 'test']), f"a click on a box of the chart opens its item and the page does not move: {moved}")
    for s, item in (('s011', 'C5'), ('s014', None)):
        await go(pg, s, f'&item={item}' if item else '')
        if not item: item = await pg.evaluate("() => { const T = EV.M.tests.reduce((a, q) => (q.sims.length > a.sims.length ? q : a)); EV.s.sel = { t: 'test', id: T.id }; EV.draw(); return T.check ? T.check.id : T.id; }")
        r = await pg.evaluate("""async () => { const M = EV.M, n = M.steps.length, bad = [], T = M.testById[EV.s.sel.id], k0 = M.recStep[T.exp] ?? 0, kc = T.check ? M.recStep[T.check.id] : Infinity, kv = T.verdict ? M.recStep[T.verdict.id] : Infinity;
          const vis = el => !!el && !el.closest('.later') && getComputedStyle(el).visibility !== 'hidden';
          for (let k = k0; k < n; k++) { EV.s.step = k; EV.draw(); if (k % 20 === 19) await new Promise(r => setTimeout(r, 0)); const sv = document.querySelector('.t-flow svg'); if (!sv) { bad.push({ k, what: 'no chart' }); continue; }
            const res = [...sv.querySelectorAll('g')].find(g => g.querySelector('polygon')), ver = [...sv.querySelectorAll('g[data-by=model]')].find(g => /next/.test(g.textContent) && !/decision rule/.test(g.textContent));
            if (vis(res.querySelector('text')) !== (k >= kc)) bad.push({ k, what: 'the check can be read before its step, or not after it' }); if (vis(ver.querySelector('.bt')) !== (k >= kv)) bad.push({ k, what: 'the verdict’s next step can be read before its step, or not after it' });
            document.querySelectorAll('#p-detail table.tt tr[data-sim]').forEach(tr => { if ((M.recStep[tr.dataset.sim] ?? 0) > k && vis(tr)) bad.push({ k, what: 'a later simulation in the table', id: tr.dataset.sim }); }); }
          EV.s.step = null; EV.draw(); return { from: k0, steps: n, problems: bad.length, first: bad.slice(0, 3) }; }""")
        say(P, not r['problems'], f"replay {s} {item}: from the step of its experiment ({r['from']}) to the last ({r['steps'] - 1}), the check and the verdict of the chart can be read only from their own steps, and the table shows no later simulation" + (f": {r['first']}" if r['problems'] else ''))
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== Part 4: type sizes and labels
TEXTS = r"""() => { const out = [], seen = new Set(), w = document.createTreeWalker(document.getElementById('ev'), NodeFilter.SHOW_TEXT); let t;
  while ((t = w.nextNode())) { const p = t.parentElement; if (!t.textContent.trim() || seen.has(p) || p.closest('title, option, script, style, #ev-print')) continue; const cs = getComputedStyle(p);
    if (cs.display === 'none' || cs.visibility === 'hidden' || !p.getClientRects().length) continue; seen.add(p);
    out.push({ px: Math.round(parseFloat(cs.fontSize) * 100) / 100, svg: p instanceof SVGElement, caps: cs.textTransform !== 'none', spaced: !['normal', '0px'].includes(cs.letterSpacing), text: t.textContent.trim().slice(0, 28) }); }
  const named = ['--f-note', '--f-sec', '--f-text', '--f-card', '--f-page'].map(n => parseFloat(getComputedStyle(document.getElementById('ev')).getPropertyValue(n)));
  const nums = [...document.querySelectorAll('#ev td.num, #ev .hf > b, #ev .kv b, #ev .rk > b, #ev .mg-n')].filter(e => e.getClientRects().length && /\d/.test(e.textContent)), plain = nums.filter(e => !getComputedStyle(e).fontVariantNumeric.includes('tabular-nums'));
  return { texts: out, named, numbers: nums.length, not_tabular: plain.length, first_plain: plain.slice(0, 3).map(e => e.textContent.trim().slice(0, 20)) }; }"""
async def part4(b):
    print('PART 4  type sizes and labels'); P = '4'
    views = [('Home', BASE, None), ("a session's page with a test open", f'{BASE}?session=s011&item=C5', None), ('the Operator tab', f'{BASE}?session=s011&tab=operator', None), ('the Compare tab', f'{BASE}?tab=compare&brief=two-hosts-udp-demand', None),
             ('a simulation open, session flow', f'{BASE}?session=s011&item=S20', "EV.s.left = 'lanes'; EV.draw()"), ('an experiment open, hypothesis map', f'{BASE}?session=s014&item=X5', "EV.s.left = 'map'; EV.draw()"),
             ('the final report open, operator columns', f'{BASE}?session=s006&item=report', "EV.s.op = true; EV.draw()"), ('a session of the first format', f'{BASE}?session=s001', None)]
    for name, url, pre in views:
        pg = await fresh(b, url); await pg.wait_for_timeout(900)
        if pre: await pg.evaluate(f"() => {{ {pre} }}"); await pg.wait_for_timeout(900)
        r = await pg.evaluate(TEXTS); tx = r['texts']; c = collections.Counter(x['px'] for x in tx); small = [x for x in tx if x['px'] < 12]; caps = [x for x in tx if x['caps'] or x['spaced']]
        say(P, len(c) <= 5 and set(c) <= set(r['named']) and not small and not caps and not r['not_tabular'] and not pg.errs,
            f"{name}: {len(tx)} texts ({sum(x['svg'] for x in tx)} in pictures) in {len(c)} sizes {sorted(int(k) if k == int(k) else k for k in c)} px; under 12 px (READABLE_PAGE.md: small text at least 12 px): {len(small)}; set in capitals or letter-spaced by a style: {len(caps)}; {r['numbers']} numbers of columns and lists, not in tabular figures: {r['not_tabular']}"
            + (f" · {[(x['px'], x['text']) for x in small[:3]]} {[x['text'] for x in caps[:3]]} {r['first_plain']} {pg.errs[:1]}" if small or caps or r['not_tabular'] or pg.errs else ''))
        await pg.context.close()
    # the sizes are named once, in index.html, and no file sets a size, capitals or letter spacing of its own
    V = ROOT / 'viewer'; html = (V / 'index.html').read_text(); files = [f for f in sorted(V.glob('evidence*.js'))]
    named = re.findall(r'--f-(\w+): (\d+)px', html); own = re.findall(r'font(?:-size)?: ?[\d.]+px', html) + [f"{f.name}: {m}" for f in files for m in re.findall(r'font-size: ?[\d.]+(?:px)?|font-size="[\d.]+"', f.read_text())]
    caps = re.findall(r'text-transform: ?(?!none)\w+|letter-spacing: ?[^;"\']+', html) + [f"{f.name}: {m}" for f in files for m in re.findall(r'text-transform: ?\w+|letter-spacing: ?[^;"\']+', f.read_text())]
    say(P, named == [('note', '12'), ('sec', '13'), ('text', '14'), ('card', '16'), ('page', '20')] and not own and not caps, f"index.html names five sizes once, {', '.join(f'{k} {v} px' for k, v in named)}; sizes set anywhere else: {own or 'none'}; capitals or letter spacing set by a style: {caps or 'none'}")
    pg = await fresh(b, f'{BASE}?session=s011&item=C5'); labels = await pg.evaluate("() => [...document.querySelectorAll('#ev h3, #ev .cap')].filter(e => e.getClientRects().length).map(e => e.textContent.trim().slice(0, 34))")
    low = [l for l in labels if re.match(r'[a-z]', l)]
    say(P, len(labels) >= 14 and not low, f"the {len(labels)} labels are in sentence case: {labels[:16]}" + (f" · begin with a small letter: {low}" if low else ''))
    over = await pg.evaluate("""() => { const bad = []; document.querySelectorAll('#s-system svg.sy, #s-how svg').forEach(sv => { const w = sv.getBoundingClientRect(); sv.querySelectorAll('foreignObject > div').forEach(d => { if (d.scrollHeight > d.clientHeight + 2) bad.push(d.textContent.trim().slice(0, 40)); }); }); return bad; }""")
    say(P, not over, f"no label of a box in “The system” or in “How to read this page” runs out of its box at 11 px" + (f": {over}" if over else ''))
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== Part 5: hints and definitions
TERMS = r"""() => { const defs = new Set(Object.values(EV_DEF)), all = [...document.querySelectorAll('#ev abbr:not(.st-l):not([title*="field:"]):not(.st-lists abbr)')].filter(a => a.getClientRects().length),  /* a setting's or a measure's label with its own hover (READABLE_PAGE.md) is not one of the fourteen defined terms */ ul = a => getComputedStyle(a).textDecorationLine.includes('underline');
  const label = a => { const p = a.parentElement; return !p.closest('small, .sm') && (['H2', 'H3', 'TH', 'LABEL'].includes(p.tagName) || p.matches('.hf > span, .kv div > span, .bt, .bt > b')); };  // a label: a heading, a column title, a form's or a field's label, a box's label
  const hints = [...document.querySelectorAll('#ev h2 small, #ev h3 .sm')].filter(s => s.getClientRects().length && !s.closest('#s-how') && /\b(click|point at|tick two|hover)\b/i.test(s.textContent)).map(s => s.textContent.trim().slice(0, 60));
  return { terms: all.length, underlined: all.filter(ul).length, first_screen: all.filter(a => ul(a) && a.getBoundingClientRect().top < innerHeight && a.getBoundingClientRect().bottom > 0).length, in_a_sentence: all.filter(a => ul(a) && !label(a)).map(a => a.parentElement.textContent.trim().slice(0, 50)),
    labels_without: all.filter(a => !ul(a) && label(a) && !a.closest('.gl')).length, no_definition: all.filter(a => !defs.has(a.title)).map(a => a.textContent), help: all.every(a => getComputedStyle(a).cursor === 'help'), hints }; }"""
async def part5(b):
    print('PART 5  hints and definitions'); P = '5'; pg = await fresh(b, f'{BASE}?session=s011'); r = await pg.evaluate(TERMS)
    say(P, not r['in_a_sentence'] and not r['no_definition'] and r['help'], f"s011, first visit: {r['terms']} defined terms, every one shows its definition on hover; {r['underlined']} have the dotted underline (all of them labels: a heading, a column title, a field's or a box's label), {r['first_screen']} of them on the first screen; underlined inside a sentence: {len(r['in_a_sentence'])}" + (f" {r['in_a_sentence'][:3]} {r['no_definition'][:3]}" if r['in_a_sentence'] or r['no_definition'] else ''))
    say(P, not r['hints'], f"s011: no grey line beside a heading tells the reader how to operate the card" + (f": {r['hints']}" if r['hints'] else ''))
    views = [('a test open', "EV.s.sel = EV.selOf(EV.M, 'C5')"), ('a simulation open', "EV.s.sel = { t: 'sim', id: 'S20' }"), ('an experiment open', "EV.s.sel = { t: 'exp', id: 'X2' }"), ('a turn open, session flow', "EV.s.sel = { t: 'log', id: 2 }; EV.s.left = 'lanes'"),
             ('the final report open, hypothesis map', "EV.s.sel = { t: 'report', id: 'report' }; EV.s.left = 'map'"), ('the brief open, operator columns', "EV.s.sel = { t: 'brief', id: 'brief' }; EV.s.op = true"), ('the summary open', "EV.s.sel = { t: 'session', id: EV.M.id }; EV.s.op = false; EV.s.left = 'tree'")]
    tot = 0
    for name, pre in views:
        await pg.evaluate(f"() => {{ {pre}; EV.draw(); }}"); await pg.wait_for_timeout(500); r = await pg.evaluate(TERMS); tot += r['terms']
        if r['in_a_sentence'] or r['no_definition'] or r['hints'] or not r['help']: say(P, False, f"s011, {name}: {r['in_a_sentence'][:3]} {r['no_definition'][:3]} {r['hints'][:3]}")
    say(P, True, f"s011 with a test, a simulation, an experiment, a turn, the final report, the brief and the summary open in turn ({tot} terms read): what did not pass is listed above, if anything")
    for name, url in (('Home', BASE), ('the Compare tab', f'{BASE}?tab=compare&brief=two-hosts-udp-demand'), ('the Operator tab', f'{BASE}?session=s011&tab=operator'), ('s014', f'{BASE}?session=s014'), ('s001', f'{BASE}?session=s001')):
        await pg.goto(url); await pg.wait_for_timeout(2500); r = await pg.evaluate(TERMS)
        say(P, not r['in_a_sentence'] and not r['no_definition'] and not r['hints'], f"{name}: {r['terms']} terms, {r['underlined']} underlined, none inside a sentence; no operating hint beside a heading" + (f": {r['in_a_sentence'][:3]} {r['no_definition'][:3]} {r['hints'][:3]}" if r['in_a_sentence'] or r['no_definition'] or r['hints'] else ''))
    await go(pg, 's011'); use = await pg.evaluate("() => { const u = document.getElementById('how-use'); return u ? { open: u.closest('details').open, n: u.querySelectorAll('li').length, text: u.textContent.replace(/\\s+/g, ' ') } : null; }")
    moved = ['click a row to go to its card in the notebook', 'click a line to open that view', 'click a dot to open that simulation', 'click an object to see its settings beside the picture', 'click a mark to open it', 'point at a mark to read what it is', 'click an item or a row to open it', 'click any item on the left', 'click a row to open that session', 'click a column title to sort', 'tick two or more', 'point at a chart']
    say(P, use and all(m in use['text'] for m in moved), f"“How to read this page” holds the moved sentences ({use['n'] if use else 0} lines under “Using the page”)" + ('' if use and all(m in use['text'] for m in moved) else f": missing {[m for m in moved if not use or m not in use['text']]}"))
    # what can be clicked shows the pointer and a change of background under it
    async def hov(sel, prop='backgroundColor', of='e', pick=0):
        """Move the mouse onto the pick-th element of sel: its cursor must be the pointer, and prop of the element `of` (a JS expression of e) must change."""
        els = await pg.query_selector_all(sel)
        if not els: return (sel, 'not on the page')
        el = els[pick if pick >= 0 else len(els) // 2]; await pg.mouse.move(2, 2); await el.evaluate("e => e.scrollIntoView({ block: 'center' })"); await pg.wait_for_timeout(80)
        get = f"e => [getComputedStyle({of}).{prop}, getComputedStyle(e).cursor, (e.closest('[data-act], tr, li, button') || e).matches(':hover')]"
        before = await el.evaluate(get); box = await el.bounding_box()
        if box is None:   # the list was drawn again between the two lines (the first poll after loading): take the element as it is now
            await pg.wait_for_timeout(1500); el = (await pg.query_selector_all(sel))[pick if pick >= 0 else len(els) // 2]; await el.evaluate("e => e.scrollIntoView({ block: 'center' })"); await pg.wait_for_timeout(80); before = await el.evaluate(get); box = await el.bounding_box()
        await pg.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2); await pg.wait_for_timeout(150); after = await el.evaluate(get)
        return (sel, True if before[0] != after[0] and after[1] == 'pointer' and after[2] else f'before {before} after {after}')
    await pg.evaluate("() => window.scrollTo(0, 0)")
    res = [await hov('#s-made a.gm'), await hov('#s-made .gt'), await hov('#s-tests tr.pick:not(.grp) td', of='e'), await hov('#s-notebook .nb-card'), await hov('#s-find tr.pick td', of='e'), await hov('#s-closer .lc-row button'),
           await hov('#s-best g[data-act=open] circle', 'fill', pick=-1), await hov('#s-knob g[data-act=open] circle', 'fill', pick=-1), await hov('#s-report button.claim'), await hov('#s-system svg.sy g[data-act] .bx', 'filter')]
    await pg.goto(BASE); await pg.wait_for_timeout(2000); res.append(await hov('#home-rows tr td'))
    res = [q for q in res if not (q[0].startswith('#s-made') and q[1] == 'not on the page')]  # the glance is not drawn since 2026-11-22
    say(P, all(ok is True for _, ok in res), f"a mark, a turn's name, a row of the tests list, a card of the notebook, a row of “What it needed to find out”, a line of “Looking closer”, a dot of each chart, a claim, an object of the system and a row of Home show the pointer and a change under it: {res}")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== Part 6: the Operator tab
import csv, subprocess
def sweep_figures(sw, target='tcp_goodput_bps', cond=('udp_loss_frac', 0.01), kx='weightUdp', ky='queuePkts'):
    """From the sweep's table itself: the cells, those that meet the condition, their best values, and the stretches of the axis across."""
    rows = list(csv.DictReader(open(ROOT / 'checks' / 'sweeps' / sw / 'table.csv'))); cell = {}
    for r in rows:
        if r.get('error') or r[target] == '' or float(r[cond[0]]) > cond[1]: continue
        k = (r[kx], r[ky]); cell[k] = max(cell.get(k, -1e99), float(r[target]))
    X = sorted({r[kx] for r in rows}, key=float); Y = {r[ky] for r in rows}; v = list(cell.values()); hi = max(v)
    d = [float(f"{float(X[i]) - float(X[i - 1]):.6g}") for i in range(1, len(X))]; ends = [i for i in range(1, len(d)) if d[i] != d[i - 1]]   # after column i the step changes
    return {'cells': len(X) * len(Y), 'meet': len(v), 'lo': round(min(v) / 1e6, 3), 'hi': round(hi / 1e6, 3), 'within': sum(x >= 0.99 * hi for x in v), 'X': X, 'ends': ends, 'steps': [d[0]] + [d[i] for i in ends]}
HEAT = r"""async () => { for (let i = 0; i < 120 && !document.getElementById('heat'); i++) await new Promise(r => setTimeout(r, 250)); const h = document.getElementById('heat'); if (!h) return null;
  const cells = [...h.querySelectorAll('rect.cell')], fills = c => { const o = {}; c.forEach(q => { const f = q.getAttribute('fill'); o[f] = (o[f] || 0) + 1; }); return o; }, xs = [...new Set(cells.map(c => +c.getAttribute('x')))].sort((a, b) => a - b), cw = +cells[0].getAttribute('width');
  const marks = [...h.querySelectorAll('g.hm')].map(g => { const c = g.querySelector('circle'); return { x: +c.getAttribute('cx'), y: +c.getAttribute('cy'), r: +c.getAttribute('r'), n: Number(g.dataset.n || 1), many: g.classList.contains('many') }; });
  const over = []; marks.forEach((a, i) => marks.slice(i + 1).forEach(b => { if (Math.hypot(a.x - b.x, a.y - b.y) < a.r + b.r) over.push([a, b]); }));
  const lb = document.getElementById('heat-best-label').getBBox(), covered = marks.filter(m => m.x + m.r > lb.x && m.x - m.r < lb.x + lb.width && m.y + m.r > lb.y && m.y - m.r < lb.y + lb.height).length;
  const hv = v => v !== '' && +v, with1 = cells.filter(c => c.dataset.v !== '');
  return { range: h.dataset.range, cells: +h.dataset.cells, meet: +h.dataset.meet, lo: +(+h.dataset.lo).toFixed(3), hi: +(+h.dataset.hi).toFixed(3), within: +h.dataset.within, fills: fills(with1), steps_used: Object.keys(fills(with1)).length, palest: with1.filter(c => c.getAttribute('fill') === '#cde2fb').length,
    below99: with1.filter(c => +c.dataset.v < 0.99 * Math.max(...with1.map(q => +q.dataset.v))).length, below99_not_palest: with1.filter(c => +c.dataset.v < 0.99 * Math.max(...with1.map(q => +q.dataset.v)) && c.getAttribute('fill') !== '#cde2fb').length,
    key: document.getElementById('heat-key').textContent.replace(/\s+/g, ' ').trim(), on: [...document.querySelectorAll('#heat-range button.on')].map(b => b.textContent), gaps_after: xs.map((x, i) => (i && x - xs[i - 1] > cw ? i - 1 : null)).filter(i => i != null),
    printed: [...h.querySelectorAll('text.hx')].map(t => t.textContent), brackets: [...h.querySelectorAll('path.hs')].map(p => [+p.dataset.a, +p.dataset.b, +p.dataset.s]), said: document.getElementById('heat-steps').textContent,
    marks: marks.length, sims_on_the_map: marks.reduce((a, m) => a + m.n, 0), many: marks.filter(m => m.many).length, overlapping: over.length, best_label_covers: covered }; }"""
async def part6(b):
    print('PART 6  the Operator tab'); P = '6'
    for sid, sw, want in (('s011', 'sw-20261111-190604', (365, 249, 48.267, 671.533, 144)), ('s004', 'sw-20261111-190100', (365, 365, 519.553, 671.585, 229))):
        F = sweep_figures(sw); mine = (F['cells'], F['meet'], F['lo'], F['hi'], F['within'])
        pg = await fresh(b, f'{BASE}?session={sid}&tab=operator'); a = await pg.evaluate(HEAT)
        say(P, a and mine == want and (a['cells'], a['meet'], a['lo'], a['hi'], a['within']) == want, f"{sid}, sweep {sw}: {F['cells']} cells, {F['meet']} meet the condition, values {F['lo']} to {F['hi']} Mbps, {F['within']} within 1% of the best (the sheet's figures, counted here from the table, and the page's own)" + ('' if a and mine == want else f": table {mine} page {a and (a['cells'], a['meet'], a['lo'], a['hi'], a['within'])}"))
        await pg.evaluate("() => document.querySelector('#heat-range [data-id=near]').click()"); n = await pg.evaluate(HEAT)
        say(P, a['range'] == 'all' and n['range'] == 'near' and a['on'] == ['all cells'] and n['on'] == ['within 1% of the best'] and a['fills'] != n['fills'] and n['palest'] >= n['below99'] == F['meet'] - F['within'] and not n['below99_not_palest'] and '99% of the best value to the best' in n['key'] and f"{F['meet'] - F['within']} cells below" in n['key'] and '99%' not in a['key'],
            f"{sid}: the switch changes the colours and the key: over all cells {a['steps_used']} steps are used ({sorted(a['fills'].values(), reverse=True)[:3]} cells in the three commonest); within 1% of the best {n['steps_used']} steps, the {n['below99']} cells below 99% of the best all in the palest; the key then says “{n['key'][n['key'].find('99%') - 1:][:95]}…”")
        ends = F['ends']; vals = [F['X'][0]] + [F['X'][i] for i in ends] + [F['X'][-1]]; said = ' · '.join((f"{F['X'][0]} to " if k == 0 else 'to ') + f"{F['X'][e]} by {s:g}" for k, (e, s) in enumerate(zip(ends + [len(F['X']) - 1], F['steps'])))
        say(P, a['gaps_after'] == ends and all(v in a['printed'] for v in vals) and [s for _, _, s in a['brackets']] == F['steps'] and said in a['said'],
            f"{sid}: the {len(ends)} gaps stand where the step between neighbours changes (after {', '.join(F['X'][i] for i in ends)}), those values are printed, and under the axis each stretch is named with its step: {a['said'][:200]}" + ('' if a['gaps_after'] == ends else f" · gaps on the page after columns {a['gaps_after']}, in the table {ends}"))
        sims = await pg.evaluate("() => EV.M.sims.filter(s => !s.same_as && s.metrics).length")
        say(P, not a['overlapping'] and not a['best_label_covers'] and a['many'] >= 1 and a['sims_on_the_map'] <= sims, f"{sid}: the label of the best cell covers no number; {a['sims_on_the_map']} of the session's {sims} simulations stand on the map as {a['marks']} marks, {a['many']} of them one mark with a count; marks that overlap: {a['overlapping']}")
        if sid == 's011':
            pick = await pg.evaluate("""async () => { window.scrollTo(0, 200); const y = scrollY, g = document.querySelector('#heat g.hm.many'), n = Number(g.dataset.n), ids = g.dataset.id.split(','); g.dispatchEvent(new MouseEvent('click', { bubbles: true })); await new Promise(r => setTimeout(r, 200));
              const links = [...document.querySelectorAll('#heat-list a[data-act=open]')].map(a => a.dataset.id), still = scrollY === y; document.querySelector('#heat-list a').click(); await new Promise(r => setTimeout(r, 1500));
              return { n, listed: links, same: String(links) === String(ids), still, opened: [EV.s.view, EV.s.sel && EV.s.sel.id] }; }""")
            say(P, pick['same'] and len(pick['listed']) == pick['n'] and pick['still'] and pick['opened'] == ['session', pick['listed'][0]], f"a click on a mark with a count lists its {pick['n']} simulations under the map and the page does not move; a click on one of them opens it in the session: {pick['opened']}")
            await pg.goto(f'{BASE}?session=s011&tab=operator'); await pg.wait_for_function("() => document.getElementById('op-score')", timeout=30000)
            sc = await pg.evaluate("() => ({ rows: [...document.querySelectorAll('#op-score tr[data-differs]')].map(r => [r.dataset.differs, r.cells[1].textContent.trim(), getComputedStyle(r.cells[1]).fontWeight]), tables: document.querySelectorAll('#op-score table').length, says: document.querySelector('#op-score + p').textContent })")
            say(P, sc['rows'] == [['queuePkts', '8', '700'], ['queuePkts', '100', '700']], f"the score: in the two tables the row whose values differ is marked: {sc['rows']} · “{sc['says']}”")
            await signs(pg, P, 'the Operator tab')
        say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

async def part6w(b):
    """The checklist: writes, so only on a scratch copy (never port 8600)."""
    print('PART 6, the checklist (on the scratch copy)'); P = '6w'
    if PORT == '8600': say(P, False, 'this part writes: run it on the scratch copy, not on port 8600'); return
    sid = 's011'; path = ROOT / 'checks' / 'scores' / f'{sid}.json'; before = json.loads(path.read_text()); pg = await fresh(b, f'{BASE}?session={sid}&tab=operator')
    await pg.wait_for_function("() => document.querySelector('#op-list tr[data-n]')", timeout=30000)
    rows = await pg.evaluate("() => [...document.querySelectorAll('#op-list tr[data-n]')].map(r => [Number(r.dataset.n), r.querySelector('select').value, r.querySelector('input').value, [...r.querySelectorAll('option')].map(o => o.value)])")
    say(P, len(rows) == len(before['checklist']) and all(r[3] == ['unjudged', 'yes', 'no'] for r in rows), f"each of the {len(rows)} items has yes, no and unjudged, and a note: {[(r[0], r[1]) for r in rows]}")
    await pg.select_option('#op-list tr[data-n="2"] select', 'yes'); await pg.wait_for_timeout(500); await pg.fill('#op-list tr[data-n="2"] input', 'says so in claim 1'); await pg.press('#op-list tr[data-n="2"] input', 'Tab'); await pg.wait_for_timeout(600)
    await pg.select_option('#op-list tr[data-n="3"] select', 'no'); await pg.wait_for_timeout(600)
    focus = await pg.evaluate("() => document.activeElement && document.activeElement.tagName"); now = json.loads(path.read_text()); got = {c['n']: (c['judgement'], c.get('note', '')) for c in now['checklist']}
    say(P, got[2] == ('yes', 'says so in claim 1') and got[3] == ('no', '') and got[1] == ('unjudged', '') and {k: v for k, v in now.items() if k != 'checklist'} == {k: v for k, v in before.items() if k != 'checklist'},
        f"a judgement made on the page is in the score file, and nothing else of the file changed: {got}")
    await pg.reload(); await pg.wait_for_function("() => document.querySelector('#op-list tr[data-n]')", timeout=30000)
    again = await pg.evaluate("() => [...document.querySelectorAll('#op-list tr[data-n]')].map(r => [Number(r.dataset.n), r.querySelector('select').value, r.querySelector('input').value, r.querySelector('.jm [data-m]').dataset.m])")
    say(P, again[1] == [2, 'yes', 'says so in claim 1', 'held'] and again[2] == [3, 'no', '', 'failed'] and again[0][1] == 'unjudged', f"it survives a reload: {again}")
    env = dict(os.environ, HOME=str(ROOT.parent)); r = subprocess.run(['/home/chunguck.kim/miniforge3/bin/python3', str(ROOT / 'harness' / 'score.py'), sid], env=env, capture_output=True, text=True, cwd=str(ROOT), timeout=600)
    after = json.loads(path.read_text()); got2 = {c['n']: (c['judgement'], c.get('note', '')) for c in after['checklist']}
    say(P, r.returncode == 0 and got2 == got, f"it survives scoring the session again (harness/score.py {sid}, exit {r.returncode}): {got2}" + ('' if r.returncode == 0 else f" · {r.stderr[-300:]}"))
    bad = await pg.evaluate("""async () => { const post = async b => { const r = await fetch('../api/judge', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) }); return [r.status, (await r.json()).error || 'accepted']; };
      return [await post({ session: 's014', n: 1, judgement: 'yes', note: '' }), await post({ session: 's011', n: 9, judgement: 'yes', note: '' }), await post({ session: 's011', n: 1, judgement: 'maybe', note: '' })]; }""")
    say(P, [x[0] for x in bad] == [400, 400, 400], f"refused: a session without a score, an item that does not exist, a judgement that is none of the three: {bad}")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== Part 7: Home
def results_from_files():
    """One row per brief, counted from the session folders and the score files themselves."""
    out = collections.OrderedDict()
    for d in sorted((ROOT / 'sessions').iterdir()):
        if not (d / 'ledger.jsonl').is_file(): continue
        meta = json.loads((d / 'session.json').read_text()) if (d / 'session.json').is_file() else {}; b = meta.get('brief'); brief = b if isinstance(b, str) else (b or meta.get('given') or {}).get('id') or ''
        recs = [r for r in (json.loads(l) for l in (d / 'ledger.jsonl').read_text().splitlines() if l.strip()) if r['type'] not in ('draft', 'scratch')]
        o = out.setdefault(brief, {'sessions': 0, 'report': 0, 'meet': 0, 'parts': [], 'unscored': 0}); o['sessions'] += 1; o['report'] += any(r['type'] == 'report' for r in recs); sc = ROOT / 'checks' / 'scores' / f'{d.name}.json'
        if sc.is_file(): s = json.loads(sc.read_text()); o['meet'] += all(s['conditions_hold_at_the_recommendation'].values()); o['parts'].append(s['gap_as_part_of_best'])
        else: o['unscored'] += 1
    return {b or 'before briefs': [str(o['sessions']), str(o['report']), str(o['meet']) if o['parts'] else 'not scored', f"{100 * max(o['parts']):.2f}%" if o['parts'] else 'not scored', str(o['unscored'])] for b, o in out.items()}
TABLE = r"""(q) => { const body = document.querySelector(q), t = body.parentElement, sc = t.closest('.ev-scroll'), rows = [...body.rows], lh = parseFloat(getComputedStyle(rows[0].cells[1]).lineHeight);
  const seqW = r => { const c = r.querySelector('[data-col=seq]'), k = c ? [...c.children] : []; return k.length ? k[k.length - 1].getBoundingClientRect().right - k[0].getBoundingClientRect().left : 0; }, col = [...t.tHead.rows[0].cells].find(c => /checks, in order/.test(c.textContent));
  return { rows: rows.length, heights: [...new Set(rows.map(r => Math.round(r.getBoundingClientRect().height)))], one_line: rows.every(r => r.getBoundingClientRect().height < 2 * lh + 4), average: Math.round(rows.reduce((a, r) => a + r.getBoundingClientRect().height, 0) / rows.length), page: document.documentElement.scrollHeight,
    scrolls: sc.scrollWidth > sc.clientWidth + 1, heads: [...t.tHead.rows[0].cells].map(c => [c.textContent.replace(/[↑↓]/g, '').trim(), (c.querySelector('a') || c).title || '']), not_started: (body.textContent.match(/not started/g) || []).length,
    review: rows.map(r => (r.querySelector('[data-col=review]') || { textContent: '' }).textContent.trim()), seq_col: Math.round(col.getBoundingClientRect().width), widest_seq: Math.round(Math.max(...rows.map(seqW))), most_marks: Math.max(...rows.map(r => r.querySelectorAll('[data-col=seq] .sq [data-m]').length)),
    cut: rows.flatMap(r => [...r.querySelectorAll('td.one')].filter(c => c.scrollWidth > c.clientWidth).map(c => [c.textContent.slice(0, 16), c.title === c.textContent, getComputedStyle(c).textOverflow])), wraps: rows.flatMap(r => [...r.cells].filter(c => c.getBoundingClientRect().height > 2 * lh + 4).map(c => c.textContent.slice(0, 20))) }; }"""
ROW = r"""(id) => { const r = document.querySelector(`#home-rows tr[data-id=${id}]`), sq = r.querySelector('[data-col=seq] .sq'), ta = r.querySelector('[data-col=seq] .tally');
  return { marks: [...sq.children].map(x => (x.classList.contains('sq-gap') ? ' ' : x.dataset.m ? ({ held: '✓', failed: '✗' }[x.dataset.m] || '–') : '')).join('').trimEnd(), counts: ta ? [Number(ta.dataset.held), Number(ta.dataset.failed)] : null,
    after: !!ta && !!(sq.compareDocumentPosition(ta) & Node.DOCUMENT_POSITION_FOLLOWING), returned: r.querySelector('[data-col=returned]').textContent.trim(), unnamed: r.querySelector('[data-col=unnamed]').textContent.trim() }; }"""
async def part7(b):
    print('PART 7  Home'); P = '7'; pg = await fresh(b, BASE); await pg.wait_for_timeout(2500); h = await pg.evaluate(TABLE, '#home-rows')
    say(P, h['one_line'] and not h['scrolls'] and not h['wraps'], f"Home at 1440 px wide: each of the {h['rows']} rows is one line high (heights {h['heights']} px, average {h['average']}; the page is {h['page']} px tall) and the table does not scroll sideways" + (f": {h['wraps'][:3]}" if h['wraps'] else ''))
    got = await pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('#home-results tbody tr')].map(r => [r.dataset.brief !== undefined ? (r.dataset.brief || 'before briefs') : r.cells[0].textContent.trim(), [...r.cells].slice(1).map(c => c.textContent.trim())]))"); heads = await pg.evaluate("() => [...document.querySelectorAll('#home-results thead th')].map(c => c.textContent.trim())"); want = results_from_files()
    real = {k: v for k, v in want.items()}; sheet = {'before briefs': ['1', '0', 'not scored', 'not scored', '1'], 'two-hosts-open': ['7', '6', 'not scored', 'not scored', '7'], 'two-hosts-udp-demand': ['11', '9', '9', '0.11%', '2']}
    say(P, got == want and heads == ['brief', 'sessions', 'with a final report', "meet the brief's conditions", 'largest gap to the best', 'not scored'] and (PORT != '8600' or want == sheet), f"“Results so far” is a table, one row per brief ({', '.join(heads[1:])}), equal to a count made here from the session and score files: {got}" + ('' if got == want else f" · from the files: {want}"))
    say(P, not h['not_started'] and all(re.fullmatch(r'\d+ to check|checked \d+ of \d+|reviewed by .*|', x) for x in h['review']), f"no row says “not started”; review progress reads: {sorted(set(h['review']))[:6]}")
    names = [x[0] for x in h['heads']]; tips = dict(h['heads'])
    say(P, 'tests held / failed' not in names and 'returned' in names and 'not named by a rule' in names and tips['returned'].startswith('Simulations returned from an earlier one') and tips['not named by a rule'].startswith('Simulations that no decision rule'),
        f"the columns: {names}; “returned” and “not named by a rule” give the full sentence on hover; the column of counts is gone")
    r = await pg.evaluate(ROW, 's011')
    say(P, r['marks'] == '✓✓✓ ✓✗ ✓✗✓ ✓✓✓✓' and r['counts'] == [10, 2] and r['after'] and r['returned'] == '4 of 44' and r['unnamed'] == '14 of 43', f"s011's row: {r['marks']}, then held {r['counts'][0]} and failed {r['counts'][1]} as marks with their counts; returned {r['returned']}; not named by a rule {r['unnamed']}")
    say(P, h['most_marks'] == 40 and h['seq_col'] <= h['widest_seq'] + 14, f"“checks, in order” is {h['seq_col']} px wide: the widest sequence (40 marks with their gaps, “+ n more” and the two counts) takes {h['widest_seq']} px")
    say(P, all(c[1] and c[2] == 'ellipsis' for c in h['cut']), f"a brief, a start and an ending never break; a text too long for its column ends in “…” and is given in full on hover: {[c[0] + '…' for c in h['cut']] or 'none is cut'}")
    await signs(pg, P, 'Home')
    await pg.goto(f'{BASE}?tab=compare&brief=two-hosts-udp-demand'); await pg.wait_for_timeout(2500); c = await pg.evaluate(TABLE, '#cmp-rows'); cn = [x[0] for x in c['heads']]
    say(P, c['one_line'] and not c['not_started'] and 'tests held / failed' not in cn and 'checks, in order' in cn and not c['wraps'], f"the Compare tab's table follows the same rules: {c['rows']} rows, one line each (heights {c['heights']} px), no “not started”, columns {cn}")
    say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

# ================================================================== Part 8: the views added since the first version
VIEWS8 = r"""() => { const col = v => { const i = document.createElement('i'); i.style.color = `var(${v})`; document.getElementById('ev').appendChild(i); const c = getComputedStyle(i).color; i.remove(); return c; };
  const tcp = col('--series-2'), text = col('--text-primary'), surf = col('--surface-1'), grid = col('--grid'), muted = col('--text-muted'), d = document.querySelector('#s-system .sy-det'), kn = document.getElementById('s-knob'), ts = document.getElementById('s-tests');
  const dots = [...kn.querySelectorAll('g[data-act=open]')].map(g => { const c = g.querySelectorAll('circle')[1], cs = getComputedStyle(c), r = g.querySelector('svg.gks'); return { ok: g.dataset.ok, ret: g.dataset.ret, fill: cs.fill, stroke: cs.stroke, d: 2 * +c.getAttribute('r'), mark: r ? [r.dataset.m, +r.getAttribute('width')] : null }; });
  const lines = el => { const lh = parseFloat(getComputedStyle(el).lineHeight); return Math.round(el.getBoundingClientRect().height / lh); };
  const rows = [...ts.querySelectorAll('tr[data-t=test]')].map(tr => ({ id: tr.dataset.id, h: lines(tr.querySelector('.tt-h')), m: lines(tr.querySelector('.tt-m')), cut: tr.querySelector('.tt-c').scrollWidth > tr.querySelector('.tt-c').clientWidth, full: tr.querySelector('.tt-c').title === tr.querySelector('.tt-c').textContent }));
  const mg = [...ts.querySelectorAll('.mg')].map(m => ({ m: +m.dataset.margin, tick: !!m.querySelector('line.mg-0'), w: +m.querySelector('rect.mg-b').getAttribute('width') }));
  const pics = [...document.querySelectorAll('#ev svg')].filter(sv => sv.getClientRects().length && !sv.closest('.gk, .gm, .gi, .mg') && sv.querySelector('text, foreignObject')).map(sv => { const s = sv.getScreenCTM().a, px = Math.min(...[...sv.querySelectorAll('text, foreignObject *')].filter(x => x.textContent.trim() && x.getClientRects().length).map(x => parseFloat(getComputedStyle(x).fontSize)));
    return { where: (sv.closest('[id]') || {}).id, scale: +s.toFixed(3), smallest: +(px * s).toFixed(2) }; });
  return { system: { rows: d.querySelectorAll('tr').length, tall: d.clientHeight, holds: d.scrollHeight, overflow: getComputedStyle(d).overflowY, last_in_view: d.querySelector('tr:last-child').getBoundingClientRect().bottom <= document.getElementById('s-system').getBoundingClientRect().bottom, names: [...d.querySelectorAll('tr td:first-child')].map(x => x.textContent.trim().slice(0, 28)) },
    axes: [...kn.querySelectorAll('.kn-row')].map(r => r.dataset.lo + ' to ' + r.dataset.hi), dots: dots.length, tcp_coloured: dots.filter(q => q.fill === tcp || q.stroke === tcp).length, meaning: dots.filter(q => q.ok !== '' && (q.ok === '1') !== (q.fill === text)).length, filled: dots.filter(q => q.fill === text).length, hollow: dots.filter(q => q.fill === surf && q.stroke === text).length,
    returned: dots.filter(q => q.ret === '1').map(q => q.mark), dot: dots[0].d, bands: [...kn.querySelectorAll('polygon.kb')].map(x => getComputedStyle(x).fill === grid).length, band_fill: [...kn.querySelectorAll('polygon.kb')].every(x => getComputedStyle(x).fill === grid), joins: [...kn.querySelectorAll('line.kj')].every(x => getComputedStyle(x).stroke === muted), n_rows: kn.querySelectorAll('.kn-row').length,
    tests: rows, card: Math.round(ts.getBoundingClientRect().height), margins: mg.length, no_tick: mg.filter(q => !q.tick).length, slivers: mg.filter(q => q.m !== 0 && q.w < 2).length, smallest_bar: Math.min(...mg.filter(q => q.m !== 0).map(q => q.w)), pics }; }"""
async def part8(b):
    print('PART 8  the views added since the first version'); P = '8'; pg = await fresh(b, f'{BASE}?session=s011'); await pg.wait_for_function("() => EV.OB && document.querySelector('#s-system svg.sy')", timeout=30000); await pg.evaluate("() => { EV.s.sysObj = EV.sysId('sender', 'tc', 'Scheduler'); EV.draw(); }"); await pg.wait_for_function("() => document.querySelector('#s-system .sy-det tr')", timeout=30000); r = await pg.evaluate(VIEWS8); s = r['system']  # no part of the picture is chosen until the reader clicks one (READABLE_PAGE.md): the check chooses the scheduler
    say(P, s['rows'] == 4 and s['holds'] <= s['tall'] + 1 and s['overflow'] not in ('auto', 'scroll') and s['last_in_view'], f"“The system”, the scheduler chosen: its {s['rows']} settings ({'; '.join(s['names'])}) are all in view; the box is {s['tall']} px tall and holds {s['holds']} px; nothing scrolls inside the card")
    say(P, r['axes'] == ['0.05 to 0.95', '0.05 to 0.40', '0.05 to 0.40', '0.300 to 0.310', '0.303 to 0.305'], f"s011's axes read: {'; '.join(r['axes'])}")
    say(P, not r['tcp_coloured'] and not r['meaning'] and r['filled'] + r['hollow'] == r['dots'], f"of the {r['dots']} dots none has the colour of TCP; they are drawn in the text colour, {r['filled']} filled (meet the brief's conditions) and {r['hollow']} hollow, as before")
    say(P, r['bands'] == r['n_rows'] - 1 and r['band_fill'] and r['joins'], f"between each axis and the one before it a shape is filled in the grid colour ({r['bands']} shapes for {r['n_rows']} axes) and its two lines are in the muted text colour")
    say(P, r['returned'] and all(m and m[0] == 'sim-returned' and m[1] >= r['dot'] for m in r['returned']), f"the {len(r['returned'])} simulations returned from an earlier one carry the mark of kind sim-returned, {r['returned'][0][1] if r['returned'] else '?'} px wide beside a dot of {r['dot']} px")
    say(P, r['margins'] and not r['no_tick'] and not r['slivers'], f"the margin: each of the {r['margins']} bars has a tick at zero, and a bar that is not zero is at least 2 px wide (the narrowest is {r['smallest_bar']} px)")
    worst = max(x['h'] + x['m'] for x in r['tests'])
    say(P, len(r['tests']) == 12 and worst <= 3 and all(x['m'] == 1 and x['h'] <= 2 for x in r['tests']) and all(x['full'] for x in r['tests']), f"the tests list: each of the {len(r['tests'])} tests of s011 takes at most {worst} text lines (the hypothesis up to two, then one line with what was compared, the check, the margin and the verdict); the card is {r['card']} px tall")
    small = [x for x in r['pics'] if x['scale'] < 0.995 or x['smallest'] < 10.99]
    say(P, not small, f"at 1440 px wide the {len(r['pics'])} pictures of the page are drawn at their own size, so their smallest text is {min(x['smallest'] for x in r['pics'])} px on the screen" + (f": scaled down: {small}" if small else ''))
    for left in ('lanes', 'map'):
        x = await pg.evaluate(f"() => {{ EV.s.left = '{left}'; EV.s.sel = EV.selOf(EV.M, 'C5'); EV.draw(); }}"); await pg.wait_for_timeout(300); q = await pg.evaluate(VIEWS8); small = [x for x in q['pics'] if x['scale'] < 0.995 or x['smallest'] < 10.99]
        if small: say(P, False, f"with the {left} and a test open, scaled down: {small}")
    await pg.evaluate("() => { EV.s.left = 'tree'; EV.s.sel = null; EV.draw(); }")
    rp = await pg.evaluate("""async () => { const M = EV.M, n = M.steps.length, bad = [], by = id => (M.recStep[id] ?? 0), vis = el => !!el && [el, ...el.querySelectorAll('*')].some(x => [...x.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()) && !x.closest('.later') && getComputedStyle(x).visibility !== 'hidden'); EV.s.sel = null;  // some text of it can be read
      for (let k = 0; k < n; k++) { EV.s.step = k; EV.draw(); if (k % 20 === 19) await new Promise(r => setTimeout(r, 0));
        document.querySelectorAll('#s-knob g[data-act=open]').forEach(g => { if (by(g.dataset.id) > k) bad.push({ k, what: 'a dot of a later simulation', id: g.dataset.id }); });
        const rows = document.querySelectorAll('#s-knob .kn-row').length; if (document.querySelectorAll('#s-knob polygon.kb').length > Math.max(0, rows - 1)) bad.push({ k, what: 'a join shape without its axis' });
        document.querySelectorAll('#s-tests tr[data-t=test]').forEach(tr => { const T = M.testById[tr.dataset.id], last = k === n - 1, part = (c, id) => { const on = vis(tr.querySelector(c)), want = id ? by(id) <= k : last; if (on !== want) bad.push({ k, test: T.id, part: c, read: on, recorded: want }); };
          if (vis(tr.querySelector('.tt-h')) !== (by(T.exp) <= k)) bad.push({ k, test: T.id, part: 'row' }); if (by(T.exp) <= k) { part('.tt-k', T.check && T.check.id); part('.tt-v', T.verdict && T.verdict.id); if (vis(tr.querySelector('.mgc')) !== !!(T.check && by(T.check.id) <= k)) bad.push({ k, test: T.id, part: 'margin' }); } }); }
      EV.s.step = null; EV.draw(); return { steps: n, problems: bad.length, first: bad.slice(0, 3) }; }""")
    say(P, not rp['problems'], f"replay s011: at each of {rp['steps']} steps the chart holds no dot of a later simulation, and a test's check, margin and verdict can be read only from their own steps" + (f": {rp['first']}" if rp['problems'] else ''))
    await signs(pg, P, 's011'); say(P, not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); await pg.context.close()

PARTS = {'1': part1, '2': part2, '3': part3, '4': part4, '5': part5, '6': part6, '6w': part6w, '7': part7, '8': part8}
async def main():
    want = [a for a in sys.argv[1:] if a in PARTS] or [k for k in PARTS if not k.endswith('w')]  # a part that writes ("6w") runs only when named
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for k in want: await PARTS[k](b)
        await b.close()
    print('RESULT:', 'PASS' if not FAILED else 'FAIL ' + ', '.join(sorted(set(FAILED))))
asyncio.run(main())
