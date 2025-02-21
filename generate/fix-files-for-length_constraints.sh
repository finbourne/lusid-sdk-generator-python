#!/bin/bash

set -eETuo pipefail

failure() {
  local lineno="$1"
  local msg="$2"
  echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

justfile_dir=$1
package_name=$2

directory="$justfile_dir/generate/.output/sdk/$package_name"


for file in "$directory/models"/*; do
    if [[ -f "$file" ]]; then
        echo "Processing file: $file"
        bash "$justfile_dir/generate/fix-file-for-lengths_constraints.sh" $file 
    fi
done

for file in "$directory/api"/*; do
    if [[ -f "$file" ]]; then
        echo "Processing file: $file"
        bash "$justfile_dir/generate/fix-file-for-lengths_constraints.sh" $file 
    fi
done

for file in "$directory/test"/*; do
    if [[ -f "$file" ]]; then
        echo "Processing file: $file"
        bash "$justfile_dir/generate/fix-file-for-lengths_constraints.sh" $file 
    fi
done