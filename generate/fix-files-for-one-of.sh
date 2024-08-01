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
application=$3

while read -r item; do
    # echo "item='$item'"
    file="$(echo "$item" | jq -r '.file')"
    find="$(echo "$item" | jq -r '.find')"
    replace="$(echo "$item" | jq -r '.replace')"
    bash "$justfile_dir/generate/fix-file-for-one-of.sh" "$justfile_dir/generate/.output/sdk/$package_name/models/$file.py" "$find" "$replace"
done <<< "$(jq -rc '.items[]' "$justfile_dir/generate/$application-one-of-fix-list.json")"