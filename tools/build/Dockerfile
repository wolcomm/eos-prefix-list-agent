FROM fedora:31

ENV BUILD_ROOT="/root"

WORKDIR $BUILD_ROOT

RUN dnf update -y
RUN dnf install -y \
        # python3 build deps
        python3 \
        python3-devel \
        python3-pip \
        pyproject-rpm-macros \
        # for setuptools_scm
        git \
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

COPY ./eos-prefix-list-agent.spec ./rpmbuild/SPECS/
COPY ./pkg-build.sh ./
COPY ./*-build.txt ./
COPY ./manifest.yaml ./
