
import json
import ollama

from llm import MODEL, OPTIONS, KEEP_ALIVE, SYSTEM_PROMPT
from agent.registry import TOOL_REGISTRY, execute_tool


# =========================================================
# PERSISTENT CONVERSATION HISTORY
# =========================================================

MEMORY_PREFIX = "Saved user memories:"

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]




# =========================================================
# CONVERSATION MANAGEMENT
# =========================================================

def trim_history(max_exchanges=3):
    """
    Preserve:
    - Permanent system prompt.
    - Saved memory context.
    - Latest N complete user-assistant exchanges.

    Tool calls and tool results remain together.
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
            # Assistant messages, tool calls and tool results
            # belong to the current user exchange.
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
# TERMINAL CONVERSATION DISPLAY
# =========================================================
def display_conversation():
    print("\n")
    print("=" * 65)
    print("                    MIO CONVERSATION")
    print("=" * 65)

    exchange_number = 0
    for msg in messages:
        role = msg.get("role")
        if role == "system":
            # print("\nSystem:",msg.get("content", ""))
            continue

        if role == "user":
            # exchange_number += 1
            # print("\n" + "-" * 65)
            # print(f" USER | Exchange {exchange_number}")
            # print("-" * 65)
            # print(msg.get("content", ""))
            print("\nUser:",msg.get("content", ""))

        elif role == "assistant":
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                for call in tool_calls:
                    function = call.get("function", {})
                    name = function.get("name", "Unknown")
                    arguments = function.get("arguments", {})
                    print(f"\n  [TOOL CALL🔨] {name}")
                    # print(
                    #     json.dumps(
                    #         arguments,
                    #         indent=4,
                    #         ensure_ascii=False,
                    #         default=str
                    #     )
                    # )

            else:
                print("\n MIO:",msg.get("content", ""))
                # print()

        elif role == "tool":
            print("\nDone using tool🔨✅")
            # print(f"\n  [TOOL RESULT] {msg.get('tool_name', 'Unknown')}")
            # print(msg.get("content", ""))

    print("\n" + "=" * 65)
    print("                 END OF CONVERSATION")
    print("=" * 65 + "\n")

# =========================================================
# Record into messages when remebering or forgetting memory
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
# MEMORY MANAGEMENT
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

    # Insert after permanent system prompt.
    messages.insert(1, memory_message)


# =========================================================
# AGENT ORCHESTRATOR
# =========================================================

def run_agent(user_input, memory_context=None, on_chunk=None):

    # Update memory only when explicitly provided.
    # Ordinary messages should pass None.
    update_memory_context(memory_context)

    # Save user message.
    messages.append({
        "role": "user",
        "content": user_input
    })

    tools = [
        tool["schema"]
        for tool in TOOL_REGISTRY.values()
    ]

    response_text = ""

    # Allow multiple tool-call iterations.
    for _ in range(10):
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=tools,
            options=OPTIONS,
            keep_alive=KEEP_ALIVE,
            think=False
        )
        assistant_message = response.message

        # -------------------------------------------------
        # FINAL ASSISTANT RESPONSE
        # -------------------------------------------------
        if not assistant_message.tool_calls:
            response_text = assistant_message.content or ""
            messages.append({
                "role": "assistant",
                "content": response_text
            })

            break

        # -------------------------------------------------
        # ASSISTANT TOOL CALLS
        # -------------------------------------------------

        # Convert Ollama SDK message into a dictionary.
        assistant_dict = assistant_message.model_dump(
            exclude_none=True
        )
        messages.append(assistant_dict)

        for tool_call in assistant_message.tool_calls:
            name = tool_call.function.name
            arguments = tool_call.function.arguments or {}

            try:
                result = execute_tool(name, arguments)

            except Exception as error:
                result = f"Tool execution failed: {error}"

            # Save tool result in conversation history.
            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": str(result)
            })

    else:
        response_text = "I couldn't complete that request."
        messages.append({
            "role": "assistant",
            "content": response_text
        })

    # -----------------------------------------------------
    # HISTORY MANAGEMENT
    # -----------------------------------------------------

    trim_history(max_exchanges=3)

    # -----------------------------------------------------
    # TERMINAL DISPLAY
    # -----------------------------------------------------

    display_conversation()

    # -----------------------------------------------------
    # TEXT TO SPEECH
    # -----------------------------------------------------

    if response_text and on_chunk:
        on_chunk(response_text)

    return response_text
