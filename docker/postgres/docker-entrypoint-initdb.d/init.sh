#!/bin/bash

apt-get update
apt-get install -y sudo

sudo -u postgres bash << EOF
createuser $DB_USER
createdb subscriptions
createdb testing
insert into users(username, password, created_at, active, is_admin) values('admin', 'pbkdf2:sha256:150000$ljwbHben$e86cd91626df47864120f4d9220b27dab4de7883d646a9e26dc89e0eb71be4cd', CURRENT_TIMESTAMP, 't', 't');
EOF
