from datashuttle import DataShuttle
from oshirase.slurm_helper import run_local_and_notify, SuccessCheck

CHECK = SuccessCheck(
    stream="stdout",
    success_pattern="successfully",
    success_message="✅ [cayde] downloading derivatives from ceph completed successfully!",
    failure_message="❌ [cayde] downloading derivatives from ceph failed. Check the log: {log_path}",
)


def _download(sub_names: str, ses_names: str):
    project = DataShuttle("my_first_project")
    project.download_custom(
        top_level_folder="derivatives",
        sub_names=sub_names,
        ses_names=ses_names,
        datatype="funcimg",
    )


def download_from_ceph(sub_names: str = "sub-XX", ses_names: str = "ses-XXX_@*@"):
    return run_local_and_notify(
        fn=_download,
        args=(sub_names, ses_names),
        check=CHECK,
        log_path="run_download_from_ceph.log",
    )


if __name__ == '__main__':
    import sys
    download_from_ceph(*sys.argv[1:])
