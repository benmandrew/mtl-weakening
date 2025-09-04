#!/bin/bash

function get_mtl() {
    local interval="$1"
    echo "G(leavingHome_p -> F${interval}(resting_p))"
}

interval="[0,1]"
bound=36
loopback=6

start_time=$(date +%s%3N)

while true
do
    loop_start_time=$(date +%s%3N)
    mtl=$(get_mtl "$interval")
    echo "Checking bound=$bound, loopback=$loopback"
    ret=$(./experiments/check_mtl.sh "$mtl" "$bound" "$loopback")
    loop_end_time=$(date +%s%3N)
    loop_elapsed_time=$((loop_end_time - loop_start_time))
    echo "Elapsed time: $loop_elapsed_time ms"

    if [[ $ret =~ \[([0-9]+),([0-9]+)\] ]]; then
        echo "Satisfying interval: $ret"
        interval=$ret
        rhs="${BASH_REMATCH[2]}"
        bound=$((rhs * 2))
    elif [ "$ret" = "Property is valid" ]; then
        echo "No interval found for bound $bound"
        break
    else
        echo "Unexpected output: $ret"
        exit 1
    fi
done

end_time=$(date +%s%3N)
echo "Final valid formula: $(get_mtl "$interval")"
echo "Total elapsed time: $((end_time - start_time)) ms"
