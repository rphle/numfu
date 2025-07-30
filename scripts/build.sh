#!/bin/bash
set -euo pipefail

python3 -m venv .numfu_build_venv
source .numfu_build_venv/bin/activate

pip install .

numfu ast src/numfu/stdlib/builtins.nfu -o src/numfu/stdlib/builtins.nfut --imports []

pip wheel . -w wheels


# rm src/numfu/stdlib/*.nfut

deactivate

rm -rf .numfu_build_venv

echo "Build complete. Wheel(s) are in dist/"
