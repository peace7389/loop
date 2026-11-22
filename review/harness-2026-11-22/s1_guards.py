"""Stage 1, items 5 and 6 (the coherence audit, 2026-11-22):
5. a measurement, a probe or a check can no longer stop the session after its simulations ran: a measurement that fails is recorded with its reason and
   left out; a check that cannot be computed is "not checked" with its reason; abs() takes one value and min()/max() two or more, refused when the rule
   is read (min(x) passed validation and raised TypeError at the check);
6. measure() keeps each value with its own time when the expression is undefined at some samples (first_time_above gave 2.0 s where it is 10.01 s;
   rate and slope wrong), and says so when it is defined at none (it divided by zero).
Usage: s1_guards.py loop LOOP_PY | tools TOOLS_PY | rules DECISION_RULES_PY"""
import sys
from pathlib import Path
kind, p = sys.argv[1], Path(sys.argv[2]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
if kind == "loop":
    rep('''                mine = measured(body["run_id"])''', '''                try:   # a measurement that fails is left out with its reason: it never stops the session after its simulations ran (the coherence audit, 2026-11-22)
                    mine = measured(body["run_id"])
                except Exception as e:
                    mine, body["measured_error"] = {}, f"{type(e).__name__}: {' '.join(str(e).split())[:200]}"''')
    rep('''        except decision_rules.DecisionRuleError as e:  # it was readable (validate), so: a simulation it names gave no value''',
        '''        except Exception as e:  # it was readable (validate), so: a simulation it names gave no value; anything else is "not checked" with its reason (the coherence audit, 2026-11-22)''')
elif kind == "tools":
    rep('''    xs = [x for x in xs if not math.isnan(x)]
    step = (ts[-1] - ts[0]) / (len(ts) - 1) if len(ts) > 1 else 0.1''', '''    step = (ts[-1] - ts[0]) / (len(ts) - 1) if len(ts) > 1 else 0.1   # the record's own step, before undefined samples leave
    keep = [i for i in range(len(xs)) if not math.isnan(xs[i])]   # each value with its own time (the coherence audit, 2026-11-22: values were paired with the wrong times)
    ts, xs = [ts[i] for i in keep], [xs[i] for i in keep]''' + ('''
    ys = [ys[i] for i in keep] if ys is not None else None''' if "ys = [val(tree2, r) for r in win]" in s else "") + '''
    if not xs:
        return f"error: {of} is not defined at any sample between {lo:g} s and {hi:g} s (it divides by zero there, or reads a quantity with no value)"''')
    n = s.count("    except ValueError as e:\n        return f\"error: cannot read {e}")
    assert n == 1, n
    s = s.replace("    except ValueError as e:\n        return f\"error: cannot read {e}", "    except (ValueError, TypeError) as e:   # TypeError: a function given the wrong number of values (the coherence audit, 2026-11-22)\n        return f\"error: cannot read {e}")
elif kind == "rules":
    rep('''                if take() != ("op", ")"):
                    raise DecisionRuleError("a bracket is not closed")
                return ("call", name, args)''', '''                if take() != ("op", ")"):
                    raise DecisionRuleError("a bracket is not closed")
                if (name == "abs" and len(args) != 1) or (name in ("min", "max") and len(args) < 2):   # refused when the rule is read, not when it is checked (the coherence audit, 2026-11-22)
                    raise DecisionRuleError(f"{name}() takes {'one value' if name == 'abs' else 'two values or more, separated by commas'}")
                return ("call", name, args)''')
p.write_text(s); print("patched", kind, p)
