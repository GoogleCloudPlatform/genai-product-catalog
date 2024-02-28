# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

load("@build_stack_rules_hugo//hugo:rules.bzl", "hugo_serve", "hugo_site", "hugo_theme")
load("//conf:copy_file_groups.bzl", "copy_file_groups")
load("@rules_python//python:defs.bzl", "py_binary")
load("@python_deps//:requirements.bzl", "requirement")
load("@bazel_skylib//rules:run_binary.bzl", "run_binary")
load("//docs:docs.bzl", "doc_gen")

hugo_theme(
    name = "hugo_theme_geekdoc",
    srcs = [
        "@theme_geekdoc//:files",
    ],
    theme_name = "hugo-geekdoc",
)

#genrule(
#    name = "copy_gen_files",
#    srcs = ["//api:api_documents_tar"],
#    outs = ["content/en/model"],
#    cmd = "mkdir -p $(RULEDIR)/content/en/model && tar -C $(RULEDIR)/content/en/model -zxf $(SRCS)",
#)

py_binary(
    name = "gen_docs",
    srcs = ["doc-gen.py"],
    main = "doc-gen.py",
    deps = [
        "//google/cloud/ml/applied",
        requirement("pydoc-markdown"),
    ],
)

doc_gen(
    name = "applied",
    target = "//google/cloud/ml/applied",
    title = "Applied",
)

doc_gen(
    name = "attributes",
    target = "//google/cloud/ml/applied/attributes",
    title = "Attributes",
)

doc_gen(
    name = "categories",
    target = "//google/cloud/ml/applied/categories",
    title = "Categories",
)

doc_gen(
    name = "embeddings",
    target = "//google/cloud/ml/applied/embeddings",
    title = "Embeddings",
)

doc_gen(
    name = "images",
    target = "//google/cloud/ml/applied/images",
    title = "Images",
)

doc_gen(
    name = "nearest_neighbors",
    target = "//google/cloud/ml/applied/knn",
    title = "Nearest Neighbor",
)

doc_gen(
    name = "marketing",
    target = "//google/cloud/ml/applied/marketing",
    title = "Marketing",
)

doc_gen(
    name = "model",
    target = "//google/cloud/ml/applied/model",
    title = "Model",
)

doc_gen(
    name = "utilities",
    target = "//google/cloud/ml/applied/utils",
    title = "Utilities",
)

hugo_site(
    name = "docs",
    assets = glob(["assets/**"]),
    config_dir = glob(["config/**"]),
    content = glob(["content/**"]) + [
        ":applied",
        ":attributes",
        ":categories",
        ":embeddings",
        ":images",
        ":nearest_neighbors",
        ":marketing",
        ":model",
        ":utilities",
    ],
    data = glob(["data/**"]),
    images = glob(["images/**"]),
    layouts = glob(["layouts/**"]),
    quiet = False,
    static = glob(["static/**"]),
    theme = ":hugo_theme_geekdoc",
    verbose = True,
)

# Run local development server
hugo_serve(
    name = "serve",
    dep = [
        ":docs",
    ],
)
