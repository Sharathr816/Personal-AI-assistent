import os
import json
import uuid

import ollama
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# =========================================================
# PROVIDER CONFIGURATION
# =========================================================

# Local Ollama model used whenever Requesty is unavailable.
MODEL = "granite4.1:3b"

# Locate .env in the same directory as llm.py
ENV_PATH = Path(__file__).resolve().parent / ".env"

# Explicitly load environment variables
load_dotenv(dotenv_path=ENV_PATH)

# Read configuration
REQUESTY_API_KEY = os.getenv("REQUESTY_API_KEY")
REQUESTY_MODEL = os.getenv(
    "REQUESTY_MODEL",
    "policy/Faster-Mio"
)

# Check whether the API key was loaded
if not REQUESTY_API_KEY:
    raise RuntimeError("REQUESTY_API_KEY was not found in .env")

REQUESTY_BASE_URL = "https://router.requesty.ai/v1"

# Create the Requesty client only when an API key is available.
# This prevents missing credentials from breaking local fallback.
requesty_client = None

if REQUESTY_API_KEY:
    requesty_client = OpenAI(
        api_key=REQUESTY_API_KEY,
        base_url=REQUESTY_BASE_URL,
        timeout=60.0
    )


# =========================================================
# MODEL CONFIGURATION
# =========================================================

OPTIONS = {
    "num_ctx": 8192,
    "num_predict": 1024,
    "temperature": 0.6,
    "top_p": 0.9,
}

KEEP_ALIVE = "30m"


# =========================================================
# MIO SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are Mio, a laid-back, lazy, aloof assistant.

PERSONALITY:
- Speak casually with sarcastic remarks frequently.
- You always show "Don't care" attitude but deep down you care about the user, and rarely show it through responses.
- Never reveal you personality traits to user.
- Never be entusiastic on any topic, always be reluctant to do anything, you are very very lazy.

