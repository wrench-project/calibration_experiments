#!/bin/bash 

if [[ $# -ne 4 ]] ; then
    echo "Usage: $0 <output dir path> <num compute nodes> <architecture> <num trials>"
    echo " You may want to edit this script to change cpu work, data footprint, and/or workflow size values"
    exit 1
fi

OUTPUT_DIR=$1
NUM_COMPUTE_NODES=$2
ARCHITECTURE=$3
NUM_TRIALS=$4


# Real workflows
real_workflows="seismology montage genome soykb cycles epigenomics bwa"
for real_workflow in $real_workflows; do
        ./run_experiments.py  -a "${ARCHITECTURE}" -w "${real_workflow}" -n "${NUM_COMPUTE_NODES}" -t "${NUM_TRIALS}" -c 0 500 5000 10000 20000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o ${OUTPUT_DIR} -s 1.0 2.0 5.0 10.0
done

# Chain
./run_experiments.py  -a "${ARCHITECTURE}" -w chain -n "${NUM_COMPUTE_NODES}" -t "${NUM_TRIALS}" -c 0 500 5000 10000 20000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o ${OUTPUT_DIR} -S 1 5 10

# Forkjoin
./run_experiments.py  -a "${ARCHITECTURE}" -w forkjoin -n ${NUM_COMPUTE_NODES} -t "${NUM_TRIALS}" -c 0 500 5000 10000 20000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o ${OUTPUT_DIR} -S 10 18 25 34 50 66 100 130 200
