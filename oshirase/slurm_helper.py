import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

import submitit
from submitit.helpers import CommandFunction

from oshirase.notification import slack_bot


@dataclass
class SuccessCheck:
    """Describes how to decide success/failure from a submitit job's log file,
    and how to phrase the resulting Slack message."""
    stream: str = "stdout"                 # "stdout" | "stderr"
    match_mode: str = "last_line"          # "last_line" | "anywhere"
    success_pattern: str = "successfully"
    success_message: str = "✅ Job {job_id} completed successfully!"
    failure_message: str = "❌ Job {job_id} failed. Check the log: {log_path}"
    on_missing_log: str = "failure"        # "failure" | "ignore"


class SlurmJobRunner:
    """Thin wrapper around submitit.AutoExecutor that centralizes SLURM resource
    parameters and offers submission of either a CLI command or a plain Python
    callable, so individual job scripts don't need to duplicate this boilerplate.

    Pass cluster="local" (or "debug") to run jobs on a machine with no SLURM at
    all -- submitit's local executor ignores the slurm_*-prefixed resource
    parameters and just runs the command/callable as a local subprocess, so the
    same submit_command/submit_callable/monitor_and_notify API works unchanged.
    See also run_local_and_notify() below for a self-detaching convenience
    wrapper around that use case."""

    def __init__(
        self,
        folder: Union[str, Path] = "../.submitit",
        job_name: str = "submitit",
        partition: str = "cpu",
        time: str = "72:00:00",
        mem_gb: int = 4,
        cpus_per_task: int = 1,
        gres: Optional[str] = None,
        gpus_per_task: Optional[int] = None,
        nodes: Optional[int] = None,
        ntasks_per_node: Optional[int] = None,
        additional_parameters: Optional[dict] = None,
        after_this_job: Optional[submitit.Job] = None,
        dependency_kind: str = "afterok",
        cluster: str = "auto",
    ):
        self.executor = submitit.AutoExecutor(folder=str(folder), cluster=cluster)

        params = dict(
            slurm_partition=partition,
            slurm_job_name=job_name,
            slurm_time=time,
            mem_gb=mem_gb,
            slurm_cpus_per_task=cpus_per_task,
        )
        if gres is not None:
            params["slurm_gres"] = gres
        if gpus_per_task is not None:
            params["slurm_gpus_per_task"] = gpus_per_task
        if nodes is not None:
            params["slurm_nodes"] = nodes
        if ntasks_per_node is not None:
            params["slurm_ntasks_per_node"] = ntasks_per_node

        add_params = dict(additional_parameters or {})
        if after_this_job is not None:
            add_params["dependency"] = f"{dependency_kind}:{after_this_job.job_id}"
        if add_params:
            params["slurm_additional_parameters"] = add_params

        self.executor.update_parameters(**params)

    def submit_command(self, argv: Sequence[str]) -> submitit.Job:
        """Submit a job that runs an arbitrary shell/CLI command."""
        return self.executor.submit(CommandFunction(list(argv)))

    def submit_callable(self, fn: Callable, *args, **kwargs) -> submitit.Job:
        """Submit a job that runs a Python callable directly in-process."""
        return self.executor.submit(fn, *args, **kwargs)

    @staticmethod
    def monitor_and_notify(
        job: submitit.Job,
        check: SuccessCheck = SuccessCheck(),
        interval: int = 30,
        notify: bool = True,
    ) -> bool:
        """Poll `job` until done, inspect its log per `check`, Slack-notify, and
        return whether the job was judged successful."""
        print(f"Start monitoring job {job.job_id} ...")
        while not job.done():
            print("Still running...")
            time.sleep(interval)

        log_path = job.paths.stdout if check.stream == "stdout" else job.paths.stderr
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []

        if check.match_mode == "last_line":
            text = lines[-1].strip() if lines else ""
        else:  # "anywhere"
            text = "".join(lines)

        if not lines:
            success = check.on_missing_log == "ignore"
        else:
            success = check.success_pattern in text

        msg = (check.success_message if success else check.failure_message).format(
            job_id=job.job_id, log_path=log_path
        )
        print(msg)
        if notify:
            slack_bot.notify_slack(msg)
        return success


# --- Backward-compatible presets + wrapper functions -------------------------
# These reproduce the exact behavior/messages of the original hardcoded
# monitor_pm_and_notify / monitor_roicat_and_notify functions, so existing
# imports of these two names keep working unchanged.

PM_SUCCESS_CHECK = SuccessCheck(
    stream="stderr",
    match_mode="last_line",
    success_pattern="successfully",
    success_message="✅ photon-mosaic job {job_id} completed successfully!",
    failure_message="❌ photon-mosaic job {job_id} failed. Check the log",
)

ROICAT_SUCCESS_CHECK = SuccessCheck(
    stream="stdout",
    match_mode="last_line",
    success_pattern="after successful completion",
    success_message="All ROICaT jobs are done!",
    failure_message="❌ ROICaT job {job_id} failed. Check the log",
)


def monitor_pm_and_notify(job: submitit.Job, interval: int = 30) -> bool:
    """Deprecated: kept for backward compatibility. Use SlurmJobRunner.monitor_and_notify."""
    return SlurmJobRunner.monitor_and_notify(job, check=PM_SUCCESS_CHECK, interval=interval)


def monitor_roicat_and_notify(job: submitit.Job, interval: int = 30) -> bool:
    """Deprecated: kept for backward compatibility. Use SlurmJobRunner.monitor_and_notify."""
    return SlurmJobRunner.monitor_and_notify(job, check=ROICAT_SUCCESS_CHECK, interval=interval)


# --- Local (non-SLURM) execution ---------------------------------------------

_DETACHED_ENV_FLAG = "_SLURM_SLACK_BOT_DETACHED"


def run_local_and_notify(
    argv: Optional[Sequence[str]] = None,
    fn: Optional[Callable] = None,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    check: SuccessCheck = SuccessCheck(),
    folder: Union[str, Path] = ".submitit_local",
    interval: int = 10,
    detach: bool = True,
    log_path: Optional[Union[str, Path]] = None,
) -> Optional[submitit.Job]:
    """Run a local (non-SLURM) command (`argv`) or Python callable (`fn`/`args`/
    `kwargs`), then Slack-notify on completion. By default detaches into a
    background process (via setsid) so the caller's terminal can be closed
    immediately; the calling script is re-exec'd with an internal env-var flag
    so the background copy runs the job instead of detaching again."""
    if argv is None and fn is None:
        raise ValueError("Specify either argv or fn")

    if detach and os.environ.get(_DETACHED_ENV_FLAG) != "1":
        log_f = open(log_path, "a") if log_path else subprocess.DEVNULL
        subprocess.Popen(
            [sys.executable] + sys.argv,
            start_new_session=True,  # setsid -- detaches from the controlling terminal
            stdin=subprocess.DEVNULL,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            env={**os.environ, _DETACHED_ENV_FLAG: "1"},
        )
        print("Detached background job started; you can close this terminal.")
        return None

    runner = SlurmJobRunner(folder=folder, cluster="local")
    job = (
        runner.submit_command(argv)
        if argv is not None
        else runner.submit_callable(fn, *args, **(kwargs or {}))
    )
    SlurmJobRunner.monitor_and_notify(job, check=check, interval=interval)
    return job
