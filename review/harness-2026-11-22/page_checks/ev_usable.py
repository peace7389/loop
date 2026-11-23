"""The usability changes of 2026-11-15, on a SCRATCH copy (EV_PORT, EV_ROOT):   ev_usable.py [parts] [--sessions s024,s006]
  cards   the set-up page: every value of a part that comes from a setting is a field in that part's card; the scheduler's card chooses
          the scheduling policy; the mark before a field switches who decides; a setting that is not set is set by typing, unset by emptying
  bars    the set-up page, "Who decides what": a bar beside every numeric setting; dragging writes the field, typing moves the handle
  aim     the board's first box says the aim the AI chose (its final report's goal, word for word) once the report is recorded, and not before
  checked a hypothesis that has its check but not yet its verdict says the check's result on its box (an edge in its colour; the fill is the verdict's)
  fold    the notebook: a click on a turn's heading folds the turn to one line and opens it again; nothing above moves; the pane is untouched
  values  a rule's bar: pointing at the dot or the threshold opens a box with its value (recounted here from the simulation's record)
  names   a simulation named in a rule is said by its settings (recounted here from the experiment's designs), the AI's label beside it
  exps    the glance: "X1 · 5 simulations"; pointing at an experiment opens a box (its tests, its simulations, how many were not run again)
  tcp     each TCP type (congestion control) has one plain line: under the type chosen on the set-up page, in the setting's box, in the TCP socket's card
  ns3     the legend names the source of a simulation's records "ns-3"
  key     the board's key is a table of two rows (a box, an arrow); it lists exactly the looks the board has; each look opens a box with its sentence
  board   a light rule between each two columns of the board, through no box; the aim's box opens the aim, whole, first in the detail; the table under
          the board has a button that opens and folds it, and folding it in Full holds
  short   a rule's bar is at most 300 px long, in the notebook and in a test's detail, with its dot and threshold inside it
  none    the set-up page: the box "or start from an empty set-up" empties the form (no texts, no knobs, every setting fixed at the first brief's
          value) and turns the list of saved briefs off; unticked, the form is filled again from the brief it held
  home    Home with a session running and a long brief name: the table does not scroll sideways at 1,440 px, each row is one line, the running
          session has the moving dot, and a start is said as month-day hour:minute with the whole time in its box
  marks   "How it worked as a researcher": present, partly, absent and not yet each have a look of their own (fill, edge, sign) and one width;
          the key of "The session at a glance" has a border around each item
  legend  every item of the legend opens a box that says what it means
  either  a rule with an "or" in it is shown as either-or lines, not as bars: every comparison, alternative and group is worked out again here from
          the page's own numbers and agrees with the harness's check; no line says "does not hold" under a rule that held; the chain of boxes is
          folded and opens with a click   (--either s008,s010,s012 names the sessions; they must have such rules)
  close   a result decided by less than the tolerance says so, in the test's detail and on its notebook card: which tests, and by how much, is
          worked out again here with the harness's own reader of rules (decision_rules.py)   (--close s014,s013 names the sessions)
  plain   who wrote a thing is said by an icon, not by a colour: no box, edge or text of a session's page or of the full report in the pane is
          violet (the colour that once meant "written by the AI"); only the small icons are   (not in the default list)
  shared  the page is shared (2026-11-17): Home, the set-up page and a running session's banner say which session is running and who started it;
          while one runs the Start button is off and says why; Stop is there only for the one who started it or the owner; the foot gives the
          one command that brings the page to somebody else's computer. The server's answers are changed on the way to the page (a pretended
          running session and two pretended accounts); nothing is started   (not in the default list)
  task    the task is written by the harness from the aim and the settings the AI may change (2026-11-17): the set-up page shows that sentence
          instead of a field, word for word what harness/tools.py writes, and it follows the form; a saved brief that still states a task of
          its own says so, with a warning, until the form is changed; a session's brief says who wrote its task   (not in the default list)
  network looking from the network (2026-11-17): with a server that says the visitor is view-only the bar shows "view only", the Start button
          is off and says why, and the foot says that one is looking only and how to use the page fully; for a user of this machine the
          foot gives the address to look from the network; on a phone (390 px) the page does not scroll sideways: what is wider than the
          screen scrolls inside its own card   (the server's answers are changed on their way to the page; not in the default list)
  limit   a final report that says what limits the result and which settings made no meaningful difference (reports since 2026-11-15) shows both
          as the part "What limits the result" of "What it proposes" and of the full report, word for word and in the report's order; a report
          recorded before has no such part; in the replay the part is absent until the report is recorded; a running session whose instructions
          ask for it has a seventh empty place   (needs the scripted session lim1 of harness_checks/test_tolerance.py; not in the default list)
Nothing is written to the scratch copy (no brief is saved, no session started)."""
import sys, os, re, json, pathlib
from playwright.sync_api import sync_playwright
PORT = os.environ.get('EV_PORT', '8611'); BASE = f"http://127.0.0.1:{PORT}/viewer/index.html"; ROOT = pathlib.Path(os.environ['EV_ROOT'])
ARGS = sys.argv[1:]; SIDS = (ARGS[ARGS.index('--sessions') + 1] if '--sessions' in ARGS else 's024,s006').split(',')
PARTS = [a for i, a in enumerate(ARGS) if not a.startswith('-') and (i == 0 or ARGS[i - 1] not in ('--sessions', '--either', '--close'))] or ['cards', 'bars', 'aim', 'checked', 'fold', 'values', 'names', 'exps', 'tcp', 'ns3', 'key', 'board', 'short', 'none', 'legend', 'home', 'marks', 'either', 'close']
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:60])
def ledger(sid): return [r for r in (json.loads(l) for l in (ROOT / 'sessions' / sid / 'ledger.jsonl').read_text().splitlines() if l.strip()) if r.get('type') not in ('draft', 'scratch')]
def labels(rule): return list(dict.fromkeys(re.findall(r'[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)', str(rule or ''))))
def num(v):
    m = re.fullmatch(r'\s*([0-9.]+)\s*([kMG]?)bps\s*', str(v)); return float(m.group(1)) * {'': 1, 'k': 1e3, 'M': 1e6, 'G': 1e9}[m.group(2)] if m else v
def same(a, b): return num(a) == num(b) if not isinstance(num(a), str) and not isinstance(num(b), str) else str(a) == str(b)

def new_page(b, url, wait, w=1500):
    ctx = b.new_context(viewport={'width': w, 'height': 1000}); pg = ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_selector(wait, timeout=60000); pg.wait_for_timeout(900); return pg
def session(b, sid): return new_page(b, f'{BASE}?session={sid}', '#s-notebook .nb-group')
def done(pg): say(not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); pg.context.close()

def part_cards(b):
    print('CARDS'); pg = new_page(b, f'{BASE}?tab=new', '#be-conf .be-c-r'); pg.set_viewport_size({'width': 1500, 'height': 1700}); pg.wait_for_timeout(300); brief = lambda: pg.evaluate("BRIEF_EDITOR.toBrief()"); card = lambda part: f'#be-conf [data-part="{part}"]'
    O = json.loads((ROOT / 'viewer' / 'objects.json').read_text()); b0 = brief()
    ids = pg.evaluate("Object.fromEntries([...document.querySelectorAll('#be-conf .be-c')].map(c => [c.querySelector('.be-c-h b').textContent + '|' + c.querySelector('.be-c-h span').textContent.split(' ')[0], c.dataset.part]))")
    sched, udpq, tcpq, sdev, tcps, link = ids['Scheduler|sender'], ids['UDP queue|sender'], ids['TCP queue|sender'], ids['Point-to-point device|sender'], ids['TCP socket|sender'], ids['Point-to-point link|between']
    # every name of a setting in a row of objects.json has its field in that row (but the rows that only repeat or follow from a value set elsewhere)
    READ = pg.evaluate("BRIEF_EDITOR.CONF_READ"); SKIP = pg.evaluate("BRIEF_EDITOR.CONF_SKIP"); KEYS = pg.evaluate("BRIEF_EDITOR.SETTINGS.map(q => q.k)"); own = {'tcpVariantPlain': 'tcpVariant', 'tcpBufPlain': 'tcpBufBytes'}
    want = {}
    parts = [(f"{h['key']}-{l['key']}-{i}", o) for h in O['hosts'] for l in O['layers'] for i, o in enumerate(h.get(l['key']) or [])] + [('link', O['channel'])]
    for pid, o in parts:
        for r in o['rows']:
            if r[0] in SKIP or r[0] in READ: continue
            ks = [own.get(k, k) for k in re.findall(r'\{(\w+)\}', r[1])]; ks = ['policy' if k == 'mode' else k for k in ks if k in KEYS or k == 'mode']
            if ks: want[f'{pid}|{r[0]}'] = ks
    got = pg.evaluate("""() => { const out = {}; document.querySelectorAll('#be-conf .be-c').forEach(c => c.querySelectorAll('.be-c-r').forEach(r => { const ks = [...r.querySelectorAll('input, select')].map(el => el.dataset.k || el.dataset.on || el.dataset.f.split('.')[1]); if (ks.length) out[c.dataset.part + '|' + r.querySelector(':scope > span').textContent] = ks; })); return out; }""")
    say(got == want and len(want) > 15, f"every value of a part that comes from a setting is a field in that part's card: {len(got)} rows with a field, as the rows of objects.json name them ({sum(len(v) for v in want.values())} fields)" + ('' if got == want else f": {[(k, got.get(k), want.get(k)) for k in set(got) | set(want) if got.get(k) != want.get(k)][:4]}"))
    f = f'{card(sched)} input[data-f="set.weightUdp.def"]'; pg.click(f); pg.fill(f, ''); pg.type(f, '0.3', delay=50); pg.wait_for_timeout(300)
    say(pg.evaluate("document.activeElement.dataset.f") == 'set.weightUdp.def' and brief()['knobs']['weightUdp']['default'] == 0.3 and pg.input_value('#be-who input[data-f="set.weightUdp.def"]') == '0.3', "0.3 typed as the ratio in the scheduler's card: the cursor stays in the field, the brief starts the ratio at 0.3, block 2 says the same")
    say('0.7' in pg.inner_text(f'{card(sched)} .be-c-r >> nth=0') and '0.3 : 0.7' in pg.text_content('#be-svg'), "TCP's share beside the field and the picture follow as it is typed")
    pg.select_option(f'{card(sched)} select[data-k=policy]', 'cap'); pg.wait_for_timeout(300)
    say(pg.evaluate("EV.nw.policy") == 'cap' and pg.is_checked('#be-policy input[value=cap]') and pg.evaluate("BRIEF_EDITOR.ctx.flags().policy") == 'cap', "the scheduling policy chosen on the scheduler's card is the policy the session would start with, and block 6 shows it")
    pg.check('#be-policy input[value=random]'); pg.wait_for_timeout(300); pg.mouse.click(5, 300); pg.wait_for_timeout(200)
    say(pg.input_value(f'{card(sched)} select[data-k=policy]') == 'random', "chosen in block 6, the scheduler's card follows")
    # what the chosen policy does, with the numbers of the form (recounted here: the ratio times the link rate); and a click on the mark straight after typing is not lost
    pg.select_option(f'{card(sched)} select[data-k=policy]', 'cap'); pg.wait_for_timeout(200); f = f'{card(sched)} input'; pg.click(f); pg.fill(f, '0.45'); pg.click(f'{card(sched)} button.be-m'); pg.wait_for_timeout(400); bb = brief(); link = float(re.match(r'[\d.]+', bb['system']['linkRate']).group(0)) * (1000 if 'Gbps' in bb['system']['linkRate'] else 1)
    eff = pg.inner_text('#be-eff'); turn = pg.inner_text(f'{card(sched)} .be-c-r >> nth=2')
    say(bb['system'].get('weightUdp') == 0.45 and f"UDP at most {0.45 * link:g} Mbps, TCP at most {0.55 * link:g} Mbps" in eff and 'nothing more to set' in eff and 'starting ratio' not in eff and 'one go' in turn, f"0.45 typed and the mark clicked straight after: the ratio is fixed at 0.45; under “cap” the card says what that does, counted here as the ratio times the link rate: “{eff}”")
    pg.select_option(f'{card(sched)} select[data-k=policy]', 'share'); pg.wait_for_timeout(300); eff = pg.inner_text('#be-eff')
    say(f"UDP {0.45 * link:g} Mbps, TCP {0.55 * link:g} Mbps" in eff and 'unused' in eff, f"under “share”: “{eff}”")
    pg.click(f'{card(sched)} button.be-m'); pg.wait_for_timeout(300); f = f'{card(sched)} input[data-f="set.weightUdp.def"]'; pg.fill(f, '0.3'); pg.wait_for_timeout(200); pg.mouse.move(5, 300); pg.wait_for_timeout(200)
    pg.check('#be-policy input[value=share]'); pg.wait_for_timeout(200); pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(100); y0 = pg.evaluate('scrollY')
    pg.click(f'{card(sched)} button.be-m'); pg.wait_for_timeout(300); bb = brief()
    say(bb['system'].get('weightUdp') == 0.3 and 'weightUdp' not in bb['knobs'] and pg.inner_text(f'{card(sched)} button.be-m').strip() == 'fixed', "a click on the mark before the ratio fixes it at the value in the field (0.3); the mark then reads “fixed” (it read “AI may change”)")
    pg.click(f'{card(sched)} button.be-m'); pg.wait_for_timeout(300); bb = brief()
    say(bb['knobs'].get('weightUdp', {}).get('default') == 0.3 and bb['knobs']['weightUdp']['min'] == b0['knobs']['weightUdp']['min'], "a second click gives it back to the AI with its range, starting from 0.3")
    f = f'{card(udpq)} input'; pg.click(f); pg.type(f, '50', delay=50); pg.click(f'{card(tcpq)} input'); pg.wait_for_timeout(400); bb = brief()
    say(bb['system'].get('queuePktsUdp') == 50 and 'queuePktsTcp' not in bb['system'] and 'queuePktsTcp' not in bb['knobs'] and pg.evaluate("document.activeElement.closest('[data-part]').dataset.part") == tcpq, "50 typed in the UDP queue's card gives that queue a length of its own (the TCP queue keeps the common one), and the click that ended the typing landed in the next field")
    f = f'{card(udpq)} input'; pg.click(f); pg.fill(f, ''); pg.click('#be-conf .be-c-h'); pg.wait_for_timeout(400); bb = brief()
    say(json.dumps(bb).replace('"default": 0.3', '"default": 0.5') == json.dumps(b0), "emptied, the UDP queue's own length is left out again: the brief is the opened one but for the ratio")
    say(pg.evaluate('scrollY') == y0, "no mark and no field of a card moved the page")
    f = f'{card(sdev)} input[data-on=devQueuePkts]'; pg.fill(f, '50'); pg.keyboard.press('Tab'); pg.wait_for_timeout(400)
    say(brief()['system'].get('devQueuePkts') == 50 and pg.evaluate("[...document.querySelectorAll('#be-conf input[data-f=\"set.devQueuePkts.value\"]')].map(x => x.value).join()") == '50,50' and 'queue 50' in pg.text_content('#be-svg'), "the device's transmit queue set in the sender's device: both devices' cards and the picture say 50")
    pg.select_option(f'{card(tcps)} select', 'TcpBbr'); pg.wait_for_timeout(300); say(brief()['knobs']['tcpVariant']['default'] == 'TcpBbr', "the TCP type chosen in the TCP socket's card is the brief's")
    f = f'{card(sched)} input'; pg.fill(f, '2'); pg.wait_for_timeout(300)
    say('0.05 to 0.95' in (pg.get_attribute(f, 'title') or '') and 'bad' in (pg.get_attribute(f, 'class') or '') and pg.is_disabled('#be-start'), f"a ratio of 2 is refused in the card, with the reason on the field (“{pg.get_attribute(f, 'title')}”), and Start is off")
    done(pg)

