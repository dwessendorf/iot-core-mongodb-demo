#!/bin/bash
# This script creates a private key and a certificate signing request.
# The private key is stored in a file named private_key.key.
# The certificate signing request is stored in a file named signing_request.csr.
# Both files are stored in the directory certificates.
# The certificates are needed for MQTT connection to IOT Core.
# It is recommended to use a self-signed certificate.
# Be aware that the private key is stored in plain text and will be uploaded to AWS Secrets Manager also in plain text.
# Everybody who has access to the AWS Secrets Manager or AWS CloudFormation in your account can read the private key.

# create a directory for certificates
mkdir -p certificates 
# define Certificate Signing Request attributes
CN="www.example.com" # change to your domain name
OU="Your Unit" # change to your organizational unit
O="Your Company" # change to your company
L="Mountain View" # change to your city
ST="California" # change to your state. Find state code at https://en.wikipedia.org/wiki/ISO_3166-2:US
C="US" # change to your country. Find country code at https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2

if [ -f "certificates/private_key.key" ] && [ -f "certificates/signing_request.csr" ]
then
    echo "#### --> Certificates already exist. Skipping creation."
else
    # create a 2048bit pem key and a x.509 certificate signing request
    openssl req -new -newkey rsa:2048 -nodes -keyout "certificates/private_key.key" -out "certificates/signing_request.csr" -subj "/C=$C/ST=$ST/L=$L/O=$O/OU=$OU/CN=$CN"

    if [ $? -eq 0 ]
    then
        echo "#### --> Created certificates/private_key.key and certificates/signing_request.csr"
    else
        echo "#### --> Certificate creation failed. Please make sure you have the openssl commandline tool installed or check the error and the openssl documentation."
    fi
fi
