import os
import uuid
from datetime import datetime
from collections.abc import AsyncIterable
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel
from typing import List, Dict
from openai import OpenAI
from openai.types.responses import ResponseTextDeltaEvent, ResponseCompletedEvent
from dotenv import load_dotenv
from aws_bedrock_token_generator import provide_token

from agents import Runner, RunConfig, ModelSettings, trace
from digital_twin_agents import digital_twin_agent
from mcp_servers import github_mcp_server
from models import ChatRequest, ChatResponse
from context import DIGITAL_TWIN_GREETING_SYSTEM_PROMPT, EXAMPLES
from utils import (
    load_conversation,
    save_conversation,
    append_and_save_conversation_pair,
)
from contextlib import AsyncExitStack

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Memory storage configuration
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
MODEL_ID = os.getenv("LLM_MODEL_ID") or "openai.gpt-oss-120b"

# Initialize S3 client if needed

openai_client = OpenAI(
    api_key=provide_token(),
    base_url=os.getenv("AWS_BEDROCK_BASE_URL"),
    project=os.getenv("PROJECT_ID"),
)


@app.get("/")
async def root():
    return {
        "message": "AI Digital Twin API",
        "memory_enabled": True,
        "storage": "S3" if USE_S3 else "local",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "use_s3": USE_S3}


@app.get("/greeting", response_class=EventSourceResponse)
async def greeting_streamed() -> AsyncIterable[ChatResponse]:
    session_id = str(uuid.uuid4())
    conversation = load_conversation(session_id)
    messages = [{"role": "system", "content": DIGITAL_TWIN_GREETING_SYSTEM_PROMPT}]

    for msg in conversation[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append(
        {"role": "user", "content": "Generate a greeting message for the visitor"}
    )
    conversation.append(
        {
            "role": "user",
            "content": "Generate a greeting message for the visitor",
        }
    )
    conversation.append({"role": "assistant", "content": ""})

    with trace(f"Running digital twin agent session {session_id}"):
        stream = openai_client.responses.create(
            model="openai.gpt-oss-120b", input=messages, stream=True
        )

        for event in stream:
            if event.type == "response.output_text.delta":
                conversation[-1]["content"] += event.delta
                yield ChatResponse(response=event.delta, session_id=session_id)
            elif event.type == "response.completed":
                append_and_save_conversation_pair(
                    conversation,
                    "Generate a greeting message for the visitor",
                    event.response.output_text,
                    session_id=session_id,
                )


@app.post("/chat", response_class=EventSourceResponse)
async def chat(request: ChatRequest) -> AsyncIterable[ChatResponse]:
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Load conversation history
        conversation = load_conversation(session_id)

        messages = []

        for msg in conversation[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": request.message})

        with trace(f"Running digital twin agent session {session_id}"):
            # async with github_mcp_server:
            async with AsyncExitStack() as stack:
                await stack.enter_async_context(github_mcp_server)
                agent_stream = Runner.run_streamed(
                    digital_twin_agent,
                    input=messages,
                    max_turns=10,
                    run_config=RunConfig(model_settings=ModelSettings(temperature=0.7)),
                )

                async for event in agent_stream.stream_events():
                    if event.type == "raw_response_event" and isinstance(
                        event.data, ResponseTextDeltaEvent
                    ) and event.data.delta:
                        print(f"Received raw response event: {event}")
                        yield ChatResponse(
                            response=event.data.delta, session_id=session_id
                        )
                    elif event.type == "response_completed_event" and isinstance(
                        event.data, ResponseCompletedEvent
                    ):
                        append_and_save_conversation_pair(
                            conversation,
                            request.message,
                            event.data.response.output_text,
                            session_id=session_id,
                        )
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Retrieve conversation history"""
    try:
        conversation = load_conversation(session_id)
        return {"session_id": session_id, "messages": conversation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cv")
async def get_cv():
    """Return the CV PDF as a file response (client can fetch as blob)."""
    cv_path = os.path.join(os.path.dirname(__file__), "public", "anton_kovachev_cv.pdf")
    if not os.path.exists(cv_path):
        raise HTTPException(status_code=404, detail="CV not found")
    return FileResponse(
        cv_path, media_type="application/pdf", filename="anton_kovachev_cv.pdf"
    )


@app.get("/sample-prompts", response_model=list[str])
async def get_sample_prompts():
    """Return a list of sample prompts."""
    return EXAMPLES


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
