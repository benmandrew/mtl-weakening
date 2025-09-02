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

bound=10
interval="(0,1)"

start_time=$(date +%s%3N)

for _ in {1..10}
do
    loop_start_time=$(date +%s%3N)
    mtl=$(get_mtl "$interval")
    ret=$(./check_mtl.sh  "$mtl" $bound)
    loop_end_time=$(date +%s%3N)
    loop_elapsed_time=$((loop_end_time - loop_start_time))
    echo "Checked bound $bound | $mtl | $loop_elapsed_time ms"
    if [ "$ret" = "No loop exists in the counterexample" ]; then
        bound=$((bound - 1))
    elif [ "$ret" = "Property is valid" ]; then
        echo "No counterexample found for bound $bound"
        bound=$((bound + 1))
    else
        interval=$ret
        bound=$((bound * 2))
    fi
done

end_time=$(date +%s%3N)
echo "Final valid formula: $(get_mtl "$interval")"
echo "Total elapsed time: $((end_time - start_time)) ms"
