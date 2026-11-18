// BRIEF_EDITOR: the set-up page, "New session". It has the seven blocks of a session's "The setting"
// (evidence_setting.js), in the same order, built from the same pieces; here each block is a form:
//   1 The network          the picture of the system, and under it one card per part with every value it has: a value that comes
//                          from a setting is a field and is set right there (the scheduler's card also chooses the scheduling
//                          policy), the mark before it says who decides and switches that; pointing at a part sets off its rows in
//                          block 2, and pointing at a row sets off its parts
//   2 Who decides what     each setting: fixed by the operator (a value), or the AI may change it (a range, a step); a numeric setting
//                          also has a bar beside its fields: drag its handle to set the value, or the two ends of the AI's range and the
//                          value it starts from; the bar and the typed fields are the same values and follow each other
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
// what a brief asks, after its name in the list of briefs (from its goal; '' until its file is read, and outside the evidence page)
const briefAsks = b => (typeof EV !== 'undefined' && EV.briefSaysPlain && EV.briefSaysPlain(b) ? ' — ' + EV.briefSaysPlain(b) : '');
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
    // the settings of builds 6 and 7: a brief may leave them out (the program then does what it always did), fix them, or leave them to the AI
    { k: 'tcpInitCwnd', kind: 'num', whole: true, least: 1, hint: 'segments', step: true, as: 'default', dflt: ['10', "TCP's first window is ns-3's own, 10 segments"], open: { min: '1', max: '100', meaning: "TCP's first window: the segments it sends before its first acknowledgement" } },
    { k: 'tcpBufBytes', kind: 'num', whole: true, least: 4096, hint: 'bytes', step: true, as: 'default', dflt: ['1048576', "TCP's send and receive buffers are 1 MB each"], open: { min: '65536', max: '4194304', meaning: "TCP's send buffer and its receive buffer, in bytes each" } },
    { k: 'devQueuePkts', kind: 'num', whole: true, least: 1, hint: 'packets', step: true, as: 'default', dflt: ['10', "each device's transmit queue holds 10 packets"], open: { min: '1', max: '1000', meaning: "most packets a device's transmit queue holds; they wait there after the scheduler has chosen them" } },
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
.be label.be-none { display: flex; align-items: flex-start; gap: 7px; margin-top: 8px; cursor: pointer; } .be label.be-none input { width: auto; margin: 3px 0 0; flex: none; } .be label.be-none small { margin-bottom: 0; }
.be-top { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.4fr); gap: 8px 22px; align-items: start; margin-bottom: 10px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface-0); padding: 9px 13px 11px; }
.be-row { display: grid; grid-template-columns: 150px 250px minmax(0, 1fr); gap: 8px 14px; align-items: start; padding: 8px 0; border-top: 1px solid var(--grid); }
.be-row code { display: block; font-size: var(--f-sec); color: var(--text-muted); }
.be-sw { display: inline-flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; } .ev .be-sw button { font-size: var(--f-sec); padding: 3px 9px; border: 0; border-radius: 0; background: var(--surface-1); color: var(--text-secondary); }
.ev .be-sw button + button { border-left: 1px solid var(--border); } .ev .be-sw button.on { background: var(--text-primary); color: var(--surface-1); font-weight: 600; }
.be-f { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px 8px; } .be-f .wide { grid-column: 1 / -1; } .be-f small { margin: 0 0 2px; }
.be table.be-who td { padding: 2px 8px 2px 0; border-bottom: 0; vertical-align: middle; } .be table.be-who input { width: 5.6em; padding: 2px 6px; } .be table.be-who input.w { width: 9.5em; } .be table.be-who .lab { font-size: var(--f-sec); color: var(--text-muted); margin: 0 3px 0 6px; }
.be-bar { position: relative; display: inline-block; width: 100%; min-width: 150px; max-width: 250px; height: 27px; vertical-align: middle; --a: 0; --b: 0; --c: var(--bt-operator, var(--text-secondary)); } .be-bar[data-mode=knob] { --c: var(--bt-model, var(--text-primary)); }
.be-bar::before { content: ''; position: absolute; left: 6px; right: 6px; top: 6px; height: 4px; border-radius: 2px; background: var(--border); }
.be-bar-band { position: absolute; top: 6px; height: 4px; border-radius: 2px; left: calc(6px + (100% - 12px) * var(--a)); width: calc((100% - 12px) * (var(--b) - var(--a))); background: var(--c); opacity: .75; }
.be table.be-who .be-bar input[type=range] { position: absolute; left: 0; top: 0; width: 100%; height: 16px; margin: 0; padding: 0; border: 0; background: none; pointer-events: none; -webkit-appearance: none; appearance: none; outline: 0; }
.be-bar input[type=range]::-webkit-slider-runnable-track { height: 16px; background: none; border: 0; } .be-bar input[type=range]::-moz-range-track { height: 16px; background: none; border: 0; }
.be-bar input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; pointer-events: auto; width: 12px; height: 12px; margin-top: 2px; border-radius: 50%; background: var(--c); border: 2px solid var(--surface-1); box-sizing: border-box; cursor: ew-resize; }
.be-bar input[type=range]::-moz-range-thumb { pointer-events: auto; width: 12px; height: 12px; border-radius: 50%; background: var(--c); border: 2px solid var(--surface-1); box-sizing: border-box; cursor: ew-resize; }
.be-bar input[data-bar-h=min]::-webkit-slider-thumb, .be-bar input[data-bar-h=max]::-webkit-slider-thumb { height: 14px; margin-top: 1px; border: 0; border-radius: 0; background: linear-gradient(90deg, transparent 0 4px, var(--c) 4px 8px, transparent 8px); }
.be-bar input[data-bar-h=min]::-moz-range-thumb, .be-bar input[data-bar-h=max]::-moz-range-thumb { height: 14px; border: 0; border-radius: 0; background: linear-gradient(90deg, transparent 0 4px, var(--c) 4px 8px, transparent 8px); }
.be-bar input[data-bar-h=def] { z-index: 2; } .be-bar input[type=range]:focus-visible::-webkit-slider-thumb { box-shadow: 0 0 0 2px var(--text-primary); } .be-bar input[type=range]:focus-visible::-moz-range-thumb { box-shadow: 0 0 0 2px var(--text-primary); }
.be .be-bar small { position: absolute; top: 14px; margin: 0; font-size: var(--f-note); line-height: 13px; color: var(--text-muted); } .be .be-bar small.lo { left: 3px; } .be .be-bar small.hi { right: 3px; } .be table.be-who td.be-bar-td { padding: 2px 16px 2px 6px; width: 230px; }
.be table.be-who .be-fl { display: inline-flex; flex-direction: column; margin: 0 8px 0 0; vertical-align: bottom; font-weight: 400; } .be table.be-who .be-fl small { margin: 0 0 1px 2px; font-size: var(--f-note); line-height: 1.15; color: var(--text-muted); white-space: nowrap; } .be table.be-who td { padding-top: 3px; padding-bottom: 3px; }
.be .be-conv { display: inline-block; margin-left: 2px; vertical-align: bottom; margin-bottom: 3px; padding: 0 8px; border-radius: 6px; background: color-mix(in srgb, var(--text-primary) 6%, transparent); color: var(--text-secondary); font-size: var(--f-sec); font-weight: 600; white-space: nowrap; } .be .be-conv:empty { display: none; } .be table.be-who tr[data-row=tcpBufBytes] input[type=text] { width: 7.2em; }
.be .be-why { display: block; color: var(--warning); font-size: var(--f-sec); font-weight: 600; margin: 1px 0 0; } .be .be-why:empty { display: none; } .be input.bad, .be textarea.bad, .be select.bad { border-color: var(--warning); }
.be input.chg, .be textarea.chg, .be select.chg, .be .be-sw.chg { box-shadow: inset 3px 0 0 var(--text-primary); } .be .chg-note { font-weight: 600; }
.be-aim label { font-weight: 400; margin: 3px 0; } .be-task { display: block; border: 1px dashed var(--border); border-radius: 6px; padding: 6px 8px; background: var(--surface-1); font-weight: 400; line-height: 1.45; min-height: 4.4em; } #be-task-own { display: block; margin-top: 4px; font-weight: 400; }
.be-two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 12px; margin-top: 6px; }
.be-conf { display: grid; grid-template-columns: repeat(auto-fill, minmax(218px, 1fr)); gap: 6px 8px; margin: 8px 0 2px; } .be-c { border: 1px solid var(--border); border-radius: 8px; background: var(--surface-1); padding: 4px 9px 5px; font-size: var(--f-note); min-width: 0; }
.be-c-h { margin-bottom: 2px; } .be-c-h b { font-size: var(--f-sec); } .be-c-h span { color: var(--text-muted); } .be-c-r { display: grid; grid-template-columns: 43% minmax(0, 1fr); gap: 0 6px; line-height: 1.4; } .be-c-r > span { color: var(--text-secondary); } .be-c-r > b { font-weight: 500; overflow-wrap: anywhere; } .be-c-r[data-knob] > b { font-weight: 700; }
.be .be-c input[type=text], .be .be-c select { width: auto; max-width: 100%; padding: 0 4px; font-size: inherit; font-weight: 600; line-height: 1.3; border-radius: 4px; border-color: color-mix(in srgb, var(--text-secondary) 55%, var(--border)); background: var(--surface-0); } .be .be-c input[type=text]::placeholder { font-weight: 400; } .be .be-c select { max-width: calc(100% - 18px); padding: 0 0 0 2px; }
.ev .be-c button.be-m { border: 0; background: none; padding: 0 3px 0 0; margin: 0; min-height: 0; font-size: inherit; line-height: inherit; font-weight: 700; color: inherit; cursor: pointer; } .ev .be-c button.be-m[data-mark=fixed] { font-weight: 400; color: var(--text-muted); }
.be-c-r { align-items: baseline; margin: 1px 0; } .be-note { grid-column: 1 / -1; margin: 3px 0 4px; padding: 3px 8px 4px; border-radius: 6px; background: color-mix(in srgb, var(--text-primary) 6%, transparent); color: var(--text-secondary); font-weight: 400; line-height: 1.35; }
.be-note::before { content: 'i'; display: inline-block; width: 13px; height: 13px; margin-right: 5px; border: 1px solid currentColor; border-radius: 50%; font: italic 700 10px/13px Georgia, serif; text-align: center; vertical-align: 1px; opacity: .8; } .be-c-r .mut { font-weight: 400; }
.be-c.wd-hot-row, .be-c.pin { border-color: var(--text-primary); box-shadow: 0 0 0 1.5px var(--text-primary); } .be-c.wd-hot-row { background: color-mix(in srgb, var(--text-primary) 8%, var(--surface-1)); }
.be table.be-who tr.wd-hot-row td { background: color-mix(in srgb, var(--text-primary) 11%, transparent); } .be table.be-who tr.wd-hot-row td:first-child { box-shadow: inset 3px 0 0 var(--text-primary); font-weight: 700; } .be table.be-who td:first-child { padding-left: 7px; }
.be-conds { margin-top: 4px; } .be-cond { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 3px 0; } .be-cond select { width: auto; } .be-cond input[data-cond=v] { width: 8em; } .be-cond-h { font-size: var(--f-text); } .be-condbox small { color: var(--text-secondary); font-size: var(--f-sec); }
.be-var { display: flex; flex-wrap: wrap; gap: 6px; } .ev .be-var button { font-size: var(--f-sec); text-align: left; padding: 3px 9px; } .be-pic svg g[data-act] { cursor: pointer; }
.be-start { border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; margin-top: 14px; } .be-start .ev-head { position: static; box-shadow: none; margin: 6px 0 10px; }
.be-msg { margin: 8px 0 0; font-size: var(--f-text); padding: 6px 10px; border-left: 3px solid var(--border); } .be-msg ul { margin: 4px 0 0; padding-left: 18px; }
.be-msg.bad { border-color: var(--warning); } .be-msg.ok { border-color: var(--text-primary); }
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
    return { id: s.id.trim(), description: s.description.trim(), system: inOrder(system, so), knobs: inOrder(knobs, ko), goal, limits: { simulations: val('num', s.sims), simulations_per_experiment: val('num', s.per) } };
  },
  body() { const b = BRIEF_EDITOR.toBrief(); delete b.id; return JSON.stringify(b); },   // what the form says, without the id
  same() { const B = BRIEF_EDITOR; return !!B.s.baseId && B.body() === B.s.base; },      // the form and the saved brief are the same
  // the brief as the AI will be given it: the description's {names} filled from the fixed settings, then the manifest's measures and tools
  given() { const B = BRIEF_EDITOR, t = B.toBrief(), sys = t.system, b = { id: t.id || B.s.baseId || '', task: B.ownTask() || EV.taskText(t), description: t.description, system: t.system, knobs: t.knobs, goal: t.goal, limits: t.limits }; b.description = b.description.replace(/\{(\w+)\}/g, (m, k) => (k in sys ? String(sys[k]) : k in t.knobs ? `the knob ${k}` : m)); return { ...b, ...(B.man || {}) }; },

  // the task of the saved brief the form was opened from, when that brief states one of its own (a brief made before 2026-11-17) and the form is still
  // that brief: a session started on it as it is gets that text. In every other case the harness writes the task (tools.task_text; here EV.taskText)
  ownTask() { const B = BRIEF_EDITOR, t = (B.s.task || '').trim(); return t && B.same() ? t : ''; },
  // every field of the form by its name, as typed: what "changed" is measured against
  fields() { const B = BRIEF_EDITOR, s = B.s, o = { description: s.description, goal: s.goal, measure: s.measure, direction: s.direction, conditions: s.conditions, tolerance: s.tolerance, sims: s.sims, per: s.per };
    B.SETTINGS.forEach(({ k }) => { const f = s.set[k]; o[`sw.${k}`] = f.off ? 'off' : f.fixed ? 'fixed' : 'knob'; ['value', 'min', 'max', 'def', 'step', 'choices', 'meaning'].forEach(x => { o[`set.${k}.${x}`] = f[x] || ''; }); });
    return o; },
  // which of a setting's fields count in its present state (a hidden field cannot be "changed")
  live(k, x) { const f = BRIEF_EDITOR.s.set[k], q = BRIEF_EDITOR.SETTINGS.find(z => z.k === k); return f.off ? false : f.fixed ? x === 'value' : x === 'choices' ? q.kind === 'choice' : x === 'min' || x === 'max' ? q.kind !== 'choice' : x === 'step' ? !!q.step && q.kind !== 'choice' : x !== 'value'; },

  // The list "Start from a saved brief": the set-up of a session when the page was opened from one, then the saved briefs. An empty set-up is a choice of another
  // kind and has a box of its own under the list (#be-none): ticked, the list is off and says so; unticked, the form is filled again from the brief it held before.
  openOpts(briefs) { const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e; return (s.none ? '<option selected value="">not used: the set-up starts empty</option>' : s.from ? `<option selected value="">the set-up of session ${e(s.from)}</option>` : '') + briefs.map(b => `<option value="${e(b)}"${!s.none && b === s.baseId ? ' selected' : ''}>${e(b)}${briefAsks(b)}</option>`).join(''); },
  // An empty set-up: no saved brief behind the form. The texts are empty, the aim is open, nothing is left to the AI yet, and every setting stands fixed at the value the
  // first brief of the project gives it (B.blankOf: its system, its knobs' defaults through B.template, its limits), so that the form is one a session could run.
  blank() {
    const B = BRIEF_EDITOR, t = B.blankOf || {}, view = B.s ? [B.s.list, B.s.obj] : [];
    if (B.s && B.s.baseId) B.prev = B.s.baseId;   // the brief to go back to when the box is unticked
    B.s = { ...B.fromBrief({ task: '', description: '', system: { ...(t.system || {}) }, knobs: {}, goal: { kind: 'open' }, limits: { ...(t.limits || {}) } }), id: B.s ? B.s.id : '', baseId: '', none: true, from: null, msg: null, busy: '', list: view[0], obj: view[1] };
    B.s.base = ''; B.s.orig = B.fields(); B.s.origRun = { policy: 'share', budget: '', draft: 'on', tokens: '', temp: '', baseline: true };
    B.draw();
  },
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
      // the picture and the table of every setting ("Who decides what") set each other off: pointing at a part of the picture sets off the rows of
      // the settings that part shows (as objects.json records them); pointing at a row sets off the parts that show that setting
      B.node.addEventListener('mouseover', ev => { const c = s => (ev.target.closest ? ev.target.closest(s) : null), g = c('#be-pic svg g[data-id]') || c('#be-conf [data-part]'), tr = c('#be-who tr[data-row]'), id = g ? g.dataset.id || g.dataset.part : '', at = g ? 'p:' + id : tr ? 'r:' + tr.dataset.row : '';
        if (at === B.linkAt) return; B.linkAt = at; B.node.querySelectorAll('.wd-hot-row, .ohot').forEach(el => el.classList.remove('wd-hot-row', 'ohot'));
        const part = pid => { B.node.querySelectorAll(`#be-conf [data-part="${pid}"]`).forEach(el => el.classList.add('wd-hot-row')); B.node.querySelectorAll('#be-pic svg g[data-id]').forEach(q => { if (q.dataset.id === pid) q.classList.add('ohot'); }); };
        if (g) { part(id); B.linkKeys(id).forEach(k => B.node.querySelectorAll(`#be-who tr[data-row="${k}"]`).forEach(r => r.classList.add('wd-hot-row'))); }
        else if (tr) B.node.querySelectorAll('#be-pic svg g[data-id]').forEach(q => { if (B.linkKeys(q.dataset.id).includes(tr.dataset.row)) part(q.dataset.id); }); });
      B.node.addEventListener('mouseout', ev => { const r = ev.target.closest ? ev.target.closest('#be-conf .be-c-r') : null; if (r && !(ev.relatedTarget && r.contains(ev.relatedTarget))) setTimeout(B.confPaint, 0); });  // a row that was left as it was under the pointer (confPaint)
      B.node.addEventListener('mouseleave', () => { B.linkAt = ''; B.node.querySelectorAll('.wd-hot-row, .ohot').forEach(el => el.classList.remove('wd-hot-row', 'ohot')); });
      B.node.addEventListener('keydown', ev => { const t = ev.target, dir = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1 }[ev.key]; if (!dir || !t.dataset || !t.dataset.barK) return; ev.preventDefault();
        const k = t.dataset.barK, now = B.barText(k, Number(t.value)); let pos = Number(t.value); do { pos += dir; } while (pos > 0 && pos < 1000 && B.barText(k, pos) === now); t.value = Math.min(1000, Math.max(0, pos)); B.barMoved(t, true); });  // the next round value, not the next thousandth of the bar
      B.node.addEventListener('focusin', ev => { B.typing = ev.target; }); B.node.addEventListener('focusout', ev => { if (ev.relatedTarget ? !B.node.contains(ev.relatedTarget) : B.node.isConnected) B.typing = null; });  // kept when the page's redraw took the node out
      host.appendChild(B.node);
      B.node.innerHTML = '<p class="sm">Loading the briefs…</p>';
      const first = ((ctx.st || {}).briefs || [])[0];
      const [t, man] = await Promise.all([B.fetchBrief('two-hosts-open'), B.fetchJson('../harness/manifest.json')]); B.template = (t && t.knobs) || {}; B.blankOf = t; B.man = man;   // ranges offered when a fixed setting is switched to a knob; the measures and tools the AI is given
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
    if (!s.description.trim()) bad.description = 'the description cannot be empty';
    const fixed = new Set(B.SETTINGS.filter(q => !s.set[q.k].off).map(q => q.k).concat('udpPacketBytes')), odd = [...new Set([...s.description.matchAll(/\{(\w+)\}/g)].map(m => m[1]))].filter(k => !fixed.has(k));
    if (odd.length) bad.description = `{${odd[0]}} is not a setting of this set-up: a name in braces stands for a fixed setting's value, or for “the knob …” where the AI may change it`;
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
    if (whole(s.sims, 'the number of simulations')) bad.sims = whole(s.sims, 'the number of simulations'); if (whole(s.per, 'the number in one turn')) bad.per = whole(s.per, 'the number in one turn');
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
    const key = n => EV.sysOwn(n, k => !!s.set[k] && !s.set[k].off), v = EV.sysDerive(Object.fromEntries(B.SETTINGS.filter(({ k }) => !s.set[k].off).map(({ k, kind }) => [k, num(kind, s.set[k].fixed ? s.set[k].value : s.set[k].def)]))), on = EV.sysFind(s.obj) ? s.obj : '';
    return EV.sysSvg({ v, knob: n => !s.set[key(n)] ? false : !s.set[key(n)].fixed, fixed: n => !!s.set[key(n)] && s.set[key(n)].fixed, on, act: 'beobj', pol: '<text x="432" y="162" text-anchor="middle" class="sv" id="sy-pol">policy not told to the AI</text>' }); },
  // the settings a part of the picture holds: those its rows of objects.json name (a queue: the common length, and its own)
  partSettings(id) { const B = BRIEF_EDITOR, f = EV.sysFind(id), keys = f ? [...new Set(f.o.rows.flatMap(([, text]) => [...String(text).matchAll(/\{(\w+)\}/g)].flatMap(m => { const k = EV.sysKey(m[1]); return EV.SYS_OWN[k] ? [EV.SYS_OWN[k], k] : [k]; })))] : []; return B.SETTINGS.filter(q => keys.includes(q.k)); },
  inp(f, v, hint, cls) { return `<input type="text" data-f="${f}" value="${BRIEF_EDITOR.ctx.e(v)}" placeholder="${BRIEF_EDITOR.ctx.e(hint || '')}" spellcheck="false"${cls ? ` class="${cls}"` : ''}>`; },
  why(f) { return `<span class="be-why" data-why="${f}"></span>`; },
  sw(q) { const f = BRIEF_EDITOR.s.set[q.k], k = q.k;
    return `<span class="be-sw">${q.as ? `<button data-sw="${k}" data-to="off" class="${f.off ? 'on' : ''}">not set</button>` : ''}<button data-sw="${k}" data-to="fixed" class="${!f.off && f.fixed ? 'on' : ''}">fixed by the operator</button><button data-sw="${k}" data-to="knob" class="${f.off || f.fixed ? '' : 'on'}">the AI may change it</button></span>${BRIEF_EDITOR.why('sw.' + k)}`; },
  // one roomy row of a setting: its name, the switch, every field with its own label (a part's settings under the picture; "all settings as a list")
  row(q) {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, inp = B.inp, { k, kind, hint, step, as } = q, f = s.set[k], common = as ? EV.LABEL[as] : null, notSet = q.dflt ? `Not set: ${q.dflt[1]}.` : `Not set: it is as long as the ${e(common)} (${e(as)}) says.`, W = x => B.why(`set.${k}.${x}`);
    const fields = f.off ? `<div class="be-f"><small class="wide" data-off="${k}">${notSet} The brief does not name it, and the simulations are started as before this setting existed.</small></div>` : f.fixed ? `<div class="be-f"><label><small>value</small>${inp(`set.${k}.value`, f.value, hint)}${W('value')}</label></div>`
      : `<div class="be-f">${kind === 'choice' ? `<label class="wide"><small>choices, separated by commas</small>${inp(`set.${k}.choices`, f.choices, 'TcpCubic, TcpNewReno')}${W('choices')}</label>`
          : `<label><small>lowest</small>${inp(`set.${k}.min`, f.min, hint)}${W('min')}</label><label><small>highest</small>${inp(`set.${k}.max`, f.max, hint)}${W('max')}</label>`}
         <label><small>starts at</small>${inp(`set.${k}.def`, f.def, hint)}${W('def')}</label>${step ? `<label title="The AI's values are rounded to it, counted from “from”; the rounding is recorded. Empty: no step."><small>step (optional)</small>${inp(`set.${k}.step`, f.step || '', 'none')}${W('step')}</label>` : ''}
         <label class="wide"><small>meaning, one line the AI reads</small>${inp(`set.${k}.meaning`, f.meaning, '')}${W('meaning')}</label>${step ? '<small class="wide">A step: the AI\'s values are rounded to it, and the rounding is recorded as a clamp.</small>' : ''}</div>`;
    return `<div class="be-row" data-row="${k}"><div><b>${e(EV.LABEL[k] || k)}</b><code>${e(k)}</code></div><div>${B.sw(q)}</div>${fields}</div>`;
  },
  // block 2: one line per setting; the switch, then a value, or a range with its default and an optional step
  // the settings a part of the picture shows: the names in braces in its rows of objects.json (a queue's own length also stands for the common one)
  linkKeys(id) { const f = typeof EV !== 'undefined' && EV.OB && EV.sysFind(id); if (!f) return []; const own = { tcpShare: 'weightUdp', tcpVariantPlain: 'tcpVariant', segment: 'mtu' };
    return [...new Set(f.o.rows.flatMap(([, text]) => [...String(text).matchAll(/\{(\w+)\}/g)].flatMap(m => { const k = own[m[1]] || m[1]; return k === 'queuePktsUdp' || k === 'queuePktsTcp' ? [k, 'queuePkts'] : [k]; })))]; },
  // block 1, under the picture: the whole configuration of the network at once, one small card per part of the picture with every value it has
  // (objects.json), as the form has it now. A value that comes from a setting is a FIELD: it is set right there, in the card of the part it
  // belongs to (the same value as in block 2, which keeps the ranges and the steps). The mark before a field says who decides, and a click on it
  // switches that: ✦ the AI may change it (the field is then the value it starts from), ✧ fixed by the operator. A setting a brief may leave
  // out has an empty field that shows what the program does without it; a value typed there sets it, emptying it leaves it out again. The
  // scheduler's card also chooses the scheduling policy (the same choice as block 6). Pointing at a part of the picture sets off its card,
  // and the other way round.
  confVals() { const B = BRIEF_EDITOR, s = B.s, num = (kind, t) => (kind === 'num' && String(t).trim() !== '' && isFinite(Number(t)) ? Number(t) : String(t).trim()), key = n => EV.sysOwn(n, k => !!s.set[k] && !s.set[k].off);
    return { v: EV.sysDerive(Object.fromEntries(B.SETTINGS.filter(({ k }) => !s.set[k].off).map(({ k, kind }) => [k, num(kind, s.set[k].fixed ? s.set[k].value : s.set[k].def)]))), knob: n => !!s.set[key(n)] && !s.set[key(n)].fixed }; },
  CONF_SKIP: ['To', 'Port', 'Address', 'Counts', 'Reported as', 'Added by', 'Carries', 'Stores packets', 'Takes', 'Priority mark', 'Header added'],
  // rows that repeat, or follow from, a value that is set in another part's card: shown, not set here
  CONF_READ: ['Link rate (read from its device)', 'Capacity', 'Segment payload'],
  // what the chosen scheduling policy does with the numbers of the form, in one sentence under its choice: the policy needs no setting of its own, its two
  // rates are the two parts of the ratio times the link's rate (link-queue-disc.cc: share = deficit round robin by those weights, cap = one token bucket per flow at that rate)
  policyEffect(pol, v) {
    const B = BRIEF_EDITOR, w = Number(v.weightUdp), link = B.rate(String(v.linkRate)), mb = x => (x >= 1e9 ? +(x / 1e9).toPrecision(4) + ' Gbps' : +(x / 1e6).toPrecision(4) + ' Mbps');
    if (pol === 'random') return 'the harness chooses share or cap when the session starts';
    if (!isFinite(w) || !link) return '';
    const u = mb(w * link), t = mb((1 - w) * link), knob = !B.s.set.weightUdp.fixed ? ` (at the starting ratio ${w})` : '';
    return pol === 'cap' ? `UDP at most ${u}, TCP at most ${t}${knob}, even when the other sends less · the ratio times the link rate: nothing more to set`
      : `both sending: UDP ${u}, TCP ${t}${knob}; what one leaves unused goes to the other`;
  },
  // one setting as a field of a card, in the state the form has it: the mark of who decides, then the value
  confField(k) {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, q = B.SETTINGS.find(x => x.k === k), f = s.set[k], common = q.as && s.set[q.as] ? s.set[q.as] : null, name = EV.LABEL[k] || k;
    const knob = f.off ? !!common && !common.fixed : !f.fixed, range = !f.off && knob ? (q.kind === 'choice' ? ` (one of ${f.choices})` : ` (${f.min} to ${f.max})`) : '';
    const says = f.off ? (common ? `Not set: it is as long as the ${EV.LABEL[q.as] || q.as} says. A value typed here gives it a length of its own.` : `Not set: ${q.dflt ? q.dflt[1] : 'the program keeps its own value'}. A value typed here sets it.`)
      : knob ? `The AI may change the ${name}${range}; this is the value it starts from. The range and the step: block 2.` : `The ${name}, fixed by the operator.`;
    const mark = `<button class="be-m" data-sw="${k}" data-to="${knob ? 'fixed' : 'knob'}" data-mark="${knob ? 'knob' : 'fixed'}" title="${knob ? 'the AI may change it · click: fix it' : 'fixed by the operator · click: let the AI change it'}" aria-label="${e(name)}: ${knob ? 'the AI may change it; press to fix it' : 'fixed by the operator; press to let the AI change it'}">${knob ? '✦' : '✧'}</button>`;
    if (q.kind === 'choice') { const now = (f.fixed ? f.value : f.def).trim(), list = f.fixed ? ((B.template[k] || {}).choices || []) : f.choices.split(',').map(c => c.trim()).filter(Boolean), opts = list.includes(now) || !now ? list : [now, ...list];
      return `${mark}<select data-f="set.${k}.${f.fixed ? 'value' : 'def'}" data-card="1" data-t="${e(says)}" title="${e(says)}" aria-label="${e(name)}">${opts.map(c => `<option value="${e(c)}"${c === now ? ' selected' : ''}>${e(c.replace(/^Tcp/, ''))}</option>`).join('')}</select>`; }
    const ph = f.off ? String(common ? (common.fixed ? common.value : common.def) : q.dflt ? q.dflt[0] : '') : '', val = f.off ? '' : f.fixed ? f.value : f.def, w = Math.min(12, Math.max(4, String(val || ph).length + 2));
    return `${mark}<input type="text" ${f.off ? `data-on="${k}"` : `data-f="set.${k}.${f.fixed ? 'value' : 'def'}"${q.as ? ' data-opt="1"' : ''}`} data-card="1" value="${e(val)}" placeholder="${e(ph)}" data-t="${e(says)}" title="${e(says)}" aria-label="${e(name)}" spellcheck="false" style="width:${w}ch">`;
  },
  confGrid() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, O = EV.OB, { v, knob } = B.confVals(), of = (h, back) => (back ? O.layers.slice().reverse() : O.layers).flatMap(l => (h[l.key] || []).map((o, i) => [`${h.key}-${l.key}-${i}`, o, `${h.title.toLowerCase()} · ${l.name.toLowerCase()}`]));
    const parts = [...of(O.hosts[0]), ['link', O.channel, 'between the two devices'], ...O.hosts.slice(1).flatMap(h => of(h, true))];  // in the order a packet meets them: the sender from its applications down, the link, the receiver from its device up
    // only what configures the network: a row that names an address or a port, or that says what a part is for, is left out (it stands in the part's own card
    // on a session's page); a part left without a row is left out with it
    const rowsOf = o => o.rows.filter(([k]) => !B.CONF_SKIP.includes(k)), pol = ((typeof EV !== 'undefined' && EV.nw) || {}).policy || 'share';
    const plain = t => e(TASK_VIEW._rate(String(t)));
    // a row's value: the words of objects.json, and in the place of a setting's name its field (a value that only follows from a setting stays a text)
    // a note explains what the chosen value does (the scheduling policy with the form's numbers, the TCP type): it stands under its row over the card's whole
    // width, on a tinted ground with an "i" before it, so that it reads as an explanation and not as a value that is set
    let note = null;
    const value = ([k, text, flag], kn) => {
      if (flag === 'op') { note = ['be-eff', B.policyEffect(pol, v)]; return `<select data-ch="nw" data-k="policy" data-policy="${e(pol)}" data-card="1" title="How the scheduler divides the link: ${e(EV.POLICY_SAYS[pol] || '')}. The same choice as block 6; never told to the AI." aria-label="scheduling policy">${['share', 'cap', 'random'].map(p => `<option value="${p}"${p === pol ? ' selected' : ''}>${p}</option>`).join('')}</select> <i class="mut">· not told to the AI</i>`; }
      if (k === 'Turn size' && pol === 'cap') return '3000 bytes: the most a flow may send in one go';  // the same 3000 bytes of the program: under cap they are each flow's burst, not a turn
      if (B.CONF_READ.includes(k)) return (kn ? '✦ ' : '') + e(EV.sysFill(text, v));
      return String(text).split(/(\{\w+\})/).map(part => { const m = /^\{(\w+)\}$/.exec(part); if (!m) return plain(part);
        const key = EV.sysKey(m[1]), own = m[1] === key || m[1] === 'tcpVariantPlain' || m[1] === 'tcpBufPlain';
        if (!s.set[key] || !own) return `<span data-dv="1">${plain(v[m[1]] != null ? v[m[1]] : 'not recorded')}</span>`;
        if (key === 'tcpVariant') { const f = s.set.tcpVariant; note = ['be-tcp', EV.tcpLine(f.fixed ? f.value : f.def)]; return B.confField(key); }  // the chosen TCP type in one plain line, as a note under its row
        return B.confField(key) + (m[1] === 'tcpBufPlain' ? ` bytes <span class="mut"><span data-dv="1">${(t => (t ? (t[0] === '≈' ? '' : '= ') + e(t) : ''))(B.bytesSay(s.set.tcpBufBytes.off ? 1048576 : s.set.tcpBufBytes.fixed ? s.set.tcpBufBytes.value : s.set.tcpBufBytes.def))}</span></span>` : ''); }).join('');
    };
    return parts.filter(([, o]) => rowsOf(o).length).map(([id, o, where]) => `<div class="be-c${B.s.obj === id ? ' pin' : ''}" data-part="${id}"><div class="be-c-h"><b>${e(o.name)}</b> <span>${e(where)}</span></div>${rowsOf(o).map(r => { const kn = [...String(r[1]).matchAll(/\{(\w+)\}/g)].some(m => knob(m[1]));
      note = null; const val = value(r, kn);
      return `<div class="be-c-r"${kn ? ' data-knob="1"' : ''}><span>${e(r[0])}</span><b>${val}</b>${note && note[1] ? `<div class="be-note" id="${note[0]}" data-dv="1" role="note">${e(note[1])}</div>` : ''}</div>`; }).join('')}</div>`).join('');
  },
  // the cards as the form says now, in place: a row is written again only when what it says has changed, and never while its own field is being typed in
  confPaint() {
    const B = BRIEF_EDITOR, conf = B.node.querySelector('#be-conf'); if (!conf) return;
    const tmp = document.createElement('div'); tmp.innerHTML = B.confGrid(); const a = [...conf.querySelectorAll('.be-c-r')], b = [...tmp.querySelectorAll('.be-c-r')];
    if (a.length !== b.length || a.some(r => r.beSays == null)) { conf.innerHTML = tmp.innerHTML; conf.querySelectorAll('.be-c-r').forEach(r => { r.beSays = r.outerHTML; }); return; }
    a.forEach((r, i) => { const h = b[i].outerHTML; if (r.beSays === h) return;
      if (r.contains(document.activeElement) || r.matches(':hover')) { const now = [...r.querySelectorAll('[data-dv]')], to = [...b[i].querySelectorAll('[data-dv]')]; if (now.length === to.length) now.forEach((el, j) => { if (el.textContent !== to[j].textContent) el.textContent = to[j].textContent; }); return; }  // the field keeps its cursor; what follows from it (TCP's share beside the ratio) follows. A row under the pointer is left too: a click that is on its way (to the mark, to the list) must find the element it was pressed on; the row is written when the pointer leaves it
      b[i].beSays = h; r.replaceWith(b[i]); });
  },
  // one setting's line of block 2 (and its roomy row, when the list is open), written again after its state changed in a card: the rest of the form is not touched
  reRow(k) {
    const B = BRIEF_EDITOR, q = B.SETTINGS.find(x => x.k === k), tr = B.node.querySelector(`#be-who tr[data-row="${k}"]`), row = B.node.querySelector(`#be-rows .be-row[data-row="${k}"]`);
    if (tr) tr.outerHTML = B.whoLine(q); if (row) row.outerHTML = B.row(q); B.paint();
  },
  // A condition is stored as the harness reads it ("udp_loss_frac <= 0.01"); the form shows it as a row built from lists, so that nobody has to know
  // the measures' field names or the grammar: the measure by its plain name, the comparison in words, the value in the unit the page uses everywhere
  // (rates in Mbps, fractions in per cent, counts as they are). Several rows: all must hold.
  COND_OPS: [['<=', 'at most'], ['>=', 'at least'], ['<', 'under'], ['>', 'over'], ['==', 'equal to']],
  condUnit: k => (/_bps$/.test(k) ? ['Mbps', 1e6] : ['udp_loss_frac', 'link_util'].includes(k) ? ['%', 0.01] : ['', 1]),
  condParse(c) { const m = /^(\w+)\s*(<=|>=|<|>|==)\s*([-\d.eE]+)$/.exec(c.trim()); return m && BRIEF_EDITOR.OUTPUTS.includes(m[1]) ? { k: m[1], op: m[2], v: Number(m[3]) } : null; },
  condRows() {
    const B = BRIEF_EDITOR, e = B.ctx.e, plain = k => (typeof TH_DATA !== 'undefined' && TH_DATA.PLAIN[k]) || k, lines = B.s.conditions.split('\n').map(c => c.trim()).filter(Boolean);
    const row = (c, i) => { const p = B.condParse(c); if (!p) return `<div class="be-cond" data-i="${i}"><input type="text" data-cond="raw" value="${e(c)}" spellcheck="false" style="flex:1"><button class="cl" data-cond-del="${i}">remove</button></div>`;
      const [unit, f] = B.condUnit(p.k);
      return `<div class="be-cond" data-i="${i}"><select data-cond="k" aria-label="measure">${B.OUTPUTS.map(k => `<option value="${k}"${k === p.k ? ' selected' : ''}>${e(plain(k))}</option>`).join('')}</select>
        <select data-cond="op" aria-label="comparison">${B.COND_OPS.map(([op, w]) => `<option value="${e(op)}"${op === p.op ? ' selected' : ''}>${w}</option>`).join('')}</select>
        <input type="text" data-cond="v" value="${e(Number((p.v / f).toPrecision(12)))}" spellcheck="false" aria-label="value"><span class="sm be-cond-u">${unit}</span><button class="cl" data-cond-del="${i}" title="remove this condition">remove</button></div>`; };
    return `<div class="be-conds" id="be-conds">${lines.map(row).join('') || '<p class="sm" style="margin:0">No condition: every result counts.</p>'}<p style="margin:3px 0 0"><button class="cl" data-cond-add="1">add a condition</button></p></div>`;
  },
  // the conditions as the rows say now, back into the stored form
  condRead() { const B = BRIEF_EDITOR; B.s.conditions = [...B.node.querySelectorAll('#be-conds .be-cond')].map(r => { const raw = r.querySelector('[data-cond=raw]'); if (raw) return raw.value.trim(); const k = r.querySelector('[data-cond=k]').value, v = r.querySelector('[data-cond=v]').value.trim(), f = B.condUnit(k)[1];
      return `${k} ${r.querySelector('[data-cond=op]').value} ${v !== '' && isFinite(Number(v)) ? Number((Number(v) * f).toPrecision(12)) : v}`; }).filter(Boolean).join('\n'); },
  // a number of bytes as a person says it: "96 kB", "1 MB", "1.5 MB" ("≈" before it where that is rounded); '' for what is not a number of bytes
  bytesSay(t) { const n = Number(String(t).trim()); if (String(t).trim() === '' || !isFinite(n) || n < 0) return ''; const u = n >= 1048576 ? [1048576, 'MB'] : n >= 1024 ? [1024, 'kB'] : [1, 'bytes'], v = +(n / u[0]).toFixed(2); return `${v * u[0] === n ? '' : '≈ '}${v} ${u[1]}`; },
  // the sizes of a setting given in bytes, in words beside its fields ("= 96 kB to 16 MB, from 1 MB"): the fields keep the bytes the program takes
  CONV: ['tcpBufBytes'],
  convSay(k) { const B = BRIEF_EDITOR, f = B.s.set[k], y = B.bytesSay; if (f.off) return ''; if (f.fixed) return y(f.value) ? (y(f.value)[0] === '≈' ? '' : '= ') + y(f.value) : ''; return y(f.min) && y(f.max) ? `lowest ${y(f.min)} · highest ${y(f.max)}${y(f.def) ? ` · starts at ${y(f.def)}` : ''}` : ''; },
  // ---- the bar of a numeric setting (block 2). Its span is the range worth dragging over, [lowest, highest, 1 = in equal ratios (a rate, a delay,
  // a count of packets: 10 to 100 takes as much room as 100 to 1000)], in the setting's own unit (a rate in bps, a delay in seconds); a value outside
  // the span can still be typed, its handle then stands at the end. A place on the bar is 0 to 1000.
  BAR: { linkRate: [1e7, 1e10, 1], linkDelay: [1e-5, 1e-2, 1], mtu: [576, 1500, 0], udpRate: [1e7, 1e10, 1], weightUdp: [0.05, 0.95, 0], queuePkts: [1, 1000, 1], queuePktsUdp: [1, 1000, 1], queuePktsTcp: [1, 1000, 1],
         tcpInitCwnd: [1, 100, 1], tcpBufBytes: [4096, 16777216, 1], devQueuePkts: [1, 1000, 1], duration: [1, 60, 0], seed: [1, 1000, 0] },
  // where a typed value stands on its bar (null: it cannot be read as a value)
  barPos(k, text) { const B = BRIEF_EDITOR, [lo, hi, ratio] = B.BAR[k], r = B.size(B.SETTINGS.find(x => x.k === k), text); if (r.why || typeof r.n !== 'number') return null;
    const n = Math.min(hi, Math.max(lo, r.n)); return Math.round(1000 * (ratio ? Math.log(n / lo) / Math.log(hi / lo) : (n - lo) / (hi - lo))); },
  // the value at a place of the bar, as it would be typed: a round value (two digits of a rate or a delay, a whole number of packets, a ratio in hundredths, a
  // buffer of 1 or 1.5 times a power of two); a rate in whole Mbps or Gbps, a delay in whole us or ms, as the harness writes them
  barText(k, pos) { const B = BRIEF_EDITOR, q = B.SETTINGS.find(x => x.k === k), [lo, hi, ratio] = B.BAR[k], x = ratio ? lo * Math.pow(hi / lo, pos / 1000) : lo + (hi - lo) * pos / 1000, two = v => Number(v.toPrecision(2));
    if (q.kind === 'rate') { const m = Math.round(two(x) / 1e6); return m >= 1000 && m % 1000 === 0 ? `${m / 1000}Gbps` : `${m}Mbps`; }
    if (q.kind === 'time') { const us = Math.round(two(x * 1e6)); return us >= 1000 && us % 1000 === 0 ? `${us / 1000}ms` : `${us}us`; }
    if (k === 'tcpBufBytes') { const base = 2 ** Math.floor(Math.log2(x)); return String(Math.min(hi, x / base >= 1.75 ? base * 2 : x / base >= 1.25 ? base * 1.5 : base)); }
    if (k === 'weightUdp') return String(Number(x.toFixed(2)));
    return String(Math.min(hi, Math.max(lo, Math.round(ratio && x >= 10 ? two(x) : x)))); },
  // the bar itself: one handle for a fixed value; for a setting the AI may change, the two ends of its range and the value it starts from
  bar(q) { const B = BRIEF_EDITOR, e = B.ctx.e, k = q.k, f = B.s.set[k]; if (!B.BAR[k] || f.off || q.kind === 'choice') return '';
    const name = EV.LABEL[k] || k, hs = f.fixed ? [['value', 'its value']] : [['min', 'the lowest value the AI may set'], ['max', 'the highest value the AI may set'], ['def', 'the value the AI starts from']], end = p => TASK_VIEW._rate(k === 'tcpBufBytes' ? EV.sysDerive({ tcpBufBytes: Number(B.barText(k, p)) }).tcpBufPlain : B.barText(k, p));
    return `<span class="be-bar" data-bar="${k}" data-mode="${f.fixed ? 'fixed' : 'knob'}"><i class="be-bar-band"></i>${hs.map(([h, says]) => `<input type="range" min="0" max="1000" step="1" value="${B.barPos(k, f[h]) ?? 0}" data-bar-k="${k}" data-bar-h="${h}" aria-label="${e(name)}: ${says}" title="${e(name)}: ${says} · drag, or use the arrow keys">`).join('')}<small class="lo">${e(end(0))}</small><small class="hi">${e(end(1000))}</small></span>`; },
  // the bars as the form says now: every handle at its typed value (but the one being dragged), the shaded part from the lowest to the highest (a fixed value: up to it)
  barPaint() { const B = BRIEF_EDITOR; B.node.querySelectorAll('.be-bar').forEach(bar => { const k = bar.dataset.bar, f = B.s.set[k], at = {};
    bar.querySelectorAll('input[type=range]').forEach(el => { const p = B.barPos(k, f[el.dataset.barH]); at[el.dataset.barH] = p ?? Number(el.value); if (p != null && el !== document.activeElement && Number(el.value) !== p) el.value = p; });
    bar.style.setProperty('--a', f.fixed ? 0 : (at.min ?? 0) / 1000); bar.style.setProperty('--b', (f.fixed ? at.value ?? 0 : Math.max(at.min ?? 0, at.max ?? 0)) / 1000); }); },
  // a handle was moved: its value is written as if typed; the ends of a range cannot pass each other, and the starting value stays between them
  barMoved(t, done) { const B = BRIEF_EDITOR, k = t.dataset.barK, h = t.dataset.barH, f = B.s.set[k], q = B.SETTINGS.find(x => x.k === k), at = x => B.barPos(k, f[x]); let pos = Number(t.value);
    if (h === 'min') pos = Math.min(pos, (at('max') ?? 1000) - 10); if (h === 'max') pos = Math.max(pos, (at('min') ?? 0) + 10); if (h === 'def') pos = Math.min(at('max') ?? 1000, Math.max(at('min') ?? 0, pos));
    f[h] = B.barText(k, pos);
    if (h !== 'value') { const lo = B.size(q, f.min), hi = B.size(q, f.max), d = B.size(q, f.def); if (!lo.why && !d.why && d.n < lo.n) f.def = f.min; if (!hi.why && !d.why && d.n > hi.n) f.def = f.max; }
    if (pos !== Number(t.value) || done) t.value = done ? B.barPos(k, f[h]) ?? pos : pos;   // let go: the handle settles on the round value it wrote
    B.node.querySelectorAll(`[data-f^="set.${k}."]`).forEach(el => { const v = f[el.dataset.f.split('.')[2]]; if (v != null && el.value !== v && el !== document.activeElement) el.value = v; });
    B.paint(); },
  whoLine(q) {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, inp = B.inp, lab = t => `<span class="lab">${t}</span>`;
    { const { k, kind, hint, step } = q, f = s.set[k], W = x => B.why(`set.${k}.${x}`);
      // every field says what it is, above it: a fixed setting has its value; one the AI may change has the lowest and the highest value the AI may set, the value the
      // session starts at (the baseline uses it, and the AI's first designs start from it), and, where it has one, the step its values are rounded to
      const fl = (name, html, tip) => `<label class="be-fl"${tip ? ` title="${e(tip)}"` : ''}><small>${name}</small>${html}</label>`;
      const fields = f.off ? `<span class="sm" data-off="${k}">${q.dflt ? e(q.dflt[1]) : 'as the ' + e(EV.LABEL[q.as])}</span>` : f.fixed ? `${fl('value', inp(`set.${k}.value`, f.value, hint, 'w'), 'The value every simulation uses')}${W('value')}`
        : kind === 'choice' ? `${fl('the AI may choose among', inp(`set.${k}.choices`, f.choices, 'TcpCubic, TcpNewReno', 'w'), 'The choices, separated by commas')}${fl('starts at', inp(`set.${k}.def`, f.def, hint, 'w'), 'The choice the session starts at: the baseline simulation uses it')}${W('choices')}${W('def')}`
        : `${fl('lowest', inp(`set.${k}.min`, f.min, hint), 'The lowest value the AI may set')}${fl('highest', inp(`set.${k}.max`, f.max, hint), 'The highest value the AI may set')}${fl('starts at', inp(`set.${k}.def`, f.def, hint), 'The value the session starts at: the baseline simulation uses it')}${step ? fl('step', inp(`set.${k}.step`, f.step || '', 'none'), 'Optional: the AI’s values are rounded to this step, counted from the lowest') : ''}${W('min')}${W('max')}${W('def')}${W('step')}`;
      return `<tr data-row="${k}"><td>${EV.label(k, f.meaning)}</td><td>${B.sw(q)}</td><td class="be-bar-td">${B.bar(q)}</td><td>${fields}${B.CONV.includes(k) && !f.off ? `<span class="be-conv" data-conv="${k}">${e(B.convSay(k))}</span>` : ''}${B.why(`set.${k}.meaning`)}</td></tr>`; }
  },
  whoTable() {
    const B = BRIEF_EDITOR;
    return `<table class="be-who" id="be-who"><tbody>${B.SETTINGS.map(B.whoLine).join('')}<tr data-row="udpPacketBytes"><td>${EV.label('udpPacketBytes')}</td><td><span data-by="operator" class="sm"><i class="sw"></i>fixed by the scenario</span></td><td></td><td>1400 bytes</td></tr></tbody></table>`;
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
          <p class="sm gl-key">${EV.sysLegend()}${around ? `<span>outside a packet's path: ${around}</span>` : ''}<span>below: one card per part, with every value it has</span><span><b>a value in a field is set right there</b></span><span><b>✧</b> before a field: fixed by the operator · click <b>✦</b> or <b>✧</b> to switch</span><span>the scheduler's card chooses the scheduling policy</span><span>ranges and steps: block 2</span></p>
          <div class="be-conf" id="be-conf" data-exact="1">${B.confGrid()}</div></div>`;
    }
    // 2 · who decides what
    const b2 = `${B.whoTable()}<p class="sm" style="margin-top:6px"><button class="cl" id="be-list" data-list="${s.list ? '0' : '1'}">${s.list ? 'close the list' : 'all settings as a list'}</button> the older form: one row per setting, with the line the AI reads about it</p>${s.list ? `<div id="be-rows">${B.SETTINGS.map(B.row).join('')}</div>` : ''}`;
    // 3 · the aim
    const pick = (f, v, opts) => `<select data-f="${f}">${opts.map(o => `<option${o === v ? ' selected' : ''}>${e(o)}</option>`).join('')}</select>`, conds = s.conditions.split('\n').map(c => c.trim()).filter(Boolean);
    const ready = s.goal === 'given' ? B.AIMS.find(a => a[2] === s.measure && a[3] === s.direction && JSON.stringify(a[4]) === JSON.stringify(conds)) : null, aim = s.goal === 'open' ? 'open' : ready && !s.custom ? ready[0] : 'custom';
    const radio = (v, html) => `<label><input type="radio" name="be-aim" data-aim="${v}"${aim === v ? ' checked' : ''}> ${html}</label>`;
    const b3 = `<div class="be-aim" id="be-aim">${B.AIMS.map(a => radio(a[0], `ready-made: ${e(a[1])}`)).join('')}${radio('custom', 'a target with conditions and a tolerance')}${radio('open', '<b>open</b>: the AI chooses its own aim and has to justify it')}</div>
      ${s.goal === 'given' ? `<div class="be-two" id="be-goal"><label>Target<small>the measure to make as large or as small as possible</small><select data-f="measure">${B.OUTPUTS.map(k => `<option value="${k}"${k === s.measure ? ' selected' : ''}>${e((typeof TH_DATA !== 'undefined' && TH_DATA.PLAIN[k]) || k)}</option>`).join('')}</select></label><label>Direction<small>which way is better</small><select data-f="direction"><option value="max"${s.direction === 'max' ? ' selected' : ''}>as large as possible</option><option value="min"${s.direction === 'min' ? ' selected' : ''}>as small as possible</option></select></label>
        <div style="grid-column:1/-1" class="be-condbox"><b class="be-cond-h">Conditions</b> <small>each a measure, a comparison and a value, chosen from the lists; all must hold</small>${B.condRows()}${B.why('conditions')}</div>
        <label>Tolerance, per cent (optional)<small>two results closer than this count as equal; default: none</small>${inp('tolerance', s.tolerance || '', 'none, e.g. 1')}${B.why('tolerance')}</label></div>` : ''}<div id="be-aim-says" style="margin-top:6px"></div>`;
    // 4 · what the AI is told, is not told, and can do
    const b4 = `<div class="be-two"><label>The task<small>the question, as the AI reads it · written by the harness from the aim and the settings the AI may change, so that it always agrees with them</small><span id="be-task" class="be-task" data-own="harness"></span><span id="be-task-own" class="sm"></span></label>
        <label>The description of the system<small>plain words, written by you; a setting's name in braces is filled with its value where it is fixed and reads “the knob …” where the AI may change it, so the text stays true either way (the name: point at a setting's label)</small><textarea data-f="description" rows="4">${e(s.description)}</textarea>${B.why('description')}</label></div><div id="be-lists" style="margin-top:8px"></div>`;
    // 5 · the limits
    const b5 = `<div class="be-two"><label>Simulations in all<small>the most a session may run; default of the opened brief: ${e((s.orig || {}).sims || 'none')}</small>${inp('sims', s.sims, 'e.g. 40')}${B.why('sims')}</label><label>In one turn<small>the most the AI may run in a single turn (a turn holds one experiment); default of the opened brief: ${e((s.orig || {}).per || 'none')}</small>${inp('per', s.per, 'e.g. 12')}${B.why('per')}</label></div>`;
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
        ${field('baseline simulation first', `<label style="font-weight:400"><input type="checkbox" data-ch="nw" data-k="baseline"${nw.baseline ? ' checked' : ''}> run it</label>`, 'default: on · every knob at its default, by the harness')}
        ${field('who rules on the tests', EV.armField(), 'default: one AI · a supervisor is a second AI, asked apart from the researcher')}</div>`;
    const blk = (i, body, cls) => EV.setBlock(i, body, { says: true, cls });
    const top = `<div class="be-top"><div><label>Start from a saved brief<small>its content fills the seven blocks</small><select id="be-open"${s.none ? ' disabled' : ''}>${B.openOpts(briefs)}</select></label>
        <label class="be-none"><input type="checkbox" id="be-none"${s.none ? ' checked' : ''}><span>or start from an empty set-up<small>no saved brief: you write the description, every setting starts fixed</small></span></label></div>
        <label>Name of the new brief<small>needed once the form differs from every saved brief · letters, digits, - and _</small>${inp('id', s.id, 'e.g. two-hosts-short-queue')}${B.why('id')}</label>
        <div><label>Variations of ${e(s.baseId || s.fromBrief || 'this brief')}</label><small>each makes one change in the form and proposes a name</small><div class="be-var" id="be-var">${B.VARIATIONS.map(([k, name, , what, no]) => `<button data-var="${k}"${no(s) ? ` disabled title="${e(no(s))}"` : ` title="${e(what)}"`}>${e(name)}</button>`).join('')}</div></div></div>`;
    B.node.innerHTML = `${top}<div class="st" id="st-blocks">${blk(0, b1, 'st-wide')}${blk(1, b2)}${blk(2, b3)}${blk(3, b4, 'st-told')}<div class="st-row st-low">${blk(4, b5)}${blk(5, b6)}${blk(6, b7)}</div></div>
      <div class="be-start" id="be-start-box"><b>The session this will start</b> <span class="sm">the header strip its page will have</span><div id="be-strip"></div><div id="be-state" class="sm"></div><div id="be-msg"></div>
        <p style="margin-top:8px"><button id="be-save">Save as new brief</button> <button class="big primary" id="be-start">Start the session</button></p></div>`;
    B.node.querySelectorAll('#be-conf .be-c-r').forEach(r => { r.beSays = r.outerHTML; });
    B.paint();
  },

  // everything that follows the typed values, updated in place (the fields themselves are not touched)
  paint() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, st = B.ctx.st || {}, $ = id => B.node.querySelector('#' + id), nw = EV.nw;
    if (!s || !s.set || !$('be-save')) return;
    const briefs = st.briefs || [];
    if (briefs.map(b => b + briefAsks(b)).join('|') !== B.list && document.activeElement !== $('be-open')) { B.list = briefs.map(b => b + briefAsks(b)).join('|'); $('be-open').innerHTML = B.openOpts(briefs); }
    const svg = $('be-svg'); if (svg) svg.innerHTML = B.picSvg();  // the picture follows the form as it is typed
    B.confPaint();  // and so do the cards of the whole configuration under it
    B.barPaint();   // and the bars of block 2
    B.node.querySelectorAll('[data-conv]').forEach(el => { const t = B.convSay(el.dataset.conv); if (el.textContent !== t) el.textContent = t; });  // a size in bytes, said as a size
    B.node.querySelectorAll('#be-policy input[type=radio]').forEach(r => { r.checked = r.value === nw.policy; });  // the policy may have been chosen on the scheduler's card
    // what cannot be used: the reason beside its field
    const bad = B.problems(), keys = Object.keys(bad);
    B.node.querySelectorAll('.be-why').forEach(el => { const w = bad[el.dataset.why] || ''; if (el.textContent !== w) el.textContent = w; });
    B.node.querySelectorAll('[data-f]').forEach(el => el.classList.toggle('bad', !!bad[el.dataset.f]));
    B.node.querySelectorAll('[data-ch=nw]').forEach(el => el.classList.toggle('bad', !!bad['nw.' + el.dataset.k]));
    // what differs from the brief or the session the form was filled from: marked
    const now = B.fields(), o = s.orig || {}, changed = Object.keys(now).filter(k => now[k] !== o[k] && (!/^set\./.test(k) || B.live(k.split('.')[1], k.split('.')[2])) && !(k === 'measure' || k === 'direction' || k === 'conditions' || k === 'tolerance' ? now.goal === 'open' && o.goal === 'open' : false));
    B.node.querySelectorAll('[data-f]').forEach(el => { if (el.dataset.f !== 'id') el.classList.toggle('chg', changed.includes(el.dataset.f)); });
    B.node.querySelectorAll('.be-sw [data-sw]').forEach(el => el.closest('.be-sw').classList.toggle('chg', changed.includes('sw.' + el.dataset.sw)));
    B.node.querySelectorAll('#be-conf [data-f]').forEach(el => { el.title = bad[el.dataset.f] ? `Cannot be used: ${bad[el.dataset.f]}` : el.dataset.t || ''; });  // a card has no room for the reason: it is the field's own note
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
    const wait = EV.mustWait ? EV.mustWait() : null;
    // the task: the sentence the harness writes from the form as it stands; and, while the form is still a saved brief that states a task of its own, that text and what it means
    { const tk = $('be-task'), own = $('be-task-own'), t = B.toBrief(), mine = B.ownTask(), made = EV.taskText(t);
      if (tk) tk.textContent = made;
      if (own) own.innerHTML = mine && mine !== made ? `<span class="warnc">The saved brief ${e(s.baseId)} states a task of its own, written by hand, and a session started on it as it is gets that text, whatever the aim and the settings say:</span> <span id="be-task-old" data-own="operator">${e(mine)}</span> <span>Save the form under a new name and the new brief gets the sentence above.</span>` : ''; }
    $('be-start').disabled = !!s.busy || !!keys.length || (!same && !id) || !!wait; $('be-start').title = wait || ''; $('be-start').textContent = s.busy === 'start' ? 'Starting…' : same ? `Start the session on ${s.baseId}` : id ? `Save as ${id} and start the session` : 'Start the session';
    $('be-state').innerHTML = keys.length ? `<span class="warnc">${keys.length} value${keys.length === 1 ? '' : 's'} cannot be used: see the reason beside ${keys.length === 1 ? 'it' : 'each'}, above.</span>`
      : `${s.from ? `Filled from session ${e(s.from)} (brief ${e(s.fromBrief)}): <span id="be-changed" data-n="${n}" class="${n ? 'chg-note' : ''}">${n ? `${n} value${n === 1 ? '' : 's'} changed, marked with a dark edge` : 'every value is that session\'s'}</span>. ` : same ? `The form is the saved brief ${e(s.baseId)}. ` : s.none ? `The form started empty: no saved brief stands behind it<span id="be-changed" data-n="${n}">${n ? ` (${n} value${n === 1 ? '' : 's'} filled in or changed since, marked with a dark edge)` : ''}</span>. ` : `The form differs from ${e(s.baseId || 'every saved brief')}<span id="be-changed" data-n="${n}"> (${n} value${n === 1 ? '' : 's'} changed, marked with a dark edge)</span>. `}
        ${same ? '' : id ? `It will be saved as <span data-own="operator">briefs/${e(id)}.json</span>; a saved brief is never overwritten.` : 'Give the new brief a name: a saved brief is never overwritten.'} ${wait ? `<b id="be-wait" class="warnc">${e(wait)}</b>` : `${running} session${running === 1 ? ' is' : 's are'} running now.`}`;
    $('be-msg').innerHTML = s.msg ? `<div class="be-msg ${s.msg.bad ? 'bad' : 'ok'}">${s.msg.lines.length > 1 ? `${e(s.msg.lines[0])}<ul>${s.msg.lines.slice(1).map(l => `<li>${e(l)}</li>`).join('')}</ul>` : e(s.msg.lines[0])}</div>` : '';
  },

  onInput(ev) {
    const B = BRIEF_EDITOR, t = ev.target, f = t.dataset && t.dataset.f;
    if (t.id === 'be-open') { if (ev.type === 'change' && t.value) { B.was = null; if (B.ctx.go && B.s.from) B.ctx.go({ from: null }); B.open(t.value); } return; }
    if (t.id === 'be-none') {
      if (ev.type !== 'change') return;
      const briefs = (B.ctx.st || {}).briefs || [], back = briefs.includes(B.prev) ? B.prev : briefs.includes('two-hosts-open') ? 'two-hosts-open' : briefs[0];
      B.was = null; if (B.ctx.go && B.s.from) B.ctx.go({ from: null });
      if (t.checked) B.blank(); else if (back) B.open(back);
      return;
    }
    if (t.dataset && t.dataset.aim) { if (ev.type !== 'change') return; const s = B.s, a = B.AIMS.find(q => q[0] === t.dataset.aim);  // the aim: a ready-made one fills the target and the conditions
      if (t.dataset.aim === 'open') s.goal = 'open'; else { s.goal = 'given'; s.custom = !a; if (a) { s.measure = a[2]; s.direction = a[3]; s.conditions = a[4].join('\n'); } }
      return B.draw(); }
    if (t.dataset && t.dataset.cond) { B.condRead(); B.s.custom = true; return t.tagName === 'SELECT' && ev.type === 'change' ? B.draw() : setTimeout(B.paint, 0); }  // a row of the conditions: a list redraws the row (its unit), typing does not
    if (t.dataset && t.dataset.ch === 'nw') return setTimeout(B.paint, 0);  // blocks 6 and 7: the page's own handler takes the value; then the lists and the strip follow
    if (t.dataset && t.dataset.barK) return B.barMoved(t, ev.type === 'change');  // a handle of a bar in block 2
    if (t.dataset && t.dataset.on) {  // a card's field of a setting the brief leaves out: a value typed there sets it (once typed: the form's lines change with it)
      if (ev.type !== 'change' || !t.value.trim()) return; const g = B.s.set[t.dataset.on]; g.off = false; g.fixed = true; g.value = g.def = t.value.trim(); return B.reRow(t.dataset.on); }
    if (!f) return;
    if (t.dataset.opt && ev.type === 'change' && !t.value.trim()) { const k = f.split('.')[1]; B.s.set[k].off = true; return B.reRow(k); }  // emptied in its card: left out again
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
    const add = ev.target.closest('[data-cond-add]'), del = ev.target.closest('[data-cond-del]');  // the conditions: one more row (the first measure not yet used), or one row less
    if (add || del) { const B = BRIEF_EDITOR, st = B.s; B.condRead(); const lines = st.conditions.split('\n').filter(Boolean);
      if (add) { const used = lines.map(c => (B.condParse(c) || {}).k), k = ['udp_loss_frac', ...B.OUTPUTS].find(q => !used.includes(q)) || 'udp_loss_frac'; lines.push(k === 'udp_loss_frac' ? 'udp_loss_frac <= 0.01' : `${k} >= 0`); } else lines.splice(Number(del.dataset.condDel), 1);
      st.conditions = lines.join('\n'); st.custom = true; return B.draw(); }
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
    if (t.dataset.sw) { const f = B.s.set[t.dataset.sw], q = B.SETTINGS.find(x => x.k === t.dataset.sw), was = f.off ? null : f.fixed ? f.value : f.def; f.off = t.dataset.to === 'off'; if (f.off) return B.draw();
      if (t.classList.contains('be-m') && was != null && String(was).trim()) f.value = f.def = was;  // the mark of a card: the value in its field stays the value, whoever decides
      if (q.dflt && !f.value.trim() && !f.def.trim()) f.value = f.def = q.dflt[0];  // it starts from what the program does without it
      else if (q.as && !f.value.trim() && !f.def.trim()) { const c = B.s.set[q.as]; f.value = f.def = (c.fixed ? c.value : c.def); }
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
