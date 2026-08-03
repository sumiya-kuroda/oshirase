from oshirase.slurm_helper import SlurmJobRunner, SuccessCheck

CONFIG_PATH = "/ceph/mrsic_flogel/public/projects/SuKu_20250111_FeedbackRF/configPhotonMosaicVisualInference_holo_ai228.yaml"

PM_CHECK = SuccessCheck(
    stream="stderr",
    success_pattern="successfully",
    success_message="✅ photon-mosaic (holo ai228) job {job_id} completed successfully!",
    failure_message="❌ photon-mosaic (holo ai228) job {job_id} failed. Check the log",
)

def run_pm():
    # Run photon-mosaic
    runner = SlurmJobRunner(
        folder="../.submitit",
        job_name="pm",
        partition="gpu_lowp",
        time="72:00:00",
        mem_gb=4,
    )

    job_pm = runner.submit_command(["photon-mosaic", "--config", CONFIG_PATH, "--jobs", "10", "--latency-wait", "30", "--rerun-incomplete"])
    print("Submitted job_id:", job_pm.job_id)
    SlurmJobRunner.monitor_and_notify(job_pm, check=PM_CHECK)

    return job_pm

if __name__ == '__main__':
    run_pm()
