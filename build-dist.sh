#!/bin/bash
# Buld script for producing a codex python package
set -euxo pipefail
cd "$(dirname "$(readlink "$0")")"

echo "*** build frontend ***"
rm -rf "codex/static_build"
cd frontend
npm run build

echo "*** collect static resources into static root ***"
cd ..
./collectstatic.sh

echo "*** build and package application ***"
# XXX poetry auto-excludes anything in gitignore. Dirty hack around that.
# BSD sed behaves differently
if [ "$(uname)" = "Darwin" ]; then
    sedi=('/usr/bin/sed' '-i' '')
else
    sedi=('sed' '-i')
fi

"${sedi[@]}" "s/.*static_root.*//" .gitignore
poetry build
git checkout .gitignore # XXX so i can run this locally
