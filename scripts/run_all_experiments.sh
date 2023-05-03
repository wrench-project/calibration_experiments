#!/bin/bash 


if [[ $# -ne 2 ]] ; then
    echo "Usage: $0 <output dir path> <num trials>"
    echo " You may want to edit this script to change cpu work, data footprint, and/or workflow size values"
    exit 1
fi

OUTPUT_DIR=$1
NUM_TRIALS=$2

# Figure out number of compute nodes
NUM_COMPUTE_NODES=$(condor_status | grep -c slot1@)

ARCHITECTURE=""
# Figure out architecture
if [[ $(grep -c "CPU E5-2670 v3" /proc/cpuinfo) -ne "0" ]] ; then
  ARCHITECTURE="haswell"
fi
if [[ $(grep -c "Gold 6126 CPU" /proc/cpuinfo) -ne "0" ]] ; then
  ARCHITECTURE="skylake"
fi
if [[ $(grep -c "Gold 6242 CPU" /proc/cpuinfo) -ne "0" ]] ; then
  ARCHITECTURE="cascadelake"
fi

if [[ -z $ARCHITECTURE ]] ; then
  echo "Error: Cannot determine architecture. Aborting"
  exit 1
fi

echo "About to run experiments for architecture $ARCHITECTURE with $NUM_COMPUTE_NODES compute nodes using $NUM_TRIALS trials..."
read -p "Continue? [Y/n] " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1
fi



# Real workflows
real_workflows="seismology montage genome soykb cycles epigenomics bwa"
for real_workflow in $real_workflows; do
        ./run_experiments.py  -a "${ARCHITECTURE}" -w "${real_workflow}" -n "${NUM_COMPUTE_NODES}" -t "${NUM_TRIALS}" -c 0 500 1000 2000 5000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o ${OUTPUT_DIR} -s 1.0 2.0 5.0 10.0
done

# Chain
./run_experiments.py  -a "${ARCHITECTURE}" -w chain -n "${NUM_COMPUTE_NODES}" -t "${NUM_TRIALS}" -c 0 500 1000 2000 5000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o ${OUTPUT_DIR} -S 1 5 10

# Forkjoin
./run_experiments.py  -a "${ARCHITECTURE}" -w forkjoin -n ${NUM_COMPUTE_NODES} -t "${NUM_TRIALS}" -c 0 500 1000 2000 5000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o ${OUTPUT_DIR} -S 10 18 25 34 50 66 100 130 200
