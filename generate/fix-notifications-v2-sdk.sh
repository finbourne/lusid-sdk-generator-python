#!/bin/bash

# shellcheck disable=SC2089

set -euo pipefail

justfile_dir=$1
package_name=$2

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

# fix AmazonSqsNotificationType/Response files
amazon_sqs_notification_type_file="$justfile_dir/generate/.output/sdk/$package_name/models/amazon_sqs_notification_type.py"
amazon_sqs_notification_type_response_file="$justfile_dir/generate/.output/sdk/$package_name/models/amazon_sqs_notification_type_response.py"

for file in $amazon_sqs_notification_type_file $amazon_sqs_notification_type_response_file; do
    # check file exists
    if ! [[ -f $file ]]; then
        echo "expected file '$file' does not exist - unable to make notifications v2 sdk fix"
        exit 1
    fi

    # 1. fix if statement
    if_statement_text_to_replace="if value not in ('AmazonSqs', 'AmazonSqsPrincipalAuth', 'AzureServiceBus', 'Email', 'Sms', 'Webhook'):"

    # check that the expected text exists in the file
    if ! grep -q "$if_statement_text_to_replace" "$file"; then
        echo "did not find expected text '$if_statement_text_to_replace' in file '$file' - unable to make notifications v2 sdk fix"
        exit 1
    fi
    # make the replacement
    if ! sed -i "s/$if_statement_text_to_replace/if not value == 'AmazonSqs':/" "$file"; then
        echo "error updating file '$file' for notifications v2 sdk fix"
        exit 1
    fi

    # 2. fix if statement error message
    error_msg_text_to_replace="raise ValueError(\"must be one of enum values ('AmazonSqs', 'AmazonSqsPrincipalAuth', 'AzureServiceBus', 'Email', 'Sms', 'Webhook')\")"
    
    # check that the expected text exists in the file
    if ! grep -q "$error_msg_text_to_replace" "$file"; then
        echo "did not find expected text '$error_msg_text_to_replace' in file '$file' - unable to make notifications v2 sdk fix"
        exit 1
    fi
    # make the replacement
    if ! sed -i "s/$error_msg_text_to_replace/raise ValueError(\"must be one of enum values ('AmazonSqs')\")/" "$file"; then
        echo "error updating file '$file' for notifications v2 sdk fix"
        exit 1
    fi
done

# fix AmazonSqsPrincipalAuthNotificationType/Response files
amazon_sqs_principal_auth_notification_type_file="$justfile_dir/generate/.output/sdk/$package_name/models/amazon_sqs_principal_auth_notification_type.py"
amazon_sqs_principal_auth_notification_type_response_file="$justfile_dir/generate/.output/sdk/$package_name/models/amazon_sqs_principal_auth_notification_type_response.py"
for file in $amazon_sqs_principal_auth_notification_type_file $amazon_sqs_principal_auth_notification_type_response_file; do
    # check file exists
    if ! [[ -f $file ]]; then
        echo "expected file '$file' does not exist - unable to make notifications v2 sdk fix"
        exit 1
    fi

    # 1. fix if statement
    if_statement_text_to_replace="if value not in ('AmazonSqsPrincipalAuth'):"

    # check that the expected text exists in the file
    if ! grep -q "$if_statement_text_to_replace" "$file"; then
        echo "did not find expected text '$if_statement_text_to_replace' in file '$file' - unable to make notifications v2 sdk fix"
        exit 1
    fi
    # make the replacement
    if ! sed -i "s/$if_statement_text_to_replace/if not value == 'AmazonSqsPrincipalAuth':/" "$file"; then
        echo "error updating file '$file' for notifications v2 sdk fix"
        exit 1
    fi
done