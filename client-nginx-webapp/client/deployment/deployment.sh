#!/bin/bash
set -e
set -x
set -o pipefail

# $source_root should be set in the wrapper SS script.
source_location=${source_root}/client/app

_cloud_service=`ss-get cloudservice`
riemann_host=`ss-get orchestrator-${_cloud_service}:hostname`
riemann_port=5555

webapp_ip=`ss-get nginx.1:hostname`

deploy_httpclient() {
    yum install -y python-pip python-devel gcc zeromq-devel
    pip install --upgrade pip
    pip install pyzmq
    pip install locustio
}

run_httpclient() {
    curl -sSf -o ~/locust-tasks.py $source_location/locust-tasks.py
    locust --host=http://$webapp_ip -f ~/locust-tasks.py WebsiteUser &
}

deploy_and_run_riemann_client() {
    pip install --upgrade six
    pip install riemann-client

    curl -sSf -o ~/locust-riemann-sender.py $source_location/locust-riemann-sender.py

    # Orchestrator ready synchronization flag!
    ss-display "Waiting for Riemann to be ready."
    ss-get --timeout 600 orchestrator-${_cloud_service}:url.service

    chmod +x ~/locust-riemann-sender.py
    ~/locust-riemann-sender.py $riemann_host:$riemann_port &
}

deploy_httpclient
run_httpclient
deploy_and_run_riemann_client

hostname=`ss-get hostname`
url="http://${hostname}:8089"
ss-set url.service $url
ss-display "Load generator: $url"
