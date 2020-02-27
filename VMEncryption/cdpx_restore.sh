#!/bin/bash

apt-get clean -y
apt-get update -y
apt-get install -y dos2unix
python2 -m pip install --user virtualenv