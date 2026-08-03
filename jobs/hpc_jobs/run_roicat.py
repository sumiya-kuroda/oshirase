import submitit
from oshirase.roicat_helpers import io, tracking_helpers
from oshirase.slurm_helper import SlurmJobRunner, SuccessCheck

# Slack message for this job lives here, next to the job that produces it, rather
# than in a shared/centralized preset.
ROICAT_CHECK = SuccessCheck(
    stream="stdout",
    success_pattern="after successful completion",
    success_message="All ROICaT jobs are done!",
    failure_message="❌ ROICaT job {job_id} failed. Check the log",
)

def run_roicat(pipeline='tracking', after_this_job: submitit.Job = None):
    # Run ROICaT
    ## Get subject ids
    config, config_path = io.load_and_process_config(reset_config=False)
    subject_paths = io.get_subject_path(config)

    jobs_roicat = []
    for subject in subject_paths:
        # A new runner is built per subject since the SLURM dependency chain
        # (afterok:<previous job id>) changes every iteration.
        runner = SlurmJobRunner(
            folder="../.submitit",
            job_name="roicat",
            partition="gpu",
            time="4:00:00",
            mem_gb=128,
            gres="gpu:1",
            cpus_per_task=1,
            gpus_per_task=1,
            nodes=1,
            ntasks_per_node=1,
            after_this_job=after_this_job,
        )

        dir_data, dir_save = tracking_helpers.constuct_roicat_params(config=config, subject=subject)

        job_roicat = runner.submit_callable(tracking_helpers.run_roicat_with_monitoring, pipeline, str(config_path), str(dir_data), str(dir_save), subject)
        if after_this_job is None:
            print("Submitted job_id:", job_roicat.job_id)
        else:
            print(
                f"Waiting for submission jobs ({after_this_job.job_id}) to complete before running collector job ({job_roicat.job_id})."
            )

        after_this_job = job_roicat
        jobs_roicat.append(job_roicat)

    SlurmJobRunner.monitor_and_notify(jobs_roicat[-1], check=ROICAT_CHECK)
    return jobs_roicat

if __name__ == '__main__':
    run_roicat()
