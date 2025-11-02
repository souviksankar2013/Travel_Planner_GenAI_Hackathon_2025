import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types
from google.adk.events import Event, EventActions
from main_agent.agent import root_agent
from google.cloud.sql.connector import Connector, IPTypes
from typing import Optional
import os
import time
import uuid


# ------------------------------------------
# Initialize FastAPI
# ------------------------------------------
app = FastAPI()

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name="main_agent", session_service=session_service)

# ------------------------------------------
# CORS setup
# ------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trip-planner-genai-hackathon.web.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------
# Cloud SQL Connection (Loop-safe)
# ------------------------------------------

async def get_db_connection():
    """
    Create and close a Cloud SQL connection safely per request.
    Avoids event loop mismatch errors.
    """
    # Create connector *inside* the function (loop-safe)
    async with Connector() as connector:
        conn = await connector.connect_async(
            os.getenv("INSTANCE_CONNECTION_NAME"),
            "asyncpg",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME", "booking"),
            ip_type=IPTypes.PUBLIC,  # Use PRIVATE if using VPC
        )
        return conn


# ------------------------------------------
# Request Models
# ------------------------------------------
class CreateSessionRequest(BaseModel):
    user_id: str

class SendMessageRequest(BaseModel):
    user_id: str
    session_id: str
    text: str

class DestroySessionRequest(BaseModel):
    user_id: str
    session_id: str

class BookingRequest(BaseModel):
    user_name: str
    email: str
    hotel_name: str
    room_type: str
    price: float
    arrival_date: str
    departure_date: str

class UserInputRequest(BaseModel):
    session_id: str
    user_id: str
    place_name: Optional[str] = None
    duration: Optional[str] = None
    budget: Optional[str] = None
    places: Optional[str] = None

# ------------------------------------------
# Endpoints
# ------------------------------------------
@app.post("/create_session")
async def create_session(req: CreateSessionRequest):
    session = await session_service.create_session(
        app_name="main_agent",
        user_id=req.user_id,
        state={"username": req.user_id}
    )
    return {
        "message": f"Session created for {req.user_id}",
        "session_id": session.id,
        "user_id": session.user_id,
        "state": session.state
    }

@app.post("/send_message")
async def send_message(req: SendMessageRequest):
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

@app.post("/saveBooking")
async def save_booking(req: BookingRequest):
    """
    Saves booking details into Google Cloud SQL (PostgreSQL).
    """
    conn = None
    try:
        # Get both connection and connector
        conn= await get_db_connection()

        # Execute insert query
        await conn.execute(
            """
            INSERT INTO booking (
                user_name, email, hotel_name, room_type,
                price, arrival_date, departure_date, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """,
            req.user_name,
            req.email,
            req.hotel_name,
            req.room_type,
            req.price,
            req.arrival_date,
            req.departure_date,
        )

        return {"status": "success", "message": "Booking saved successfully"}

    except Exception as e:
        import traceback
        print("DB ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error saving booking: {str(e)}")

    finally:
        if conn:
            await conn.close()

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
    try:
        await session_service.delete_session(
            app_name="main_agent",
            user_id=req.user_id,
            session_id=req.session_id,
        )
        return {"message": f"Session {req.session_id} destroyed for {req.user_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
