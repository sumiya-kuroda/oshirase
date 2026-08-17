# cayde_jobs

Job scripts for this category go here, following the same pattern as
`jobs/hpc_jobs/`:

- Each script defines a callable job function (see
  `jobs/hpc_jobs/run_local_example.py` for the minimal shape).
- Register it in [jobs/registry.py](../registry.py): add an
  `from jobs.cayde_jobs import <module> as _<alias>` import, then add a
  `"<job_name>": _<alias>.<function>` entry to `JOB_REGISTRY`.

Once registered, the job is runnable both via the `/oshirase-run <job_name>`
Slack command and the `oshirase-run <job_name>` CLI — no other code changes
needed.
