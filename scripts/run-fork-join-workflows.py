#!/usr/bin/env python3

import json
import os
import sys
import pathlib
import shutil
import subprocess
import tarfile

from datetime import datetime
from wfcommons.wfbench import WorkflowBenchmark
from wfcommons.wfbench.translator import PegasusTranslator

machine = sys.argv[1]
num_runs = int(sys.argv[2])

tar_dir = pathlib.Path("./runs")
tar_dir.mkdir(parents=True, exist_ok=True)


for n in range(num_runs):
    # work dir
    work_dir = pathlib.Path("./wfbench-workflow")
    work_dir.mkdir(exist_ok=False)

    input_dir = work_dir.joinpath("data")
    input_dir.mkdir()
    fileSizeInBytes = 1024 * 1024 # 1 MB
    with open(input_dir.joinpath("fork_join_00000001_input.txt"), 'wb') as fout:
        fout.write(os.urandom(fileSizeInBytes))

    workflow_path = pathlib.Path("./fork-join-workflow.json")
    translator = PegasusTranslator(workflow_path)
    translator.translate(work_dir.joinpath("pegasus-workflow.py"))

    # submit workflow
    proc = subprocess.Popen(["bash", "run-workflow.sh"])
    proc.wait()

    # compress run dir
    for dagman_path in work_dir.joinpath("work/cc/pegasus").glob("**/*.dag.dagman.out"):
        run_dir = dagman_path.parent
        tar_file = tar_dir.joinpath(f"fork-join-workflow-{machine}-{n+1:04d}.tar.gz")
        with tarfile.open(tar_file, "w:gz") as tar:
            tar.add(run_dir, arcname=run_dir.name)

        # cleanup
        shutil.rmtree(work_dir)
        break
