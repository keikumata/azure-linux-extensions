#!/bin/bash

apt-get install -y virtualenv

cd /source/VMEncryption

python -m virtualenv ./env
. env/bin/activate
pip install -r requirements.txt
python -m unittest test.test_check_utils