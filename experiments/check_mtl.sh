#!/bin/bash

if [ $# -lt 1 ]; then
	echo "No arguments supplied"
	exit 1
fi

# Allow script to exit even if nuXmv is hanging
# To kill nuXmv process run:
#   kill -9 $(pgrep nuXmv)
trap 'exit 130' INT

tempdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename "$0").XXXXXXXXXXXX")

input_smv_file=models/foraging-robots.smv

if ! nuXmv "$input_smv_file" >/dev/null; then
	echo "SMV file failed to parse"
	exit 1
fi

# nuXmv trace plugins:
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
check_ltlspec_bmc_onepb -k "$2" -l '*' -o "problem"
show_traces -o "trace.txt" -p 0
quit
EOL

# Generate LTL from MTL
ltlspec=$(python3 -m src.mtl2ltlspec "$1")

# Append LTL specification to model file
cp "$input_smv_file" "$tempdir/model.smv"
echo "LTLSPEC $ltlspec;" >>"$tempdir/model.smv"

# Run NuXmv
(cd "$tempdir" || exit ;\
	nuXmv -source "$tempdir/commands.txt" "$tempdir/model.smv") >/dev/null

# Analyse counterexample
# python3 -m src.analyse_cex "$1" --quiet <<<"$nuxmv_output"

cat "$tempdir/trace.txt"

# Print the markings
# python3 -m src.trace2marking --quiet "$tempdir/trace.txt"
