import ollama

from llm import MODEL, OPTIONS, KEEP_ALIVE, SYSTEM_PROMPT
from agent.registry import TOOL_REGISTRY, execute_tool


def run_agent(user_input):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    tools = [
        tool["schema"]
        for tool in TOOL_REGISTRY.values()
    ]

    for _ in range(5):
        # In one loop tool call, in other loop returns response with tool result in history
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=tools,
            options=OPTIONS,
            keep_alive=KEEP_ALIVE,
            think=False
        )

        # No tool requested: return Mio's response
        if not response.message.tool_calls:
            return response.message.content or ""

        # Preserve the assistant's tool-call message
        messages.append(response.message)
        # print(response.message)

        for tool_call in response.message.tool_calls:

            name = tool_call.function.name
            print(name)
            arguments = tool_call.function.arguments or {}
            print(arguments)

            try:
                result = execute_tool(name, arguments) # To validate the tool
                print(f"Tool result: {result}")

            except ValueError as error:
                result = f"Tool rejected: {error}"
                print(result)

            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": str(result)
            })

    return "I couldn't complete that request."


if __name__ == "__main__":
    result = run_agent("open cmd")
    print("\n\nMio:", result)