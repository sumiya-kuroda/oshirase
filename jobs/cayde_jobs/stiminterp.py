from oshirase.slurm_helper import run_local_and_notify, SuccessCheck

CHECK = SuccessCheck(
    stream="stdout",
    success_pattern="successfully",
    success_message="✅ [cayde] photon-mosaic-pipeline preprocessing - stiminterp completed successfully!",
    failure_message="❌ [cayde] photon-mosaic-pipeline preprocessing - stiminterp failed. Check the log: {log_path}",
)

def run_stiminterp():
    return run_local_and_notify(
        argv=["photon-mosaic-pipeline", "--config=/mnt/ceph/public/projects/SuKu_20250111_FeedbackRF/configPhotonMosaicVisualInference_stiminterp.yaml", "all", "--until", "preprocessing"],
        check=CHECK,
        log_path="run_stiminterp.log",
    )

if __name__ == '__main__':
    run_stiminterp()
