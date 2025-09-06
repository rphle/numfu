#!/bin/bash
set -e

versionpy="src/numfu/_version.py"
packagejson="docusaurus/package.json"

# read version from pyproject.toml
version=$(grep '^version' pyproject.toml | head -n1 | cut -d'"' -f2)

echo "Updating version to $version"

# update _version.py
sed -i.bak "s/^__version__ *= *.*/__version__ = \"$version\"/" $versionpy
rm "$versionpy.bak"

# update package.json
jq ".version = \"$version\"" $packagejson > "$packagejson.tmp"
mv "$packagejson.tmp" "$packagejson"

echo "Updated _version.py and package.json to $version"
