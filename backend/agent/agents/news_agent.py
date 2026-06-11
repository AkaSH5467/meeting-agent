from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from agent.tools.web_search import web_search_tool
from agent.prompts import NEWS_AGENT_PROMPT

news_agent = LlmAgent(
    name="news_agent",
    model="gemini-2.5-flash",
    instruction=NEWS_AGENT_PROMPT,
    tools=[FunctionTool(web_search_tool)],
)