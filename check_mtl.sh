#!/bin/bash

if [ $# -lt 1 ]; then
	echo "No arguments supplied"
	exit 1
fi

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
go_bmc
check_ltlspec_bmc_onepb -k "$2"
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
	grep -Fv "*** ")

# echo "$nuxmv_output"

# Analyse counterexample
python3 -m src.analyse_cex "$1" --quiet <<<"$nuxmv_output"
