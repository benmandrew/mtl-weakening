#!/bin/bash

if [ $# -lt 1 ]; then
	echo "No arguments supplied"
	exit 1
fi

# Allow script to exit even if nuXmv is hanging
# To kill nuXmv process run:
#   kill -9 $(ps aux | grep nuXmv | awk '{print $2}')
trap 'exit 130' INT

# Use path relative to script
parent_path=$(
	(cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1)
	pwd -P
)
cd "$parent_path" || exit 1

tempdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename "$0").XXXXXXXXXXXX")

input_smv_file=models/foraging-robots.smv
temp_smv_file="$tempdir/model.smv"

if ! nuXmv "$input_smv_file" >/dev/null; then
	echo "SMV file failed to parse"
	exit 1
fi

# Write commands file
cat >"$tempdir/commands.txt" <<EOL
set on_failure_script_quits 1
go_bmc
check_ltlspec_bmc_onepb -k "$2" -l '*'
quit
EOL

# Generate LTL from MTL
ltlspec=$(python3 -m src.mtl2ltlspec "$1")

# Append LTL specification to model file
cp "$input_smv_file" "$temp_smv_file"
echo "LTLSPEC $ltlspec;" >>"$temp_smv_file"

# Run NuXmv
nuxmv_output=$(nuXmv \
	-source "$tempdir/commands.txt" "$temp_smv_file" 2>/dev/null |
	grep -Fv "*** " |
	grep -v -e '^$')

# >&2 echo "$nuxmv_output"

# Analyse counterexample
python3 -m src.analyse_cex "$1" --quiet <<<"$nuxmv_output"
