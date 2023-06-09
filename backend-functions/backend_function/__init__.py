import json
import logging
from typing import Callable

import azure.functions as func

from accessible_search import handlers, protocol, services
from backend_function.exceptions import HTTPException


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request")

    action_mapping: dict[str, Callable[[func.HttpRequest], func.HttpResponse]] = {
        "chatgpt": action_query_chatgpt,
        "chatgpt-stream": action_query_chatgpt_stream,
        "select-relevant-section": action_select_relevant_section,
        "speech-to-text": action_speech_to_text,
        "text-to-speech": action_text_to_speech,
    }

    action = req.route_params.get("action")

    try:
        return action_mapping[action](req)
    except KeyError:
        return func.HttpResponse(f"Invalid action: {action}", status_code=400)
    except HTTPException as ex:
        return func.HttpResponse(ex.msg, status_code=ex.status_code)


def action_query_chatgpt(request: func.HttpRequest) -> func.HttpResponse:
    parameters = protocol.ChatGPTRequest(**get_request_json(request))
    response_dict = handlers.handle_query_chatgpt(parameters)
    return build_json_response(response_dict)


def action_query_chatgpt_stream(request: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("Streaming not implemented for Functions backend", status_code=501)


def action_select_relevant_section(request: func.HttpRequest) -> func.HttpResponse:
    parameters = protocol.SelectRelevantSectionRequest(**get_request_json(request))
    response_dict = handlers.handle_select_relevant_section(parameters)
    return build_json_response(response_dict)


def action_speech_to_text(request: func.HttpRequest) -> func.HttpResponse:
    file = list(request.files.values())[0]
    filename = "/tmp/temp.wav"

    content = file.stream.read()
    with open(filename, "wb") as f:
        f.write(content)

    response_dict = services.perform_speech_to_text(filename=filename)

    return build_json_response(response_dict)


def action_text_to_speech(request: func.HttpRequest) -> func.HttpResponse:
    parameters = protocol.TextToSpeechRequest(**get_request_json(request))
    response_dict = services.perform_text_to_speech(parameters.text)
    return build_json_response(response_dict)


def get_request_json(request: func.HttpRequest) -> dict:
    try:
        return request.get_json()
    except ValueError as e:
        raise HTTPException(f"Invalid parameters received: {e}", status_code=400)


def build_json_response(response_dict: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(response_dict),
        status_code=status_code,
        headers={"Content-Type": "application/json"},
    )
