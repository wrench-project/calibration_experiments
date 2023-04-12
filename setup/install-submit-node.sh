#!/bin/bash

CONDOR_HOST=$1

ufw disable

# install HTCondor
apt-get update && apt-get install -y curl
curl -fsSL https://get.htcondor.org | sudo /bin/bash -s -- --no-dry-run
rm /etc/condor/config.d/00-minicondor
cat <<EOT>> /etc/condor/config.d/00-minicondor
use ROLE: CentralManager
use ROLE: Submit

BIND_ALL_INTERFACES = True
CONDOR_HOST = $CONDOR_HOST

SEC_DEFAULT_AUTHENTICATION = OPTIONAL
SEC_DEFAULT_AUTHENTICATION_METHODS = CLAIMTOBE

SCHEDD_INTERVAL = 5
NEGOTIATOR_INTERVAL = 2
NEGOTIATOR_CYCLE_DELAY = 5
STARTER_UPDATE_INTERVAL = 5
SHADOW_QUEUE_UPDATE_INTERVAL = 10
UPDATE_INTERVAL = 5
RUNBENCHMARKS = 0

HOSTALLOW_WRITE = *
HOSTALLOW_READ = *
ALLOW_WRITE = *
ALLOW_READ = *
ALLOW_NEGOTIATOR = *
ALLOW_DAEMON = *
ALLOW_COLLECTOR = *
NUM_CPUS = 16
EOT

systemctl restart condor

# install Pegasus
wget -O - http://download.pegasus.isi.edu/pegasus/gpg.txt | sudo apt-key add -
echo 'deb [arch=amd64] http://download.pegasus.isi.edu/pegasus/ubuntu bionic main' | sudo tee /etc/apt/sources.list.d/pegasus.list
apt-get update
apt-get install -y pegasus

# install WfCommons
cd /home/cc
git clone https://github.com/wfcommons/wfcommons
chown -R cc:cc /home/cc/wfcommons
cd wfcommons
#git checkout feature/wfbench
pip install -e .
#cd bin
#g++ -o cpu-benchmark cpu-benchmark.cpp
cp bin/cpu-benchmark /home/cc

# configure environment
cd /home/cc
cp calibration_experiments/scripts/RUN_CHAINS.sh .
cp calibration_experiments/scripts/run-workflow.sh .
cp calibration_experiments/scripts/run-chain-workflows.py .
cp calibration_experiments/scripts/run-fork-join-workflows.py .
chown cc:cc exp.py run-workflow.sh run-chain-workflows.py run-fork-join-workflows.py
