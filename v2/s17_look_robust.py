"""After v2.2 (2026-11-27, the same evening): the supervisor's look after the researcher's reply is not needed to go on. A model server error at
that request stopped the session; it now gives a note and the session goes on, as the look at the baseline did before stage 16 (the coherence
audit of 2026-11-22 had made it so for that look). Found by the full run of the harness checks after the deploy (`test_stage1`, section F)."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
sub("harness/loop.py",
    '''                    except (ValueError, KeyError, TypeError) as e:
                        append(ledger, turn, "note", due[-1], {"text": f"the supervisor's look at {', '.join(due)} could not be read ({type(e).__name__}): no finding of its own"})''',
    '''                    except Exception as e:   # its look is not needed to go on: a note, and the session goes on (also at a model server error, as the look at the baseline was)
                        append(ledger, turn, "note", due[-1], {"text": f"the supervisor's look at {', '.join(due)} could not be read ({type(e).__name__}): no finding of its own"})''',
    "(code) a failed look gives a note and the session goes on, whatever failed")
done("stage17_look_robust", "after v2.2: a look of the supervisor that fails does not stop the session")
