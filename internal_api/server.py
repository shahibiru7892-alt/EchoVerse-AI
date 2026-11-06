from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from chatbot import generate_response
from database.db import (
    initialize_database,
    create_conversation,
    get_messages
)


# Initialize FastAPI
app = FastAPI(
    title="EchoVerse AI API",
    description="AI Entertainment Chatbot API powered by Groq",
    version="1.0.0"
)


# Initialize database
initialize_database()


# Request model
class ChatRequest(BaseModel):
    conversation_id: int
    message: str


# Home endpoint
@app.get("/")
def home():

    return {
        "message": "Welcome to EchoVerse AI API",
        "status": "Running"
    }


# Create conversation
@app.post("/conversation")
def new_conversation():

    conversation_id = create_conversation()

    return {
        "conversation_id": conversation_id,
        "message": "Conversation created successfully"
    }


# Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    reply = generate_response(
        request.message,
        request.conversation_id
    )

    return {
        "user_message": request.message,
        "ai_response": reply
    }


# Get conversation history
@app.get("/conversation/{conversation_id}")
def conversation_history(conversation_id: int):

    messages = get_messages(conversation_id)

    return {
        "conversation_id": conversation_id,
        "history": messages
    }