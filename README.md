# E-Commerce Website with AI Shopping Assistant

A full-stack e-commerce application with a React frontend, Node.js/Express backend, SQLite database, and an AI-powered shopping assistant chatbot backed by AWS Bedrock.

## Architecture

| Service   | Stack                          | Port |
|-----------|--------------------------------|------|
| Frontend  | React 18, React Router v6      | 3000 |
| Backend   | Node.js, Express, better-sqlite3 | 3001 |
| Chatbot   | Python, FastAPI, Strands SDK   | 3002 |

---

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **AWS account** with access to Amazon Bedrock

---

## 1. AWS IAM Setup

The chatbot uses **Amazon Bedrock** to power its AI responses. You need AWS credentials with Bedrock permissions.

### Step 1 — Enable the Bedrock model

1. Sign in to the [AWS Console](https://console.aws.amazon.com)
2. Navigate to **Amazon Bedrock → Model access** (top-right region must match your `AWS_DEFAULT_REGION`)
3. Click **Manage model access**
4. Find **Amazon Nova Pro** and enable it
5. Wait for status to show **Access granted** (usually instant)

### Step 2 — Create an IAM user with Bedrock permissions

1. Go to **IAM → Users → Create user**
2. Give it a name (e.g. `bedrock-dev`)
3. On the permissions step, choose **Attach policies directly**
4. Search for and attach **AmazonBedrockFullAccess** (or a least-privilege custom policy)
5. Complete user creation

### Step 3 — Generate access keys

1. Open the newly created user → **Security credentials** tab
2. Click **Create access key** → choose **Application running outside AWS**
3. Copy the **Access key ID** and **Secret access key** — you won't see the secret again

> **Temporary credentials (SSO / assume-role):** If your organisation uses AWS SSO or you're using `aws sts assume-role`, you'll also have a session token. Set `AWS_SESSION_TOKEN` in `.env` as well.

---

## 2. Required Files Not in the Repo

Two files are excluded from version control and must be created locally before running the app.

### `chatbot/.env` — AWS credentials and chatbot config

```bash
cp chatbot/.env.example chatbot/.env
```

Then open `chatbot/.env` and fill in your credentials:

```ini
# Required
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Only needed for temporary/SSO credentials
# AWS_SESSION_TOKEN=...

# Bedrock model (must be enabled in your account)
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
```

The remaining settings have sensible defaults and generally don't need to change:

| Variable             | Default                    | Description                        |
|----------------------|----------------------------|------------------------------------|
| `SERVER_HOST`        | `0.0.0.0`                  | Chatbot server bind address        |
| `SERVER_PORT`        | `3002`                     | Chatbot server port                |
| `BACKEND_BASE_URL`   | `http://localhost:3001`    | Backend API URL                    |
| `BACKEND_TIMEOUT`    | `10`                       | Backend request timeout (seconds)  |
| `SESSION_TTL_MINUTES`| `30`                       | Idle session expiry                |
| `MAX_CONTEXT_MESSAGES`| `20`                      | Chat history window size           |
| `LLM_TEMPERATURE`    | `0.7`                      | Model creativity (0.0–1.0)         |
| `LLM_MAX_TOKENS`     | `2048`                     | Max tokens per response            |

### `backend/ecommerce.db` — SQLite database

This file is **auto-generated** the first time the backend starts. You do not need to create it manually. The backend seeds it with 20 products and sample reviews on first run.

---

## 3. Installation

### Backend

```bash
cd backend
npm install
```

### Frontend

```bash
cd frontend
npm install
```

### Chatbot

```bash
cd chatbot
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 4. Running the Application

Start all three services in separate terminals, in this order:

**Terminal 1 — Backend**
```bash
cd backend
npm start
# Running on http://localhost:3001
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm start
# Running on http://localhost:3000
```

**Terminal 3 — Chatbot**
```bash
cd chatbot
source venv/bin/activate        # Windows: venv\Scripts\activate
python -m src.chat_handler
# Running on http://localhost:3002
```

Open http://localhost:3000 in your browser.

---

## 5. API Overview

### Backend endpoints

| Method | Path                  | Description                  |
|--------|-----------------------|------------------------------|
| GET    | `/api/products`       | List all products             |
| GET    | `/api/products/:id`   | Product detail with reviews   |
| GET    | `/api/cart`           | Cart items with product info  |
| POST   | `/api/cart`           | Add item to cart              |
| PUT    | `/api/cart/:id`       | Update cart item quantity     |
| DELETE | `/api/cart/:id`       | Remove cart item              |

### Chatbot endpoint

| Method | Path     | Description                          |
|--------|----------|--------------------------------------|
| POST   | `/chat`  | Send a message, receive AI response  |

---

## 6. Project Structure

```
/
├── backend/              Express API server
│   ├── server.js         REST endpoints
│   ├── database.js       SQLite schema and seed data
│   └── ecommerce.db      Auto-generated SQLite database (gitignored)
│
├── frontend/             React SPA
│   └── src/
│       ├── App.js        Routing
│       └── pages/        Home, Product, Cart pages
│
├── chatbot/              AI shopping assistant
│   ├── src/              Application source
│   ├── .env              Local credentials (gitignored — copy from .env.example)
│   ├── .env.example      Template for .env
│   └── requirements.txt  Python dependencies
│
└── README.md
```

---

## 7. Security Notes

- **Never commit `.env`** — it is listed in `.gitignore` at both the root and `chatbot/` level
- **Rotate credentials** if they are ever accidentally exposed
- Use IAM policies that grant only the permissions you need (least privilege)
- Prefer short-lived credentials (SSO, instance profiles) over long-lived IAM user keys in shared or production environments
