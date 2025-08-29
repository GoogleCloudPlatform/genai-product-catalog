from google.adk.agents import LlmAgent

mock_agent = LlmAgent(
    name="mock_agent",
    description="A mock agent.",
    model="gemini-1.5-flash",
    instruction="You are a mock agent.",
    output_key="mock_output",
)
