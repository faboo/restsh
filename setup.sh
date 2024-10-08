#!/bin/bash

set -e
set -o pipefail

virtualenv -p python3 -q .venv

source .venv/bin/activate

for requirements in requirements/*
do
	pip3 install --no-user -q -r $requirements
done

