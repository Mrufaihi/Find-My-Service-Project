# Find My Service

A modern web application that helps users find service providers near them using AI-powered search.

![Main Interface](images/main-interface.png)
*Screenshot placeholder: Main search interface*

## What It Does

Find My Service connects people with local service providers by:

- Finding businesses based on specific needs (plumbers, doctors, etc.)
- Showing ratings and review information
- Providing location-based results
- Working in multiple languages
- Handling different service categories

![Search Results](images/search-results.png)
*Screenshot placeholder: Search results with ratings*

## How It Works

1. **User enters their query** - What they need help with, where they are, and service category
2. **AI-powered search** - Our system uses multiple search tools to find the best matches
3. **Smart verification** - Checks that providers actually offer the requested services
4. **Fallback systems** - Always delivers results even when search APIs have issues
5. **Rating filtering** - Shows only highly-rated providers (4.0+ stars)

## Technology Stack

- **Frontend**: Svelte with TailwindCSS
- **Backend**: Django
- **AI Search**: Claude AI with brave_search, google_maps, and web_search tools
- **Database**: SQLite (development) / PostgreSQL (production)

![Architecture](images/architecture.png)
*Diagram placeholder: System architecture*

## Key Features

- **Multi-category search** - Find providers in different categories
- **Interactive map** - Select your location visually
- **Rating display** - See provider ratings at a glance
- **Robust search** - Gracefully handles API limits and errors
- **Smooth UI** - Clean, modern interface with dark/light mode

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- API keys for Google Maps and Brave Search

### Setup

1. Clone the repository

```bash
git clone https://github.com/yourusername/find-my-service.git
cd find-my-service
```

2. Install backend dependencies

```bash
pip install -r requirements.txt
```

3. Install frontend dependencies

```bash
cd frontend
npm install
```

4. Set up your API keys in `find_my_service/mcp_config.json`
5. Run development servers:

```bash
# Backend
python manage.py runserver

# Frontend (in another terminal)
cd frontend
npm run dev
```

## Future Plans

- User accounts and saved providers
- User rating system
- Favoriting places and storing them
- Provider verification system
- More detailed provider information


## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Find My Service: The smart way to find help nearby*
