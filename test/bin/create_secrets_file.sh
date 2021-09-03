#!/bin/bash

cat << EOF > .secrets.toml
[development]
BNB_CLIENT_KEY = "${BNB_CLIENT_KEY}"
BNB_CLIENT_SECRET = "${BNB_CLIENT_SECRET}"
EOF
