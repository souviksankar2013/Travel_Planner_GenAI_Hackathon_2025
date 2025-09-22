# agent.py
import httpx
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from . import prompt
import os

MCP_BASE_URL = os.environ.get("MCP_URL")

# Tools
def filter_hotels(params: dict):
    """
    Calls the FastAPI /filter_hotels endpoint.
    Filter hotels based on criteria like room type, price range, rating and facilities.
    """
    try:
        resp = httpx.post(f"{MCP_BASE_URL}/filter_hotels", json=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def hotel_distances(params: dict):
    """
    Calls the FastAPI /hotel_distances endpoint. Calculates distance between hotels and tourist places.
    """
    try:
        resp = httpx.post(f"{MCP_BASE_URL}/hotel_distances", json=params, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
    


# Wrap hotel filter function
filter_hotels_tool = FunctionTool(
    func=filter_hotels
    
)

# Wrap hotel distance function
hotel_distances_tool = FunctionTool(
    func=hotel_distances
    
)




# Main Agent
hotel_booking_agent = Agent(
    name="hotel_booking_agent",
    model="gemini-2.5-flash",
    description="Agent to help search and filter hotels and geocode places.",
    instruction=prompt.SEARCH_HOTELS_INSTR,
    tools=[filter_hotels_tool, hotel_distances_tool]  # ✅ functions wrapped as tools
    
)
