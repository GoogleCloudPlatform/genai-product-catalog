# Digital Commerce

This demo project illustrates using multiple facets the Google Cloud ecosystem
while keeping a small application footprint to show developer and enthusiasts
how to use Gemini in a retail setting.

## Tooling and Setup

This project uses Node JS and is built using a Monorepo with NX. In
addition, it requires a Google Storage Bucket and a access to Firebase.

### Tooling Roles

* Google Cloud Storage - Is used as a temporary swap for media files (sound and video).
* Firebase - Is used to record changed to settings and simply track who the demo is being showed to.
* Google APIs - Vertex API and Google Voice API
* Node JS - Is used to build and run the components of the demo.
    * API - Is the REST API and the Websocket Server used for managing Gemini and Google API requests.
    * Demo - Is a React application for interacting with the API and Socket Server.
    * Model - Is a set of shared definitions used by the API and the Demo project.

### Setting up a Google Cloud Project

* Create a new project
* Enable App Engine for the project
* Enable Google Cloud Storage
    * Create a storage bucket: 'retail-storage-\<project-name>'
    * Add the App Engine service account to the Google Cloud Storage Bucket
* Enable the Vertex AI API
* It's highly recommend using organization level access controls e.g. identity aware proxy aka IAP. 
https://cloud.google.com/security/products/iap?hl=en

### Configuration Changes

In the apps/api directory update the app.yaml file and the .env file to your Google Bucket Name.

The app engine service account MUST have read/write access to the bucket.


### Setup

Once you download this repository, open a shell of your choice
and follow these steps

```shell

# If you don't have NodeJS on your system currently:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# If you're using bash
source ~/.bashrc 

# If your're using zsh
source ~/.zshrc

# Install Node to your local user account
nvm install 22

# Test node:
node -v # should print `v22.5.x`

# Next, add NX to your global node settings
npm add --global nx@latest

# Once complete, change to your project download directory
cd ~/PROJECT_DIRECTORY

# Run the standard install:
npm install

# Build the various components:
nx build api
nx build demo 

# If you'd like to see the project relationships:
nx graph

# To run the demo locally
nx run api:serve 

# In another terminal
nx run demo:serve

# Click the link to open the demo in your browser
```