def part_bars(b):
    print('BARS'); pg = new_page(b, f'{BASE}?tab=new', '#be-who .be-bar'); brief = lambda: pg.evaluate("BRIEF_EDITOR.toBrief()"); b0 = brief()
    bars = pg.evaluate("Object.fromEntries([...document.querySelectorAll('#be-who .be-bar')].map(x => [x.dataset.bar, x.dataset.mode + ':' + x.querySelectorAll('input').length]))")
    want = {**{k: 'fixed:1' for k, v in b0['system'].items() if k != 'udpPacketBytes'}, **{k: 'knob:3' for k, v in b0['knobs'].items() if 'choices' not in v}}
    say(bars == want, f"a bar beside every numeric setting the brief sets: one handle for each of the {sum(v == 'fixed:1' for v in want.values())} fixed, three (lowest, highest, start) for each of the {sum(v == 'knob:3' for v in want.values())} the AI may change" + ('' if bars == want else f': {bars} / {want}'))
    off = pg.evaluate("""() => { const B = BRIEF_EDITOR, out = []; document.querySelectorAll('#be-who .be-bar input').forEach(el => { const k = el.dataset.barK, h = el.dataset.barH, f = B.s.set[k], q = B.SETTINGS.find(x => x.k === k);
      const a = B.size(q, f[h]).n, b = B.size(q, B.barText(k, Number(el.value))).n; if (Math.abs(a - b) > 1e-9 * Math.max(1, Math.abs(a))) out.push([k, h, f[h], B.barText(k, Number(el.value))]); }); return out; }""")
    say(not off and json.dumps(brief()) == json.dumps(b0), "each handle stands at its typed value (its place read back gives the same value), and drawing the bars changed nothing in the brief" + (f" (but: {off})" if off else ''))
    def drag(k, h, frac):
        bar = pg.locator(f'#be-who .be-bar[data-bar="{k}"]'); bar.scroll_into_view_if_needed(); bx = bar.bounding_box()
        pos = pg.evaluate(f"Number(document.querySelector('#be-who input[data-bar-k=\"{k}\"][data-bar-h=\"{h}\"]').value)") / 1000
        x0 = bx['x'] + 6 + (bx['width'] - 12) * pos; y = bx['y'] + 8; x1 = bx['x'] + 6 + (bx['width'] - 12) * frac
        pg.mouse.move(x0, y); pg.mouse.down(); pg.mouse.move((x0 + x1) / 2, y, steps=4); pg.mouse.move(x1, y, steps=4); pg.mouse.up(); pg.wait_for_timeout(250)
    drag('weightUdp', 'def', 0.25); v = brief()['knobs']['weightUdp']['default']
    say(abs(v - (0.05 + 0.9 * 0.25)) < 0.02 and pg.input_value('#be-who input[data-f="set.weightUdp.def"]') == str(v) and pg.input_value('#be-conf input[data-f="set.weightUdp.def"]') == str(v), f"the ratio's start handle dragged to a quarter of its bar writes {v} into its field, and into the scheduler's card")
    drag('weightUdp', 'min', 0.5); k = brief()['knobs']['weightUdp']
    say(k['min'] > 0.4 and k['min'] <= k['default'] <= k['max'], f"the lowest value dragged past the start value takes the start value along: {k['min']} to {k['max']}, from {k['default']}")
    drag('weightUdp', 'max', 0.1); k = brief()['knobs']['weightUdp']
    say(k['min'] < k['max'] and k['min'] <= k['default'] <= k['max'], f"the highest value cannot pass the lowest: {k['min']} to {k['max']}, from {k['default']}")
    drag('linkRate', 'value', 0.5); v = brief()['system']['linkRate']; say(v in ('300Mbps', '310Mbps', '320Mbps', '330Mbps', '340Mbps'), f"a rate's bar is in equal ratios: the middle of 10 Mbps to 10 Gbps is {v}, written as the harness writes a rate")
    pg.fill('#be-who input[data-f="set.queuePkts.def"]', '10'); pg.wait_for_timeout(250)
    say(pg.evaluate("Number(document.querySelector('#be-who input[data-bar-k=queuePkts][data-bar-h=def]').value)") == 333, "10 typed as the queue length's start value moves its handle to a third of the bar (1 to 1000 in equal ratios)")
    pg.fill('#be-who input[data-f="set.queuePkts.def"]', '5000'); pg.wait_for_timeout(250)
    say(pg.evaluate("Number(document.querySelector('#be-who input[data-bar-k=queuePkts][data-bar-h=def]').value)") == 1000 and brief()['knobs']['queuePkts']['default'] == 5000, "a value beyond the bar can still be typed: the handle stands at the end, the brief has the typed value")
    pg.focus('#be-who input[data-bar-k=seed][data-bar-h=def]'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(250)
    say(brief()['knobs']['seed']['default'] == b0['knobs']['seed']['default'] + 2, "the keyboard: two presses of the right arrow on the seed's start handle add 2")
    pg.click('#be-who tr[data-row=devQueuePkts] button[data-to=fixed]'); pg.wait_for_timeout(300)
    say(pg.evaluate("!!document.querySelector('#be-who .be-bar[data-bar=devQueuePkts][data-mode=fixed]')") and not pg.evaluate("!!document.querySelector('#be-who .be-bar[data-bar=tcpInitCwnd]')") and not pg.evaluate("!!document.querySelector('#be-who .be-bar[data-bar=tcpVariant]')"), "a setting that is switched on gets its bar; one that is not set, and the TCP type (a list, not a number), have none")
    # a size in bytes is also said as a size, beside its fields, and follows them; the arrow keys go to the next round value of a bar whose values are round
    row = '#be-who tr[data-row=tcpBufBytes]'; pg.click(f'{row} button[data-to=knob]'); pg.wait_for_timeout(300); pg.fill(f'{row} input[data-f="set.tcpBufBytes.min"]', '98304'); pg.fill(f'{row} input[data-f="set.tcpBufBytes.max"]', '16777216'); pg.wait_for_timeout(300); c1 = pg.inner_text(f'{row} .be-conv')
    pg.focus(f'{row} input[data-bar-h=def]'); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(300); d1 = brief()['knobs']['tcpBufBytes']['default']; c2 = pg.inner_text(f'{row} .be-conv')
    say(c1 == 'lowest 96 kB · highest 16 MB · starts at 1 MB' and d1 == 1572864 and c2 == 'lowest 96 kB · highest 16 MB · starts at 1.5 MB', f"TCP's buffers, typed in bytes (98304 to 16777216, from 1048576), are said beside the fields as “{c1}”; one press of the right arrow on the start handle goes to the next round size, 1.5 MB ({d1} bytes), and the words follow")
    pg.click(f'{row} button[data-to=off]'); pg.wait_for_timeout(300)
    labels = pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('#be-who tr[data-row]')].map(tr => [tr.dataset.row, [...tr.querySelectorAll('.be-fl')].map(l => l.querySelector('small').textContent + ':' + (l.querySelector('input').dataset.f || '').split('.').pop())]).filter(q => q[1].length))")
    odd = {k: v for k, v in labels.items() if v not in (['value:value'], ['lowest:min', 'highest:max', 'starts at:def'], ['lowest:min', 'highest:max', 'starts at:def', 'step:step'], ['the AI may choose among:choices', 'starts at:def'])}
    say(len(labels) >= 8 and not odd, f"every field of “Who decides what” says what it is, above it: “value” for a fixed setting; “lowest”, “highest”, “starts at” (and “step”) for one the AI may change ({len(labels)} settings)" + (f": {odd}" if odd else ''))
    for w in (1500, 1280):
        pg.set_viewport_size({'width': w, 'height': 1000}); pg.wait_for_timeout(300)
        r = pg.evaluate("(() => { const t = document.getElementById('be-who'); return [Math.round(t.getBoundingClientRect().right), Math.round(t.parentElement.getBoundingClientRect().right), document.documentElement.scrollWidth, innerWidth]; })()")
        say(r[0] <= r[1] + 1 and r[2] <= r[3], f"{w} px wide: the table with its bars fits its block and the page has no sideways scroll (table to {r[0]}, block to {r[1]}; page {r[2]} of {r[3]})")
    done(pg)

def part_aim(b):
    print('AIM')
    for sid in SIDS:
        led = ledger(sid); meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); goal = ((meta.get('given') or {}).get('goal') or {}); rep = next((r for r in led if r['type'] == 'report'), None)
        pg = session(b, sid); READ = "() => { const g = document.querySelector('#s-map svg g[data-aim]'), c = document.getElementById('map-chose'); return g ? { text: g.textContent.replace(/\\s+/g, ' ').trim(), chose: c ? c.textContent : null, attr: g.dataset.chose || null, own: c ? c.dataset.own : null, flag: !!g.querySelector('svg.ic-flag'), cls: g.querySelector('rect.bx').classList.contains('st-aim'), by: g.dataset.by, fits: (() => { const d = g.querySelector('.bt'), fo = g.querySelector('foreignObject'); return d && fo ? d.scrollHeight <= fo.getBoundingClientRect().height / (g.ownerSVGElement.getBoundingClientRect().width / g.ownerSVGElement.viewBox.baseVal.width) + 1 : null; })() } : null; }"
        r = pg.evaluate(READ)
        if goal.get('kind') == 'open' and rep and rep['body'].get('goal'):
            want = rep['body']['goal'] if isinstance(rep['body']['goal'], str) else ' · '.join(rep['body']['goal'])
            say(r and r['attr'] == want and r['chose'] == want and r['own'] == 'model' and 'chosen by the AI at the end' in r['text'] and r['flag'] and r['cls'] and r['by'] == 'model', f"{sid} (open aim): the board's first box says the aim the AI chose, word for word from its final report ({len(want)} characters, marked as the AI's own), and that the AI chose it at the end; the box carries the aim's flag and colour: “{want[:60]}…”")
            say(r['fits'] is not False, f"{sid}: the box's text is cut by the browser at a whole line, inside the box")
            k = pg.evaluate("(id) => EV.M.recStep[id]", rep['id']); pg.evaluate("(k) => { EV.s.step = k - 1; EV.draw(); }", k); pg.wait_for_timeout(300); r0 = pg.evaluate(READ)
            say(r0 and r0['chose'] is None and r0['attr'] is None and 'the AI chooses its own aim' in r0['text'] and want[:25] not in pg.evaluate("document.getElementById('s-find').textContent"), f"{sid}: in the replay, one step before the final report (step {k - 1}), the box says only that the aim is open: the chosen aim is not on the board")
            pg.evaluate("() => { EV.s.step = null; EV.draw(); }"); pg.wait_for_timeout(300); pg.locator('#s-map svg g[data-aim]').hover(); pg.wait_for_timeout(500)
            pop = pg.evaluate("() => { const p = document.querySelector('#wd-pop [data-bp=chose]'); return p ? p.textContent : null; }"); say(pop == want, f"{sid}: pointing at the box opens the brief's card with the whole chosen aim")
        else:
            say(r and r['chose'] is None and r['attr'] is None, f"{sid} (the brief gives the aim{'' if rep else '; no final report'}): the board's first box is the brief's aim, nothing is said to be chosen by the AI: “{r and r['text'][:70]}”")
        done(pg)

