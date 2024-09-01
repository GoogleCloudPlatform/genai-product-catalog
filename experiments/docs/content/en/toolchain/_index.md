---
title: 'Development Toolchain'
weight: 5
---



## Data Scientists

We strongly encourage you to follow the examples in the example directory.
Use a standard virtual environment, finding all requirements in the conf/requirements.txt file.

## Contributors

### Tooling

This project uses Bazel to build all modules and manage dependencies. In 
conjunction with the Google Cloud CLI and app development libraries.
Setting up a Bazel build environment is extremely simple, the following steps
will get you up and running.

1. Download and install NPM (Node Package Manager) - NPM is used to manage Bazel through a plugin called Bazelisk. 
2. Once NPM is installed an your system path, open the console of your choice and issue the following command: `npm install -g @bazel/bazelisk`
3. That's it, bazel is ready to be used.

#### Why Bazel with Python?

* Bazel is a hermetic build system, ensuring that when you build your software it WILL NOT be influenced by your local environment.
* Bazel supports many languages, Python is only one of them, and to build everything here, we also use Hugo and may use additional gRPC libraries.
* Bazel can operate along side your normal development tools and NOT impact your work life style.
* Bazel helps automate most developer tasks in a lightweight runtime.
* Bazel is configured using a language called Starlark, and it's a lot like Python which makes it a natural fit.

### Building

Building uses the following files:

* WORKSPACE - Defines the dependencies needed to build our software.
* BUILD.bazel - You'll see these files in various directories, they tell bazel which software to build and test.
* Targets - Targets are defined in BUILD files by name, for example, docs/BUILD.bazel you can see "gen_docs", this target builds the pydocs for the site, while other targets make them available as markdown in the final output directory. Targets can be access via a simple path `//docs:gen_docs` would tell bazel to perform that action.
* Rules - Are used to tell bazel what to do. For example: run, test, ... are types of rules, and every langauge has similar targets.

#### Build Everything

```shell
bazel build //...
```

#### Build Some Things

```shell
# Everything under docs
bazel build //docs/...

# All google libraries
bazel build //google/...

# Only build a single target
# Because there is a rule named 'applied' in this directory, it will run as the default rule
bazel build //google/cloud/ml/applied

# A single named target
bazel build //docs:model 
```

#### Running a target
```shell

# Run the document site locally
bazel run //docs:serve

# Start the service locally
bazel run //examples/service:run
```

#### Testing

```shell
# Run all tests under the google directory
bazel test //google/...
```
