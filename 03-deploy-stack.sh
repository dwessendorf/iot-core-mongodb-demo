#!/bin/bash
# Script to deploy the CDK stack
# This script assumes that both python virtual environment and CDK app are already created. Run 01-prepare-cdk.sh and 02-check-changes.sh before running this script.

echo "#### --> Starting deployment..."
cdk deploy --all

if [ $? -eq 0 ]
then
    echo "#### --> Seems that deployment was successful. Please be aware of any costs that might apply due to the AWS services deployed."
    echo "#### --> Tipp: If you want to deploy without giving confirmations run: cdk deploy --all --require-approval=never"
else
    echo "#### --> Seems the deployment got errors. Check the error messages above and consult the aws documentation for more details."
fi