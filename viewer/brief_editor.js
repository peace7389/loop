// BRIEF_EDITOR: the operator's form for writing a brief (briefs/<id>.json), mounted in the Control page.
// A brief is opened from the existing ones, changed, and saved under a NEW id through POST /api/brief; control.py
// checks it the way loop.py does (tools.check_brief) and never overwrites a file. "Start session with this brief"
// starts a session on the brief the form shows, once the form and a saved brief are the same.
// The form lives in one node that is kept when the page around it is redrawn, so nothing typed is lost.
//   BRIEF_EDITOR.mount(host, ctx)   ctx = { st: control.py's status, post(path, body), e: escape, sec: section frame,
//                                           session(): the other choices of a session, after(): reload the page's data }
// ======================================================================================================
const BRIEF_EDITOR = {
  // every setting of the program, in the order shown; `only` = it can only be fixed (the answer format has no field for it)
  SETTINGS: [
    { k: 'linkRate', name: 'Link rate', kind: 'text', only: true, hint: 'e.g. 1Gbps' }, { k: 'linkDelay', name: 'Link delay, one way', kind: 'text', only: true, hint: 'e.g. 50us' },
    { k: 'mtu', name: 'Largest packet', kind: 'num', only: true, hint: 'bytes' }, { k: 'weightUdp', name: 'UDP share of the link', kind: 'num', hint: '0.05 to 0.95' },
    { k: 'udpRate', name: 'UDP offered rate', kind: 'text', hint: 'e.g. 300Mbps' }, { k: 'queuePkts', name: 'Queue length', kind: 'num', hint: 'packets' },
    { k: 'tcpVariant', name: 'TCP congestion control', kind: 'choice', hint: 'e.g. TcpCubic' }, { k: 'duration', name: 'Measured time', kind: 'num', hint: 'seconds' },
    { k: 'seed', name: 'Random seed', kind: 'num', hint: 'whole number' }],
  OUTPUTS: ['tcp_goodput_bps', 'udp_goodput_bps', 'udp_loss_frac', 'drops_band0', 'drops_band1', 'tcp_retrans', 'link_util'],
  CSS: `
.be { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 26px; align-items: start; }
.be h3 { font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); margin: 20px 0 8px; } .be h3:first-child { margin-top: 0; }
.be label { display: block; font-size: 14px; font-weight: 600; } .be small { display: block; font-size: 12px; font-weight: 400; color: var(--text-muted); margin: 1px 0 5px; }
.be input, .be select, .be textarea { font: inherit; font-size: 14px; font-weight: 400; width: 100%; padding: 6px 9px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-1); color: var(--text-primary); }
.be textarea { resize: vertical; line-height: 1.45; }
.be-row { display: grid; grid-template-columns: 190px 128px minmax(0, 1fr); gap: 10px 14px; align-items: start; padding: 10px 0; border-top: 1px solid var(--border); }
.be-row b { font-size: 14px; } .be-row code { display: block; font-size: 12px; color: var(--text-muted); }
.be-sw { display: inline-flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.be-sw button { font: inherit; font-size: 13px; padding: 5px 12px; border: 0; background: var(--surface-1); color: var(--text-secondary); cursor: pointer; }
.be-sw button + button { border-left: 1px solid var(--border); } .be-sw button.on { background: var(--text-primary); color: var(--surface-1); font-weight: 600; }
.be-sw button:disabled { cursor: default; opacity: .45; }
.be-f { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px 10px; } .be-f .wide { grid-column: 1 / -1; } .be-f small { margin: 0 0 3px; }
.be-two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; }
.be-side { position: sticky; top: 12px; border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
.be-side button.go { font: inherit; font-size: 14.5px; font-weight: 600; width: 100%; padding: 8px 12px; margin-top: 10px; border: 1px solid var(--text-primary); border-radius: 8px; background: var(--text-primary); color: var(--surface-1); cursor: pointer; }
.be-side button.go.plain { background: var(--surface-1); color: var(--text-primary); } .be-side button.go:disabled { opacity: .45; cursor: default; }
.be-msg { margin: 10px 0 0; font-size: 13.5px; padding: 6px 10px; border-left: 3px solid var(--border); } .be-msg ul { margin: 4px 0 0; padding-left: 18px; }
.be-msg.bad { border-color: var(--critical); background: color-mix(in srgb, var(--critical) 8%, transparent); } .be-msg.ok { border-color: var(--good); background: color-mix(in srgb, var(--good) 8%, transparent); }
.be-read { margin: 6px 0 0; font-size: 13px; line-height: 1.5; color: var(--text-secondary); max-height: 190px; overflow: auto; border: 1px dashed var(--border); border-radius: 8px; padding: 8px 10px; }
.be-read mark { background: color-mix(in srgb, var(--series-1) 18%, transparent); color: inherit; padding: 0 2px; border-radius: 3px; } .be-read mark.bad { background: color-mix(in srgb, var(--critical) 22%, transparent); }
@media (max-width: 1000px) { .be { grid-template-columns: 1fr; } .be-side { position: static; } .be-row { grid-template-columns: 1fr; } }`,
  node: null, s: null, ctx: null, template: {}, list: '', typing: null,

  async fetchBrief(id) { try { const r = await fetch(`../briefs/${id}.json?t=${Date.now()}`, { cache: 'no-store' }); return r.ok ? await r.json() : null; } catch (x) { return null; } },

  // ---- a brief file <-> the form's state (every field of the form is a text, as typed)
  fromBrief(b) {
    const B = BRIEF_EDITOR, set = {};
    B.SETTINGS.forEach(({ k }) => {
      const kn = (b.knobs || {})[k], t = B.template[k] || {}, str = v => (v == null ? '' : String(v));
      set[k] = { fixed: !kn, value: str((b.system || {})[k] != null ? b.system[k] : (kn || t).default), min: str((kn || t).min), max: str((kn || t).max),
                 choices: ((kn || t).choices || []).join(', '), def: str((kn || t).default), meaning: str((kn || t).meaning) };
    });
    const g = b.goal || {}, t = g.target || {};
    return { id: '', task: b.task || '', description: b.description || '', set, goal: g.kind === 'given' ? 'given' : 'open', measure: t.measure || 'tcp_goodput_bps', direction: t.direction || 'max',
             conditions: (g.conditions || []).join('\n'), sims: String((b.limits || {}).simulations || ''), per: String((b.limits || {}).simulations_per_experiment || '') };
  },
  toBrief() {
    const B = BRIEF_EDITOR, s = B.s, system = {}, knobs = {};
    const val = (kind, v) => { const t = String(v).trim(); return kind === 'num' && t !== '' && isFinite(Number(t)) ? Number(t) : t; };
    B.SETTINGS.forEach(({ k, kind }) => {
      const f = s.set[k];
      if (f.fixed) { system[k] = val(kind, f.value); if (k === 'mtu') system.udpPacketBytes = 1400; }
      else knobs[k] = kind === 'choice' ? { choices: f.choices.split(',').map(c => c.trim()).filter(Boolean), default: f.def.trim(), meaning: f.meaning.trim() }
        : { min: val(kind, f.min), max: val(kind, f.max), default: val(kind, f.def), meaning: f.meaning.trim() };
    });
    const goal = s.goal === 'open' ? { kind: 'open' } : { kind: 'given', target: { measure: s.measure, direction: s.direction }, conditions: s.conditions.split('\n').map(c => c.trim()).filter(Boolean) };
    return { id: s.id.trim(), task: s.task.trim(), description: s.description.trim(), system, knobs, goal, limits: { simulations: val('num', s.sims), simulations_per_experiment: val('num', s.per) } };
  },
  body() { const b = BRIEF_EDITOR.toBrief(); delete b.id; return JSON.stringify(b); },   // what the form says, without the id
  same() { const B = BRIEF_EDITOR; return !!B.s.baseId && B.body() === B.s.base; },      // the form and the saved brief are the same

  async open(id) {
    const B = BRIEF_EDITOR, b = await B.fetchBrief(id);
    if (!b) { B.s.msg = { bad: true, lines: [`Cannot read briefs/${id}.json.`] }; return B.draw(); }
    const keep = B.s ? B.s.id : '';
    B.s = { ...B.fromBrief(b), id: keep, baseId: id, msg: null, busy: '' };
    B.s.base = B.body();
    B.draw();
  },

  async mount(host, ctx) {
    const B = BRIEF_EDITOR; B.ctx = ctx;
    if (!document.getElementById('be-css')) { const st = document.createElement('style'); st.id = 'be-css'; st.textContent = B.CSS; document.head.appendChild(st); }
    if (!B.node) {
      B.node = document.createElement('div');
      B.node.addEventListener('input', B.onInput); B.node.addEventListener('change', B.onInput); B.node.addEventListener('click', B.onClick);
      B.node.addEventListener('focusin', ev => { B.typing = ev.target; }); B.node.addEventListener('focusout', ev => { if (ev.relatedTarget ? !B.node.contains(ev.relatedTarget) : B.node.isConnected) B.typing = null; });  // kept when the page's redraw took the node out
      host.appendChild(B.node);
      B.node.innerHTML = ctx.sec(3, 'A brief', 'Loading the briefs…', '');
      const first = ((ctx.st || {}).briefs || [])[0];
      const t = await B.fetchBrief('two-hosts-open'); B.template = (t && t.knobs) || {};   // ranges offered when a fixed setting is switched to a knob
      B.s = { baseId: '', msg: null, busy: '', id: '' };
      if (first) await B.open(((ctx.st || {}).briefs || []).includes('two-hosts-open') ? 'two-hosts-open' : first); else B.draw();
      return;
    }
    const had = B.typing && B.node.contains(B.typing) ? [B.typing, B.typing.selectionStart, B.typing.selectionEnd] : null;
    host.appendChild(B.node);   // the same node, with everything typed in it
    if (had) { had[0].focus({ preventScroll: true }); try { had[0].setSelectionRange(had[1], had[2]); } catch (x) { /* a select or a button */ } }
    B.paint();
  },

  draw() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, briefs = (B.ctx.st || {}).briefs || []; B.list = briefs.join('|');
    if (!s || !s.set) { B.node.innerHTML = B.ctx.sec(3, 'A brief', 'No brief could be read from briefs/.', ''); return; }
    const inp = (f, v, hint, cls) => `<input type="text" data-f="${f}" value="${e(v)}" placeholder="${e(hint || '')}" spellcheck="false"${cls ? ` class="${cls}"` : ''}>`;
    const row = ({ k, name, kind, only, hint }) => { const f = s.set[k];
      const fields = f.fixed ? `<div class="be-f"><label><small>value</small>${inp(`set.${k}.value`, f.value, hint)}</label></div>`
        : `<div class="be-f">${kind === 'choice' ? `<label class="wide"><small>choices, separated by commas</small>${inp(`set.${k}.choices`, f.choices, 'TcpCubic, TcpNewReno')}</label>`
            : `<label><small>from</small>${inp(`set.${k}.min`, f.min, hint)}</label><label><small>to</small>${inp(`set.${k}.max`, f.max, hint)}</label>`}
           <label><small>default</small>${inp(`set.${k}.def`, f.def, hint)}</label>
           <label class="wide"><small>meaning, one line the model reads</small>${inp(`set.${k}.meaning`, f.meaning, '')}</label></div>`;
      return `<div class="be-row"><div><b>${e(name)}</b><code>${e(k)}</code></div>
        <div><span class="be-sw"><button data-sw="${k}" data-to="fixed" class="${f.fixed ? 'on' : ''}">Fixed</button><button data-sw="${k}" data-to="knob" class="${f.fixed ? '' : 'on'}"${only ? ' disabled title="The answer format has no field for it, so the model cannot set it"' : ''}>Knob</button></span></div>
        ${fields}</div>`; };
    const pick = (f, v, opts) => `<select data-f="${f}">${opts.map(o => `<option${o === v ? ' selected' : ''}>${e(o)}</option>`).join('')}</select>`;
    const form = `
      <h3>What the model is told</h3>
      <label>Task<small>the question, as the model reads it</small><textarea data-f="task" rows="3">${e(s.task)}</textarea></label>
      <label style="margin-top:12px">Description of the system<small>plain words, written by you. {name} is replaced by the fixed setting of that name, e.g. {linkRate}; a knob cannot be used that way</small><textarea data-f="description" rows="7">${e(s.description)}</textarea></label>
      <h3>Settings</h3>
      <p class="th-sm" style="margin:0 0 8px">Fixed: one value, the model cannot change it. Knob: the model may set it within the range (or among the choices). The UDP packet size is 1400 bytes in the scenario and is always stated as fixed.</p>
      ${B.SETTINGS.map(row).join('')}
      <h3>Goal</h3>
      <div class="be-two"><label>Kind<small>open: the model must state and justify its own goal</small><select data-f="goal"><option value="open"${s.goal === 'open' ? ' selected' : ''}>open</option><option value="given"${s.goal === 'given' ? ' selected' : ''}>given: a target and conditions</option></select></label>
        ${s.goal === 'given' ? `<div class="be-two"><label>Target measure<small>one of the outputs</small>${pick('measure', s.measure, B.OUTPUTS)}</label><label>Direction<small>as large or as small as possible</small>${pick('direction', s.direction, ['max', 'min'])}</label></div>
        <label style="grid-column:1/-1">Conditions<small>one per line, e.g. udp_loss_frac &lt;= 0.01; all must hold</small><textarea data-f="conditions" rows="2" spellcheck="false">${e(s.conditions)}</textarea></label>` : ''}</div>
      <h3>Limits</h3>
      <div class="be-two"><label>Simulations<small>the session's budget at the start</small>${inp('sims', s.sims, 'e.g. 40')}</label><label>Simulations per experiment<small>not used until an experiment can hold several simulations</small>${inp('per', s.per, 'e.g. 12')}</label></div>`;
    const side = `<div class="be-side">
      <label>Open a brief<small>its content fills the form</small><select id="be-open">${briefs.map(b => `<option${b === s.baseId ? ' selected' : ''}>${e(b)}</option>`).join('')}</select></label>
      <label style="margin-top:12px">New id<small>the file will be briefs/&lt;id&gt;.json · lower-case letters, digits, - and _</small>${inp('id', s.id, 'e.g. two-hosts-short-queue')}</label>
      <button class="go" id="be-save">Save as new brief</button>
      <button class="go plain" id="be-start">Start session with this brief</button>
      <div id="be-state" class="th-sm" style="margin-top:8px"></div><div id="be-msg"></div>
      <h3 style="margin-top:16px">The description as the model will read it</h3><div class="be-read" id="be-read"></div></div>`;
    B.node.innerHTML = B.ctx.sec(3, 'A brief', 'The assignment a session works on: what the model is told, which settings are fixed and which it may change, the goal and the limits. Open an existing brief, change it, and save it under a new id; a saved brief is never overwritten.',
      `<div class="be"><div>${form}</div>${side}</div>`);
    B.paint();
  },

  // everything that follows the typed values, updated in place (the fields themselves are not touched)
  paint() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, st = B.ctx.st || {}, $ = id => B.node.querySelector('#' + id);
    if (!s || !s.set || !$('be-save')) return;
    const briefs = st.briefs || [];
    if (briefs.join('|') !== B.list && document.activeElement !== $('be-open')) { B.list = briefs.join('|'); $('be-open').innerHTML = briefs.map(b => `<option${b === s.baseId ? ' selected' : ''}>${e(b)}</option>`).join(''); }
    const same = B.same(), id = s.id.trim(), taken = briefs.includes(id), running = !!((st.session && st.session.running) || st.other_loop);
    $('be-save').disabled = !!s.busy || !id || taken; $('be-save').textContent = s.busy === 'save' ? 'Saving…' : 'Save as new brief';
    $('be-start').disabled = !!s.busy || !same || running; $('be-start').textContent = s.busy === 'start' ? 'Starting…' : same ? `Start session with ${s.baseId}` : 'Start session with this brief';
    $('be-state').textContent = taken ? `A brief named ${id} already exists; choose another id.`
      : !same ? `The form differs from ${s.baseId || 'every saved brief'}: save it under a new id, then a session can start with it.`
      : running ? `The form is the saved brief ${s.baseId}. A session is running, so another cannot start.`
      : `The form is the saved brief ${s.baseId}. A session started here uses the draft, scheduling policy and baseline chosen in section 2, and this brief's limit of simulations.`;
    $('be-msg').innerHTML = s.msg ? `<div class="be-msg ${s.msg.bad ? 'bad' : 'ok'}">${s.msg.lines.length > 1 ? `${e(s.msg.lines[0])}<ul>${s.msg.lines.slice(1).map(l => `<li>${e(l)}</li>`).join('')}</ul>` : e(s.msg.lines[0])}</div>` : '';
    const fixed = Object.fromEntries(B.SETTINGS.filter(({ k }) => s.set[k].fixed).map(({ k }) => [k, s.set[k].value.trim()])); fixed.udpPacketBytes = '1400';
    $('be-read').innerHTML = e(s.description).replace(/\{(\w+)\}/g, (m, k) => (k in fixed ? `<mark>${e(fixed[k])}</mark>` : `<mark class="bad" title="not a fixed setting of this brief">${m}</mark>`)) || '<span class="th-muted">empty</span>';
  },

  onInput(ev) {
    const B = BRIEF_EDITOR, t = ev.target, f = t.dataset && t.dataset.f;
    if (t.id === 'be-open') { if (ev.type === 'change') B.open(t.value); return; }
    if (!f) return;
    const path = f.split('.'); let o = B.s; path.slice(0, -1).forEach(p => { o = o[p]; }); o[path[path.length - 1]] = t.value;
    if (f === 'goal' && ev.type === 'change') return B.draw();   // the target and the conditions appear or go
    B.paint();
  },
  async onClick(ev) {
    const B = BRIEF_EDITOR, t = ev.target.closest('button'); if (!t || t.disabled) return;
    if (t.dataset.sw) { const f = B.s.set[t.dataset.sw]; f.fixed = t.dataset.to === 'fixed'; if (f.fixed && !f.value.trim()) f.value = f.def; if (!f.fixed && !f.def.trim()) f.def = f.value; return B.draw(); }
    if (t.id === 'be-save') {
      const b = B.toBrief(); B.s.busy = 'save'; B.s.msg = null; B.paint();
      try { const r = await B.ctx.post('../api/brief', { brief: b }); B.s.baseId = r.saved; B.s.base = B.body(); B.s.id = ''; B.s.msg = { lines: [`Saved as ${r.file}.`] }; B.s.busy = ''; await B.ctx.after(); return B.draw(); }
      catch (x) { const parts = String(x.message).replace(/^brief [^:]*: /, '').split('; '); B.s.msg = { bad: true, lines: parts.length > 1 ? ['Not saved. The brief cannot be used as it is:', ...parts] : ['Not saved: ' + parts[0]] }; }
      B.s.busy = ''; return B.paint();
    }
    if (t.id === 'be-start') {
      B.s.busy = 'start'; B.s.msg = null; B.paint();
      try { const r = await B.ctx.post('../api/session', { brief: B.s.baseId, ...B.ctx.session() }); B.s.msg = { lines: [`Session ${r.id} started with brief ${B.s.baseId}.`] }; }
      catch (x) { B.s.msg = { bad: true, lines: ['Not started: ' + x.message] }; }
      B.s.busy = ''; await B.ctx.after(); B.paint();
    }
  },
};
