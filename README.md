# Truth Board

A real-time news analysis platform that tracks media bias, fact-checks claims, and identifies conflicts in news coverage.

## Features

- **Bias Analysis**: Measures political and geographic bias in news sources
- **Fact Checking**: Automated verification of claims using multiple sources
- **Conflict Detection**: Identifies contradictory reporting across sources
- **Truth Scoring**: AI-powered confidence ratings for news events
- **International Coverage**: Tracks global news diversity and perspectives

## Tech Stack

- **Backend**: Python (FastAPI) with PostgreSQL
- **Frontend**: Next.js with TypeScript
- **Deployment**: Render (API) + Vercel (Frontend)
- **AI**: OpenAI GPT-4 for analysis and fact-checking

## Quick Start

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `.env` files with:
- `DATABASE_URL`: PostgreSQL connection string
- `NEWSAPI_KEY`: News API key
- `MEDIASTACK_KEY`: MediaStack API key

## API Endpoints

- `GET /events` - List news events with analysis
- `GET /events/{id}` - Get specific event details
- `GET /health/ready` - Health check

## Deployment

The application is deployed on:
- **API**: https://truthboard-api.onrender.com
- **Frontend**: https://truthboard.vercel.app

## Data Sources

- GDELT (Global Database of Events)
- NewsAPI
- MediaStack
- RSS feeds from major news outlets
- Reddit discussions
- Official sources (WHO, NASA, USGS, etc.)

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Sources   │───▶│   Backend    │───▶│  Frontend   │
│ (News APIs) │    │   (FastAPI)  │    │  (Next.js)  │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ PostgreSQL   │
                   │  Database    │
                   └──────────────┘
```

## License

MIT License
