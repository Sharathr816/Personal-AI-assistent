# import ollama

# from llm import MODEL, OPTIONS, KEEP_ALIVE
# from agent.registry import TOOL_REGISTRY

# tools = [
#     tool["schema"]
#     for tool in TOOL_REGISTRY.values()
# ]

# response = ollama.chat(
#     model=MODEL,
#     messages=[
#         {
#             "role": "system",
#             "content": "You must call get_current_time to answer the user's question. Never guess the time."
#         },
#         {
#             "role": "user",
#             "content": "Call get_current_time and tell me the current time."
#         }
#     ],
#     tools=tools,
#     options=OPTIONS,
#     keep_alive=KEEP_ALIVE,
#     think=False
# )

# print("\n--- RAW RESPONSE ---")
# print(response.message)

# print("\n--- TOOL CALLS ---")
# print(response.message.tool_calls)

# if response.message.tool_calls:
#     for call in response.message.tool_calls:
#         print("\nTool name:", call.function.name)
#         print("Arguments:", call.function.arguments)
# else:
#     print("\nQwen did not request any tools.")
#     print("Response:", response.message.content)


# Validation testing

# from pydantic import BaseModel, ConfigDict

# from agent.registry import register_tool, execute_tool


# # Define expected arguments
# class TestArgs(BaseModel):
#     model_config = ConfigDict(extra="forbid", strict=True)

#     name: str
#     count: int


# # Dummy function
# def test_function(name, count):
#     return f"Received {name}, count = {count}"


# Register tool testing
# register_tool(
#     name="test_tool",
#     description="Temporary tool for testing argument validation.",
#     args_model=TestArgs,
#     function=test_function
# )


# # Test cases
# tests = [
#     ("Valid arguments", "test_tool", {"name": "Mio", "count": 5}),
#     ("Missing argument", "test_tool", {"name": "Mio"}),
#     ("Wrong type", "test_tool", {"name": "Mio", "count": "5"}),
#     ("Unexpected argument", "test_tool", {
#         "name": "Mio", "count": 5, "extra": True
#     }),
#     ("Unknown tool", "fake_tool", {})
# ]


# for description, tool_name, arguments in tests:
#     print(f"\n--- {description} ---")

#     try:
#         result = execute_tool(tool_name, arguments)
#         print("ACCEPTED:", result)

#     except ValueError as error:
#         print("REJECTED:", error)

# Write notes tool testing
# from agent.registry import execute_tool

# # Test 1: Save a note
# result = execute_tool(
#     "write_note",
#     {
#         "title": "Mio Test Note",
#         "content": "This is a test note.\nMio can save long responses here."
#     }
# )

# print("\nTest 1:", result)


# # Test 2: Save another note with the same title
# result = execute_tool(
#     "write_note",
#     {
#         "title": "Mio Test Note",
#         "content": "This should create a second file."
#     }
# )

# print("\nTest 2:", result)


# # Test 3: Invalid arguments
# try:
#     execute_tool(
#         "write_note",
#         {"title": "Invalid Note"}
#     )
# except ValueError as error:
#     print("\nTest 3: Rejected correctly:", error)


# # Test 4: Invalid filename characters
# result = execute_tool(
#     "write_note",
#     {
#         "title": "Test/Unsafe:Title",
#         "content": "Filename sanitization test."
#     }
# )

# print("\nTest 4:", result)


# Notepad opening tool test
# from agent.registry import execute_tool

# # Test 1: Open an existing note
# try:
#     result = execute_tool(
#         "open_note",
#         {"path": "Agentic Systems Overview_1.txt"}
#     )
#     print("Test 1:", result)

# except Exception as error:
#     print("Test 1 FAILED:", error)


# # Test 2: Reject nonexistent note
# try:
#     execute_tool(
#         "open_note",
#         {"path": "does_not_exist.txt"}
#     )
# except FileNotFoundError as error:
#     print("\nTest 2 PASSED:", error)


# # Test 3: Reject directory traversal
# try:
#     execute_tool(
#         "open_note",
#         {"path": "../../some_file.txt"}
#     )
# except ValueError as error:
#     print("\nTest 3 PASSED:", error)


# # Test 4: Reject missing arguments
# try:
#     execute_tool("open_note", {})
# except ValueError as error:
#     print("\nTest 4 PASSED:", error)

# Broweser tool testing
# from agent.registry import execute_tool


# # Test 1: Launch Brave and connect Playwright.
# try:
#     result = execute_tool("connect_brave", {})
#     print("Test 1 PASSED:", result)
# except Exception as error:
#     print("Test 1 FAILED:", repr(error))
#     raise


# # Test 2: Check the browser connection.
# try:
#     result = execute_tool("get_brave_status", {})
#     print("\nTest 2 PASSED:")
#     print(result)

#     assert "connected successfully" in result.lower()

# except Exception as error:
#     print("\nTest 2 FAILED:", repr(error))
#     raise


# # Test 3: Verify that the connection is reused.
# try:
#     result = execute_tool("connect_brave", {})
#     assert "already connected" in result.lower()

#     print("\nTest 3 PASSED: Existing connection reused.")

# except Exception as error:
#     print("\nTest 3 FAILED:", repr(error))
#     raise


# You tube search testing
# from agent.registry import execute_tool

# # Test 1: Search YouTube.
# try:
#     result = execute_tool(
#         "search_youtube",
#         {
#             "query": "lofi hip hop radio",
#             "max_results": 5
#         }
#     )

#     print("SEARCH RESULTS:")
#     print(result)

#     assert "YouTube results" in result or "No YouTube" in result

# except Exception as error:
#     print("SEARCH TEST FAILED:", repr(error))
#     raise

# from agent.registry import execute_tool


# # Test 1: Empty search query
# try:
#     execute_tool("search_youtube", {"query": ""})
#     print("FAILED: Empty query was accepted")
# except ValueError:
#     print("PASSED: Empty query rejected")


# # Test 2: Invalid result limit
# try:
#     execute_tool(
#         "search_youtube",
#         {"query": "lofi", "max_results": 500}
#     )
#     print("FAILED: Invalid result limit was accepted")
# except ValueError:
#     print("PASSED: Invalid result limit rejected")


# # Test 3: Wrong argument type
# try:
#     execute_tool(
#         "search_youtube",
#         {"query": "lofi", "max_results": "5"}
#     )
#     print("FAILED: Wrong argument type was accepted")
# except ValueError:
#     print("PASSED: Wrong argument type rejected")



# Application opening testings

from agent.application_tools import (
    search_applications,
    open_application,
)

# First, discover shortcuts beginning with S.
# print(search_applications("s"))

# Then test launching using a path returned by the search.

print(open_application(r"C:\Users\Public\Desktop\Steam.lnk"))