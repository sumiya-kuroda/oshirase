"""Thin bootstrap for the `oshirase-run` console script.

Lives inside the oshirase package (so it's always importable via the normal
package mechanism, regardless of whether jobs/ is already on sys.path) but
is kept free of slack_bolt/swc_slack imports -- unlike
oshirase.notification.slack_commands (the `oshirase-listen` listener) --
so `oshirase-run` doesn't require the Slack stack to be installed just to
trigger a job from a terminal.
"""
import sys
from pathlib import Path

# jobs/ lives outside the oshirase package (see jobs/registry.py), so it's
# only importable if the repo root is on sys.path. Resolve that explicitly
# from this file's own location rather than relying on cwd or install-tool
# incidentals (see oshirase/notification/slack_commands.py for the same
# pattern, applied at a different directory depth).
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs.cli import run_cli  # noqa: E402,F401 -- re-exported for setup.py's entry point
