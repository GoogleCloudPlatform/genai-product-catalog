from typing import List, Dict

from google.generativeai import GenerativeModel

from enrichment.chain import Command, Context


class DescriptionCmd(Command):
    agent_name: str
    prompt: str
    keys: List[str]

    def __init__(self, agent_name: str, prompt: str, keys: List[str]):
        self.prompt = prompt
        self.keys = keys

    def execute(self, context: Context):
        if context.has_key(self.agent_name):
            agent: GenerativeModel = context.get(self.agent_name)
            prompt_vars: Dict[str, str] = {}

            for key in self.keys:
                prompt_values = context.get_prompt_var(key)
                if prompt_values is not None:
                    prompt_vars[key] = prompt_values

            self.prompt.format(**prompt_vars)

            # TODO - Add Agent logic here



