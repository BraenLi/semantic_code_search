"""Semantic Code Search MCP Server."""

import asyncio
import sys
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from semantic_mcp.config import Config
from semantic_mcp.services.indexer import Indexer
from semantic_mcp.services.search import SearchService
from semantic_mcp.services.watcher import WatcherService


# Create server instance
app = Server("semantic-code-search")

# Global services
config: Config | None = None
indexer: Indexer | None = None
search_service: SearchService | None = None
watcher: WatcherService | None = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="semantic_code_search",
            description="Search code using natural language queries. Finds relevant functions, classes, and code snippets based on semantic meaning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of what code to find (e.g., 'function that handles user authentication')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                    "language": {
                        "type": "string",
                        "description": "Filter by language (python, c, cpp)",
                        "enum": ["python", "c", "cpp"],
                    },
                    "node_type": {
                        "type": "string",
                        "description": "Filter by code element type",
                        "enum": ["function", "class", "method", "struct"],
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="index_codebase",
            description="Index or re-index the target codebase. This is automatically done on startup but can be called manually to force a refresh.",
            inputSchema={
                "type": "object",
                "properties": {
                    "full": {
                        "type": "boolean",
                        "description": "Perform full re-index instead of incremental",
                        "default": False,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocation."""
    global indexer, search_service

    if name == "semantic_code_search":
        if not search_service:
            return [TextContent(
                type="text",
                text="Error: Search service not initialized. Run index_codebase first.",
            )]

        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        language = arguments.get("language")
        node_type = arguments.get("node_type")

        if not query:
            return [TextContent(
                type="text",
                text="Error: 'query' argument is required",
            )]

        # Perform search
        results = await search_service.search(
            query=query,
            limit=limit,
            language=language,
            node_type=node_type,
        )

        # Format results
        if not results:
            return [TextContent(
                type="text",
                text="No results found for your query.",
            )]

        output = f"Found {len(results)} results:\n\n"
        code_limit = config.result_code_limit if config else 500
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['file']}:{result['start_line']}-{result['end_line']}\n"
            output += f"   {result['type']}: {result['name']}\n"
            output += f"   Score: {result['score']:.2f}\n"
            output += f"   {result['description']}\n"
            # Only truncate if code is longer than limit
            code = result.get('code', '')
            if code and len(code) > code_limit:
                output += f"   ```{result['language']}\n{code[:code_limit]}...\n```\n\n"
            elif code:
                output += f"   ```{result['language']}\n{code}\n```\n\n"
            else:
                output += f"   ```{result['language']}\n<code not available>\n```\n\n"

        return [TextContent(type="text", text=output)]

    elif name == "index_codebase":
        if not indexer:
            return [TextContent(
                type="text",
                text="Error: Indexer not initialized",
            )]

        full = arguments.get("full", False)

        if full:
            # Clear and re-index
            stats = await indexer.index_all()
        else:
            # Incremental (for now, just do full)
            stats = await indexer.index_all()

        return [TextContent(
            type="text",
            text=f"Indexing complete. Indexed {stats['indexed']} files, {stats['errors']} errors.",
        )]

    return [TextContent(
        type="text",
        text=f"Unknown tool: {name}",
    )]


async def initialize_services():
    """Initialize all services."""
    global config, indexer, search_service, watcher

    config = Config.from_env()

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    # Initialize services
    indexer = Indexer(config)
    search_service = SearchService(config)

    # Perform initial indexing
    print("Indexing codebase...", file=sys.stderr)
    stats = await indexer.index_all()
    print(f"Indexed {stats['indexed']} files", file=sys.stderr)

    # Start file watcher
    watcher = WatcherService(config, indexer)
    watcher.start()
    print("File watcher started", file=sys.stderr)


async def main():
    """Main entry point."""
    await initialize_services()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def run():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
