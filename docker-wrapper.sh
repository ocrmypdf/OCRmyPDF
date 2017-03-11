#!/bin/bash

. /appenv/bin/activate
cd /home/docker
exec ocrmypdf "$@"