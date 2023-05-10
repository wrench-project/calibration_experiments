#!/opt/local/bin/bash
set -e


IPs="129.114.108.220 129.114.109.104 129.114.109.38 129.114.109.82 129.114.109.189 129.114.108.237 129.114.109.41 129.114.109.111"

declare -A IP_DIR_MAP

echo "These IPs below are hardcoded into the script:"
for IP in $IPs; do
	NUMFILEFOUND=$(ssh cc@"$IP" ls 'tracing_output/*.json' | wc -l)
	FILEFOUND=$(ssh cc@"$IP" ls 'tracing_output/*.json' | head -1)
	ACTIVE=$(ssh cc@129.114.108.220 ps auxww | grep run_all_ex | wc -l)
	ARCHITECTURE=$(echo "$FILEFOUND" | sed 's/[^-]*-[^-]*-[^-]*-[^-]*-[^-]*-\([^-]*\)-.*/\1/')
	NUM_COMPUTE_NODES=$(echo "$FILEFOUND" | sed 's/[^-]*-[^-]*-[^-]*-[^-]*-[^-]*-[^-]*-\([^-]*\)-.*/\1/')
	ACTIVE_STRING=""
	if [ "$ACTIVE" -eq "1" ]; then
	  ACTIVE_STRING="RUNNING"
	else
	  ACTIVE_STRING="NOT RUNNING"
	fi
	DIRNAME="./$ARCHITECTURE-$NUM_COMPUTE_NODES-compute-nodes"
	NUMLOCALFILEFOUND=$(find "$DIRNAME" -name '*.json' | wc -l)
	printf '  - %-*s' 19 "$IP: "
	printf '%-*s' 11 "$ARCHITECTURE"
	echo "  $NUM_COMPUTE_NODES compute nodes ($NUMFILEFOUND remote files, $NUMLOCALFILEFOUND local files, *$ACTIVE_STRING*)"
	IP_DIR_MAP["$IP"]="$DIRNAME"
	if [ ! -d "$DIRNAME" ]; then
  	  mkdir "$DIRNAME"
	fi
done


echo ""
read -p "Continue? [y/n] " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && echo "Bye!" && exit 1
fi

declare -A OPERATION_MAP
OPERATION_MAP["1"]="Rsync all .json's FROM IPs"
OPERATION_MAP["2"]="Rsync all .tar.gz's FROM IPs"
OPERATION_MAP["3"]="Rsync all .json's and .tar.gz's FROM IPs"

NUM_OPS=${#OPERATION_MAP[@]}

echo ""
echo "Select one of the options below:"
for OP_INDEX in $(seq 1 "$NUM_OPS"); do
  echo "  $OP_INDEX. ${OPERATION_MAP[$OP_INDEX]}"
done

while true; do
# Prompt the user for a number between 1 and $NUM_OPS
  read -p "Choice? " -n 1 -r SELECTED_OPERATION

  if [[ "$SELECTED_OPERATION" =~ ^[1-$NUM_OPS]$ ]]; then
    # The input is valid, continue with the script
    echo ""
    break
  else
    # The input is invalid, print an error message and try again
    echo ""
    echo "Error: Input must be a number between 1 and 4"
  fi
done


SELECTED_IPs=$IPs

echo "About to do: ${OPERATION_MAP[$SELECTED_OPERATION]} for the following:"
for IP in $SELECTED_IPs; do
  echo "  - $IP (${IP_DIR_MAP[$IP]})"
done

echo ""
read -p "Are you sure? [y/n] " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && echo "Bye!" && exit 1
fi

# Do the work
for IP in $SELECTED_IPs; do
  case $SELECTED_OPERATION in
    "1")
      rsync --times -vr --exclude '*.tar.gz' cc@"$IP":/home/cc/tracing_output/ ./"${IP_DIR_MAP[$IP]}"/
      ;;
    "2")
      rsync --times -vr --exclude '*.json' cc@"$IP":/home/cc/tracing_output/ ./"${IP_DIR_MAP[$IP]}"/
      ;;
    "3")
      rsync --times -vr cc@"$IP":/home/cc/tracing_output/ ./"${IP_DIR_MAP[$IP]}"/
      ;;
    "4")
      rsync --times -vr --exclude '*.tar.gz' ./"${IP_DIR_MAP[$IP]}"/ cc@"$IP":/home/cc/tracing_output/
      ;;
    *)
      echo "FATAL ERROR: UNKNOWN OPERATION"
      ;;
  esac
done


