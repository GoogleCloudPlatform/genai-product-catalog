import unittest

from enrichment.chain import Chain, Command, Context


class Cmd1(Command):
    def execute(self, context: Context):
        context.add("test_string", "value")

class Cmd2(Command):
    def execute(self, context: Context):
        context.add("test_string", context.get("test_string") + "_1")

class TestChain(unittest.TestCase):
    def test_chain(self):
        chain = Chain()
        chain.add_command(Cmd1())
        chain.add_command(Cmd2())

        ctx = Context()
        chain.execute(ctx)

        out = ctx.get("test_string")
        self.assertEqual(out, "value_1")
