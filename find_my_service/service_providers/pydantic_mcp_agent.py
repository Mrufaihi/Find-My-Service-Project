import asyncio
import os
import pathlib
import sys
import traceback
import logging
import nest_asyncio

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Apply nest_asyncio to allow nested event loops
try:
    nest_asyncio.apply()
    logging.info("Applied nest_asyncio to allow nested event loops")
except Exception as e:
    logging.warning(f"Failed to apply nest_asyncio: {e}")

# Import additional required packages
try:
    from pydantic_ai import Agent
    from pydantic_ai.models.gemini import GeminiModel
    from pydantic_ai.providers.google_gla import GoogleGLAProvider
    logging.info("Successfully imported pydantic_ai modules")
except ImportError as e:
    logging.error(f"Error importing pydantic_ai: {e}")
    logging.error("Required packages not found. Please install with:")
    logging.error("pip install pydantic-ai python-dotenv nest-asyncio")
    sys.exit(1)

# Import the MCPClient
MCPClient = None
try:
    from .mcp_client import MCPClient
    logging.info("Successfully imported MCPClient")
except (ImportError, ValueError) as e:
    logging.error(f"MCPClient import failed: {e}")
    logging.error("Warning: MCP client not found. Tools will not be available.")

# Get app directory
CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
BASE_DIR = CURRENT_DIR.parent

# Define path to config file
CONFIG_FILE = os.path.join(BASE_DIR, "find_my_service", "mcp_config.json")

# Fallback to project root if file doesn't exist
if not os.path.exists(CONFIG_FILE):
    CONFIG_FILE = os.path.join(BASE_DIR, "mcp_config.json")
    
logging.info(f"CONFIG_FILE path: {CONFIG_FILE}")
logging.info(f"CONFIG_FILE exists: {os.path.exists(CONFIG_FILE)}")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv not installed, continuing without loading .env")

def get_model():
    """Get the appropriate LLM model for the agent."""
    # Get API key from environment
    api_key = os.getenv('LLM_API_KEY') or os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        logging.error("No API key found for the AI model! MCP search will not work.")
        raise ValueError("Missing API key for LLM model. Set LLM_API_KEY or GEMINI_API_KEY in .env file.")
    
    # Use a real model with API key
    model_name = os.getenv('MODEL_CHOICE', 'gemini-2.0-flash')
    
    # Create model with explicit API key
    model = GeminiModel(
        model_name,
        provider=GoogleGLAProvider(api_key=api_key)
    )
    return model

async def verify_mcp_setup():
    """Verify MCP setup and requirements"""
    issues = []
    
    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):
        issues.append(f"Config file not found: {CONFIG_FILE}")
    
    # Check MCPClient import
    if MCPClient is None:
        issues.append("MCPClient module could not be imported")
    
    # Check required packages
    try:
        import mcp
    except ImportError:
        issues.append("MCP package not installed. Run: pip install modelcontextprotocol")
    
    return issues

