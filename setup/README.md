# Installing on Chameleon Cloud

Make sure you're on Ubuntu22 so that Python is recent-ish

## Installing Submit Node

1. SSH to the submit node instance (`ssh cc@<PUBLIC_IP_ADDRESS>`)
2. `cd /home/cc`
3. `git clone https://github.com/wrench-project/pegasus_workflows_on_chameleon.git`
4. `cd calibration_experiments/setup`
5. `sudo su`
6. `bash install-submit-node.sh <IP_FOR_SUBMIT_NODE>` 

## Installing Worker Nodes

1. SSH to the each worker node instance (`ssh cc@<PUBLIC_IP_ADDRESS>`)
2. `cd /home/cc`
3. `git clone https://github.com/wrench-project/pegasus_workflows_on_chameleon.git`
4. `cd calibration_experiments/setup`
5. `sudo su`
6. `bash install-worker-node.sh <IP_FOR_SUBMIT_NODE>` 
