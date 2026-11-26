
import json
import re

import llm
from agent.registry import TOOL_REGISTRY, execute_tool


# =========================================================
# PERSISTENT CONVERSATION HISTORY
# =========================================================

MEMORY_PREFIX = "Saved user memories:"

messages = [
    {
        "role": "system",
        "content": llm.SYSTEM_PROMPT
    }
]


# =========================================================
# TOKEN USAGE TRACKING
# =========================================================

TOKEN_USAGE = {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0,
    "llm_calls": 0
}


# =========================================================
# CONVERSATION MANAGEMENT
# =========================================================

def trim_history(max_exchanges=3):
    """
    Preserve:
    - Permanent system prompt.
    - Saved memory context.
    - Latest N complete user-assistant exchanges.

    Tool calls and their results remain together.
    """

    system_messages = [
        msg for msg in messages
        if msg.get("role") == "system"
    ]

    conversation = [
        msg for msg in messages
        if msg.get("role") != "system"
    ]

    exchanges = []
    current_exchange = []

    for msg in conversation:

        if msg.get("role") == "user":

            if current_exchange:
                exchanges.append(current_exchange)

            current_exchange = [msg]

        else:
            if current_exchange:
                current_exchange.append(msg)

    if current_exchange:
        exchanges.append(current_exchange)

    recent_exchanges = exchanges[-max_exchanges:]

    messages[:] = system_messages + [
        msg
        for exchange in recent_exchanges
        for msg in exchange
    ]


# =========================================================
# TERMINAL DISPLAY
# =========================================================

def display_conversation():
    print("\n" + "=" * 65)
    print("                    MIO CONVERSATION")
    print("=" * 65)

    for msg in messages:
        role = msg.get("role")

        if role == "system":
            continue

        if role == "user":
            print("\nUser:", msg.get("content", ""))

        elif role == "assistant":
            tool_calls = msg.get("tool_calls") or []

            if tool_calls:
                for call in tool_calls:
                    name = call.get("function", {}).get("name", "Unknown")
                    print(f"\n  [TOOL CALL🔨] {name}")
            else:
                print("\nMIO:", msg.get("content", ""))

        elif role == "tool":
            print("\nDone using tool🔨✅")

    print("\n" + "=" * 65)
    print("                 END OF CONVERSATION")
    print("=" * 65 + "\n")

# =========================================================
# RECORD MEMORY COMMAND EXCHANGES
# =========================================================

def record_exchange(user_input, response_text):

    messages.append({
        "role": "user",
        "content": user_input
    })

    messages.append({
        "role": "assistant",
        "content": response_text
    })

    trim_history(max_exchanges=3)
    display_conversation()


# =========================================================
# MEMORY CONTEXT MANAGEMENT
# =========================================================

def update_memory_context(memory_context=None):
    """
    Update saved memories in conversation history.

    None:
        Preserve the existing memory context.

    Non-None:
        Insert memory context if absent.
        Replace existing memory context if present.
    """

    if memory_context is None:
        return

    memory_message = {
        "role": "system",
        "content": f"{MEMORY_PREFIX}\n{memory_context}"
    }

    for index, msg in enumerate(messages):
        if (
            msg.get("role") == "system"
            and msg.get("content", "").startswith(MEMORY_PREFIX)
        ):
            messages[index] = memory_message
            return

    # Insert memory context after the permanent system prompt.
    messages.insert(1, memory_message)


# =========================================================
# STREAMED TEXT -> TTS CHUNKING
# =========================================================

def _make_tts_streamer(on_chunk):
    """
    Convert token-sized deltas into sentence-sized TTS chunks.

    This avoids sending tiny fragments to TTS while still allowing speech
    to begin before the model has generated its complete response.
    """
    buffer = ""
    sentence_end = re.compile(r'(?<=[.!?])\s+')

    def feed(token_text):
        nonlocal buffer

        buffer += token_text

        # Send complete sentences as soon as possible.
        while True:
            match = sentence_end.search(buffer)
            if not match:
                break

            sentence = buffer[:match.end()].strip()
            buffer = buffer[match.end():]

            if sentence:
                on_chunk(sentence)

    def flush():
        nonlocal buffer
        remainder = buffer.strip()
        buffer = ""

        if remainder:
            on_chunk(remainder)

    return feed, flush


