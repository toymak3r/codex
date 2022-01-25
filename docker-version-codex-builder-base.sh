#!/bin/bash
# Compute the version tag for ajslater/codex-builder-base
set -euo pipefail
CODEX_BASE_VERSION=$(./docker-version-codex-base.sh)
# shellcheck disable=SC2046
read -ra SHELLCHECK_DEPS <<<$(find vendor/shellcheck -type f \( ! -name "*~" \))
# shellcheck disable=SC2046
read -ra PYTHON_CACHER_DEPS <<<$(find python_cacher -type f \( \
    ! -path "*__pycache__*" \
    ! -name "*~" \
    \))
DEPS=(
    "$0"
    .dockerignore
    builder-base.Dockerfile
    builder-requirements.txt
    docker-build-codex-builder-base.sh
    "${PYTHON_CACHER_DEPS[@]}"
    "${SHELLCHECK_DEPS[@]}"
)
DEPS_MD5S=$(md5sum "${DEPS[@]}")
md5sum "${DEPS[@]}"
VERSION=$(echo -e "$CODEX_BASE_VERSION  codex-base-version\n$DEPS_MD5S" |
    LC_ALL=C sort |
    md5sum |
    awk '{print $1}')
if [[ ${CIRCLECI:-} ]]; then
    ARCH=$(uname -m)
    VERSION="${VERSION}-$ARCH"
fi
echo "$VERSION"
