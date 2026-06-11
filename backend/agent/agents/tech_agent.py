from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from agent.tools.tech_lookup import tech_lookup_tool
from agent.prompts import TECH_AGENT_PROMPT

tech_agent = LlmAgent(
    name="tech_agent",
    model="gemini-2.5-flash",
    instruction=TECH_AGENT_PROMPT,
    tools=[FunctionTool(tech_lookup_tool)],
)