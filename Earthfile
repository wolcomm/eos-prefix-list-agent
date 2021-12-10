VERSION 0.6

FROM python:3.7-slim
WORKDIR "/root/"

all:
    BUILD +deps
    BUILD +safety
    BUILD +lint
    BUILD +typecheck
    BUILD +build
    BUILD --build-arg CEOS_VERSION="4.26.3M" +test
    BUILD --build-arg CEOS_VERSION="4.27.0F" +test

deps:
    RUN apt update -qq && \
        apt upgrade -qqy && \
        apt install -qqy git g++ swig libssl-dev
    RUN python -m pip install \
        --progress-bar off \
        --upgrade pip
    RUN python -m pip install \
        --progress-bar off \
        --no-warn-script-location \
        --user \
        pipenv

    RUN mkdir -p src
    WORKDIR "src/"
    COPY Pipfile Pipfile.lock .
    RUN python -m pipenv sync --dev

    COPY --dir share/ lib/ bin/ prefix_list_agent/ tests/ .
    COPY LICENSE README.md pyproject.toml setup.cfg .

    LABEL org.opencontainers.image.source=https://github.com/wolcomm/eos-prefix-list-agent
    SAVE IMAGE --push ghcr.io/wolcomm/eos-prefix-list-agent/ci-deps:latest

safety:
    BUILD +deps
    FROM +deps
    RUN --secret SAFETY_API_KEY python -m pipenv run safety check --full-report

lint:
    FROM +deps
    RUN python -m pipenv run flake8 .

typecheck:
    FROM +deps
    RUN python -m pipenv run mypy --package prefix_list_agent

sdist:
    FROM +deps
    COPY --dir .git/ .
    RUN python -m pipenv run python -m build --sdist --outdir dist/

    SAVE ARTIFACT dist/*.tar.gz AS LOCAL dist/sdist/

build:
    FROM fedora:31

    WORKDIR "/root"

    RUN dnf update -y
    RUN dnf install -y \
            # python3 build deps
            python3 \
            python3-devel \
            python3-pip \
            pyproject-rpm-macros \
            # rpm build tools
            rpm-build \
            rpm-devel \
            rpmlint \
            rpmdevtools \
            # for switools
            gcc-c++ \
            swig \
            openssl-devel

    RUN rpmdev-setuptree

    COPY packaging/rpm/eos-prefix-list-agent.spec ./rpmbuild/SPECS/
    COPY packaging/swix/manifest.yaml .
    COPY Pipfile Pipfile.lock .

    RUN python3 -m pip install \
            --disable-pip-version-check \
            --progress-bar off \
            --no-warn-script-location \
            --user \
            pipenv
    RUN python3 -m pipenv lock --dev-only -r > requirements.txt
    RUN python3 -m pip install \
            --disable-pip-version-check \
            --progress-bar off \
            --prefix /usr \
            --ignore-installed \
            -r "requirements.txt"
    
    COPY +sdist/*.tar.gz rpmbuild/SOURCES/

    RUN SDIST="$(find rpmbuild/SOURCES/ -name '*.tar.gz' | head -n1)" && \
        VERSION="$(tar zxfO "$SDIST" --no-anchored PKG-INFO | grep '^Version:' | head -n1 | cut -d' ' -f2)" && \
        rpmbuild -ba rpmbuild/SPECS/eos-prefix-list-agent.spec -D "_version $VERSION" && \
        mkdir -p dist && \
        SWIX="dist/eos-prefix-list-agent-${VERSION}.swix" && \
        swix-create -i manifest.yaml "$SWIX" rpmbuild/RPMS/**/*.rpm

    SAVE ARTIFACT dist/*.swix AS LOCAL dist/swix/

    LABEL org.opencontainers.image.source=https://github.com/wolcomm/eos-prefix-list-agent
    SAVE IMAGE --push ghcr.io/wolcomm/eos-prefix-list-agent/ci-build:latest

test-image:
    ARG --required CEOS_VERSION
    FROM workonline.azurecr.io/ceos-lab:$CEOS_VERSION
    WORKDIR "/root"

    RUN python3 -m ensurepip --default-pip
    RUN python3 -m pip install --upgrade pip

    COPY Pipfile Pipfile.lock .

    RUN python3 -m pip install \
        --user \
        --no-warn-script-location \
        --progress-bar off \
        pipenv
    RUN python3 -m pipenv sync --system

    COPY pyproject.toml .
    COPY tests/data/startup-config /mnt/flash/
    COPY --dir tests .

    SAVE IMAGE --cache-from ghcr.io/wolcomm/eos-prefix-list-agent/ci-test:$CEOS_VERSION

    ARG LOCAL_PACKAGE
    IF [ -n "$LOCAL_PACKAGE" ]
        COPY $LOCAL_PACKAGE /mnt/flash/
    ELSE
        COPY +build/*.swix /mnt/flash/
    END

    RUN SWIX="$(basename $(find /mnt/flash -name '*.swix'))" && \
        echo "copy flash:/${SWIX} extension:" > install-extension-script && \
        echo "extension ${SWIX}" >> install-extension-script

    SAVE ARTIFACT install-extension-script

    LABEL org.opencontainers.image.source=https://github.com/wolcomm/eos-prefix-list-agent
    SAVE IMAGE --push ghcr.io/wolcomm/eos-prefix-list-agent/ci-test:$CEOS_VERSION

test:
    FROM earthly/dind:alpine

    ARG --required CEOS_VERSION
    BUILD --build-arg CEOS_VERSION=$CEOS_VERSION +test-image

    COPY +test-image/install-extension-script .

    WITH DOCKER --load test-image:latest=+test-image --build-arg CEOS_VERSION=$CEOS_VERSION
        RUN docker run --detach --privileged --rm --name test test-image:latest && \
            t=30; while [[ $t -gt 0 ]]; do \
                echo -n "."; \
                if docker exec --tty test /usr/bin/Cli -c 'show version' >/dev/null; then \
                    started=1 && break; \
                fi; \
                sleep 1; \
                let t--; \
            done; \
            [[ $started ]] && \
            docker exec --tty test Cli -p 15 -c "$(cat install-extension-script)" && \
            docker exec --tty test python3 -m pytest && \
            docker cp test:/root/coverage.xml ./
    END

    SAVE ARTIFACT coverage.xml AS LOCAL coverage.xml

docs:
    FROM peaceiris/mdbook:latest
    WORKDIR "/root"

    COPY --dir docs .

    RUN mdbook build docs/

    SAVE ARTIFACT docs/book/ AS LOCAL dist/

clean:
    LOCALLY
    RUN rm -rf dist/ coverage.xml
