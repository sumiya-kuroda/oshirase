"""`oshirase-run <job_name>`: run a job directly from a terminal, without
going through Slack. Jobs that want to detach do so themselves (e.g.
run_local_example -> run_local_and_notify(detach=True)), matching the
behavior of running a job script directly.
"""
import sys

from jobs.registry import resolve_job, UnknownJobError, JOB_REGISTRY


def run_cli() -> None:
    if len(sys.argv) != 2:
        print(
            f"Usage: oshirase-run <job_name>\n"
            f"Valid job names: {', '.join(sorted(JOB_REGISTRY))}",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        job = resolve_job(sys.argv[1])
    except UnknownJobError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    job()


if __name__ == "__main__":
    run_cli()
