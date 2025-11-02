"""Booking agent and sub-agents, handling the confirmation and payment of selected hotels."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from main_agent.sub_agents.booking_and_payment import prompt

# ===========================
# BOOKING & PAYMENT AGENT
# ===========================
booking_and_payment_agent = Agent(
    model="gemini-2.5-flash",
    name="booking_and_payment_agent",
    description=(
        "An intelligent sub-agent that handles hotel booking confirmations "
        "and payment processing after a user selects a hotel in the format "
        "HOTELNAME_RATING_ROOMTYPE_PRICE."
    ),
    instruction=prompt.BOOK_PAYMENT_INSTR,
    tools=[],  # No external tools or function calls needed
    generate_content_config=GenerateContentConfig(
        temperature=0.0,
        top_p=0.5
    ),
)


