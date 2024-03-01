FROM rust:slim-buster as rust

RUN cargo install just

FROM openapitools/openapi-generator-cli:v7.0.1 as maven

RUN apt update && apt -y install jq git gettext-base libicu-dev
# need to install the following for python
RUN apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev liblzma-dev \
    && cd tmp \
    && curl -O https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tar.xz \
    && tar -xf Python-3.8.2.tar.xz \
    && cd Python-3.8.2 \
    && ./configure --enable-optimizations --enable-loadable-sqlite-extensions \
    && make -j 4 \
    && make altinstall \
    && ln -s $(which python3.8) /usr/bin/python3 \
    && ln -s $(which python3.8) /usr/bin/python \
    && curl -sSL https://install.python-poetry.org | python3 -

ENV PATH=${PATH}:/root/.local/bin

COPY --from=rust /usr/local/cargo/bin/just /usr/bin/just

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
