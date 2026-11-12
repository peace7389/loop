// The margin of a check: how far it was from its decision rule. A column of the tests list; not a chart.
// Read from the check's rule with its numbers written in (the harness's record): for a > b or a >= b it is
// (a - b) / |b|, for a < b or a <= b it is (b - a) / |b|; comparisons joined by AND give the smallest, by OR the
// largest. A right side of 0, or ==, has no margin: "not applicable". Whether the check held or failed is taken from
// the check itself, never from the sign. Shown as a number with a short bar, cut at +-100% and marked when cut.
// During the replay a check recorded after the chosen step shows nothing here. The column is not printed.
// ======================================================================================================
Object.assign(EV, {
  MARGIN_NOTE: "By how much of the rule's right side the measured side cleared it. It depends on how the rule was written, so it compares checks of the same kind only; it does not say whether a prediction was bold.",
  // a rule with its numbers written in -> its margin (a number), null (not applicable), or undefined (it cannot be read)
  margin(text) {
    const tok = String(text || '').match(/\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+|[A-Za-z_]+|<=|>=|==|&&|\|\||[-+*/(),<>]/g) || []; let i = 0;
    const peek = () => tok[i], take = () => tok[i++], is = (...w) => w.includes(String(peek()).toUpperCase()), fail = () => { throw new Error('unreadable'); };
    const expr = () => { let v = term(); while (peek() === '+' || peek() === '-') v = take() === '+' ? v + term() : v - term(); return v; };
    const term = () => { let v = factor(); while (peek() === '*' || peek() === '/') { const op = take(), b = factor(); v = op === '*' ? v * b : v / b; } return v; };
    const factor = () => { const t = take();
      if (t === '-') return -factor();
      if (t === '(') { const v = expr(); if (take() !== ')') fail(); return v; }
      if (/^[\d.]/.test(t || '')) return Number(t);
      const f = { abs: Math.abs, min: Math.min, max: Math.max }[t]; if (!f || take() !== '(') fail();
      const args = [expr()]; while (peek() === ',') { take(); args.push(expr()); } if (take() !== ')') fail(); return f(...args); };
    const cmp = () => { const a = expr(), op = take(), b = ['<', '<=', '>', '>=', '=='].includes(op) ? expr() : fail();
      return op === '==' || b === 0 ? null : (op[0] === '>' ? a - b : b - a) / Math.abs(b); };
    const part = () => { const at = i; try { return cmp(); } catch (x) { i = at; if (peek() !== '(') throw x; } take(); const v = either(); if (take() !== ')') fail(); return v; };
    const join = (next, words, pick) => () => { const ms = [next()]; while (is(...words)) { take(); ms.push(next()); } return ms.some(m => m === null) ? null : pick(...ms); };
    const both = join(part, ['AND', '&&'], Math.min), either = join(both, ['OR', '||'], Math.max);
    try { const m = either(); return i < tok.length || (m !== null && !isFinite(m)) ? undefined : m; } catch (x) { return undefined; }
  },
  marginText: m => (m < 0 ? '−' : '+') + (Math.abs(100 * m) >= 1000 ? Math.abs(100 * m).toFixed(0) : Math.abs(100 * m).toFixed(1)) + '%',
  // the cell of one test's check: the number, and a bar from the middle, to the right when the measured side cleared the rule
  marginCell(c) {
    if (!c || !EV.seen(c.id)) return '';  // no check was made, or it is recorded after the replay's step
    const m = EV.margin(c.numbers), col = c.result === 'held' ? 'var(--good)' : c.result === 'failed' ? 'var(--critical)' : 'var(--text-muted)';
    if (m === undefined) return `<span class="mut" title="The rule with its numbers written in could not be read">${c.numbers == null ? 'not recorded' : 'not read'}</span>`;
    if (m === null) return '<span class="mut" data-margin="na" title="The rule compares with ==, or its right side is 0: there is no margin">not applicable</span>';
    const cut = Math.abs(m) > 1, w = Math.min(1, Math.abs(m)) * 24;
    return `<span class="mg" data-margin="${m}" data-cut="${+cut}" title="${EV.e(c.numbers)}"><span class="mg-n">${EV.marginText(m)}</span><svg width="56" height="12" viewBox="0 0 56 12"><line x1="28" x2="28" y1="1" y2="11" stroke="var(--text-muted)"/>
      <rect x="${m < 0 ? 28 - w : 28}" y="3.5" width="${Math.max(w, 0.8)}" height="5" fill="${col}"/>${cut ? `<path d="M${m < 0 ? 2.5 : 53.5},2 l${m < 0 ? -2.5 : 2.5},4 l${m < 0 ? 2.5 : -2.5},4" fill="none" stroke="${col}" stroke-width="1.6"/>` : ''}</svg>${cut ? '<span class="sm" title="The bar is cut at 100%">cut</span>' : ''}</span>`;
  },
});
