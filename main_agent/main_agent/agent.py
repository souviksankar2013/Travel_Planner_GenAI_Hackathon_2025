from google.adk.agents.llm_agent import Agent
from .sub_agents.itinery_extract.agent import itinery_agent
from .sub_agents.welcome.agent import welcome_agent
from .sub_agents.hotel_booking.agent import hotel_booking_agent
from .sub_agents.booking_and_payment.agent import booking_and_payment_agent

from . import prompt

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A Root Travel Assistant Agent.',
    instruction=prompt.PROMPT,
    sub_agents=[welcome_agent, itinery_agent,hotel_booking_agent,booking_and_payment_agent],
)
