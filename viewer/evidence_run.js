// Set up and run. "New session" (the address ?tab=new, reached from Home's one button, or from a session's "Start a
// new session from this setup": ?tab=new&from=<session>): the set-up page. On a running session's page: the banner (evidence_live.js) with Stop. Everything goes through control.py's POST endpoints; the page itself writes no file.
// The operator's own simulation and sweep, on the Operator tab, are in evidence_oprun.js.
// ======================================================================================================
Object.assign(EV, {
  nw: { policy: 'share', budget: '', draft: 'on', tokens: '', temp: '', baseline: true, arm: 'hypotheses' },  // blocks 6 and 7 of the set-up page
  briefs: {},  // brief id -> its file (null: it cannot be read), fetched once
  briefOf(id) { if (id && !(id in EV.briefs)) { EV.briefs[id] = undefined; EV.json(`../briefs/${id}.json`).then(b => { EV.briefs[id] = b; EV.draw(); }); } return EV.briefs[id]; },
  // who rules on a test (block 7 of the set-up page): one AI that judges its own tests, or a researcher and a supervisor, a second AI asked apart from it
  armField() { const a = EV.nw.arm || 'hypotheses'; return `<select data-ch="nw" data-k="arm" id="nw-arm" title="With a supervisor: the researcher proposes and does not rule on its own tests. A second AI, asked apart from it and never shown its reasons, reads each new guess against the records it cites, reviews each test before any simulation is run, and rules on what the checks mean"><option value="hypotheses"${a === 'hypotheses' ? ' selected' : ''}>one AI, which judges its own tests</option><option value="supervised"${a === 'supervised' ? ' selected' : ''}>a researcher and a supervisor</option></select>`; },
  flags() {  // the choices of the panel as control.py takes them; a field left empty keeps the loop's default
    const n = EV.nw, o = { policy: n.policy, draft: n.draft, baseline: !!n.baseline, ...(n.arm && n.arm !== 'hypotheses' ? { arm: n.arm } : {}) }, num = (k, to) => { if (String(n[k]).trim()) o[to] = Number(n[k]); };
    num('budget', 'budget'); num('tokens', 'max_tokens'); num('temp', 'temperature'); return o;
  },

  // ---- "New session": the set-up page. Its seven blocks, the strip above Start and the two buttons are drawn by
  // brief_editor.js in a node of its own, which is kept when the page is drawn again (nothing typed is lost).
  newTab() {
    const st = EV.st, S = EV.s, running = st.sessions.filter(x => x.running).length;
    return `<div class="ev-card" id="new-setup"><h2>New session <small>one complete attempt by the AI at one ${EV.term('Brief', 'brief')} · ${EV.runningSays() || running + ' running now'}${S.from ? ` · filled from session ${EV.e(S.from)}` : ''}</small></h2>
      <p class="sec-q">What will the network be, what will the AI be asked, and what will it see?</p>${EV.legendBar()}
      <div id="be-kind" class="kind-pick" role="radiogroup" aria-label="The system to set up"><p class="kind-h"><b>The system to set up</b> <span class="sm">choose one</span></p>
        <label class="kind-card${EV.setupKind() === 'two' ? ' on' : ''}"><input type="radio" name="ev-kind" data-ch="kind" value="two"${EV.setupKind() === 'two' ? ' checked' : ''}>
          <svg viewBox="0 0 64 28" width="64" height="28" aria-hidden="true"><rect x="1" y="5" width="18" height="18" rx="4" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="45" y="5" width="18" height="18" rx="4" fill="none" stroke="currentColor" stroke-width="1.6"/><line x1="19" y1="12" x2="45" y2="12" stroke="var(--series-1)" stroke-width="2.4"/><line x1="19" y1="16" x2="45" y2="16" stroke="var(--series-2)" stroke-width="2.4"/></svg>
          <span><b>The two-host system</b><span class="sm">ready-made: two hosts, one link, a UDP and a TCP flow</span></span></label>
        <label class="kind-card${EV.setupKind() === 'net' ? ' on' : ''}"><input type="radio" name="ev-kind" data-ch="kind" value="net"${EV.setupKind() === 'net' ? ' checked' : ''}>
          <svg viewBox="0 0 64 28" width="64" height="28" aria-hidden="true"><rect x="1" y="1" width="14" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="1" y="16" width="14" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="25" y="8.5" width="14" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="49" y="8.5" width="14" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 2"/><line x1="15" y1="6.5" x2="25" y2="12" stroke="var(--series-1)" stroke-width="2"/><line x1="15" y1="21.5" x2="25" y2="16" stroke="var(--series-2)" stroke-width="2"/><line x1="39" y1="14" x2="49" y2="14" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 2"/><path d="M56 11.2v5.6M53.2 14h5.6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span><b>A network I build</b><span class="sm">drag and drop: add or remove hosts, links, applications, queues</span></span></label></div>
      <div id="be-host" data-kind="${EV.setupKind()}"></div></div>`;
  },
  // which set-up page is shown: the two-host system's (brief_editor.js) or the builder of a network (brief_net.js); remembered
  setupKind() { let v = null; try { v = localStorage.getItem('ev-kind'); } catch (x) { /* no storage */ } return v === 'net' ? 'net' : 'two'; },
  async afterNew() {
    if (!document.getElementById('be-host')) return;
    if (EV.setupKind() === 'net') {
      if (typeof BRIEF_NET === 'undefined') { if (EV.bnBusy) return; EV.bnBusy = true;
        // the builder draws on JointJS (vendor/joint.min.js, open source): the library first, then the drawing surface, then the builder
        for (const f of ['vendor/joint.min.js', 'brief_canvas.js', 'brief_net.js'].filter(f => f !== 'brief_canvas.js' || typeof NETC === 'undefined')) await new Promise(ok => { const s = document.createElement('script'); s.src = f + (f.startsWith('vendor/') ? '' : '?t=' + Date.now()); s.onload = s.onerror = ok; document.head.appendChild(s); }); }
      if (typeof BRIEF_EDITOR === 'undefined' && !EV.beCss) { EV.beCss = true; await new Promise(ok => { const s = document.createElement('script'); s.src = 'brief_editor.js?t=' + Date.now(); s.onload = s.onerror = ok; document.head.appendChild(s); }); }  // the builder uses the form styles of the two-host set-up page
      if (typeof BRIEF_EDITOR !== 'undefined' && !document.getElementById('be-css')) { const st = document.createElement('style'); st.id = 'be-css'; st.textContent = BRIEF_EDITOR.CSS; document.head.appendChild(st); }
      const h = document.getElementById('be-host'); if (!h || typeof BRIEF_NET === 'undefined') return;
      return BRIEF_NET.mount(h, { get st() { return EV.st; }, post: EV.post, e: EV.e, flags: EV.flags, after: async () => { EV.sig = ''; EV.briefs = {}; await EV.load(); },
        started: async id => { for (let i = 0; i < 40; i++) { const st = await EV.json('../api/status'); if (st && st.sessions.some(x => x.id === id)) break; await new Promise(ok => setTimeout(ok, 500)); } return EV.go({ view: 'session', sid: id, from: null }); } });
    }
    if (typeof BRIEF_EDITOR === 'undefined') { if (EV.beBusy) return; EV.beBusy = true;
      await new Promise(ok => { const s = document.createElement('script'); s.src = 'brief_editor.js?t=' + Date.now(); s.onload = s.onerror = ok; document.head.appendChild(s); }); }
    const host = document.getElementById('be-host'); if (!host || typeof BRIEF_EDITOR === 'undefined') return;
    // the two-host form is offered the briefs without a network; one that has a network belongs to the builder (brief_net.js)
    BRIEF_EDITOR.mount(host, { get st() { const st = EV.st, net = new Set((st && st.network_briefs) || []); return net.size ? { ...st, briefs: st.briefs.filter(b => !net.has(b)) } : st; }, post: EV.post, e: EV.e, from: EV.s.from || null, flags: EV.flags,
      go: o => { Object.assign(EV.s, o); history.replaceState(null, '', EV.address()); },
      after: async () => { EV.sig = ''; await EV.load(); },
      started: async id => { for (let i = 0; i < 40; i++) { const st = await EV.json('../api/status'); if (st && st.sessions.some(x => x.id === id)) break; await new Promise(ok => setTimeout(ok, 500)); }  // until the loop has made its folder
        return EV.go({ view: 'session', sid: id, from: null }); } });
  },

  // ---- a running session: where its work is, what just arrived, and Stop (for a session started from this server): evidence_live.js
  banner() { return EV.liveBanner(); },
});
EV.chg = Object.assign(EV.chg || {}, {
  kind(t) { try { localStorage.setItem('ev-kind', t.value === 'net' ? 'net' : 'two'); } catch (x) { /* no storage */ } EV.draw(); },
  nw(t) { const n = EV.nw, k = t.dataset.k; n[k] = t.type === 'checkbox' ? t.checked : t.value;  // a field never draws the page again: it would lose the cursor to its neighbour
    if (k === 'draft') { const el = document.querySelector('#new-setup input[data-k=tokens]'); if (el) el.placeholder = n.draft === 'on' ? 32000 : 3000; } },
});
EV.inp = Object.assign(EV.inp || {}, { nw(t) { EV.chg.nw(t); } });  // as it is typed, so that a value that cannot be used is refused at once
EV.act = Object.assign(EV.act || {}, {
  new() { EV.go({ view: 'new', from: null }); },
  async stop() {
    if (!window.confirm(`Stop session ${EV.s.sid}? It ends where it is, without a final report.`)) return;
    EV.stopping = true; EV.stopMsg = ''; EV.draw();
    try { await EV.post('../api/stop', { session: EV.s.sid }); } catch (x) { EV.stopMsg = x.message; }
    EV.stopping = false; EV.sig = ''; EV.load();
  },
});