def part_checked(b):
    print('CHECKED'); sid = SIDS[0]; led = ledger(sid); pg = session(b, sid); pos = {r['id']: i for i, r in enumerate(led)}
    # a hypothesis whose check was recorded some steps before its verdict: in the replay, between the two, its box says the check's result
    cases = []
    for c in [r for r in led if r['type'] == 'check']:
        h = c['body'].get('for'); v = next((r for r in led if r['type'] == 'verdict' and r['body'].get('for') == h and pos[r['id']] > pos[c['id']]), None)
        later = [q for q in led if q['type'] == 'check' and q['body'].get('for') == h and pos[q['id']] > pos[c['id']]]
        if v and not later and c['body'].get('result') in ('held', 'failed'): cases.append((h, c, v))
    READ = "(h) => { const g = document.querySelector(`#s-map g[data-node=\"${h}\"]`); if (!g) return null; const r = g.querySelector('rect.bx'); return { check: g.dataset.check || null, edge: r.classList.contains('ck-held') ? 'held' : r.classList.contains('ck-failed') ? 'failed' : null, text: g.textContent.replace(/\\s+/g, ' ').trim().slice(0, 60), why: (w => (w ? { res: w.dataset.why, text: w.textContent.trim(), h: Math.round(w.getBoundingClientRect().height), in: w.getBoundingClientRect().right <= r.getBoundingClientRect().right + 1 && w.getBoundingClientRect().bottom <= r.getBoundingClientRect().bottom + 1 } : null))(g.querySelector('.bx-why')), filled: ['st-supported', 'st-refuted', 'st-inconclusive'].some(c => r.classList.contains(c)), key: !!document.getElementById('mk-ck') }; }"
    bad = []; tried = 0
    for h, c, v in cases[:6]:
        kc, kv = pg.evaluate("(ids) => ids.map(i => EV.M.recStep[i])", [c['id'], v['id']])
        if kv <= kc: continue
        tried += 1; res = c['body']['result']
        pg.evaluate("(k) => { EV.s.step = k; EV.draw(); }", kc); pg.wait_for_timeout(150); at = pg.evaluate(READ, h)
        pg.evaluate("(k) => { EV.s.step = k; EV.draw(); }", kc - 1); pg.wait_for_timeout(150); before = pg.evaluate(READ, h)
        pg.evaluate("(k) => { EV.s.step = k; EV.draw(); }", kv); pg.wait_for_timeout(150); after = pg.evaluate(READ, h)
        if not at or at['check'] != res or at['edge'] != res or f'check {res}' not in at['text'] or at['filled'] or not at['key'] or (before and (before['check'] or before['edge'])) or not after or after['check'] or after['edge'] or not after['filled'] or (before and before['why']) or after['why'] or not at['why'] or at['why']['res'] != res or not re.search(r'\d', at['why']['text']) or at['why']['h'] > 20 or not at['why']['in']: bad.append((h, kc, kv, before, at, after))
    pg.evaluate("() => { EV.s.step = null; EV.draw(); }")
    say(tried > 0 and not bad, f"{sid}: a hypothesis whose check is recorded before its verdict ({tried} tried, in the replay): at the step of its check its box says “check held” or “check failed” (as the ledger has it) with an edge in that colour and no fill, and the key under the board explains the edge; under the question stands one line that says why (what was measured against the rule, with its numbers), inside the box; one step earlier it says nothing of a check; at the step of the verdict the box is filled by the verdict and the edge and that line are gone" + (f": {bad[:2]}" if bad else ''))
    done(pg)

def part_fold(b):
    print('FOLD'); sid = SIDS[0]; led = ledger(sid); pg = session(b, sid); turns = sorted({r['turn'] for r in led if r['type'] == 'turn' and r['turn'] > 0})
    t = turns[1] if len(turns) > 1 else turns[0]; H = f'#s-notebook .nb-turn[data-turn="{t}"]'; pg.locator(H).scroll_into_view_if_needed(); pg.wait_for_timeout(200)
    top = lambda: pg.evaluate("(s) => Math.round(document.querySelector(s).getBoundingClientRect().top)", H); vis = lambda g: pg.evaluate("(g) => [...document.querySelectorAll(`#s-notebook .nb-group[data-group=\"${g}\"] > :not(.nb-head)`)].filter(c => c.offsetParent).length", str(g))
    t0, c0, sel0 = top(), vis(t), pg.evaluate("JSON.stringify(EV.s.sel)"); pg.click(f'{H} b'); pg.wait_for_timeout(300)
    say(c0 > 0 and vis(t) == 0 and top() == t0 and pg.evaluate("JSON.stringify(EV.s.sel)") == sel0 and pg.get_attribute(H, 'aria-expanded') == 'false', f"{sid}: a click on the heading of turn {t} folds its {c0} parts to that one line; the heading stays where it was ({t0} px), the pane on the right is untouched")
    tested = [x for r in led if r['type'] == 'experiment' and r.get('turn') == t for x in (r['body'].get('tests') or [q['for'] for q in r['body'].get('decision_rules') or []])]; head = pg.inner_text(H)
    say(all(h in head for h in tested), f"{sid}: folded, the heading names the hypotheses the turn tested, each with how it stands ({', '.join(dict.fromkeys(tested)) or 'none'}): “{' '.join(head.split())[:110]}”")
    pg.evaluate("EV.draw()"); pg.wait_for_timeout(300); say(vis(t) == 0, f"{sid}: the turn stays folded when the page is drawn again")
    pg.click(f'{H} .nb-rec'); pg.wait_for_timeout(400); say(pg.evaluate("JSON.stringify(EV.s.sel)") == json.dumps({'t': 'log', 'id': t}, separators=(',', ':')) and vis(t) == 0, f"{sid}: “the turn's record” in the heading opens the turn in the pane (the one place for it), and does not unfold it")
    pg.click(f'{H} b'); pg.wait_for_timeout(300); say(vis(t) == c0, f"{sid}: a second click opens the turn again ({c0} parts)")
    allv = lambda: pg.evaluate("[...document.querySelectorAll('#s-notebook .nb-group:not([data-group=\"0\"]) > :not(.nb-head)')].filter(c => c.offsetParent).length"); n0 = allv()
    pg.click('#nb-folds button[data-id="1"]'); pg.wait_for_timeout(300); f1 = allv(); pg.click('#nb-folds button[data-id="0"]'); pg.wait_for_timeout(300)
    say(f1 == 0 and allv() == n0 and n0 > 0, f"{sid}: “fold every turn” leaves {len(turns)} headings and nothing under them, “open every turn” brings the {n0} parts back")
    done(pg)

def part_values(b):
    print('VALUES'); sid = SIDS[0]; led = ledger(sid); pg = session(b, sid); sims = {(r.get('parent'), r['body'].get('label')): r for r in led if r['type'] == 'simulation'}
    bars = pg.evaluate("""() => [...document.querySelectorAll('#s-notebook .nb-card[data-id] .rb')].slice(0, 60).map(r => { const d = r.querySelector('.rb-hit[data-hit=dot]'), t = r.querySelector('.rb-hit[data-hit=th]'); return { test: r.closest('.nb-card').dataset.id, a: +r.dataset.a, b: +r.dataset.b, held: r.dataset.held, dot: d.dataset.wd.slice(2).split('¦'), th: t.dataset.wd.slice(2).split('¦'), measure: d.dataset.measure || null, sim: d.dataset.sim || null, shown: r.querySelector('.rb-l b').textContent, wide: [...r.querySelectorAll('.rb-th, .rb-dot, .rb-hit')].filter(el => el.scrollWidth > el.clientWidth + 1).length }; })""")
    bad = []; tried = 0
    for x in bars:
        d, t = x['dot'], x['th']; st = 'held' if x['held'] == '1' else 'failed'
        if x['measure']:  # the left side is one measure of one simulation: the dot stands at that simulation's own recorded value
            exp = x['test'].split('.')[0]; own = [s for (e, _), s in sims.items() if e == exp]; rec = sims.get((exp, x['sim'])) or (own[0] if len(own) == 1 else None); tried += 1
            if not rec or x['a'] != rec['body']['metrics'][x['measure']]: bad.append((x['test'], x['measure'], x['sim'], x['a']))
        vague = [w for w in ('left side', 'right side', 'worked out') if w in ' '.join(d + t)]  # each side is said by what it is, never by where it stands in the rule
        if d[0] != x['shown'] or d[1] != 'measured' or not d[2] or d[4] != st or t[4] != st or not d[5].startswith('must be ') or not t[0] or not t[1] or not t[2] or len(d) != 7 or len(t) != 7 or t[6] != x['shown'] or vague or x['wide']: bad.append((x['test'], d, t, x['wide']))  # value | what it is | the measure | where | held or failed | the rule | measured (a threshold)
    say(len(bars) > 0 and tried > 0 and not bad, f"{sid}: each of the {len(bars)} bars on the notebook's cards has a place to point at for its dot and one for its threshold; the dot's box gives the value the card shows and names what it is in words (never “the left side”), and where the left side is one measure of one simulation ({tried} bars) that value is the simulation's own record; both boxes say whether the comparison holds as the bar does; no mark is wider than its place" + (f": {bad[:3]}" if bad else ''))
    for hit, labels in (('dot', ['Measure', 'Simulation', 'Rule']), ('th', ['Measure', 'Simulation', 'Rule', 'Measured'])):
        el = pg.locator(f'#s-notebook .rb .rb-hit[data-hit={hit}]').first; el.scroll_into_view_if_needed(); y = pg.evaluate('scrollY'); el.hover(); pg.wait_for_timeout(450)
        pop = pg.evaluate("() => { const p = document.getElementById('wd-pop'); return p ? { labels: [...p.querySelectorAll('.wd-kv dt')].map(x => x.textContent), values: [...p.querySelectorAll('.wd-kv dd')].map(x => x.innerText.replace(/\\s+/g, ' ').trim()), value: (p.querySelector('[data-wd-value] b') || {}).textContent, chip: (p.querySelector('[data-wd-value] .wd-kind') || {}).textContent, big: parseFloat(getComputedStyle(p.querySelector('[data-wd-value] b')).fontSize), small: Math.min(...[...p.querySelectorAll('p, span, dt, dd')].map(x => parseFloat(getComputedStyle(x).fontSize))), signs: p.querySelectorAll('.wd-kv .rs').length } : null; }")
        ok = pop and [l for l in pop['labels'] if l in ('Measure', 'Simulation', 'Simulations', 'Rule', 'Measured')] == pop['labels'] and 'Measure' in pop['labels'] and 'Rule' in pop['labels'] and (hit == 'dot' or 'Measured' in pop['labels']) and all(pop['values']) and pop['value'] and pop['chip'] and pop['big'] >= 18 and pop['small'] >= 12 and pop['signs'] == 1
        say(ok and pg.evaluate('scrollY') == y, f"{sid}: pointing at the {'dot' if hit == 'dot' else 'threshold'} opens a box at once: the value large with what it is on a chip (“{pop and pop['value']}” · {pop and pop['chip']}), then each thing under its own name: {pop and dict(zip(pop['labels'], pop['values']))}"); pg.mouse.move(5, 5); pg.wait_for_timeout(200)
    done(pg)

def part_names(b):
    print('NAMES')
    for sid in SIDS:
        led = ledger(sid); meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); kn = ((meta.get('given') or {}).get('knobs') or {}); pg = session(b, sid); KNOB = pg.evaluate("TH_DATA.KNOB"); want = {}
        for x in [r for r in led if r['type'] == 'experiment']:
            runs = x['body'].get('runs') or []; nth = {}
            for r in x['body'].get('decision_rules') or x['body'].get('rules') or []:
                n = nth[r['for']] = nth.get(r['for'], 0) + 1; tid = f"{x['id']}.{r['for']}" + (f'.{n}' if n > 1 else ''); ls = labels(r.get('decision_rule') or r.get('rule')); mine = [q for q in runs if q['label'] in ls] if len(ls) > 1 else None
                keys = list(dict.fromkeys(list(kn) + [k for q in runs for k in (q.get('params') or {})])); val = lambda q, k: (q.get('params') or {}).get(k, (kn.get(k) or {}).get('default'))
                for l in ls:
                    me = next((q for q in runs if q['label'] == l), None)
                    if not me: continue
                    group = mine if mine else [me]; vary = [k for k in keys if any(not same(val(q, k), val(group[0], k)) for q in group)]
                    use = vary or [k for k in keys if k in kn and 'default' in kn[k] and not same(val(me, k), kn[k]['default'])]
                    want[f'{tid}|{l}'] = [KNOB.get(k, k) for k in use]
        got = pg.evaluate("""() => { const out = {}; EV.M.tests.filter(T => T.rule).forEach(T => (T.labels || []).forEach(l => { out[T.id + '|' + l] = EV.simSays(T, l); })); return out; }""")
        names = sorted(KNOB.values(), key=len, reverse=True); split = lambda s: [n for n in re.findall('|'.join(re.escape(n) + r'(?= )' for n in names), s)] if s and s != 'every setting at its default' else []
        diff = [(k, got.get(k), want.get(k)) for k in want if split(got.get(k, '')) != want[k]]
        say(len(want) > 0 and not diff, f"{sid}: a simulation named in a rule is said by its settings: for each of the {len(want)} (test, label) pairs the settings named are those in which the test's simulations differ (one simulation: those that are not the brief's defaults), recounted here from the experiments' designs" + (f": {diff[:3]}" if diff else ''))
        shown = pg.evaluate("""() => [...document.querySelectorAll('#s-notebook .nb-card[data-id]')].flatMap(c => [...c.querySelectorAll('[data-l=expected] .sim-lab')].map(l => [c.dataset.id, l.textContent, l.previousElementSibling ? l.previousElementSibling.textContent : null, l.dataset.own]))""")
        bad = [q for q in shown if got.get(f'{q[0]}|{q[1]}') != q[2] or q[3] != 'model']
        say(len(shown) > 0 and not bad, f"{sid}: on the notebook's cards, each of the {len(shown)} places where a rule names a simulation reads “at <its settings>” with the AI's own label small beside it (marked as the AI's): e.g. “at {shown[0][2]} ({shown[0][1]})”" + (f": {bad[:3]}" if bad else ''))
        done(pg)

