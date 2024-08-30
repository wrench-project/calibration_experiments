#!/usr/bin/python3
import glob
import json


def get_workflow_names():
    files = glob.glob("*.json")
    workflow_names = set()
    for file in files:
        workflow_names.add(file.split("-")[0])
    workflow_names = list(workflow_names)
    return sorted(workflow_names)


def get_workflow_num_tasks(workflow_name):
    files = glob.glob(workflow_name + "-*.json")
    num_tasks = set()
    for file in files:
        num_tasks.add(int(file.split("-")[1]))
    num_tasks = list(num_tasks)
    return sorted(num_tasks)


def get_all_others(workflow_name, num_tasks):
    files = glob.glob(workflow_name + "-" + str(num_tasks) + "*.json")
    cpu_works = set()
    data_footprints = set()
    architectures = set()
    num_compute_nodes = set()
    for file in files:
        cpu_works.add(int(file.split("-")[2]))
        data_footprints.add(int(file.split("-")[4]))
        architectures.add(file.split("-")[5])
        num_compute_nodes.add(int(file.split("-")[6]))
    return sorted(list(cpu_works)), sorted(list(data_footprints)), sorted(list(architectures)), sorted(list(num_compute_nodes))


def get_makespans(files):
    makespans = []
    for file in files:
        makespans.append(json.load(open(file))["workflow"]["execution"]["makespanInSeconds"])
    return makespans


def mean(l):
    return sum(l) / len(l)

def process_workflow(workflow_name):
    num_tasks = get_workflow_num_tasks(workflow_name)

    print(workflow_name + ":")

    do_compute_node_sanity = False
    do_cpu_work_sanity = False
    do_data_footprint_sanity = True

    # Looking at CPU work sanity
    if do_cpu_work_sanity:
        num_sanity = 0
        num_insanity = 0
        for num_task in num_tasks:
            cpu_works, data_footprints, architectures, num_compute_nodes = get_all_others(workflow_name, num_tasks)
            for architecture in architectures:
                # print(f"{workflow_name}:{num_task}:{architecture}")

                for data_footprint in data_footprints:
                    for num_nodes in num_compute_nodes:
                        for i in range(0, len(cpu_works) - 1):
                            files_curr = glob.glob(f"{workflow_name}-{num_task}-{cpu_works[i]}-0.6"
                                                   f"-{data_footprint}-{architecture}-{num_nodes}-*.json")
                            makespans_curr = sorted(get_makespans(files_curr))
                            if not makespans_curr:
                                continue
                            try:
                                files_next = glob.glob(f"{workflow_name}-{num_task}-{cpu_works[i + 1]}-0.6"
                                                       f"-{data_footprint}-{architecture}-{num_nodes}-*.json")
                            except:
                                continue
                            makespans_next = sorted(get_makespans(files_next))
                            if not makespans_next:
                                continue

                            # print(f"{makespans_curr}  {makespans_next}")
                            # if max(makespans_curr) > min(makespans_next):
                            if mean(makespans_curr) > mean(makespans_next):
                                num_insanity += 1
                            else:
                                num_sanity += 1
        print(f"  CPU work sanity={num_sanity}  insanity={num_insanity}")

    # Looking at data footprint sanity
    if do_data_footprint_sanity:
        num_sanity = 0
        num_insanity = 0
        for num_task in num_tasks:
            cpu_works, data_footprints, architectures, num_compute_nodes = get_all_others(workflow_name, num_tasks)
            for architecture in architectures:
                # print(f"{workflow_name}:{num_task}:{architecture}")

                for cpu_work in cpu_works:
                    for num_nodes in num_compute_nodes:
                        for i in range(0, len(data_footprints) - 1):
                            files_curr = glob.glob(f"{workflow_name}-{num_task}-{cpu_work}-0.6"
                                                   f"-{data_footprints[i]}-{architecture}-{num_nodes}-*.json")
                            makespans_curr = sorted(get_makespans(files_curr))
                            if not makespans_curr:
                                continue
                            try:
                                files_next = glob.glob(f"{workflow_name}-{num_task}-{cpu_work}-0.6"
                                                       f"-{data_footprints[i+1]}-{architecture}-{num_nodes}-*.json")
                            except:
                                continue
                            makespans_next = sorted(get_makespans(files_next))
                            if not makespans_next:
                                continue

                            # print(f"{makespans_curr}  {makespans_next}")
                            # if max(makespans_curr) > min(makespans_next):
                            if mean(makespans_curr) > mean(makespans_next):
                                num_insanity += 1
                            else:
                                num_sanity += 1
        print(f"  Data footprint sanity={num_sanity}  insanity={num_insanity}")

    if do_compute_node_sanity:
        # Looking at compute node sanity
        num_sanity = 0
        num_insanity = 0
        for num_task in num_tasks:
            cpu_works, data_footprints, architectures, num_compute_nodes = get_all_others(workflow_name, num_tasks)
            for architecture in architectures:
                # print(f"{workflow_name}:{num_task}:{architecture}")

                for cpu_work in cpu_works:
                    for data_footprint in data_footprints:
                        for i in range(0, len(num_compute_nodes) - 1):
                            files_curr = glob.glob(f"{workflow_name}-{num_task}-{cpu_work}-0.6"
                                                   f"-{data_footprint}-{architecture}-{num_compute_nodes[i]}-*.json")
                            makespans_curr = sorted(get_makespans(files_curr))
                            if not makespans_curr:
                                continue
                            try:
                                files_next = glob.glob(f"{workflow_name}-{num_task}-{cpu_work}-0.6"
                                                       f"-{data_footprint}-{architecture}-{num_compute_nodes[i+1]}-*.json")
                            except:
                                continue
                            makespans_next = sorted(get_makespans(files_next))
                            if not makespans_next:
                                continue

                            # print(f"{makespans_curr}  {makespans_next}")
                            # if min(makespans_curr) < max(makespans_next):
                            if mean(makespans_curr) < mean(makespans_next):
                                num_insanity += 1
                            else:
                                num_sanity += 1
        print(f"  Compute node sanity={num_sanity}  insanity={num_insanity}")


def main():
    workflow_names = get_workflow_names()
    for workflow_name in workflow_names:
        process_workflow(workflow_name)


if __name__ == "__main__":
    main()
