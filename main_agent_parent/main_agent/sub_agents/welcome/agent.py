# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Booking agent and sub-agents, handling the confirmation and payment of bookable events."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from main_agent.sub_agents.welcome import prompt


welcome_agent = Agent(
    model="gemini-2.5-flash",
    name="welcome_agent",
    description="A friendly agent that welcomes users and helps them get started.",
    instruction=prompt.WELCOME_AGENT_INSTR,
    tools=[
        # AgentTool(agent=create_reservation)
        # AgentTool(agent=payment_choice),
        # AgentTool(agent=process_payment),
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.0, top_p=0.5
    )
)
