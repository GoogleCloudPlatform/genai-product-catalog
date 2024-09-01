---
title: "Contributing"
weight: 1
icon: "pen-solid"
---

## Prerequisites

Prior to contributing to a Google Open Source repository, Google, LLC requires non-Google contributors to sign and file a [Contributor License Agreement](https://cla.developers.google.com/clas). If you DO NOT have a CLA on file your code WILL NOT be merged into this repository.

### Why do we have a CLA?

Our CLA allows open source projects adminstered by Google to safely accept code and documentation from external contributors.

For additional information, please visit our [Alphabet CLA Policy and Rationale](https://opensource.google/documentation/reference/cla/policy) page.

## Introduction

{{< mermaid class="text-center">}}
flowchart LR

A(Create GitHub Account) -->|Request access| B(Fork Repository)
B -->|Open Clone| C(Checkout Source Code)
C --> D(Make Changes)
D --> E(Write Tests)
E --> F(Test)
F --> G(Verify)
G --> H(Commit)
H --> I(Create PR)
I --> J[Collaborate]
J --> K{Pass}
K --> L[Merge]
K -->|Fix Suggestions| C
L --> C
{{< /mermaid >}}

### Steps

1. Ensure you have a [GitHub](https://www.github.com) account.
2. Request access if the repository is private.
3. Fork the repository. This makes a copy to your local GitHub account.
4. Clone the newly created fork to your developer machine.
   - `git clone <repository name>`
5. Make any changes or additions to the code.
6. Write automated test cases.
7. Verify all tests are passing and all code is commented and meets the style
   guide requirements.
   _ `bazel test //...` runs all tests
   _ `bazel coverage //java/...` runs test coverage on a specific target.
8. Commit your code, and push back to your fork.
   - `git commit add .`
   - `git commit -a`
   - Add comments, if you are referencing a feature or bug, please indicate the number first.
   - `git push`
9. Verify the build runs in GitHub actions on your own branch. This is important, especially if
   you are updating BUILD or WORKSPACE files.
10. From the GitHub interface, create a pull request and ensure you comment the
    reasons and thought processes behind the change or additions. \* [Understanding Pull Requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)
11. Once created, you will collaborate with the maintainers for QA purposes,
    unless they simply accept the changed and merge it.
12. If not, you may be asked to make some changes and create a new PR.

## Project Structure

The Google Retail Cloud project is divided into the following directory structure:

- conf - Configuration files
- docs - The documentation site
- examples - Examples on how to use the python modules
- google - Is the root library for all google libraries
- third-party - Is all third party data and licenses.


## Licensing

This project is licensed under the Apache 2.0 license. Please see the LICENSE file in the root of the project.
