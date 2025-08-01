#!/bin/bash
set -euo pipefail

if pip list | grep -F numfu  &> /dev/null; then
    echo 'numfu already installed'
else
    pip install .
fi

numfu ast src/numfu/stdlib/builtins.nfu -o src/numfu/stdlib/builtins.nfut --imports []

pip wheel . -w wheels

# rm src/numfu/stdlib/*.nfut

echo "Build & install complete. Wheel(s) are in wheels/"
