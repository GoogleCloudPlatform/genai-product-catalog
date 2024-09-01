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

"""
    This common has been added to extend the file group from function by allowing
    one or more file group content be copied between packages. This is especially
    useful when using "third_party" files.
"""

def _copy_file_groups_impl(ctx):
    """ Copies a file group to the current project and adds a prefix if specified."""
    input_files = [
        f
        for t in ctx.attr.srcs
        for f in t.files.to_list()
    ]

    # Placeholder for declaring outputs.
    output_files = []

    # Local variable for the prefix
    base_dir = ctx.attr.prefix

    # Append a file separator
    if not base_dir.endswith("/"):
        base_dir = base_dir + "/"

    for f in input_files:
        out = ctx.actions.declare_file(base_dir + f.basename)
        output_files.append(out)
        ctx.actions.run_shell(
            outputs = [out],
            inputs = depset([f]),
            arguments = [f.path, out.path],
            command = "cp $1 $2",
        )

    if len(input_files) != len(output_files):
        fail("Unable to copy all files, file count mismatch.")

    return [
        DefaultInfo(
            files = depset(output_files),
            runfiles = ctx.runfiles(files = output_files),
        ),
    ]

copy_file_groups = rule(
    implementation = _copy_file_groups_impl,
    attrs = {
        "prefix": attr.string(),
        "srcs": attr.label_list(),
    },
)
