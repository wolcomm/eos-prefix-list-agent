#!/usr/bin/env bash

set -eo pipefail

USAGE="$(cat <<EOF
usage: $0 ([-d] [-s <sdist-path] | -h)
    -d                  Drop into a bash shell on the cEOS container after building.
    -s <sdist-path>     Path to sdist archive
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

while getopts "ds:h" OPT; do
    case $OPT in
        d)
            DEBUG=1
            ;;
        s)
            SDIST="$OPTARG"
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

if [[ -z "$SDIST" ]]; then
    echo "ERROR: -s <sdist-path> is required"
    echo "$USAGE"
    exit 2
fi

if [[ -d "$SDIST" ]]; then
    echo "$SDIST is a directory"
    SDIST="$(find ${SDIST} -name '*.tar.gz' | head -n 1)"
    if [[ -f "$SDIST" ]]; then
        echo "Found sdist ${SDIST}"
    else
        echo "Unable to find sdist"
        exit 1
    fi
fi

echo -n "Building package version: "
VERSION="$(tar zxfO "${SDIST}" --no-anchored PKG-INFO | grep '^Version:' | head -n 1 | cut -d ' ' -f 2)" || fail
echo "${VERSION}"

# Prepare build container
echo -n "Building build container image"
IMAGE_ID="$(docker build --quiet tools/build)" &&
  ok || fail
echo "Starting build container"
CONTAINER_ID="$(docker run --detach --rm --env "VERSION=${VERSION}" "${IMAGE_ID}" /usr/bin/sleep infinity)" &&
  ok || fail

echo -n "Copying sdist into build container"
docker cp "${SDIST}" "${CONTAINER_ID}:/root/rpmbuild/SOURCES/" >/dev/null &&
  ok || fail

echo "Building packages"
docker exec --tty "${CONTAINER_ID}" /root/pkg-build.sh
BUILD_RESULT=$?

echo -n "Retrieving built packages"
OUT_DIR="bdist"
mkdir -p "${OUT_DIR}"
docker cp "${CONTAINER_ID}:/root/dist" "$OUT_DIR/$VERSION" >/dev/null &&
  ok || fail

# Drop into a shell if requested
if [[ -n "$DEBUG" ]]; then
  docker exec --interactive --tty "${CONTAINER_ID}" /bin/bash ||
    fail
fi

# Clean up
clean

exit ${BUILD_RESULT}
