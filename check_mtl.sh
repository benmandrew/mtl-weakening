#!/bin/bash

if [ $# -lt 1 ]
  then
    echo "No arguments supplied"
    exit 1
fi

# Use path relative to script
parent_path=$( (cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1) ; pwd -P )
cd "$parent_path" || exit 1

tempdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename "$0").XXXXXXXXXXXX")

# Write commands file
cat > "$tempdir/commands.txt" <<EOL
go_bmc
check_ltlspec_bmc_onepb -k 30
quit
EOL

# Generate LTL from MTL
ltlspec=$(python3 -m src.mtl2ltlspec "$1")

# Append LTL specification to model file
cp res/model.smv "$tempdir/model.smv"
echo "LTLSPEC $ltlspec;" >> "$tempdir/model.smv"

# Run NuXmv, kill after 60s to handle syntax
# errors that drop into the interactive shell
nuxmv_output=$(timeout --signal=KILL 60s nuXmv \
    -source "$tempdir/commands.txt" "$tempdir/model.smv" \
    | grep -Fv "*** ")

if [ "$2" = "cex" ]; then
    echo "$nuxmv_output"
else
    # Analyse counterexample
    python3 -m src.analyse_cex "$*" --debug <<< "$nuxmv_output"
fi
