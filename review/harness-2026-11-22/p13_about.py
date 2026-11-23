"""After the deploy, part 13 (s057 turn 1 and s058 turn 10, 2026-11-23): a guess cited another guess in about (Y3 cited Y2; Y31 cited Y30, the guess
it competed with, written earlier in the same answer), and the harness answered "about names ids that are not in the ledger: Y30", which is not
the reason (Y30 was recorded a moment before) and does not say what to do. about lists the records a guess starts from (results, readings,
checks, rulings), never guesses: the refusal now says so, and where a guess this one answers goes (competes_with, or revises).
python3 -I p13_about.py LOOP_PY"""
import sys
from pathlib import Path
f = Path(sys.argv[1]); s = f.read_text()
a = '''            bad = [a for a in about or [] if a != "brief" and a not in kinds] if isinstance(about, list) else []
            return ((f"about names ids that are not in the ledger: {', '.join(map(str, bad))}" if bad else'''
b = '''            bad = [a for a in about or [] if a != "brief" and a not in kinds] if isinstance(about, list) else []
            guesses = [a for a in about or [] if isinstance(a, str) and re.fullmatch(r"Y\\d+", a)] if isinstance(about, list) else []   # part 13: a guess cited as a record
            if guesses:
                g, gs = ("guess", "guesses") if supervised else ("why", "whys")
                return (f"about lists the records a {g} starts from (results, readings, checks, rulings), never {gs}: {', '.join(guesses)} "
                        f"{'is a ' + g if len(guesses) == 1 else 'are ' + gs}. "
                        + (f"A {g} this one explains otherwise goes in competes_with, one it states more exactly in revises" if supervised and COMP["on"] else f"A {g} this one states more exactly goes in revises")), "harness", None
            return ((f"about names ids that are not in the ledger: {', '.join(map(str, bad))}" if bad else'''
assert s.count(a) == 1; f.write_text(s.replace(a, b)); print("p13 applied to", f)
