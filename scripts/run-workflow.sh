#!/bin/bash

if [[ $# -ne 2 ]] ; then
    echo "Usage: $0 <work dir path> <cpu-benchmark dir>"
    exit 1
fi

# reorganize work dir
cd "$1" || exit
mkdir data
mv *.txt data
cp "$2"/cpu-benchmark .

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

