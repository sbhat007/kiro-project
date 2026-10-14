---
inclusion: always
---

# Tech Stack

## Backend
- Node.js with ES modules (`"type": "module"`)
- Express.js for REST API
- better-sqlite3 for database
- CORS enabled for cross-origin requests
- Port: 3001

## Frontend
- React 18.2
- React Router DOM v6 for routing
- Create React App (react-scripts)
- Port: 3000

## Database
- SQLite (ecommerce.db)
- Tables: products, reviews, cart_items
- Auto-seeded with 20 products and sample reviews

## Common Commands

### Backend
```bash
cd backend
npm install    # Install dependencies
npm start      # Start server on http://localhost:3001
```

### Frontend
```bash
cd frontend
npm install    # Install dependencies
npm start      # Start dev server on http://localhost:3000
npm run build  # Production build
```

## Development Workflow
1. Start backend first (terminal 1)
2. Start frontend second (terminal 2)
3. Frontend proxies API calls to backend via CORS
