#!/bin/bash

CONDOR_HOST=$1

apt-get update && apt-get install ufw

ufw disable

# install pip
apt-get install -y python3-pip

# install HTCondor
apt-get install -y curl
curl -fsSL https://get.htcondor.org | sudo /bin/bash -s -- --no-dry-run --channel stable
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
#apt-get install -y pegasus=5.0.3-1+ubuntu18
apt-get install -y pegasus

# install WfCommons
cd /home/cc
git clone https://github.com/wfcommons/wfcommons
cd wfcommons
#git checkout 83a9ba730f44f984c64de877e1f202b0d64487ad
chown -R cc:cc /home/cc/wfcommons
#git checkout feature/wfbench
pip install python-dateutil==2.8.2
pip install -e .
#cd bin
#g++ -o cpu-benchmark cpu-benchmark.cpp
cp bin/cpu-benchmark /home/cc
cp /home/cc/wfcommons/bin/wfbench /usr/local/bin/

# fetch the 1.4 WfFormat schema
cd /home/cc
wget https://github.com/wfcommons/WfFormat/archive/refs/tags/v1.4.tar.gz
tar -xzf v1.4.tar.gz
cd WfFormat-1.4
cp wfcommons-schema.json /home/cc


# Put relevant scripts in $HOME
cd /home/cc
scripts="run-workflow.sh run_experiments.py run_all_experiments.sh"
for script in $scripts; do
	cp pegasus_workflows_on_chameleon/scripts/$script .
	chown cc:cc $script
done
