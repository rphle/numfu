#!/bin/bash
set -euo pipefail

bash scripts/install.sh

pip wheel . -w wheels

echo "Build complete. Wheel(s) are in wheels/"
