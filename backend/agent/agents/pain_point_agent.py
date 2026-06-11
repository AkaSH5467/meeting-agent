from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from agent.tools.web_search import web_search_tool
from agent.prompts import PAIN_POINT_AGENT_PROMPT

pain_point_agent = LlmAgent(
    name="pain_point_agent",
    model="gemini-2.5-flash",
    instruction=PAIN_POINT_AGENT_PROMPT,
    tools=[FunctionTool(web_search_tool)],
)