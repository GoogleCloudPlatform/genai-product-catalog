# GenAI for Product Catalog Enrichment

This repository showcases the application of Google Cloud's Generative AI for product cataloging. The solution will:

- Suggest product category given a sparse description and (optionally) a product image
- Generate product attributes
- Generate detailed marketing copy for these products

These results are grounded using a customer provided product catalog, enabling more specific and relevant results than a purely generative approach would provide.

## Data Scientist / Developer Setup

Download and install the following utilities to make the most of this project.


* Google Cloud CLI
  * [Download](https://cloud.google.com/sdk/docs/install)
  > It's recommended that you download and run the install script from your $HOME/bin directory.
* Python 3.11+
  * [Downloads](https://www.python.org/downloads/)

## Setup your Terminal Environment

Add and ensure the following lines exist in your $HOME/.zshrc or $HOME/.bashrc
respective to your terminal preferences.

```shell
# Sets the default Python SDK for Google Cloud
export CLOUDSDK_PYTHON=.venv

# These lines SHOULD HAVE been added by the Google Cloud CLI Setup:
# The next line updates PATH for the Google Cloud SDK.
if [ -f '$HOME/bin/google-cloud-sdk/path.zsh.inc' ]; then . '$HOME/bin/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '$HOME/bin/google-cloud-sdk/completion.zsh.inc' ]; then . '$HOME/bin/google-cloud-sdk/completion.zsh.inc'; fi

# Adds utilities to path:
export PATH=$PATH:$JAVA_HOME/bin:$HOME/bin
```

## Setup your virtual environment

This example uses `pip` as it's installed with Python3
```shell
# Create a development environment in the directory
python3 -m venv venv
# Activate the virtual environment
source ./venv/bin/activate
# Update PIP
pip install --upgrade pip
# Install dependencies
pip install -r build/requirements.txt
```

## Tooling Installation

### Installing Java

### Installing NodeJS

### Installing Bazel




