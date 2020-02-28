#!/bin/bash

# This check is designed to fail fast, starting by failing if the system doesn't support systemd. From that point, we should order
#   the checks to be as high level to low level as possible, ensuring that obvious failures are picked up first and exit quickly.

OK=0
NOTOK=1
UNKNOWN=2

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

# Dumb check to ensure that the kubelet service is running
systemctl status kubelet.service | grep 'Active:' | grep -q running
if [ $? -ne 0 ]; then
    echo "Kubelet service is not running"
    exit $NOTOK
fi

# The following checks are duplicants of the kubelet-monitor checks found here: 
#   https://dev.azure.com/msazure/CloudNativeCompute/_git/ansible?path=%2Fplaybooks%2Fv1%2Froles%2Fhealth-monitor%2Ffiles%2Fkubelet-monitor.sh
#
# ensure-kubelet-alive
if ! output=$(curl -m "${COMMAND_TIMEOUT_SECONDS}" -f -s -S http://127.0.0.1:10255/healthz 2>&1); then
    echo "kubelet healthcheck failed with:"
    echo $output
    exit $NOTOK
fi

# ensure-no-container-name-conflicts
if journalctl -u kubelet --since "1 min ago" | grep -q "Error response from daemon: Conflict. The container name"; then
echo "Container conflicts detected."
exit $NOTOK
fi

# ensure-no-docker-image-inspect-failures
echo "Checking for ${CONTAINER_RUNTIME_NAME} image inspect failures..."
if journalctl -u kubelet --since "1 min ago" | grep -q 'unable to inspect docker image'; then
    echo "${CONTAINER_RUNTIME_NAME} lost images. Removing failed containers."
    exit $NOTOK
fi

# ensure-no-image-inspect-failures
echo "Checking for ${CONTAINER_RUNTIME_NAME} image inspect failures (type 2)..."
if journalctl -u kubelet --since "1 min ago" | grep -qi 'failed to inspect image'; then
    echo "${CONTAINER_RUNTIME_NAME} lost images. Removing failed containers."
    exit $NOTOK
fi

echo "Kubelet service passed all checks and is running"
exit $OK
