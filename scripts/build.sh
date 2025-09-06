#!/bin/bash
set -euo pipefail

bash scripts/install.sh

pip wheel . -w wheels
python -m build

echo "Build complete. Wheel(s) are in wheels/"
