#!/bin/bash

set -eETuo pipefail

failure() {
  local lineno="$1"
  local msg="$2"
  echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

file_path="$1"
import_statement="$2"
update_forward_refs="$3"

echo "$file_path"
echo "Fixing imports for Access"


# Check if the import statement is already present
if ! grep -Fxq "$import_statement" "$file_path"; then
  # Append the import statement to the bottom of the file
  echo "$import_statement" >> "$file_path"
  echo "Import statement added to $file_path"
else
  echo "Import statement is already present in $file_path"
fi

# Append the additional line if it's not already present
if ! grep -Fxq "$update_forward_refs" "$file_path"; then
  # Ensure the file ends with a new line, then append the additional line at the bottom
  echo -e "\n$update_forward_refs" >> "$file_path"
  echo "Import statement added to $file_path"
else
  echo "Import statement is already present in $file_path"
fi