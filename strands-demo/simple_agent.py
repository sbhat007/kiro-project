from strands import Agent
from strands_tools import calculator, python_repl, http_request

# Create an agent with community tools (uses Bedrock Claude 4 Sonnet by default)
agent = Agent(
    tools=[calculator, python_repl, http_request],
    system_prompt="You are a helpful assistant that can perform calculations, execute Python code, and make HTTP requests."
)

# Test the agent with a simple calculation
print("Testing agent with a calculation...")
response = agent("What is 15 * 23 + 47?")
print(f"Response: {response}\n")

# Test with conversation history
print("Testing conversation memory...")
agent("My favorite number is 42")
response = agent("What's my favorite number?")
print(f"Response: {response}")
