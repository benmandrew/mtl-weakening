#!/bin/bash

# for run in {101..200}; do
#     interval=$(./check_mtl.sh 'G(leavingHome_p -> F[0,1](resting_p))' "$run");

#     if [ -n "$interval" ]; then
#         # Remove the brackets from the interval (first and last character)
#         csv_interval=$(echo "$interval" | sed -e 's/^.//' -e 's/.$//')
#         echo "$run, $csv_interval"
#     else
#         echo "$run, ,"
#     fi
# done

# interval="(0,1)"

# formatted_interval=$(echo "$interval" | sed -e 's/^.//' -e 's/.$//')
# mtl="G(leavingHome_p -> F[${formatted_interval}](resting_p))"
# echo "$mtl"
# interval=$(./check_mtl.sh  "$mtl" 10);
# echo "$interval"

# formatted_interval=$(echo "$interval" | sed -e 's/^.//' -e 's/.$//')
# mtl="G(leavingHome_p -> F[${formatted_interval}](resting_p))"
# echo "$mtl"
# interval=$(./check_mtl.sh  "$mtl" 20);
# echo "$interval"

# interval=$(./check_mtl.sh  "$mtl" 21);
# echo "$interval"

# formatted_interval=$(echo "$interval" | sed -e 's/^.//' -e 's/.$//')
# mtl="G(leavingHome_p -> F[${formatted_interval}](resting_p))"
# echo "$mtl"
# interval=$(./check_mtl.sh  "$mtl" 42);
# echo "$interval"

# formatted_interval=$(echo "$interval" | sed -e 's/^.//' -e 's/.$//')
# mtl="G(leavingHome_p -> F[${formatted_interval}](resting_p))"
# echo "$mtl"
# interval=$(./check_mtl.sh  "$mtl" 82);
# echo "$interval"

# interval="(0,1)"