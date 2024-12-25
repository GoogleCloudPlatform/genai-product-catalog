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

import logging
import argparse

from common.config import Config
from common.utils import encrypt, generate_random_string
from api.server import start as start
from db.main import create_tables

logger = logging.getLogger(__name__)
FORMAT = '[%(asctime)s] (%(filename)s . %(funcName)s :: %(lineno)d) -- %(message)s'

def main():
    logging.basicConfig(filename="application.log", level=logging.INFO, format=FORMAT)

    parser = argparse.ArgumentParser(
        prog="gRetail",
        description="A command line interface for demonstrating retail functions using Google Gemini.",
        epilog="\nGoogle Cloud Platform"
    )

    parser.add_argument("-c", "--config", action="store", help="The TOML configuration file.", default="env.toml")
    subparsers = parser.add_subparsers(dest="action", help='Command Help')

    # Generate random salt
    subparsers.add_parser('generate-salt', help='Generates a random salt')

    encrypt_password = subparsers.add_parser('encrypt-password', help='Encrypts password with local salt, not good enough for production environments unless the salt and password are seperated.')
    encrypt_password.add_argument("-p", "--password", help='The password to encrypt')
    encrypt_password.add_argument("-s", "--salt", help='The salt for the password')

    api_server = subparsers.add_parser('api-server', help='Starts the server in dev mode')
    api_server.add_argument("-i", "--ip", help='The ip address to bind the server to.', default="127.0.0.1")
    api_server.add_argument("-p", "--port", help='The port to run the server on', default=8000)
    api_server.add_argument("-r", "--reload", help='Reload the server on file changes', default=False)

    database = subparsers.add_parser("database", help="Functions for managing the database")
    database.add_argument("-i", "--initialize", help='Initializes the database tables')

    args = parser.parse_args()
    config = Config(args.config)

    match args.action:
        case 'database':
            print("Creating tables")
            if "-i" in args or "--initialize" in args:
                create_tables()
            else:
                print('No action specified')
        case 'encrypt-password':
            print("Encrypted Password: ", encrypt(args.password, args.salt))
        case 'generate-salt':
            print("Salt: ", generate_random_string(64))
        case 'api-server':
            print('Starting Server: {}:{}', args.ip, args.port)
            start(args.ip, args.port, args.reload)


if __name__ == "__main__":
    main()