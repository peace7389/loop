// The words that need explaining: a setting, a measure, a part of the network. Wherever one stands on a session's
// page (in the AI's own words, in the page's lines, in a table) it gets a dotted line under it, and its first occurrence
// in a card, a row or a claim is set a little heavier. Pointing at it, or reaching it with the Tab key, opens a small
// box beside it; nothing else changes and the page does not move (scrolled, the box follows its word). The text itself is never changed: the AI wrote
// "weightUdp", and "weightUdp" stays; the box says what it is.
// A word is found by a fixed list, not by guessing:
//   a setting   its field name (weightUdp), and its plain name where that is more than one word ("queue length");
//               the short plain names ("ratio", "seed", "measured time") only where the page itself wrote a setting's
//               values (data-exact)
//   a measure   its field name (udp_loss_frac) and its plain name ("UDP loss")
//   a part      the names of the picture's objects that are one of a kind: UDP queue, TCP queue, scheduler, UDP source,
//               TCP source
// What the box shows is taken from what is recorded, nothing is written for it:
//   a setting   the brief's own line about it (the words the AI was given), its range and where the session started,
//               or that the operator fixed it and at what; the values this session tried, by the replay's step
//   a measure   the harness's line about it (the words the AI was given), its unit, its value in the baseline, what the
//               brief's goal says about it, and where in the picture it is measured
//   a part      its card from "The setting" (EV.objCard): where it sits, what it is set to, who may change that; the
//               scheduling policy stays operator-only there as everywhere
// The labels and terms the page already explains on hover (EV.label, EV.term) open the same box instead of the
// browser's own tooltip; their title stays in the page for a reader who cannot point.
// ======================================================================================================
Object.assign(EV, {
  WD_PARTS: [['UDP queue', 'sender', 'tc'], ['TCP queue', 'sender', 'tc'], ['Scheduler', 'sender', 'tc'], ['UDP source', 'sender', 'apps'], ['TCP source', 'sender', 'apps']],
  WD_IN: '#s-system, #s-made, #s-find, #s-notebook, #s-proposes, #s-research, #p-detail',  // where words are marked
  WD_SKIP: 'svg, script, style, textarea, select, option, input, abbr, .wd, .wd-pop, button:not(.chip), .review, [data-nowd]',
  // the list of this session: name (lower case) -> key; and the two patterns (everywhere; where the page wrote a setting's values)
  wdList() {
    const M = EV.M; if (M._wd) return M._wd; const b = M.brief || {}, given = (M.meta && M.meta.given) || {}, names = {}, short = {}, add = (o, n, k) => { if (n && !(String(n).toLowerCase() in o)) o[String(n).toLowerCase()] = k; };
    Object.keys({ ...(b.system || {}), ...(b.knobs || {}) }).forEach(k => { const plain = EV.LABEL[k]; if (/[A-Z_]/.test(k)) add(names, k, 'k:' + k); else add(short, k, 'k:' + k); if (plain && plain.includes(' ') && plain !== 'measured time') add(names, plain, 'k:' + k); else add(short, plain, 'k:' + k); });
    Object.keys({ ...TH_DATA.PLAIN, ...(given.outputs || {}) }).forEach(k => { add(names, k, 'm:' + k); if (!['link_rate_bps', 'weight_udp'].includes(k)) add(names, TH_DATA.PLAIN[k], 'm:' + k); });
    EV.WD_PARTS.forEach(([n]) => add(names, n, 'o:' + n));
    const re = o => { const all = Object.keys(o).sort((p, q) => q.length - p.length).map(n => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')); return all.length ? new RegExp(`(?<![A-Za-z0-9_])(${all.join('|')})(?![A-Za-z0-9_])`, 'gi') : null; };
    return (M._wd = { names, both: { ...short, ...names }, re: re(names), reExact: re({ ...short, ...names }) });
  },
  // after the page is drawn: the words of the list are wrapped where they stand; the text is the same before and after
  wordsMark() {
    const M = EV.M, root = document.getElementById('ev'); if (!M || !root || EV.wordsOff) return; const W = EV.wdList(); if (!W.re) return;
    root.querySelectorAll(EV.WD_IN).forEach(box => {
      const tw = document.createTreeWalker(box, NodeFilter.SHOW_TEXT, { acceptNode: n => (n.nodeValue.length < 3 || !n.parentElement || n.parentElement.closest(EV.WD_SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT) }), nodes = [], first = new Map();
      while (tw.nextNode()) nodes.push(tw.currentNode);
      nodes.forEach(n => { const exact = !!n.parentElement.closest('[data-exact]'), re = exact ? W.reExact : W.re, text = n.nodeValue; re.lastIndex = 0; let m, at = 0, frag = null;
        while ((m = re.exec(text))) { const key = W.both[m[1].toLowerCase()]; if (!key) continue; frag = frag || document.createDocumentFragment();
          if (m.index > at) frag.appendChild(document.createTextNode(text.slice(at, m.index)));
          const s = document.createElement('span'), block = n.parentElement.closest('.nb-card, tr, button.chip, .pr-b, li, p, .nb-head') || box, seen = first.get(block) || first.set(block, new Set()).get(block);
          s.className = 'wd'; s.dataset.wd = key; s.textContent = m[1]; if (!seen.has(key)) { seen.add(key); s.classList.add('wd1'); s.tabIndex = 0; }
          frag.appendChild(s); at = m.index + m[1].length; }
        if (frag) { if (at < text.length) frag.appendChild(document.createTextNode(text.slice(at))); n.parentNode.replaceChild(frag, n); } });
      // what the page already explains on hover: the same box
      box.querySelectorAll('abbr[title]').forEach(a => { const t = a.title, f = /\(field: (\w+)\)\s*$/.exec(t), mm = /^(\w+): /.exec(t), d = Object.keys(EV_DEF).find(k => EV_DEF[k] === t);
        const key = f && ('k:' + f[1]) in EV.wdKeys(W) ? 'k:' + f[1] : mm && ('m:' + mm[1]) in EV.wdKeys(W) ? 'm:' + mm[1] : d ? 'd:' + d : null; if (key) a.dataset.wd = key; });
    });
  },
  wdKeys(W) { return W.keys || (W.keys = Object.fromEntries(Object.values(W.both).map(k => [k, 1]))); },
  // ---- what the box says, by key
  wdBody(key) {
    const M = EV.M, e = EV.e, b = M.brief || {}, given = (M.meta && M.meta.given) || {}, [kind, name] = [key[0], key.slice(2)], head = (title, what, field) => `<p class="wd-h"><b>${e(title)}</b> <span class="sm">${what}${field ? ` · field <code>${e(field)}</code>` : ''}</span></p>`;
    if (kind === 'd') return `${head(name, 'a word of this page')}<p>${e(EV_DEF[name] || '')}</p>`;
    if (kind === 'o') { const p = EV.WD_PARTS.find(q => q[0] === name), id = p && EV.OB ? EV.sysId(p[1], p[2], p[0]) : null; return id ? `<div class="wd-obj">${EV.objCard(id)}</div><p class="sm">from the picture in “The setting”</p>` : `${head(name, 'a part of the network')}<p class="sm">Its settings are in the picture of “The setting”.</p>`; }
    if (kind === 'k') { const kn = (b.knobs || {})[name], fixed = (b.system || {})[name], plain = EV.LABEL[name] || name;
      const tried = (() => { const vs = [...new Set(M.sims.filter(q => EV.seen(q.id) && q.params && q.params[name] != null && (M.expById[q.exp] || {}).by !== 'harness').map(q => q.params[name]))], num = vs.length > 0 && vs.every(x => typeof x === 'number');
        return !vs.length ? '' : `<p class="sm" data-wd-tried="${vs.length}">This session's own simulations tried ${vs.length === 1 ? 'one value: ' + e(EV.setVal(name, vs[0])) : num ? `${vs.length} values, from ${e(EV.setVal(name, Math.min(...vs)))} to ${e(EV.setVal(name, Math.max(...vs)))}` : `${vs.length} values: ${e(vs.map(v => EV.setVal(name, v)).join(', '))}`}.</p>`; })();
      return `${head(plain, 'a setting', name)}${kn && kn.meaning ? `<p data-own="operator" data-wd-says="1">${e(kn.meaning)}</p><p class="sm">the brief's line about it: the words the AI was given</p>` : `<p data-wd-says="1">${e(EV.SET_SAYS[name] || '')}</p>`}
        ${kn ? `<p data-exact="1"><span class="st-by" data-by="model"><i class="sw"></i>the AI may change it</span>: <span data-wd-range="1">${e(EV.setRange(name, kn))}</span>; the session started from <b data-wd-default="1">${e(EV.setVal(name, kn.default))}</b></p>${tried}`
          : fixed !== undefined ? `<p data-exact="1"><span class="st-by" data-by="operator"><i class="sw"></i>fixed by the operator</span> at <b data-wd-fixed="1">${e(EV.setVal(name, fixed))}</b></p>` : ''}`; }
    // a measure
    const says = (given.outputs || {})[name], s0 = M.simById.S0 && EV.seen('S0') ? M.simById.S0 : null, g = b.goal || {}, cond = (g.conditions || []).find(c => new RegExp('^\\s*' + name + '\\b').test(c)), unit = /_bps$/.test(name) ? 'Mbps or Gbps' : ['udp_loss_frac', 'link_util'].includes(name) ? 'per cent' : /^drops_|retrans/.test(name) ? 'a count of packets' : '';
    const where = EV.OB ? [EV.OB.channel, ...EV.OB.hosts.flatMap(h => ['apps', 'stack', 'tc', 'dev'].flatMap(l => (h[l] || []).map(o => ({ ...o, host: h.title }))))].find(o => (o.measured || []).includes(name)) : null;
    return `${head(TH_DATA.PLAIN[name] || name, 'a measure of each simulation', name)}${says ? `<p data-own="harness" data-wd-says="1">${e(says)}</p><p class="sm">the harness's line about it: the words the AI was given</p>` : ''}
      <p>${unit ? `shown in ${unit}` : ''}${s0 && s0.metrics && s0.metrics[name] != null ? `${unit ? ' · ' : ''}in the baseline: <b data-wd-base="1">${EV.v4(name, s0.metrics[name])}</b>` : ''}</p>
      ${g.kind === 'given' && g.target && g.target.measure === name ? `<p data-wd-goal="target"><span class="st-by" data-by="operator"><i class="sw"></i>the brief's target</span>: the ${g.target.direction === 'min' ? 'smallest' : 'largest'} is wanted</p>` : ''}${cond ? `<p data-wd-goal="condition"><span class="st-by" data-by="operator"><i class="sw"></i>the brief's condition</span>: ${EV.readHtml(cond) || e(cond)}</p>` : ''}
      ${where ? `<p class="sm">measured at: ${e(where.name)}${where.host ? ', ' + e(where.host.toLowerCase()) : ''}</p>` : ''}`;
  },
  // ---- the box: one for the page, shown beside the word that is pointed at or has the keyboard's focus
  wdShow(el) {
    const root = document.getElementById('ev'); EV.wdHide(); if (!el.isConnected || !EV.M) return;
    const pop = document.createElement('div'); pop.id = 'wd-pop'; pop.className = 'wd-pop'; pop.setAttribute('role', 'tooltip'); pop.dataset.wd = el.dataset.wd; pop.innerHTML = EV.wdBody(el.dataset.wd); root.appendChild(pop);
    // the browser's own tooltip of the word and of what it stands in is held back while the box is open
    EV._wdTitles = []; for (let a = el; a && a !== root; a = a.parentElement) if (a.title) { EV._wdTitles.push([a, a.title]); a.removeAttribute('title'); }
    EV._wdEl = el; EV.wdPlace();
  },
  // beside its word: below it where there is room, else above; when the page is scrolled the box follows its word, and goes once the word has left the window
  wdPlace() {
    const el = EV._wdEl, pop = document.getElementById('wd-pop'); if (!el || !pop) return; const r = el.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return EV.wdHide();
    const w = pop.offsetWidth, h = pop.offsetHeight, below = r.bottom + 6 + h <= innerHeight || r.top - 6 - h < 0;
    pop.style.left = Math.max(8, Math.min(r.left, innerWidth - w - 8)) + 'px'; pop.style.top = Math.max(4, below ? Math.min(r.bottom + 6, innerHeight - h - 4) : r.top - 6 - h) + 'px';
  },
  wdHide() { clearTimeout(EV._wdT); const pop = document.getElementById('wd-pop'); if (pop) pop.remove(); (EV._wdTitles || []).forEach(([a, t]) => { if (a.isConnected && !a.title) a.title = t; }); EV._wdTitles = []; EV._wdEl = null; },
});
(() => { const root = document.getElementById('ev'), of = ev => (ev.target.closest ? ev.target.closest('[data-wd]:not(.wd-pop)') : null);
  root.addEventListener('mouseover', ev => { const el = of(ev); if (!el || el === EV._wdEl) return; clearTimeout(EV._wdT); EV._wdT = setTimeout(() => EV.wdShow(el), 140); });
  root.addEventListener('mouseout', ev => { const el = of(ev); if (el && !(ev.relatedTarget && el.contains(ev.relatedTarget))) EV.wdHide(); });
  root.addEventListener('focusin', ev => { const el = of(ev); if (el) EV.wdShow(el); });
  root.addEventListener('focusout', ev => { if (of(ev)) EV.wdHide(); });
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape') EV.wdHide(); });
  window.addEventListener('scroll', () => EV.wdPlace(), { passive: true });
})();
