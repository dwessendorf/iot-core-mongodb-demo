#!/bin/bash
# Script to check the changes that will be deployed.

echo "#### --> Checking the changes that will be deployed (cdk diff)..."
cdk diff --all

if [ $? -eq 0 ]
then
    echo "#### --> Diff created successfully. Make sure you have checked the diff and be aware of any costs that might apply due to the AWS services deployed."
    echo "#### --> TIPP: If you see a message regarding CheckBootStrapVersion, this can be ignored, it's OK ;-)"
else
    echo "#### --> Seems the diff got errors. Check the error messages above and consult the aws documentation for more details."
fi

