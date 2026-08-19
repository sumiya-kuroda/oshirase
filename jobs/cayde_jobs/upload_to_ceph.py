from datashuttle import DataShuttle
from oshirase.slurm_helper import run_local_and_notify, SuccessCheck

CHECK = SuccessCheck(
    stream="stdout",
    success_pattern="successfully",
    success_message="✅ [cayde] uploading derivatives to ceph completed successfully!",
    failure_message="❌ [cayde] uploading derivatives to ceph failed. Check the log: {log_path}",
)

project = DataShuttle("my_first_project")

fn_upload = project.upload_custom(
    top_level_folder="derivatives",
    sub_names="sub-XX",
    ses_names="ses-XXX_@*@",
    datatype="funcimg",
)

def upload_to_ceph():
    return run_local_and_notify(
        fn=fn_upload,
        check=CHECK,
        log_path="run_stiminterp.log",
    )

if __name__ == '__main__':
    upload_to_ceph()


project = DataShuttle("my_first_project")

project.upload_custom(
    top_level_folder="derivatives",
    sub_names="all_sub",
    ses_names="ses-001_@*@",
    datatype="funcimg",
)