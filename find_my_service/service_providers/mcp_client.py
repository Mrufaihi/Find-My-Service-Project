from pydantic_ai import RunContext, Tool as PydanticTool
from pydantic_ai.tools import ToolDefinition
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPTool
from contextlib import AsyncExitStack
from typing import Any, List
import asyncio
import logging
import shutil
import json
import os
import sys
import pathlib
import traceback

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

class MCPClient:
    """Manages connections to one or more MCP servers based on mcp_config.json"""

    def __init__(self) -> None:
        self.servers: List[MCPServer] = []
        self.config: dict[str, Any] = {}
        self.tools: List[Any] = []
        self.exit_stack = AsyncExitStack()

    def load_servers(self, config_path: str) -> None:
        """Load server configuration from a JSON file (typically mcp_config.json)
        and creates an instance of each server.
        """
        with open(config_path, "r") as config_file:
            self.config = json.load(config_file)
        self.servers = [MCPServer(name, config) for name, config in self.config["mcpServers"].items()]

    async def start(self) -> List[PydanticTool]:
        """Start each MCP server and return the tools formatted for Pydantic AI."""
        self.tools = []
        for server in self.servers:
            try:
                logging.debug(f"Initializing server: {server.name}")
                await server.initialize()
                logging.debug(f"Creating pydantic tools for server: {server.name}")
                tools = await server.create_pydantic_ai_tools()
                logging.debug(f"Found {len(tools)} tools in server: {server.name}")
                for tool in tools:
                    logging.debug(f"  - {tool.name}")
                self.tools += tools
            except Exception as e:
                logging.error(f"Failed to initialize server {server.name}: {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                try:
                    await server.cleanup()
                except Exception as cleanup_error:
                    logging.error(f"Error cleaning up failed server {server.name}: {cleanup_error}")

        if not self.tools:
            logging.warning("No tools were found from any servers")
            
        return self.tools

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in self.servers:
            try:
                await server.cleanup()
            except (asyncio.CancelledError, Exception) as e:
                logging.warning(f"Warning during cleanup of server {server.name}: {e}")

    async def cleanup(self) -> None:
        """Clean up all resources including the exit stack."""
        try:
            await self.cleanup_servers()
            try:
                # Check if the event loop is still running
                try:
                    current_loop = asyncio.get_running_loop()
                    # Only close the exit stack if we're in a valid event loop
                    await self.exit_stack.aclose()
                except RuntimeError:
                    # No running event loop or loop is closed
                    logging.warning("Could not access event loop during cleanup")
            except Exception as e:
                logging.warning(f"Warning while closing exit stack: {e}")
        except Exception as e:
            logging.warning(f"Warning during final cleanup: {e}")


class MCPServer:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: dict[str, Any]) -> None: 
        self.name: str = name
        self.config: dict[str, Any] = config
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize(self) -> None:
        """Initialize the server connection."""
        command = (
            shutil.which("npx")
            if self.config["command"] == "npx"
            else self.config["command"]
        )
        if command is None:
            raise ValueError(f"The command '{self.config['command']}' could not be found in PATH.")
        
        server_params = StdioServerParameters(
            command=command,
            args=self.config["args"],
            env=self.config["env"] if self.config.get("env") else None,
        )
        try:
            logging.debug(f"Starting MCP server: {self.name} with command: {command} {' '.join(self.config['args'])}")
            
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            
            logging.debug(f"Server {self.name} stdio connection established, creating session")
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            logging.debug(f"Initializing session for server: {self.name}")
            await session.initialize()
            self.session = session
            logging.debug(f"Server {self.name} initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def create_pydantic_ai_tools(self) -> List[PydanticTool]:
        """Convert MCP tools to pydantic_ai Tools."""
        try:
            tools = (await self.session.list_tools()).tools
            return [self.create_tool_instance(tool) for tool in tools]
        except Exception as e:
            logging.error(f"Error listing tools for server {self.name}: {e}")
            return []

    def create_tool_instance(self, tool: MCPTool) -> PydanticTool:
        """Initialize a Pydantic AI Tool from an MCP Tool."""
        async def execute_tool(**kwargs: Any) -> Any:
            return await self.session.call_tool(tool.name, arguments=kwargs)

        async def prepare_tool(ctx: RunContext, tool_def: ToolDefinition) -> ToolDefinition | None:
            # Clean up schema for pydantic-ai
            input_schema = tool.inputSchema.copy()
            
            if 'type' not in input_schema:
                input_schema['type'] = 'object'
                
            if '$schema' in input_schema:
                del input_schema['$schema']
                
            if 'properties' in input_schema:
                for prop in input_schema['properties'].values():
                    if isinstance(prop, dict) and '$schema' in prop:
                        del prop['$schema']
            
            tool_def.parameters_json_schema = input_schema
            return tool_def
            
        return PydanticTool(
            execute_tool,
            name=tool.name,
            description=tool.description or "",
            takes_ctx=False,
            prepare=prepare_tool
        )

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                try:
                    # Check if the event loop is still running
                    try:
                        current_loop = asyncio.get_running_loop()
                        # Only close the exit stack if we're in a valid event loop
                        await self.exit_stack.aclose()
                    except RuntimeError:
                        # No running event loop or loop is closed
                        logging.warning(f"Could not access event loop during cleanup of server {self.name}")
                except Exception as e:
                    logging.warning(f"Warning while closing exit stack for server {self.name}: {e}")
                self.session = None
                self.stdio_context = None
            except Exception as e:
                logging.error(f"Error during cleanup of server {self.name}: {e}") 