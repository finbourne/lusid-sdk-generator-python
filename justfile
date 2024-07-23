# Generate SDK's from a swagger.json file.
#
#  Ensure that you set the following environment variables to an appropriate value before running
#    PACKAGE_NAME
#    PROJECT_NAME
#    PACKAGE_VERSION
#    PYPI_PACKAGE_LOCATION

export APPLICATION_NAME := `echo ${APPLICATION_NAME:-lusid}`
export PACKAGE_NAME := `echo ${PACKAGE_NAME:-lusid}`
export PROJECT_NAME := `echo ${PROJECT_NAME:-lusid-sdk}`
export PACKAGE_VERSION := `echo ${PACKAGE_VERSION:-2.0.0}`

export PYPI_PACKAGE_LOCATION := `echo ${PYPI_PACKAGE_LOCATION:-~/.pypi/packages}`

# needed for tests
export FBN_ACCESS_TOKEN := `echo ${FBN_ACCESS_TOKEN:-access-token}`
export FBN_TOKEN_URL := `echo ${FBN_TOKEN_URL:-https://lusid.com}`
export FBN_USERNAME := `echo ${FBN_USERNAME:-username}`
export FBN_PASSWORD := `echo ${FBN_PASSWORD:-password}`
export FBN_CLIENT_ID := `echo ${FBN_CLIENT_ID:-client-id}`
export FBN_CLIENT_SECRET := `echo ${FBN_CLIENT_SECRET:-client-secret}`
export TEST_API_MODULE := `echo ${TEST_API_MODULE:-api.application_metadata_api}`
export TEST_API := `echo ${TEST_API:-ApplicationMetadataApii}`
export GENERATE_API_TESTS := `echo ${GENERATE_API_TESTS:-true}`

swagger_path := "./swagger.json"

swagger_url := "https://fbn-prd.lusid.com/api/swagger/v0/swagger.json"
fix_notifications_v2_sdk_flag := "--fix-notifications-v2-sdk"

get-swagger:
    echo {{swagger_url}}
    curl -s {{swagger_url}} > swagger.json

build-docker-images: 
    docker build -t finbourne/lusid-sdk-gen-python:latest --ssh default=$SSH_AUTH_SOCK -f Dockerfile .

generate-templates:
    docker run \
        -v {{justfile_directory()}}/.templates:/usr/src/templates \
        finbourne/lusid-sdk-gen-python:latest -- java -jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar author template -g python -o /usr/src/templates

generate-local FLAG="":
    # check if the notifications fix flag has been set
    if [ "{{FLAG}}" != "{{fix_notifications_v2_sdk_flag}}" ] && [ -n "{{FLAG}}" ]; then echo "unexpected flag '{{FLAG}}' ... did you mean '{{fix_notifications_v2_sdk_flag}}'?"; fi
    
    # generate the sdk
    rm -r {{justfile_directory()}}/generate/.output || true # ensure a clean output dir before starting
    envsubst < generate/config-template.json > generate/.config.json
    cp generate/templates/description.{{APPLICATION_NAME}}.mustache generate/templates/description.mustache
    docker run \
        -e JAVA_OPTS="-Dlog.level=error -Xmx6g" \
        -e PACKAGE_VERSION=${PACKAGE_VERSION} \
        -e GENERATE_API_TESTS=${GENERATE_API_TESTS} \
        -v {{justfile_directory()}}/generate/:/usr/src/generate/ \
        -v {{justfile_directory()}}/generate/.openapi-generator-ignore:/usr/src/generate/.output/.openapi-generator-ignore \
        -v {{justfile_directory()}}/{{swagger_path}}:/tmp/swagger.json \
        finbourne/lusid-sdk-gen-python:latest -- ./generate/generate.sh ./generate ./generate/.output /tmp/swagger.json .config.json
    rm -f generate/.output/.openapi-generator-ignore
    rm generate/templates/description.mustache

    # split the README into two, and move one up a level
    bash generate/split-readme.sh
    
    # try to fix the notifications sdk if flag set
    if [ "{{FLAG}}" = "{{fix_notifications_v2_sdk_flag}}" ]; then just fix-notifications-v2-sdk; fi

