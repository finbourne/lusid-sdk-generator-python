#!/bin/bash

set -eEuo pipefail

export TEST_API_MODULE=api.instrument_api
export TEST_API=InstrumentApi
export TEST_METHOD='get_open_figi_parameter_option(finbourne_horizon.models.OpenFigiParameterOptionName.CURRENCY,'

export PACKAGE_NAME=candela_sdk
export PROJECT_NAME=candela-sdk
export APPLICATION_NAME=candela
export META_REQUEST_ID_HEADER_KEY=candela-meta-requestid
export REPO_URL="https://pypi.org"
export GIT_USER_ID=finbourne
export GIT_REPO_ID=candela-sdk-python
export REPOSITORY_NAME=pypi

just test-local