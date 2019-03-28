#!/usr/bin/env bash
#
# Copyright (c) 2019 Workonline Communications (Pty) Ltd. All rights reserved.
#
# The contents of this file are licensed under the MIT License
# (the "License"); you may not use this file except in compliance with the
# License.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

usage() {
    cat <<EOF
Usage: ${0##*/} [VERSION]

    Create a new tagged release for the current repo at VERSION.
    If no arguments are provided, VERSION will be read from STDIN.

    Example:
        $ package/__meta__.py | ${0##*/}

EOF
}

error() { echo "$@" 1>&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# Set VERSION
if [[ $# -gt 1 ]]; then
    echo "Too many arguments provided"
    usage; exit 1
fi
if [[ -z "$1" ]]; then
    echo "Reading from STDIN. End with Ctrl+D..."
    VERSION=$(cat)
else
    VERSION=$1
fi
if [[ "$VERSION" == "--help" || "$VERSION" == "-h" ]]; then
    usage; exit 0
fi
if [[ ! "$VERSION" =~ ^[0-9]+(\.[0-9]+)+$ ]]; then
    PRE="pre-"
fi
echo -e "Creating ${PRE}release\n"

# Check that we have hub installed

have "hub" || error "'hub' is required for creating github releases."

PREVIOUS=$(hub release | sort -V | head -n 1) ||
    error "Getting previous release failed"

if [[ -n "$PREVIOUS" ]]; then
    SINCE=" since [${PREVIOUS}]($(hub browse --url)/releases/tag/${PREVIOUS}):" ||
        error "Getting repository URL failed"
    LOG_RANGE="${PREVIOUS}..HEAD"
else
    LOG_RANGE="HEAD"
fi

CHANGE_LOG=$(git log ${LOG_RANGE} --oneline --no-color) ||
    error "Getting git log failed"
RELEASE_MSG=$(cat <<EOF
${VERSION}

## Change Log
Changes${SINCE}:
${CHANGE_LOG}
EOF
)
CMD="hub release create ${PRE:+-p} -F - ${VERSION}"

echo -e "${RELEASE_MSG}\n"
echo "Running: ${CMD}" && echo -e "${RELEASE_MSG}" | ${CMD} && echo "Done" ||
    error "Failed to create release"
