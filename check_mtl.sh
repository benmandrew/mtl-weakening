#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    exit 1
fi

tempdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename "$0").XXXXXXXXXXXX")

# Generate LTL from MTL
ltlspec=$(python3 -m src.mtl2ltlspec "$*")

# Substitute LTL specification into model file
sed "s/\$LTLSPEC/$ltlspec/g" res/model.in.smv > "$tempdir/model.smv"

# Run NuXmv
nuxmv_output=$(nuXmv "$tempdir/model.smv" | grep -Fv "*** ")

# Analyse counterexample
python3 -m src.analyse_cex "$*" <<< "$nuxmv_output"
