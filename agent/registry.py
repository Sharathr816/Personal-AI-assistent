from datetime import datetime
from pydantic import BaseModel, ConfigDict, ValidationError, Field

from agent.note_tools import (
    WriteNoteArgs,
    write_note,
    open_note,
    OpenNoteArgs
)

from agent.browser_tools import (
    connect_brave,
    get_brave_status,
    search_youtube,
    play_youtube_video
)

from agent.application_tools import (
    search_applications,
    open_application
)


TOOL_REGISTRY = {}

# argument schema for tools that don't require arguments.It ensures Qwen cannot pass unexpected arguments like {"location": "Bengaluru"} to that tool
class NoArguments(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True
    )

# For you tube search and play
class SearchYouTubeArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    query: str = Field(min_length=1, max_length=300)
    max_results: int = Field(default=5, ge=1, le=10)


class PlayYouTubeVideoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    video_url: str = Field(min_length=1, max_length=2048)

class SearchApplicationsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=1, max_length=100)
    max_results: int = Field(default=30, ge=1, le=100)


class OpenApplicationArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    shortcut_path: str = Field(min_length=1, max_length=2048)
    exe_path: str | None = Field(default=None, max_length=2048)

def register_tool(name, description, args_model, function):
    TOOL_REGISTRY[name] = {
        "function": function,
        "args_model": args_model,
        "schema": {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": args_model.model_json_schema()
            }
        }
    }

# Tool validater
def execute_tool(name, arguments):
    # Reject unknown tools
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {name}")

    tool = TOOL_REGISTRY[name]

    # Validate arguments before execution - If valid, it returns a validated Pydantic object. If invalid, it raises ValidationError
    try:
        validated_args = tool["args_model"].model_validate(
            arguments,
            strict=True
        )
    except ValidationError as error:
        raise ValueError(f"Invalid tool arguments: {error}")

    # Execute only after successful validation
    return tool["function"](**validated_args.model_dump()) # Converts the validated arguments into a dictionary and passes them to the Python function.



# Tools and tools register
def get_current_time():
    return datetime.now().strftime(
        "%A, %d %B %Y, %I:%M %p"
    )


# Register first tool
register_tool(
    name="get_current_time",
    description="Get the current date and time.",
    args_model=NoArguments,
    function=get_current_time
)

# Register notes tool
register_tool(
    name="write_note",
    description=(
        "Save text content as a UTF-8 text file in the notes directory. "
        "Use this when the user asks to save or write a note."
    ),
    args_model=WriteNoteArgs,
    function=write_note
)
register_tool(
    name="open_note",
    description=(
        "Open an existing saved note in Windows Notepad. "
        "Provide the note filename or its path inside the notes directory."
    ),
    args_model=OpenNoteArgs,
    function=open_note
)

# Brave connection
register_tool(
    name="connect_brave",
    description=(
        "Launch Mio's dedicated Brave browser profile and connect "
        "Playwright to it. Use this before performing browser actions."
    ),
    args_model=NoArguments,
    function=connect_brave
)
register_tool(
    name="get_brave_status",
    description="Check whether Mio is connected to Brave and report its open tab count."
                "If not connected, connect using connect_brave",
    args_model=NoArguments,
    function=get_brave_status
)

# You tube
register_tool(
    name="search_youtube",
    description=(
        "Search YouTube for videos matching the user's request. "
        "Returns video titles, channel names and URLs. "
        "Use the results to select the most relevant video."
    ),
    args_model=SearchYouTubeArgs,
    function=search_youtube
)
register_tool(
    name="play_youtube_video",
    description=(
        "Open a selected YouTube video URL in Mio's Brave browser "
        "and attempt to start playback. Use a URL returned by "
        "search_youtube."
    ),
    args_model=PlayYouTubeVideoArgs,
    function=play_youtube_video
)

# Application management
register_tool(
    name="search_applications",
    description=(
        "Search Windows application shortcuts by their prefix letter. "
        "Use this when the user asks to find or open an installed application. "
        "Returns application names and shortcut paths."
    ),
    args_model=SearchApplicationsArgs,
    function=search_applications
)

register_tool(
    name="open_application",
    description=(
        "Launch an application using its Windows shortcut path. "
        "Use a shortcut path returned by search_applications."
    ),
    args_model=OpenApplicationArgs,
    function=open_application
)