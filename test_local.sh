#!/bin/bash

set -eEuo pipefail

export TEST_API_MODULE=api.apps_api
export TEST_API=AppsApi
export TEST_METHOD='print('

export PACKAGE_NAME=candela
export PROJECT_NAME=candela-sdk
export APPLICATION_NAME=candelacd 
export META_REQUEST_ID_HEADER_KEY=candela-meta-requestid
export REPO_URL="https://pypi.org"
export GIT_USER_ID=finbourne
export GIT_REPO_ID=candela-sdk-python
export REPOSITORY_NAME=pypi

just test-local