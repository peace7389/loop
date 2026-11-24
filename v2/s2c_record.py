"""v2, stage 2c: the ruling's record keeps what stage 2 added (follows, changed, cannot_tell): without them the rule "a guess is refuted only where
its hypothesis follows from it" read nothing.   python3 v2/s2c_record.py"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
sub("harness/loop.py", '''for k in ("questions", "fits", "competes_with", "fits_again", "fits_contradicted", "misses") if ruling.get(k)}''',
    '''for k in ("questions", "fits", "competes_with", "fits_again", "fits_contradicted", "misses", "follows", "changed", "cannot_tell") if ruling.get(k)}''', "item 4, B4, B12: the ruling's record holds the review's Follows, the questions that changed, and what could not be told")
done("stage2c", "v2, stage 2c: the ruling's record")
