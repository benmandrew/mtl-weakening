#!/bin/bash

function format_interval() {
    local interval="$1"
    echo "$interval" | sed -e 's/^.//' -e 's/.$//'
}

function get_mtl() {
    local interval="$1"
    formatted_interval=$(format_interval "$interval")
    echo "G(leavingHome_p -> F[${formatted_interval}](resting_p))"
}

bound=36
interval="(0,18)"

start_time=$(date +%s%3N)

while true
do
    loop_start_time=$(date +%s%3N)
    mtl=$(get_mtl "$interval")
    ret=$(./experiments/check_mtl.sh "$mtl" $bound)
    loop_end_time=$(date +%s%3N)
    loop_elapsed_time=$((loop_end_time - loop_start_time))
    echo "Checked bound $bound | $mtl | $loop_elapsed_time ms"

    if [[ $ret =~ \[([0-9]+),([0-9]+)\] ]]; then
        echo "Counterexample found for bound $bound: $ret"
        echo "$ret"
        interval=$ret
        bound=$((ret * 2))
    elif [ "$ret" = "No loop exists in the counterexample" ]; then
        bound=$((bound - 1))
    elif [ "$ret" = "Property is valid" ]; then
        echo "No counterexample found for bound $bound"
        break
    else
        echo "Unexpected output: $ret"
        exit 1
    fi
done

end_time=$(date +%s%3N)
echo "Final valid formula: $(get_mtl "$interval")"
echo "Total elapsed time: $((end_time - start_time)) ms"
