"""Inbound Slack handling: a `/oshirase-run <job_name>` slash command that
triggers one of the jobs registered in jobs.registry.

Runs over Socket Mode (no public HTTPS endpoint needed, matching the app
manifest documented in the README), so the only new secret required is a
Slack app-level token (SLACK_BOT_APP_TOKEN).

Each triggered job is submitted from a detached subprocess, mirroring the
run_local_and_notify(detach=True) pattern in oshirase.slurm_helper: this
decouples a job's poll-until-done lifetime (up to 72h) from the listener
process's own uptime, so restarting the listener never drops a completion
notification for a job that's still running.
"""
import os
import subprocess
import sys
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from oshirase.notification import slack_bot

# jobs/ lives outside the oshirase package (deliberately -- see registry.py),
# so it's only importable if the repo root is on sys.path. Rather than rely
# on that being true incidentally (whichever cwd the process happens to
# start with, or whichever editable-install mechanism put it there), resolve
# it explicitly from this file's own location, which is stable regardless of
# cwd or install tool (pip/uv/conda all preserve __file__ for editable
# installs).
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs.registry import resolve_job, UnknownJobError


def build_app(config_path=None) -> App:
    configs = slack_bot.load_and_process_config(config_path)
    client = slack_bot.get_slack_client(configs=configs)
    app = App(client=client)

    @app.command("/oshirase-run")
    def handle_run(ack, command, respond):
        ack()

        job_name = command.get("text", "").split()[:1]
        job_name = job_name[0] if job_name else ""
        user_id = command.get("user_id", "unknown")

        try:
            resolve_job(job_name)
        except UnknownJobError as e:
            respond(response_type="ephemeral", text=str(e))
            return

        try:
            slack_bot.notify_slack(f"🚀 <@{user_id}> started `{job_name}`...")
            _dispatch_detached(job_name)
        except Exception as e:
            respond(response_type="ephemeral", text=f"Failed to start `{job_name}`: {e}")

    return app


def _dispatch_detached(job_name: str) -> None:
    """Spawn a fully detached subprocess that resolves and runs the named job.
    The child owns the whole submit + monitor_and_notify lifecycle, independent
    of this listener process."""
    code = (
        "from jobs.registry import resolve_job; "
        f"resolve_job({job_name!r})()"
    )
    # A fresh interpreter doesn't inherit this process's sys.path fixup, so
    # give it the repo root via PYTHONPATH explicitly rather than relying on
    # this subprocess's cwd to happen to be the repo root too.
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            filter(None, [str(REPO_ROOT), os.environ.get("PYTHONPATH", "")])
        ),
    }
    subprocess.Popen(
        [sys.executable, "-c", code],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        env=env,
    )


def main():
    app = build_app()
    SocketModeHandler(app, slack_bot.get_app_token()).start()


if __name__ == "__main__":
    main()
