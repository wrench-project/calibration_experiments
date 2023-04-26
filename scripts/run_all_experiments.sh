#!/bin/bash 

# Real workflows
real_workflows="seismology montage genome soykb cycles epigenomics bwa"
for real_workflow in $real_workflows; do
        ./run_experiments.py  -a haswell -w $real_workflow -n 1 -t 1 -c 0 500 5000 10000 20000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o /tmp -s 1.0 2.0 5.0 10.0
done

# Chain
./run_experiments.py  -a haswell -w chain -n 1 -t 1 -c 0 500 5000 10000 20000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o /tmp -S 1 5 10 

# Forkjoin
./run_experiments.py  -a haswell -w forkjoin -n 1 -t 1 -c 0 500 5000 10000 20000 -f 0.6 -d 0 100000000 1000000000 10000000000 -o /tmp -S 10 18 25 34 50 66 100 130 200
