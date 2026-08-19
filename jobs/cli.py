"""`oshirase-run <job_name> [args...]`: run a job directly from a terminal,
without going through Slack. Extra args are passed through positionally to
the job function (e.g. `oshirase-run upload_to_ceph sub-01 ses-002`), so
jobs that don't take any just get called with none, same as before. Jobs
that want to detach do so themselves (e.g. run_local_example ->
run_local_and_notify(detach=True)), matching the behavior of running a job
script directly.
"""
import sys

from jobs.registry import resolve_job, UnknownJobError, JOB_REGISTRY


def run_cli() -> None:
    if len(sys.argv) < 2:
        print(
            f"Usage: oshirase-run <job_name> [args...]\n"
            f"Valid job names: {', '.join(sorted(JOB_REGISTRY))}",
            file=sys.stderr,
        )
        sys.exit(2)

    job_name, *job_args = sys.argv[1:]

    try:
        job = resolve_job(job_name)
    except UnknownJobError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    job(*job_args)


if __name__ == "__main__":
    run_cli()
