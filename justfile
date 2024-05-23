# Generate SDK's from a swagger.json file.
#
#  Ensure that you set the following environment variables to an appropriate value before running
#    PACKAGE_NAME
#    PROJECT_NAME
#    PACKAGE_VERSION
#    PYPI_PACKAGE_LOCATION

export PACKAGE_NAME := `echo ${PACKAGE_NAME:-lusid_drive}`
export PROJECT_NAME := `echo ${PROJECT_NAME:-lusid-drive-sdk}`
export PACKAGE_VERSION := `echo ${PACKAGE_VERSION:-2.0.0}`

export PYPI_PACKAGE_LOCATION := `echo ${PYPI_PACKAGE_LOCATION:-~/.pypi/packages}`

swagger_path := "./swagger.json"

swagger_url := "https://fbn-prd.lusid.com/drive/swagger/v0/swagger.json"

get-swagger:
    echo {{swagger_url}}
    curl -s {{swagger_url}} > swagger.json

build-docker-images: 
    docker build -t finbourne/lusid-sdk-gen-python:latest --ssh default=$SSH_AUTH_SOCK -f Dockerfile .

generate-templates:
    export PACKAGE_NAME_SPACED=${PACKAGE_NAME//_/ } && envsubst < generate/config-template.json > generate/.config.json
    docker run \
        -v {{justfile_directory()}}/.templates:/usr/src/templates \
        finbourne/lusid-sdk-gen-python:latest -- java -jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar author template -g python -o /usr/src/templates

generate-local:
    export PACKAGE_NAME_SPACED=${PACKAGE_NAME//_/ } && envsubst < generate/config-template.json > generate/.config.json
    docker run \
        -e JAVA_OPTS="-Dlog.level=error -Xmx6g" \
        -e PACKAGE_VERSION=${PACKAGE_VERSION} \
        -v {{justfile_directory()}}/generate/:/usr/src/generate/ \
        -v {{justfile_directory()}}/generate/.openapi-generator-ignore:/usr/src/generate/.output/.openapi-generator-ignore \
        -v {{justfile_directory()}}/{{swagger_path}}:/tmp/swagger.json \
        finbourne/lusid-sdk-gen-python:latest -- ./generate/generate.sh ./generate ./generate/.output /tmp/swagger.json .config.json
    rm -f generate/.output/.openapi-generator-ignore

link-tests:
    mkdir -p {{justfile_directory()}}/generate/.output/sdk/test/
    rm -rf {{justfile_directory()}}/generate/.output/sdk/test/*
    ln -s {{justfile_directory()}}/test_sdk/* {{justfile_directory()}}/generate/.output/sdk/test 

link-tests-cicd TARGET_DIR:
    mkdir -p {{TARGET_DIR}}/sdk/test/
    rm -rf {{TARGET_DIR}}/sdk/test/*
    ln -s {{justfile_directory()}}/test_sdk/* {{TARGET_DIR}}/sdk/test
 
test-local:
    @just generate-local
    @just link-tests
    cd {{justfile_directory()}}/generate/.output/sdk && poetry install && poetry run pytest test

test-cicd TARGET_DIR:
    @just link-tests-cicd {{TARGET_DIR}}
    cd {{TARGET_DIR}}/sdk && poetry install && poetry run pytest test --ignore=test/integration

test-only:
    mkdir -p {{justfile_directory()}}/generate/.output/sdk/test/
    cp -r {{justfile_directory()}}/test_sdk/* {{justfile_directory()}}/generate/.output/sdk/test 

    docker run \
        -t \
        -e FBN_TOKEN_URL=${FBN_TOKEN_URL} \
        -e FBN_USERNAME=${FBN_USERNAME} \
        -e FBN_PASSWORD=${FBN_PASSWORD} \
        -e FBN_CLIENT_ID=${FBN_CLIENT_ID} \
        -e FBN_CLIENT_SECRET=${FBN_CLIENT_SECRET} \
        -e FBN_LUSID_API_URL=${FBN_LUSID_API_URL} \
        -e FBN_APP_NAME=${FBN_APP_NAME} \
        -e FBN_ACCESS_TOKEN=${FBN_ACCESS_TOKEN} \
        -v {{justfile_directory()}}/generate/.output/sdk:/usr/src/sdk/ \
        -w /usr/src/sdk \
        python:3.11 bash -c "pip install poetry; poetry install; poetry run pytest"

generate TARGET_DIR:
    @just generate-local
    
    # need to remove the created content before copying over the top of it.
    # this prevents deleted content from hanging around indefinitely.
    rm -rf {{TARGET_DIR}}/sdk/lusid
    rm -rf {{TARGET_DIR}}/sdk/docs
    
    cp -R generate/.output/* {{TARGET_DIR}}

# Generate an SDK from a swagger.json and copy the output to the TARGET_DIR
generate-cicd TARGET_DIR:
    mkdir -p {{TARGET_DIR}}
    mkdir -p ./generate/.output
    export PACKAGE_NAME_SPACED=${PACKAGE_NAME//_/ } && envsubst < generate/config-template.json > generate/.config.json
    cp ./generate/.openapi-generator-ignore ./generate/.output/.openapi-generator-ignore

    ./generate/generate.sh ./generate ./generate/.output {{swagger_path}} .config.json
    rm -f generate/.output/.openapi-generator-ignore

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

generate-and-publish TARGET_DIR:
    @just generate {{TARGET_DIR}}
    @just publish-only

generate-and-publish-local:
    @just generate-local
    @just publish-only-local

generate-and-publish-cicd OUT_DIR:
    @just generate-cicd {{OUT_DIR}}
    @just publish-cicd {{OUT_DIR}}
