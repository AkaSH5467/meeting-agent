from google.adk.agents import LlmAgent
from agent.prompts import SYNTHESIS_AGENT_PROMPT

synthesis_agent = LlmAgent(
    name="synthesis_agent",
    model="gemini-2.5-flash",
    instruction=SYNTHESIS_AGENT_PROMPT,
    tools=[],
)