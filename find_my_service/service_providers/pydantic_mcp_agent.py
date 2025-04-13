from dotenv import load_dotenv
import asyncio
import pathlib
import sys
import os
import traceback
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Import additional required packages
try:
    from pydantic_ai import Agent
    from pydantic_ai.models.gemini import GeminiModel
    from pydantic_ai.providers.google_gla import GoogleGLAProvider
    logging.info("Successfully imported pydantic_ai modules")
except ImportError as e:
    logging.error(f"Error importing pydantic_ai: {e}")
    logging.error("Required packages not found. Please install with:")
    logging.error("pip install pydantic-ai python-dotenv")
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
logging.info(f"CONFIG_FILE path: {CONFIG_FILE}")
logging.info(f"CONFIG_FILE exists: {os.path.exists(CONFIG_FILE)}")

# Load environment variables
load_dotenv()

def get_model():
    """Get the appropriate LLM model for the agent."""
    # For testing, we can use a mock model if API key is not available
    api_key = os.getenv('LLM_API_KEY') or os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        logging.warning("No API key found for the AI model! Creating mock model.")
        # Create a simple mock model for testing
        from pydantic_ai.models.base import BaseModel
        
        class MockModel(BaseModel):
            def __init__(self):
                pass
                
            async def generate(self, *args, **kwargs):
                return {
                    "choices": [{
                        "message": {
                            "content": "This is a mock response. Please add a valid API key in .env file."
                        }
                    }]
                }
        
        return MockModel()
    
    # Use a real model if API key is available
    model_name = os.getenv('MODEL_CHOICE', 'gemini-1.5-flash')
    
    # Create model with explicit API key
    model = GeminiModel(
        model_name,
        provider=GoogleGLAProvider(api_key=api_key)
    )
    return model

async def get_pydantic_ai_agent():
    """
    Create and return a Pydantic AI agent with MCP tools.
    This function is used by API endpoints to get an agent instance.
    """
    # Create a basic agent even if MCP is not available
    agent = Agent(model=get_model())
    
    # Return early if MCPClient is not available
    if MCPClient is None:
        logging.warning("Using AI agent without MCP tools (MCPClient is None)")
        # Create a dummy tool for testing
        from pydantic_ai import Tool
        
        async def dummy_search(**kwargs):
            logging.info(f"Dummy search called with: {kwargs}")
            return [
                {"name": "Test Provider 1", "rating": 4.5, "mentions": 15},
                {"name": "Test Provider 2", "rating": 3.8, "mentions": 8}
            ]
        
        dummy_tool = Tool(
            dummy_search,
            name="dummy_search",
            description="A dummy search tool for testing",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "location": {"type": "string", "description": "Location to search"}
                }
            }
        )
        
        agent.tools = [dummy_tool]
        logging.info("Added dummy tool for testing")
        return None, agent
    
    client = None
    try:
        # Check if CONFIG_FILE exists before proceeding
        if not os.path.exists(CONFIG_FILE):
            logging.error(f"Config file not found: {CONFIG_FILE}")
            # Create a dummy tool since we can't load real ones
            return create_agent_with_dummy_tools(agent)
            
        # Initialize MCP client with tools from config
        logging.info("Creating MCPClient instance...")
        client = MCPClient()
        
        logging.info("Loading servers from config...")
        client.load_servers(str(CONFIG_FILE))
        
        try:
            logging.info("Starting MCP client and loading tools...")
            # Add timeout for server startup
            tools = await asyncio.wait_for(client.start(), timeout=10.0)
            logging.info(f"Client started successfully, found {len(tools)} tools")
            
            if not tools:
                logging.warning("No tools were found by the MCP client!")
                # Create a dummy tool since we can't load real ones
                return client, create_agent_with_dummy_tools(agent)[1]
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
                for tool in tools:
                    logging.info(f"Tool available: {tool.name}")
                
                # Assign tools to agent
                agent.tools = tools
                
                logging.info(f"Agent created with {len(agent.tools) if hasattr(agent, 'tools') else 0} tools")
                return client, agent
                
        except asyncio.TimeoutError:
            logging.error("Timeout waiting for MCP client to start")
            return client, create_agent_with_dummy_tools(agent)[1]
        except Exception as e:
            logging.error(f"Error starting MCP client: {e}")
            logging.error(f"Stack trace: {traceback.format_exc()}")
            # Return client and agent with dummy tools
            return client, create_agent_with_dummy_tools(agent)[1]
        
    except Exception as e:
        logging.error(f"Error initializing MCP client: {e}")
        logging.error(f"Stack trace: {traceback.format_exc()}")
        # Return agent with dummy tools
        return None, create_agent_with_dummy_tools(agent)[1]

