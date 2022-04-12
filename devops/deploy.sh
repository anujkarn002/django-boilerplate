#!/usr/bin/env bash
ssh -o StrictHostKeyChecking=no root@<IP_ADDRESS> << 'ENDSSH'
 cd /api
 docker login -u $REGISTRY_USER -p $CI_BUILD_TOKEN $CI_REGISTRY
 docker pull registry.gitlab.com/<USERNAME>/<REPOSITORY_NAME>:latest
 docker-compose up -d
ENDSSH