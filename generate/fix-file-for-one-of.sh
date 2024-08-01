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
    echo "expected file '$file' does not exist - unable to carry out fix for one of"
    exit 1
fi

# 1. fix if statement
if_statement_text_to_replace="if value not in ($find):"

# check that the expected text exists in the file
if ! grep -q "$if_statement_text_to_replace" "$file"; then
    echo "did not find expected text '$if_statement_text_to_replace' in file '$file' - unable to carry out fix for one of"
    exit 1
fi
# make the replacement
if ! sed -i "s/$if_statement_text_to_replace/if not value == $replace:/" "$file"; then
    echo "error updating file '$file' for one of fix"
    exit 1
fi

# 2. fix if statement error message
error_msg_text_to_replace="raise ValueError(\"must be one of enum values ($find)\")"

# check that the expected text exists in the file
if ! grep -q "$error_msg_text_to_replace" "$file"; then
    echo "did not find expected text '$error_msg_text_to_replace' in file '$file' - unable to carry out fix for one of"
    exit 1
fi
# make the replacement
if ! sed -i "s/$error_msg_text_to_replace/raise ValueError(\"must be one of enum values ($replace)\")/" "$file"; then
    echo "error updating file '$file' for one of fix"
    exit 1
fi
