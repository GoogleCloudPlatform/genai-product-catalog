# Developer Setup

### Python

1. Install Python 3.12+ on your workstation
2. Install [pipx](https://pipx.pypa.io/stable/installation/)
3. Install [Poetry](https://python-poetry.org/docs/)

### Project
From the terminal
```shell
cd <project-root>
## Tell poetry to use a local path virtual environment
poetry config virtualenvs.path ./venv
## Install all dependencies
poetry install
## Start the poetry shell (venv)
poetry shell
```

### Database
1. Install Postgresql (Locally or a cloud instance)
2. Install pgvector
    1. Local [Instructions](https://github.com/pgvector/pgvector)
    2. Cloud PG Vector is already installed by default
3. Create a user and a database with the following commands:
    1. `CREATE USER gcp-genai-catalog WITH PASSWORD '<password>';`
    2. `CREATE DATABASE gcp-genai-catalog OWNER gcp-genai-catalog;`
    3. `GRANT CONNECT ON gcp-genai-catalog TO gcp-genai-catalog;`
4. Login to the database and enable PGVector
    1. `CREATE EXTENSION IF NOT EXISTS vector;`
5. Encrypt the password you created above for configuration
    1. `cd <project-directory>`
    2. `poetry shell`
    3. `poetry install`
    4. `retail generate-salt` - copy the salt
    5. `retail encrypt-password -p <your password> -s <your salt>`
       6. Create a local configuration file called "env.loca    l.toml" using "env.toml" as a template **This file is ignored by git**.
           1. In the application section:
               1. Add your Google Cloud Project ID `project_id = "<your project id>"`
               2. Add your API key `api_key = "<your api key>"`
           2. In the postgres section
               1. Add the salt `salt = "<your salt>"`
               2. Add the password `password = "<your encrypted password>"`
7. Ensure your Google Cloud CLI is setup
    1. `gcloud config set project <project name>`
    2. `gcloud auth application-default set-quota-project`
    3. `gcloud auth application-default login`

```toml
[application]
project_id="my-really-cool-gcp-project"
api_key="some-really-long-api-key"

[postgres]
salt = "GMtAcYskKjSahsjdCEQmNxe7xJd3Ed3lAa6Povpw4ekwmKWONbf9uvcYdRUpgRIdQ"
password = "0935125421390f782f375204320b5262"
```

> NOTE: You only need to override values, the end configuration is a composite of both files
> with 'local' overriding the values in env.toml

Once the database is set up, you can initialize the database from the project directory.

```shell
cd <project-directory>
# If not active already
poetry shell 
# Ensure the project is installed
poetry install
# Run the DB initialize script
db-init
```

#### Using a managed instance from your developer instance

##### Create your database instance with Terraform

```shell
# Make sure you've setup your GCP CLI

cd <project directory>/support/terraform
terraform init
terraform apply

```

Visit the [Connect using the Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy) page
and download the appropriate command  line tool and make it executable. Binaries for Linux 64, Apple 64 and Apple AARCH 64
are available in the third_party/google folder.

```shell
cd third_party/google
ln -s <arch-file> cloud-sql-proxy
chmod 755 cloud-sql-proxy

# Ensure your account can access the database
gcloud sql instances describe gcp-genai-catalog

# Start the proxy and use your IDE to connect to the instance, and/or update the port in the toml file.
./cloud-sql-proxy --address 127.0.0.1 --port 6543 <project-id>:<region>:gcp-genai-catalog

# Example my-project:us-central1:gcp-genai-catalog
```
