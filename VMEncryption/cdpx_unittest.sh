#!/bin/bash
cd /source/VMEncryption

python2 -m virtualenv ./env
. env/bin/activate
pip install -r requirements.txt
python2 -m unittest test.test_check_utils