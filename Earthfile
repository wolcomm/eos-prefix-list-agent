VERSION 0.6

FROM python:3.7-slim
WORKDIR "/root/"

all:
    BUILD +safety
    FOR PKG IN "prefix_list_agent" "prefix_list_agent_cli"
        BUILD --build-arg PKG=$PKG +lint
        BUILD --build-arg PKG=$PKG +typecheck
        BUILD --build-arg PKG=$PKG +build-rpm
    END
    BUILD +build-swix
    BUILD --build-arg CEOS_VERSION="4.26.3M" +test
    BUILD --build-arg CEOS_VERSION="4.27.0F" +test

deps:
    RUN apt update -qq && \
        apt upgrade -qqy && \
        apt install -qqy git g++ swig libssl-dev zip
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

    LABEL org.opencontainers.image.source=https://github.com/wolcomm/eos-prefix-list-agent
    SAVE IMAGE --push ghcr.io/wolcomm/eos-prefix-list-agent/ci-deps:latest

safety:
    BUILD +deps
    FROM +deps
    RUN --secret SAFETY_API_KEY python -m pipenv run safety check --full-report

src:
    ARG --required PKG
    FROM +deps
    COPY --dir $PKG/ .
    COPY LICENSE README.md .

lint:
    ARG --required PKG
    FROM --build-arg PKG=$PKG +src
    RUN python -m pipenv run flake8 .

typecheck:
    ARG --required PKG
    FROM --build-arg PKG=$PKG +src
    RUN python -m pipenv run mypy --package $PKG

sdist:
    ARG --required PKG
    FROM --build-arg PKG=$PKG +src
    COPY --dir .git/ .
    RUN python -m pipenv run python -m build --sdist --outdir dist/ $PKG/

    SAVE ARTIFACT dist/*.tar.gz AS LOCAL dist/sdist/

build-rpm:
    FROM fedora:31

    WORKDIR "/root"

    RUN dnf update -y
    RUN dnf install -y \
            # python build deps
            python3 python3-devel python3-pip \
            python2 python2-devel python2-pip python2-wheel \
            pyproject-rpm-macros \
            # rpm build tools
            rpm-build rpm-devel rpmlint rpmdevtools \
            # for switools
            gcc-c++ swig openssl-devel zip

    RUN python3 -m pip install \
            --disable-pip-version-check \
            --progress-bar off \
            --no-warn-script-location \
            --user \
            pipenv
    COPY Pipfile Pipfile.lock .
    RUN python3 -m pipenv lock --dev-only -r > requirements.txt
    RUN python3 -m pip install \
            --disable-pip-version-check \
            --progress-bar off \
            --prefix /usr \
            --ignore-installed \
            -r "requirements.txt"
    
    ARG --required PKG
    RUN rpmdev-setuptree
    COPY packaging/rpm/$PKG.spec ./rpmbuild/SPECS/
    COPY --build-arg PKG=$PKG +sdist/*.tar.gz rpmbuild/SOURCES/

    RUN SDIST="$(find rpmbuild/SOURCES/ -name '*.tar.gz' | head -n1)" && \
        VERSION="$(tar zxfO "$SDIST" --no-anchored PKG-INFO | grep '^Version:' | head -n1 | cut -d' ' -f2)" && \
        echo -n "$VERSION" > VERSION && \
        rpmbuild -ba rpmbuild/SPECS/$PKG.spec -D "_version $VERSION"

    SAVE ARTIFACT VERSION
    SAVE ARTIFACT rpmbuild/RPMS/**/*.rpm AS LOCAL dist/rpm/

    LABEL org.opencontainers.image.source=https://github.com/wolcomm/eos-prefix-list-agent
    SAVE IMAGE --push ghcr.io/wolcomm/eos-prefix-list-agent/ci-build-rpm:$PKG

build-swix:
    FROM +deps

    RUN mkdir -p dist rpms

    FOR PKG IN "prefix_list_agent" "prefix_list_agent_cli"
        BUILD --build-arg PKG=$PKG +build-rpm
        COPY --build-arg PKG=$PKG +build-rpm/*.rpm rpms/
    END

    COPY --build-arg PKG="prefix_list_agent" +build-rpm/VERSION ./

    COPY packaging/swix/manifest.yaml .
    RUN SWIX="dist/eos-prefix-list-agent-$(cat VERSION).swix" && \
        python -m pipenv run swix-create -i manifest.yaml "$SWIX" rpms/*.rpm

    SAVE ARTIFACT dist/*.swix AS LOCAL dist/swix/

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

    COPY prefix_list_agent/pyproject.toml .
    COPY tests/data/startup-config /mnt/flash/
    COPY --dir tests .

    SAVE IMAGE --cache-from ghcr.io/wolcomm/eos-prefix-list-agent/ci-test:$CEOS_VERSION

    ARG LOCAL_PACKAGE
    IF [ -n "$LOCAL_PACKAGE" ]
        COPY $LOCAL_PACKAGE /mnt/flash/
    ELSE
        COPY +build-swix/*.swix /mnt/flash/
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
