# Truth Layer Frontend

Next.js 14 frontend for the Truth Layer MVP.

## Features

- **Server-Side Rendering**: SEO-friendly event pages
- **Responsive Design**: Mobile-first with Tailwind CSS
- **Confidence Meters**: Visual trust indicators
- **Evidence Drawers**: Expandable source lists
- **Real-time Updates**: ISR with 60-second revalidation

## Development

### Local Setup

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Open http://localhost:3000
```

### Docker

```bash
# Build
docker build -t truth-layer-frontend .

# Run
docker run -p 3000:3000 truth-layer-frontend
```

## Pages

- `/` - Top Confirmed Events (≥75 score)
- `/developing` - Developing Events (40-74 score)
- `/underreported` - Underreported Stories
- `/stats` - System Statistics

## Components

- `EventCard` - Event display with metadata
- `ConfidenceMeter` - Visual score indicator
- `EvidenceDrawer` - Collapsible source list
- `StatsPanel` - Aggregate metrics

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Tech Stack

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS

## License

MIT
