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
cd ${PROFILE_DIR}/io/k8s/kube-aggregator/pkg/apis/apiregistration
zip -r ${CSAR_DIR}/io.k8s.kube-aggregator.pkg.apis.apiregistration.csar .
cd ${PROFILE_DIR}/io/k8s/apiextensions-apiserver/pkg/apis/apiextensions
zip -r ${CSAR_DIR}/io.k8s.apiextensions-apiserver.pkg.apis.apiextensions.csar .
cd ${PROFILE_DIR}/io/k8s/api/events
zip -r ${CSAR_DIR}/io.k8s.api.events.csar .
cd ${PROFILE_DIR}/io/k8s/api/networking
zip -r ${CSAR_DIR}/io.k8s.api.networking.csar .
cd ${PROFILE_DIR}/io/k8s/api/authentication
zip -r ${CSAR_DIR}/io.k8s.api.authentication.csar .
cd ${PROFILE_DIR}/io/k8s/api/scheduling
zip -r ${CSAR_DIR}/io.k8s.api.scheduling.csar .
cd ${PROFILE_DIR}/io/k8s/api/coordination
zip -r ${CSAR_DIR}/io.k8s.api.coordination.csar .
cd ${PROFILE_DIR}/io/k8s/api/storage
zip -r ${CSAR_DIR}/io.k8s.api.storage.csar .
cd ${PROFILE_DIR}/io/k8s/api/node
zip -r ${CSAR_DIR}/io.k8s.api.node.csar .
cd ${PROFILE_DIR}/io/k8s/api/apps
zip -r ${CSAR_DIR}/io.k8s.api.apps.csar .
cd ${PROFILE_DIR}/io/k8s/api/rbac
zip -r ${CSAR_DIR}/io.k8s.api.rbac.csar .
cd ${PROFILE_DIR}/io/k8s/api/core
zip -r ${CSAR_DIR}/io.k8s.api.core.csar .
cd ${PROFILE_DIR}/io/k8s/api/batch
zip -r ${CSAR_DIR}/io.k8s.api.batch.csar .
cd ${PROFILE_DIR}/io/k8s/api/policy
zip -r ${CSAR_DIR}/io.k8s.api.policy.csar .
cd ${PROFILE_DIR}/io/k8s/api/discovery
zip -r ${CSAR_DIR}/io.k8s.api.discovery.csar .
cd ${PROFILE_DIR}/io/k8s/api/autoscaling
zip -r ${CSAR_DIR}/io.k8s.api.autoscaling.csar .
cd ${PROFILE_DIR}/io/k8s/api/authorization
zip -r ${CSAR_DIR}/io.k8s.api.authorization.csar .
cd ${PROFILE_DIR}/io/k8s/api/admissionregistration
zip -r ${CSAR_DIR}/io.k8s.api.admissionregistration.csar .
cd ${PROFILE_DIR}/io/k8s/api/certificates
zip -r ${CSAR_DIR}/io.k8s.api.certificates.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/version
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.version.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/util/intstr
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.util.intstr.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/runtime
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.runtime.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/apis/meta
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.apis.meta.csar .
cd ${PROFILE_DIR}/io/k8s/apimachinery/pkg/api/resource
zip -r ${CSAR_DIR}/io.k8s.apimachinery.pkg.api.resource.csar .

# Go into Ubicity repository 
cd "${UBICITY_DIR}"
. env/bin/activate

# Add profiles
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.version.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.util.intstr.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.runtime.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.apis.meta.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.apimachinery.pkg.api.resource.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.kube-aggregator.pkg.apis.apiregistration.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.apiextensions-apiserver.pkg.apis.apiextensions.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.core.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.events.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.networking.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.authentication.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.scheduling.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.coordination.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.storage.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.node.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.apps.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.rbac.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.batch.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.policy.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.discovery.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.autoscaling.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.authorization.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.admissionregistration.csar
./ubicity profile add ${CSAR_DIR}/io.k8s.api.certificates.csar
