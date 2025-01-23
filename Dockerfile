FROM rust:slim-buster AS rust

RUN cargo install just

FROM openapitools/openapi-generator-cli:v7.0.1 AS maven

# These are required to compile Python from source
RUN apt update && apt -y install jq git gettext-base libicu-dev
RUN apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev liblzma-dev

# Compiling Python from source
RUN curl -O https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tar.xz
RUN tar -xf Python-3.8.2.tar.xz
RUN cd Python-3.8.2 && ./configure && make -j $(nproc) && make install && ln -s $(which python3.8) /usr/bin/python3

# Check Python install & update pip
RUN python3.8 -m pip install --upgrade pip

ENV PATH=${PATH}:/root/.local/bin

# Installing poetry through pip is more reliable then scripts changed in CTOOLS-85
RUN pip install poetry
RUN poetry --version

RUN mkdir -p /usr/src/
WORKDIR /usr/src/

# Make ssh dir
# Create known_hosts
# Add github key
RUN mkdir /root/.ssh/ \
    && touch /root/.ssh/known_hosts \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts

RUN --mount=type=ssh \
    git clone git@github.com:finbourne/lusid-sdk-doc-templates.git /tmp/docs \
    && git clone git@github.com:finbourne/lusid-sdk-workflow-template.git /tmp/workflows

COPY generate/ /usr/src/generate
COPY ./justfile /usr/src/
COPY test_sdk /usr/src/test_sdk

# sometimes poetry publish fails due to connection timeouts
# default is 15 secs, I've increased to 120 to mitigate.
ENV POETRY_REQUESTS_TIMEOUT=120
