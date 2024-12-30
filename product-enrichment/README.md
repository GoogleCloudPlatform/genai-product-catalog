# Generative AI Product Catalog Enrichment

## Introduction

This project introduces an intermediary to be executed prior to
search indexing. The following ideas and code are intended for customer use
and licensed according to open source licensing terms.

## Documents

[More information here](docs/index.md)

### Environment Setup

See full documents for setting up your [developer workstation](docs/developer-setup.md).

```shell
poetry install
poetry shell
```

### Running test cases

```shell
poetry run pytest tests/
```

### View Document Site

```shell
# Start your poetry shell if not already started
poetry install
poetry shell
# Start the document site
poetry run mkdocs serve
# MacOS or Modern Ubuntu Based Linux
open http://localhost:8000
```

### Running the examples

```shell

### Encrypt local password, this will prompt you to input the password
gRetail encrypt-password

### Generate a new 64 byte random salt. Note, this does not change your password, or yaml files.
gRetail generate-salt

### Generate the database tables. This assumes you have configured your 'env.local.yaml' file.
gRetail database -i

### Start the API Server
gRetail api-server

### Customize the API server to listen on all hosts with a new port and disable reload
gRetail api-server -i 0.0.0.0 -p 8080 -r False
```




