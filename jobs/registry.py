"""Allowlist of job scripts that can be triggered by name (e.g. from the Slack
`/oshirase-run <job_name>` command, or the `oshirase-run` CLI). This is the
only surface through which an external trigger can select what runs -- there
is deliberately no way to pass through arbitrary text/commands, only a
lookup into this fixed dict of (module path, function name) pairs.

Job modules are imported lazily, inside resolve_job(), rather than all at
once at the top of this file: several jobs pull in heavy/optional
dependencies (e.g. run_roicat -> the real `roicat` package -> `optuna`), and
importing every job module eagerly meant one job's missing dependency broke
resolution of every other job too, even completely unrelated ones. Importing
only the requested job's module means a broken job only breaks itself.

Merges job modules across every jobs/<category>_jobs/ directory into one flat
JOB_REGISTRY, so callers (slack_commands.py, jobs/cli.py) only need one
import and one resolve_job() regardless of which category a job lives under.
"""
import importlib
from typing import Callable, Dict, Tuple

# name -> (module path, function name). Function name is looked up via
# getattr rather than importing it directly, since several modules define a
# function with the same name `run_pm`, which would otherwise collide.
JOB_REGISTRY: Dict[str, Tuple[str, str]] = {
    "pm": ("jobs.hpc_jobs.run_pm", "run_pm"),
    "roicat": ("jobs.hpc_jobs.run_roicat", "run_roicat"),
    "pm_roicat": ("jobs.hpc_jobs.run_pm_roicat", "run_pm_roicat"),
    "pm_holo_ai228": ("jobs.hpc_jobs.run_pm_holo_ai228", "run_pm"),
    "pm_holo_ai230": ("jobs.hpc_jobs.run_pm_holo_ai230", "run_pm"),
    "pm_visual_ai228": ("jobs.hpc_jobs.run_pm_visual_ai228", "run_pm"),
    "pm_visual_ai230": ("jobs.hpc_jobs.run_pm_visual_ai230", "run_pm"),
    "pm_visual_mesoscan_np2": ("jobs.hpc_jobs.run_pm_visual_mesoscan_np2", "run_pm"),
    "echo": ("jobs.hpc_jobs.run_local_example", "run_local_example"),
    "stiminterp": ("jobs.cayde_jobs.stiminterp", "run_stiminterp"),  # cayde
    "upload": ("jobs.cayde_jobs.upload_to_ceph", "upload_to_ceph"),  # cayde
    # Add "<job_name>": ("jobs.cayde_jobs.<module>", "<function>") here as
    # job scripts are added under jobs/cayde_jobs/.
}


class UnknownJobError(KeyError):
    def __init__(self, name: str):
        self.name = name
        self.valid_names = sorted(JOB_REGISTRY)
        super().__init__(
            f"Unknown job '{name}'. Valid job names: {', '.join(self.valid_names)}"
        )


def resolve_job(name: str) -> Callable:
    try:
        module_path, func_name = JOB_REGISTRY[name]
    except KeyError:
        raise UnknownJobError(name) from None

    module = importlib.import_module(module_path)
    return getattr(module, func_name)
