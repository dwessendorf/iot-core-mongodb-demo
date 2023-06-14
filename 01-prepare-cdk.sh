#!/bin/bash
# This script will prepare the cdk environment for deployment.
# It will create a virtual environment, activate it and install all dependencies.
# It will get the AWS Account and Region.
# It will bootstrap the cdk environment. (see https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html)
# Please ensure following environment variables are set before deploying the application: MONGODB_HOST, MONGODB_USER, MONGODB_PW

# Create a virtual environment
python3 -m venv .venv

if [ $? -eq 0 ]
then
    echo "#### --> Virtual environment successfully created"
else
    echo "#### --> Creation of virtual environment failed. Do you have a supported version of python 3 installed? Please check the error message."
fi   

# Activate virtual environment
source .venv/bin/activate
    
if [ $? -eq 0 ]
then
    echo "#### --> Activated virtual environment!"
else
    echo "#### --> Activation of virtual environment failed. Please check the error message. If you are running Windows run the following command: .venv/Scripts/activate.bat"
fi   

# Install dependencies
pip3 install -r requirements.txt

if [ $? -eq 0 ]
then
    echo "#### --> Installed all dependencies"
else
    echo "#### --> Installation of dependencies failed. Please check the error message. If you are running Windows run the following command: pip install -r requirements.txt"
fi    

# Get AWS Account
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)

if [ $? -eq 0 ]
then
    echo "#### --> Deploying to AWS Account $CDK_DEFAULT_ACCOUNT"
else
    echo "#### --> Getting AWS Account failed. Do you have a supported version of aws installed? Please check the error message. Consider running aws configure."
fi

# Get AWS Region
export CDK_DEFAULT_REGION=$(aws configure get region)

if [ $? -eq 0 ]
then
    echo "#### --> Deploying to AWS Region $CDK_DEFAULT_REGION"
else
    echo "#### --> Getting AWS Region failed. Do you have a supported version of aws installed? Have you seleceted a default region? Please check the error message. Consider running aws configure."
fi

# Bootstrap CDK
cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/$CDK_DEFAULT_REGION 

if [ $? -eq 0 ]
then
    echo "#### --> CDK bootstrapped! Please ensure following environment variables are set before deploying the application: MONGODB_HOST, MONGODB_USER, MONGODB_PW"
else
    echo "#### --> Bootstrapping cdk failed. Please check the error message and consult the aws documentation fro help."
fi


