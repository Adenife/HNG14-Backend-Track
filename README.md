# Insighta Labs+ Backend

Secure, authenticated FastAPI backend for the Insighta Labs+ platform.

## 🚀 Live Demo

**Public API URL:** `https://your-deployed-url.com`  
**API Documentation (Swagger):** `https://your-deployed-url.com/docs`

---

## 🛠️ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Language:** Python 3.9+
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** GitHub OAuth 2.0 + JWT with PKCE
- **Deployment:** [Render / Railway / Fly.io]

---

## 🏗️ Architecture

### System Overview

Insighta Labs+ consists of three interconnected components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CLI Tool      │     │   Web Portal    │     │   Backend API   │
│  (insighta-cli) │────▶│   (Next.js)     │────▶│   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │   PostgreSQL    │
                                                └─────────────────┘
```

### Security Model

- **OAuth 2.0 + PKCE**: GitHub-based authentication with Proof Key for Code Exchange
- **JWT Tokens**: Short-lived access tokens (3 min) with refresh token rotation (5 min)
- **Role-Based Access Control (RBAC)**: `admin` (full access) and `analyst` (read-only)
- **Rate Limiting**: 10 req/min on auth endpoints, 60 req/min on API endpoints per user

---

## 🔐 Authentication Flow

### Token Lifecycle

1. **Login**: User authenticates via GitHub OAuth
2. **Access Token** (3 min expiry): Used for API requests
3. **Refresh** (5 min expiry): Used to obtain new token pairs
4. **Rotation**: Each refresh invalidates the old refresh token
5. **Logout**: Server-side token revocation

### Token Handling in Different Interfaces

| Interface | Token Storage                  | Security                             |
| --------- | ------------------------------ | ------------------------------------ |
| CLI       | `~/.insighta/credentials.json` | File permissions                     |
| Web       | HTTP-only cookies              | `HttpOnly`, `Secure`, `SameSite=Lax` |

---

## 👥 Role Enforcement

| Role      | Permissions                                            |
| --------- | ------------------------------------------------------ |
| `admin`   | Create profiles, delete profiles, read, search, export |
| `analyst` | Read, search, export (no modifications)                |

All `/api/*` endpoints require authentication and enforce role permissions via FastAPI dependencies.

---

## 🧠 Natural Language Parsing (NLQ) Approach

The parser uses a Pattern-Matching Strategy for fast, deterministic search:

| Keyword/Pattern                   | Captured Value    |
| --------------------------------- | ----------------- |
| `(?:from\|in)\s+([a-zA-Z\s]{2,})` | Country Name/Code |
| `(?:male\|female\|other)`         | Gender            |
| `(\d+)\s+to\s+(\d+)`              | Age Range         |

---

## 🚦 API Endpoints

### Authentication

| Method | Endpoint                | Description                         |
| ------ | ----------------------- | ----------------------------------- |
| GET    | `/auth/github`          | Redirect to GitHub OAuth            |
| GET    | `/auth/github/callback` | Handle OAuth callback, issue tokens |
| POST   | `/auth/refresh`         | Rotate token pair                   |
| POST   | `/auth/logout`          | Revoke refresh token                |

### Profiles

| Method | Endpoint               | Description                            | Access     |
| ------ | ---------------------- | -------------------------------------- | ---------- |
| GET    | `/api/profiles`        | List with filters, sorting, pagination | analyst+   |
| GET    | `/api/profiles/{id}`   | Get single profile                     | analyst+   |
| GET    | `/api/profiles/search` | Natural language search                | analyst+   |
| POST   | `/api/profiles`        | Create new profile                     | admin only |
| GET    | `/api/profiles/export` | Export as CSV                          | analyst+   |

### Headers Required

All `/api/*` requests must include:

```
X-API-Version: 1
Authorization: Bearer <access_token>
```

---

## 📦 Installation

```bash
# Clone and setup
git clone https://github.com/your-org/HNG14-Backend-Track.git
cd HNG14-Backend-Track

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GitHub OAuth credentials
```

### Environment Variables

```env
# Database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=insighta
POSTGRES_HOST=localhost
POSTGRES_HOSTNAME=localhost
DATABASE_PORT=5432

# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=3
REFRESH_TOKEN_EXPIRE_MINUTES=5

# URLs
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

---

## 🏃 Running

```bash
# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

---

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

---

## 📁 Project Structure

```
HNG14-Backend-Track/
├── main.py                    # Application entry point
├── alembic.ini                # Alembic configuration
├── app/
│   ├── core/
│   │   ├── auth.py            # Authentication dependencies
│   │   ├── config.py          # Settings management
│   │   ├── database.py        # Database connection
│   │   ├── limiter.py         # Rate limiting
│   │   ├── logging.py         # Request logging
│   │   ├── middleware.py      # API versioning, logging
│   │   └── security.py        # JWT token creation/verification
│   ├── models/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── cruds/             # Database operations
│   │   └── schemas/           # Pydantic schemas
│   ├── routers/
│   │   ├── auth.py            # Auth endpoints
│   │   ├── profiles.py        # Profile endpoints
│   │   └── ...
│   └── services/
│       └── external_api.py    # External API calls
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_profiles.py
└── .github/workflows/
    └── ci.yml                 # GitHub Actions CI
```

---

## 📄 License

MIT License
