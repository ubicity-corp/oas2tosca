#!/bin/bash

# Exit on first error
set -e

# Find directories
PROFILE_DIR=~/Temp/
HERE=$(dirname "$(readlink --canonicalize "$BASH_SOURCE")")
WORKSPACE=$(readlink --canonicalize "$HERE/..")
CSAR_DIR="${HERE}"/csars
UBICITY_DIR="${WORKSPACE}"/ubicity

# Make sure CSAR directory exists
mkdir -p ${CSAR_DIR}

# Create CSARs for all profiles
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/runtime
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.runtime.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/apis/meta
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.apis.meta.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/api/resource
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.api.resource.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/util/intstr
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.util.intstr.csar .
cd ${PROFILE_DIR}/io/k8s/api/core
zip -r ${CSAR_DIR}/io.k8s.api.core.csar .

# Go into Ubicity repository 
cd "${UBICITY_DIR}"
. env/bin/activate

# Add profiles
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.runtime.csar 
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.apis.meta.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.api.resource.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.util.intstr.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.core.csar 


