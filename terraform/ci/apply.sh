#!/bin/bash

set -e

# Get the path from whe
starting_path=$(pwd)

# Cd target dir
cd "$(dirname "$BASH_SOURCE")"

# Terraform infrastructure
# Terraform Format
terraform fmt -check
# Terraform init
terraform init
# Terraform validate
terraform validate -no-color
# Terraform plan
terraform plan -no-color
# Terraform apply
terraform apply

# Back to initial path
cd "$starting_path"