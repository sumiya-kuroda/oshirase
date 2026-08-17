"""Allowlist of job scripts that can be triggered by name (e.g. from the Slack
`/oshirase-run <job_name>` command, or the `oshirase-run` CLI). This is the
only surface through which an external trigger can select what runs -- there
is deliberately no way to pass through arbitrary text/commands, only a
lookup into this fixed dict.

Each job module is imported by module object (not `from <module> import run_pm`)
because several of them define a function with the same name `run_pm`, which
would otherwise silently collide.

Merges job modules across every jobs/<category>_jobs/ directory into one flat
JOB_REGISTRY, so callers (slack_commands.py) only need one import and one
resolve_job() regardless of which category a job lives under.
"""
from typing import Callable, Dict

from jobs.hpc_jobs import run_pm as _run_pm
from jobs.hpc_jobs import run_roicat as _run_roicat
from jobs.hpc_jobs import run_pm_roicat as _run_pm_roicat
from jobs.hpc_jobs import run_pm_holo_ai228 as _run_pm_holo_ai228
from jobs.hpc_jobs import run_pm_holo_ai230 as _run_pm_holo_ai230
from jobs.hpc_jobs import run_pm_visual_ai228 as _run_pm_visual_ai228
from jobs.hpc_jobs import run_pm_visual_ai230 as _run_pm_visual_ai230
from jobs.hpc_jobs import run_pm_visual_mesoscan_np2 as _run_pm_visual_mesoscan_np2
from jobs.hpc_jobs import run_local_example as _run_local_example

# Add `from jobs.cayde_jobs import <module> as _<alias>` lines here as job
# scripts are added under jobs/cayde_jobs/, then register them below
# alongside the hpc_jobs entries.

JOB_REGISTRY: Dict[str, Callable] = {
    "pm": _run_pm.run_pm,
    "roicat": _run_roicat.run_roicat,
    "pm_roicat": _run_pm_roicat.run_pm_roicat,
    "pm_holo_ai228": _run_pm_holo_ai228.run_pm,
    "pm_holo_ai230": _run_pm_holo_ai230.run_pm,
    "pm_visual_ai228": _run_pm_visual_ai228.run_pm,
    "pm_visual_ai230": _run_pm_visual_ai230.run_pm,
    "pm_visual_mesoscan_np2": _run_pm_visual_mesoscan_np2.run_pm,
    "echo": _run_local_example.run_local_example,
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
        return JOB_REGISTRY[name]
    except KeyError:
        raise UnknownJobError(name) from None
