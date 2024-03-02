---
title: "Google - GenAI Product Catalog"
---

# GenAI for Product Catalog Enrichment

This repository showcases the application of Google Cloud's Generative AI for product cataloging. The solution will:

- Suggest product category given a sparse description and (optionally) a product image
- Generate product attributes
- Generate detailed marketing copy for these products

These results are grounded using a customer provided product catalog, enabling more specific and relevant results than a purely generative approach would provide.

## Data Scientist / Developer Setup

Download and install the following utilities to make the most of this project.

### Prerequisits

* Google Cloud CLI
  * [Download](https://cloud.google.com/sdk/docs/install)
  > It's recommended that you download and run the install script from your $HOME/bin directory.
* Python 3.11+
  * [Downloads](https://www.python.org/downloads/)

## Setup

### Setup a Virtual Environment

This example uses `pip` as it's installed with Python3
```shell
# Create a development environment in the directory
python3 -m venv venv
# Activate the virtual environment
source ./venv/bin/activate
# Update PIP
pip install --upgrade pip
# Install dependencies
pip install -r conf/requirements.txt
```

### Setup Google Cloud Development Tools

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

## Contributors

### Installing Java

Install Java JDK 17 and ensure it's on your path.

### Installing NodeJS

Install the latest Node JS and make sure it's on your path; this is used to manage the build environment.

### Installing Bazel

Once Java and Node JS are installed, run the following commands from the terminal.

```shell

# May require sudo
npm install -g @bazel/bazelisk

npm install -g @bazel/ibazel

```

Now you can use the the bazel build utility to run, test, and add confidently to the repository.
Please see the [development tool chain](https://googlecloudplatform.github.io/genai-product-catalog/toolchain/) for more information.