# =========================================================
# AGENT ORCHESTRATOR
# =========================================================

def run_agent(user_input, memory_context=None, on_chunk=None):
    """
    Run one agent turn.

    Requesty is attempted first. If a cloud call fails, Ollama handles
    the rest of this turn. Both providers stream text into the same TTS
    sentence buffer.
    """
    update_memory_context(memory_context)

    messages.append({
        "role": "user",
        "content": user_input
    })

    tools = [
        tool["schema"]
        for tool in TOOL_REGISTRY.values()
    ]

    response_text = ""
    input_tokens = 0
    output_tokens = 0
    llm_calls = 0

    # Each new user turn starts with Requesty.
    active_provider = "requesty"

    # Build the optional TTS callback. If no callback is supplied,
    # generation still streams internally but nothing is spoken here.
    tts_feed = None
    tts_flush = None

    if on_chunk:
        tts_feed, tts_flush = _make_tts_streamer(on_chunk)

    # Prevent a failed cloud stream from leaving an incomplete sentence
    # in the TTS buffer. Already spoken complete sentences cannot be undone.
    cloud_stream_started = False

    for iteration in range(10):
        llm_calls += 1

        try:
            if active_provider == "requesty":
                print(f"[LLM] Requesty call {iteration + 1}")

                response = llm.requesty_chat(
                    messages,
                    tools,
                    on_token=tts_feed
                )

            else:
                print(f"[LLM] Ollama fallback call {iteration + 1}")

                response = llm.ollama_chat(
                    messages,
                    tools,
                    on_token=tts_feed
                )

        except Exception as error:
            if active_provider == "requesty":
                print(f"[REQUESTY ERROR] {type(error).__name__}: {error}")
                print("[FALLBACK] Switching to local Ollama.")

                active_provider = "ollama"

                # If cloud output had already begun, the user may have
                # heard part of it. Clear only the unsent TTS remainder.
                if tts_feed:
                    tts_feed, tts_flush = _make_tts_streamer(on_chunk)

                continue

            # Local provider also failed. Surface the actual error.
            print(f"[OLLAMA ERROR] {type(error).__name__}: {error}")
            response_text = "I'm having trouble reaching both language models."
            messages.append({
                "role": "assistant",
                "content": response_text
            })
            break

        input_tokens += response.get("prompt_eval_count", 0) or 0
        output_tokens += response.get("eval_count", 0) or 0

        assistant_message = response["message"]
        content = assistant_message.get("content", "") or ""
        tool_calls = assistant_message.get("tool_calls") or []

        # Final assistant response: save it and finish the turn.
        if not tool_calls:
            response_text = content

            messages.append({
                "role": "assistant",
                "content": response_text
            })

            break

        # Store the assistant tool-call message in history.
        messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls
        })

        # Execute each requested tool through the registry allowlist.
        for tool_call in tool_calls:
            call_id = tool_call.get("id")
            function = tool_call.get("function", {})
            name = function.get("name")
            arguments = function.get("arguments") or {}

            try:
                result = execute_tool(name, arguments)
            except Exception as error:
                result = f"Tool execution failed: {error}"

            # Keep both identifiers: Requesty needs tool_call_id;
            # Ollama needs tool_name. The conversion helpers select one.
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "tool_name": name,
                "content": str(result)
            })

    else:
        response_text = "I couldn't complete that request."
        messages.append({
            "role": "assistant",
            "content": response_text
        })

    # Flush any final partial sentence to TTS, including error responses.
    if tts_flush:
        tts_flush()

    # Update conversation history and usage statistics.
    trim_history(max_exchanges=3)

    TOKEN_USAGE["input_tokens"] = input_tokens
    TOKEN_USAGE["output_tokens"] = output_tokens
    TOKEN_USAGE["total_tokens"] = input_tokens + output_tokens
    TOKEN_USAGE["llm_calls"] = llm_calls

    print(
        f"[TOKENS] Input: {input_tokens} | "
        f"Output: {output_tokens} | Calls: {llm_calls}"
    )

    display_conversation()

    return response_text
