import os

from agents.mcp import MCPServerStdio

memory_server = MCPServerStdio(
    name="Memory",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory@2026.8.31"],
    },
    client_session_timeout_seconds=60,
)

search_server = MCPServerStdio(
    name="Brave Search",
    params={
        "command": "npx",
        "args": ["-y", "@brave/brave-search-mcp-server@2.1.4"],
        "env": {
            **os.environ,
            "BRAVE_API_KEY": os.environ["BRAVE_API_KEY"],
        },
    },
    client_session_timeout_seconds=60,
)
