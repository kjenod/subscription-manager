#!/bin/bash

apt-get update
apt-get install -y sudo

sudo -u postgres bash << EOF
createuser $DB_USER
createdb subscriptions
createdb testing
EOF
