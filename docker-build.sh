#!/bin/sh
docker buildx build -f compose/production/django/Dockerfile -t ghcr.io/whoigit/appdev-analytics-dataserver:stable --platform linux/amd64 --push .
