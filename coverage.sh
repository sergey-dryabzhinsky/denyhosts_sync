#!/bin/sh
python-coverage run /usr/bin/trial tests/test_get_new_hosts.py tests/test_models.py tests/test_purge_methods.py
python-coverage html
