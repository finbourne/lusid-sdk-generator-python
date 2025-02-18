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
find=$2
replace=$3

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
    echo "expected file '$file' does not exist - unable to carry out fix"
    exit 1
fi

# make the replacement
if ! sed  -i -e "s/$find/$replace/g" "$file"; then
    echo "error updating file '$file'"
    exit 1
fi