def part_exps(b):
    print('EXPS'); sid = SIDS[0]; led = ledger(sid); pg = session(b, sid); want = {}
    if not pg.evaluate("() => !!document.getElementById('s-made')"): print('   skipped: the experiments of “The session at a glance” (the card is not drawn since 2026-11-22)'); done(pg); return
    for x in [r for r in led if r['type'] == 'experiment']:
        own = [s for s in led if s['type'] == 'simulation' and s.get('parent') == x['id']]; back = sum(1 for s in own if s['body'].get('same_as'))
        want[x['id']] = f"{x['id']} · {len(own)} simulation{'' if len(own) == 1 else 's'}" + (f" {back} not run again" if back else '')
    base = [r for r in led if r['type'] == 'simulation' and (r.get('parent') in (None, 'X0'))]
    got = pg.evaluate("Object.fromEntries([...document.querySelectorAll('#s-made a.gx')].map(a => [a.dataset.id, (a.innerText + ' ' + ((a.parentElement.querySelector(`.gx-note[data-for=\"${a.dataset.id}\"]`) || {}).innerText || '')).replace(/\\s+/g, ' ').trim()]))")
    cmpw = {k: v for k, v in want.items() if k in got}
    say(len(cmpw) > 0 and all(got[k] == cmpw[k] for k in cmpw), f"{sid}: the glance says what the number after an experiment is, counted here from the ledger: {[got[k] for k in list(cmpw)[:3]]}" + ('' if all(got[k] == cmpw[k] for k in cmpw) else f": {[(got[k], cmpw[k]) for k in cmpw if got[k] != cmpw[k]][:3]}"))
    xs = [r for r in led if r['type'] == 'experiment' and (r['body'].get('decision_rules') or r['body'].get('tests'))]; x = xs[0]; hyps = list(dict.fromkeys([q['for'] for q in x['body'].get('decision_rules') or []] + (x['body'].get('tests') or [])))
    el = pg.locator(f'#s-made a.gx[data-id="{x["id"]}"]'); el.scroll_into_view_if_needed(); y = pg.evaluate('scrollY'); el.hover(); pg.wait_for_timeout(500)
    pop = pg.evaluate("() => { const p = document.getElementById('wd-pop'); return p ? { text: p.innerText.replace(/\\s+/g, ' ').trim(), tests: [...p.querySelectorAll('[data-xp=test] b')].map(x => x.textContent), sims: (p.querySelector('[data-xp=sims]') || {}).textContent, back: (p.querySelector('[data-xp=back]') || {}).textContent || '' } : null; }")
    own = [s for s in led if s['type'] == 'simulation' and s.get('parent') == x['id']]; back = sum(1 for s in own if s['body'].get('same_as'))
    say(pop and pop['tests'] == hyps and pop['sims'].startswith(f"{len(own)} simulation") and (pop['back'].startswith(f'{back} of them') if back else not pop['back']) and pg.evaluate('scrollY') == y, f"{sid}: pointing at {x['id']} in the glance opens a box: the hypotheses it tests ({', '.join(hyps)}), each with how its check ended, its {len(own)} simulations in words (“{pop and pop['sims'][:70]}”)" + (f", {back} not run again" if back else ''))
    pg.mouse.move(5, 5); pg.wait_for_timeout(200); done(pg)

def part_tcp(b):
    print('TCP'); pg = new_page(b, f'{BASE}?tab=new', '#be-conf .be-c-r'); SAYS = pg.evaluate("EV.TCP_SAYS"); card = pg.locator('#be-conf .be-c', has_text='TCP socket').first
    b0 = pg.evaluate("BRIEF_EDITOR.toBrief()"); choices = b0['knobs']['tcpVariant']['choices']; line = lambda k: f"{SAYS[k][0]}: {SAYS[k][1]}"
    say(all(c in SAYS for c in choices) and all(len(v[1].split()) <= 22 for v in SAYS.values()), f"each of the {len(choices)} TCP types the brief offers has one plain line of at most 22 words (the longest: {max(len(v[1].split()) for v in SAYS.values())})")
    first = pg.inner_text('#be-tcp'); other = next(c for c in choices if c != b0['knobs']['tcpVariant']['default']); card.locator('select').select_option(other); pg.wait_for_timeout(300)
    say(first == line(b0['knobs']['tcpVariant']['default']) and pg.inner_text('#be-tcp') == line(other), f"the set-up page: under the TCP type chosen in the TCP socket's card stands its line, and it follows the choice ({other.replace('Tcp', '')}: “{pg.inner_text('#be-tcp')}”)")
    done(pg)
    for sid in SIDS:
        meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); given = meta.get('given') or {}; kn = (given.get('knobs') or {}).get('tcpVariant'); fx = (given.get('system') or {}).get('tcpVariant'); want = [c.replace('Tcp', '') for c in (kn['choices'] if kn else [fx] if fx else [])]
        pg = session(b, sid); w = pg.locator('#ev [data-wd="k:tcpVariant"] >> visible=true').first   # a visible one: the first may stand in a section that is not shown (2026-11-23)
        if not want or w.count() == 0: say(True, f"{sid}: its brief names no TCP type on the page"); done(pg); continue
        w.scroll_into_view_if_needed(); w.hover(); pg.wait_for_timeout(500)
        got = pg.evaluate(r"() => [...document.querySelectorAll('#wd-pop .tcp-l')].map(p => [p.dataset.tcp, p.innerText.replace(/\s+/g, ' ').trim()])"); fits = pg.evaluate("() => { const p = document.getElementById('wd-pop').getBoundingClientRect(); return p.top >= 0 && p.bottom <= innerHeight + 1; }")
        say([g[0] for g in got] == want and all(SAYS['Tcp' + g[0]][1] in g[1] and SAYS['Tcp' + g[0]][0] in g[1] for g in got) and fits, f"{sid}: pointing at “TCP type” opens the setting's box with one line for each of the {len(want)} types its brief {'offers' if kn else 'fixes'} ({', '.join(want)}), and the box fits the window")
        pg.mouse.move(5, 5); pg.wait_for_timeout(200); start = (kn['default'] if kn else fx)
        word = pg.evaluate("() => { EV.s.sysObj = EV.sysId('sender', 'stack', 'TCP socket'); EV.draw(); const el = document.querySelector('#s-system .tcp-word'), d = document.querySelector('#s-system .sy-det.on'); return el ? { tcp: el.dataset.tcp, wd: el.dataset.wd, cut: d.scrollHeight > d.clientHeight + 1 } : null; }")
        pg.locator('#s-system .tcp-word').hover(); pg.wait_for_timeout(500); own = pg.evaluate("(t) => { const p = document.querySelector(`#wd-pop .tcp-l[data-tcp=\"${t}\"]`); return p ? p.innerText : null; }", start.replace('Tcp', ''))
        say(word and word['tcp'] == start.replace('Tcp', '') and word['wd'] == 'k:tcpVariant' and not word['cut'] and own and SAYS[start][1] in own, f"{sid}: in “The setting” the TCP socket's card names the type ({word and word['tcp']}) as a word with a box: pointing at it opens the setting's box with that type's line; the card keeps its height, nothing in it is cut")
        pg.mouse.move(5, 5); pg.evaluate("() => { EV.s.sysObj = ''; EV.draw(); }")
        done(pg)

def part_ns3(b):
    print('NS3'); sid = SIDS[0]; pg = session(b, sid)
    lg = pg.evaluate("() => [...document.querySelectorAll('#ev-legend .lg[data-by]')].map(x => [x.dataset.by, x.textContent.trim()])")
    sup_arm = (json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()).get('flags') or {}).get('arm') == 'supervised'
    want = [['operator', 'operator'], ['model', 'researcher']] + ([['supervisor', 'supervisor']] if sup_arm else []) + [['simulator', 'ns-3'], ['harness', 'harness']]
    say(lg == want, f"{sid}: the legend's sources, in the order the operator set on 2026-11-22: {[q[1] for q in lg]}")
    left = pg.evaluate("() => { document.querySelectorAll('details').forEach(d => { d.open = true; }); const t = document.getElementById('ev').innerText + ' ¦ ' + [...document.querySelectorAll('#ev [title]')].map(x => x.title).join(' ¦ '); return [...new Set((t.match(/.{0,30}\\bsimulator\\b.{0,25}/gi) || []).map(s => s.replace(/\\s+/g, ' ')))]; }")
    ok = [s for s in left if "simulator's code" in s or 'the network simulator' in s]
    say(len(left) == len(ok), f"{sid}: nowhere on the session's page is a record said to be produced by “the simulator”; the word is left where it describes ns-3 (“ns-3, the network simulator”) and in “the simulator's code” ({len(ok)} places)" + ('' if len(left) == len(ok) else f": {[s for s in left if s not in ok][:4]}"))
    done(pg)

def part_key(b):
    print('KEY')
    for sid in SIDS:
        pg = session(b, sid); pg.locator('#map-key').scroll_into_view_if_needed(); pg.wait_for_timeout(200); y0 = pg.evaluate('scrollY')
        r = pg.evaluate("""() => { const q = s => [...document.querySelectorAll(s)], K = ['good', 'bad', 'mixed', 'neutral', 'weak', 'brief'], k = document.getElementById('map-key').getBoundingClientRect(), c = document.getElementById('s-find').getBoundingClientRect();
          return { rows: q('#map-key .mk-grp').map(g => [g.dataset.g, g.querySelector('.mk-h').textContent, !!g.querySelector('.mk-is').textContent.trim()]), listed: q('#map-key .mk[data-k]').map(x => x.dataset.k).sort(),
            drawn: [...new Set(q('#s-map .ev-map path.edge').flatMap(p => [...p.classList]).filter(c => K.includes(c)))].sort(), states: q('#map-key .mk[data-s]').map(x => x.dataset.s).sort(),
            has: [...new Set(q('#s-map .ev-map g[data-node] rect.bx').flatMap(r => [...r.classList]).filter(c => /^st-/.test(c)).map(c => c.slice(3)))].sort(), cls: Object.fromEntries(EV.STATES.map(s => [s, EV.stCls(s).replace(/^st-/, '')])),
            ans: [!!document.getElementById('mk-ans'), q('#s-map .ev-map rect.ring').length > 0], inside: k.left >= c.left && k.right <= c.right + 1, bordered: q('#map-key .mk').filter(x => parseFloat(getComputedStyle(x).borderTopWidth) > 0).length, small: Math.min(...q('#map-key *').filter(x => x.children.length === 0 && x.textContent.trim()).map(x => parseFloat(getComputedStyle(x).fontSize))) }; }""")
        want_states = sorted(st for st, c in r['cls'].items() if st != 'open' and c in r['has'])
        say([x[0] for x in r['rows']] == ['box', 'arrow'] and all(x[2] for x in r['rows']) and r['inside'] and r['bordered'] == 0 and r['small'] >= 12,
            f"{sid}: the board's key is one table of two rows, “{r['rows'][0][1]}” and “{r['rows'][1][1]}”, each saying what the mark is; it stands inside its card, its looks have no borders of their own, and its smallest text is {r['small']} px")
        say(r['listed'] == r['drawn'] and r['states'] == want_states and r['ans'][0] == r['ans'][1], f"{sid}: the key lists exactly the looks the board has: arrows {r['listed']} (drawn: {r['drawn']}), boxes {r['states']} (drawn: {want_states}), the ring {'listed and drawn' if r['ans'][0] else 'neither listed nor drawn'}")
        bad = []; items = pg.locator('#map-key .mk[data-wd]'); n = items.count()
        for i in range(n):
            el = items.nth(i); key = el.get_attribute('data-wd'); el.hover(); pg.wait_for_timeout(300)
            got = pg.evaluate("(k) => { const p = document.getElementById('wd-pop'), s = EV.LEGEND_SAYS[k.slice(2)], b = p && p.getBoundingClientRect(); return { text: p ? p.innerText : null, want: s ? s[2] : null, inside: !!p && b.left >= 0 && b.right <= innerWidth && b.top >= 0 && b.bottom <= innerHeight, y: scrollY }; }", key)
            if not got['text'] or not got['want'] or got['want'] not in got['text'] or not got['inside'] or got['y'] != y0: bad.append((key, got))
        pg.mouse.move(5, 5); pg.wait_for_timeout(200)
        say(n > 0 and not bad and not pg.evaluate("!!document.getElementById('wd-pop')"), f"{sid}: pointing at each of the key's {n} looks opens a box with its sentence, inside the window; the page does not move, and the box goes when the pointer leaves" + (f": {bad[:2]}" if bad else ''))
        wide = []
        for w in (900, 1100, 1280, 1800):
            pg.set_viewport_size({'width': w, 'height': 1000}); pg.wait_for_timeout(350)
            if pg.evaluate("document.documentElement.scrollWidth > innerWidth + 1"): wide.append(w)
        say(not wide, f"{sid}: the key makes nothing scroll sideways from 900 to 1,800 px" + (f": {wide}" if wide else ''))
        done(pg)

