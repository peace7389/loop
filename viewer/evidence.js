// EV: the evidence page. This file: the address (which view), loading, the top bar, clicks, the replay and the review marks.
// evidence_home.js draws Home (no session selected).
// evidence_top.js draws the introduction, the structure map, the legend and the claim chips; evidence_views.js and
// evidence_flow.js the three flow charts; evidence_cards.js, evidence_test.js and evidence_panels.js what opens beside them;
// evidence_more.js the sections below; evidence_operator.js the Operator and Compare tabs.
// ======================================================================================================
const EV = {
  s: { view: 'home', sid: null, brief: null, sel: null, step: null, claim: null, path: false, collapsed: {}, intro: true, heat: ['weightUdp', 'queuePkts'], wide: {}, xchart: null,
       left: 'tree', tree: {}, how: false, more: false, zoom: false, op: false, home: { sort: 'started', dir: -1, filter: '' } },   // op: the "operator columns" switch
  M: null, st: null, files: {}, marks: {}, charts: {}, sig: '',
  e: s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])),
  term: (name, text) => `<abbr title="${EV.e(EV_DEF[name] || '')}">${EV.e(text || name.toLowerCase())}</abbr>`,
  nr: '<span class="mut">not recorded</span>',
  time: ts => String(ts || '').slice(11, 19) || '–',
  mb: v => (typeof v === 'number' ? (v / 1e6).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : '–'),
  val(k, v) { return v == null ? '–' : typeof v !== 'number' ? String(v) : /_bps$/.test(k) ? EV.mb(v) + ' Mbps' : Number.isInteger(v) ? v.toLocaleString('en-US') : String(+v.toPrecision(6)); },
  get off() { return !!window.EV_EXPORT; },  // an exported copy: its data is in export_data.js beside the page, there is no server
  async get(url) {
    if (window.EV_EXPORT) { const k = url.replace(/^(\.\.\/)+/, '').split('?')[0]; return k === 'api/status' ? JSON.stringify(EV_EXPORT.status) : k in EV_EXPORT.files ? EV_EXPORT.files[k] : null; }
    try { const r = await fetch(url + (url.includes('?') ? '&' : '?') + 't=' + Date.now(), { cache: 'no-store' }); return r.ok ? await r.text() : null; } catch (x) { return null; } },
  async json(url) { const t = await EV.get(url); try { return t == null ? null : JSON.parse(t); } catch (x) { return null; } },
  async post(path, body) {  // the operator's actions go through control.py; a refusal comes back as its own sentence
    if (EV.off) throw new Error('This is an exported copy: nothing can be started or saved from it.');
    const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }), j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error || `refused (${r.status})`); return j;
  },
  store: (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (x) { return null; } },

  // ---- the address decides the view: /viewer/ is Home; ?session=<id> that session's page (&tab=operator its operator
  // tab); ?tab=compare the comparison of the sessions of one brief. The top bar is the same in every view.
  route() {
    const q = new URLSearchParams(location.search), S = EV.s, tab = q.get('tab');
    const named = q.get('session') || (EV.off ? EV_EXPORT.session : null); if (named) S.sid = named;  // Home and Compare name none: the session chosen earlier stays chosen
    S.brief = q.get('brief') || S.brief; S.view = tab === 'compare' ? 'compare' : !named ? 'home' : tab === 'operator' ? 'operator' : 'session';
    S.item = q.get('item') || '';  // the item a link names: selected once the session is read
  },
  address() { const S = EV.s; return S.view === 'home' ? location.pathname : S.view === 'compare' ? `?tab=compare${S.brief ? '&brief=' + encodeURIComponent(S.brief) : ''}` : `?session=${S.sid}${S.view === 'operator' ? '&tab=operator' : S.sel && EV.M && EV.M.id === S.sid && EV.itemOf(S.sel) ? '&item=' + encodeURIComponent(EV.itemOf(S.sel)) : ''}`; },
  go(o) {  // to another view or session; the browser's Back returns
    const S = EV.s, other = 'sid' in o && o.sid !== S.sid; Object.assign(S, o);
    if (other) { S.sel = null; S.step = null; S.claim = null; S.path = false; S.collapsed = {}; S.cmp = null; S.tree = {}; S.more = false; }
    history.pushState(null, '', EV.address()); EV.sig = ''; return EV.load();
  },

  async start() {
    EV.s.op = EV.store('ev-op') === '1'; EV.s.how = EV.store('ev-read') !== '1'; EV.store('ev-read', '1'); EV.route();  // "How to read this page": open on the first visit only
    const root = document.getElementById('ev');
    root.addEventListener('click', EV.click); root.addEventListener('change', EV.change); root.addEventListener('input', EV.input);
    root.addEventListener('toggle', ev => { if (ev.target.id === 's-how') EV.s.how = ev.target.open; }, true);
    window.addEventListener('popstate', () => { EV.route(); EV.sig = ''; EV.load(); });
    document.addEventListener('keydown', ev => { if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) || EV.s.view !== 'session' || !EV.M) return;
      if (ev.key === 'ArrowRight') { EV.replay('next'); ev.preventDefault(); } else if (ev.key === 'ArrowLeft') { EV.replay('prev'); ev.preventDefault(); } });
    await EV.load();
    if (!EV.off) setInterval(EV.load, 8000);
  },

  // the session list, then the chosen session's own files; the page is drawn again only when something changed, and
  // never while the reader is typing in one of its fields
  async load() {
    const st = await EV.json('../api/status'); if (!st || !Array.isArray(st.sessions)) { document.getElementById('ev').innerHTML = '<div class="ev-card">This page is served by harness/control.py, which lists the sessions. It does not answer.</div>'; return; }
    const S = EV.s, all = st.sessions, row = all.find(x => x.id === S.sid) || null, a = document.activeElement;
    if (EV.sig && a && a.closest && a.closest('#ev') && ['INPUT', 'TEXTAREA'].includes(a.tagName) && a.type !== 'checkbox') return;
    EV.st = st;
    if ((S.view === 'session' || S.view === 'operator') && !row) S.view = 'home';
    if (S.view === 'home' || S.view === 'compare') {
      const sig = JSON.stringify([S.view, all.map(x => [x.id, x.records, x.running, x.how, x.score, x.review, x.policy]), st.briefs, st.session && st.session.running]);
      if (sig === EV.sig) return; EV.sig = sig; return EV.draw(); }
    const base = `../sessions/${S.sid}/`, sig = JSON.stringify([S.sid, row.records, row.running, row.how, S.view, row.score, row.policy]);
    if (sig === EV.sig) return; EV.sig = sig;
    const [led, meta, rep, idx, score, marks] = await Promise.all([EV.get(base + 'ledger.jsonl'), EV.json(base + 'session.json'), EV.json(base + 'report.json'), EV.get(base + 'runs/index.json'),
      row.score ? EV.json(`../checks/scores/${S.sid}.json`) : null, row.review && row.review.n ? EV.json(`../checks/reviews/${S.sid}.json`) : null]);
    // the scheduling policy comes from control.py only: it withholds a policy the harness chose until the session is scored
    EV.files = { row, score, index: EV_DATA.lines(idx), policy: row.policy || null, key: row.brief ? await EV.json(`../checks/keys/${row.brief}.json`) : null };
    EV.marks = marks || {}; EV.marksFor = S.sid;
    EV.M = EV_DATA.build({ id: S.sid, ledger: EV_DATA.lines(led), session: meta, report: rep, running: !!row.running });
    const linked = S.item != null && S.view === 'session'; if (linked) { S.sel = S.item ? EV.selOf(EV.M, S.item) : null; S.item = null; }  // from the address: on arrival, and on Back
    EV.draw(); if (linked && S.sel) EV.reveal();
  },

  draw() {
    const S = EV.s, e = EV.e, st = EV.st, y = window.scrollY, on = v => (S.view === v ? 'on' : '');
    Object.values(EV.charts).forEach(c => c.destroy()); EV.charts = {};
    const need = st.sessions.some(x => x.id === S.sid) ? '' : ' disabled title="Choose a session first"';  // the two pages of one session
    const label = x => `${x.id} · ${x.brief || 'before briefs'} · ${String(x.started || '').replace('T', ' ').slice(0, 16) || 'no record yet'} · ${x.simulations || 0} simulations · ${x.running ? 'running now' : x.how || 'ending not recorded'}`;
    const bar = EV.off ? `<div class="ev-bar"><b>Two hosts, one link: session ${e(S.sid)}</b><span><button data-act="view" data-id="session" class="${on('session')}">Session</button>${EV_EXPORT.operator ? ` <button data-act="view" data-id="operator" class="${on('operator')}">Operator</button>` : ''}</span>${EV_EXPORT.operator ? `<label style="font-weight:400"><input type="checkbox" data-ch="op"${S.op ? ' checked' : ''}> show operator columns</label>` : ''}<span class="end">an exported copy · it opens without a server</span></div>`
      : `<div class="ev-bar ev-nav"><span class="grp"><span class="cap">All sessions</span><button data-act="view" data-id="home" class="${on('home')}">Home</button><button data-act="view" data-id="compare" class="${on('compare')}">Compare sessions</button></span>
      <span class="grp"><span class="cap" title="${e(EV_DEF.Session)}">One session</span><select data-ch="session"><option value="">choose a session…</option>${st.sessions.slice().reverse().map(x => `<option value="${e(x.id)}"${x.id === S.sid ? ' selected' : ''}>${e(label(x))}</option>`).join('')}</select>
      <button data-act="view" data-id="session" class="${on('session')}"${need}>Session</button><button data-act="view" data-id="operator" class="${on('operator')}"${need || ` title="${e(EV_DEF.Operator)}"`}>Operator</button></span>
      <label class="end" style="font-weight:400" title="Operator-only items: the scheduling policy, the gap to the best row of the sweep"><input type="checkbox" data-ch="op"${S.op ? ' checked' : ''}> show operator columns</label></div>`;
    // the earlier pages are not part of this page's structure: one quiet line at the foot of every view
    const foot = EV.off ? '' : `<div class="ev-foot noprint">earlier pages: <a href="index_runs.html${S.sid ? '?session=' + e(S.sid) : ''}">runs compared</a> · <a href="index_full.html${S.sid ? '?session=' + e(S.sid) : ''}">system, packet events, older control page</a></div>`;
    if (S.view === 'compare' && S.brief == null) { const n = {}; st.sessions.forEach(x => { n[x.brief || ''] = (n[x.brief || ''] || 0) + 1; }); S.brief = ((st.sessions.find(x => x.id === S.sid) || {}).brief) || Object.keys(n).sort((p, q) => n[q] - n[p])[0] || ''; }
    const body = S.view === 'home' ? EV.homeView() : S.view === 'compare' ? EV.compareTab() : !EV.M ? '<div class="ev-card">No session yet.</div>' : S.view === 'operator' ? EV.operatorTab() : EV.sessionTab();
    const root = document.getElementById('ev'), inner = ['.tree', '.ev-lanes', '.ev-map', '.ev-side', '.qlist'].map(q => { const el = root.querySelector(q); return el && [q, el.scrollTop, el.scrollLeft]; }).filter(Boolean);
    root.innerHTML = bar + body + foot + '<div id="ev-print"></div>';
    inner.forEach(([q, top, left]) => { const el = root.querySelector(q); if (el) { el.scrollTop = top; el.scrollLeft = left; } });  // the lists that scroll inside the page stay where the reader left them
    if (S.view === 'session' && EV.M && !EV.off) history.replaceState(null, '', EV.address());  // the address follows the selection: it is always the link to what is open
    const hd = document.getElementById('ev-head'); if (hd) document.getElementById('ev').style.setProperty('--head-h', hd.offsetHeight + 'px');  // the detail pane stays below the header strip
    if (S.view === 'session') { EV.applyReplay(); EV.afterDraw(); } else if (S.view === 'operator') EV.afterOperator(); else if (S.view === 'home' && EV.afterHome) EV.afterHome();
    if (window.scrollY !== y) window.scrollTo(0, y);
  },

  // ---- clicks: every clickable thing carries data-act (and data-id); nothing here moves the page
  click(ev) {
    const t = ev.target.closest('[data-act]'); if (!t) return; const S = EV.s, a = t.dataset.act, id = t.dataset.id;
    if (a === 'view') return EV.go({ view: id });  // the chosen session stays chosen, wherever the reader goes
    if (a === 'pick') return EV.go({ view: 'session', sid: id });
    if (a === 'sort') { const h = S.home; h.dir = h.sort === id ? -h.dir : 1; h.sort = id; return EV.draw(); }
    if (a === 'open') { S.sel = { t: t.dataset.t, id: /^\d+$/.test(id || '') && t.dataset.t === 'log' ? Number(id) : id, test: t.dataset.test || undefined };  // test: the test a simulation was opened from
      return S.view !== 'session' ? EV.go({ view: 'session' }) : EV.draw(); }  // from the heat map: to the session's page
    if (a === 'step') { const o = EV.M.steps[Number(id)].open; S.sel = { t: o.t, id: o.t === 'log' ? o.turn : o.t === 'brief' ? 'brief' : o.t === 'report' ? 'report' : o.id }; return EV.draw(); }
    if (a === 'replay') return EV.replay(id);
    if (a === 'claim') { S.claim = S.claim === Number(id) ? null : Number(id); const c = EV.M.claims[Number(id) - 1]; if (S.claim && c && (c.tests[0] || c.exps[0])) S.sel = c.tests[0] ? { t: 'test', id: c.tests[0] } : { t: 'exp', id: c.exps[0] }; return EV.draw(); }
    if (a === 'wide') { S.wide[id] = !S.wide[id]; return EV.draw(); }      // a test's chart over all the simulations of its experiment
    if (a === 'xchart') { S.xchart = S.xchart === id ? null : id; return EV.draw(); }  // an experiment's chart, on request
    if (a === 'path') { S.path = !S.path; return EV.draw(); }
    if (a === 'fold') { S.collapsed[id] = !S.collapsed[id]; return EV.draw(); }
    if (a === 'intro') { S.intro = false; return EV.draw(); }
    if (a === 'print') return EV.printSheet(Number(id));
    if (a === 'goto') { const [to, left, open] = id.split('|'); if (left) S.left = left; if (open) S.sel = { t: open, id: open }; if (left || open) EV.draw();  // a box of the structure map: to that part of the page
      const el = document.getElementById(to); if (el) el.scrollIntoView({ block: 'start' }); return; }
    if (a === 'export') return EV.exportChart(id, t.dataset.x);
    if (EV.act && EV.act[a]) return EV.act[a](id, t);  // the actions the other files add
  },
  change(ev) {
    const t = ev.target, S = EV.s;
    if (t.dataset.ch === 'session') return EV.go(t.value ? { view: S.view === 'operator' ? 'operator' : 'session', sid: t.value } : { view: 'home', sid: null });
    if (t.dataset.ch === 'op') { S.op = t.checked; EV.store('ev-op', S.op ? '1' : '0'); return EV.draw(); }
    if (t.dataset.ch === 'brief') { S.brief = t.value; history.replaceState(null, '', EV.address()); return EV.draw(); }
    if (t.dataset.ch === 'heat') { S.heat[Number(t.dataset.i)] = t.value; return EV.draw(); }
    if (t.dataset.ch === 'cmp') { S.cmp = t.value || null; return EV.draw(); }
    if (t.dataset.ch === 'review') return EV.saveReview(t.closest('[data-item]'));
    if (EV.chg && EV.chg[t.dataset.ch]) return EV.chg[t.dataset.ch](t);
  },
  input(ev) { const t = ev.target; if (t.dataset.in === 'filter') { EV.s.home.filter = t.value; EV.homeRows(); }  // typing in the filter redraws the rows only
    else if (EV.inp && EV.inp[t.dataset.ch]) EV.inp[t.dataset.ch](t); },

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
    const ro = EV.off ? ' disabled' : '';  // an exported copy shows the marks; it cannot save one
    return `<div class="review" data-item="${EV.e(item)}"><label><input type="checkbox" data-ch="review"${m.tick ? ' checked' : ''}${ro}> reviewed</label>
      <input type="text" data-ch="review" placeholder="reviewer's note" value="${EV.e(m.note || '')}"${ro}></div>`;
  },
  async saveReview(box) {
    const item = box.dataset.item, tick = box.querySelector('input[type=checkbox]').checked, note = box.querySelector('input[type=text]').value;
    const r = await fetch('../api/review', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session: EV.s.sid, item, tick, note }) });
    if (r.ok) { if (tick || note.trim()) EV.marks[item] = { tick, note }; else delete EV.marks[item]; EV.draw(); }
  },
  itemOf: sel => (sel ? `${sel.t}:${sel.id ?? ''}` : ''),
};