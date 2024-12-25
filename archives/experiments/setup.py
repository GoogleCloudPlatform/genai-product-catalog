# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os
import re

import setuptools  # type: ignore

package_root = os.path.abspath(os.path.dirname(__file__))
name = "google-cloud-ml-applied"

description = "Google Cloud ML Applied Client Library"

version = None

with open(os.path.join(package_root, "google/cloud/ml/applied/gapic_version.py")) as fp:
    version_candidates = re.findall(r"(?<=\")\d+.\d+.\d+(?=\")", fp.read())
    assert len(version_candidates) == 1
    version = version_candidates[0]

if version[0] == "0":
    release_status = "Development Status :: 4 - Beta"
else:
    release_status = "Development Status :: 5 - Production/Stable"


readme_filename = os.path.join(package_root, "README.rst")
with io.open(readme_filename, encoding="utf-8") as readme_file:
    readme = readme_file.read()

url = "https://github.com/"

packages = [
    package
    for package in setuptools.find_namespace_packages()
    if package.startswith("google")
]

dependencies = [
    "requests>=2.31.0",
    "scipy>=1.11.4",
    "numpy>=1.26.3",
    "mediapipe>==0.10.9",
    "pandas>=2.1.4",
    "en_core_web_sm@https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.4.0/en_core_web_sm-3.4.0-py3-none-any.whl"
    "spacy>=3.4.4",
    "spacy-cleaner>=3.1.0",
    "json-pickle>=3.0.2",
    "google-api-python-client>=2.113.0",
    "google-cloud-aiplatform>=1.39.0",
    "google-cloud-storage>=2.14.0",
    "google-cloud-bigquery>=3.15.0",
    "gcloud>=0.18.3",
    "grpclib==0.4.7",
    "grpcio==1.60.0",
    "fastapi>=0.108.0",
    "uvicorn>=0.25.0",
]

setuptools.setup(
    name=name,
    version=version,
    description=description,
    long_description=readme,
    author="Google LLC",
    author_email="googleapis-packages@google.com",
    license="Apache 2.0",
    url=url,
    classifiers=[
        release_status,
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Internet",
    ],
    platforms="Posix; MacOS X; Windows",
    packages=packages,
    python_requires=">=3.7",
    install_requires=dependencies,
    include_package_data=True,
    zip_safe=False,
)