def part_board(b):
    print('BOARD')
    for sid in SIDS:
        pg = session(b, sid); pg.locator('#s-map').scroll_into_view_if_needed(); pg.wait_for_timeout(200)
        r = pg.evaluate("""() => { const q = s => [...document.querySelectorAll(s)], m = document.querySelector('#s-map .ev-map'), xs = q('#s-map line.map-sep').map(l => Number(l.getAttribute('x1'))),
          bx = q('#s-map .ev-map rect.bx').map(r => [Number(r.getAttribute('x')), Number(r.getAttribute('x')) + Number(r.getAttribute('width'))]);
          return { cols: Number(m.dataset.cols), seps: xs.length, through: xs.filter(x => bx.some(([a, z]) => x > a - 2 && x < z + 2)).length, between: xs.every((x, i) => bx.some(([a, z]) => z < x) && bx.some(([a]) => a > x)),
            width: q('#s-map line.map-sep').map(l => parseFloat(getComputedStyle(l).strokeWidth))[0] }; }""")
        say(r['seps'] == r['cols'] - 1 and r['through'] == 0 and r['between'] and r['width'] <= 1, f"{sid}: a light rule ({r['width']} px, dashed) stands between each two of the board's {r['cols']} columns ({r['seps']} rules), with boxes on both sides and through none")
        # the aim's box opens the aim
        meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); goal = ((meta.get('given') or {}).get('goal') or {}); rep = next((r['body'] for r in reversed(ledger(sid)) if r['type'] == 'report'), {})
        y0 = pg.evaluate('scrollY'); pg.locator('#s-map g[data-act=open][data-t=brief][data-aim]').first.click(); pg.wait_for_timeout(400)
        d = pg.evaluate("""() => { const p = document.getElementById('p-detail'), a = p.querySelector('#bc-aim'), h = [...p.querySelectorAll('h3')]; const t = el => (el ? el.innerText.replace(/\\s+/g, ' ').trim() : null);
          return { first: h.length ? h[0].closest('#bc-aim') === a && !!a : false, kind: a ? a.dataset.aim : null, goal: t(p.querySelector('#bc-goal')), chose: t(p.querySelector('#bc-chose')), none: !!(p.querySelector('#bc-chose') || { dataset: {} }).dataset.none, who: t(p.querySelector('.bc-who')), y: scrollY }; }""")
        flat = lambda v: re.sub(r'\s+', ' ', str(v or '')).strip()
        if goal.get('kind') == 'open':
            ok = d['first'] and d['kind'] == 'open' and ((rep.get('goal') and not d['none'] and flat(d['chose']).replace(' ', '') == flat(rep['goal']).replace(' ', '') and 'at the end' in (d['who'] or '')) or (not rep.get('goal') and d['none']))
            say(ok and d['y'] == y0, f"{sid}: a click on the aim's box opens the brief with the aim first: left open, and " + (f"the aim the AI chose, whole ({len(flat(rep.get('goal')))} characters, as in its final report), said to be stated at the end" if rep.get('goal') else 'that the AI stated none') + '; the page does not move')
        else:
            say(d['first'] and d['kind'] == 'given' and d['goal'] and 'set by the operator' in d['goal'] and d['chose'] is None and d['y'] == y0, f"{sid}: a click on the aim's box opens the brief with the aim first: the brief's own (“{(d['goal'] or '')[:60]}…”), set by the operator; the page does not move")
        # the table under the board: its button, and what Full and Brief do
        if pg.locator('#find-list').count():
            R = "() => { const d = document.getElementById('find-list'), b = d.querySelector('summary .fl-btn'), v = [...b.children].filter(x => getComputedStyle(x).display !== 'none').map(x => x.textContent); return { open: d.open, word: v.join('|'), edge: parseFloat(getComputedStyle(b).borderTopWidth), y: Math.round(d.getBoundingClientRect().top + scrollY) }; }"
            pg.evaluate("() => { EV.store('ev-find', '0'); EV.s.findOpen = null; EV.act.level('brief'); }"); pg.wait_for_timeout(300); f0 = pg.evaluate(R)
            pg.click('#find-list > summary'); pg.wait_for_timeout(250); f1 = pg.evaluate(R); pg.evaluate("EV.draw()"); pg.wait_for_timeout(250); f2 = pg.evaluate(R)
            pg.click('#find-list > summary'); pg.wait_for_timeout(250); f3 = pg.evaluate(R)
            pg.evaluate("EV.act.level('full')"); pg.wait_for_timeout(350); f4 = pg.evaluate(R); pg.click('#find-list > summary'); pg.wait_for_timeout(250); pg.evaluate("EV.draw()"); pg.wait_for_timeout(250); f5 = pg.evaluate(R)
            pg.evaluate("EV.act.level('brief')"); pg.wait_for_timeout(350); f6 = pg.evaluate(R)
            seq = [(f['open'], f['word']) for f in (f0, f1, f2, f3, f4, f5, f6)]
            say(seq == [(False, 'open'), (True, 'fold'), (True, 'fold'), (False, 'open'), (True, 'fold'), (False, 'open'), (False, 'open')] and f0['edge'] >= 1,
                f"{sid}: “The same, test by test” has a button with an edge that says what a click will do (open / fold); opened, it stays open through a redraw; Full opens it, and folded there it stays folded through a redraw; back in Brief it is as it was left there" + ('' if f0['edge'] >= 1 else ' (no edge)') + f": {seq}")
            pg.evaluate("() => { EV.store('ev-find', '0'); EV.s.findOpen = null; EV.act.level('brief'); }")
        done(pg)

def part_short(b):
    print('SHORT')
    for sid in SIDS:
        pg = session(b, sid)
        R = """() => [...document.querySelectorAll('#ev .rb-t')].filter(t => t.getBoundingClientRect().width > 0).map(t => { const r = t.getBoundingClientRect(), marks = [...t.querySelectorAll('.rb-dot, .rb-th')].map(m => { const q = m.getBoundingClientRect(); return (q.left + q.right) / 2; });
            return { w: Math.round(r.width), in: marks.every(x => x >= r.left - 1 && x <= r.right + 1), n: marks.length, where: t.closest('#p-detail') ? 'detail' : 'page' }; })"""
        page = pg.evaluate(R); tid = pg.evaluate("() => { const t = EV.M.tests.find(t => t.check && EV.ruleBars(t, 0)); if (!t) return null; EV.s.sel = { t: 'test', id: t.id }; EV.draw(); return t.id; }"); pg.wait_for_timeout(400); both = pg.evaluate(R)
        det = [x for x in both if x['where'] == 'detail']
        if not page and not det: say(True, f"{sid}: no rule of this session is drawn as a bar"); done(pg); continue
        say(all(x['w'] <= 300 and x['in'] and x['n'] for x in page + det) and (not tid or det), f"{sid}: a rule's bar is at most 300 px long ({len(page)} on the page: {sorted(set(x['w'] for x in page))} px; {len(det)} in the detail of test {tid}: {sorted(set(x['w'] for x in det))} px), with its dot and its threshold inside it")
        done(pg)

def part_none(b):
    print('NONE'); pg = new_page(b, f'{BASE}?tab=new', '#be-conf .be-c-r'); first = json.loads((ROOT / 'briefs' / 'two-hosts-open.json').read_text())
    R = "() => ({ sel: document.getElementById('be-open').value, off: document.getElementById('be-open').disabled, shown: document.getElementById('be-open').selectedOptions[0].textContent, box: document.getElementById('be-none').checked, label: document.querySelector('label.be-none').innerText.replace(/\\s+/g, ' ').trim(), opts: [...document.querySelectorAll('#be-open option')].map(o => [o.value, o.textContent]), state: document.getElementById('be-state').innerText, start: [document.getElementById('be-start').textContent, document.getElementById('be-start').disabled], save: document.getElementById('be-save').disabled, bad: BRIEF_EDITOR.problems(), brief: BRIEF_EDITOR.toBrief() })"
    r0 = pg.evaluate(R); saved = sorted(p.stem for p in (ROOT / 'briefs').glob('*.json') if 'topology' not in json.loads(p.read_text()))   # a brief that has a network is offered to the builder, not to this form
    say(sorted(o[0] for o in r0['opts']) == saved and r0['sel'] in saved and not r0['off'] and not r0['box'] and r0['label'].startswith('or start from an empty set-up'), f"the list “Start from a saved brief” holds the {len(saved)} saved briefs that have no network and nothing else, and the page opens on one ({r0['sel']}); under it stands a box of its own, not ticked: “{r0['label'][:60]}”")
    other = next(s for s in saved if s != 'two-hosts-open'); pg.select_option('#be-open', other); pg.wait_for_timeout(1000)
    pg.check('#be-none'); pg.wait_for_timeout(1000); r1 = pg.evaluate(R); br = r1['brief']
    want = {**first['system'], **{k: v['default'] for k, v in first['knobs'].items()}}
    say(r1['box'] and 'task' not in br and br['description'] == '' and br['knobs'] == {} and br['goal'] == {'kind': 'open'} and br['limits'] == first['limits'] and all(same(br['system'].get(k), v) for k, v in want.items()) and set(br['system']) == set(want),
        f"ticked, the form is empty: no description, no knob, the aim open (the task is not typed: the harness writes it); the {len(want)} settings stand fixed at the first brief's values and its limits ({br['limits']})")
    say(r1['off'] and r1['sel'] == '' and 'not used' in r1['shown'], f"the list is off while the box is ticked and says so (“{r1['shown']}”)")
    say(sorted(r1['bad']) == ['description'] and r1['start'][1] and r1['save'], f"the form says what an empty set-up still needs (the description: “{r1['bad'].get('description')}”), and neither button can be pressed")
    pg.fill('textarea[data-f=description]', 'A description.'); pg.press('textarea[data-f=description]', 'Tab'); pg.wait_for_timeout(400); r2 = pg.evaluate(R)
    say(not r2['bad'] and 'The form started empty' in r2['state'] and '1 value filled in or changed' in r2['state'] and r2['box'] and r2['off'], f"with a description nothing is refused any more, and the box is still ticked; the line under the form: “{r2['state'][:80]}”")
    say(r2['start'][1] and 'name' in r2['state'], f"it cannot be started before it has a name of its own (“{r2['start'][0]}” is off, and the line asks for a name)")
    pg.uncheck('#be-none'); pg.wait_for_timeout(1000); r3 = pg.evaluate(R); disk = json.loads((ROOT / 'briefs' / f'{other}.json').read_text())
    say(not r3['box'] and not r3['off'] and r3['sel'] == other and r3['brief']['description'] == disk['description'].strip() and set(r3['brief']['knobs']) == set(disk['knobs']) and f'saved brief {other}' in r3['state'] and sorted(o[0] for o in r3['opts']) == saved, f"unticked, the list is on again and the form is filled from the brief it held before ({other}: “{r3['state'][:50]}”)")
    done(pg)

def part_legend(b):
    print('LEGEND'); sid = SIDS[0]; pg = session(b, sid); y0 = pg.evaluate('scrollY'); items = pg.locator('#ev-legend [data-wd]'); n = items.count(); bad = []
    for i in range(n):
        el = items.nth(i); key = el.get_attribute('data-wd'); el.hover(); pg.wait_for_timeout(300)
        got = pg.evaluate("(k) => { const p = document.getElementById('wd-pop'), s = EV.LEGEND_SAYS[k.slice(2)], b = p && p.getBoundingClientRect(); return { text: p ? p.innerText : null, want: s ? [s[0], s[2], s[3]] : null, inside: !!p && b.left >= 0 && b.right <= innerWidth && b.top >= 0 && b.bottom <= innerHeight, y: scrollY }; }", key)
        if not got['text'] or not got['want'] or not all(w in got['text'] for w in got['want']) or not got['inside'] or got['y'] != y0: bad.append((key, got))
    pg.mouse.move(5, 300); pg.wait_for_timeout(200); h = pg.evaluate("Math.round(document.getElementById('ev-legend').getBoundingClientRect().height)")
    say(n >= 9 and not bad and h <= 26, f"{sid}: each of the legend's {n} items opens a box with its name, what it means and where it is seen, inside the window, and the page does not move; the legend is {h} px high" + (f": {bad[:2]}" if bad else ''))
    done(pg)

def part_home(b):
    print('HOME'); ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200])); long = 'two-hosts-udp-demand-coarse-ratio-and-more'
    def status(route):
        r = route.fetch(); st = r.json(); st['sessions'][-1].update(running=True, how=None, brief=long); route.fulfill(status=200, content_type='application/json', body=json.dumps(st))
    pg.route('**/api/status*', status); pg.goto(BASE); pg.wait_for_selector('#home-rows tr', timeout=60000); pg.wait_for_timeout(1500)
    R = """() => { const t = document.querySelector('#home-rows'), sc = t.closest('.ev-scroll'), run = t.querySelector('tr.run'), d = t.querySelector('td[data-col=started]');
      return { scrollW: sc.scrollWidth, clientW: sc.clientWidth, heights: [...new Set([...t.children].map(r => Math.round(r.getBoundingClientRect().height)))], rows: t.children.length,
        run: run ? { dot: !!run.children[0].querySelector('.nowdot'), pill: !!run.querySelector('.pill'), brief: run.children[1].title, cut: run.children[1].scrollWidth > run.children[1].clientWidth, how: run.children[3].innerText.trim() } : null,
        started: [...t.querySelectorAll('td[data-col=started]')].map(d => [d.textContent.trim(), d.title]) }; }"""
    wide = []
    for w in (1280, 1440, 1800):
        pg.set_viewport_size({'width': w, 'height': 900}); pg.wait_for_timeout(400); h = pg.evaluate(R)
        if w >= 1440 and h['scrollW'] > h['clientW']: wide.append((w, h['scrollW'], h['clientW']))
    pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(400); h = pg.evaluate(R)
    say(not wide and h['heights'] == [h['heights'][0]] and h['run'] and h['run']['dot'] and not h['run']['pill'] and h['run']['brief'] == long and h['run']['cut'] and h['run']['how'].startswith('running now'),
        f"Home with a session running on a brief with a name of {len(long)} characters: at 1,440 px the table is {h['scrollW']} px wide in {h['clientW']} and does not scroll sideways (nor at 1,800), each of the {h['rows']} rows is {h['heights'][0]} px high; the running session has the moving dot beside its name and “running now”, the long name is cut with its whole in the cell's box" + (f": {wide}" if wide else ''))
    ok = [d for d in h['started'] if d[0] == 'not recorded' or (re.fullmatch(r'\d\d-\d\d \d\d:\d\d', d[0]) and re.fullmatch(r'\d{4}-' + re.escape(d[0]) + r'(:\d\d)?', d[1]))]
    say(len(ok) == len(h['started']) and len(h['started']) == h['rows'], f"when a session started is said as month-day hour:minute ({h['started'][0][0]}), with the whole time in the cell's box ({h['started'][0][1]}), in all {len(h['started'])} rows")
    say(not pg.errs, f"script errors: {pg.errs[:3] or 'none'}"); ctx.close()

