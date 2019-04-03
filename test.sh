VERSION="latest"
REGISTRY="workonline.azurecr.io"

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

# Prepare test container
echo -n "Building test image"
IMAGE_ID="$(docker build --build-arg REGISTRY="${REGISTRY}" --build-arg VERSION="${VERSION}" --quiet .)" &&
  ok || fail
echo -n "Starting container"
CONTAINER_ID="$(docker run --detach --privileged --rm "${IMAGE_ID}")" &&
  ok || fail

# Run unit test suite
echo "Running unit test suite"
docker exec --interactive --tty "${CONTAINER_ID}" pytest tests/unit/
echo -n "Retrieving coverage report"
docker cp ${CONTAINER_ID}:/root/coverage.xml ./ >/dev/null &&
  ok || fail

# Run integration test suite
echo "Running integration test suite"
docker exec --interactive --tty "${CONTAINER_ID}" pytest tests/integration/

# Drop into a shell if requested
if [[ -n "$1" ]]; then
  docker exec --interactive --tty "${CONTAINER_ID}" /bin/bash ||
    fail
fi

# Clean up
clean

exit 0
