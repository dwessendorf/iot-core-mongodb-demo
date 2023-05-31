python3 -m venv .venv

OS="`uname`"
case $OS in
  'Linux')
    source .venv/bin/activate
    ;;
  'FreeBSD')
    source .venv/bin/activate
    ;;
  'WindowsNT')
    .venv/bin/activate.bat
    ;;
  'Darwin') 
    source .venv/bin/activate
    ;;
  *) ;;
esac

pip3 install -r requirements.txt

export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
export CDK_DEFAULT_REGION=$(aws configure get region)


