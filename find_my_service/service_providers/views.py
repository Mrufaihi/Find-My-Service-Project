from django.shortcuts import render
from django.http import JsonResponse
from .models import ServiceProvider, UserSearch
import json
import re
from django.views.decorators.csrf import csrf_exempt
import logging
import asyncio
import traceback

# Set up proper logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import MCP agent
try:
    from .pydantic_mcp_agent import get_pydantic_ai_agent
    MCP_AVAILABLE = True
    logger.info("MCP agent imported successfully")
except ImportError as e:
    logger.error(f"Failed to import MCP agent: {e}")
    MCP_AVAILABLE = False

# Create your views here.

def index(request):
    """
    Renders the main page of the application.
    This serves the page that contains our Svelte app.
    """
    return render(request, 'index.html')

def search_providers(request):
    """
    Enhanced search function that:
    1. Receives search query and location
    2. Records the search in the database
    3. Uses MCP tools via AI agent if available, falls back to mock data
    4. Returns results to the frontend
    """
    logger.info("Search provider request received")
    query = request.GET.get('query', '')
    location = request.GET.get('location', '')
    category = request.GET.get('category', 'general')
    
    logger.info(f"Search params - Query: '{query}', Location: '{location}', Category: '{category}'")
    
    # Save the search query (only if both fields are provided)
    if query and location:
        UserSearch.objects.create(query=query, location=location)
        logger.debug("Search query saved to database")
    
    # Check if MCP is available for enhanced search
    if MCP_AVAILABLE:
        logger.info("MCP is available, attempting AI-powered search")
        
        # Import these at runtime to avoid circular imports
        import nest_asyncio
        
        # Apply nest_asyncio to allow nested event loops
        try:
            nest_asyncio.apply()
            logger.info("Applied nest_asyncio to allow nested event loops")
        except Exception as e:
            logger.warning(f"Failed to apply nest_asyncio: {e}")
        
        try:
            # Use a dedicated function to handle the asyncio operations
            # This avoids event loop issues between requests
            search_results, raw_response = run_in_fresh_loop(query, location, category)
            
            # Process the search results
            if isinstance(search_results, str):
                # This means we got an error message
                logger.warning(f"AI search returned error: {search_results}")
                return JsonResponse({
                    'success': True,
                    'providers': get_dummy_search_results(query, location),
                    'debug_message': search_results,
                    'raw_response': raw_response,
                    'mcp_powered': True
                })
            
            # If search was successful
            if search_results:
                logger.info(f"AI search successful, returning {len(search_results)} results")
                return JsonResponse({
                    'success': True,
                    'providers': search_results,
                    'raw_response': raw_response,
                    'mcp_powered': True
                })
        except Exception as e:
            logger.error(f"Error in search_providers: {str(e)}")
            logger.error(traceback.format_exc())
            # Continue with fallback if MCP fails
            return JsonResponse({
                'success': True,
                'providers': get_dummy_search_results(query, location),
                'error': str(e),
                'traceback': traceback.format_exc(),
                'mcp_powered': False
            })
    else:
        logger.info("MCP is not available, using fallback search")
    
    # Extract potential provider names from the query as fallback
    potential_names = extract_potential_names(query)
    logger.info(f"Using fallback search, extracted {len(potential_names)} potential names")
    
    # Return mock data if MCP search failed or isn't available
    mock_results = [
        {'id': 1, 'name': 'Dr. Sarah Johnson', 'mentions': 18, 'rating': 4.8},
        {'id': 2, 'name': 'Elite Plumbing Services', 'mentions': 12, 'rating': 4.5},
        {'id': 3, 'name': 'Smile Dental Clinic', 'mentions': 9, 'rating': 4.7}
    ]
    
    logger.info("Returning mock results")
    # Return the results as JSON
    return JsonResponse({
        'success': True,
        'providers': mock_results,
        'extracted_names': potential_names,
        'mcp_powered': False
    })

