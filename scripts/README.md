# Running experiments

Before running any of the scripts in this folder, be sure to have completed the installation/configuration of the submit and worker nodes (found in the `../setup` folder).

Scripts in this folder should be run from the **submit** node.

## Running Chain Workflows

1. SSH to the submit node instance (`ssh cc@<PUBLIC_IP_ADDRESS>`)
2. `cd /home/cc`
3. `git clone https://github.com/rafaelfsilva/calibration_experiments` (if not there already)
4. `python calibration_experiments/scripts/create-chain-workflow.py --help` (too see list of available parameters)
5. For a simple sleep example: `python calibration_experiments/scripts/create-chain-workflow.py > /home/cc/chain-workflow.json`
6. Start a screen session for the runs: `screen`
7. `python run-chain-workflows.py <MACHINE_NAME> <NUM_OF_RUNS>` (machine names: cascadelake, skylake, haswell)
8. While the experiments are running, leave the screen session by typing: `Ctrl + A` then `Ctrl + D`
9. Once experiment executions are completed, you can find the logs of the executions at: `/home/cc/runs/chain-workflow-<MACHINE_NAME>-<RUN_NUM>.tar.gz`

## Running Fork-Join Workflows

1. SSH to the submit node instance (`ssh cc@<PUBLIC_IP_ADDRESS>`)
2. `cd /home/cc`
3. `git clone https://github.com/rafaelfsilva/calibration_experiments` (if not there already)
4. `python calibration_experiments/scripts/create-fork-join-workflow.py --help` (too see list of available parameters)
5. For a simple sleep example: `python calibration_experiments/scripts/create-fork-join-workflow.py > /home/cc/fork-join-workflow.json`
6. Start a screen session for the runs: `screen`
7. `python run-fork-join-workflows.py <MACHINE_NAME> <NUM_OF_RUNS>` (machine names: cascadelake, skylake, haswell)
8. While the experiments are running, leave the screen session by typing: `Ctrl + A` then `Ctrl + D`
9. Once experiment executions are completed, you can find the logs of the executions at: `/home/cc/runs/fork-join-workflow-<MACHINE_NAME>-<RUN_NUM>.tar.gz`
