import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types
from main_agent.agent import root_agent
from google.adk.events import Event, EventActions
import time
import uuid
from typing import Optional


# Initialize FastAPI
app = FastAPI()

# Session service (in-memory for demo; replace with Firestore/Redis in production)
session_service = InMemorySessionService()

# Create a runner for the agent
runner = Runner(agent=root_agent, app_name="main_agent", session_service=session_service)

# -------------------------
# CORS setup
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trip-planner-genai-hackathon.web.app"],  # only your frontend
    allow_credentials=True,
    allow_methods=["*"],  # or ["POST", "GET", "OPTIONS"]
    allow_headers=["*"],  # or ["Content-Type", "Authorization"]
)



# -------------------------
# Request models
# -------------------------
class CreateSessionRequest(BaseModel):
    user_id: str


class SendMessageRequest(BaseModel):
    user_id: str
    session_id: str
    text: str


class DestroySessionRequest(BaseModel):
    user_id: str
    session_id: str


APP_NAME = "main_agent"

class PlaceRequest(BaseModel):
    session_id: str
    place_name: str
    user_id: str

class UserInputRequest(BaseModel):
    session_id: str
    user_id: str
    place_name: Optional[str] = None
    duration: Optional[str] = None
    budget: Optional[str] = None
    places:  Optional[str] = None


# -------------------------
# Endpoints
# -------------------------
@app.post("/create_session")
async def create_session(req: CreateSessionRequest):
    """
    Creates a new ADK session and stores the username in session state.
    """
    session = await session_service.create_session(
        app_name="main_agent",
        user_id=req.user_id,
        state={"username": req.user_id}   # store username in session state
    )

    return {
        "message": f"Session created for {req.user_id}",
        "session_id": session.id,
        "user_id": session.user_id,
        "state": session.state
    }


@app.post("/send_message")
async def send_message(req: SendMessageRequest):
    """
    Sends a message to the agent using the Runner and returns the response.
    """
    responses = []
    async for event in runner.run_async(
        user_id=req.user_id,
        session_id=req.session_id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=req.text)]
        ),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            responses.append(event.content.parts[0].text)

    return {"responses": responses}




# @app.post("/save_place")
# async def save_place(req: PlaceRequest):
#     session = await session_service.get_session(
#         app_name="main_agent",
#         user_id=req.user_id,
#         session_id=req.session_id,
#     )
#     if not session:
#         return {"error": "Session not found"}

#     # # Build state delta
#     state_changes = {"place_name": req.place_name}

#     # # Create the EventActions
#     actions = EventActions(state_delta=state_changes)

#     # # Create an Event object
#     event = Event(
#         invocation_id=str(uuid.uuid4()),
#         author="user",             # or whatever makes sense
#         actions=actions,
#         timestamp=int(time.time() * 1000)  # milliseconds, or appropriate format
#         # content or other fields if needed
#     )

#     # # Append the event
#     await session_service.append_event(session,event)

#     updated_session = await session_service.get_session(
#         app_name="main_agent",
#         user_id=session.user_id,
#         session_id=req.session_id,
#     )

#     return {"status": "ok", "session": session}


@app.post("/save_user_input")
async def save_user_input(req: UserInputRequest):
    session = await session_service.get_session(
        app_name="main_agent",
        user_id=req.user_id,
        session_id=req.session_id,
    )
    if not session:
        return {"error": "Session not found"}

    state_changes = {}
    if req.place_name:
        state_changes["place_name"] = req.place_name
    if req.duration:
        state_changes["duration"] = req.duration
    if req.budget:
        state_changes["budget"] = req.budget
    
    if req.places:
        state_changes["places"] = req.places

    actions = EventActions(state_delta=state_changes)
    event = Event(
        invocation_id=str(uuid.uuid4()),
        author="user",
        actions=actions,
        timestamp=int(time.time() * 1000),
    )
    await session_service.append_event(session, event)

    updated_session = await session_service.get_session(
        app_name="main_agent",
        user_id=session.user_id,
        session_id=req.session_id,
    )

    return {"status": "ok", "session": updated_session.state}






@app.post("/destroy_session")
async def destroy_session(req: DestroySessionRequest):
    """
    Destroys an existing ADK session for the given user and session_id.
    """
    try:
        # Attempt to delete the session
        await session_service.delete_session(
            app_name="main_agent",
            user_id=req.user_id,
            session_id=req.session_id,
        )
        return {"message": f"Session {req.session_id} destroyed for {req.user_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

