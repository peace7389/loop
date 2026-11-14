// BRIEF_EDITOR: the set-up page, "New session". It has the seven blocks of a session's "The setting"
// (evidence_setting.js), in the same order, built from the same pieces; here each block is a form:
//   1 The network          the picture of the system; a click on a part opens its settings to set
//   2 Who decides what     each setting: fixed by the operator (a value), or the AI may change it (a range, a step)
//   3 The aim              a ready-made aim, or a target with conditions and a tolerance, or "open: the AI chooses"
//   4 What the AI is told, is not told, and can do    the task and the description to write; the three lists, which
//                          follow the form as it changes; the exact text the AI will be given
//   5 The limits           simulations in all and in one experiment
//   6 Kept from the AI     the scheduling policy: share, cap, or random
//   7 How the AI runs      the flags, each beside its default
// Above "Start" stands the header strip the session's page will have. Every block says in one sentence what it is for,
// every default is shown, and a value that is not allowed is refused as it is typed, with the reason in words
// (BRIEF_EDITOR.problems: the rules of harness/tools.py check_brief and of control.py's start, said here first; the
// server checks again when a brief is saved or a session started).
// A brief is opened from the saved ones, or the form is filled from a session ("Start a new session from this setup":
// every value of that session, each changed value marked). A brief is saved under a NEW id through POST /api/brief and
// is never overwritten. The older form, one roomy row per setting, stays reachable as "all settings as a list".
// The form lives in one node that is kept when the page around it is redrawn, so nothing typed is lost.
//   BRIEF_EDITOR.mount(host, ctx)   ctx = { st: control.py's status, post(path, body), e: escape, from: a session id or null,
//                                           flags(): the choices of blocks 6 and 7, after(): reload the page's data, go(o): to another view }
// The editor of the older control page (index_full.html) is brief_editor_old.js.
// ======================================================================================================
const BRIEF_EDITOR = {
  // every setting of the program, in the order shown; every one can be fixed or opened to the AI (the answer format is built from the brief).
  // step: a numeric knob may have one; open: the range and meaning offered when a setting no brief has opened yet is switched to a knob
  // as: a setting a brief may leave out ("not set"); it then has the value of the setting named here, and the program is started without it
  SETTINGS: [
    { k: 'linkRate', kind: 'rate', hint: 'e.g. 1Gbps', open: { min: '100Mbps', max: '10Gbps', meaning: "rate of the link, e.g. '500Mbps'" } },
    { k: 'linkDelay', kind: 'time', hint: 'e.g. 50us', open: { min: '10us', max: '10ms', meaning: "one-way delay of the link, e.g. '200us'" } },
    { k: 'mtu', kind: 'num', whole: true, least: 576, hint: 'bytes', step: true, open: { min: '1428', max: '1500', meaning: 'largest packet the link carries, in bytes' } },
    { k: 'udpRate', kind: 'rate', zero: true, hint: 'e.g. 300Mbps' }, { k: 'weightUdp', kind: 'num', lo: 0.05, hi: 0.95, hint: '0.05 to 0.95', step: true },
    { k: 'queuePkts', kind: 'num', whole: true, least: 1, hint: 'packets', step: true },
    { k: 'queuePktsUdp', kind: 'num', whole: true, least: 1, hint: 'packets', step: true, as: 'queuePkts', open: { min: '4', max: '1000', meaning: 'most packets the UDP queue holds' } },
    { k: 'queuePktsTcp', kind: 'num', whole: true, least: 1, hint: 'packets', step: true, as: 'queuePkts', open: { min: '4', max: '1000', meaning: 'most packets the TCP queue holds' } },
    { k: 'tcpVariant', kind: 'choice', hint: 'e.g. TcpCubic' }, { k: 'duration', kind: 'num', above: 0, hint: 'seconds', step: true },
    { k: 'seed', kind: 'num', whole: true, least: 1, hint: 'whole number', step: true }],
  // ready-made aims: [key, the aim in words, measure, direction, conditions]
  AIMS: [['tcp-loss-1', 'the largest TCP goodput, while UDP loss stays at or under 1 %', 'tcp_goodput_bps', 'max', ['udp_loss_frac <= 0.01']],
         ['tcp-no-loss', 'the largest TCP goodput with no UDP loss at all', 'tcp_goodput_bps', 'max', ['udp_loss_frac <= 0']]],
  // ready-made variations of the opened brief: [key, name, the id's ending, what it changes, when it cannot be used]
  VARIATIONS: [
    ['noloss', 'no loss allowed', 'no-loss', 'the condition on UDP loss becomes udp_loss_frac <= 0', s => (s.goal !== 'given' ? "this brief's aim is open: it has no condition to tighten" : '')],
    ['coarse', 'coarse ratio (steps of 0.01)', 'coarse-ratio', 'the ratio gets a step of 0.01', s => (s.set.weightUdp.fixed ? 'this brief fixes the ratio' : '')],
    ['small', 'small budget (15 simulations)', 'budget-15', 'the session may run 15 simulations', () => '']],
  OUTPUTS: ['tcp_goodput_bps', 'udp_goodput_bps', 'udp_loss_frac', 'drops_band0', 'drops_band1', 'tcp_retrans', 'link_util'],
  CSS: `
.be label { display: block; font-size: var(--f-text); font-weight: 600; } .be small { display: block; font-size: var(--f-sec); font-weight: 400; color: var(--text-muted); margin: 1px 0 4px; }
.be input[type=text], .be input[type=number], .be select, .be textarea { width: 100%; padding: 4px 8px; font-weight: 400; } .be textarea { resize: vertical; line-height: 1.45; }
.be-top { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.4fr); gap: 8px 22px; align-items: start; margin-bottom: 12px; }
.be-row { display: grid; grid-template-columns: 150px 250px minmax(0, 1fr); gap: 8px 14px; align-items: start; padding: 8px 0; border-top: 1px solid var(--grid); }
.be-row code { display: block; font-size: var(--f-sec); color: var(--text-muted); }
.be-sw { display: inline-flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; } .ev .be-sw button { font-size: var(--f-sec); padding: 3px 9px; border: 0; border-radius: 0; background: var(--surface-1); color: var(--text-secondary); }
.ev .be-sw button + button { border-left: 1px solid var(--border); } .ev .be-sw button.on { background: var(--text-primary); color: var(--surface-1); font-weight: 600; }
.be-f { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px 8px; } .be-f .wide { grid-column: 1 / -1; } .be-f small { margin: 0 0 2px; }
.be table.be-who td { padding: 2px 8px 2px 0; border-bottom: 0; vertical-align: middle; } .be table.be-who input { width: 5.6em; padding: 2px 6px; } .be table.be-who input.w { width: 9.5em; } .be table.be-who .lab { font-size: var(--f-sec); color: var(--text-muted); margin: 0 3px 0 6px; }
.be .be-why { display: block; color: var(--critical); font-size: var(--f-sec); font-weight: 600; margin: 1px 0 0; } .be .be-why:empty { display: none; } .be input.bad, .be textarea.bad, .be select.bad { border-color: var(--critical); }
.be input.chg, .be textarea.chg, .be select.chg { box-shadow: inset 3px 0 0 var(--series-1); } .be .chg-note { color: var(--series-1); font-weight: 600; }
.be-aim label { font-weight: 400; margin: 3px 0; } .be-two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 12px; margin-top: 6px; }
.be-var { display: flex; flex-wrap: wrap; gap: 6px; } .ev .be-var button { font-size: var(--f-sec); text-align: left; padding: 3px 9px; } .be-pic svg g[data-act] { cursor: pointer; }
.be-start { border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; margin-top: 14px; } .be-start .ev-head { position: static; box-shadow: none; margin: 6px 0 10px; }
.be-msg { margin: 8px 0 0; font-size: var(--f-text); padding: 6px 10px; border-left: 3px solid var(--border); } .be-msg ul { margin: 4px 0 0; padding-left: 18px; }
.be-msg.bad { border-color: var(--critical); background: color-mix(in srgb, var(--critical) 8%, transparent); } .be-msg.ok { border-color: var(--good); background: color-mix(in srgb, var(--good) 8%, transparent); }
.be .kv input, .be .kv select { width: 100%; } .be .kv input[type=checkbox] { width: auto; }
@media (max-width: 1000px) { .be-top, .be-row { grid-template-columns: minmax(0, 1fr); } }`,
  node: null, s: null, ctx: null, template: {}, list: '', typing: null, man: null,

  async fetchJson(url) { try { const r = await fetch(`${url}?t=${Date.now()}`, { cache: 'no-store' }); return r.ok ? await r.json() : null; } catch (x) { return null; } },
  fetchBrief(id) { return BRIEF_EDITOR.fetchJson(`../briefs/${id}.json`); },

  // ---- a brief file <-> the form's state (every field of the form is a text, as typed)
  fromBrief(b) {
    const B = BRIEF_EDITOR, set = {};
    B.SETTINGS.forEach(({ k, as }) => {
      const kn = (b.knobs || {})[k], t = B.template[k] || {}, str = v => (v == null ? '' : String(v));
      set[k] = { off: !!as && !kn && (b.system || {})[k] == null, fixed: !kn, value: str((b.system || {})[k] != null ? b.system[k] : (kn || t).default), min: str((kn || t).min), max: str((kn || t).max),
                 choices: ((kn || t).choices || []).join(', '), def: str((kn || t).default), meaning: str((kn || t).meaning), step: str((kn || {}).step) };
    });
    const g = b.goal || {}, t = g.target || {};
    return { id: '', task: b.task || '', description: b.description || '', set, order: [Object.keys(b.system || {}), Object.keys(b.knobs || {})], goal: g.kind === 'given' ? 'given' : 'open', measure: t.measure || 'tcp_goodput_bps', direction: t.direction || 'max', tolerance: g.tolerance == null ? '' : String(g.tolerance),
             conditions: (g.conditions || []).join('\n'), sims: String((b.limits || {}).simulations || ''), per: String((b.limits || {}).simulations_per_experiment || '') };
  },
  val(kind, v) { const t = String(v).trim(); return kind === 'num' && t !== '' && isFinite(Number(t)) ? Number(t) : t; },
  toBrief() {
    const B = BRIEF_EDITOR, s = B.s, system = {}, knobs = {}, val = B.val;
    B.SETTINGS.forEach(({ k, kind, step }) => {
      const f = s.set[k];
      if (f.off) return;
      if (f.fixed) system[k] = val(kind, f.value);
      else knobs[k] = kind === 'choice' ? { choices: f.choices.split(',').map(c => c.trim()).filter(Boolean), default: f.def.trim(), meaning: f.meaning.trim() }
        : { min: val(kind, f.min), max: val(kind, f.max), default: val(kind, f.def), ...(step && String(f.step || '').trim() ? { step: val('num', f.step) } : {}), meaning: f.meaning.trim() };
    });
    system.udpPacketBytes = 1400;  // set by the scenario; a brief can only state it
    // each part in the order of the brief (or the session) the form was filled from, then what was added, in the order of the form: the answer format follows the order of the knobs
    const inOrder = (o, first) => Object.fromEntries([...(first || []).filter(k => k in o), ...Object.keys(o).filter(k => !(first || []).includes(k))].map(k => [k, o[k]])), [so, ko] = s.order || [];
    const goal = s.goal === 'open' ? { kind: 'open' } : { kind: 'given', target: { measure: s.measure, direction: s.direction }, conditions: s.conditions.split('\n').map(c => c.trim()).filter(Boolean), ...(String(s.tolerance || '').trim() ? { tolerance: val('num', s.tolerance) } : {}) };
    return { id: s.id.trim(), task: s.task.trim(), description: s.description.trim(), system: inOrder(system, so), knobs: inOrder(knobs, ko), goal, limits: { simulations: val('num', s.sims), simulations_per_experiment: val('num', s.per) } };
  },
  body() { const b = BRIEF_EDITOR.toBrief(); delete b.id; return JSON.stringify(b); },   // what the form says, without the id
  same() { const B = BRIEF_EDITOR; return !!B.s.baseId && B.body() === B.s.base; },      // the form and the saved brief are the same
  // the brief as the AI will be given it: the description's {names} filled from the fixed settings, then the manifest's measures and tools
  given() { const B = BRIEF_EDITOR, t = B.toBrief(), sys = t.system, b = { id: t.id || B.s.baseId || '', task: t.task, description: t.description, system: t.system, knobs: t.knobs, goal: t.goal, limits: t.limits }; b.description = b.description.replace(/\{(\w+)\}/g, (m, k) => (k in sys ? String(sys[k]) : m)); return { ...b, ...(B.man || {}) }; },

  // every field of the form by its name, as typed: what "changed" is measured against
  fields() { const B = BRIEF_EDITOR, s = B.s, o = { task: s.task, description: s.description, goal: s.goal, measure: s.measure, direction: s.direction, conditions: s.conditions, tolerance: s.tolerance, sims: s.sims, per: s.per };
    B.SETTINGS.forEach(({ k }) => { const f = s.set[k]; o[`sw.${k}`] = f.off ? 'off' : f.fixed ? 'fixed' : 'knob'; ['value', 'min', 'max', 'def', 'step', 'choices', 'meaning'].forEach(x => { o[`set.${k}.${x}`] = f[x] || ''; }); });
    return o; },
  // which of a setting's fields count in its present state (a hidden field cannot be "changed")
  live(k, x) { const f = BRIEF_EDITOR.s.set[k], q = BRIEF_EDITOR.SETTINGS.find(z => z.k === k); return f.off ? false : f.fixed ? x === 'value' : x === 'choices' ? q.kind === 'choice' : x === 'min' || x === 'max' ? q.kind !== 'choice' : x === 'step' ? !!q.step && q.kind !== 'choice' : x !== 'value'; },

  async open(id) {
    const B = BRIEF_EDITOR, b = await B.fetchBrief(id);
    if (!b) { B.s.msg = { bad: true, lines: [`Cannot read briefs/${id}.json.`] }; return B.draw(); }
    const keep = B.s ? B.s.id : '', view = B.s ? [B.s.list, B.s.obj] : [];
    B.s = { ...B.fromBrief(b), id: keep, baseId: id, from: null, msg: null, busy: '', list: view[0], obj: view[1] };
    B.s.base = B.body(); B.s.orig = B.fields(); B.s.origRun = { policy: 'share', budget: '', draft: 'on', tokens: '', temp: '', baseline: true };  // blocks 6 and 7 are measured against the defaults
    B.draw();
  },
  // "Start a new session from this setup": every value of a session (what it was given, its flags, its policy)
  async openFrom(sid) {
    const B = BRIEF_EDITOR, m = await B.fetchJson(`../sessions/${sid}/session.json`), row = ((B.ctx.st || {}).sessions || []).find(x => x.id === sid) || {};
    if (!m || !m.given) { B.s = { ...(B.s || {}), msg: { bad: true, lines: [`Session ${sid} records no brief: it cannot fill the set-up.`] } }; return B.draw(); }
    const g = m.given, briefs = (B.ctx.st || {}).briefs || []; let id = `${g.id}-again`.slice(0, 56), n = 1; while (briefs.includes(id)) id = `${g.id}-again`.slice(0, 54) + '-' + (++n);
    B.s = { ...B.fromBrief(g), id, baseId: '', from: sid, fromBrief: g.id, msg: null, busy: '', list: false, obj: null };
    B.s.base = ''; B.s.orig = B.fields();
    const f = m.flags || {}, nw = EV.nw; nw.policy = row.policy_hidden ? 'random' : row.policy || nw.policy; nw.budget = f.budget == null ? '' : String(f.budget); nw.draft = f.draft || 'on'; nw.tokens = f.max_tokens == null ? '' : String(f.max_tokens); nw.temp = f.temperature == null ? '' : String(f.temperature); nw.baseline = f.baseline !== false && f.baseline !== 'off';
    B.s.origRun = { policy: nw.policy, budget: nw.budget, draft: nw.draft, tokens: nw.tokens, temp: nw.temp, baseline: nw.baseline };
    B.draw();
  },

  async mount(host, ctx) {
    const B = BRIEF_EDITOR; B.ctx = ctx;
    if (!document.getElementById('be-css')) { const st = document.createElement('style'); st.id = 'be-css'; st.textContent = B.CSS; document.head.appendChild(st); }
    if (!B.node) {
      B.node = document.createElement('div'); B.node.className = 'be';
      B.node.addEventListener('input', B.onInput); B.node.addEventListener('change', B.onInput); B.node.addEventListener('click', B.onClick);
      B.node.addEventListener('focusin', ev => { B.typing = ev.target; }); B.node.addEventListener('focusout', ev => { if (ev.relatedTarget ? !B.node.contains(ev.relatedTarget) : B.node.isConnected) B.typing = null; });  // kept when the page's redraw took the node out
      host.appendChild(B.node);
      B.node.innerHTML = '<p class="sm">Loading the briefs…</p>';
      const first = ((ctx.st || {}).briefs || [])[0];
      const [t, man] = await Promise.all([B.fetchBrief('two-hosts-open'), B.fetchJson('../harness/manifest.json')]); B.template = (t && t.knobs) || {}; B.man = man;   // ranges offered when a fixed setting is switched to a knob; the measures and tools the AI is given
      B.s = { baseId: '', msg: null, busy: '', id: '' }; B.was = ctx.from || null;
      if (ctx.from) await B.openFrom(ctx.from); else if (first) await B.open(((ctx.st || {}).briefs || []).includes('two-hosts-open') ? 'two-hosts-open' : first); else B.draw();
      return;
    }
    if ((ctx.from || null) !== B.was) { B.was = ctx.from || null; host.appendChild(B.node); if (ctx.from) return B.openFrom(ctx.from); }  // the page was opened again, from another session
    const had = B.typing && B.node.contains(B.typing) ? [B.typing, B.typing.selectionStart, B.typing.selectionEnd] : null;
    host.appendChild(B.node);   // the same node, with everything typed in it
    if (had) { had[0].focus({ preventScroll: true }); try { had[0].setSelectionRange(had[1], had[2]); } catch (x) { /* a select or a button */ } }
    if (!had && B.s && B.s.set && B.picture() && !B.node.querySelector('svg.sy')) return B.draw();  // the list of ns-3 objects has arrived: the picture can be drawn
    B.paint();
  },

  // ---- what cannot be used, said as it is typed: field name -> the reason in words (the rules of tools.check_brief and of control.py's start)
  rate(v) { const m = String(v).trim().match(/^([0-9.]+)\s*([kMG]?)bps$/); return m && isFinite(Number(m[1])) ? Number(m[1]) * { '': 1, k: 1e3, M: 1e6, G: 1e9 }[m[2]] : null; },
  secs(v) { const m = String(v).trim().match(/^(\d+(?:\.\d+)?)(ns|us|ms|s)$/); return m ? Number(m[1]) * { ns: 1e-9, us: 1e-6, ms: 1e-3, s: 1 }[m[2]] : null; },
  // a value of one setting: its size as a number (for comparing), or the reason it cannot be used
  size(q, v) {
    const B = BRIEF_EDITOR, t = String(v).trim(), name = EV.LABEL[q.k] || q.k; if (t === '') return { why: 'a value is needed' };
    if (q.kind === 'rate') { const r = B.rate(t); return r == null ? { why: `a rate is a number and a unit, like 300Mbps or 1Gbps` } : r < (q.zero ? 0 : 1) ? { why: `the ${name} must be above 0` } : { n: r }; }
    if (q.kind === 'time') { const r = B.secs(t); return r == null ? { why: 'a time is a number and a unit, like 50us or 2ms' } : { n: r }; }
    if (q.kind === 'choice') return /^Tcp[A-Za-z0-9]+$/.test(t) ? { n: t } : { why: 'the name of a TCP type starts with Tcp, like TcpCubic' };
    const n = Number(t); if (!isFinite(n)) return { why: 'a number is needed' };
    if (q.whole && !Number.isInteger(n)) return { why: 'a whole number is needed' }; if (q.least != null && n < q.least) return { why: `at least ${q.least}` };
    if (q.lo != null && (n < q.lo || n > q.hi)) return { why: `from ${q.lo} to ${q.hi}` }; if (q.above != null && n <= q.above) return { why: `above ${q.above}` };
    return { n };
  },
  problems() {
    const B = BRIEF_EDITOR, s = B.s, bad = {}, briefs = (B.ctx.st || {}).briefs || [], id = s.id.trim();
    if (id && !/^[A-Za-z0-9_-]{1,60}$/.test(id)) bad.id = 'a name is letters, digits, - and _, at most 60'; else if (id && briefs.includes(id)) bad.id = `a brief named ${id} already exists, and a brief is never overwritten: choose another name`;
    if (!s.task.trim()) bad.task = 'the task cannot be empty'; if (!s.description.trim()) bad.description = 'the description cannot be empty';
    const fixed = new Set(B.SETTINGS.filter(q => s.set[q.k].fixed && !s.set[q.k].off).map(q => q.k).concat('udpPacketBytes')), odd = [...new Set([...s.description.matchAll(/\{(\w+)\}/g)].map(m => m[1]))].filter(k => !fixed.has(k));
    if (odd.length) bad.description = `{${odd[0]}} is not a fixed setting of this set-up: a name in braces is filled from a fixed setting`;
    B.SETTINGS.forEach(q => { const f = s.set[q.k], p = x => `set.${q.k}.${x}`; if (f.off) return;
      if (f.fixed) { const v = B.size(q, f.value); if (v.why) bad[p('value')] = v.why; return; }
      if (!f.meaning.trim()) bad[p('meaning')] = 'a knob needs one line that says what it is: the AI reads it';
      if (q.kind === 'choice') { const cs = f.choices.split(',').map(c => c.trim()).filter(Boolean), w = cs.map(c => B.size(q, c)).find(v => v.why);
        if (!cs.length) bad[p('choices')] = 'at least one choice is needed'; else if (w) bad[p('choices')] = w.why; if (!cs.includes(f.def.trim())) bad[p('def')] = 'the default must be one of the choices'; return; }
      const lo = B.size(q, f.min), hi = B.size(q, f.max), d = B.size(q, f.def); if (lo.why) bad[p('min')] = lo.why; if (hi.why) bad[p('max')] = hi.why; if (d.why) bad[p('def')] = d.why;
      if (!lo.why && !hi.why && lo.n >= hi.n) bad[p('max')] = '“to” must be above “from”'; else if (!lo.why && !hi.why && !d.why && (d.n < lo.n || d.n > hi.n)) bad[p('def')] = 'the default must lie in the range';
      if (q.step && String(f.step || '').trim()) { const n = Number(f.step); if (q.kind !== 'num') bad[p('step')] = 'a step is for a numeric setting'; else if (!isFinite(n) || n <= 0) bad[p('step')] = 'a step is a number above 0';
        else if (!lo.why && !hi.why && n > hi.n - lo.n) bad[p('step')] = 'the step is larger than the range'; else if (q.whole && !Number.isInteger(n)) bad[p('step')] = 'a whole number is needed'; } });
    const own = k => !s.set[k].off; if (!s.set.queuePkts.fixed && own('queuePktsUdp') && own('queuePktsTcp')) bad['sw.queuePkts'] = 'both queues have their own length, so the common queue length would change nothing: fix it, or leave one queue without its own length';
    if (s.goal === 'given') { const t = String(s.tolerance || '').trim(), n = Number(t); if (t && (!isFinite(n) || n <= 0 || n >= 100)) bad.tolerance = 'a tolerance is a number of per cent above 0 and below 100';
      const c = s.conditions.split('\n').map(x => x.trim()).filter(Boolean).find(x => !/^\w+\s*(<=|>=|<|>|==)\s*[-\d.eE]+$/.test(x) || !B.OUTPUTS.includes(x.match(/^\w+/)[0])); if (c) bad.conditions = `“${c}” cannot be read: a condition is a measure, a comparison and a number, like udp_loss_frac <= 0.01`; }
    const whole = (v, name) => (/^\d+$/.test(String(v).trim()) && Number(v) >= 1 ? '' : `${name} is a whole number of at least 1`);
    if (whole(s.sims, 'the number of simulations')) bad.sims = whole(s.sims, 'the number of simulations'); if (whole(s.per, 'the number in one experiment')) bad.per = whole(s.per, 'the number in one experiment');
    const nw = EV.nw, t = x => String(x ?? '').trim();
    if (t(nw.budget) && whole(nw.budget, 'the budget')) bad['nw.budget'] = whole(nw.budget, 'the budget'); else if (t(nw.budget) && !bad.sims && Number(nw.budget) > Number(s.sims)) bad['nw.budget'] = `the brief allows ${s.sims.trim()} simulations: the budget cannot be larger`;
    if (t(nw.tokens) && !(/^\d+$/.test(t(nw.tokens)) && Number(nw.tokens) >= 256 && Number(nw.tokens) <= 100000)) bad['nw.tokens'] = 'a whole number from 256 to 100000';
    if (t(nw.temp) && !(isFinite(Number(nw.temp)) && Number(nw.temp) >= 0 && Number(nw.temp) <= 2)) bad['nw.temp'] = 'a number from 0 to 2';
    return bad;
  },

  // the picture of the system as the form: possible once its objects are read
  picture() { if (EV.OB === undefined) EV.sysLoad(); return !!EV.OB; },
  // the picture as the form says now: each value in the colour of its state (drawn again as a value is typed: paint())
  picSvg() { const B = BRIEF_EDITOR, s = B.s, num = (kind, t) => (kind === 'num' && String(t).trim() !== '' && isFinite(Number(t)) ? Number(t) : String(t).trim());
    const key = n => EV.sysOwn(n, k => !!s.set[k] && !s.set[k].off), v = EV.sysDerive(Object.fromEntries(B.SETTINGS.filter(({ k }) => !s.set[k].off).map(({ k, kind }) => [k, num(kind, s.set[k].fixed ? s.set[k].value : s.set[k].def)]))), on = EV.sysFind(s.obj) ? s.obj : EV.sysId('sender', 'tc', 'Scheduler') || 'link';
    return EV.sysSvg({ v, knob: n => !s.set[key(n)] ? false : !s.set[key(n)].fixed, fixed: n => !!s.set[key(n)] && s.set[key(n)].fixed, on, act: 'beobj', pol: '<text x="432" y="162" text-anchor="middle" class="sv" id="sy-pol">policy not told to the AI</text>' }); },
  // the settings a part of the picture holds: those its rows of objects.json name (a queue: the common length, and its own)
  partSettings(id) { const B = BRIEF_EDITOR, f = EV.sysFind(id), keys = f ? [...new Set(f.o.rows.flatMap(([, text]) => [...String(text).matchAll(/\{(\w+)\}/g)].flatMap(m => { const k = EV.sysKey(m[1]); return EV.SYS_OWN[k] ? [EV.SYS_OWN[k], k] : [k]; })))] : []; return B.SETTINGS.filter(q => keys.includes(q.k)); },
  inp(f, v, hint, cls) { return `<input type="text" data-f="${f}" value="${BRIEF_EDITOR.ctx.e(v)}" placeholder="${BRIEF_EDITOR.ctx.e(hint || '')}" spellcheck="false"${cls ? ` class="${cls}"` : ''}>`; },
  why(f) { return `<span class="be-why" data-why="${f}"></span>`; },
  sw(q) { const f = BRIEF_EDITOR.s.set[q.k], k = q.k;
    return `<span class="be-sw">${q.as ? `<button data-sw="${k}" data-to="off" class="${f.off ? 'on' : ''}">not set</button>` : ''}<button data-sw="${k}" data-to="fixed" class="${!f.off && f.fixed ? 'on' : ''}">fixed by the operator</button><button data-sw="${k}" data-to="knob" class="${f.off || f.fixed ? '' : 'on'}">the AI may change it</button></span>${BRIEF_EDITOR.why('sw.' + k)}`; },
  // one roomy row of a setting: its name, the switch, every field with its own label (a part's settings under the picture; "all settings as a list")
  row(q) {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, inp = B.inp, { k, kind, hint, step, as } = q, f = s.set[k], common = as ? EV.LABEL[as] : null, W = x => B.why(`set.${k}.${x}`);
    const fields = f.off ? `<div class="be-f"><small class="wide" data-off="${k}">Not set: it is as long as the ${e(common)} (${e(as)}) says. The brief does not name it, and the simulations are started as before this setting existed.</small></div>` : f.fixed ? `<div class="be-f"><label><small>value</small>${inp(`set.${k}.value`, f.value, hint)}${W('value')}</label></div>`
      : `<div class="be-f">${kind === 'choice' ? `<label class="wide"><small>choices, separated by commas</small>${inp(`set.${k}.choices`, f.choices, 'TcpCubic, TcpNewReno')}${W('choices')}</label>`
          : `<label><small>from</small>${inp(`set.${k}.min`, f.min, hint)}${W('min')}</label><label><small>to</small>${inp(`set.${k}.max`, f.max, hint)}${W('max')}</label>`}
         <label><small>default</small>${inp(`set.${k}.def`, f.def, hint)}${W('def')}</label>${step ? `<label title="The AI's values are rounded to it, counted from “from”; the rounding is recorded. Empty: no step."><small>step (optional)</small>${inp(`set.${k}.step`, f.step || '', 'none')}${W('step')}</label>` : ''}
         <label class="wide"><small>meaning, one line the AI reads</small>${inp(`set.${k}.meaning`, f.meaning, '')}${W('meaning')}</label>${step ? '<small class="wide">A step: the AI\'s values are rounded to it, and the rounding is recorded as a clamp.</small>' : ''}</div>`;
    return `<div class="be-row" data-row="${k}"><div><b>${e(EV.LABEL[k] || k)}</b><code>${e(k)}</code></div><div>${B.sw(q)}</div>${fields}</div>`;
  },
  // block 2: one line per setting; the switch, then a value, or a range with its default and an optional step
  whoTable() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, inp = B.inp, lab = t => `<span class="lab">${t}</span>`;
    const line = q => { const { k, kind, hint, step } = q, f = s.set[k], W = x => B.why(`set.${k}.${x}`);
      const fields = f.off ? `<span class="sm" data-off="${k}">as the ${e(EV.LABEL[q.as])}</span>` : f.fixed ? `${inp(`set.${k}.value`, f.value, hint, 'w')}${W('value')}`
        : kind === 'choice' ? `${inp(`set.${k}.choices`, f.choices, 'TcpCubic, TcpNewReno', 'w')}${lab('from')}${inp(`set.${k}.def`, f.def, hint, 'w')}${W('choices')}${W('def')}`
        : `${inp(`set.${k}.min`, f.min, hint)}${lab('to')}${inp(`set.${k}.max`, f.max, hint)}${lab('from')}${inp(`set.${k}.def`, f.def, hint)}${step ? `${lab('step')}${inp(`set.${k}.step`, f.step || '', 'none')}` : ''}${W('min')}${W('max')}${W('def')}${W('step')}`;
      return `<tr data-row="${k}"><td>${EV.label(k, f.meaning)}</td><td>${B.sw(q)}</td><td>${fields}${B.why(`set.${k}.meaning`)}</td></tr>`; };
    return `<table class="be-who" id="be-who"><tbody>${B.SETTINGS.map(line).join('')}<tr data-row="udpPacketBytes"><td>${EV.label('udpPacketBytes')}</td><td><span data-by="operator" class="sm"><i class="sw"></i>fixed by the scenario</span></td><td>1400 bytes</td></tr></tbody></table>`;
  },
  draw() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, briefs = (B.ctx.st || {}).briefs || [], nw = EV.nw, inp = B.inp; B.list = briefs.join('|');
    if (!s || !s.set) { B.node.innerHTML = `<p class="sm">${s && s.msg ? e(s.msg.lines[0]) : 'No brief could be read from briefs/.'}</p>`; return; }
    const num = (kind, t) => (kind === 'num' && String(t).trim() !== '' && isFinite(Number(t)) ? Number(t) : String(t).trim()), pic = B.picture();
    // 1 · the network: the picture is the form; a click on a part opens its settings under it
    let b1 = '<p class="sm">Loading the picture of the system…</p>';
    if (pic) {
      const on = EV.sysFind(s.obj) ? s.obj : EV.sysId('sender', 'tc', 'Scheduler') || 'link';
      const f = EV.sysFind(on), mine = B.partSettings(on), around = (EV.OB.around || []).map((o, i) => `<a data-act="beobj" data-id="around-${i}" style="cursor:pointer${on === 'around-' + i ? ';font-weight:700' : ''}">${e(o.name.toLowerCase())}</a>`).join(', ');
      b1 = `<div class="be-pic" id="be-pic"><div class="ev-scroll" id="be-svg">${B.picSvg()}</div>
          <p class="sm gl-key"><span><i class="sw" style="background:var(--series-1)"></i>UDP</span><span><i class="sw" style="background:var(--series-2)"></i>TCP</span>${EV.sysLegend()}${around ? `<span>outside a packet's path: ${around}</span>` : ''}<span>click a part to open its settings</span></p></div>
        <p class="sm" id="be-part" style="margin:6px 0 2px"><b>${e(f.o.name)}</b> · ${mine.length ? `its setting${mine.length === 1 ? '' : 's'}:` : 'this part has no setting a brief can set.'}</p>${mine.map(B.row).join('')}`;
    }
    // 2 · who decides what
    const b2 = `${B.whoTable()}<p class="sm" style="margin-top:6px"><button class="cl" id="be-list" data-list="${s.list ? '0' : '1'}">${s.list ? 'close the list' : 'all settings as a list'}</button> the older form: one row per setting, with the line the AI reads about it</p>${s.list ? `<div id="be-rows">${B.SETTINGS.map(B.row).join('')}</div>` : ''}`;
    // 3 · the aim
    const pick = (f, v, opts) => `<select data-f="${f}">${opts.map(o => `<option${o === v ? ' selected' : ''}>${e(o)}</option>`).join('')}</select>`, conds = s.conditions.split('\n').map(c => c.trim()).filter(Boolean);
    const ready = s.goal === 'given' ? B.AIMS.find(a => a[2] === s.measure && a[3] === s.direction && JSON.stringify(a[4]) === JSON.stringify(conds)) : null, aim = s.goal === 'open' ? 'open' : ready && !s.custom ? ready[0] : 'custom';
    const radio = (v, html) => `<label><input type="radio" name="be-aim" data-aim="${v}"${aim === v ? ' checked' : ''}> ${html}</label>`;
    const b3 = `<div class="be-aim" id="be-aim">${B.AIMS.map(a => radio(a[0], `ready-made: ${e(a[1])}`)).join('')}${radio('custom', 'a target with conditions and a tolerance')}${radio('open', '<b>open</b>: the AI chooses its own aim and has to justify it')}</div>
      ${s.goal === 'given' ? `<div class="be-two" id="be-goal"><label>Target<small>one of the measures</small>${pick('measure', s.measure, B.OUTPUTS)}</label><label>Direction<small>as large or as small as possible</small>${pick('direction', s.direction, ['max', 'min'])}</label>
        <label style="grid-column:1/-1">Conditions<small>one per line, e.g. udp_loss_frac &lt;= 0.01; all must hold</small><textarea data-f="conditions" rows="2" spellcheck="false">${e(s.conditions)}</textarea>${B.why('conditions')}</label>
        <label>Tolerance, per cent (optional)<small>two results closer than this count as equal; default: none</small>${inp('tolerance', s.tolerance || '', 'none, e.g. 1')}${B.why('tolerance')}</label></div>` : ''}<div id="be-aim-says" style="margin-top:6px"></div>`;
    // 4 · what the AI is told, is not told, and can do
    const b4 = `<div class="be-two"><label>The task<small>the question, as the AI reads it</small><textarea data-f="task" rows="4">${e(s.task)}</textarea>${B.why('task')}</label>
        <label>The description of the system<small>plain words, written by you; {name} is filled from the fixed setting of that name, e.g. {linkRate}</small><textarea data-f="description" rows="4">${e(s.description)}</textarea>${B.why('description')}</label></div><div id="be-lists" style="margin-top:8px"></div>`;
    // 5 · the limits
    const b5 = `<div class="be-two"><label>Simulations in all<small>the most a session may run; default of the opened brief: ${e((s.orig || {}).sims || 'none')}</small>${inp('sims', s.sims, 'e.g. 40')}${B.why('sims')}</label><label>In one experiment<small>the most the AI may plan at once; default of the opened brief: ${e((s.orig || {}).per || 'none')}</small>${inp('per', s.per, 'e.g. 12')}${B.why('per')}</label></div>`;
    // 6 · kept from the AI: the scheduling policy
    const pol = v => `<label style="font-weight:400;margin:3px 0"><input type="radio" name="nw-policy" data-ch="nw" data-k="policy" value="${v}"${nw.policy === v ? ' checked' : ''}> <b>${v}</b> <span class="sm" style="display:inline">${e(EV.POLICY_SAYS[v])}${v === 'share' ? ' · the default' : v === 'random' ? '; the page shows it only once the session is scored' : ''}</span></label>`;
    const b6 = `<div id="be-policy" data-by="operator">${pol('share')}${pol('cap')}${pol('random')}<p class="sm">Never told to the AI.</p></div>`;
    // 7 · how the AI runs: every flag beside its default
    const field = (label, html, note, k) => `<div><span>${label}</span>${html}<span>${note}</span>${k ? B.why('nw.' + k) : ''}</div>`;
    const b7 = `<div class="kv" id="be-flags">
        ${field('simulations allowed at the start', `<input type="number" min="1" data-ch="nw" data-k="budget" value="${e(nw.budget)}" placeholder="${e(s.sims)}">`, "default: the brief's limit", 'budget')}
        ${field('draft before the answer', `<select data-ch="nw" data-k="draft"><option${nw.draft === 'on' ? ' selected' : ''}>on</option><option${nw.draft === 'off' ? ' selected' : ''}>off</option></select>`, 'default: on')}
        ${field('most tokens of one answer', `<input type="number" min="256" data-ch="nw" data-k="tokens" value="${e(nw.tokens)}" placeholder="${nw.draft === 'on' ? 32000 : 3000}">`, 'default: 32000 with a draft, 3000 without', 'tokens')}
        ${field('temperature', `<input type="number" min="0" max="2" step="0.1" data-ch="nw" data-k="temp" value="${e(nw.temp)}" placeholder="0.3">`, 'default: 0.3', 'temp')}
        ${field('baseline simulation first', `<label style="font-weight:400"><input type="checkbox" data-ch="nw" data-k="baseline"${nw.baseline ? ' checked' : ''}> run it</label>`, 'default: on · every knob at its default, by the harness')}</div>`;
    const blk = (i, body, cls) => EV.setBlock(i, body, { says: true, cls });
    const top = `<div class="be-top"><label>Start from a saved brief<small>its content fills the seven blocks</small><select id="be-open">${s.from ? `<option selected value="">the set-up of session ${e(s.from)}</option>` : ''}${briefs.map(b => `<option${b === s.baseId ? ' selected' : ''}>${e(b)}</option>`).join('')}</select></label>
        <label>Name of the new brief<small>needed once the form differs from every saved brief · letters, digits, - and _</small>${inp('id', s.id, 'e.g. two-hosts-short-queue')}${B.why('id')}</label>
        <div><label>Variations of ${e(s.baseId || s.fromBrief || 'this brief')}</label><small>each makes one change in the form and proposes a name</small><div class="be-var" id="be-var">${B.VARIATIONS.map(([k, name, , what, no]) => `<button data-var="${k}"${no(s) ? ` disabled title="${e(no(s))}"` : ` title="${e(what)}"`}>${e(name)}</button>`).join('')}</div></div></div>`;
    B.node.innerHTML = `${top}<div class="st" id="st-blocks">${blk(0, b1, 'st-wide')}${blk(1, b2)}${blk(2, b3)}${blk(3, b4, 'st-told')}<div class="st-row st-low">${blk(4, b5)}${blk(5, b6)}${blk(6, b7)}</div></div>
      <div class="be-start" id="be-start-box"><b>The session this will start</b> <span class="sm">the header strip its page will have</span><div id="be-strip"></div><div id="be-state" class="sm"></div><div id="be-msg"></div>
        <p style="margin-top:8px"><button id="be-save">Save as new brief</button> <button class="big primary" id="be-start">Start the session</button></p></div>`;
    B.paint();
  },

  // everything that follows the typed values, updated in place (the fields themselves are not touched)
  paint() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, st = B.ctx.st || {}, $ = id => B.node.querySelector('#' + id), nw = EV.nw;
    if (!s || !s.set || !$('be-save')) return;
    const briefs = st.briefs || [];
    if (briefs.join('|') !== B.list && document.activeElement !== $('be-open')) { B.list = briefs.join('|'); $('be-open').innerHTML = (s.from ? `<option selected value="">the set-up of session ${e(s.from)}</option>` : '') + briefs.map(b => `<option${b === s.baseId ? ' selected' : ''}>${e(b)}</option>`).join(''); }
    const svg = $('be-svg'); if (svg) svg.innerHTML = B.picSvg();  // the picture follows the form as it is typed
    // what cannot be used: the reason beside its field
    const bad = B.problems(), keys = Object.keys(bad);
    B.node.querySelectorAll('.be-why').forEach(el => { const w = bad[el.dataset.why] || ''; if (el.textContent !== w) el.textContent = w; });
    B.node.querySelectorAll('[data-f]').forEach(el => el.classList.toggle('bad', !!bad[el.dataset.f]));
    B.node.querySelectorAll('[data-ch=nw]').forEach(el => el.classList.toggle('bad', !!bad['nw.' + el.dataset.k]));
    // what differs from the brief or the session the form was filled from: marked
    const now = B.fields(), o = s.orig || {}, changed = Object.keys(now).filter(k => now[k] !== o[k] && (!/^set\./.test(k) || B.live(k.split('.')[1], k.split('.')[2])) && !(k === 'measure' || k === 'direction' || k === 'conditions' || k === 'tolerance' ? now.goal === 'open' && o.goal === 'open' : false));
    B.node.querySelectorAll('[data-f]').forEach(el => { if (el.dataset.f !== 'id') el.classList.toggle('chg', changed.includes(el.dataset.f)); });
    B.node.querySelectorAll('[data-sw]').forEach(el => el.closest('.be-sw').classList.toggle('chg', changed.includes('sw.' + el.dataset.sw)));
    const run = s.origRun, runChanged = run ? Object.keys(run).filter(k => String(run[k]) !== String(nw[k])) : [];
    B.node.querySelectorAll('[data-ch=nw]').forEach(el => { if (el.type !== 'radio') el.classList.toggle('chg', runChanged.includes(el.dataset.k)); });
    // the aim in words, the three lists and the exact text: they follow the form
    const given = B.given(), c = { mode: 'setup', b: given, man: B.man, given, flags: { baseline: !!nw.baseline } };
    const says = $('be-aim-says'); if (says) says.innerHTML = EV.setAim(c);
    const lists = $('be-lists'); if (lists) { const open = (lists.querySelector('details') || {}).open; if (open != null) EV.s.exact = open; lists.innerHTML = EV.setLists(c); }
    // the strip of the session to be, and what the two buttons will do
    const same = B.same(), id = s.id.trim(), running = st.sessions ? st.sessions.filter(x => x.running).length : 0, will = same ? s.baseId : id;
    const strip = $('be-strip'); if (strip) strip.innerHTML = EV.strip([['brief', EV.term('Brief', 'Brief'), will ? e(will) : '<span class="mut">needs a name</span>'], ['session', EV.term('Session', 'Session'), '<span class="mut">new</span>'], ['how', 'How it ended', '<span class="mut">not started</span>'],
      ['sims', EV.term('Simulation', 'Simulations'), `0 of ${e(String(nw.budget).trim() || s.sims.trim() || '?')}`], ['rec', 'Recommends', '<span class="mut">no recommendation yet</span>']], 'be-head');
    const n = changed.length + runChanged.length;
    $('be-save').disabled = !!s.busy || !id || !!keys.length || same; $('be-save').textContent = s.busy === 'save' ? 'Saving…' : 'Save as new brief';
    $('be-start').disabled = !!s.busy || !!keys.length || (!same && !id); $('be-start').textContent = s.busy === 'start' ? 'Starting…' : same ? `Start the session on ${s.baseId}` : id ? `Save as ${id} and start the session` : 'Start the session';
    $('be-state').innerHTML = keys.length ? `<span class="bad">${keys.length} value${keys.length === 1 ? '' : 's'} cannot be used: see the red line${keys.length === 1 ? '' : 's'} above.</span>`
      : `${s.from ? `Filled from session ${e(s.from)} (brief ${e(s.fromBrief)}): <span id="be-changed" data-n="${n}" class="${n ? 'chg-note' : ''}">${n ? `${n} value${n === 1 ? '' : 's'} changed, marked with a blue edge` : 'every value is that session\'s'}</span>. ` : same ? `The form is the saved brief ${e(s.baseId)}. ` : `The form differs from ${e(s.baseId || 'every saved brief')}<span id="be-changed" data-n="${n}"> (${n} value${n === 1 ? '' : 's'} changed, marked with a blue edge)</span>. `}
        ${same ? '' : id ? `It will be saved as briefs/${e(id)}.json; a saved brief is never overwritten.` : 'Give the new brief a name: a saved brief is never overwritten.'} ${running} session${running === 1 ? ' is' : 's are'} running now.`;
    $('be-msg').innerHTML = s.msg ? `<div class="be-msg ${s.msg.bad ? 'bad' : 'ok'}">${s.msg.lines.length > 1 ? `${e(s.msg.lines[0])}<ul>${s.msg.lines.slice(1).map(l => `<li>${e(l)}</li>`).join('')}</ul>` : e(s.msg.lines[0])}</div>` : '';
  },

  onInput(ev) {
    const B = BRIEF_EDITOR, t = ev.target, f = t.dataset && t.dataset.f;
    if (t.id === 'be-open') { if (ev.type === 'change' && t.value) { B.was = null; if (B.ctx.go && B.s.from) B.ctx.go({ from: null }); B.open(t.value); } return; }
    if (t.dataset && t.dataset.aim) { if (ev.type !== 'change') return; const s = B.s, a = B.AIMS.find(q => q[0] === t.dataset.aim);  // the aim: a ready-made one fills the target and the conditions
      if (t.dataset.aim === 'open') s.goal = 'open'; else { s.goal = 'given'; s.custom = !a; if (a) { s.measure = a[2]; s.direction = a[3]; s.conditions = a[4].join('\n'); } }
      return B.draw(); }
    if (t.dataset && t.dataset.ch === 'nw') return setTimeout(B.paint, 0);  // blocks 6 and 7: the page's own handler takes the value; then the lists and the strip follow
    if (!f) return;
    const path = f.split('.'); let o = B.s; path.slice(0, -1).forEach(p => { o = o[p]; }); o[path[path.length - 1]] = t.value;
    B.node.querySelectorAll(`[data-f="${f}"]`).forEach(el => { if (el !== t && el.value !== t.value) el.value = t.value; });  // the same field shown twice (under the picture, and in block 2)
    B.paint();
  },
  async save() {  // the form as a new brief; true when it was saved
    const B = BRIEF_EDITOR, b = B.toBrief();
    try { const r = await B.ctx.post('../api/brief', { brief: b }); B.s.baseId = r.saved; B.s.base = B.body(); B.s.id = ''; B.s.msg = { lines: [`Saved as ${r.file}.`] }; await B.ctx.after(); return true; }
    catch (x) { const parts = String(x.message).replace(/^brief [^:]*: /, '').split('; '); B.s.msg = { bad: true, lines: parts.length > 1 ? ['Not saved. The brief cannot be used as it is:', ...parts] : ['Not saved: ' + parts[0]] }; return false; }
  },
  async onClick(ev) {
    const B = BRIEF_EDITOR, part = ev.target.closest('[data-act=beobj]'); if (part) { B.s.obj = part.dataset.id; return B.draw(); }  // a part of the picture: its settings open under it
    const t = ev.target.closest('button'); if (!t || t.disabled) return;
    if (t.id === 'be-list') { B.s.list = !B.s.list; return B.draw(); }
    if (t.dataset.var) {  // a ready-made variation: one change in the form, and a new name proposed
      const s = B.s, v = B.VARIATIONS.find(q => q[0] === t.dataset.var), briefs = (B.ctx.st || {}).briefs || [], base = s.baseId || s.fromBrief || 'brief';
      if (v[0] === 'noloss') { const cs = s.conditions.split('\n').map(c => c.trim()).filter(c => c && !/^udp_loss_frac\b/.test(c)); s.conditions = [...cs, 'udp_loss_frac <= 0'].join('\n'); }
      if (v[0] === 'coarse') s.set.weightUdp.step = '0.01';
      if (v[0] === 'small') { s.sims = '15'; if (Number(s.per) > 15) s.per = '15'; }
      let id = `${base}-${v[2]}`.slice(0, 56), n = 1; while (briefs.includes(id)) id = `${base}-${v[2]}`.slice(0, 54) + '-' + (++n); s.id = id;
      s.msg = { lines: [`Variation “${v[1]}”: ${v[3]}. Save it as ${id}, or change the name first.`] }; return B.draw(); }
    if (t.dataset.sw) { const f = B.s.set[t.dataset.sw], q = B.SETTINGS.find(x => x.k === t.dataset.sw); f.off = t.dataset.to === 'off'; if (f.off) return B.draw();
      if (q.as && !f.value.trim() && !f.def.trim()) { const c = B.s.set[q.as]; f.value = f.def = (c.fixed ? c.value : c.def); }
      f.fixed = t.dataset.to === 'fixed'; if (f.fixed && !f.value.trim()) f.value = f.def; if (!f.fixed && !f.def.trim()) f.def = f.value;
      if (!f.fixed && q.open) { if (!f.min.trim()) f.min = q.open.min; if (!f.max.trim()) f.max = q.open.max; if (!f.meaning.trim()) f.meaning = q.open.meaning; }  // a setting no brief has opened yet: a range to start from
      return B.draw(); }
    if (t.id === 'be-save') { B.s.busy = 'save'; B.s.msg = null; B.paint(); await B.save(); B.s.busy = ''; return B.draw(); }
    if (t.id === 'be-start') {
      B.s.busy = 'start'; B.s.msg = null; B.paint();
      if (!B.same() && !(await B.save())) { B.s.busy = ''; return B.draw(); }  // a form that differs from every saved brief is saved under its new name first
      try { const r = await B.ctx.post('../api/session', { brief: B.s.baseId, ...B.ctx.flags() }); B.s.busy = ''; B.s.msg = { lines: [`Session ${r.id} started with brief ${B.s.baseId}.`] }; B.draw(); return B.ctx.started ? B.ctx.started(r.id) : null; }
      catch (x) { B.s.msg = { bad: true, lines: ['Not started: ' + x.message] }; }
      B.s.busy = ''; await B.ctx.after(); B.draw();
    }
  },
};
