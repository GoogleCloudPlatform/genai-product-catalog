#   Copyright 2022 Google LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import string
import random

DOT_SEPARATOR = '.'
DEFAULT_ENCODING = 'utf-8'
GTIN_LENGTH = 14
GTIN_RIGHT_PAD = '0'

def fix_gtin(gtin: str) -> str:
    if gtin:
        return gtin.rjust(GTIN_LENGTH, GTIN_RIGHT_PAD)
    else:
        return "".rjust(GTIN_LENGTH, GTIN_RIGHT_PAD)


def fix_prompt(value: str) -> str:
    value = value.strip()
    value = "\n".join(map(lambda x: x.strip(), value.split("\n")))
    return value


def fix_output(value: str) -> str:
    value = value.replace("```json", "")
    value = value.replace("```", "")
    return value

def get_env_file_name(file_name: str) -> str:
    env = os.environ.get('GCP_RETAIL_RUNTIME', 'local')

    env_file = None
    parts = file_name.split(DOT_SEPARATOR)
    if len(parts) == 2:
        temp_file = DOT_SEPARATOR.join([parts[0], env, parts[1]])
        if os.path.isfile(temp_file):
            env_file = temp_file

    return env_file

def generate_random_string(length):
    letters = string.ascii_letters + string.digits  # Alphanumeric characters
    return ''.join(random.choice(letters) for i in range(length))

def string_to_hex(string):
    return ''.join([hex(ord(char))[2:] for char in string])

def hex_to_string(hex_string):
    return bytes.fromhex(hex_string).decode(DEFAULT_ENCODING)

def __xor_encrypt_decrypt(text, key):
    text_bytes = text.encode(DEFAULT_ENCODING)
    key_bytes = key.encode(DEFAULT_ENCODING)
    result_bytes = bytes([b ^ k for b, k in zip(text_bytes, key_bytes)])
    return result_bytes

def encrypt(text, key):
    return (__xor_encrypt_decrypt(text, key)).hex()

def decrypt(text, key):
    converted = hex_to_string(text)
    return (__xor_encrypt_decrypt(converted, key)).decode(DEFAULT_ENCODING)
