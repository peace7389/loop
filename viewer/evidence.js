// EV: the evidence page. This file: loading, the top bar, clicks, the replay and the review marks.
// evidence_top.js draws the introduction, the structure map, the legend and the claim chips; evidence_views.js and
// evidence_flow.js the three flow charts; evidence_cards.js and evidence_panels.js what opens beside them;
// evidence_more.js the sections below; evidence_operator.js the Operator and Compare tabs.
// ======================================================================================================
const EV = {
  s: { brief: null, sid: null, tab: 'session', sel: null, step: null, claim: null, path: false, collapsed: {}, intro: true, heat: ['weightUdp', 'queuePkts'] },
  M: null, st: null, files: {}, marks: {}, charts: {}, sig: '',
  e: s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])),
  term: (name, text) => `<abbr title="${EV.e(EV_DEF[name] || '')}">${EV.e(text || name.toLowerCase())}</abbr>`,
  nr: '<span class="mut">not recorded</span>',
  time: ts => String(ts || '').slice(11, 19) || '–',
  mb: v => (typeof v === 'number' ? (v / 1e6).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : '–'),
  val(k, v) { return v == null ? '–' : typeof v !== 'number' ? String(v) : /_bps$/.test(k) ? EV.mb(v) + ' Mbps' : Number.isInteger(v) ? v.toLocaleString('en-US') : String(+v.toPrecision(6)); },
  async get(url) { try { const r = await fetch(url + (url.includes('?') ? '&' : '?') + 't=' + Date.now(), { cache: 'no-store' }); return r.ok ? await r.text() : null; } catch (x) { return null; } },
  async json(url) { const t = await EV.get(url); try { return t == null ? null : JSON.parse(t); } catch (x) { return null; } },

  async start() {
    const q = new URLSearchParams(location.search); EV.s.sid = q.get('session'); EV.s.tab = q.get('tab') || 'session';
    const root = document.getElementById('ev');
    root.addEventListener('click', EV.click); root.addEventListener('change', EV.change);
    document.addEventListener('keydown', ev => { if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) || EV.s.tab !== 'session') return;
      if (ev.key === 'ArrowRight') { EV.replay('next'); ev.preventDefault(); } else if (ev.key === 'ArrowLeft') { EV.replay('prev'); ev.preventDefault(); } });
    await EV.load();
    setInterval(EV.load, 8000);
  },

  // the session list, then the chosen session's own files; the page is drawn again only when something changed
  async load() {
    const st = await EV.json('../api/status'); if (!st || !Array.isArray(st.sessions)) { document.getElementById('ev').innerHTML = '<div class="ev-card">This page is served by harness/control.py, which lists the sessions. It does not answer.</div>'; return; }
    EV.st = st; const S = EV.s, all = st.sessions;
    if (!all.some(x => x.id === S.sid)) S.sid = (all.find(x => x.running) || all[all.length - 1] || {}).id || null;
    const row = all.find(x => x.id === S.sid) || {}; S.brief = S.brief && S.keepBrief ? S.brief : row.brief || null;
    const base = `../sessions/${S.sid}/`, sig = JSON.stringify([S.sid, row.records, row.running, row.how, S.tab]);
    if (sig === EV.sig) return; EV.sig = sig;
    const [led, meta, rep, idx, op, score, marks] = await Promise.all([EV.get(base + 'ledger.jsonl'), EV.json(base + 'session.json'), EV.json(base + 'report.json'), EV.get(base + 'runs/index.json'),
      EV.get('../checks/operator.jsonl'), EV.json(`../checks/scores/${S.sid}.json`), EV.json(`../checks/reviews/${S.sid}.json`)]);
    const oper = EV_DATA.lines(op).filter(o => o.session === S.sid);
    EV.files = { row, score, index: EV_DATA.lines(idx), policy: (oper[0] && (oper[0].policy || oper[0].mode)) || row.policy || null, key: row.brief ? await EV.json(`../checks/keys/${row.brief}.json`) : null,
                 scores: {} };
    EV.marks = marks || {};
    EV.M = EV_DATA.build({ id: S.sid, ledger: EV_DATA.lines(led), session: meta, report: rep, running: !!row.running });
    if (S.sel && S.selFor !== S.sid) { S.sel = null; S.step = null; S.claim = null; S.path = false; S.collapsed = {}; }
    S.selFor = S.sid;
    EV.draw();
  },

  draw() {
    const S = EV.s, e = EV.e, st = EV.st, y = window.scrollY;
    Object.values(EV.charts).forEach(c => c.destroy()); EV.charts = {};
    const label = x => `${x.id} · ${x.brief || 'before briefs'} · ${String(x.started || '').replace('T', ' ').slice(0, 16) || 'no record yet'} · ${x.simulations || 0} simulations · ${x.running ? 'running now' : x.how || 'ending not recorded'}`;
    const briefs = [...new Set(st.sessions.map(x => x.brief || ''))];
    const tabs = [['session', 'Session'], ['operator', 'Operator'], ['compare', 'Compare sessions']];
    const bar = `<div class="ev-bar"><label>${EV.term('Brief', 'Brief')} <select data-ch="brief">${briefs.map(b => `<option value="${e(b)}"${b === (S.brief || '') ? ' selected' : ''}>${e(b || 'before briefs')}</option>`).join('')}</select></label>
      <label>${EV.term('Session', 'Session')} <select data-ch="session">${st.sessions.filter(x => (x.brief || '') === (S.brief || '')).slice().reverse().map(x => `<option value="${e(x.id)}"${x.id === S.sid ? ' selected' : ''}>${e(label(x))}</option>`).join('')}</select></label>
      <span>${tabs.map(([k, t]) => `<button data-act="tab" data-id="${k}" class="${S.tab === k ? 'on' : ''}">${t}</button>`).join(' ')}</span>
      <span class="end">other pages: <a href="index_runs.html?session=${e(S.sid)}">runs compared</a> · <a href="index_full.html?session=${e(S.sid)}">system, packet events, control</a></span></div>`;
    const body = !EV.M ? '<div class="ev-card">No session yet.</div>' : S.tab === 'operator' ? EV.operatorTab() : S.tab === 'compare' ? EV.compareTab() : EV.sessionTab();
    document.getElementById('ev').innerHTML = bar + body + '<div id="ev-print"></div>';
    if (S.tab === 'session') { EV.applyReplay(); EV.afterDraw(); } else if (S.tab === 'operator') EV.afterOperator();
    if (window.scrollY !== y) window.scrollTo(0, y);
  },

  // ---- clicks: every clickable thing carries data-act (and data-id); nothing here moves the page
  click(ev) {
    const t = ev.target.closest('[data-act]'); if (!t) return; const S = EV.s, a = t.dataset.act, id = t.dataset.id;
    if (a === 'tab') { S.tab = id; EV.sig = ''; history.replaceState(null, '', `?session=${S.sid}&tab=${id}`); return EV.load(); }
    if (a === 'open') { S.sel = { t: t.dataset.t, id: /^\d+$/.test(id || '') && t.dataset.t === 'log' ? Number(id) : id };
      if (S.tab !== 'session') { S.tab = 'session'; EV.sig = ''; history.replaceState(null, '', `?session=${S.sid}&tab=session`); return EV.load(); }  // from the heat map
      return EV.draw(); }
    if (a === 'pick') { S.sid = id; S.tab = 'session'; S.sel = null; S.step = null; S.claim = null; EV.sig = ''; history.replaceState(null, '', `?session=${id}&tab=session`); return EV.load(); }
    if (a === 'step') { const k = Number(id), o = EV.M.steps[k].open; S.sel = { ...o, id: o.t === 'log' ? o.turn : o.id, k }; return EV.draw(); }
    if (a === 'replay') return EV.replay(id);
    if (a === 'claim') { S.claim = S.claim === Number(id) ? null : Number(id); const c = EV.M.claims[Number(id) - 1]; if (S.claim && c && c.exps[0]) S.sel = { t: 'exp', id: c.exps[0] }; return EV.draw(); }
    if (a === 'path') { S.path = !S.path; return EV.draw(); }
    if (a === 'fold') { S.collapsed[id] = !S.collapsed[id]; return EV.draw(); }
    if (a === 'intro') { S.intro = false; return EV.draw(); }
    if (a === 'print') return EV.printSheet(Number(id));
    if (a === 'goto') { const el = document.getElementById(id); if (el) el.scrollIntoView({ block: 'start' }); return; }
    if (a === 'export') return EV.exportChart(id, t.dataset.x);
  },
  change(ev) {
    const t = ev.target, S = EV.s;
    if (t.dataset.ch === 'session') { S.sid = t.value; S.sel = null; S.step = null; S.claim = null; EV.sig = ''; history.replaceState(null, '', `?session=${S.sid}&tab=${S.tab}`); return EV.load(); }
    if (t.dataset.ch === 'brief') { S.brief = t.value || null; S.keepBrief = true; const first = EV.st.sessions.filter(x => (x.brief || '') === t.value).pop(); if (first) { S.sid = first.id; S.sel = null; S.step = null; } S.keepBrief = false; EV.sig = ''; return EV.load(); }
    if (t.dataset.ch === 'heat') { S.heat[Number(t.dataset.i)] = t.value; return EV.draw(); }
    if (t.dataset.ch === 'cmp') { S.cmp = t.value || null; return EV.draw(); }
    if (t.dataset.ch === 'review') return EV.saveReview(t.closest('[data-item]'));
  },

  // ---- replay: at step k everything recorded later is greyed, in all three views
  replay(how) {
    const S = EV.s, n = EV.M.steps.length - 1;
    S.step = how === 'first' ? 0 : how === 'last' ? null : how === 'prev' ? Math.max(0, (S.step == null ? n : S.step) - 1) : S.step == null ? null : S.step + 1 > n ? null : S.step + 1;
    if (S.step === n) S.step = null;
    EV.draw();
  },
  seen: id => EV.s.step == null || (EV.M.recStep[id] ?? 0) <= EV.s.step,
  applyReplay() {
    const k = EV.s.step;
    document.querySelectorAll('#ev [data-step]').forEach(el => el.classList.toggle('later', k != null && Number(el.dataset.step) > k));
  },

  // ---- review marks: a tick and a note per item, kept by control.py in checks/reviews/<session>.json
  reviewBox(item) {
    const m = EV.marks[item] || {};
    return `<div class="review" data-item="${EV.e(item)}"><label><input type="checkbox" data-ch="review"${m.tick ? ' checked' : ''}> reviewed</label>
      <input type="text" data-ch="review" placeholder="reviewer's note" value="${EV.e(m.note || '')}"></div>`;
  },
  async saveReview(box) {
    const item = box.dataset.item, tick = box.querySelector('input[type=checkbox]').checked, note = box.querySelector('input[type=text]').value;
    const r = await fetch('../api/review', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session: EV.s.sid, item, tick, note }) });
    if (r.ok) { if (tick || note.trim()) EV.marks[item] = { tick, note }; else delete EV.marks[item]; EV.draw(); }
  },
  itemOf: sel => (sel ? `${sel.t}:${sel.id ?? ''}` : ''),
};