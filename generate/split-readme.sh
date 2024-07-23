#!/bin/bash

set -eETuo pipefail

failure() {
  local lineno="$1"
  local msg="$2"
  echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

# split the README into two, and move one up a level
split_line=$(grep -n START_OF_NESTED_README generate/.output/sdk/README.md | cut -d: -f1)
head -n $(( split_line - 1 )) generate/.output/sdk/README.md > generate/.output/README.md
tail -n +$(( split_line + 1 )) generate/.output/sdk/README.md > generate/.output/sdk/README.md.new
mv generate/.output/sdk/README.md.new generate/.output/sdk/README.md