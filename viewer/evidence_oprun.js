// On the Operator tab: "Run one simulation" (an operator run with chosen settings, shown in the standard result panel,
// stored by control.py in checks/op-<time>/ and listed in checks/control.jsonl) and "Run a sweep" (a grid of knob values,
// progress, Stop; its table goes to checks/sweeps/<id>/). Neither ever reaches a session's folder.
// ======================================================================================================
Object.assign(EV, {
  or: { vals: {}, policy: 'share', busy: false, msg: '', runs: null, open: null },  // the run form; runs: checks/control.jsonl
  sw: { grid: {}, policy: 'share', busy: false, msg: '', st: null, timer: null },    // the sweep form; st: the sweep's status

  runCard() {
    const M = EV.M, o = EV.or, e = EV.e, b = M.brief; if (!b) return `<div class="ev-card"><h2>Run one simulation</h2><p class="sm">The knobs come from the session's brief: ${EV.nr}.</p></div>`;
    const knobs = Object.entries(b.knobs || {}), runs = (o.runs || []).filter(r => r.brief === b.id), cur = runs.find(r => r.id === o.open) || null;
    const inp = ([k, d]) => (d.choices ? `<select data-ch="or" data-k="${e(k)}">${d.choices.map(c => `<option${(o.vals[k] ?? d.default) === c ? ' selected' : ''}>${e(c)}</option>`).join('')}</select>`
      : `<input type="text" data-ch="or" data-k="${e(k)}" value="${e(o.vals[k] ?? '')}" placeholder="${e(d.default)}">`);
    const defaults = { id: 'defaults', label: 'the brief\'s defaults', params: Object.fromEntries(knobs.map(([k, d]) => [k, d.default])) };
    return `<div class="ev-card" id="op-run"><h2>Run one simulation <small>an ${EV.term('Operator', 'operator')} run with chosen settings · stored under checks/, never in a session</small></h2>
      <div class="kv">${knobs.map(q => `<div><span>${e(TH_DATA.KNOB[q[0]] || q[0])} (${e(q[0])})${q[1].choices ? '' : ` · ${e(q[1].min)} to ${e(q[1].max)}`}</span>${inp(q)}</div>`).join('')}
        <div><span>${EV.term('Scheduling policy', 'scheduling policy')}</span><select data-ch="or" data-k="_policy"><option${o.policy === 'share' ? ' selected' : ''}>share</option><option${o.policy === 'cap' ? ' selected' : ''}>cap</option></select></div></div>
      <p style="margin-top:8px"><button data-act="oprun"${o.busy ? ' disabled' : ''}>${o.busy ? 'Running… (about 20 s)' : 'Run'}</button> <span class="sm">a field left empty keeps the brief's default</span>${o.msg ? ` <span class="bad">${e(o.msg)}</span>` : ''}
        ${runs.length ? ` · <label style="font-weight:400">operator runs so far <select data-ch="oropen"><option value="">none opened</option>${runs.slice().reverse().map(r => `<option value="${e(r.id)}"${r.id === o.open ? ' selected' : ''}>${e(`${r.id} · ${r.policy} · ${Object.entries(r.params).filter(([k]) => k in (b.knobs || {})).map(([k, v]) => k + ' ' + v).join(', ')}`)}</option>`).join('')}</select></label>` : ''}</p>
      ${cur ? `<h3>${EV_ICON.simulation} Operator run ${e(cur.id)} · scheduling policy ${e(cur.policy)} · ${e(cur.seconds)} s${Object.keys(cur.clamped || {}).length ? ` · brought into range: ${e(JSON.stringify(cur.clamped))}` : ''}</h3>
        ${EV.resultPanel(EV.opSim(cur), defaults, { ctlHead: 'the brief\'s defaults', ctlName: 'brief\'s default' })}` : ''}</div>`;
  },
  opSim: r => ({ id: r.id, label: 'operator run', run: r.id, src: `../checks/${r.id}/series.csv`, params: r.params, metrics: r.metrics, ts: r.ts }),

  sweepCard() {
    const M = EV.M, w = EV.sw, e = EV.e, b = M.brief; if (!b) return '';
    const knobs = Object.entries(b.knobs || {}), vals = k => String(w.grid[k] || '').split(',').map(v => v.trim()).filter(Boolean), any = knobs.some(([k]) => vals(k).length), n = knobs.reduce((a, [k]) => a * (vals(k).length || 1), 1);
    const st = w.st, live = st && st.state === 'running';
    return `<div class="ev-card" id="op-sweep"><h2>Run a sweep <small>a grid of knob values; every combination is one simulation · its table is stored under checks/sweeps/</small></h2>
      <div class="kv">${knobs.map(([k, d]) => `<div><span>${e(k)}: values, separated by commas</span><input type="text" data-ch="sw" data-k="${e(k)}" value="${e(w.grid[k] || '')}" placeholder="${e(d.choices ? d.choices.slice(0, 2).join(', ') : `${d.min}, ${d.default}, ${d.max}`)}"></div>`).join('')}
        <div><span>${EV.term('Scheduling policy', 'scheduling policy')}</span><select data-ch="sw" data-k="_policy"><option${w.policy === 'share' ? ' selected' : ''}>share</option><option${w.policy === 'cap' ? ' selected' : ''}>cap</option></select></div></div>
      <p class="sm" style="margin-top:6px">A knob left empty keeps the brief's default. <span id="sw-n">${any ? `<b>${n.toLocaleString('en-US')} combination${n === 1 ? '' : 's'}</b>.` : 'No value entered yet.'}</span></p>
      <p><button id="sw-go" data-act="swstart"${!any || live || w.busy ? ' disabled' : ''}>Start the sweep</button>${live ? ' <button data-act="swstop">Stop</button>' : ''}${w.msg ? ` <span class="bad">${e(w.msg)}</span>` : ''}</p>
      ${st ? `<p><span class="prog" style="width:260px"><i style="width:${st.total ? 100 * st.done / st.total : 0}%"></i></span> sweep ${e(st.id)}: <b>${st.done} of ${st.total}</b> done${st.failed ? ` · ${st.failed} failed` : ''} · ${e(st.state)}${live ? '' : ` · table: checks/sweeps/${e(st.id)}/table.csv`}</p>` : ''}</div>`;
  },
  watchSweep() {  // follow a running sweep; the timer ends with it
    const w = EV.sw; if (w.timer || !w.st || w.st.state !== 'running') return;
    w.timer = setInterval(async () => { const st = await EV.json(`../api/sweep/${w.st.id}`); if (st) w.st = st;
      if (!st || st.state !== 'running') { clearInterval(w.timer); w.timer = null; }
      const a = document.activeElement; if (EV.s.view === 'operator' && !(a && ['INPUT', 'TEXTAREA'].includes(a.tagName) && a.type !== 'checkbox')) EV.draw(); }, 2000);
  },
  // after the Operator tab is drawn: the list of operator runs, a sweep that is running, the charts of the opened run
  async afterRun() {
    const o = EV.or, w = EV.sw, T = TASK_VIEW; Object.values(T._charts).forEach(c => { try { c.destroy(); } catch (q) {} }); T._charts = {};
    if (o.runs == null) { o.runs = []; o.runs = EV_DATA.lines(await EV.get('../checks/control.jsonl')); if (o.runs.length) return EV.draw(); }
    if (!w.st && !w.asked && (EV.st.sweeps || []).length) { w.asked = true; const st = await EV.json(`../api/sweep/${EV.st.sweeps[EV.st.sweeps.length - 1]}`); if (st && st.state === 'running') { w.st = st; return EV.draw(); } }
    EV.watchSweep();
    const cur = (o.runs || []).find(r => r.id === o.open); if (cur && await EV.timeCharts(EV.opSim(cur))) EV.draw();
  },
});
EV.chg = Object.assign(EV.chg || {}, {
  or(t) { if (t.dataset.k === '_policy') EV.or.policy = t.value; else EV.or.vals[t.dataset.k] = t.value; },
  oropen(t) { EV.or.open = t.value || null; EV.draw(); },
  sw(t) { if (t.dataset.k === '_policy') EV.sw.policy = t.value; },
});
// typing in the sweep's grid: the number of combinations and the Start button follow in place (the page is not drawn again, so the field keeps the cursor)
EV.inp = Object.assign(EV.inp || {}, {
  sw(t) { const w = EV.sw, ks = Object.keys((EV.M.brief || {}).knobs || {}); if (t.dataset.k === '_policy') return; w.grid[t.dataset.k] = t.value;
    const vals = k => String(w.grid[k] || '').split(',').map(v => v.trim()).filter(Boolean), any = ks.some(k => vals(k).length), n = ks.reduce((a, k) => a * (vals(k).length || 1), 1), el = document.getElementById('sw-n'), go = document.getElementById('sw-go');
    if (el) el.innerHTML = any ? `<b>${n.toLocaleString('en-US')} combination${n === 1 ? '' : 's'}</b>.` : 'No value entered yet.'; if (go) go.disabled = !any || w.busy || (w.st && w.st.state === 'running'); },
});
EV.act = Object.assign(EV.act || {}, {
  async oprun() {
    const o = EV.or, b = EV.M.brief, params = {}; if (o.busy) return;
    Object.entries(b.knobs).forEach(([k, d]) => { const v = o.vals[k]; if (v !== undefined && String(v).trim() !== '') params[k] = d.choices || typeof d.default === 'string' ? v : Number(v); });
    o.busy = true; o.msg = ''; EV.draw();
    try { const r = await EV.post('../api/run', { brief: b.id, policy: o.policy, params }); o.runs = null; o.open = r.id; } catch (x) { o.msg = x.message; }
    o.busy = false; EV.draw();
  },
  async swstart() {
    const w = EV.sw, b = EV.M.brief, grid = {}; if (w.busy) return;
    Object.entries(b.knobs).forEach(([k, d]) => { const vs = String(w.grid[k] || '').split(',').map(v => v.trim()).filter(Boolean); if (vs.length) grid[k] = vs.map(v => (d.choices || typeof d.default === 'string' ? v : Number(v))); });
    w.busy = true; w.msg = ''; EV.draw();
    try { w.st = await EV.post('../api/sweep', { brief: b.id, policy: w.policy, grid }); EV.watchSweep(); } catch (x) { w.msg = x.message; }
    w.busy = false; EV.draw();
  },
  async swstop() { const w = EV.sw; try { await EV.post(`../api/sweep/${w.st.id}/stop`, {}); } catch (x) { w.msg = x.message; EV.draw(); } },
});
