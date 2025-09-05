#!/bin/bash

base_dir="tests/modules/errors"

test_numfu() {
    local file="$1"
    local expected_output="$2"
    local test_name="$3"

    echo "$test_name ($file)"

    output=$(numfu "$file" 2>&1)
    exit_code=$?

    if [[ "$output" == *"$expected_output"* ]]; then
        return 0
    else
        echo "❌ Test failed: '$expected_output' not found in output."
        return 1
    fi
}

test_numfu "$base_dir/missing_module.nfu" "Cannot find module" "Missing Module Import Test"
test_numfu "$base_dir/missing_export.nfu" "does not export an identifier named" "Missing Export Test"
test_numfu "$base_dir/invalid_names.nfu" "is an invalid module name" "Invalid Module Names Test"
test_numfu "$base_dir/invalid_import.nfu" "Imports must be at the top of the file" "Top-Level Imports Test"
test_numfu "$base_dir/nested_export.nfu" "Export must be at the top level" "Top-Level Exports Test"
test_numfu "$base_dir/undefined_export.nfu" "is not defined in the current scope" "Undefined Export Test"
