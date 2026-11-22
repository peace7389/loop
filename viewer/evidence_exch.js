// ======================================================================================================
// What the agents exchanged, in "Turn by turn: who did what" (2026-11-22, the operator: "shouldn't we show what each entity exchanged to help
// users see how they cooperate?"; of three ways, the first). Each record names what it answers (its parent); where that is a record of another
// entity, the two are an exchange: the researcher asks and the harness returns a reading, the researcher states a guess and the supervisor
// reads it, the researcher designs an experiment and ns-3 runs its simulations, the harness checks a rule, the supervisor rules on a hypothesis.
//  - each box says what it answers ("← answers Q5 · Researcher") and what answered it ("→ Harness: T5, T6");
//  - pointing at a box outlines its partners and draws an arrow to each, from the one that asked to the one that answered; nothing moves;
//  - a box made by an agent links to that turn in Agent transcripts (agents.html), where what it was given and what it wrote stand in full.
// The turn records (bookkeeping of the harness) are left out.
// ======================================================================================================
Object.assign(EV, {
  // the exchanges of the open session: of each record, the record of another entity it answers (from), and those of other entities that answer it (to)
  tnExch() {
    const M = EV.M; if (!M) return { from: {}, to: {} }; if (M._exch) return M._exch;
    const recs = (M.recs || []).filter(r => !['draft', 'scratch', 'turn'].includes(r.type)), by = Object.fromEntries(recs.map(r => [r.id, r])), from = {}, to = {};
    recs.forEach(r => { const p = by[r.parent]; if (!p || EV.tnCol(p) === EV.tnCol(r)) return; from[r.id] = p.id; (to[p.id] = to[p.id] || []).push(r.id); });
    return (M._exch = { from, to, by });
  },
  tnWho(id) { const r = EV.tnExch().by[id]; return r ? EV.TN_COLS[EV.tnCol(r)][0] : ''; },
  // the line under a box's head: what it answers, and who answered it (each entity once, its records as links; a long list ends in "and n more")
  tnXLine(r) {
    const X = EV.tnExch(), e = EV.e, ln = id => (EV.seen(id) ? EV.link(id) : e(id)), p = X.from[r.id], kids = (X.to[r.id] || []).filter(EV.seen), out = [];
    if (p && EV.seen(p)) out.push(`<span class="tn-xa" title="${e(`This answers ${p}, a record of the ${EV.tnWho(p)}`)}">← answers ${ln(p)} · ${e(EV.tnWho(p))}</span>`);
    const byWho = {}; kids.forEach(k => { (byWho[EV.tnWho(k)] = byWho[EV.tnWho(k)] || []).push(k); });
    Object.entries(byWho).forEach(([who, ids]) => out.push(`<span class="tn-xb" title="${e(`${ids.length === 1 ? 'This record of the ' + who + ' answers it' : 'These ' + ids.length + ' records of the ' + who + ' answer it'}: ${ids.join(', ')}`)}">→ ${e(who)}: ${ids.slice(0, 6).map(ln).join(', ')}${ids.length > 6 ? ` and ${ids.length - 6} more` : ''}</span>`));
    return out.length ? `<div class="tn-x">${out.join('')}</div>` : '';
  },
  // the link of an agent's box to that turn in Agent transcripts
  tnCallLink(t, col) { return ['model', 'supervisor', 'judge'].includes(col) ? `<a class="tn-call" href="agents.html?session=${encodeURIComponent(EV.M.id)}#turn-${t}" target="_blank" rel="noopener" title="What the agents were given and what they wrote in turn ${t}, in Agent transcripts (a new tab)">transcript ↗</a>` : ''; },
  // pointing at a record: its partners outlined, and an arrow to each, drawn over the turns (in the box that scrolls them, or the fold itself)
  tnPoint(item) {
    EV.tnUnpoint(); const id = item && item.dataset.rid; if (!id) return;
    const X = EV.tnExch(), partners = [X.from[id], ...(X.to[id] || [])].filter(Boolean), host = document.getElementById('tn-scroll') || document.getElementById('s-turns'); if (!partners.length || !host) return;
    const hr = host.getBoundingClientRect(), at = el => { const b = el.getBoundingClientRect(); return { x: b.left - hr.left + host.scrollLeft, y: b.top - hr.top + host.scrollTop, w: b.width, h: b.height }; };
    const me = at(item), paths = [];
    item.classList.add('tn-me');
    partners.forEach(pid => { const el = host.querySelector(`.tn-item[data-rid="${CSS.escape(pid)}"]`); if (!el) return; el.classList.add('tn-partner');
      const o = at(el), asker = pid === X.from[id] ? o : me, answer = pid === X.from[id] ? me : o;
      const right = answer.x > asker.x + asker.w / 2, same = Math.abs(answer.x - asker.x) < 4;
      const x1 = same ? asker.x + asker.w - 6 : right ? asker.x + asker.w : asker.x, y1 = asker.y + Math.min(asker.h / 2, 18), x2 = same ? answer.x + answer.w - 6 : right ? answer.x : answer.x + answer.w, y2 = answer.y + Math.min(answer.h / 2, 18);
      const dx = same ? 28 : (x2 - x1) / 2;
      paths.push(`<path d="M${x1.toFixed(1)},${y1.toFixed(1)} C${(x1 + dx).toFixed(1)},${y1.toFixed(1)} ${(x2 - (same ? -28 : dx)).toFixed(1)},${y2.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}" marker-end="url(#tn-xhead)"/>`); });
    if (!paths.length) return;
    host.insertAdjacentHTML('beforeend', `<svg class="tn-xsvg" id="tn-xsvg" width="${host.scrollWidth}" height="${host.scrollHeight}" aria-hidden="true"><defs><marker id="tn-xhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>${paths.join('')}</svg>`);
  },
  tnUnpoint() { document.querySelectorAll('#tn-xsvg').forEach(s => s.remove()); document.querySelectorAll('.tn-item.tn-me, .tn-item.tn-partner').forEach(el => el.classList.remove('tn-me', 'tn-partner')); },
});
// pointing and leaving (and the keyboard's focus) draw and take away the arrows; the page is drawn again often (a live session): the arrows go with it
document.addEventListener('mouseover', ev => { const it = ev.target.closest && ev.target.closest('#s-turns .tn-item[data-rid]'); if (it && !it.classList.contains('tn-me')) EV.tnPoint(it); else if (!it && document.getElementById('tn-xsvg')) EV.tnUnpoint(); });
document.addEventListener('focusin', ev => { const it = ev.target.closest && ev.target.closest('#s-turns .tn-item[data-rid]'); if (it) EV.tnPoint(it); });
