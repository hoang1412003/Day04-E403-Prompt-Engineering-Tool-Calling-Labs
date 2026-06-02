from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path

# Add project root to path so we can import src
sys.path.append(str(Path(__file__).parent.parent))

from src.agent.graph import build_agent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Order Agent API")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the LangGraph agent once with custom provider
agent = build_agent(provider="custom")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Convert Pydantic models to dicts for LangGraph
    messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Invoke the agent
    response = agent.invoke({"messages": messages_dict})
    
    # Extract the final message from the agent
    final_message = response["messages"][-1]
    
    # Support both object attribute (langchain message) and dict
    content = final_message.content if hasattr(final_message, "content") else final_message["content"]
    
    return {"role": "assistant", "content": content}