def part_marks(b):
    print('MARKS')
    for sid in SIDS:
        pg = session(b, sid)
        r = pg.evaluate("""() => { const q = s => [...document.querySelectorAll(s)], look = el => { const c = getComputedStyle(el), bf = getComputedStyle(el, '::before'); return [c.backgroundColor, c.borderTopStyle, c.borderTopColor, c.color, bf.content].join('|'); };
          const ws = q('#s-research tbody .rs-w'); return { words: ws.map(w => [w.dataset.w, look(w), Math.round(w.getBoundingClientRect().width), parseFloat(getComputedStyle(w).fontSize), getComputedStyle(w).fontWeight]),
            key: q('#s-made .gl-key > span').map(x => [x.textContent.trim().slice(0, 30), parseFloat(getComputedStyle(x).borderTopWidth), Math.round(x.getBoundingClientRect().right), x.id, x.classList.contains('gl-note'), Math.round(x.getBoundingClientRect().top)]), card: (el => (el ? Math.round(el.getBoundingClientRect().right) : null))(document.getElementById('s-made')), doc: document.documentElement.scrollWidth, win: innerWidth }; }""")
        looks = {}
        for w, lk, width, size, weight in r['words']: looks.setdefault(w, set()).add(lk)
        strong = [x for x in r['words'] if x[0] in ('present', 'partly', 'absent', 'not-yet')]
        say(r['words'] and all(len(v) == 1 for v in looks.values()) and len({next(iter(v)) for v in looks.values()}) == len(looks) and len({x[2] for x in strong}) <= 1 and all(x[3] >= 13 and int(x[4]) >= 600 for x in strong) and all('none' not in next(iter(looks[w])).split('|')[4] for w in looks if w in ('present', 'partly', 'absent', 'not-yet')),
            f"{sid}: the {len(r['words'])} lines of “How it worked as a researcher” end in a word with a look of its own ({', '.join(sorted(looks))}: each differs from the others in fill, edge or sign, and each has a sign before it); present, partly, absent and not yet are {sorted({x[2] for x in strong})} px wide, in {min(x[3] for x in strong) if strong else '-'} px type, bold")
        items = [k for k in r['key'] if not k[4]]; notes = [k for k in r['key'] if k[4]]
        if not r['key']: print(f'   {sid}: skipped: the key of “The session at a glance” (the card is not drawn since 2026-11-22)')
        else: say(items and all(k[1] >= 1 for k in items) and len(notes) == 2 and all(k[1] == 0 for k in notes) and min(k[5] for k in notes) > max(k[5] for k in items) and all(k[2] <= r['card'] for k in r['key']) and r['doc'] <= r['win'],
            f"{sid}: each of the {len(items)} items of the key of “The session at a glance” that explains a mark has a border of its own; the two sentences about the card (“{notes[0][0] if notes else ''}…”, “{notes[1][0] if len(notes) > 1 else ''}…”) have none and stand on a line of their own under them; all inside the card, and nothing scrolls sideways")
        done(pg)

def part_either(b):
    print('EITHER'); sids = (ARGS[ARGS.index('--either') + 1] if '--either' in ARGS else 's008,s010,s012').split(',')
    OPS = {'>': lambda a, c: a > c, '>=': lambda a, c: a >= c, '<': lambda a, c: a < c, '<=': lambda a, c: a <= c, '==': lambda a, c: a == c}
    for sid in sids:
        led = ledger(sid); pg = session(b, sid)
        tests = pg.evaluate("() => EV.M.tests.filter(t => t.rule && /\\bor\\b|\\|\\|/i.test(t.rule) && t.check && !t.check.void).map(t => ({ id: t.id, hyp: t.hyp, check: t.check.id, result: t.check.result, groups: !!EV.ruleGroups(t) }))")
        if not tests: say(False, f"{sid}: no checked rule with an “or” in it: name sessions that have one (--either)"); done(pg); continue
        bad = []; n_cmp = n_grp = sentence = 0; y0 = None
        for t in tests:
            r = pg.evaluate("""(id) => { EV.s.sel = { t: 'test', id }; EV.draw(); const p = document.getElementById('p-detail'), res = p.querySelector('[data-td=result]'), exp = p.querySelector('[data-td=expected]'), txt = el => el.innerText.replace(/\\s+/g, ' ');
              const grp = root => [...root.querySelectorAll('.ro')].map(g => ({ held: g.dataset.held === undefined ? null : g.dataset.held === '1', word: (g.querySelector('.ro-r') || { innerText: '' }).innerText.trim(), head: !!g.querySelector('.ro-h'),
                alts: [...g.querySelectorAll('.ro-alt')].map(a => ({ met: a.dataset.met === undefined ? null : a.dataset.met === '1', sign: !!a.querySelector('.ro-b > .gk'), grey: getComputedStyle(a).color, either: (a.querySelector('.ro-j') || { textContent: '' }).textContent,
                  cmps: [...a.querySelectorAll('.ro-c')].map(c => ({ op: c.dataset.op, met: c.dataset.met === undefined ? null : c.dataset.met === '1', a: c.dataset.a === undefined ? null : Number(c.dataset.a), b: c.dataset.b === undefined ? null : Number(c.dataset.b), not: /\\bnot (over|under|at least|at most|equal to)\\b/.test(c.querySelector('.ro-w').textContent) })) })) }));
              return { res: grp(res), exp: grp(exp), bars: res.querySelectorAll('.rb').length, badge: (res.querySelector('[data-rr=check]') || { textContent: '' }).textContent.trim(), notHold: (txt(res).match(/does not hold/g) || []).length, expNums: exp.querySelectorAll('.ro-c[data-met]').length, chain: document.getElementById('td-chain') ? document.getElementById('td-chain').open : null, flowW: (document.querySelector('#td-chain .t-flow') || { clientWidth: -1 }).clientWidth, rule: !!p.querySelector('[data-td=result] .rr, [data-td=result] code'), key: !!res.querySelector('.ro-key'), primary: getComputedStyle(p).color }; }""", t['id'])
            if not t['groups']:   # nested deeper than either-or groups: the sentence, and no bars
                sentence += 1
                if r['bars'] or r['res'] or not r['rule']: bad.append((t['hyp'], 'a rule nested deeper is a sentence without bars', r['bars'], len(r['res'])))
                continue
            if r['bars'] or not r['res'] or len(r['exp']) != len(r['res']) or r['expNums'] or r['chain'] is not False: bad.append((t['hyp'], 'lines, no bars, the same groups under Expected without numbers, the chain folded', r['bars'], len(r['res']), len(r['exp']), r['expNums'], r['chain'])); continue
            whole = True
            for g in r['res']:
                n_grp += 1; alts = []
                for a in g['alts']:
                    cs = []
                    for c in a['cmps']:
                        n_cmp += 1
                        if c['a'] is None or c['b'] is None or c['op'] not in OPS: bad.append((t['hyp'], 'a comparison without its two numbers', c)); cs.append(None); continue
                        want = OPS[c['op']](c['a'], c['b']); cs.append(want)
                        if c['met'] != want or c['not'] != (not want): bad.append((t['hyp'], 'a comparison', c, want))
                    am = all(x is True for x in cs); alts.append(am)
                    if a['met'] != am or (len(g['alts']) > 1 and a['sign'] != am) or (len(g['alts']) > 1 and (a['grey'] == r['primary']) != am): bad.append((t['hyp'], 'an alternative: met, its sign, grey when it is not met', a['met'], am, a['sign'], a['grey']))
                gh = any(alts); whole = whole and gh
                if g['held'] != gh or g['word'] != ('holds' if gh else 'does not hold') or (len(g['alts']) > 1 and [a['either'] for a in g['alts']][:2] != ['either', 'or']): bad.append((t['hyp'], 'a group', g['held'], gh, g['word']))
            if whole != (t['result'] == 'held') or (t['result'] in r['badge']) is False: bad.append((t['hyp'], "the groups together against the harness's check", whole, t['result'], r['badge']))
            if t['result'] == 'held' and r['notHold']: bad.append((t['hyp'], '“does not hold” under a rule that held', r['notHold']))
            if not r['key']: bad.append((t['hyp'], 'the line that says what an either-or is'))
        ok_n = len(tests) - sentence
        say(not bad and ok_n > 0, f"{sid}: {ok_n} checked rule{'s' if ok_n != 1 else ''} with an “or” ({n_grp} groups, {n_cmp} comparisons) stand as either-or lines in the test's detail, and none as bars: each comparison worked out again from its two numbers says “not …” exactly when it is not met; an alternative is met when all its comparisons are, has the sign then and is grey otherwise; a group holds when one alternative is met; all groups together give the result the harness recorded; under a rule that held no line says “does not hold”; “Expected” lists the same groups without numbers" + (f"; {sentence} nested deeper stay a sentence" if sentence else '') + (f": {bad[:3]}" if bad else ''))
        # the chain of boxes: folded, opens with a click and is drawn then, and the browser remembers it
        pg.wait_for_timeout(400); pg.evaluate("document.querySelector('#td-chain > summary').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(300); y0 = pg.evaluate('scrollY'); pg.click('#td-chain > summary'); pg.wait_for_timeout(400); o1 = pg.evaluate("() => ({ open: document.getElementById('td-chain').open, w: document.querySelector('#td-chain .t-flow').clientWidth, boxes: document.querySelectorAll('#td-chain .t-flow svg *').length, store: localStorage.getItem('ev-chain'), y: scrollY })")
        pg.evaluate("EV.draw()"); pg.wait_for_timeout(300); o2 = pg.evaluate("() => ({ open: document.getElementById('td-chain').open, boxes: document.querySelectorAll('#td-chain .t-flow svg *').length })")
        pg.click('#td-chain > summary'); pg.wait_for_timeout(300); o3 = pg.evaluate("() => ({ open: document.getElementById('td-chain').open, store: localStorage.getItem('ev-chain') })")
        say(o1['open'] and o1['w'] > 200 and o1['boxes'] > 10 and o1['store'] == '1' and o1['y'] == y0 and o2['open'] and o2['boxes'] > 10 and not o3['open'] and o3['store'] == '0', f"{sid}: the chain of boxes is folded in a test's detail; a click on its line opens it and draws it to the pane's width ({o1['w']} px, {o1['boxes']} marks), the page does not move, it stays open through a redraw, and the browser remembers open and closed" + ('' if o1['open'] and o2['open'] and not o3['open'] and o1['y'] == y0 else f": {y0, o1, o2, o3}"))
        done(pg)

def part_close(b):
    print('CLOSE'); sids = (ARGS[ARGS.index('--close') + 1] if '--close' in ARGS else 's014,s013').split(',')
    sys.path.insert(0, str(ROOT / 'harness')); import importlib; dr = importlib.import_module('decision_rules'); outs = json.loads((ROOT / 'harness' / 'manifest.json').read_text())['outputs']
    for sid in sids:
        led = ledger(sid); meta = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text()); goal = ((meta.get('given') or {}).get('goal') or {}); tol = goal['tolerance'] if type(goal.get('tolerance')) in (int, float) else 1.0
        want = {}; n_rules = 0
        for i, x in enumerate(led):
            if x['type'] != 'experiment' or 'runs' not in x['body']: continue
            sims = [r for r in led if r['type'] == 'simulation' and r.get('parent') == x['id']]; values = {q['body']['label']: q['body'].get('metrics') for q in sims}; labels = [q['label'] for q in x['body']['runs']]
            for d in x['body'].get('decision_rules') or []:
                ck = next((r for r in led if r['type'] == 'check' and r.get('parent') == x['id'] and r['body'].get('for') == d.get('for') and r['body'].get('decision_rule') == d.get('decision_rule')), None)
                if not ck or ck['body'].get('result') not in ('held', 'failed') or 'decision_rule' not in d: continue
                n_rules += 1; k = led.index(ck); earlier = {v for r in led[:k] if r['type'] == 'simulation' for v in (r['body'].get('metrics') or {}).values() if type(v) in (int, float) and v}
                try: cs = dr.comparisons(d['decision_rule'], outs, labels, values)
                except Exception: continue
                res = lambda kinds, a, c: kinds == ('measured', 'measured') or (kinds == ('measured', 'number') and c in earlier) or (kinds == ('number', 'measured') and a in earlier)
                close = [round(100 * abs(a - c) / max(abs(a), abs(c)), 6) for a, op, c, kinds in cs if res(kinds, a, c) and op != '==' and max(abs(a), abs(c)) > 0 and 100 * abs(a - c) / max(abs(a), abs(c)) < tol]
                if close: want[(x['id'], d['for'], d['decision_rule'])] = close
        pg = session(b, sid)
        got = pg.evaluate("() => ({ tol: EV.tolerance(), void: EV.M.tests.filter(t => t.check && t.check.void).map(t => [t.exp, t.hyp, t.rule]), tests: EV.M.tests.filter(t => t.check && !t.check.void).map(t => ({ id: t.id, key: [t.exp, t.hyp, t.rule], check: t.check.id, pct: EV.closeCalls(t).map(c => +c.pct.toFixed(6)) })) })")
        page = {tuple(t['key']): t['pct'] for t in got['tests'] if t['pct']}; void = {tuple(k) for k in got['void']}; n_void = len([k for k in want if k in void])
        want = {k: v for k, v in want.items() if k not in void}   # a void check (two labels of its rule are one simulation) is shown as void: it compared a simulation with itself, and says so
        same = set(page) == set(want) and all(len(page[k]) == len(want[k]) and all(abs(a - c) < 2e-6 for a, c in zip(page[k], want[k])) for k in page)
        say(got['tol'] == tol and same and (want or sid not in ('s014', 's013', 's016', 's019')), f"{sid}: with the tolerance of {tol:g} %, {len(want)} of its {n_rules} checked rules were decided by less than it (worked out here with the harness's own reader of rules, from the records); the page marks the same tests with the same differences" + (f" ({n_void} more are void checks, which the page shows as void)" if n_void else '') + ('' if same else f": only here {sorted(set(want) - set(page))[:2]}, only on the page {sorted(set(page) - set(want))[:2]}"))
        marked = [t for t in got['tests'] if t['pct']]; plain = [t for t in got['tests'] if not t['pct']]; bad = []
        for t in marked[:3]:
            d = pg.evaluate("""(id) => { EV.s.sel = { t: 'test', id }; EV.draw(); const p = document.querySelector('#p-detail [data-td=result] .tol-note'), c = document.querySelector(`#s-notebook .nb-card[data-id="${id}"] .tol-note`); const t = el => (el ? el.innerText.replace(/\\s+/g, ' ').trim() : null);
              return { n: p ? Number(p.dataset.close) : 0, tol: p ? Number(p.dataset.tol) : null, text: t(p), card: t(c), warn: !!(p && p.querySelector('.gk')) }; }""", t['id'])
            if d['n'] != len(t['pct']) or d['tol'] != tol or not d['warn'] or 'count as equal' not in (d['text'] or '') or 'no meaningful difference' not in (d['card'] or ''): bad.append((t['id'], d))
        for t in plain[:2]:
            d = pg.evaluate("(id) => { EV.s.sel = { t: 'test', id }; EV.draw(); return document.querySelectorAll(`#p-detail .tol-note, #s-notebook .nb-card[data-id=\"${id}\"] .tol-note`).length; }", t['id'])
            if d: bad.append((t['id'], 'a note on a test that was not close'))
        if marked: say(not bad, f"{sid}: a marked test says so in its detail (how many comparisons, the two numbers, the difference, that two results closer than the tolerance count as equal) and on its notebook card (“… no meaningful difference”), with the sign of what needs a look; a test that was not close has no such line ({min(3, len(marked))} and {min(2, len(plain))} tried)" + (f": {bad[:2]}" if bad else ''))
        done(pg)

