#!/bin/bash
#
# CHAINS

if [ "$#" -ne 1 ]; then
	    echo "Usage: " $0 " <haswell|skylake|cascadelake>"
	    exit 0
fi

NUM_SAMPLES=10
PERCENT_CPU=0.6
ARCH=$1

for NUM_TASKS in 1 5 10; do
	for CPU_WORK in 0 500 5000 10000; do
		for DATA_FOOTPRINT in 0 1000 10000; do
			KEY=chain-${NUM_TASKS}-${CPU_WORK}-${DATA_FOOTPRINT}-${PERCENT_CPU}-${ARCH}
			if [ ! -d "${KEY}" ]
			then
				echo "RUNNING " ${KEY}
				/bin/rm -rf wfbench-workflow
				python calibration_experiments/scripts/create-chain-workflow.py --command WfBench --num_tasks ${NUM_TASKS} --cpu_work ${CPU_WORK} --percent_cpu ${PERCENT_CPU}  --data ${DATA_FOOTPRINT} > chain-workflow.json
				echo "WORKFLOW CREATED IN chain-workflow.json"
				echo "RUNNING WORKFLOW..."
				python calibration_experiments/scripts/run-chain-workflows.py ${ARCH} ${NUM_SAMPLES}
				echo "WORKFLOW DONE!"
				mv runs ${KEY}
			else
				echo "${KEY} ALREADY THERE .... SKIPPING!"
			fi
		done
	done
done