def run_in_fresh_loop(query, location, category):
    """Run the search in a fresh event loop"""
    logger.debug("Creating fresh event loop for search")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the combined search in the new loop
        return loop.run_until_complete(run_combined_search(query, location, category))
    finally:
        # Make sure to close the loop and clean up, but only after the task is complete
        loop.close()
        logger.debug("Closed fresh event loop")

async def run_combined_search(query, location, category):
    """Run the combined search with clean agent initialization"""
    mcp_client = None
    try:
        # Create a fresh agent for each search
        logger.debug("Getting fresh Pydantic AI agent")
        mcp_client, agent = await get_pydantic_ai_agent()
        
        if agent is None:
            logger.error("Failed to get agent, agent is None")
            return "Error: Failed to initialize AI agent", "Agent is None"
        
        logger.info(f"Agent created with {len(agent.tools) if hasattr(agent, 'tools') else 0} tools")
        
        # Create prompt with category-specific details
        if category == 'general':
            category_prompt = "Find any type of service provider that can help with this request."
        elif category == 'handy':
            category_prompt = "Focus on finding handymen, repair services, and maintenance professionals."
        elif category == 'medicine':
            category_prompt = "Focus on finding doctors, clinics, hospitals, and healthcare providers."
        else:
            category_prompt = f"Focus on finding providers in the {category} category."
            
        prompt = f"""
        Find service providers that can help with the following request:
        
        Request: {query}
        Location: {location}
        
        {category_prompt}
        
        Use web search or maps to find the most relevant service providers.
        For each provider, return their name, an estimated number of mentions/reviews,
        and an estimated rating score from 1-5.
        
        Format the results as a JSON array where each item has the properties:
        "name" (string), "mentions" (number), and "rating" (number from 1-5).
        """
        
        logger.debug("Running agent for search results")
        result = await agent.run(prompt)
        
        # Extract and process response
        response_text = extract_response_text(result)
        providers = extract_providers(response_text)
        
        # Return both the processed results and the raw response
        return providers, response_text
    except Exception as e:
        logger.error(f"Error in combined search: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Search error: {str(e)}", f"Error details: {str(e)}"
    finally:
        # Clean up MCP client in the finally block
        if mcp_client:
            logger.debug("Cleaning up MCP client")
            await mcp_client.cleanup()

def get_dummy_search_results(query, location):
    """Generate dummy search results when real ones fail"""
    query_lower = query.lower()
    
    # Dentist-related searches
    if 'dentist' in query_lower or 'dental' in query_lower or 'teeth' in query_lower:
        return [
            {"name": "Al-Madinah Dental Center", "rating": 4.8, "mentions": 120},
            {"name": "Dr. Tariq Dental Clinic", "rating": 4.5, "mentions": 85},
            {"name": "Jeddah Smile Dentistry", "rating": 4.6, "mentions": 93}
        ]
    # Plumber-related searches
    elif 'plumb' in query_lower or 'pipe' in query_lower or 'leak' in query_lower:
        return [
            {"name": "Jeddah Plumbing Services", "rating": 4.2, "mentions": 42},
            {"name": "Al-Balad Maintenance Co.", "rating": 3.9, "mentions": 28},
            {"name": "Expert Pipe Fixers", "rating": 4.4, "mentions": 56}
        ]
    # Electrician-related searches
    elif 'electric' in query_lower or 'wiring' in query_lower or 'power' in query_lower:
        return [
            {"name": "Jeddah Electrical Services", "rating": 4.5, "mentions": 63},
            {"name": "Al-Balad Electric Co.", "rating": 4.3, "mentions": 45},
            {"name": "Power Solutions Jeddah", "rating": 4.7, "mentions": 71}
        ]
    # Doctor-related searches
    elif 'doctor' in query_lower or 'physician' in query_lower or 'medical' in query_lower:
        return [
            {"name": "Dr. Ahmed Family Clinic", "rating": 4.9, "mentions": 142},
            {"name": "Jeddah Medical Center", "rating": 4.6, "mentions": 118},
            {"name": "Saudi German Hospital", "rating": 4.7, "mentions": 220}
        ]
    # Generic fallback
    else:
        return [
            {"name": f"Top {query.title()} Provider", "rating": 4.7, "mentions": 78},
            {"name": f"Jeddah {query.title()} Services", "rating": 4.3, "mentions": 54},
            {"name": f"Al-Balad {query.title()} Experts", "rating": 4.5, "mentions": 62}
        ]

# Helper function to extract text from response object
def extract_response_text(result):
    """Extract text from various response object formats"""
    if hasattr(result, 'data'):
        return result.data
    elif hasattr(result, 'text'):
        return result.text
    elif hasattr(result, 'content'):
        return result.content
    elif hasattr(result, 'response'):
        return result.response
    else:
        return str(result)

# Helper function to extract providers from response text
def extract_providers(response_text):
    """Extract provider data from response text"""
    logger.debug(f"Extracting providers from response: {response_text[:200]}...")
    
    # Try to find JSON array in the response
    import re
    json_match = re.search(r'\[.*\]', response_text.replace('\n', ''), re.DOTALL)
    
    if json_match:
        providers_json = json_match.group(0)
        logger.debug(f"Extracted JSON: {providers_json}")
        try:
            providers = json.loads(providers_json)
            logger.info(f"Successfully parsed {len(providers)} providers from JSON")
            return providers
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return parse_ai_response(response_text)
    else:
        logger.warning("No JSON array found in AI response, falling back to text parsing")
        return parse_ai_response(response_text)

async def mcp_search(query, location, category="general"):
    """
    Use MCP tools via AI agent to search for service providers.
    
    Args:
        query (str): User's search query
        location (str): Location for search
        category (str): Category of service
        
    Returns:
        list: Provider results from AI-powered search
        or
        str: Error message if search failed
    """
    logger.info("Starting MCP search")
    try:
        # Get MCP agent with tools
        logger.debug("Getting Pydantic AI agent")
        mcp_client, agent = await get_pydantic_ai_agent()
        if agent is None:
            logger.error("Failed to get agent, agent is None")
            return "Error: Failed to initialize AI agent"
            
        if hasattr(agent, 'tools'):
            logger.info(f"Agent has {len(agent.tools)} tools available")
        else:
            logger.warning("Agent has no tools attribute")
        
        # Create prompt for the AI
        prompt = f"""
        Find service providers that can help with the following request:
        
        Request: {query}
        Location: {location}
        Category: {category}
        
        Use web search or maps to find the most relevant service providers.
        For each provider, return their name, an estimated number of mentions/reviews,
        and an estimated rating score from 1-5.
        
        Format the results as a JSON array where each item has the properties:
        "name" (string), "mentions" (number), and "rating" (number from 1-5).
        """
        
        logger.debug(f"Sending prompt to AI agent: {prompt[:100]}...")
        
        # Process the request with AI agent
        logger.info("Running AI agent with prompt")
        result = await agent.run(prompt)
        logger.info("AI agent returned a result")
        
        # Extract response text
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
        
        logger.debug(f"AI response: {response_text[:200]}...")
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\[.*\]', response_text.replace('\n', ''), re.DOTALL)
        
        if json_match:
            providers_json = json_match.group(0)
            logger.debug(f"Extracted JSON: {providers_json}")
            providers = json.loads(providers_json)
            logger.info(f"Successfully parsed {len(providers)} providers from JSON")
            return providers
        else:
            logger.warning("No JSON array found in AI response, falling back to text parsing")
            # If JSON not found, parse text results as best as possible
            parsed_results = parse_ai_response(response_text)
            logger.info(f"Parsed {len(parsed_results)} providers from text")
            return parsed_results
            
    except Exception as e:
        logger.error(f"Error in MCP search: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Search error: {str(e)}"
    finally:
        # Clean up MCP client if it exists
        if 'mcp_client' in locals() and mcp_client:
            logger.debug("Cleaning up MCP client")
            await mcp_client.cleanup()

def parse_ai_response(text):
    """
    Parse non-JSON AI response into provider data.
    This is a fallback when the AI doesn't return proper JSON.
    
    Args:
        text (str): Text response from AI
        
    Returns:
        list: Parsed provider data
    """
    logger.info("Parsing AI text response")
    providers = []
    
    # Look for patterns like "Name: ABC Company" followed by rating info
    provider_blocks = re.split(r'\d+\.\s+', text)[1:]  # Split by numbered list items
    
    if not provider_blocks:
        # Try splitting by double newlines
        logger.debug("No numbered list found, trying paragraph splits")
        provider_blocks = text.split("\n\n")
    
    logger.debug(f"Found {len(provider_blocks)} potential provider blocks")
    
    for block in provider_blocks:
        if not block.strip():
            continue
            
        # Extract name
        name_match = re.search(r'(?:Name:?\s*|^)([^,\n]+)', block)
        name = name_match.group(1).strip() if name_match else "Unknown Provider"
        
        # Extract rating
        rating_match = re.search(r'(?:Rating:?\s*|rating:?\s*)(\d+\.?\d*)', block)
        rating = float(rating_match.group(1)) if rating_match else 4.0
        
        # Extract mentions/reviews
        mentions_match = re.search(r'(?:Mentions:?\s*|mentions:?\s*|Reviews:?\s*|reviews:?\s*)(\d+)', block)
        mentions = int(mentions_match.group(1)) if mentions_match else 10
        
        logger.debug(f"Parsed provider: {name}, rating: {rating}, mentions: {mentions}")
        
        providers.append({
            "name": name,
            "rating": rating,
            "mentions": mentions
        })
    
    # If no providers were parsed but there's text, create a single entry
    if not providers and text.strip():
        logger.warning("Could not parse any providers from text, creating generic entry")
        providers.append({
            "name": "AI Recommendation",
            "rating": 4.0,
            "mentions": 1
        })
        
    return providers

def extract_potential_names(text):
    """
    A simple proof of concept for name extraction.
    
    This function uses regular expressions to find patterns that might represent
    service provider names in the text. In a real implementation, this would use
    more sophisticated NLP techniques like Named Entity Recognition.
    
    Args:
        text (str): The user's search query text
        
    Returns:
        list: A list of potential service provider names found in the text
    """
    # Simple patterns to match potential service provider names
    name_patterns = [
        r'Dr\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Dr. First Last
        r'Mr\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Mr. First Last
        r'Mrs\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Mrs. First Last
        r'Ms\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',   # Ms. First Last
        r'[A-Z][a-z]+\'s\s+[A-Z][a-z]+',       # Sarah's Dental
        r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+Services' # Elite Plumbing Services
    ]
    
    potential_names = []
    for pattern in name_patterns:
        matches = re.findall(pattern, text)
        potential_names.extend(matches)
    
    return potential_names

async def get_raw_ai_response(query, location, category="general"):
    """
    Get the raw AI response for debugging purposes.
    """
    try:
        # Get MCP agent with tools
        mcp_client, agent = await get_pydantic_ai_agent()
        
        if agent is None:
            return "Error: Agent is None"
            
        # Create prompt for the AI
        prompt = f"""
        Find service providers that can help with the following request:
        
        Request: {query}
        Location: {location}
        Category: {category}
        
        Use web search or maps to find the most relevant service providers.
        For each provider, return their name, an estimated number of mentions/reviews,
        and an estimated rating score from 1-5.
        
        Format the results as a JSON array where each item has the properties:
        "name" (string), "mentions" (number), and "rating" (number from 1-5).
        """
        
        # Process the request with AI agent
        result = await agent.run(prompt)
        
        # Extract response text
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
            
        return response_text
    except Exception as e:
        return f"Error getting raw response: {str(e)}"
    finally:
        if 'mcp_client' in locals() and mcp_client:
            await mcp_client.cleanup()
