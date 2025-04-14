# Find My Service

A modern web application that helps users find service providers near them using AI-powered search.


https://github.com/user-attachments/assets/3f1bf2b4-91f9-4a75-91b9-7af1e12f0c5b

-----

<img width="1680" alt="Screenshot 2025-04-14 at 11 01 59 AM" src="https://github.com/user-attachments/assets/e44c9046-2816-41a3-b08f-2a30dc1e0936" />


## What It Does

Find My Service connects people with local service providers by:

- Finding businesses based on specific needs (plumbers, doctors, etc.)
- Showing ratings and review information
- Providing location-based results
- Working in multiple languages
- Handling different service categories


<img width="845" alt="Screenshot 2025-04-14 at 11 03 17 AM" src="https://github.com/user-attachments/assets/a3d6c326-802e-4488-9316-0ef24dcc1542" />
Real results, Real Provider:
<img width="1369" alt="Screenshot 2025-04-14 at 10 51 17 AM" src="https://github.com/user-attachments/assets/ec6b0526-73c6-4c4a-b958-3d6c329eafce" />


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
