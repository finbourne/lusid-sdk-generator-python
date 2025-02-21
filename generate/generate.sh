#!/bin/bash

set -EeTuo pipefail

failure() {
    local lineno=$1
    local msg=$2
    echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

if [[ ${#1} -eq 0 ]]; then
    echo
    echo "[ERROR] generate folder file path not specified"
    exit 1
fi

if [[ ${#2} -eq 0 ]]; then
    echo
    echo "[ERROR] output folder file path not specified"
    exit 1
fi

if [[ ${#3} -eq 0 ]]; then
    echo
    echo "[ERROR] swagger file not specified"
    exit 1
fi

gen_root=$1
output_folder=$2
swagger_file=$3
config_file_name=$4
sdk_output_folder=$output_folder/sdk
JAVA_OPTS=${JAVA_OPTS:--Dlog.level=info}

if [[ -z $config_file_name || ! -f $gen_root/$config_file_name ]] ; then
    echo "[INFO] '$config_file_name' not found, using default config.json"
    config_file_name=.config.json
fi

echo "[INFO] root generation      : $gen_root"
echo "[INFO] output folder        : $output_folder"
echo "[INFO] swagger file         : $swagger_file"
echo "[INFO] config file          : $config_file_name"
echo "[INFO] generating api tests : $GENERATE_API_TESTS"

ignore_file_name=.openapi-generator-ignore
config_file=$gen_root/$config_file_name
ignore_file=$output_folder/$ignore_file_name

app_name=$(cat $config_file | jq -r .packageName)

#   remove all previously generated files
shopt -s extglob
echo "[INFO] removing previous sdk: $sdk_output_folder"
rm -rf $sdk_output_folder
shopt -u extglob

# ignore files
mkdir -p $sdk_output_folder
cp $ignore_file $sdk_output_folder

# sdk_version=$(cat $swagger_file | jq -r '.info.version')
# sdk_version=${PACKAGE_VERSION}
# cat $config_file | jq -r --arg SDK_VERSION "$sdk_version" '.packageVersion |= $SDK_VERSION' > temp && mv temp $config_file

# remove the verbose description
cat $swagger_file | jq -r '.info.description |= "FINBOURNE Technology"' > $sdk_output_folder/swagger.json

echo "[INFO] generating sdk version: ${PACKAGE_VERSION}"

# generate the SDK
java ${JAVA_OPTS} -jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar generate \
    --global-property modelTests=true,debugModels=true,apiTests=${GENERATE_API_TESTS} \
    -i $sdk_output_folder/swagger.json \
    -g python \
    -o $sdk_output_folder \
    -t $gen_root/templates \
    -c $config_file > $sdk_output_folder/models.json # enable the following if a manual override is required 
    
    # --skip-validate-spec


rm -rf $sdk_output_folder/.openapi-generator/
rm -f $sdk_output_folder/.gitlab-ci.yml $sdk_output_folder/setup.cfg
rm -f $sdk_output_folder/.openapi-generator-ignore
rm -f $sdk_output_folder/swagger.json
rm -rf $sdk_output_folder/.github/
# rm -f $output_folder/.openapi-generator-ignore

mkdir -p $output_folder/docs
cp -R /tmp/docs/docs/* $output_folder/docs
mkdir -p $output_folder/.github/
cp -R /tmp/workflows/github/* $output_folder/.github/
touch $sdk_output_folder/$app_name/py.typed
# list all model files
model_files=$(find $sdk_output_folder/$app_name/models -type f -maxdepth 1 )
for file in $model_files
do
    # fixes two bugs in generated code (can't be done in template)
    # backslashes are incorrectly escaped in regex paths - which causes an odd number of backslashes when they should be even
    # dict type is imported as a model (isMap is not set)
    new_contents=$(sed 's/&\\\\\"/\&\\"/' $file | sed '/from lusid\.models\.dict\[str,_result_value\] import Dict\[str, ResultValue\]/d')
    echo "$new_contents" > $file
done

# list all API files, and text replace. Workaround until we start using pydantic directly with OpenApi generator
api_files=$(find $sdk_output_folder/$app_name/api -type f -maxdepth 1)
for file in $api_files
do
   # replace "from pydantic import" with "from pydantic.v1 import"
  new_contents=$(sed 's/from pydantic import/from pydantic.v1 import/' $file)
  echo "$new_contents" > $file
done

(
    cd $sdk_output_folder;
    poetry install;
    # poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics;
)