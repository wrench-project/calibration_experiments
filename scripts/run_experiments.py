#!/usr/bin/env python3

import subprocess
import tarfile
import os
import time
import sys
import shutil
from datetime import datetime
import getpass
import json
import math
import pathlib
from argparse import ArgumentParser

from wfcommons import SeismologyRecipe, MontageRecipe, GenomeRecipe, SoykbRecipe, CyclesRecipe, EpigenomicsRecipe, \
    BwaRecipe
from wfcommons.wfbench import WorkflowBenchmark
from wfcommons.wfbench.translator import PegasusTranslator
from wfcommons.wfinstances import PegasusLogsParser


architectures = ["haswell", "skylake", "cascadelake"]
workflow_recipe_map = {"seismology": SeismologyRecipe,
                       "montage": MontageRecipe,
                       "genome": GenomeRecipe,
                       "soykb": SoykbRecipe,
                       "cycles": CyclesRecipe,
                       "epigenomics": EpigenomicsRecipe,
                       "bwa": BwaRecipe,
                       "chain": None,
                       "forkjoin": None}


def parse_arguments(args):
    parser = ArgumentParser()
    parser.add_argument("-a", "--architecture", required=True, choices=architectures,
                        action='append',
                        help="<" + "|".join(architectures) + "> (only one)")

    parser.add_argument("-w", "--workflow", required=True, choices=workflow_recipe_map.keys(),
                        action='append',
                        help="<" + "|".join(workflow_recipe_map.keys()) + "> (only one)")

    parser.add_argument("-n", "--num_compute_nodes", type=int, required=True,
                        action='append',
                        help="<# of compute nodes> (only one)")

    parser.add_argument("-t", "--num_trials", type=int, required=True,
                        action='append',
                        help="<# of trials> (only one)")

    parser.add_argument("-c", "--cpu_work", type=int, required=True,
                        nargs='+',
                        action='extend',
                        help="<CPU work value>")

    parser.add_argument("-f", "--cpu_fraction", type=float, required=True,
                        nargs='+',
                        action='extend',
                        help="<CPU fraction>")

    parser.add_argument("-d", "--data_footprint", type=int, required=True,
                        nargs='+',
                        action='extend',
                        help="<data footprint in bytes>")

    parser.add_argument("-o", "--output_dir", required=True,
                        action='append',
                        help="<output dir> (only one)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--workflow_size_factor", required=False,
                       type=float,
                       nargs='+',
                       action='extend',
                       help="<factor by which to scale the min #task, which defines the workflow size> (only for "
                            "WfChef-generated workflows)")
    group.add_argument("-S", "--workflow_size", required=False,
                       type=int,
                       nargs='+',
                       action='extend',
                       help="<#tasks in workflow> (only for chain/forkjoin workflows)")

    parser.add_argument("-p", "--print_workflow_sizes",
                        action='store_true',
                        help="<print the actual workflow sizes>")

    parsed_args = parser.parse_args(args[1:])

    # Architecture
    architecture_values = parsed_args.architecture
    if len(architecture_values) > 1:
        sys.stderr.write("Error: a single -a/--architecture argument should be specified\n")
        sys.exit(1)

    # Workflow
    workflow_values = parsed_args.workflow
    if len(workflow_values) > 1:
        sys.stderr.write("Error: a single -w/--workflow argument should be specified\n")
        sys.exit(1)

    # Num compute nodes
    num_compute_nodes_values = parsed_args.num_compute_nodes
    if len(num_compute_nodes_values) > 1:
        sys.stderr.write("Error: a single -n/--num_compute_nodes argument should be specified\n")
        sys.exit(1)
    if num_compute_nodes_values[0] < 1:
        sys.stderr.write("Error: invalid -n/--num_compute_nodes value\n")
        sys.exit(1)

    # Num trials
    num_trials_values = parsed_args.num_trials
    if len(num_trials_values) > 1:
        sys.stderr.write("Error: a single -n/--num_trials argument should be specified\n")
        sys.exit(1)
    if num_trials_values[0] < 1:
        sys.stderr.write("Error: invalid -n/--num_trials value\n")
        sys.exit(1)

    # Output dir
    output_dir_values = parsed_args.output_dir
    if len(output_dir_values) > 1:
        sys.stderr.write("Error: a single -o/--output_dir argument should be specified\n")
        sys.exit(1)
    if not os.path.isdir(output_dir_values[0]):
        sys.stderr.write("Error: output directory '" + output_dir_values[0] + "' does not exist\n")
        sys.exit(1)

    # CPU works
    cpu_work_values = sorted(list(set(parsed_args.cpu_work)))

    # CPU fractions
    cpu_fraction_values = sorted(list(set(parsed_args.cpu_fraction)))
    for f in cpu_fraction_values:
        if (f < 0.0) or (f > 1.0):
            sys.stderr.write("Error: invalid CPU fraction value '" + f + "'\n")
            sys.exit(1)

    # Data footprints
    data_footprint_values = sorted(list(set(parsed_args.data_footprint)))

    # Workflow size factors / sizes
    workflow_size_factor_values = parsed_args.workflow_size_factor
    workflow_size_values = parsed_args.workflow_size
    if workflow_size_factor_values:
        workflow_size_factor_values = sorted(list(set(workflow_size_factor_values)))
        if workflow_recipe_map[workflow_values[0]] is None:
            sys.stderr.write("Error: Cannot use -s/--workflow_size_factor with a non-WfBench-generated workflow\n")
            sys.exit(1)
    if workflow_size_values:
        workflow_size_values = sorted(list(set(workflow_size_values)))
        if workflow_recipe_map[workflow_values[0]] is not None:
            sys.stderr.write("Error: Cannot use -s/--workflow_size_factor with a WfBench-generated workflow\n")
            sys.exit(1)
        if workflow_values[0] == "forkjoin":
            if min(workflow_size_values) < 3:
                sys.stderr.write("Error: Cannot use create a forkjoin workflow with less than 4 tasks\n")
                sys.exit(1)

    # Print workflow sizes
    print_workflow_sizes_value = parsed_args.print_workflow_sizes

    # Return argument dict
    config = {"architecture": architecture_values[0],
              "workflow": workflow_values[0],
              "num_compute_nodes": num_compute_nodes_values[0],
              "num_trials": num_trials_values[0],
              "output_dir": output_dir_values[0],
              "cpu_work": cpu_work_values,
              "cpu_fraction": cpu_fraction_values,
              "data_footprint": data_footprint_values,
              "workflow_size_factor": workflow_size_factor_values,
              "workflow_size": workflow_size_values,
              "print_workflow_sizes": print_workflow_sizes_value}
    return config


