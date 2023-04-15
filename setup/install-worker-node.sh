#!/bin/bash

CONDOR_HOST=$1

# install HTCondor
apt-get update && apt-get install -y curl
curl -fsSL https://get.htcondor.org | sudo /bin/bash -s -- --no-dry-run --channel stable
rm /etc/condor/config.d/00-minicondor
cat <<EOT>> /etc/condor/config.d/00-minicondor
use ROLE: Execute

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
sleep 10

# install dependencies
cd $HOME
pip install pandas filelock
apt install -y stress-ng
mkdir -p /var/lib/condor
mkdir -p /var/lib/condor/execute
chown condor:condor -R /var/lib/condor
chmod -R 777 /var/lib/condor/execute
