## Prerequisites
* Git
* This project downloaded
* Google Cloud Console Access as a Project Administrator.
* [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed on the Admin’s workstation.

## Demo Components
* App Engine
* APIs & Services
* FireStore
* Google Cloud Storage

Recommended Production Components
* GKE
* Pub/Sub
* APIs & Services
* Google Cloud Storage

### Project Technology Stack

#### Google Cloud

This project uses Google Cloud components for operations and interactions with
the Gemini LLM services and models.

#### NodeJS

This project is written in NodeJS. It represents the lowest bar of complexity in
service integration and a Human In the Loop (HITL) workflow. It's important not
to confuse that with performance or capability. Today's V8 JavaScript engine
is almost on par with GoLang when configured correctly.

## Workstation Setup

The following instructions are for the developer and administration / SRE of the system.

### Terminal

This project uses the Terminal for most setup steps, and will call out the Console
analogs where appropriate. More specifically these instructions are written for 
a Linux prompt system (Apple Mac OS, or *nx) shells. As of this writing, there are
two predominant shells: Bash (Borne Again Shell), ZSH. All of these examples are targeted in ZSH and 
should be applicable in Bash.

All work in the terminal will be done from or within the project directory.
```shell
# replace PROJECT_HOME with the actual path to you project:
# ~/Projects/oss/genai-product-catalog/demos/digital-commerce
cd PROJECT_HOME
````

### Setting Up Node JS

Open your terminal and use the following commands, updates and instructions for other operating systems
can be found [here](https://nodejs.org/en/download/package-manager).

#### Mac OS
```shell
# Download and install nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
# reloads your current shell so nvm and node are on your system path
source ~/.zshrc
# Download and install Node.js:
nvm install 24
# Verify the Node.js version:
node -v # Should print "v24.4.1".
nvm current # Should print "v24.4.1".
# Verify npm version:
npm -v # Should print "11.4.2".
```

### NX (Required NodeJS)

The repository is a Mono Repo using [NX](https://nx.dev/), NX is a build system that allows multiple modules
to exist in a single directory structure.

```shell
# Setup the nx CLI globally
npm install -g nx
```

### Prebuild tasks

Since you downloaded the repository, there are configuration files you'll need to create

```shell
# First, create the dispatch.yaml file, this is the file used by AppEngine as the virtual router.
cp example-dispatch.yaml dispatch.yaml
```

#### API
```shell
# Next, create the application descriptor for the API project, this is required to build the project.
# as the app.yaml file IS a project dependency.
cp apps/api/src/example-app.yaml apps/api/src/app.yaml
```

```shell
# Next update the apps/api/.env file in your favorite editor
vim apps/api/.env
```

> NOTE: you will need to create an apps/api/.env.prod file before deploying

#### Demo
```shell
# Next, create the application descriptor for the Demo project.
cp apps/demo/public/example-app.yaml apps/demo/public/app.yaml
```

### Testing the Tools

In the terminal navigate to the project directory.

```shell
npm install

# Build the API Project
nx build api

# Build the Demo Project
nx build demo
```

## Google Cloud
* In Google Cloud Console (Console)
* Console Search (Search)

### Enable App Engine

Search: "App Engine"
Click the link and follow the setup guide.

### Enable APIs
Search: "APIs & Services"
 type: "APIs & Services" in the search bar and choose the first link.

Enable the following APIs:
Compute Engine API
Gemini for Google Cloud API
Vertex AI API
App Engine







