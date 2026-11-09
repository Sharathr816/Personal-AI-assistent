## All challenges and how I overcame

8/11/26
Added mio to github using git commands so that I can access her and keep  track of versions in case my laptop busts.
Came up with complete memory architecture for mio present in chatgpt.

9/11/26
created MVP memory architecture.
created files:
memory.py - memory operations.
Conversation_manager.py - logic on how/when to use memory (The logical brain)
mio_memory.db - sqlite database

The current architecture changed where instead sending transcription directly to llm, transcription is processed to build memory/context(Conversation_manager.py) and then sent to llm.

Now, voice.py interacts with conversation manager instead of directly with llm, convo manager interact with llm now.

Currently i am feeding mio wple request_message of size 10 [{role:..., content:...}...], mio reads and rembers only this. This is the context window having system, user prompt + Mio's response + memory contents(upto 20). No semantic search for now

while implementing forget functionality in keyword detection period(.) was also taken hence counldn't able to delete multiple entries