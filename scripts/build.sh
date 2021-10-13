#!/bin/bash

# Exit on first failure
set -e

# Find relevant directories

HERE=$(dirname "$(readlink --canonicalize "$BASH_SOURCE")")
TOP_DIR=$(readlink --canonicalize "$HERE/..")
WHEELS_DIR="${TOP_DIR}"/wheels

# Build
pip wheel ${TOP_DIR} --wheel-dir ${WHEELS_DIR}



						      