def get_min_workflow_size(workflow):
    recipe = workflow_recipe_map[workflow]
    for s in range(0, 1000):
        benchmark = WorkflowBenchmark(recipe=recipe, num_tasks=s)
        try:
            path = benchmark.create_benchmark(pathlib.Path("/tmp/"),
                                              cpu_work=0,
                                              data=0,
                                              percent_cpu=1.0)
            with open(path, 'r') as f:
                return s
        except Exception:
            pass


def compute_workflow_sizes(workflow, size_factors):
    recipe = workflow_recipe_map[workflow]
    min_size = get_min_workflow_size(workflow)
    sizes = {}
    for factor in size_factors:
        desired_size = int(min_size * factor)
        benchmark = WorkflowBenchmark(recipe=recipe, num_tasks=desired_size)
        path = benchmark.create_benchmark(pathlib.Path("/tmp/"),
                                          cpu_work=0,
                                          data=0,
                                          percent_cpu=1.0)
        with open(path, 'r') as f:
            data = json.load(f)
            sizes[desired_size] = len(data["workflow"]["tasks"])

    return sizes


def create_chain_workflow(desired_num_tasks, cpu_fraction, cpu_work, data_footprint, lock_files_folder, work_dir):

    def get_arguments(task_index):
        arguments = [
            "chain_" + str(i).zfill(8),
            "--percent-cpu " + str(cpu_fraction),
            "--cpu-work " + str(cpu_work),
            "--path-lock " + str(lock_files_folder) + "/cores.txt.lock",
            "--path-cores " + str(lock_files_folder) + "/cores.txt",
            "--out {'chain_" + str(task_index).zfill(8) + "_output.txt': " +
            str(file_size_in_bytes) + "}"
        ]

        if task_index == 1:
            arguments.append("chain_" + str(task_index).zfill(8) + "_input.txt")
        else:
            arguments.append("chain_" + str(task_index - 1).zfill(8) + "_output.txt")

        return arguments

    # method to get task parents
    def get_parents(task_index):
        parents = []
        if task_index > 1:
            parents.append("chain_" + str(task_index - 1).zfill(8))
        return parents

    # method to get task children
    def get_children(task_index):
        children = []
        if task_index < desired_num_tasks:
            children.append("chain_" + str(task_index + 1).zfill(8))
        return children

    # method to get task files
    def get_files(task_index):
        files = []

        if task_index == 1:
            files.append({
                "link": "input",
                "name": "chain_" + str(task_index).zfill(8) + "_input.txt",
                "size": file_size_in_kilobytes
            })
        else:
            files.append({
                "link": "input",
                "name": "chain_" + str(task_index - 1).zfill(8) + "_output.txt",
                "size": file_size_in_kilobytes
            })

        files.append({
            "link": "output",
            "name": "chain_" + str(task_index).zfill(8) + "_output.txt",
            "size": file_size_in_kilobytes
        })

        return files

    # create workflow
    file_size_in_bytes = math.ceil(data_footprint / (desired_num_tasks + 1))
    file_size_in_kilobytes = math.ceil(file_size_in_bytes / 1000)

    workflow_json = {
        "name": "Chain-Benchmark",
        "description": "Instance generated with WfCommons - https://wfcommons.org",
        "createdAt": str(datetime.utcnow().isoformat()),
        "schemaVersion": "1.3",
        "author": {
            "name": str(getpass.getuser()),
            "email": "support@wfcommons.org"
        },
        "wms": {
            "name": "WfCommons",
            "version": "0.9-dev",
            "url": "https://docs.wfcommons.org/en/v0.9-dev/"
        },
        "workflow": {
            "executedAt": str(datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")),
            "makespan": 0,
            "tasks": []
        }
    }

    # create num_tasks tasks
    for i in range(1, desired_num_tasks + 1):
        # create task
        task = {
            "name": "chain_" + str(i).zfill(8),
            "id": str(i).zfill(8),
            "type": "compute",
            "command": {
                "program": str(pathlib.Path.home()) + "/wfcommons/wfcommons/wfbench/wfbench.py",
                "arguments": get_arguments(i)
            },
            "parents": get_parents(i),
            "children": get_children(i),
            "files": get_files(i),
            "cores": 1
        }

        # add task to workflow
        workflow_json["workflow"]["tasks"].append(task)

    file_name = f"chain-benchmark-{desired_num_tasks}.json"
    with open(str(work_dir.absolute()) + "/" + file_name, 'w') as f:
        f.write(json.dumps(workflow_json, indent=4))

    # Create input dir and file
    input_dir = work_dir.joinpath("data")
    input_dir.mkdir()
    with open(input_dir.joinpath("chain_00000001_input.txt"), 'wb') as fout:
        fout.write(os.urandom(file_size_in_bytes))

    return pathlib.Path(str(work_dir.absolute()) + "/" + file_name)


def create_forkjoin_workflow(desired_num_tasks, cpu_fraction, cpu_work, data_footprint, lock_files_folder, work_dir):
    ###
    # Creates a forkjoin workflow
    #      1
    #     /|\
    #    / | \
    #   2  3  ...
    #    \ | /
    #     \|/
    #      N
    ##

    # method to get task arguments
    def get_arguments(task_index):
        arguments = [
            "forkjoin_" + str(task_index).zfill(8),
            "--percent-cpu " + str(cpu_fraction),
            "--cpu-work " + str(cpu_work),
            "--path-lock " + str(lock_files_folder) + "/cores.txt.lock",
            "--path-cores " + str(lock_files_folder) + "/cores.txt",
            "--out {'forkjoin_" + str(task_index).zfill(8) + "_output.txt': " + str(
                str(file_size_in_bytes)) + "}"
        ]
        if task_index == 1:
            arguments.append("forkjoin_" + str(task_index).zfill(8) + "_input.txt")
        elif task_index in range(2, desired_num_tasks):
            arguments.append("forkjoin_" + str(1).zfill(8) + "_output.txt")
        elif task_index == desired_num_tasks:
            for j in range(2, desired_num_tasks):
                arguments.append("forkjoin_" + str(j).zfill(8) + "_output.txt")

        return arguments

    # method to get task parents
    def get_parents(task_index):
        parents = []

        if task_index == desired_num_tasks:
            for j in range(2, desired_num_tasks):
                parents.append("forkjoin_" + str(j).zfill(8))
        elif task_index in range(2, desired_num_tasks):
            parents.append("forkjoin_" + str(1).zfill(8))

        return parents

    # method to get task children
    def get_children(task_index):
        children = []

        if task_index == 1:
            for j in range(2, desired_num_tasks):
                children.append("forkjoin_" + str(j).zfill(8))
        elif task_index in range(2, desired_num_tasks):
            children.append("forkjoin_" + str(desired_num_tasks).zfill(8))

        return children

    # method to get task files
    def get_files(task_index):
        files = []

        if task_index == 1:
            files.append({
                "link": "input",
                "name": "forkjoin_" + str(task_index).zfill(8) + "_input.txt",
                "size": file_size_in_kilobytes
            })
        elif task_index in range(2, desired_num_tasks):
            files.append({
                "link": "input",
                "name": "forkjoin_" + str(1).zfill(8) + "_output.txt",
                "size": file_size_in_kilobytes
            })
        elif task_index == desired_num_tasks:
            for j in range(2, desired_num_tasks):
                files.append({
                    "link": "input",
                    "name": "forkjoin_" + str(j).zfill(8) + "_output.txt",
                    "size": file_size_in_kilobytes
                })

        files.append({
            "link": "output",
            "name": "forkjoin_" + str(task_index).zfill(8) + "_output.txt",
            "size": file_size_in_kilobytes
        })

        return files

    # create workflow
    if desired_num_tasks < 4:
        raise Exception("Cannot create a forkjoin benchmark with fewer than 4 tasks")

    file_size_in_bytes = math.ceil(data_footprint / (desired_num_tasks + 1))
    file_size_in_kilobytes = math.ceil(file_size_in_bytes / 1000)

    workflow_json = {
        "name": "Forkjoin-Benchmark",
        "description": "Instance generated with WfCommons - https://wfcommons.org",
        "createdAt": str(datetime.utcnow().isoformat()),
        "schemaVersion": "1.3",
        "author": {
            "name": str(getpass.getuser()),
            "email": "support@wfcommons.org"
        },
        "wms": {
            "name": "WfCommons",
            "version": "0.9-dev",
            "url": "https://docs.wfcommons.org/en/v0.9-dev/"
        },
        "workflow": {
            "executedAt": str(datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")),
            "makespan": 0,
            "tasks": []
        }
    }

    # create num_tasks tasks
    for i in range(1, desired_num_tasks + 1):
        # create task
        task = {
            "name": "forkjoin_" + str(i).zfill(8),
            "id": str(i).zfill(8),
            "type": "compute",
            "command": {
                "program": str(pathlib.Path.home()) + "/wfcommons/wfcommons/wfbench/wfbench.py",
                "arguments": get_arguments(i)
            },
            "parents": get_parents(i),
            "children": get_children(i),
            "files": get_files(i),
            "cores": 1
        }

        # add task to workflow
        workflow_json["workflow"]["tasks"].append(task)

    # Create input dir and file
    input_dir = work_dir.joinpath("data")
    input_dir.mkdir()
    with open(input_dir.joinpath("forkjoin_00000001_input.txt"), 'wb') as fout:
        fout.write(os.urandom(file_size_in_bytes))

    file_name = f"forkjoin-benchmark-{desired_num_tasks}.json"
    with open(str(work_dir.absolute()) + "/" + file_name, 'w') as f:
        f.write(json.dumps(workflow_json, indent=4))

    return pathlib.Path(str(work_dir.absolute()) + "/" + file_name)


def create_benchmark(work_dir, workflow, desired_num_tasks, cpu_fraction, cpu_work, data_footprint):

    lock_files_folder = pathlib.Path("/var/lib/condor/execute")
    os.system(f"sudo chmod 777 {lock_files_folder}")

    if workflow_recipe_map[workflow]:
        # create benchmark
        benchmark = WorkflowBenchmark(recipe=workflow_recipe_map[workflow], num_tasks=desired_num_tasks)
        benchmark_path = benchmark.create_benchmark(save_dir=work_dir,
                                                    cpu_work=cpu_work,
                                                    data=data_footprint,
                                                    percent_cpu=cpu_fraction,
                                                    lock_files_folder=lock_files_folder)
    else:
        # Creating the lock files (code copied from create_benchmark)
        if lock_files_folder:
            try:
                lock_files_folder.mkdir(exist_ok=True, parents=True)
                lock = lock_files_folder.joinpath("cores.txt.lock")
                cores = lock_files_folder.joinpath("cores.txt")
                with lock.open("w+"), cores.open("w+"):
                    pass
            except (FileNotFoundError, OSError) as e:
                sys.stderr.write(f"Could not find folder to create lock files: {lock_files_folder.resolve()}\n"
                                 f"You will need to create them manually: 'cores.txt.lock' and 'cores.txt'\n")

        if workflow == "chain":
            benchmark_path = create_chain_workflow(desired_num_tasks=desired_num_tasks,
                                                   cpu_fraction=cpu_fraction,
                                                   cpu_work=cpu_work,
                                                   data_footprint=data_footprint,
                                                   lock_files_folder=lock_files_folder,
                                                   work_dir=work_dir)

        elif workflow == "forkjoin":
            benchmark_path = create_forkjoin_workflow(desired_num_tasks=desired_num_tasks,
                                                      cpu_fraction=cpu_fraction,
                                                      cpu_work=cpu_work,
                                                      data_footprint=data_footprint,
                                                      lock_files_folder=lock_files_folder,
                                                      work_dir=work_dir)

        else:
            raise Exception(f"Unknown workflow {workflow}")

    return benchmark_path


def create_work_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    work_dir = pathlib.Path(path)
    work_dir.mkdir()
    return work_dir


def create_pegasus_workflow(work_dir, json_file_path):
    translator = PegasusTranslator(json_file_path)
    translator.translate(work_dir.joinpath("pegasus-workflow.py"))


def run_pegasus_workflow(work_dir, cpu_benchmark_dir):
    proc = subprocess.Popen(["bash", "run-workflow.sh", str(work_dir.absolute()), cpu_benchmark_dir])
    proc.wait()


def process_pegasus_workflow_execution(work_dir, benchmark_path, output_dir, tar_file_to_generate_prefix):

    run_dir = None
    for dagman_path in work_dir.joinpath("work/cc/pegasus").glob("**/*.dag.dagman.out"):
        run_dir = dagman_path.parent
        break

    if not run_dir:
        raise Exception("process_pegasus_workflow_execution(): Couldn't find run dir")

    # Rename the directory so that it matches the .tar.gz filename
    renamed_dir = run_dir.rename(run_dir.parent.joinpath(tar_file_to_generate_prefix))

    # Putting benchmark workflow .json in there, just for kicks
    shutil.copy(str(benchmark_path.absolute()), str(renamed_dir.absolute()))

    with tarfile.open(str(output_dir.joinpath(tar_file_to_generate_prefix+".tar.gz")), "w:gz") as tar:
        tar.add(renamed_dir, arcname=renamed_dir.name)

    # Generate observed workflow
    parser = PegasusLogsParser(submit_dir=renamed_dir, ignore_auxiliary=False)
    # generating the workflow instance object
    workflow = parser.build_workflow(tar_file_to_generate_prefix + ".json")
    # writing the workflow instance to a JSON file
    workflow_path = output_dir.joinpath(tar_file_to_generate_prefix + ".json")
    workflow.write_json(workflow_path)


def main():
    # Parse arguments
    config = parse_arguments(sys.argv)

    # Compute actual workflow sizes if only factors were provided
    if config["workflow_size_factor"] is not None:
        config["workflow_size"] = compute_workflow_sizes(config["workflow"], config["workflow_size_factor"])
    else:
        tmp = {}
        for x in config["workflow_size"]:
            tmp[x] = x
        config["workflow_size"] = tmp

    if config["print_workflow_sizes"]:
        print("----------------------")
        print("Desired \tActual")
        print("#tasks  \t#tasks")
        print("----------------------")
        for desired_size in sorted(config["workflow_size"].keys()):
            print(str(desired_size) + "\t\t" + str(config["workflow_size"][desired_size]))
        sys.exit(0)

    for desired_num_tasks in sorted(config["workflow_size"].keys()):
        for cpu_work in config["cpu_work"]:
            for cpu_fraction in config["cpu_fraction"]:
                for data_footprint in config["data_footprint"]:
                    for trial in range(0, config["num_trials"]):

                        output_dir = pathlib.Path(config["output_dir"])
                        timestamp = int(time.time())
                        tar_file_to_generate_prefix = config["workflow"] + f"-{desired_num_tasks}-{cpu_work}-{cpu_fraction}-{data_footprint}-" + \
                                                      config["architecture"] + "-" + str(config["num_compute_nodes"]) + f"-{timestamp}"

                        if output_dir.joinpath(tar_file_to_generate_prefix+".tar.gz").is_file():
                            sys.stderr.write(f"File {tar_file_to_generate_prefix}: file already exists. [SKIPPING]\n")
                            continue
                        else:
                            sys.stderr.write(f"RUNNING WORKFLOW {tar_file_to_generate_prefix}...\n")

                        # Create a fresh working directory
                        work_dir = create_work_dir(str(pathlib.Path.home())+"/wfbench-workflow")

                        # Create the benchmark workflow
                        benchmark_path = create_benchmark(work_dir, config["workflow"], desired_num_tasks,
                                                          cpu_fraction, cpu_work, data_footprint)

                        # Create Pegasus workflow
                        create_pegasus_workflow(work_dir, benchmark_path)

                        # Run the Pegasus workflow
                        run_pegasus_workflow(work_dir, str(pathlib.Path.home()))

                        # Process result
                        process_pegasus_workflow_execution(work_dir, benchmark_path, output_dir, tar_file_to_generate_prefix)

                        # Remove working directory
                        shutil.rmtree(str(work_dir.absolute()), ignore_errors=True)


if __name__ == "__main__":
    main()