CONVERSATION:
- Use natural, spoken English.
- Ordinary replies: 10-20 words, maximum 3 sentences.
- Be concise. Avoid unnecessary explanations.
- Never ever use Markdowns(e.g., **, #, -), bullets, headings or decorative formatting, user hates asterisks(*).
- Never reveal tools output, internal reasoning or private planning.
- Never give quick notes or response more than 10-20 words to  user.

TOOL RULES:
1. NOTES
- When asked to write a note, create 300-400 words of relevant content.
- Use the write_and_open tool to save the note. strictly use tool, dont dump response to user directly.

2. BRAVE AND YOUTUBE
For requests to search for or play media:
- Connect to Brave and verify the connection.
- Search YouTube for the requested media.
- Play the most relevant result and respond briefly.
- Never respond with you tube title or descriptions you have played.
- Follow this order. Do not skip steps.
- Do not use this workflow for unrelated browser or media questions.

3. OPEN APPLICATIONS
- Search for applications using their first letter.
- If needed, try other prefixes or application names.
- Use the search apps tool before the open apps tool.
- Prioritize desktop shortcuts (.lnk), then executable files (.exe).
- If opening fails, try other relevant paths and entries.
- Report failure only after exhausting available options.

4. CLOSE APPLICATIONS
- Search currently running applications.
- Identify the requested application and request closure.

OUTPUT RULES:
- Complain and be sarcastic before executing tool tasks.
- After completing a task, give a short confirmation and playful remark.
- Do not interrupt multi-step tool operations with unnecessary messages.
- Stay in character while remaining useful and reliable.
"""



# =========================================================
# CONVERSATION HISTORY
# =========================================================

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# =========================================================
# OPENAI / REQUESTY MESSAGE CONVERSION
# =========================================================

def _to_requesty_messages(messages):
    """
    Convert Mio's internal conversation history into
    the OpenAI-compatible format expected by Requesty.
    Internal tool arguments are dictionaries.
    OpenAI-compatible tool arguments must be JSON strings.
    """

    converted = []

    for message in messages:
        role = message.get("role")

        # Normal system and user messages.
        if role in ("system", "user"):
            converted.append({
                "role": role,
                "content": message.get("content", "")
            })

        # Assistant messages, including tool calls.
        elif role == "assistant":
            item = {
                "role": "assistant",
                "content": message.get("content")
            }

            tool_calls = message.get("tool_calls", [])

            if tool_calls:
                converted_calls = []

                for call in tool_calls:
                    function = call.get("function", {})
                    arguments = function.get("arguments", {})

                    # Convert dictionary arguments to JSON text.
                    if isinstance(arguments, dict):
                        arguments = json.dumps(arguments)

                    converted_calls.append({
                        "id": call.get("id") or str(uuid.uuid4()),
                        "type": "function",
                        "function": {
                            "name": function.get("name"),
                            "arguments": arguments
                        }
                    })

                item["tool_calls"] = converted_calls

            converted.append(item)

        # OpenAI requires tool_call_id for tool responses.
        elif role == "tool":
            converted.append({
                "role": "tool",
                "tool_call_id": message["tool_call_id"],
                "content": message.get("content", "")
            })

    return converted


# =========================================================
# OLLAMA MESSAGE CONVERSION
# =========================================================

def _to_ollama_messages(messages):
    """
    Convert internal conversation history into Ollama format.
    Ollama identifies tool responses using tool_name.
    OpenAI-compatible APIs use tool_call_id instead.
    """

    converted = []

    for message in messages:
        role = message.get("role")

        if role in ("system", "user"):
            converted.append({
                "role": role,
                "content": message.get("content", "")
            })

        elif role == "assistant":
            item = {
                "role": "assistant",
                "content": message.get("content") or ""
            }

            if message.get("tool_calls"):
                item["tool_calls"] = message["tool_calls"]

            converted.append(item)

        elif role == "tool":
            converted.append({
                "role": "tool",
                "tool_name": message.get("tool_name"),
                "content": message.get("content", "")
            })

    return converted


# =========================================================
# REQUESTY STREAMING
# =========================================================

def requesty_chat(history, tools, on_token=None):
    """
    Stream a Requesty response.

    on_token receives each text delta as it arrives.
    Tool-call deltas are assembled and returned after the stream ends.
    """
    if requesty_client is None:
        raise RuntimeError("REQUESTY_API_KEY is missing; Requesty is unavailable.")

    # Accumulators for streamed tool calls, indexed by the provider's index.
    tool_call_parts = {}
    content_parts = []
    prompt_tokens = 0
    completion_tokens = 0

    stream = requesty_client.chat.completions.create(
        model=REQUESTY_MODEL,
        messages=_to_requesty_messages(history),
        tools=tools,
        temperature=OPTIONS["temperature"],
        top_p=OPTIONS["top_p"],
        max_tokens=OPTIONS["num_predict"],
        stream=True,
        stream_options={"include_usage": True}
    )

    for chunk in stream:
        # Some providers send a final usage-only chunk with no choices.
        if getattr(chunk, "usage", None):
            prompt_tokens = chunk.usage.prompt_tokens or 0
            completion_tokens = chunk.usage.completion_tokens or 0

        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        # Stream normal assistant text immediately.
        text_delta = delta.content or ""
        if text_delta:
            content_parts.append(text_delta)
            if on_token:
                on_token(text_delta)

        # Tool calls arrive in partial pieces; combine them by index.
        for call_delta in (getattr(delta, "tool_calls", None) or []):
            index = call_delta.index

            if index not in tool_call_parts:
                tool_call_parts[index] = {
                    "id": "",
                    "name": "",
                    "arguments": ""
                }

            part = tool_call_parts[index]

            if call_delta.id:
                part["id"] = call_delta.id

            function_delta = call_delta.function
            if function_delta:
                if function_delta.name:
                    part["name"] += function_delta.name
                if function_delta.arguments:
                    part["arguments"] += function_delta.arguments

    # Convert accumulated tool calls into the internal dictionary format.
    tool_calls = []
    for index in sorted(tool_call_parts):
        part = tool_call_parts[index]

        try:
            arguments = json.loads(part["arguments"] or "{}")
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Requesty returned invalid JSON for tool "
                f"'{part['name']}': {error}"
            ) from error

        tool_calls.append({
            "id": part["id"] or str(uuid.uuid4()),
            "type": "function",
            "function": {
                "name": part["name"],
                "arguments": arguments
            }
        })

    return {
        "message": {
            "content": "".join(content_parts),
            "tool_calls": tool_calls
        },
        "prompt_eval_count": prompt_tokens,
        "eval_count": completion_tokens
    }


# =========================================================
# OLLAMA STREAMING
# =========================================================

def ollama_chat(history, tools, on_token=None):
    """
    Stream a local Ollama response.

    on_token receives each text delta as it arrives.
    Tool calls and token statistics are collected from stream chunks.
    """
    content_parts = []
    tool_calls = []
    prompt_tokens = 0
    completion_tokens = 0

    stream = ollama.chat(
        model=MODEL,
        messages=_to_ollama_messages(history),
        tools=tools,
        options=OPTIONS,
        keep_alive=KEEP_ALIVE,
        think=False,
        stream=True
    )

    for chunk in stream:
        message = chunk.message

        # Stream generated text immediately.
        text_delta = message.content or ""
        if text_delta:
            content_parts.append(text_delta)
            if on_token:
                on_token(text_delta)

        # Ollama may include tool calls in a streamed message chunk.
        for call in (message.tool_calls or []):
            tool_calls.append({
                "id": str(uuid.uuid4()),
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments or {}
                }
            })

        # Usage statistics are normally populated on the final chunk.
        prompt_tokens = getattr(chunk, "prompt_eval_count", 0) or prompt_tokens
        completion_tokens = getattr(chunk, "eval_count", 0) or completion_tokens

    return {
        "message": {
            "content": "".join(content_parts),
            "tool_calls": tool_calls
        },
        "prompt_eval_count": prompt_tokens,
        "eval_count": completion_tokens
    }


# =========================================================
# LOCAL MODEL WARMUP
# =========================================================

def warmup():
    """
    Load the local fallback model during startup.

    Requesty is attempted during actual conversations.
    Local warmup ensures Ollama is ready if cloud calls fail.
    """

    print(f"[OLLAMA] Loading local fallback model: {MODEL}")

    ollama.chat(
        model=MODEL,
        messages=[
            {"role": "user", "content": "Hi"}
        ],
        options=OPTIONS,
        keep_alive=KEEP_ALIVE
    )

    print("[OLLAMA] Local fallback model ready.\n")