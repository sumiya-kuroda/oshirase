import subprocess
from pathlib import Path

from oshirase.slurm_helper import SlurmJobRunner, SuccessCheck

PROJ = Path("/ceph/mrsic_flogel/public/projects/SuKu_20250111_FeedbackRF")

# Full-resolution StitchIt output: one folder of 2D section tifs per channel.
# Voxel size (z, y, x) in µm: 5 µm optical planes (40 µm slices / 8 planes),
# 2.23 µm stitched pixels (StitchingParameters.VoxelSize in the recipe).
VOXEL_SIZE = ("5", "2.23", "2.23")


def _channel_dir(in_dir: Path, chan: int) -> Path:
    d = in_dir / str(chan)
    if not d.is_dir() or not any(d.glob("*.tif")):
        raise FileNotFoundError(f"No tifs found in {d}")
    return d


def _run_brainreg(sub: str, ses: str, atlas: str):
    in_dir = PROJ / "rawdata" / sub / ses / "anat" / "stitchedImages_100"
    out_dir = PROJ / "derivatives" / sub / ses / "anat" / "brainreg"

    red = _channel_dir(in_dir, 2)    # registration channel
    green = _channel_dir(in_dir, 3)  # extra channel, transformed only
    blue = _channel_dir(in_dir, 4)   # extra channel, transformed only
    print("red:  ", red)
    print("green:", green)
    print("blue: ", blue)

    out_dir.mkdir(parents=True, exist_ok=True)

    # The outer oshirase_job.sh activates photon-mosaic-pipeline, so run brainreg
    # inside its own conda env.
    subprocess.run(
        [
            "conda", "run", "--no-capture-output", "-n", "brainreg",
            "brainreg", str(red), str(out_dir),
            "-v", *VOXEL_SIZE,
            "--orientation", "psl",
            "--atlas", atlas,
            "-a", str(green), str(blue),
            "--n-free-cpus", "0",
        ],
        check=True,
    )
    print("Done:", out_dir)


def run_brainreg(sub: str = "sub-XXXXXXX", ses: str = "ses-XXX", atlas: str = "allen_mouse_25um"):
    # Run brainreg (niftyreg is CPU-only, no GPU needed).
    # Switch atlas to allen_mouse_10um for full-res (more RAM/time).
    check = SuccessCheck(
        stream="stderr",
        success_pattern="successful",
        success_message=f"✅ brainreg job {{job_id}} ({sub}/{ses}) completed successfully!",
        failure_message=f"❌ brainreg job {{job_id}} ({sub}/{ses}) failed. Check the log",
    )

    runner = SlurmJobRunner(
        folder="../.submitit",
        job_name="brainreg",
        partition="cpu",
        time="24:00:00",  # reads ~70 GB/channel of full-res tifs from ceph
        mem_gb=120,  # planes are downsampled to atlas res as they're loaded
        cpus_per_task=16,  # threads for niftyreg
        nodes=1,
        ntasks_per_node=1,
    )

    job_brainreg = runner.submit_callable(_run_brainreg, sub, ses, atlas)
    print("Submitted job_id:", job_brainreg.job_id)
    SlurmJobRunner.monitor_and_notify(job_brainreg, check=check)

    return job_brainreg


if __name__ == '__main__':
    import sys
    run_brainreg(*sys.argv[1:])
