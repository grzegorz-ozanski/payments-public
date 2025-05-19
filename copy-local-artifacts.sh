#!/usr/bin/env bash

ARTIFACTS_HOST_NAME=blackview.perch-antares.ts.net
ARTIFACTS_HOST_USER=grzegorz
WORKFLOW_NAME=run_payments
ARTIFACTS_HOST_ROOT=/home/${ARTIFACTS_HOST_USER}/vmshared/github-runner/artifacts/${WORKFLOW_NAME}
DEFAULT_JOB="run-windows"
TARGET_ROOT="run"
read -r -p "Job name: [${DEFAULT_JOB}]: " JOB_NAME
RUN_NUMBER=$1
if [ -z "${RUN_NUMBER}" ]; then
    read -r -p "Run number: " RUN_NUMBER
fi
JOB_NAME=${JOB_NAME:-${DEFAULT_JOB}}
SRC="${ARTIFACTS_HOST_USER}@${ARTIFACTS_HOST_NAME}:${ARTIFACTS_HOST_ROOT}/${JOB_NAME}/${RUN_NUMBER}"
DST="${TARGET_ROOT}/${JOB_NAME}"
mkdir -p "${DST}"
DST="${TARGET_ROOT}/${JOB_NAME}/${RUN_NUMBER}"
echo "Copyinng ${JOB_NAME} run #${RUN_NUMBER} artifacts from ${SRC} to ${DST}"
scp -r "${SRC}" "${DST}"
