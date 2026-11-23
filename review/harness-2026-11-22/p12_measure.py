"""After the deploy, part 12 (s058 turn 9, 2026-11-23 07:00): the last repair of H12 named q_full_fine, a measurement that experiment X8 had defined
the turn before; the repair request showed its value among the earlier results (q_full_fine=0.7), and the harness refused the rule with "q_full_fine
is not one of the outputs", so the test was not run. A measurement is taken by the experiment that defines it (a repair cannot define one). The
refusal now says so when the name is a measurement an earlier experiment defined: where it was defined, that a rule may name it only where its own
experiment defines it too, and which measurements this experiment has. python3 -I p12_measure.py LOOP_PY"""
import sys
from pathlib import Path
f = Path(sys.argv[1]); s = f.read_text()
a = '''            except decision_rules.DecisionRuleError as e:
                return (f"the decision rule for {r['for']} cannot be read: {e}. Decision rule: {r.get('decision_rule')}"
                        + (". A rule compares the simulations of its own test: to compare with one that ran before, list it among the runs with its settings "
                           "(the same settings are returned, not run again)" if "no simulation in this experiment is labelled" in str(e) else ""))'''
b = '''            except decision_rules.DecisionRuleError as e:
                nm = re.match(r"(\\w+) is not one of the outputs", str(e))   # a measurement an earlier experiment defined (part 12: s058 H12 named X8's q_full_fine)
                by_x = next((x["id"] for x in reversed(ledger) if nm and x["type"] == "experiment" and any(isinstance(m, dict) and m.get("name") == nm.group(1) for m in x["body"].get("measurements") or [])), None)
                own = [m.get("name") for m in ex.get("measurements") or [] if isinstance(m, dict) and m.get("name")]
                return (f"the decision rule for {r['for']} cannot be read: {e}. Decision rule: {r.get('decision_rule')}"
                        + (". A rule compares the simulations of its own test: to compare with one that ran before, list it among the runs with its settings "
                           "(the same settings are returned, not run again)" if "no simulation in this experiment is labelled" in str(e) else
                           f". {nm.group(1)} is a measurement experiment {by_x} defined: a measurement is taken by the experiment that defines it, so a rule may name it "
                           f"only where its own experiment defines it too (in measurements, the same definition again); the measurements of this experiment: {', '.join(own) or 'none'}" if by_x else ""))'''
assert s.count(a) == 1; f.write_text(s.replace(a, b)); print("p12 applied to", f)
