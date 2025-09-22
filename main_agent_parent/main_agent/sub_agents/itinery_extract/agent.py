from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from google.adk.tools import FunctionTool

from main_agent.sub_agents.itinery_extract import prompt
import httpx,os


itinery_agent = Agent(
    model="gemini-2.5-flash",
    name="itinery_agent",
    description="""interact with the user and collect details step by step to design their trip""",
    instruction=prompt.ITINERY_AGENT_INSTR,
    
)