async def get_pydantic_ai_agent():
    """
    Create and return a Pydantic AI agent with MCP tools.
    This function is used by API endpoints to get an agent instance.
    """
    # Prepare the system prompt
    system_prompt = """You are a service provider finder powered by real-time search tools.
    When users ask about services, ALWAYS use your search tools to find real options.
    Never say you cannot search or access real-time information.
    When someone asks about a service:
    1. Use 'brave_web_search' to find real service providers for the query
    2. Use 'google_maps' or equivalent tools to get location-specific information
    3. Return specific provider names, their ratings and reviews found
    You must respond with real results found from your tools."""
    
    try:
        # Create a basic agent with tool use enforced
        agent = Agent(
            model=get_model(),
            system_prompt=system_prompt,
        )
        
        # Force tool usage mode to auto
        agent.tool_choice = "auto"
    except ValueError as e:
        logging.error(f"Failed to create agent: {e}")
        return None, None
    
    # Check MCP setup
    setup_issues = await verify_mcp_setup()
    if setup_issues:
        for issue in setup_issues:
            logging.error(f"MCP setup issue: {issue}")
        
        logging.error("MCP is required but has setup issues")
        return None, agent
    
    # Return early if MCPClient is not available
    if MCPClient is None:
        logging.warning("Using AI agent without MCP tools (MCPClient is None)")
        return None, agent
    
    client = None
    try:
        # Initialize MCP client with tools from config
        logging.info("Creating MCPClient instance...")
        client = MCPClient()
        
        logging.info("Loading servers from config...")
        client.load_servers(str(CONFIG_FILE))
        
        try:
            logging.info("Starting MCP client and loading tools...")
            
            # Ensure we're using the current event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Start the client with timeout
            tools = await asyncio.wait_for(client.start(), timeout=30.0)
            logging.info(f"Client started successfully, found {len(tools)} tools")
            
            if not tools:
                logging.warning("No tools were found by the MCP client!")
                return client, agent
            else:
                # Clean tool schemas
                logging.info("Cleaning tool schemas...")
                for tool in tools:
                    if hasattr(tool, 'parameters') and isinstance(tool.parameters, dict):
                        if '$schema' in tool.parameters:
                            del tool.parameters['$schema']
                        # Clean nested properties
                        if 'properties' in tool.parameters:
                            for prop in tool.parameters['properties'].values():
                                if isinstance(prop, dict) and '$schema' in prop:
                                    del prop['$schema']
                        
                        # Ensure proper schema format
                        if not tool.parameters.get('type'):
                            tool.parameters['type'] = 'object'
                
                # Log available tools
                tool_names = []
                for tool in tools:
                    tool_name = getattr(tool, 'name', 'unknown')
                    logging.info(f"Tool available: {tool_name}")
                    tool_names.append(tool_name)
                
                # Create new agent with combined system prompt and tools
                tool_instruction = f"\n\nAvailable tools: {', '.join(tool_names)}. Always use the relevant tool to search."
                # Make sure to explicitly assign tools to agent.tools as a property
                try:
                    new_agent = Agent(
                        model=get_model(),
                        system_prompt=system_prompt + tool_instruction,
                        tools=tools
                    )
                    # Ensure the tools are assigned as a property
                    if not hasattr(new_agent, 'tools'):
                        # Try setting tools as a property
                        new_agent.tools = tools
                    new_agent.tool_choice = "auto"
                    
                    # Verify tools exist
                    if hasattr(new_agent, 'tools'):
                        logging.info(f"Agent created with {len(new_agent.tools) if new_agent.tools else 0} tools")
                    else:
                        logging.warning("Agent was created but still has no tools attribute")
                    
                    return client, new_agent
                except Exception as e:
                    logging.error(f"Error creating agent with tools: {e}")
                    logging.error(traceback.format_exc())
                    return client, agent
                
        except asyncio.TimeoutError:
            logging.error("Timeout waiting for MCP client to start")
            return client, agent
        except Exception as e:
            logging.error(f"Error starting MCP client: {e}")
            logging.error(f"Stack trace: {traceback.format_exc()}")
            return client, agent
        
    except Exception as e:
        logging.error(f"Error initializing MCP client: {e}")
        logging.error(f"Stack trace: {traceback.format_exc()}")
        return None, agent

# Modified test function with proper event loop and cleanup handling
async def test_agent():
    """
    Simple test function to verify the agent is working correctly.
    """
    logging.info("======= TESTING AGENT =======")
    mcp_client = None
    
    try:
        # Get the agent
        mcp_client, agent = await get_pydantic_ai_agent()
        
        # Check if we have a valid agent
        if agent is None:
            logging.error("Agent is None")
            return
        
        # Print agent info
        if hasattr(agent, 'tools'):
            logging.info(f"Agent has tools")
            # Don't try to iterate over tools as it might not be iterable
        else:
            logging.warning("Agent has no tools attribute")
        
        # Test prompt
        test_prompt = "What is the weather like in New York?"
        logging.info(f"Testing agent with prompt: {test_prompt}")
        
        # Run the agent
        result = await agent.run(test_prompt)
        
        # Print the result
        response_text = ""
        if hasattr(result, 'data'):
            response_text = result.data
        elif hasattr(result, 'text'):
            response_text = result.text
        elif hasattr(result, 'content'):
            response_text = result.content
        elif hasattr(result, 'response'):
            response_text = result.response
        else:
            response_text = str(result)
        
        logging.info(f"Agent response: {response_text}")
        logging.info("======= TEST COMPLETE =======")
    except Exception as e:
        logging.error(f"Error testing agent: {str(e)}")
        logging.error(traceback.format_exc())
    finally:
        # Clean up
        if mcp_client:
            try:
                await mcp_client.cleanup()
                logging.info("MCP client cleaned up successfully")
            except Exception as e:
                logging.error(f"Error cleaning up MCP client: {e}")

# If this file is run directly, run the test
if __name__ == "__main__":
    asyncio.run(test_agent()) 