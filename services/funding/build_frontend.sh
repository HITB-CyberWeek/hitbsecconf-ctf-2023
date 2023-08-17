#!/bin/bash

set -ex

cd "$(dirname "$0")"

docker build -t funding-frontend-builder -f frontend.build.Dockerfile .
docker run --rm -v "$PWD/frontend.build":/app/frontend/out funding-frontend-builder

echo Successfully built frontend:
ls -la frontend.build
