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

Now, voice.py interacts with conversation manager instead of directly with llm, convo manager interact with llm now (Memory_context parameter added).

Currently i am feeding mio wple request_message of size 10 [{role:..., content:...}...], mio reads and rembers only this. This is the context window having system, user prompt + Mio's response + memory contents(upto 20). No semantic search for now

while implementing forget functionality in keyword detection period(.) was also taken hence counldn't able to delete multiple entries.

Done with memory (semantic search - chroma db is not implemented).

Done with managing context window by making num_ctx = 8192 and num_predict(output) to 512, working fine.


10/11/26
Started with agentic capabilities for MIO.
Decided the following capabilities...
    - Use brave to open and play u tube videos
    - Notepad to write long responses.
    - Access to my X:/ drive to perform file operation with permissions for modification and deletion.
    - Access to processes to open and close applications i say.
Only using python, no agentic frameworks - Mio decides, ops are purely done by python programs called by mio.

### Note: Sometimes llm itself fails in calling tools and passing correct arguments (Encountered file not found when opening even though it existed), the frequency drastically reduces when i use more intelligent models.

Regiter tools in agent/register.py.
orchestrator.py the bridge between Qwen and your Python tools.
Updated system prompt to avail tool usages.
Qwen3.5 sometimes calls tool and sometimes dosen't, started searching for new llm,
upgraded to granite4.1:3b and tool call is working..

Checking tool validation:
First checked for fake tools - success.
Checked for no arguments tools(class Noarguments) - success.
checked for tools having arguments (Class Testargs) - Success. 

Registered notes tool:
makes a notes directory if not exists.
create a file with title and dumps contents into it.
tool result is just "Notes saves successfully" hence no context tokens wastage.
tested for title sanitization and conflicts, tested on tool validation as well.
Implemented opening notepad tool, successfully opnes it when asked in natural language.

Scraped file tools as i couldn't find any use case.

You tube through brave browser.
Playwright's Python API supports attaching to Chromium-based browsers such as Brave through connect_over_cdp().(CDP belongs to the browser)
Made cdp endpoint available and connected to it using playwright.
you tube playback feature done...
    - connect to brave (If playwright connection is already up then it is brave, uses this to play else new connection)
    - llm passes search query to search tool.
    - search tool first gets you tube page or uses existing opened you tube tab.
    - on next run picks the best result from search output wrt to mu query and plays it.

Started application opening tool.
can't open apps other than .lnk.
System prompt is not proper and confusing the llm.
sometimes apps are opened and sometimes I get tool rejected.
Some times even when tool is called successfully Mio responds "Couldn't open"

11/11/26
System prompt corrected, open application works, performance can be increased by using more intelligent llm.

Started closing applications:
There are two ways to close applications:
    - Graceful close: Ask the application to close normally, allowing it to save data.
    - Force termination: Kill the process immediately, potentially losing unsaved work.
For now using only gracefull close.
Not implementing list + close of background processes.
Some limitations:
    Some packaged Windows apps have windows owned by a separate hosting process. Our executable matching can miss them.
    Two separate Brave instances using the same executable could be grouped together. Closing by executable path may close windows from both.
    Our current verification checks whether windows disappear, not whether all application processes terminate.

Final touches to the agentic capabiltiy
Optimized conversation history to the model to hold 3 user-assistent exchanges, this also include complete tool calls in that exchange.
Made memory fixed in messages[1], updating at satrt and when remebering and forgetting.
Record exchange when remebering or forgetting something, as these branch don't call run_agent (Conversation_manager.py)

## Note - Stuffs to implement to complete MVP:
 - Implement semantic search.
 - Reduce speech latency, currently takes 3-4 seconds.
 - Optimize whisper, so that it can properly transcribe.