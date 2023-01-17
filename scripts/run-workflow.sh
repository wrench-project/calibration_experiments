#!/bin/bash

# reorganize work dir
cd wfbench-workflow
mkdir data
mv *.txt data
cp ../cpu-benchmark .

# generate pegasus YAML workflow
export PYTHONPATH=$PYTHONPATH:/usr/lib/python3.6/dist-packages
python3 pegasus-workflow.py

pegasus-plan --dir work --cleanup none --output-site local --submit `ls *.yml`
sleep 30

PID_FILE=`ls work/cc/pegasus/*/run0001/*.pid`

echo "Waiting for workflow execution to complete..."

while [[ -f $PID_FILE ]]
do
  sleep 90
done

echo "Workflow execution completed."

