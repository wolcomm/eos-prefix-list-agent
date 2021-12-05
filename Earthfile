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
        apt install -qqy git
    RUN python -m pip install --upgrade pip

    RUN mkdir -p src
    WORKDIR "src/"
    COPY --dir bin/ packaging/ prefix_list_agent/ tests/ .
    COPY LICENSE pyproject.toml README.md setup.cfg tox.ini .

    LABEL org.opencontainers.image.source=https://github.com/wolcomm/eos-prefix-list-agent
    SAVE IMAGE --push ghcr.io/wolcomm/eos-prefix-list-agent/ci-deps:latest

safety:
    FROM +deps
    RUN python -m pip install --user -r packaging/requirements-safety.txt
    RUN python -m safety check -r packaging/requirements-dev.txt --full-report

lint:
    FROM +deps
    RUN python -m pip install --user -r packaging/requirements-lint.txt
    RUN python -m flake8 .

typecheck:
    FROM +deps
    RUN python -m pip install --user -r packaging/requirements-typecheck.txt
    RUN python -m mypy \
        --package prefix_list_agent \
        --config-file tox.ini

sdist:
    FROM +deps
    COPY --dir .git/ .
    RUN python -m pip install --user build==0.7.0
    RUN python -m build --sdist --outdir dist/

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

    COPY ./tools/build/eos-prefix-list-agent.spec ./rpmbuild/SPECS/
    COPY ./tools/build/*-build.txt ./
    COPY ./tools/build/manifest.yaml ./

    RUN python3 -m pip install \
            --disable-pip-version-check \
            --progress-bar off \
            --prefix /usr \
            --ignore-installed \
            -r "requirements-build.txt"
    
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

    COPY tools/test/requirements-test.txt ./

    RUN python3 -m pip install --user -r "requirements-test.txt"

    COPY tools/test/.coveragerc ./
    COPY tools/test/startup-config /mnt/flash
    COPY --dir tests ./

    COPY +build/*.swix /mnt/flash

    RUN SWIX="$(basename $(find /mnt/flash -name '*.swix'))" && \
        echo "copy flash:/${SWIX} extension:" > install-extension-script && \
        echo "extension ${SWIX}" >> install-extension-script

    SAVE ARTIFACT install-extension-script

    LABEL org.opencontainers.image.source=https://github.com/wolcomm/eos-prefix-list-agent
    SAVE IMAGE eos-prefix-list-agent-test:$CEOS_VERSION
    SAVE IMAGE --push ghcr.io/wolcomm/eos-prefix-list-agent/ci-test:$CEOS_VERSION

test:
    FROM earthly/dind:alpine

    ARG --required CEOS_VERSION
    BUILD --build-arg CEOS_VERSION=$CEOS_VERSION +test-image

    COPY +test-image/install-extension-script ./

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
            docker exec --tty test .local/bin/pytest -vs \
                --strict-markers \
                --cov \
                --cov-report="term-missing" \
                --cov-report="xml" \
                --cov-branch && \
            docker cp test:/root/coverage.xml ./
    END

    SAVE ARTIFACT coverage.xml AS LOCAL coverage.xml
