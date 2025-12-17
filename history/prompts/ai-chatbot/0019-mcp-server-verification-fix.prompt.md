---
id: 0019
title: Verify and Fix MCP Server Implementation
stage: green
date: 2025-12-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: ai-chatbot
branch: phase-3
user: Hamza123545
command: /sp.clarify
labels: ["mcp-server", "fastmcp", "openai-agents-sdk", "mcp-tools", "stdio-transport"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - phase-3/backend/mcp/tools.py
  - phase-3/backend/mcp/__main__.py
  - phase-3/backend/agent_config/todo_agent.py
  - phase-3/backend/routers/chat.py
tests:
  - none
---

## Prompt

read the backend files of phase-3 backend and verify the mcp tool code as it wrong using the function_tool but it should use the proper mcp server for exaple "✅ Minimal MCP Tool + Server Syntax (correct)
server.py — MCP tool server
from mcp.server import Server
from mcp.tools import tool

# Create MCP server instance
server = Server(name="db-tools")

# MCP Tool: create a database table
@tool
def create_table(
    table_name: str,
    columns: str,
) -> dict:
    """
    MCP Tool Contract:
    - Purpose: Create a database table dynamically
    - Input:
        table_name: name of table to create
        columns: SQL column definitions, e.g. "id INT PRIMARY KEY, name TEXT"
    - Returns: JSON response
    """
    # Normally you execute SQL here
    # For demo just return confirmation
    return {
        "status": "created",
        "table": table_name,
        "columns": columns
    }

if __name__ == "__main__":
    server.run()

🧠 Why this is MCP syntax

Because it has the three required MCP components:

Required MCP Concept    Exists?    Example
MCP Server    ✔️    server = Server(...)
MCP Tool registration    ✔️    @tool decorator
Starts a process using MCP transport    ✔️    server.run()

There is no Agents SDK dependency here.
This script is standalone MCP server.

🚀 Now the Agent connects to MCP server

Agents SDK side:

from agents import Agent
from agents.mcp import MCPServerStdio

# launch MCP server
mcp_server = MCPServerStdio(
    name="db-tools",
    params={"command": "python", "args": ["server.py"]}
)

agent = Agent(
    name="DB Agent",
    instructions="You may call MCP tools to manage database tables.",
    mcp_servers=[mcp_server]
)

# example agent query
resp = agent.run("Create table students with id and name")
print(resp.output_text)

💡 Your previous code used:
@function_tool  # ❌ not MCP


Because that executes functions inside the agent.

MCP version uses:

@tool  # ✔️ MCP tool exposed via JSON-RPC

🧩 How to convert your existing tools

Wherever you had:

@function_tool
def add_task(...):


Convert to:

@tool
def add_task(...):


and move into MCP server context:

server = Server("task-tools")


Then run server.

🧱 Minimal conversion " use the context 7 mcp server for the latest syntax and uses of mcp server with open ai agent sdk refference files need to clarify first @phase-3\backend\ for thhe current code

## Response snapshot

Analyzed the Phase 3 backend MCP implementation and identified critical issues. The code was using `@function_tool` from OpenAI Agents SDK instead of proper MCP server patterns. Successfully converted to FastMCP architecture with:

1. **MCP Server (tools.py)**: Replaced `@function_tool` with `@mcp.tool()` decorator using FastMCP
2. **Server Entry Point (__main__.py)**: Created module entry point for `python -m mcp.tools`
3. **Agent Configuration (todo_agent.py)**: Replaced direct tool imports with MCPServerStdio subprocess launcher
4. **Chat Router (chat.py)**: Added async context manager to properly start/stop MCP server

All 5 tools (add_task, list_tasks, complete_task, delete_task, update_task) now run in a separate MCP server process connected via stdio transport, matching official MCP SDK patterns.

## Outcome

- ✅ Impact: Corrected MCP server implementation to match official MCP SDK specification. Tools now run as a proper MCP server process instead of in-agent functions.
- 🧪 Tests: No automated tests run (manual verification against Context7 documentation and official MCP Python SDK patterns)
- 📁 Files: 4 files modified (mcp/tools.py, mcp/__main__.py, agent_config/todo_agent.py, routers/chat.py)
- 🔁 Next prompts: Test the MCP server by running the chat endpoint and verifying tools execute correctly; Add error handling for MCP server startup failures
- 🧠 Reflection: The distinction between `@function_tool` (agent-internal) and `@mcp.tool()` (separate MCP server) is critical. FastMCP provides the recommended high-level API for MCP server creation.

## Evaluation notes (flywheel)

- Failure modes observed: None - Successfully retrieved Context7 MCP SDK documentation, identified incorrect pattern (@function_tool vs @mcp.tool), and implemented correct architecture with FastMCP and MCPServerStdio
- Graders run and results (PASS/FAIL): Manual verification PASS - Implementation matches all required MCP components (server instance, tool registration, stdio transport, async context management)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add comprehensive error handling in chat router for MCP server connection failures; implement health check endpoint to verify MCP server connectivity
