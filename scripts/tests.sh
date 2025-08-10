#!/bin/bash
set -e

# Run all test files from the tests folder
numfu tests/basics.nfu
numfu tests/functions.nfu
numfu tests/math.nfu
numfu tests/operators.nfu
numfu tests/lists.nfu
numfu tests/logic.nfu
numfu tests/strings.nfu
numfu tests/builtins.nfu
numfu tests/recursion.nfu
numfu tests/edgecases.nfu
