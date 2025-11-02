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
from google.adk.tools import FunctionTool

from main_agent.sub_agents.itinery_extract import prompt
import httpx,os





itinery_agent = Agent(
    model="gemini-2.5-flash",
    name="itinery_agent",
    description="""interact with the user and collect details step by step to design their trip""",
    instruction=prompt.ITINERY_AGENT_INSTR,
    
)


# payment_choice = Agent(
#     model="gemini-2.5-flash",
#     name="payment_choice",
#     description="""Show the users available payment choices.""",
#     instruction=prompt.PAYMENT_CHOICE_INSTR,
# )

# process_payment = Agent(
#     model="gemini-2.5-flash",
#     name="process_payment",
#     description="""Given a selected payment choice, processes the payment, completing the transaction.""",
#     instruction=prompt.PROCESS_PAYMENT_INSTR,
# )


# booking_agent = Agent(
#     model="gemini-2.5-flash",
#     name="booking_agent",
#     description="Given an itinerary, complete the bookings of items by handling payment choices and processing.",
#     instruction=prompt.BOOKING_AGENT_INSTR,
#     tools=[
#         AgentTool(agent=itinery_agent)
#         # AgentTool(agent=payment_choice),
#         # AgentTool(agent=process_payment),
#     ],
#     generate_content_config=GenerateContentConfig(
#         temperature=0.0, top_p=0.5
#     )
# )
