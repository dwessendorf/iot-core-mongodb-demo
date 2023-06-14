#!/bin/bash
# Script to destroy all resources of this stack in AWS account

echo "#### --> Preparing the deletion of the stack... Relax you will be asked to confirm... ;-)"
cdk destroy --all
