#!/bin/bash

set -xeuo pipefail

# install python build requirements into /usr
# rpmbuild does not find modules in /usr/local, and the packaged versions
# are either missing or outdated.
python3 -m pip install \
    --disable-pip-version-check \
    --progress-bar off \
    --prefix /usr \
    --ignore-installed \
    -r "requirements-build.txt"

# build binary and source rpms
rpmbuild -ba rpmbuild/SPECS/eos-prefix-list-agent.spec -D "_version ${VERSION}" -v

# build swix and copy the build products into the source tree
OUT_DIR="dist"
mkdir -p "$OUT_DIR"
SWIX="${OUT_DIR}/eos-prefix-list-agent-${VERSION}.swix"
swix-create -i manifest.yaml \
    $SWIX \
    $BUILD_ROOT/rpmbuild/RPMS/**/*.rpm
cp ${BUILD_ROOT}/rpmbuild/SRPMS/*.rpm \
    ${BUILD_ROOT}/rpmbuild/RPMS/**/*.rpm \
    "${OUT_DIR}/"
