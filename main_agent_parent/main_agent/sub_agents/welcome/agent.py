
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from main_agent.sub_agents.welcome import prompt


welcome_agent = Agent(
    model="gemini-2.5-flash",
    name="welcome_agent",
    description="A friendly agent that welcomes users and helps them get started.",
    instruction=prompt.WELCOME_AGENT_INSTR,
    generate_content_config=GenerateContentConfig(
        temperature=0.0, top_p=0.5
    )
)
