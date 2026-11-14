// BRIEF_EDITOR as the older control page (index_full.html) uses it: the operator's form for writing a brief
// (briefs/<id>.json). The evidence page's set-up page, "New session", has its own: brief_editor.js.
// A brief is opened from the existing ones, changed, and saved under a NEW id through POST /api/brief; control.py
// checks it the way loop.py does (tools.check_brief) and never overwrites a file. "Start session with this brief"
// starts a session on the brief the form shows, once the form and a saved brief are the same.
// The settings are read and set on the picture of the system (viewer/evidence_system.js, where the page has it): a click
// on a part opens its settings, each with a switch "fixed / the model may change it", a value or a range, and a default;
// the same rows for every setting stay reachable as "all settings as a list". A numeric knob may have a step (the
// model's values are rounded to it), a given goal a tolerance in per cent (two results closer than this count as
// equal). "Variations" fill the form with a ready-made change of the opened brief, to save under a new id.
// The form lives in one node that is kept when the page around it is redrawn, so nothing typed is lost.
//   BRIEF_EDITOR.mount(host, ctx)   ctx = { st: control.py's status, post(path, body), e: escape, sec: section frame,
//                                           session(): the other choices of a session, after(): reload the page's data }
// ======================================================================================================
const BRIEF_EDITOR = {
  // every setting of the program, in the order shown; every one can be fixed or opened to the model (the answer format is built from the brief).
  // step: a numeric knob may have one; open: the range and meaning offered when a setting no brief has opened yet is switched to a knob
  // as: a setting a brief may leave out ("not set"); it then has the value of the setting named here, and the program is started without it
  SETTINGS: [
    { k: 'linkRate', name: 'Link rate', kind: 'text', hint: 'e.g. 1Gbps', open: { min: '100Mbps', max: '10Gbps', meaning: "rate of the link, e.g. '500Mbps'" } },
    { k: 'linkDelay', name: 'Link delay, one way', kind: 'text', hint: 'e.g. 50us', open: { min: '10us', max: '10ms', meaning: "one-way delay of the link, e.g. '200us'" } },
    { k: 'mtu', name: 'Largest packet', kind: 'num', hint: 'bytes', step: true, open: { min: '1428', max: '1500', meaning: 'largest packet the link carries, in bytes' } }, { k: 'weightUdp', name: 'UDP share of the link', kind: 'num', hint: '0.05 to 0.95', step: true },
    { k: 'udpRate', name: 'UDP offered rate', kind: 'text', hint: 'e.g. 300Mbps' }, { k: 'queuePkts', name: 'Queue length', kind: 'num', hint: 'packets', step: true },
    { k: 'queuePktsUdp', name: 'UDP queue length', kind: 'num', hint: 'packets', step: true, as: 'queuePkts', open: { min: '4', max: '1000', meaning: 'most packets the UDP queue holds' } },
    { k: 'queuePktsTcp', name: 'TCP queue length', kind: 'num', hint: 'packets', step: true, as: 'queuePkts', open: { min: '4', max: '1000', meaning: 'most packets the TCP queue holds' } },
    { k: 'tcpVariant', name: 'TCP congestion control', kind: 'choice', hint: 'e.g. TcpCubic' }, { k: 'duration', name: 'Measured time', kind: 'num', hint: 'seconds', step: true },
    { k: 'seed', name: 'Random seed', kind: 'num', hint: 'whole number', step: true }],
  // ready-made variations of the opened brief: [key, name, the id's ending, what it changes, when it cannot be used]
  VARIATIONS: [
    ['noloss', 'no loss allowed', 'no-loss', 'the condition on UDP loss becomes udp_loss_frac <= 0', s => (s.goal !== 'given' ? "this brief's goal is open: it has no condition to tighten" : '')],
    ['coarse', 'coarse ratio (steps of 0.01)', 'coarse-ratio', 'the UDP share of the link gets a step of 0.01', s => (s.set.weightUdp.fixed ? 'this brief fixes the UDP share of the link' : '')],
    ['small', 'small budget (15 simulations)', 'budget-15', 'the session may run 15 simulations', () => '']],
  OUTPUTS: ['tcp_goodput_bps', 'udp_goodput_bps', 'udp_loss_frac', 'drops_band0', 'drops_band1', 'tcp_retrans', 'link_util'],
  CSS: `
.be { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 26px; align-items: start; }
.be h3 { font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); margin: 20px 0 8px; } .be h3:first-child { margin-top: 0; }
.be label { display: block; font-size: 14px; font-weight: 600; } .be small { display: block; font-size: 12px; font-weight: 400; color: var(--text-muted); margin: 1px 0 5px; }
.be input, .be select, .be textarea { font: inherit; font-size: 14px; font-weight: 400; width: 100%; padding: 6px 9px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-1); color: var(--text-primary); }
.be textarea { resize: vertical; line-height: 1.45; }
.be-row { display: grid; grid-template-columns: 170px 236px minmax(0, 1fr); gap: 10px 14px; align-items: start; padding: 10px 0; border-top: 1px solid var(--border); }
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
.be-pic { border: 1px solid var(--border); border-radius: 10px; padding: 8px 10px 4px; margin: 6px 0 4px; } .be-pic svg g[data-act] { cursor: pointer; } .be-pic .key { display: flex; gap: 4px 18px; flex-wrap: wrap; font-size: 12.5px; color: var(--text-secondary); margin: 2px 0 6px; }
.be-pic .key i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; background: var(--c); } .be-var { display: grid; gap: 6px; margin-top: 6px; } .be-var button { font: inherit; font-size: 13px; text-align: left; padding: 6px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-1); color: var(--text-primary); cursor: pointer; }
.be-var button:disabled { opacity: .45; cursor: default; } .be-var button small { margin: 1px 0 0; }
@media (max-width: 1000px) { .be { grid-template-columns: 1fr; } .be-side { position: static; } .be-row { grid-template-columns: 1fr; } }`,
  node: null, s: null, ctx: null, template: {}, list: '', typing: null,

  async fetchBrief(id) { try { const r = await fetch(`../briefs/${id}.json?t=${Date.now()}`, { cache: 'no-store' }); return r.ok ? await r.json() : null; } catch (x) { return null; } },

  // ---- a brief file <-> the form's state (every field of the form is a text, as typed)
  fromBrief(b) {
    const B = BRIEF_EDITOR, set = {};
    B.SETTINGS.forEach(({ k, as }) => {
      const kn = (b.knobs || {})[k], t = B.template[k] || {}, str = v => (v == null ? '' : String(v));
      set[k] = { off: !!as && !kn && (b.system || {})[k] == null, fixed: !kn, value: str((b.system || {})[k] != null ? b.system[k] : (kn || t).default), min: str((kn || t).min), max: str((kn || t).max),
                 choices: ((kn || t).choices || []).join(', '), def: str((kn || t).default), meaning: str((kn || t).meaning), step: str((kn || {}).step) };
    });
    const g = b.goal || {}, t = g.target || {};
    return { id: '', task: b.task || '', description: b.description || '', set, goal: g.kind === 'given' ? 'given' : 'open', measure: t.measure || 'tcp_goodput_bps', direction: t.direction || 'max', tolerance: g.tolerance == null ? '' : String(g.tolerance),
             conditions: (g.conditions || []).join('\n'), sims: String((b.limits || {}).simulations || ''), per: String((b.limits || {}).simulations_per_experiment || '') };
  },
  toBrief() {
    const B = BRIEF_EDITOR, s = B.s, system = {}, knobs = {};
    const val = (kind, v) => { const t = String(v).trim(); return kind === 'num' && t !== '' && isFinite(Number(t)) ? Number(t) : t; };
    B.SETTINGS.forEach(({ k, kind, step }) => {
      const f = s.set[k];
      if (f.off) return;
      if (f.fixed) system[k] = val(kind, f.value);
      else knobs[k] = kind === 'choice' ? { choices: f.choices.split(',').map(c => c.trim()).filter(Boolean), default: f.def.trim(), meaning: f.meaning.trim() }
        : { min: val(kind, f.min), max: val(kind, f.max), default: val(kind, f.def), ...(step && String(f.step || '').trim() ? { step: val('num', f.step) } : {}), meaning: f.meaning.trim() };
    });
    system.udpPacketBytes = 1400;  // set by the scenario; a brief can only state it
    const goal = s.goal === 'open' ? { kind: 'open' } : { kind: 'given', target: { measure: s.measure, direction: s.direction }, conditions: s.conditions.split('\n').map(c => c.trim()).filter(Boolean), ...(String(s.tolerance || '').trim() ? { tolerance: val('num', s.tolerance) } : {}) };
    return { id: s.id.trim(), task: s.task.trim(), description: s.description.trim(), system, knobs, goal, limits: { simulations: val('num', s.sims), simulations_per_experiment: val('num', s.per) } };
  },
  body() { const b = BRIEF_EDITOR.toBrief(); delete b.id; return JSON.stringify(b); },   // what the form says, without the id
  same() { const B = BRIEF_EDITOR; return !!B.s.baseId && B.body() === B.s.base; },      // the form and the saved brief are the same

  async open(id) {
    const B = BRIEF_EDITOR, b = await B.fetchBrief(id);
    if (!b) { B.s.msg = { bad: true, lines: [`Cannot read briefs/${id}.json.`] }; return B.draw(); }
    const keep = B.s ? B.s.id : '', view = B.s ? [B.s.mode, B.s.obj] : [];
    B.s = { ...B.fromBrief(b), id: keep, baseId: id, msg: null, busy: '', mode: view[0], obj: view[1] };
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
    if (!had && B.s && B.s.set && B.picture() && !B.node.querySelector('svg.sy')) return B.draw();  // the list of ns-3 objects has arrived: the picture can be drawn
    B.paint();
  },

  // the picture of the system as the form: possible where the page has it (evidence_system.js) and its objects are read
  picture() { if (typeof EV === 'undefined' || !EV.sysSvg) return false; if (EV.OB === undefined) EV.sysLoad(); return !!EV.OB; },
  // the settings a part of the picture holds: those its rows of objects.json name
  partSettings(id) { const B = BRIEF_EDITOR, f = EV.sysFind(id), keys = f ? [...new Set(f.o.rows.flatMap(([, text]) => [...String(text).matchAll(/\{(\w+)\}/g)].flatMap(m => { const k = EV.sysKey(m[1]); return EV.SYS_OWN[k] ? [EV.SYS_OWN[k], k] : [k]; })))] : []; return B.SETTINGS.filter(q => keys.includes(q.k)); },
  draw() {
    const B = BRIEF_EDITOR, s = B.s, e = B.ctx.e, briefs = (B.ctx.st || {}).briefs || []; B.list = briefs.join('|');
    if (!s || !s.set) { B.node.innerHTML = B.ctx.sec(3, 'A brief', 'No brief could be read from briefs/.', ''); return; }
    const inp = (f, v, hint, cls) => `<input type="text" data-f="${f}" value="${e(v)}" placeholder="${e(hint || '')}" spellcheck="false"${cls ? ` class="${cls}"` : ''}>`;
    const row = ({ k, name, kind, hint, step, as }) => { const f = s.set[k], common = as ? B.SETTINGS.find(q => q.k === as) : null;
      const fields = f.off ? `<div class="be-f"><small class="wide" data-off="${k}">Not set: it is as long as “${e(common.name)}” (${e(as)}) says. The brief does not name it, and the simulations are started as before this setting existed.</small></div>` : f.fixed ? `<div class="be-f"><label><small>value</small>${inp(`set.${k}.value`, f.value, hint)}</label></div>`
        : `<div class="be-f">${kind === 'choice' ? `<label class="wide"><small>choices, separated by commas</small>${inp(`set.${k}.choices`, f.choices, 'TcpCubic, TcpNewReno')}</label>`
            : `<label><small>from</small>${inp(`set.${k}.min`, f.min, hint)}</label><label><small>to</small>${inp(`set.${k}.max`, f.max, hint)}</label>`}
           <label><small>default</small>${inp(`set.${k}.def`, f.def, hint)}</label>${step ? `<label title="The model's values are rounded to it, counted from “from”; the rounding is recorded. Empty: no step."><small>step (optional)</small>${inp(`set.${k}.step`, f.step || '', 'none')}</label>` : ''}
           <label class="wide"><small>meaning, one line the model reads</small>${inp(`set.${k}.meaning`, f.meaning, '')}</label>${step ? '<small class="wide">A step: the model\'s values are rounded to it, and the rounding is recorded as a clamp.</small>' : ''}</div>`;
      return `<div class="be-row" data-row="${k}"><div><b>${e(name)}</b><code>${e(k)}</code></div>
        <div><span class="be-sw">${as ? `<button data-sw="${k}" data-to="off" class="${f.off ? 'on' : ''}">not set</button>` : ''}<button data-sw="${k}" data-to="fixed" class="${!f.off && f.fixed ? 'on' : ''}">fixed</button><button data-sw="${k}" data-to="knob" class="${f.off || f.fixed ? '' : 'on'}">the model may change it</button></span></div>
        ${fields}</div>`; };
    // the settings: on the picture (a click on a part opens its settings), or all of them as a list
    const pic = B.picture(), mode = pic && s.mode !== 'list' ? 'picture' : 'list', num = (kind, t) => (kind === 'num' && String(t).trim() !== '' && isFinite(Number(t)) ? Number(t) : String(t).trim());
    let settings = B.SETTINGS.map(row).join('');
    if (mode === 'picture') {
      const key = n => EV.sysOwn(n, k => !!s.set[k] && !s.set[k].off), v = EV.sysDerive(Object.fromEntries(B.SETTINGS.filter(({ k }) => !s.set[k].off).map(({ k, kind }) => [k, num(kind, s.set[k].fixed ? s.set[k].value : s.set[k].def)]))), on = EV.sysFind(s.obj) ? s.obj : EV.sysId('sender', 'tc', 'Scheduler') || 'link';
      const f = EV.sysFind(on), mine = B.partSettings(on), around = (EV.OB.around || []).map((o, i) => `<a data-act="beobj" data-id="around-${i}" style="cursor:pointer;text-decoration:underline${on === 'around-' + i ? ';font-weight:700' : ''}">${e(o.name.toLowerCase())}</a>`).join(', ');
      const reach = new Set(['link', ...(EV.OB.around || []).map((o, i) => 'around-' + i), ...EV.OB.hosts.flatMap(h => EV.OB.layers.flatMap(l => (h[l.key] || []).map((o, i) => `${h.key}-${l.key}-${i}`)))].flatMap(id => B.partSettings(id).map(q => q.k))), off = B.SETTINGS.filter(q => !reach.has(q.k));
      settings = `<div class="be-pic" id="be-pic"><div style="overflow:auto">${EV.sysSvg({ v, knob: n => !s.set[key(n)] ? false : !s.set[key(n)].fixed, fixed: n => !!s.set[key(n)] && s.set[key(n)].fixed, on, act: 'beobj' })}</div>
          <div class="key"><span style="--c:var(--by-model)"><i></i>the model may change it</span><span style="--c:var(--by-operator)"><i></i>fixed by the operator</span>${around ? `<span>outside a packet's path: ${around}</span>` : ''}</div></div>
        <p class="th-sm" style="margin:8px 0 2px"><b>${e(f.o.name)}</b> · ${mine.length ? `its setting${mine.length === 1 ? '' : 's'}:` : 'this part has no setting a brief can set.'}</p>${mine.map(row).join('')}
        ${off.length ? `<p class="th-sm" style="margin:10px 0 2px">Not on the picture:</p>${off.map(row).join('')}` : ''}`;
    }
    const pick = (f, v, opts) => `<select data-f="${f}">${opts.map(o => `<option${o === v ? ' selected' : ''}>${e(o)}</option>`).join('')}</select>`;
    const form = `
      <h3>What the model is told</h3>
      <label>Task<small>the question, as the model reads it</small><textarea data-f="task" rows="3">${e(s.task)}</textarea></label>
      <label style="margin-top:12px">Description of the system<small>plain words, written by you. {name} is replaced by the fixed setting of that name, e.g. {linkRate}; a knob cannot be used that way</small><textarea data-f="description" rows="7">${e(s.description)}</textarea></label>
      <h3>Settings</h3>
      <p class="th-sm" style="margin:0 0 8px">Fixed: one value, the model cannot change it. The model may change it: within the range (or among the choices), starting from the default. Each queue's own length may also be left “not set”: the queue is then as long as the common queue length. The UDP packet size is 1400 bytes in the scenario and is always stated as fixed.</p>
      ${pic ? `<span class="be-sw" id="be-mode"><button data-mode="picture" class="${mode === 'picture' ? 'on' : ''}">on the picture</button><button data-mode="list" class="${mode === 'list' ? 'on' : ''}">all settings as a list</button></span>${mode === 'picture' ? ' <span class="th-sm">click a part to open its settings</span>' : ''}` : ''}
      ${settings}
      <h3>Goal</h3>
      <div class="be-two"><label>Kind<small>open: the model must state and justify its own goal</small><select data-f="goal"><option value="open"${s.goal === 'open' ? ' selected' : ''}>open</option><option value="given"${s.goal === 'given' ? ' selected' : ''}>given: a target and conditions</option></select></label>
        ${s.goal === 'given' ? `<div class="be-two"><label>Target measure<small>one of the outputs</small>${pick('measure', s.measure, B.OUTPUTS)}</label><label>Direction<small>as large or as small as possible</small>${pick('direction', s.direction, ['max', 'min'])}</label></div>
        <label style="grid-column:1/-1">Conditions<small>one per line, e.g. udp_loss_frac &lt;= 0.01; all must hold</small><textarea data-f="conditions" rows="2" spellcheck="false">${e(s.conditions)}</textarea></label>
        <label>Tolerance, per cent (optional)<small>two results closer than this count as equal: the model is told, and the score says "at the best, within the tolerance"</small>${inp('tolerance', s.tolerance || '', 'none, e.g. 1')}</label>` : ''}</div>
      <h3>Limits</h3>
      <div class="be-two"><label>Simulations<small>the session's budget at the start</small>${inp('sims', s.sims, 'e.g. 40')}</label><label>Simulations per experiment<small>not used until an experiment can hold several simulations</small>${inp('per', s.per, 'e.g. 12')}</label></div>`;
    const side = `<div class="be-side">
      <label>Open a brief<small>its content fills the form</small><select id="be-open">${briefs.map(b => `<option${b === s.baseId ? ' selected' : ''}>${e(b)}</option>`).join('')}</select></label>
      <label style="margin-top:12px">New id<small>the file will be briefs/&lt;id&gt;.json · lower-case letters, digits, - and _</small>${inp('id', s.id, 'e.g. two-hosts-short-queue')}</label>
      <button class="go" id="be-save">Save as new brief</button>
      <button class="go plain" id="be-start">Start session with this brief</button>
      <div id="be-state" class="th-sm" style="margin-top:8px"></div><div id="be-msg"></div>
      <h3 style="margin-top:16px">Variations of ${e(s.baseId || 'this brief')}</h3><small>each fills the form with one change and proposes a new id; then save it</small>
      <div class="be-var" id="be-var">${B.VARIATIONS.map(([k, name, , what, no]) => `<button data-var="${k}"${no(s) ? ` disabled title="${e(no(s))}"` : ''}>${e(name)}<small>${e(no(s) || what)}</small></button>`).join('')}</div>
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
    const fixed = Object.fromEntries(B.SETTINGS.filter(({ k }) => s.set[k].fixed && !s.set[k].off).map(({ k }) => [k, s.set[k].value.trim()])); fixed.udpPacketBytes = '1400';
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
    const B = BRIEF_EDITOR, part = ev.target.closest('[data-act=beobj]'); if (part) { B.s.obj = part.dataset.id; return B.draw(); }  // a part of the picture: its settings open under it
    const t = ev.target.closest('button'); if (!t || t.disabled) return;
    if (t.dataset.mode) { B.s.mode = t.dataset.mode; return B.draw(); }
    if (t.dataset.var) {  // a ready-made variation: one change in the form, and a new id proposed
      const s = B.s, v = B.VARIATIONS.find(q => q[0] === t.dataset.var), briefs = (B.ctx.st || {}).briefs || [];
      if (v[0] === 'noloss') { const cs = s.conditions.split('\n').map(c => c.trim()).filter(c => c && !/^udp_loss_frac\b/.test(c)); s.conditions = [...cs, 'udp_loss_frac <= 0'].join('\n'); }
      if (v[0] === 'coarse') s.set.weightUdp.step = '0.01';
      if (v[0] === 'small') { s.sims = '15'; if (Number(s.per) > 15) s.per = '15'; }
      let id = `${s.baseId}-${v[2]}`.slice(0, 56), n = 1; while (briefs.includes(id)) id = `${s.baseId}-${v[2]}`.slice(0, 54) + '-' + (++n); s.id = id;
      s.msg = { lines: [`Variation “${v[1]}”: ${v[3]}. Save it as ${id}, or change the id first.`] }; return B.draw(); }
    if (t.dataset.sw) { const f = B.s.set[t.dataset.sw], q = B.SETTINGS.find(x => x.k === t.dataset.sw); f.off = t.dataset.to === 'off'; if (f.off) return B.draw();
      if (q.as && !f.value.trim() && !f.def.trim()) { const c = B.s.set[q.as]; f.value = f.def = (c.fixed ? c.value : c.def); }
      f.fixed = t.dataset.to === 'fixed'; if (f.fixed && !f.value.trim()) f.value = f.def; if (!f.fixed && !f.def.trim()) f.def = f.value;
      if (!f.fixed && q.open) { if (!f.min.trim()) f.min = q.open.min; if (!f.max.trim()) f.max = q.open.max; if (!f.meaning.trim()) f.meaning = q.open.meaning; }  // a setting no brief has opened yet: a range to start from
      return B.draw(); }
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
