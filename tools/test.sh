#!/usr/bin/env bash

set -eo pipefail

DEFAULT_VERSION="4.26.1F"
REGISTRY="workonline.azurecr.io"
USAGE="$(cat <<EOF
usage: $0 ([-d] [-v <version>] [-t <pytest-args>] | -h)
    -d                  Drop into a bash shell on the cEOS container after testing.
    -p <package>        SWIX/RPM extension package
    -t <pytest-args>    Arguments to pass to pytest
    -T <tests-dir>      Tests directory to bind-mount into container
    -v <version>        Test on cEOS <version>. default: $DEFAULT_VERSION.
    -h                  Display this help message.
EOF
)"

ok() { echo "  [OK]"; }
fail() {
  if [ -z "$1" ]; then clean; fi
  echo "  [FAIL]"; exit 1;
}

clean() {
  if [[ "${CONTAINER_ID}" ]]; then
    echo -n "Shutting down container"
    docker kill "${CONTAINER_ID}" >/dev/null &&
      ok || fail 1
  fi
  if [[ "${IMAGE_ID}" ]]; then
    echo -n "Cleaning up image"
    docker image rm "${IMAGE_ID}" >/dev/null &&
      ok || fail 1
  fi
}

while getopts "dp:t:T:v:h" OPT; do
    case $OPT in
        d)
            DEBUG=1
            ;;
        p)
            PACKAGE="$OPTARG"
            ;;
        t)
            PYTEST_ARGS="$OPTARG"
            ;;
        T)
            TESTS_DIR="$OPTARG"
            ;;
        v)
            VERSION="$OPTARG"
            ;;
        h)
            echo "$USAGE"
            exit 0
            ;;
        *)
            echo "$USAGE"
            exit 1
            ;;
    esac
done

if [[ -z "$VERSION" ]]; then
    echo "Using default cEOS version: $DEFAULT_VERSION"
    VERSION="$DEFAULT_VERSION"
fi

if [[ -z "$PACKAGE" ]]; then
    echo "ERROR: -p <package> is required"
    exit 2
fi

if [[ -d "$PACKAGE" ]]; then
    echo "Searching for packages in directory $PACKAGE"
    PACKAGE="$(find ${PACKAGE} -name '*.swix' | head -n 1)"
    if [[ -f "$PACKAGE" ]]; then
        echo "Found package ${PACKAGE}"
    else
        echo "ERROR: Unable to find package"
        exit 1
    fi
fi

if [[ -z "$TESTS_DIR" ]]; then
    echo "ERROR: -T <tests-dir> is required"
    exit 2
fi

# Prepare test container
echo -n "Building test image"
IMAGE_ID="$(docker build --build-arg REGISTRY="${REGISTRY}" --build-arg VERSION="${VERSION}" --quiet tools/test)" &&
  ok || fail
echo -n "Starting container"
CONTAINER_ID="$(docker run --detach --privileged --rm -v "$(readlink -f $TESTS_DIR):/root/tests:ro" "${IMAGE_ID}")" &&
  ok || fail

echo -n "Copying extension package"
docker cp ${PACKAGE} ${CONTAINER_ID}:/mnt/flash &&
  ok || fail

# Run test suite
echo "Running test suite"
docker exec --tty "${CONTAINER_ID}" pytest \
    --extension-pkg "$(basename $PACKAGE)" \
    --exec-path "/usr/bin" \
    ${PYTEST_ARGS}
TEST_RESULT=$?

# Drop into a shell if requested
if [[ -n "$DEBUG" ]]; then
  docker exec --interactive --tty "${CONTAINER_ID}" /bin/bash ||
    fail
fi

# Clean up
clean

exit $TEST_RESULT