def part_plain(b):
    print('PLAIN')
    FIND = r"""() => { const rgb = v => { let m = /^rgba?\(([^)]+)\)/.exec(v); if (m) { const q = m[1].split(/[ ,\/]+/).map(Number); return q.length > 3 && q[3] === 0 ? null : q.slice(0, 3); }
        m = /^color\(srgb ([^)]+)\)/.exec(v); if (m) { const q = m[1].split(/[ \/]+/).map(Number); return q.length > 3 && q[3] === 0 ? null : q.slice(0, 3).map(x => x * 255); } return null; };
      const violet = c => !!c && c[2] - c[1] > 40 && c[0] - c[1] > 8 && c[2] > c[0], out = [];
      document.querySelectorAll('#ev *').forEach(el => { if (el.closest('i.sw, .lv-ico, svg, .sy') || el.matches('i, svg')) return; const c = getComputedStyle(el), r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
        const tests = [['fill', c.backgroundColor, 1], ['text', c.color, el.childNodes.length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) ? 1 : 0], ...['Left', 'Right', 'Top', 'Bottom'].map(s => ['edge ' + s.toLowerCase(), c['border' + s + 'Color'], parseFloat(c['border' + s + 'Width'])])];
        tests.forEach(([k, v, on]) => { if (on && violet(rgb(v))) out.push(`${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}.${String(el.className).split(' ')[0]} ${k} ${v}`); }); });
      return { n: document.querySelectorAll('#ev *').length, claims: document.querySelectorAll('#rp .rp-claim').length, bad: [...new Set(out)].slice(0, 6) }; }"""
    for sid in SIDS[:1] + [x for x in ('r1',) if (ROOT / 'sessions' / x).is_dir()]:
        pg = session(b, sid); pg.evaluate("() => { EV.s.full = true; EV.s.sel = { t: 'report', id: 'report' }; EV.draw(); }"); pg.wait_for_timeout(400); r = pg.evaluate(FIND)
        say(r['claims'] > 0 and r['n'] > 500 and not r['bad'], f"{sid}, in Full with the final report open in the pane ({r['claims']} claims, {r['n']} elements looked at): nothing but the small icons is violet: {r['bad'] or 'none'}")
        done(pg)

def part_shared(b):
    print('SHARED'); sid = SIDS[0]; state = {}
    def new(url, wait):
        ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); pg = ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
        def change(route):
            resp = route.fetch(); d = resp.json(); rows = d['sessions'] if isinstance(d, dict) else d
            if state.get('run'):
                for x in rows:
                    if x['id'] == sid: x.update(running=True, stoppable=state.get('stoppable', True), by=state['by'], can_stop=state['you'] in (state['by'], state['owner']) and state.get('stoppable', True))
            if isinstance(d, dict):
                d.update(you=state.get('you', d.get('you')), owner=state.get('owner', d.get('owner')), running_now=[{'id': sid, 'by': state['by']}] if state.get('run') else [])
                if state.get('old'): [d.pop(k, None) for k in ('you', 'owner', 'running_now', 'one_at_a_time', 'share')]
            route.fulfill(response=resp, body=json.dumps(d), headers={**resp.headers, 'content-type': 'application/json'})
        pg.route('**/api/status*', change); pg.route('**/api/sessions*', change); pg.goto(url); pg.wait_for_selector(wait, timeout=60000); pg.wait_for_timeout(900); return pg
    T = "el => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null)"
    # nothing running
    state.clear(); pg = new(f'{BASE}?tab=new', '#new-setup #be-start'); pg.wait_for_function("() => document.querySelector('#be-pic svg.sy')", timeout=60000); pg.wait_for_timeout(600)
    r = pg.evaluate(f"() => {{ const t = {T}; return {{ off: document.getElementById('be-start').disabled, wait: t(document.getElementById('be-wait')), state: t(document.getElementById('be-state')), share: t(document.getElementById('ev-share')), port: location.port, host: EV.st.share.host, who: !!document.getElementById('run-who') }}; }}")
    say(not r['off'] and r['wait'] is None and '0 sessions are running now' in r['state'] and not r['who'], f"nothing is running: the Start button is on, and the set-up page says “0 sessions are running now”")
    say(r['share'] and f"ssh -N -L 4{r['port']}:127.0.0.1:{r['port']} THEIR-ACCOUNT@{r['host']}" in r['share'] and f"http://127.0.0.1:4{r['port']}/viewer/" in r['share'] and 'one session runs at a time' in r['share'], f"the foot gives the one command for somebody else, with this server's name and port: “{r['share']}”")
    done(pg)
    # a session runs, started by somebody else; the one who looks is a third account
    state.update(run=True, by='dana.levi', you='noa.bar', owner='the.owner')
    pg = new(BASE, '#home-rows tr'); h = pg.evaluate(f"() => {{ const t = {T}, row = document.querySelector('#home-rows tr.run'), c = row && row.querySelector('[data-col=how]'); return {{ head: t(document.getElementById('run-who')), cell: t(c), title: c && c.title, h: row && Math.round(row.getBoundingClientRect().height), h0: Math.round(document.querySelector('#home-rows tr:not(.run)').getBoundingClientRect().height), wide: document.documentElement.scrollWidth - innerWidth, id: row && row.dataset.id }}; }}")
    say(h['id'] == sid and h['head'] == f'{sid} running now, started by dana.levi' and h['cell'] == 'running now · dana.levi' and 'started by dana.levi' in h['title'] and h['h'] == h['h0'] and h['wide'] <= 0, f"Home, with {sid} running: the title line says “{h['head']}”, its row says “{h['cell']}” (in full in its box), the row is as high as the others and the page does not scroll sideways")
    done(pg)
    pg = new(f'{BASE}?tab=new', '#new-setup #be-start'); pg.wait_for_function("() => document.querySelector('#be-pic svg.sy')", timeout=60000); pg.wait_for_timeout(600)
    r = pg.evaluate(f"() => {{ const t = {T}, b = document.getElementById('be-start'); return {{ off: b.disabled, title: b.title, wait: t(document.getElementById('be-wait')), head: t(document.querySelector('#new-setup h2 #run-who')) }}; }}")
    say(r['off'] and r['wait'] and sid in r['wait'] and 'dana.levi' in r['wait'] and 'One session runs at a time' in r['wait'] and r['title'] == r['wait'] and r['head'], f"the set-up page: the Start button is off, and says why on the button and under it (“{r['wait']}”)")
    state['run'] = False; pg.evaluate("() => EV.load()"); pg.wait_for_timeout(1500); r2 = pg.evaluate("() => ({ off: document.getElementById('be-start').disabled, wait: !!document.getElementById('be-wait') })")
    say(not r2['off'] and not r2['wait'], "when that session has ended, the button is on again without loading the page anew")
    state['run'] = True; done(pg)
    # the banner: who started it and who can stop it; and its line of text never wraps, so that a note of what just arrived, however long, leaves the banner as high as it was
    # (a banner that grew by a line moved the page by 20 px: found by the live view's own check on 2026-11-17)
    BAN = f"""() => {{ const t = {T}, bar = () => document.getElementById('live-bar'), by = document.getElementById('live-by'), btn = bar().querySelector('button[data-act=stop]'), h0 = Math.round(bar().getBoundingClientRect().height);
      const line = bar().querySelector('.lv-say'), sp = document.createElement('span'); sp.className = 'sm'; sp.id = 'live-arrived'; sp.textContent = ' · just arrived: ' + 'the reply of turn 3 with 2 verdicts, 4 hypotheses, experiment X2 and its 12 simulations; '.repeat(4);
      line.appendChild(sp); const h1 = Math.round(bar().getBoundingClientRect().height), note = !!document.getElementById('live-arrived'); sp.remove();
      return {{ by: t(by), tip: by ? by.title : null, stop: !!btn, stopTip: btn ? btn.title : null, end: t(bar().querySelector('.end')), h0, h1, note }}; }}"""
    still = lambda r: r['note'] and r['h0'] == r['h1'] <= 56
    pg = new(f'{BASE}?session={sid}', '#live-bar'); r = pg.evaluate(BAN)
    say(r['by'] == 'started by dana.levi' and not r['stop'] and 'Only dana.levi or the.owner can stop it' in r['tip'] and still(r), f"the running session's banner, seen by a third account: “{r['end']}” and no Stop button (its box: “{r['tip']}”); with a note of what just arrived the banner is as high as without ({r['h0']} px)")
    done(pg)
    state['you'] = 'dana.levi'; pg = new(f'{BASE}?session={sid}', '#live-bar'); r = pg.evaluate(BAN)
    say(r['by'] is None and r['stop'] and r['stopTip'] == 'You started this session' and r['end'] == 'Stop' and still(r), f"seen by the one who started it: the Stop button alone (its box: “{r['stopTip']}”), as before the page was shared; the banner keeps its height ({r['h0']} px)")
    done(pg)
    state['you'] = 'the.owner'; pg = new(f'{BASE}?session={sid}', '#live-bar'); r = pg.evaluate(BAN)
    say(r['by'] == 'started by dana.levi' and r['stop'] and 'As the owner of the page you can stop it' in r['tip'] and still(r), f"seen by the owner of the page: “{r['end']}”, with the Stop button; the banner keeps its height ({r['h0']} px)")
    done(pg)
    pg = new(f'{BASE}?session={sid}', '#live-bar', ); pg.set_viewport_size({'width': 1500, 'height': 1000}); pg.wait_for_timeout(500); r = pg.evaluate(BAN)
    say(still(r), f"and at 1,500 px, the width the live view's own check uses: {r['h0']} px with and without the note")
    done(pg)
    state.update(you='noa.bar', stoppable=False, by='the.owner'); pg = new(f'{BASE}?session={sid}', '#live-bar'); r = pg.evaluate(BAN)
    say(r['end'] == 'started from a terminal by the.owner · this page cannot stop it' and not r['stop'] and 'not with this page' in r['tip'] and 'stopped in that terminal' in r['tip'] and still(r), f"a session started from a terminal: “{r['end']}” (its box: “{r['tip']}”); the banner keeps its height")
    state['you'] = 'the.owner'; r = (lambda pg2: (pg2.evaluate(BAN), done(pg2))[0])(new(f'{BASE}?session={sid}', '#live-bar'))
    say(r['end'] == 'started from a terminal by the.owner (you) · this page cannot stop it' and not r['stop'], f"seen by the one who started it from the terminal: “{r['end']}”")
    done(pg)
    # a server that does not say who (an older one): the page is as it was
    state.clear(); state.update(old=True); pg = new(f'{BASE}?tab=new', '#new-setup #be-start'); pg.wait_for_function("() => document.querySelector('#be-pic svg.sy')", timeout=60000); pg.wait_for_timeout(600)
    r = pg.evaluate("() => ({ off: document.getElementById('be-start').disabled, share: !!document.getElementById('ev-share'), state: document.getElementById('be-state').textContent })")
    say(not r['off'] and not r['share'] and 'running now' in r['state'], "with a server that says nothing of accounts the set-up page is as before: the button on, no line at the foot")
    done(pg)

