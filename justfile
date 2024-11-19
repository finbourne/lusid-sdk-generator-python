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
export TEST_API := `echo ${TEST_API:-ApplicationMetadataApi}`
export TEST_METHOD := `echo ${TEST_METHOD:-'list_access_controlled_resources('}`
export GENERATE_API_TESTS := `echo ${GENERATE_API_TESTS:-false}`

swagger_path := "./swagger.json"

swagger_url := "https://fbn-prd.lusid.com/api/swagger/v0/swagger.json"

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
    # generate the sdk
    rm -r {{justfile_directory()}}/generate/.output || true # ensure a clean output dir before starting
    envsubst < generate/config-template.json > generate/.config.json
    # Basic check if file exists
    if [ -f "./generate/templates/description.{{APPLICATION_NAME}}.mustache" ]; then \
        cp ./generate/templates/description.{{APPLICATION_NAME}}.mustache ./generate/templates/description.mustache; \
    else \
        echo "[INTERNAL] FINBOURNE Technology {{APPLICATION_NAME}} SDK" > ./generate/templates/description.mustache; \
    fi
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
    
    # make the necessary post-generation fixes to the sdks using the 'oneOf' openapi feature
    # caused by a bug in the python generator
    if [ "{{APPLICATION_NAME}}" = "notifications" ] || [ "{{APPLICATION_NAME}}" = "workflow" ]; then just make-fix-for-one-of; fi

    echo "Application name: $APPLICATION_NAME"

    if [ "{{APPLICATION_NAME}}" = "access" ]; then just make-import-fix; fi

add-tests:
    mkdir -p {{justfile_directory()}}/generate/.output/sdk/test/
    rm -rf {{justfile_directory()}}/generate/.output/sdk/test/*
    cp -R {{justfile_directory()}}/test_sdk/* {{justfile_directory()}}/generate/.output/sdk/test

    # these test files have been copied from the lusid sdk tests
    # rename to match values for the sdk being tested
    find {{justfile_directory()}}/generate/.output/sdk/test -type f -exec sed -i -e "s/TO_BE_REPLACED/${PACKAGE_NAME}/g" {} \;

    # note the default values at the top of this justfile won't work for the horizon or luminesce sdk
    # (they don't have this api/method)
    find {{justfile_directory()}}/generate/.output/sdk/test -type f -exec sed -i -e "s/TEST_API_MODULE/${TEST_API_MODULE}/g" {} \;
    find {{justfile_directory()}}/generate/.output/sdk/test -type f -exec sed -i -e "s/TEST_API/${TEST_API}/g" {} \;
    find {{justfile_directory()}}/generate/.output/sdk/test -type f -exec sed -i -e "s/TEST_METHOD/${TEST_METHOD}/g" {} \;

link-tests-cicd TARGET_DIR:
    mkdir -p {{TARGET_DIR}}/sdk/test/
    rm -rf {{TARGET_DIR}}/sdk/test/*
    ln -s {{justfile_directory()}}/test_sdk/* {{TARGET_DIR}}/sdk/test

    # these test files have been copied from the lusid sdk tests
    # rename to match values for the sdk being tested
    find {{justfile_directory()}}/test_sdk -type f -exec sed -i -e "s/TO_BE_REPLACED/${PLACEHOLDER_VALUE_FOR_TESTS}/g" {} \;
    find {{justfile_directory()}}/test_sdk -type f -exec sed -i -e "s/TEST_API_MODULE/${TEST_API_MODULE}/g" {} \;
    find {{justfile_directory()}}/test_sdk -type f -exec sed -i -e "s/TEST_API/${TEST_API}/g" {} \;
    find {{justfile_directory()}}/test_sdk -type f -exec sed -i -e "s/TEST_METHOD/${TEST_METHOD}/g" {} \;
 
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
    mkdir -p {{TARGET_DIR}}
    mkdir -p ./generate/.output
    envsubst < generate/config-template.json > generate/.config.json
    cp ./generate/.openapi-generator-ignore ./generate/.output/.openapi-generator-ignore
    # Basic check if file exists
    if [ -f "./generate/templates/description.{{APPLICATION_NAME}}.mustache" ]; then \
        cp ./generate/templates/description.{{APPLICATION_NAME}}.mustache ./generate/templates/description.mustache;
    else \
        echo "[INTERNAL] FINBOURNE Technology {{APPLICATION_NAME}} SDK" > ./generate/templates/description.mustache; \
    fi

    ./generate/generate.sh ./generate ./generate/.output {{swagger_path}} .config.json
    rm -f generate/.output/.openapi-generator-ignore

    # split the README into two, and move one up a level
    bash generate/split-readme.sh

    # make the necessary post-generation fixes to the sdks using the 'oneOf' openapi feature
    # caused by a bug in the python generator
    if [ "{{APPLICATION_NAME}}" = "notifications" ] || [ "{{APPLICATION_NAME}}" = "workflow" ]; then just make-fix-for-one-of; fi

    if [ "{{APPLICATION_NAME}}" = "access" ]; then just make-import-fix; fi

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

make-fix-for-one-of:
    bash {{justfile_directory()}}/generate/fix-files-for-one-of.sh {{justfile_directory()}} ${PACKAGE_NAME} ${APPLICATION_NAME}

make-import-fix:
    bash {{justfile_directory()}}/generate/fix-imports-for-access.sh \
    {{justfile_directory()}}/generate/.output/sdk/finbourne_access/models/policy_selector_definition.py \
    "from finbourne_access.models.selector_definition import SelectorDefinition" \
    "PolicySelectorDefinition.update_forward_refs()"
    bash {{justfile_directory()}}/generate/fix-imports-for-access.sh \
    {{justfile_directory()}}/generate/.output/sdk/finbourne_access/models/selector_definition.py \
    "from finbourne_access.models.policy_selector_definition import PolicySelectorDefinition" \
    "SelectorDefinition.update_forward_refs()"