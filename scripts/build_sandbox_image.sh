#!/usr/bin/env bash
# Build the data-analysis sandbox image (numpy/scipy/pandas/scikit-learn/cryptography).
# Owner-operated: it's a large, slow build (downloads the scientific wheels once). After it,
# point the sandbox at it in config/local.toml:  [sandbox] image = "mind-palace-sandbox:latest"
#
#   ./scripts/build_sandbox_image.sh
#
# Needs the podman machine running (`podman machine start`). The resulting image holds the wheels
# baked in, so sandboxed code uses them with NO network at run time (the container stays
# --network=none, --read-only, non-root — core/sandbox/policy.py).
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${1:-mind-palace-sandbox:latest}"
echo "building $TAG from ops/sandbox/Containerfile (this pulls the scientific stack — slow once)…"
podman build -t "$TAG" -f ops/sandbox/Containerfile ops/sandbox
echo
echo "built $TAG. Enable it for this machine in config/local.toml:"
echo "    [sandbox]"
echo "    image = \"$TAG\""
echo "Verify:  podman run --rm -i --network=none $TAG python3 - <<<'import numpy,pandas,sklearn; print(\"libs ok\")'"
