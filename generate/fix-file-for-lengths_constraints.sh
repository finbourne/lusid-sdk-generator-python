#!/bin/bash

# shellcheck disable=SC2089

set -eETuo pipefail

failure() {
  local lineno="$1"
  local msg="$2"
  echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

file=$1
pattern=',\s*max_items=[0-9]\+'

# need the GNU version of sed on a mac
if [[ $(uname) == Darwin ]]; then
    if gsed --version > /dev/null; then
        shopt -s expand_aliases
        alias sed=gsed
    else
        echo "GNU sed required for this script, please add it. See https://formulae.brew.sh/formula/gnu-sed"
        exit 1
    fi
fi

# check file exists
if ! [[ -f $file ]]; then
    echo "expected file '$file' does not exist - unable to carry out fix for one of"
    exit 1
fi

# remove
# it may not be necessary to check if the text exists in the file
if ! sed -i "s/$pattern//g" "$file"; then
    echo "error updating file '$file' for one of fix"
    exit 1
fi
