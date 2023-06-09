if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Annotated

import fastapi
from fastapi.responses import StreamingResponse
import uvicorn

from accessible_search import handlers, protocol, services

app = fastapi.FastAPI()

rate_limit_lock = asyncio.Lock()
rate_limit_data = defaultdict(list)
rate_limit_times = 10
rate_limit_window = timedelta(seconds=60)


@app.middleware("http")
async def rate_limit_middleware(request: fastapi.Request, call_next):
    """Rudimentary in-memory rate limiting solution."""
    global rate_limit_data

    client_ip = request.client.host
    current_time = datetime.now()

    async with rate_limit_lock:
        rate_limit_data[client_ip] = [
            time for time in rate_limit_data[client_ip]
            if current_time - time < rate_limit_window
        ]

        if len(rate_limit_data[client_ip]) >= rate_limit_times:
            raise fastapi.HTTPException(status_code=429, detail="Too Many Requests")

        rate_limit_data[client_ip].append(current_time)

    return await call_next(request)


@app.post("/api/chatgpt", response_model=protocol.TextOutputResponse)
async def query_chatgpt(parameters: protocol.ChatGPTRequest):
    response_dict = await handlers.handle_query_chatgpt_async(parameters)
    return protocol.TextOutputResponse(**response_dict)


@app.post("/api/chatgpt-stream")
async def query_chatgpt_stream(parameters: protocol.ChatGPTRequest):
    event_stream = handlers.handle_query_chatgpt_stream(parameters)
    return StreamingResponse(event_stream, media_type="text/event-stream")


@app.post("/api/select-relevant-section")
async def select_relevant_section(parameters: protocol.SelectRelevantSectionRequest):
    response_dict = await handlers.handle_select_relevant_section_async(parameters)
    return protocol.TextOutputResponse(**response_dict)


@app.post("/api/speech-to-text")
async def speech_to_text(file: Annotated[bytes, fastapi.File()]):
    response_dict = services.perform_speech_to_text(content=file)
    return protocol.TextOutputResponse(**response_dict)


@app.post("/api/text-to-speech")
async def text_to_speech(parameters: protocol.TextToSpeechRequest):
    response_dict = services.perform_text_to_speech(parameters.text)
    return protocol.TextOutputResponse(**response_dict)


if __name__ == "__main__":
    # For local testing only
    uvicorn.run("server:app", port=8000)
