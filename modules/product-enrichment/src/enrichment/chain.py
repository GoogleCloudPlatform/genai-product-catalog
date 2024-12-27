from typing import Dict, Any, List
from abc import ABC, abstractmethod


class Context(object):
    state: Dict[str, Any]
    errors: List[Exception]

    def __init__(self, state: Dict[str, Any]):
        self.errors = []
        self.state = state

    def add(self, key: str, value: Any):
        self.state[key] = value

    def remove(self, key: str):
        del self.state[key]

    def has_errors(self):
        return self.errors != []

    def add_error(self, error: Exception):
        self.errors.append(error)

    def clear_errors(self):
        self.errors = []

class Command(ABC):
    @abstractmethod
    def execute(self, context: Context) -> bool:
        pass

class Chain(Command):
    commands: List[Command]
    fail_on_error: bool = False

    def __init__(self, commands=None, fail_on_error: bool = False):
        if commands is None:
            commands = []
        self.commands = commands
        self.fail_on_error = fail_on_error

    def add_command(self, command: Command):
        self.commands.append(command)

    def remove_command(self, command: Command):
        self.commands.remove(command)

    def execute(self, context: Context):
        for command in self.commands:
            command.execute(context)
            if self.fail_on_error and context.has_errors():
                return False
        return True