def part_task(b):
    print('TASK'); sys.path.insert(0, str(ROOT / 'harness')); import importlib; tools = importlib.import_module('tools')
    T = "id => { const el = document.getElementById(id); return el ? el.textContent.replace(/\\s+/g, ' ').trim() : null; }"
    READ = f"() => {{ const t = {T}, B = BRIEF_EDITOR; return {{ base: B.s.baseId, same: B.same(), task: t('be-task'), own: t('be-task-own'), old: t('be-task-old'), warn: !!document.querySelector('#be-task-own .warnc'), brief: B.toBrief(), given: B.given().task, field: !!document.querySelector('[data-f=task]'), start: t('be-start'), off: document.getElementById('be-start').disabled }}; }}"
    pg = new_page(b, f'{BASE}?tab=new', '#new-setup #be-start', 1440); pg.wait_for_function("() => document.querySelector('#be-pic svg.sy')", timeout=60000); pg.wait_for_timeout(600)
    def open_brief(bid): pg.select_option('#be-open', bid); pg.wait_for_function(f"() => BRIEF_EDITOR.s.baseId === '{bid}'", timeout=30000); pg.wait_for_timeout(700); return pg.evaluate(READ)
    olds = [x for x in ('trap', 'two-hosts-open', 'two-hosts-udp-demand') if (ROOT / 'briefs' / f'{x}.json').is_file()]; news = [x for x in ('trap-2', 'two-hosts-open-2', 'two-hosts-udp-demand-2') if (ROOT / 'briefs' / f'{x}.json').is_file()]
    bad = []
    for bid in olds + news:
        r = open_brief(bid); disk = json.loads((ROOT / 'briefs' / f'{bid}.json').read_text()); want = tools.task_text(disk); own = (disk.get('task') or '').strip()
        if r['task'] != want or r['field'] or 'task' in r['brief'] or not r['same'] or r['off']: bad.append((bid, 'sentence', r['task'], want))
        if own and not (r['old'] == own and r['warn'] and r['given'] == own and bid in r['own']): bad.append((bid, 'own task not said', r['own']))
        if not own and (r['own'] or r['given'] != want or tools.check_brief(dict(disk), bid)['task'] != want): bad.append((bid, 'a note where the brief has no task of its own', r['own']))
    say(not bad and len(olds) == 3 and len(news) == 3, f"the set-up page has no task field; for {len(olds) + len(news)} saved briefs it shows the sentence harness/tools.py writes, word for word; the {len(olds)} briefs that state a task of their own ({', '.join(olds)}) say so with a warning and their text, the {len(news)} without ({', '.join(news)}) are read with the sentence: {bad[:2] or 'all agree'}")
    r0 = open_brief('trap')
    r1 = pg.evaluate(f"() => {{ const B = BRIEF_EDITOR; B.s.set.duration.fixed = true; B.s.set.duration.value = '10'; B.draw(); return ({READ})(); }}")
    say(not r1['same'] and r1['own'] == '' and r1['given'] == r1['task'] == tools.task_text(r1['brief']) and 'duration' not in r1['task'] and 'You may change 4 settings' in r1['task'] and 'duration' in r0['task'],
        f"trap with the measured time made fixed: the form is no longer the saved brief, its own text is gone, and the sentence follows (“{r1['task']}”)")
    r2 = pg.evaluate(f"() => {{ const B = BRIEF_EDITOR; B.s.goal = 'open'; B.draw(); return ({READ})(); }}")
    say(r2['task'] == tools.task_text(r2['brief']) and r2['task'].startswith('No aim is given.'), f"with the aim left open the sentence says so (“{r2['task'][:70]}…”)")
    r3 = pg.evaluate(f"() => {{ const B = BRIEF_EDITOR; B.s.goal = 'given'; B.s.measure = 'udp_loss_frac'; B.s.direction = 'min'; B.s.conditions = 'tcp_goodput_bps >= 100000000\\nlink_util >= 0.9'; B.draw(); return ({READ})(); }}")
    say(r3['task'] == tools.task_text(r3['brief']) and 'the smallest udp_loss_frac, while tcp_goodput_bps >= 100000000 and link_util >= 0.9' in r3['task'], f"another target and two conditions: “{r3['task'][:110]}…”")
    done(pg)
    sid = SIDS[0]; pg = session(b, sid)
    c = pg.evaluate(f"() => {{ const t = {T}; EV.s.sel = {{ t: 'brief', id: 'brief' }}; EV.draw(); const a = [t('bc-task-by'), document.getElementById('bc-task').dataset.own, t('bc-task')]; const keep = EV.M.brief.task; EV.M.brief.task = EV.taskText(EV.M.brief); EV.draw(); const h = [t('bc-task-by'), document.getElementById('bc-task').dataset.own, t('bc-task')]; EV.M.brief.task = keep; EV.draw(); return {{ a, h }}; }}")
    given = json.loads((ROOT / 'sessions' / sid / 'session.json').read_text())['given']
    say(c['a'][0] == 'written by hand in the brief' and c['a'][1] == 'operator' and c['a'][2] == re.sub(r'\s+', ' ', given['task']).strip() and c['h'][0].startswith('written by the harness') and c['h'][1] == 'harness' and c['h'][2] == tools.task_text(given),
        f"{sid}'s brief in the pane says its task was “{c['a'][0]}”; a brief whose task is the harness's sentence says “{c['h'][0]}”")
    done(pg)

def part_network(b):
    print('NETWORK'); sid = SIDS[0]; state = {}
    def new(url, wait, mobile=False):
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True) if mobile else b.new_context(viewport={'width': 1440, 'height': 1000})
        pg = ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
        def change(route):
            resp = route.fetch(); d = resp.json()
            if isinstance(d, dict):
                d['share'] = {'host': 'the.server', 'port': 8600, 'network': state.get('network', True)}
                if state.get('far'): d.update(view_only=True, you=None)
                else: d['view_only'] = False
            route.fulfill(response=resp, body=json.dumps(d), headers={**resp.headers, 'content-type': 'application/json'})
        pg.route('**/api/status*', change); pg.goto(url); pg.wait_for_selector(wait, timeout=60000); pg.wait_for_timeout(900); return pg
    T = "id => { const el = document.getElementById(id); return el ? el.textContent.replace(/\\s+/g, ' ').trim() : null; }"
    READ = f"() => {{ const t = {T}, b = document.getElementById('be-start'); return {{ pill: t('ev-viewonly'), only: t('ev-viewonly-foot'), look: t('ev-look'), share: t('ev-share'), off: b ? b.disabled : null, why: b ? b.title : null, wait: t('be-wait') }}; }}"
    state.update(far=True); pg = new(f'{BASE}?tab=new', '#new-setup #be-start'); pg.wait_for_function("() => document.querySelector('#be-pic svg.sy')", timeout=60000); pg.wait_for_timeout(600); r = pg.evaluate(READ)
    say(r['pill'] == 'view only' and r['off'] and 'can only be read' in r['why'] and r['wait'] == r['why'] and r['only'].startswith('You are looking only.') and r['look'] is None and 'To start sessions and change things you need an account on the.server' in r['share'],
        f"a visitor from the network: the bar says “{r['pill']}”, the Start button is off and says why (“{r['why'][:70]}…”), the foot says “{r['only']}” and how to use the page fully")
    done(pg)
    state.update(far=False); pg = new(f'{BASE}?tab=new', '#new-setup #be-start'); pg.wait_for_function("() => document.querySelector('#be-pic svg.sy')", timeout=60000); pg.wait_for_timeout(600); r = pg.evaluate(READ)
    say(r['pill'] is None and not r['off'] and r['only'] is None and r['look'] and 'http://the.server:8600/viewer/' in r['look'] and 'For somebody else, to use the page as you do' in r['share'],
        f"a user of this machine: no such mark, the Start button on, and the foot gives the address to look from the network (“{r['look']}”)")
    done(pg); state.update(network=False); pg = new(BASE, '#home-rows tr'); r = pg.evaluate(READ)
    say(r['look'] is None and r['share'], "a server that does not answer on the network: the foot gives the tunnel alone")
    done(pg)
    state.update(far=True, network=True); wide = {}
    for name, url, wait in (('Home', BASE, '#home-rows tr'), (sid, f'{BASE}?session={sid}', '#s-notebook .nb-group')):
        pg = new(url, wait, mobile=True); wide[name] = pg.evaluate("() => [document.documentElement.scrollWidth, innerWidth, [...document.querySelectorAll('#ev .ev-card')].filter(c => c.scrollWidth > c.clientWidth + 2).length]"); done(pg)
    say(all(w[0] <= w[1] for w in wide.values()) and wide[sid][2] > 0, f"on a phone (390 px) the page does not scroll sideways (Home and {sid}: {wide}); what is wider than the screen scrolls inside its own card ({wide[sid][2]} such cards on {sid})")

def part_limit(b):
    print('LIMIT'); norm = lambda x: re.sub(r'\s+', ' ', str(x or '')).strip()
    READ = """() => { const t = el => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null), P = document.getElementById('s-proposes'), L = P.querySelector('[data-pr=limit]');
      EV.s.sel = { t: 'report', id: 'report' }; EV.draw(); const P2 = document.getElementById('s-proposes'), L2 = P2.querySelector('[data-pr=limit]'), R = document.querySelector('#rp [data-rp=limit]');
      return { blocks: [...P2.querySelectorAll('[data-pr]')].map(x => [x.dataset.pr, Number(t(x.querySelector('.st-n')))]), limit: t(document.getElementById('pr-limit')), own: L2 ? [...L2.querySelectorAll('[data-own=model]')].map(t) : [],
        nd: L2 ? [...L2.querySelectorAll('#pr-nodiff [data-knob]')].map(x => x.dataset.knob) : null, ndText: t(document.getElementById('pr-nodiff')), names: L2 ? [...L2.querySelectorAll('#pr-nodiff [data-knob]')].map(x => EV.LABEL[x.dataset.knob] || x.dataset.knob) : [],
        pane: [...document.querySelectorAll('#rp [data-rp]')].map(x => x.dataset.rp), paneText: R ? t(R) : null, paneNd: t(document.getElementById('rp-nodiff')), wide: document.documentElement.scrollWidth - innerWidth }; }"""
    sid = 'lim1'
    if not (ROOT / 'sessions' / sid).is_dir(): say(False, f"{sid} is not in the scratch copy (EV_EXTRA must hold the scripted session of harness_checks/test_tolerance.py)"); return
    rep = next(r['body'] for r in ledger(sid) if r['type'] == 'report'); pg = session(b, sid); r = pg.evaluate(READ)
    keys = [q[0] for q in r['blocks']]; want = [k for k in ['aim', 'adjust', 'expected', 'limit', 'diagnosis', 'because', 'but', 'explanation'] if k in keys]
    say(keys == want and 'limit' in keys and keys.index('limit') == 3 and [q[1] for q in r['blocks']] == list(range(1, len(keys) + 1)), f"{sid}: “What limits the result” is the fourth part of “What it proposes”, after the expected result, and the parts are numbered in order: {r['blocks']}")
    say(r['limit'] == norm(rep['limit']) and r['own'] == [norm(rep['limit'])] and r['nd'] == rep['no_difference'] and all(n in r['ndText'] for n in r['names']) and r['wide'] <= 0,
        f"{sid}: the part holds the report's own text, marked as the AI's (“{r['limit'][:60]}”), and names the settings of its list and no other ({rep['no_difference']}: “{r['ndText']}”)")
    say('limit' in r['pane'] and r['pane'].index('limit') == r['pane'].index('expected') + 1 and norm(rep['limit']) in r['paneText'] and all(n in r['paneNd'] for n in r['names']), f"{sid}: the full report in the pane has the same part after the expected result: {r['pane']}")
    e = pg.evaluate("""() => { const t = el => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null), R = EV.repNow(), keep = R.no_difference; R.no_difference = []; EV.draw(); const a = t(document.getElementById('pr-nodiff')), n = document.querySelectorAll('#pr-nodiff [data-knob]').length;
      delete R.no_difference; EV.draw(); const b2 = document.getElementById('pr-nodiff'), still = !!document.getElementById('pr-limit'); R.no_difference = keep; EV.draw(); return { a, n, gone: !b2, still, back: document.querySelectorAll('#pr-nodiff [data-knob]').length }; }""")
    say(e['n'] == 0 and 'empty' in (e['a'] or '') and e['gone'] and e['still'] and e['back'] == len(rep['no_difference']), f"{sid}: with an empty list the part says so (“{e['a']}”) and names nothing; without a list the line is not there and the text stays")
    k = pg.evaluate("() => { const n = EV.M.steps.length, out = []; for (const k of [0, n - 2, n - 1]) { EV.s.step = k; EV.draw(); out.push([k, !!document.querySelector('#s-proposes [data-pr=limit]'), !!EV.repNow()]); } EV.s.step = null; EV.draw(); return out; }")
    say(all(has == rep_there for _, has, rep_there in k) and not k[0][1] and k[-1][1], f"{sid}: in the replay the part is there only from the step that records the report: {k}")
    s = pg.evaluate("""() => { const rn = EV.repNow, ln = EV.liveNow; let n = null, err = null; try { EV.repNow = () => null; EV.liveNow = () => ({ phase: 'reply', mode: null }); n = [...new DOMParser().parseFromString(EV.proposesCard(), 'text/html').querySelectorAll('#pr-slots .pr-slot h3')].map(h => h.textContent.replace(/^\\d+/, '').trim()); } catch (x) { err = String(x); } EV.repNow = rn; EV.liveNow = ln; return { n, err }; }""")
    say(not s['err'] and s['n'] and len(s['n']) == 7 and s['n'][3] == 'What limits the result', f"{sid} (its instructions ask the report for what limits the result): while no report is recorded, a running session would show seven empty places, the fourth “What limits the result”: {s}")
    done(pg)
    for old in SIDS[:1]:
        pg = session(b, old); r = pg.evaluate(READ); keys = [q[0] for q in r['blocks']]
        s = pg.evaluate("""() => { const rn = EV.repNow, ln = EV.liveNow; let n = null, err = null; try { EV.repNow = () => null; EV.liveNow = () => ({ phase: 'reply', mode: null }); n = new DOMParser().parseFromString(EV.proposesCard(), 'text/html').querySelectorAll('#pr-slots .pr-slot').length; } catch (x) { err = String(x); } EV.repNow = rn; EV.liveNow = ln; return { n, err }; }""")
        say('limit' not in keys and r['nd'] is None and r['ndText'] is None and 'limit' not in r['pane'] and [q[1] for q in r['blocks']] == list(range(1, len(keys) + 1)) and s['n'] == 6 and not s['err'], f"{old}, recorded before reports had the part: no such part on the card ({keys}) or in the pane, the numbering has no gap, and a running session of that kind would show six empty places ({s})")
        done(pg)

with sync_playwright() as p:
    b = p.chromium.launch()
    for part in PARTS: globals()['part_' + part](b)
    b.close()
print('RESULT:', f'FAIL {len(FAILED)}' if FAILED else 'PASS'); [print('  FAILED', f) for f in FAILED]
