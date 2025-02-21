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
patternMax=',\s*max_items=[0-9]\+'
patternMin=',\s*min_items=[0-9]\+'
patternGe=',\s*ge=[0-9]\+'
patternLe=',\s*le=[0-9]\+'

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
    echo "expected file '$file' does not exist - unable to remove contraints"
    exit 1
fi

if ! sed -i "s/$patternMax//g" "$file"; then
    echo "error updating file '$file' for removing MaxItems"
    exit 1
fi
if ! sed -i "s/$patternMin//g" "$file"; then
    echo "error updating file '$file' for removing MinItems"
    exit 1
fi
if ! sed -i "s/$patternGe//g" "$file"; then
    echo "error updating file '$file' for removing GE"
    exit 1
fi
if ! sed -i "s/$patternLe//g" "$file"; then
    echo "error updating file '$file' for removing LE"
    exit 1
fi

