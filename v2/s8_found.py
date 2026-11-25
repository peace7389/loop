"""v2, stage 8: what the checks of wrong input found.
  - a network in which no flow passes a scheduler (for example after two new links took both flows off its link) was refused with "put it on the
    side that sends, or use a plain queue": a refusal describes what is wrong and suggests no change (the operator, 2026-11-23: "describe, never
    suggest")."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
sub("harness/network.py", '''bad.append(f"no flow passes {sch}: put it on the side that sends, or use a plain queue")''', '''bad.append(f"no flow passes {sch}: a scheduler divides its link between the flows that pass it on that side")''',
    "the refusal of a network whose scheduler no flow passes: what is wrong, and no suggestion (found by the check of wrong input)")
done("stage8", "v2, stage 8: what the checks of wrong input found")
