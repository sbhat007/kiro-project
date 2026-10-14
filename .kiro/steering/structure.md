---
inclusion: always
---

# Project Structure

## Root Layout
```
/backend          Backend API server
/frontend         React frontend application
README.md         Setup and running instructions
```

## Backend Structure
```
backend/
├── server.js       Express server with REST endpoints
├── database.js     SQLite setup, schema, and seeding
├── ecommerce.db    SQLite database file
└── package.json    Dependencies: express, cors, better-sqlite3
```

### API Endpoints
- `GET /api/products` - List all products
- `GET /api/products/:id` - Get product with reviews
- `GET /api/cart` - Get cart items with product details
- `POST /api/cart` - Add item to cart
- `PUT /api/cart/:id` - Update cart item quantity
- `DELETE /api/cart/:id` - Remove cart item

## Frontend Structure
```
frontend/
├── public/
│   └── index.html       HTML template
├── src/
│   ├── index.js         React entry point
│   ├── App.js           Main component with routing
│   ├── App.css          Global styles
│   └── pages/
│       ├── Home.js      Product grid page
│       ├── Product.js   Product detail page
│       └── Cart.js      Shopping cart page
└── package.json         Dependencies: react, react-router-dom
```

### Routing
- `/` - Home page (product grid)
- `/product/:id` - Product detail page
- `/cart` - Shopping cart page

## Code Conventions
- ES modules syntax (import/export)
- Functional React components with hooks
- API calls use fetch with async/await
- Console logging for backend operations
- Inline styles and CSS for frontend styling
