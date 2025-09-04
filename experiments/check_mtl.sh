#!/bin/bash

if [ $# -lt 4 ]; then
	>&2 echo "Not enough arguments supplied"
	exit 1
fi

mtl=$1
de_bruijn=$2
bound=$3
loopback=$4

# Allow script to exit even if nuXmv is hanging
# To kill nuXmv process run:
#   kill -9 $(pgrep nuXmv)
trap 'exit 130' INT

tempdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename "$0").XXXXXXXXXXXX")

# >&2 echo "Temporary directory created at: $tempdir"

input_smv_file=models/foraging-robots.smv

if ! nuXmv "$input_smv_file" >/dev/null; then
	>&2 echo "SMV file failed to parse"
	exit 1
fi

# nuXmv trace plugins, controlled with flag `-p`:
#   0   BASIC TRACE EXPLAINER - shows changes only
#   1   BASIC TRACE EXPLAINER - shows all variables
#   2   TRACE TABLE PLUGIN - symbols on column
#   3   TRACE TABLE PLUGIN - symbols on row
#   4   TRACE XML DUMP PLUGIN - an xml document
#   5   TRACE COMPACT PLUGIN - Shows the trace in a compact tabular fashion
#   6   TRACE XML EMBEDDED DUMP PLUGIN - an xml element
#   7   Empty Trace Plugin

# Write commands file
cat >"$tempdir/commands.txt" <<EOL
set on_failure_script_quits 1
go_bmc
check_ltlspec_bmc_onepb -k "$bound" -l "$loopback" -o "problem"
show_traces -o "trace.xml" -p 4
quit
EOL

# Generate LTL from MTL
ltlspec=$(python3 -m src.mtl2ltlspec "$mtl")

# Append LTL specification to model file
cp "$input_smv_file" "$tempdir/model.smv"
echo "LTLSPEC $ltlspec;" >>"$tempdir/model.smv"

# Run NuXmv
(cd "$tempdir" || exit ;\
	nuXmv -source "$tempdir/commands.txt" "$tempdir/model.smv") >"$tempdir/nuXmv.log" 2>&1

no_cex_string="no counterexample found with bound $bound and loop at $loopback"

if grep -q "$no_cex_string" "$tempdir/nuXmv.log"; then
    echo "Property is valid"
	exit 0
fi

if [ ! -f "$tempdir/trace.xml" ]; then
    # >&2 echo "Trace file not found at: $tempdir/trace.xml"
	exit 1
fi

# Analyse counterexample
python3 -m src.analyse_cex --mtl "$mtl" --de-bruijn "$de_bruijn" --quiet "$tempdir/trace.xml"

# Print the markings
# python3 -m src.trace2marking --quiet "$tempdir/trace.xml"
