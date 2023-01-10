#!/usr/bin/env python3

import json
import os
import sys
import pathlib
import shutil
import subprocess
import tarfile

from datetime import datetime
from wfcommons import SeismologyRecipe, MontageRecipe, GenomeRecipe, SoykbRecipe
from wfcommons.wfbench import WorkflowBenchmark
from wfcommons.wfbench.translator import PegasusTranslator

machine = sys.argv[1]

tar_dir = pathlib.Path("./runs")
tar_dir.mkdir(parents=True, exist_ok=True)

# recipes
for recipe in [SeismologyRecipe]:
    for cpu_work in [250, 500, 1000, 10000, 20000]:
        for num_tasks in [250, 500, 1000]:
            for data_footprint in [10, 100, 1000, 10000]:
                percent_cpu = 0.6
                # work dir
                work_dir = pathlib.Path("./wfbench-workflow")
                work_dir.mkdir(exist_ok=False)

                lock_files_folder = pathlib.Path("/var/lib/condor/execute")
                os.system(f"sudo chmod 777 {lock_files_folder}")

                # create benchmark
                benchmark = WorkflowBenchmark(recipe=recipe, num_tasks=num_tasks)
                benchmark_path = benchmark.create_benchmark(save_dir=work_dir,
                                                            cpu_work=cpu_work,
                                                            data=data_footprint,
                                                            percent_cpu=percent_cpu,
                                                            lock_files_folder=lock_files_folder)

                # generate pegasus workflow
                translator = PegasusTranslator(benchmark.workflow)
                translator.translate(work_dir.joinpath("pegasus-workflow.py"))

                # submit workflow
                proc = subprocess.Popen(["bash", "run-workflow.sh"])
                proc.wait()

                # compress run dir
                for dagman_path in work_dir.joinpath("work/cc/pegasus").glob("**/*.dag.dagman.out"):
                    run_dir = dagman_path.parent
                    app = recipe.__name__.replace('Recipe', '')
                    tar_file = tar_dir.joinpath(f"{app.lower()}-{num_tasks}-{cpu_work}-{data_footprint}-{percent_cpu}-"
                                                f"{machine}.tar.gz")
                    with tarfile.open(tar_file, "w:gz") as tar:
                        tar.add(run_dir, arcname=run_dir.name)

                    # cleanup
                    shutil.rmtree(work_dir)
                    break
