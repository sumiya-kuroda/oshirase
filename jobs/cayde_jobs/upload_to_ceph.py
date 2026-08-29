import shutil
import sys
from pathlib import Path

from datashuttle import DataShuttle
from oshirase.slurm_helper import run_local_and_notify, SuccessCheck

CHECK = SuccessCheck(
    stream="stdout",
    success_pattern="successful",
    success_message="✅ [cayde] uploading derivatives to ceph completed successfully!",
    failure_message="❌ [cayde] uploading derivatives to ceph failed. Check the log: {log_path}",
)


def _upload(sub_names: str, ses_names: str):
    project = DataShuttle("SuKu_20250111_FeedbackRF")
    project.upload_custom(
        top_level_folder="derivatives",
        sub_names=sub_names,
        ses_names=ses_names,
        datatype="funcimg",
    )


def _delete_local(sub_names: str, ses_names: str):
    project = DataShuttle("SuKu_20250111_FeedbackRF")
    local = Path(project.cfg["local_path"])          # print once to confirm it's right
    glob_sub = sub_names.replace("@*@", "*")
    glob_ses = ses_names.replace("@*@", "*")
    targets = list((local / "derivatives").glob(f"{glob_sub}/{glob_ses}/funcimg"))
    for t in targets:
        print("deleting", t)
        shutil.rmtree(t)
    if not targets:
        print("nothing matched — check the path / wildcards")


def upload_to_ceph(
    sub_names: str = "sub-XX",
    ses_names: str = "ses-XXX_@*@",
    delete_local: bool = True,
):
    result = run_local_and_notify(
        fn=_upload,
        args=(sub_names, ses_names),
        check=CHECK,
        log_path="run_upload_to_ceph.log",
        detach=not delete_local,
    )
    if delete_local and result:      # only deletes after CHECK passed
        _delete_local(sub_names, ses_names)
    return result


if __name__ == "__main__":
    upload_to_ceph(*sys.argv[1:])