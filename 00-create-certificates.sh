#!/bin/bash
mkdir certificates
# define CN
CN="www.example.com"

# identify OS
OS="`uname`"
case $OS in
  'Linux')
    OS='Linux'
    ;;
  'FreeBSD')
    OS='FreeBSD'
    ;;
  'WindowsNT')
    OS='Windows'
    ;;
  'Darwin') 
    OS='Mac'
    ;;
  'SunOS')
    OS='Solaris'
    ;;
  'AIX') ;;
  *) ;;
esac

echo "You are running $OS."

# create a 2048bit pem key and a x.509 certificate signing request
openssl req -new -newkey rsa:2048 -nodes -keyout "certificates/private_key.key" -out "certificates/signing_request.csr" -subj "/C=US/ST=California/L=Mountain View/O=Your Company/OU=Your Unit/CN=$CN"

echo "Created certificates/private_key.key and certificates/signing_request.csr"
