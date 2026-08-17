"""Example: run an arbitrary (non-SLURM) command locally and get a Slack
notification when it finishes. Detaches from the terminal by default, so you
can run `python run_local_example.py` and close the shell immediately.

Swap `argv`/`check` below for your own command and success pattern, or pass
`fn=my_function, args=(...), kwargs={...}` instead of `argv` to run a plain
Python callable in-process rather than a shell command.
"""
from oshirase.slurm_helper import run_local_and_notify, SuccessCheck

# Slack message for this job lives here, next to the job that produces it.
EXAMPLE_CHECK = SuccessCheck(
    stream="stdout",
    success_pattern="Done",
    success_message="✅ run_local_example job {job_id} completed successfully!",
    failure_message="❌ run_local_example job {job_id} failed. Check the log: {log_path}",
)

def run_local_example():
    return run_local_and_notify(
        argv=["python", "-c", "print('Done')"],
        check=EXAMPLE_CHECK,
        log_path="run_local_example.log",
    )

if __name__ == '__main__':
    run_local_example()
