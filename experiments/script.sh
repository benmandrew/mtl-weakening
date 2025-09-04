#!/bin/bash

for run in {1..100}; do
    ret=$(./check_mtl.sh '(G(leavingHome_p -> F[0,5](resting_p))) & G(F(TRUE))' "$run");

    if [ "$ret" = "No loop exists in the counterexample" ]; then
        echo "$ret"
    elif [ "$ret" = "Property is valid" ]; then
        echo "$ret"
    else
        # Remove the brackets from the interval (first and last character)
        csv_interval=$(echo "$ret" | sed -e 's/^.//' -e 's/.$//')
        echo "$run, $csv_interval"
    fi
done
