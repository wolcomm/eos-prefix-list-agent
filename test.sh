#!/usr/bin/env bash

DEFAULT_VERSION="4.26.1F"
REGISTRY="workonline.azurecr.io"
USAGE="$(cat <<EOF
usage: $0 ([-d] [-v <version>] [-t <pytest-args>] | -h)
    -d                  Drop into a bash shell on the cEOS container after testing.
    -v <version>        Test on cEOS <version>. default: $DEFAULT_VERSION.
    -t <pytest-args>    Arguments to pass to pytest
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

while getopts "dv:t:h" OPT; do
    case $OPT in
        d)
            DEBUG=1
            ;;
        v)
            VERSION="$OPTARG"
            ;;
        t)
            PYTEST_ARGS="$OPTARG"
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

# Prepare test container
echo -n "Building test image"
IMAGE_ID="$(docker build --build-arg REGISTRY="${REGISTRY}" --build-arg VERSION="${VERSION}" --quiet .)" &&
  ok || fail
echo -n "Starting container"
CONTAINER_ID="$(docker run --detach --privileged --rm "${IMAGE_ID}")" &&
  ok || fail

# Run test suite
echo "Running test suite"
docker exec --tty "${CONTAINER_ID}" pytest "${PYTEST_ARGS}"
TEST_RESULT=$?

# Retrieve coverage report
echo -n "Retrieving coverage report"
docker cp ${CONTAINER_ID}:/root/coverage.xml ./ >/dev/null &&
  ok || fail

# Drop into a shell if requested
if [[ -n "$DEBUG" ]]; then
  docker exec --interactive --tty "${CONTAINER_ID}" /bin/bash ||
    fail
fi

# Clean up
clean

exit $TEST_RESULT