add-tests:
    mkdir -p {{justfile_directory()}}/generate/.output/sdk/test/
    rm -rf {{justfile_directory()}}/generate/.output/sdk/test/*
    cp -R {{justfile_directory()}}/test_sdk/* {{justfile_directory()}}/generate/.output/sdk/test

    # these test files have been copied from the lusid sdk tests
    # rename to match values for the sdk being tested
    find {{justfile_directory()}}/generate/.output/sdk/test -type f -exec sed -i -e "s/TO_BE_REPLACED/${PACKAGE_NAME}/g" {} \;

    # note these values won't work for the horizon sdk
    # (it doesn't have this api)
    find {{justfile_directory()}}/generate/.output/sdk/test -type f -exec sed -i -e "s/TEST_API_MODULE/${TEST_API_MODULE}/g" {} \;
    find {{justfile_directory()}}/generate/.output/sdk/test -type f -exec sed -i -e "s/TEST_API/${TEST_API}/g" {} \;

link-tests-cicd TARGET_DIR:
    mkdir -p {{TARGET_DIR}}/sdk/test/
    rm -rf {{TARGET_DIR}}/sdk/test/*
    ln -s {{justfile_directory()}}/test_sdk/* {{TARGET_DIR}}/sdk/test

    # these test files have been copied from the lusid sdk tests
    # rename to match values for the sdk being tested
    find {{justfile_directory()}}/test_sdk -type f -exec sed -i -e "s/TO_BE_REPLACED/${PLACEHOLDER_VALUE_FOR_TESTS}/g" {} \;
    find {{justfile_directory()}}/test_sdk -type f -exec sed -i -e "s/TEST_API_MODULE/${TEST_API_MODULE}/g" {} \;
    find {{justfile_directory()}}/test_sdk -type f -exec sed -i -e "s/TEST_API/${TEST_API}/g" {} \;
 
setup-test-local:
    @just generate-local
    @just add-tests
    echo "{\"api\":{\"personalAccessToken\":\"$FBN_ACCESS_TOKEN\",\"tokenUrl\":\"$FBN_TOKEN_URL\",\"username\":\"$FBN_USERNAME\",\"password\":\"$FBN_PASSWORD\",\"clientId\":\"$FBN_CLIENT_ID\",\"clientSecret\":\"$FBN_CLIENT_SECRET\",\"apiUrl\":\"NOT_USED\"}}" > {{justfile_directory()}}/generate/.output/sdk/secrets.json
    cp {{justfile_directory()}}/generate/.output/sdk/secrets.json {{justfile_directory()}}/generate/.output/sdk/secrets-pat.json

test-local:
    @just setup-test-local
    cd {{justfile_directory()}}/generate/.output/sdk && poetry install && poetry run pytest test

test-cicd TARGET_DIR:
    @just link-tests-cicd {{TARGET_DIR}}
    echo "{\"api\":{\"personalAccessToken\":\"$FBN_ACCESS_TOKEN\",\"tokenUrl\":\"$FBN_TOKEN_URL\",\"username\":\"$FBN_USERNAME\",\"password\":\"$FBN_PASSWORD\",\"clientId\":\"$FBN_CLIENT_ID\",\"clientSecret\":\"$FBN_CLIENT_SECRET\",\"apiUrl\":\"NOT_USED\"}}" > {{TARGET_DIR}}/sdk/secrets.json
    cp {{TARGET_DIR}}/sdk/secrets.json {{TARGET_DIR}}/sdk/secrets-pat.json
    cd {{TARGET_DIR}}/sdk && poetry install && poetry run pytest test

test-local-in-docker:
    @just setup-test-local
    docker run \
        -t \
        -e FBN_TOKEN_URL=${FBN_TOKEN_URL} \
        -e FBN_USERNAME=${FBN_USERNAME} \
        -e FBN_PASSWORD=${FBN_PASSWORD} \
        -e FBN_CLIENT_ID=${FBN_CLIENT_ID} \
        -e FBN_CLIENT_SECRET=${FBN_CLIENT_SECRET} \
        -e FBN_LUSID_API_URL=${FBN_LUSID_API_URL} \
        -e FBN_ACCESS_TOKEN=${FBN_ACCESS_TOKEN} \
        -v {{justfile_directory()}}/generate/.output/sdk:/usr/src/sdk/ \
        -w /usr/src/sdk \
        python:3.11 bash -c "pip install poetry && poetry install && poetry run pytest"

generate TARGET_DIR FLAG="":
    @just generate-local {{FLAG}}
    
    # need to remove the created content before copying over the top of it.
    # this prevents deleted content from hanging around indefinitely.
    rm -rf {{TARGET_DIR}}/sdk/lusid
    rm -rf {{TARGET_DIR}}/sdk/docs
    
    cp -R generate/.output/* {{TARGET_DIR}}

# Generate an SDK from a swagger.json and copy the output to the TARGET_DIR
generate-cicd TARGET_DIR FLAG="":
    # check if the notifications fix flag has been set
    if [ "{{FLAG}}" != "{{fix_notifications_v2_sdk_flag}}" ] && [ -n "{{FLAG}}" ]; then echo "unexpected flag '{{FLAG}}' ... did you mean '{{fix_notifications_v2_sdk_flag}}'?"; fi
    
    mkdir -p {{TARGET_DIR}}
    mkdir -p ./generate/.output
    envsubst < generate/config-template.json > generate/.config.json
    cp ./generate/.openapi-generator-ignore ./generate/.output/.openapi-generator-ignore
    cp ./generate/templates/description.{{APPLICATION_NAME}}.mustache ./generate/templates/description.mustache

    ./generate/generate.sh ./generate ./generate/.output {{swagger_path}} .config.json
    rm -f generate/.output/.openapi-generator-ignore

    # split the README into two, and move one up a level
    bash generate/split-readme.sh

    # try to fix the notifications sdk if flag set
    if [ "{{FLAG}}" = "{{fix_notifications_v2_sdk_flag}}" ]; then just fix-notifications-v2-sdk; fi

    # need to remove the created content before copying over the top of it.
    # this prevents deleted content from hanging around indefinitely.
    rm -rf {{TARGET_DIR}}/sdk/${PACKAGE_NAME}
    rm -rf {{TARGET_DIR}}/sdk/docs
    
    cp -R generate/.output/. {{TARGET_DIR}}
    echo "copied output to {{TARGET_DIR}}"
    ls {{TARGET_DIR}}

publish-only-local:
    docker run \
        -v $(pwd)/generate/.output:/usr/src \
        finbourne/lusid-sdk-gen-python:latest -- bash -ce "cd sdk; poetry build"
    mkdir -p ${PYPI_PACKAGE_LOCATION}
    cp generate/.output/sdk/dist/* ${PYPI_PACKAGE_LOCATION}

publish-only:
    docker run \
        -e POETRY_PYPI_TOKEN_PYPI:${PYPI_TOKEN} \
        -v $(pwd)/generate/.output:/usr/src \
        finbourne/lusid-sdk-gen-python:latest -- bash -ce "cd sdk; poetry publish"

publish-cicd SRC_DIR:
    #!/usr/bin/env bash
    set -euxo pipefail
    echo "PACKAGE_VERSION to publish: ${PACKAGE_VERSION}"
    if [ "${REPOSITORY_NAME}" == "pypi" ]; then
        poetry publish --build --directory {{SRC_DIR}}/sdk ;
    else
        poetry publish --build --repository ${REPOSITORY_NAME} --directory {{SRC_DIR}}/sdk
    fi

publish-to SRC_DIR OUT_DIR:
    echo "PACKAGE_VERSION to publish: ${PACKAGE_VERSION}"
    cd {{SRC_DIR}}/sdk
    poetry build
    cp dist/* {{OUT_DIR}}/

generate-and-publish TARGET_DIR FLAG="":
    @just generate {{TARGET_DIR}} {{FLAG}}
    @just publish-only

generate-and-publish-local FLAG="":
    @just generate-local {{FLAG}}
    @just publish-only-local

generate-and-publish-cicd OUT_DIR FLAG="":
    @just generate-cicd {{OUT_DIR}} {{FLAG}}
    @just publish-cicd {{OUT_DIR}}

fix-notifications-v2-sdk:
    bash {{justfile_directory()}}/generate/fix-notifications-v2-sdk.sh {{justfile_directory()}} ${PACKAGE_NAME}

