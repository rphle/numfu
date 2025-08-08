#!/bin/bash
set -euo pipefail

# check python version
ver=$(python3 -V 2>&1 | sed -E 's/.* ([0-9]+)\.([0-9]+).*/\1 \2/')
major=$(echo $ver | cut -d' ' -f1)
minor=$(echo $ver | cut -d' ' -f2)

if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -le 12 ]; }; then
    echo "NumFu requires python >= 3.13"
    exit 1
fi

# perform a first install to ensure that the builtins can be parsed.
if pip list | grep -F numfu  &> /dev/null; then
    echo 'NumFu already installed'
else
    pip install .
fi

numfu parse src/numfu/stdlib/builtins.nfu  --imports ""

# create an editable install and build wheels
pip install -e .
pip wheel . -w wheels

# rm src/numfu/stdlib/*.nfut

echo "Sucessfully installed NumFu"
