###
 # Creates a chain workflow
 #   1
 #   |
 #   2
 #   |
 #   ...
 #   |
 #   N
 ##

from datetime import datetime
from enum import Enum
import argparse
import getpass
import json
import math
import pathlib

# commands
class Commands(Enum):
    Sleep = "/bin/sleep"
    WfBench = "/home/cc/wfcommons/wfcommons/wfbench/wfbench.py"

# method to check minimum num_tasks
def check_num_tasks(num_tasks):
    if int(num_tasks) < 1:
        raise argparse.ArgumentTypeError("must be >= 1")

    return int(num_tasks)

# arguments
parser = argparse.ArgumentParser(description="Creates a chain workflow")
parser.add_argument("--command", type=str, default="Sleep", choices=[i.name for i in Commands], help="Command to use for this workflow (default: Sleep)")
parser.add_argument("--save_dir", type=pathlib.Path, default="./workflow", help="Folder to save the workflow JSON instance and input data files (default: ./workflow)")
parser.add_argument("--num_tasks", type=check_num_tasks, default=10, help="Total number of tasks in the workflow (default: 10; minimum: 1)")
parser.add_argument("--seconds", type=int, default=30, help="Number of seconds to sleep (default: 30)")
parser.add_argument("--cpu_work", type=int, default=1000, help="CPU work per workflow task (default: 1000)")
parser.add_argument("--percent_cpu", type=float, default=0.6, help="The percentage of CPU threads (default: 0.6; range: 0.0 - 1.0)")
parser.add_argument("--data", type=int, default=10000, help="Total workflow data footprint in MB (default: 10000)")
parser.add_argument("--lock_files_folder", type=pathlib.Path, default="/var/lib/condor/execute", help="Folder containing lock files for CPU affinity (default: /var/lib/condor/execute)")
parser.add_argument("--pegasus_file", type=pathlib.Path, default="./workflow.py", help="File to save the Pegasus python script (default: ./workflow.py)")
args = parser.parse_args()

# method to get task arguments
def get_arguments(i):
    arguments = []

    if args.command == "Sleep":
        arguments.append(f"\"{args.seconds}\"")
    elif args.command == "WfBench":
        arguments = [
            "chain_" + str(i).zfill(8),
            "--percent-cpu " + str(args.percent_cpu),
            "--cpu-work " + str(args.cpu_work),
            "--path-lock " + str(args.lock_files_folder) + "/cores.txt.lock",
            "--path-cores " + str(args.lock_files_folder) + "/cores.txt",
            "--out {'chain_" + str(i).zfill(8) + "_output.txt': " + str(math.ceil(args.data / args.num_tasks)) + "}"
        ]

        if i == 1:
            arguments.append("chain_" + str(i).zfill(8) + "_input.txt")
        else:
            arguments.append("chain_" + str(i - 1).zfill(8) + "_output.txt")

    return arguments

# method to get task parents
def get_parents(i):
    parents = []

    if i > 1:
        parents.append("chain_" + str(i - 1).zfill(8))

    return parents

# method to get task children
def get_children(i):
    children = []

    if i < args.num_tasks:
        children.append("chain_" + str(i + 1).zfill(8))

    return children

# method to get task files
def get_files(i):
    files = []

    if args.command == "WfBench":
        if i == 1:
            files.append({
                "link": "input",
                "name": "chain_" + str(i).zfill(8) + "_input.txt",
                "size": math.ceil(1000 * args.data / args.num_tasks)  # KB
            })
        else:
            files.append({
                "link": "input",
                "name": "chain_" + str(i - 1).zfill(8) + "_output.txt",
                "size": math.ceil(1000 * args.data / args.num_tasks)  # KB
            })

        files.append({
            "link": "output",
            "name": "chain_" + str(i).zfill(8) + "_output.txt",
            "size": math.ceil(1000 * args.data / args.num_tasks)  # KB
        })

    return files

# create workflow
workflow = {
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
for i in range(1, args.num_tasks + 1):
    # create task
    task = {
        "name": "chain_" + str(i).zfill(8),
        "id": str(i).zfill(8),
        "type": "compute",
        "command": {
            "program": Commands[args.command].value,
            "arguments": get_arguments(i)
        },
        "parents": get_parents(i),
        "children": get_children(i),
        "files": get_files(i),
        "cores": 1
    }

    # add task to workflow
    workflow["workflow"]["tasks"].append(task)

# debug
print(json.dumps(workflow, indent=4))
