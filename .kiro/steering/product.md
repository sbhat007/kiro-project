---
inclusion: always
---

# Product Overview

Simple 3-tier e-commerce application demonstrating a full-stack web store.

## Core Features

- Product catalog with 20 items (emoji-based images)
- Product detail pages with reviews and pricing
- Shopping cart with add/update/remove functionality
- SQLite database for persistence

## Architecture

Three-tier architecture:
- Frontend: React SPA with client-side routing
- Backend: Express REST API
- Database: SQLite with better-sqlite3

Frontend and backend run as separate processes communicating via HTTP.
