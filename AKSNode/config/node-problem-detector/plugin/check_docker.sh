#!/bin/bash

# This check is designed to fail fast, starting by failing if the system doesn't support systemd. From that point, we should order
#   the checks to be as high level to low level as possible, ensuring that obvious failures are picked up first and exit quickly.

OK=0
NOTOK=1
UNKNOWN=2

HEALTHCHECK_COMMAND="${HEALTHCHECK_COMMAND:-docker ps}"
HEALTHCHECK_COMMAND_TIMEOUT="${HEALTHCHECK_COMMAND_TIMEOUT:-60}"

which systemctl >/dev/null
if [ $? -ne 0 ]; then
    echo "Systemd is not supported"
    exit $UNKNOWN
fi

if which docker &> /dev/null; then
  CONTAINER_RUNTIME_NAME="docker"
else
  CONTAINER_RUNTIME_NAME="containerd"
fi

# Dumb check to ensure that a container runtime service is running
systemctl status ${CONTAINER_RUNTIME_NAME}.service | grep 'Active:' | grep -q running
if [ $? -ne 0 ]; then
    echo "${CONTAINER_RUNTIME_NAME} service is not running"
    exit $NOTOK
fi

# The following checks are duplicants of the docker-monitor checks found here: 
#   https://dev.azure.com/msazure/CloudNativeCompute/_git/ansible?path=%2Fplaybooks%2Fv1%2Froles%2Fhealth-monitor%2Ffiles%2Fdocker-monitor.sh
#
# ensure-container-runtime-alive
echo "Checking container runtime health with \"${HEALTHCHECK_COMMAND}\""
if ! timeout ${HEALTHCHECK_COMMAND_TIMEOUT} ${HEALTHCHECK_COMMAND} > /dev/null; then
    echo "${HEALTHCHECK_COMMAND} failed!"
    exit $NOTOK
fi

echo "${CONTAINER_RUNTIME_NAME} service passed all checks and is running"
exit $OK
