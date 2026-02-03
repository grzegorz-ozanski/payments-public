#!/usr/bin/env bash

ARTIFACTS_HOST_NAME=blackview.perch-antares.ts.net
ARTIFACTS_HOST_USER=grzegorz
LAST_WORKSPACE_ROOT=/tmp
LAST_WORKSPACE=last_workspace
TARGET_ROOT="run"
SSH_HOST=${ARTIFACTS_HOST_USER}@${ARTIFACTS_HOST_NAME}
SRC="${LAST_WORKSPACE_ROOT}/${LAST_WORKSPACE}"
DST="${TARGET_ROOT}/${LAST_WORKSPACE}"
PACKER="zstd -T0 --no-progress -o"
ARCHIVE_NAME="${LAST_WORKSPACE}.tar.zst"
RUNNER_NAME=github-runner
RUNNER_ROOT=/tmp/actions-runner/jobs/

echo "Copyinng ${JOB_NAME} last run artifacts from ${SRC} to ${DST}"
ssh -t "${SSH_HOST}" "
    rm -rf ${SRC} && 
    docker cp ${RUNNER_NAME}:${RUNNER_ROOT}/${LAST_WORKSPACE} ${LAST_WORKSPACE_ROOT} && 
    cd ${LAST_WORKSPACE_ROOT} && 
    rm -f ${ARCHIVE_NAME} && 
    tar -c ${LAST_WORKSPACE} | pv -s \$(du -sb ${LAST_WORKSPACE} | awk '{print \$1}') | ${PACKER} ${ARCHIVE_NAME}
"
mkdir -p "${TARGET_ROOT}"
rm -rf "${TARGET_ROOT:?}/${LAST_WORKSPACE}"
scp -r "${SSH_HOST}:${LAST_WORKSPACE_ROOT}/${ARCHIVE_NAME}" "${TARGET_ROOT}/${ARCHIVE_NAME}"
bash -c "cd ${TARGET_ROOT} && tar -xf ${ARCHIVE_NAME} && rm -f ${ARCHIVE_NAME}"
