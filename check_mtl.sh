#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    exit 1
fi

tempdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")

ltlspec=$(python3 -m src.mtl2ltlspec "$*")
sed "s/\$LTLSPEC/$ltlspec/g" res/model.in.smv > $tempdir/model.smv
cat $tempdir/model.smv
nuXmv $tempdir/model.smv | grep -Fv "*** "