def create_agent_with_dummy_tools(agent=None):
    """Helper function to create an agent with dummy tools for fallback"""
    if agent is None:
        agent = Agent(model=get_model())
    
    from pydantic_ai import Tool
    
    # Create a dummy search tool
    async def dummy_brave_search(**kwargs):
        logging.info(f"Dummy Brave search called with: {kwargs}")
        query = kwargs.get('query', '')
        location = kwargs.get('location', '')
        
        # Return mock search results based on query
        if 'dentist' in query.lower():
            return [
                {"name": "Al-Madinah Dental Center", "rating": 4.8, "mentions": 120},
                {"name": "Dr. Tariq Dental Clinic", "rating": 4.5, "mentions": 85},
                {"name": "Jeddah Smile Dentistry", "rating": 4.6, "mentions": 93}
            ]
        elif 'plumber' in query.lower():
            return [
                {"name": "Jeddah Plumbing Services", "rating": 4.2, "mentions": 42},
                {"name": "Al-Balad Maintenance Co.", "rating": 3.9, "mentions": 28},
                {"name": "Expert Pipe Fixers", "rating": 4.4, "mentions": 56}
            ]
        else:
            return [
                {"name": f"Top {query.title()} Provider", "rating": 4.7, "mentions": 78},
                {"name": f"Jeddah {query.title()} Services", "rating": 4.3, "mentions": 54},
                {"name": f"Al-Balad {query.title()} Experts", "rating": 4.5, "mentions": 62}
            ]
    
    # Create a dummy maps tool
    async def dummy_maps_search(**kwargs):
        logging.info(f"Dummy Maps search called with: {kwargs}")
        query = kwargs.get('query', '')
        location = kwargs.get('location', '')
        
        # Return mock location results
        return [
            {"name": f"{query.title()} Service Near {location}", "address": f"123 Main St, {location}", "rating": 4.5, "reviews": 42},
            {"name": f"24/7 {query.title()} Services", "address": f"456 Oak Rd, {location}", "rating": 4.2, "reviews": 28},
            {"name": f"Premier {query.title()} Center", "address": f"789 Pine Ave, {location}", "rating": 4.8, "reviews": 65}
        ]
    
    # Create the tools
    brave_tool = Tool(
        dummy_brave_search,
        name="mcp_brave_brave_web_search",
        description="Search the web for information about businesses and services",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "count": {"type": "number", "description": "Number of results"}
            },
            "required": ["query"]
        }
    )
    
    maps_tool = Tool(
        dummy_maps_search,
        name="mcp_github_search_code", 
        description="Search for businesses and locations on a map",
        parameters={
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search query"},
                "location": {"type": "string", "description": "Location to search near"}
            },
            "required": ["q"]
        }
    )
    
    # Add tools to agent
    agent.tools = [brave_tool, maps_tool]
    logging.info(f"Created agent with {len(agent.tools)} dummy tools for fallback")
    
    return None, agent

# Add this test function at the end of the file
async def test_agent():
    """
    Simple test function to verify the agent is working correctly.
    """
    logging.info("======= TESTING AGENT =======")
    try:
        # Get the agent
        mcp_client, agent = await get_pydantic_ai_agent()
        
        # Check if we have a valid agent
        if agent is None:
            logging.error("Agent is None")
            return
        
        # Print agent info
        if hasattr(agent, 'tools'):
            logging.info(f"Agent has {len(agent.tools)} tools")
            for i, tool in enumerate(agent.tools):
                logging.info(f"Tool {i+1}: {tool.name} - {tool.description[:50]}...")
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
        import traceback
        logging.error(traceback.format_exc())
    finally:
        # Clean up
        if 'mcp_client' in locals() and mcp_client:
            await mcp_client.cleanup()

# If this file is run directly, run the test
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent()) 