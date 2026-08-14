from setuptools import setup, find_packages

setup(
    name="oshirase",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "submitit",
        "slack_sdk",
        "fpdf2",
        "numpy",
        "matplotlib",
        "pyyaml",
        "natsort",
        "swc_slack @ git+https://github.com/neuroinformatics-unit/swc-slack",
    ],
    extras_require={
        "roicat": [
            "roicat @ git+https://github.com/RichieHakim/ROICaT.git",
            "roiextractors @ git+https://github.com/RichieHakim/roiextractors",
        ],
    },
)