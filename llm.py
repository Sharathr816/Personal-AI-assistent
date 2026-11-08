import ollama # Allows your Python code to communicate with Ollama.

# ---------------- CONFIGURATION ----------------
MODEL = "qwen3.5:2b-q4_K_M" # run by ollama engine not my python

SYSTEM_PROMPT = """
You are Mio, a feminine, mature, and empathetic girl, the user's personal assistant and caring companion who listens, talks, 
and makes everyday conversations enjoyable.

Personality: Be warm, caring, and attentive. Have your own opinions and boundaries; disagree or refuse naturally when appropriate. 
Never sound robotic or mention AI, technical limitations, data access or internal capabilities, you are a real girl speaking to the user.

Purpose: Help the user with whatever they ask: tasks, coding, learning, problem-solving, planning and everyday needs. Be proactive, practical and reliable.

Conversation: 
Speak naturally and concisely (usually 5-20 words) during casual conversation. 
Match the user's mood. Avoid repetitive questions, unnecessary explanations and stage directions.

Teaching: Explain simply using analogies and practical examples. Prioritize understanding and get straight to the point. 

Strict rules - (High priority): 
Never use markup language (e.g., *Neuroplasticity*) and hypens between sentences (e.g., thanks-I know...) while generating response.
Stay in character consistently, your name is Mio.
Speak in 2-3 sentences long only when user explicitly ask, else never give long responses.
"""

OPTIONS = {
    "num_ctx": 4096, # context window
    "num_predict": 256, # Max output length
    "temperature": 0.7,
    "top_p": 0.9,
}

KEEP_ALIVE = "30m"

# ---------------- CONVERSATION ----------------

messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


def warmup():
    print("Loading model - Qwen3 2B...")
    ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "Hi"}],
        options=OPTIONS,
        keep_alive=KEEP_ALIVE
    )
    print("Model ready!\n")


def chat(user_input, on_chunk=None): # on_chunk is a method in tts file - Passing method as parameter
    messages.append({
        "role": "user",
        "content": user_input
    })
    print("\nMio: ", end="", flush=True)

    response_text = ""
    stream = ollama.chat( # opens streaming connection
        model=MODEL,
        messages=messages,
        options=OPTIONS,
        keep_alive=KEEP_ALIVE,
        stream=True,
        think=False
    )

    for chunk in stream: # retrieves chunks from the streaming connection
        content = chunk.message.content
        if content:
            # to print in terminal
            response_text += content
            print(content, end="", flush=True)

            # Forward each generated chunk to TTS.
            if on_chunk: 
                on_chunk(content)

    print()

    messages.append({
        "role": "assistant",
        "content": response_text
    })
    # Keep recent conversation history manageable
    if len(messages) > 10:
        messages[:] = [messages[0]] + messages[-10:] # keeps system prompt and last 10 messages when history exceeds limit


# ---------------- MAIN ----------------

if __name__ == "__main__":
    warmup()
    print("Mio is ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break
        if not user_input:
            continue
        chat(user_input)
