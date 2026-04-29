# Insighta Labs+ (Stage 3): Comprehensive Documentation

## 1. Executive Summary

The objective of Stage 3 was to evolve the initial "Profile Intelligence System" into **Insighta Labs+**, a secure, multi-interface platform usable by both technical engineers and non-technical analysts. 

To achieve this, the architecture was split into three distinct boundaries:
1. **The Core Backend (`HNG14-Backend-Track`)**: A secure, authenticated, and rate-limited FastAPI server acting as the single source of truth.
2. **The Terminal CLI (`insighta-cli`)**: A fast, robust tool for engineers utilizing a PKCE OAuth flow.
3. **The Web Portal (`insighta-web`)**: A Next.js dashboard providing a seamless, visually rich interface for non-technical users, utilizing server-side security.

---

## 2. Strategic Architecture & Security Decisions

### Why separate repositories?
Separating the Backend, CLI, and Web Portal enforces a strict **Separation of Concerns (SoC)**. It forces the backend to be truly stateless and API-driven, ensuring that no matter the client (CLI, Web, or future mobile apps), the security guarantees and business logic remain consistent.

### The Authentication Strategy (OAuth 2.0 + JWT)
We opted for **GitHub OAuth 2.0** combined with **JWT (JSON Web Tokens)** because it offloads credential management to a trusted provider (GitHub).
- **Short-Lived Access Tokens (3 mins)**: Limits the window of opportunity if a token is intercepted.
- **Refresh Tokens (5 mins) with Rotation**: Every time a client requests a new access token, the old refresh token is invalidated and a new one is issued. This detects and prevents token reuse/hijacking.

### Interface-Specific Security
- **CLI Security (PKCE)**: The CLI uses *Proof Key for Code Exchange (PKCE)*. It generates a cryptographic challenge locally, opens the browser, and spins up a temporary localhost server. Once GitHub redirects back, the CLI completes the exchange without ever hardcoding a client secret into the CLI package.
- **Web Portal Security (HTTP-Only Cookies)**: The Next.js frontend handles the OAuth exchange *on the server side*. Tokens are stored in `HttpOnly`, `Strict` cookies. This means the tokens are completely invisible to client-side JavaScript, effectively eliminating XSS (Cross-Site Scripting) token theft.

---

## 3. Step-by-Step Breakdown of What Was Done

### Phase 1: Backend Security & Database Refactoring
1. **New Database Models**: Added `users` and `refresh_tokens` tables to PostgreSQL to track authenticated users and their valid sessions.
2. **Alembic Migrations**: Configured Alembic to track database schema changes over time. Removed the primitive `Base.metadata.create_all()` startup script.
3. **OAuth Endpoints (`/auth/*`)**: Implemented `/auth/github` (redirect generator), `/auth/github/callback` (token issuer), `/auth/refresh` (token rotation), and `/auth/logout` (token revocation).
4. **Role-Based Access Control (RBAC)**: Enforced `admin` (can create/delete) and `analyst` (read-only) roles using FastAPI `Depends()` guards on all profile endpoints.

### Phase 2: Middleware & API Enhancements
1. **API Versioning Middleware**: Intercepts all requests to `/api/*` and enforces the presence of the `X-API-Version: 1` header.
2. **Logging Middleware**: Logs method, path, execution time, and status codes for observability.
3. **Pagination & Export**: Standardized response schemas to include `page`, `limit`, `total`, `total_pages`, and `links` (`prev`, `next`). Added a `GET /api/profiles/export` endpoint that streams raw CSV data back to authorized clients.

### Phase 3: The CLI Implementation
1. **Scaffolding**: Created a standalone Python package using `Click` and `Rich`.
2. **Local Auth Server**: Wrote a custom threading logic to spin up a local server on port `8899` during login to catch the GitHub callback automatically.
3. **HTTP Client Wrapper**: Implemented an API layer that automatically intercepts `401 Unauthorized` responses, hits the refresh endpoint, and retries the failed request invisibly to the user.
4. **Commands**: Mapped backend endpoints to terminal commands (`insighta profiles list`, `insighta profiles search`, `insighta profiles export`).

### Phase 4: The Web Portal Implementation
1. **Next.js Scaffold**: Created a Next.js 15 App Router project with Tailwind CSS.
2. **Server-Side Callback**: Created an API route `app/api/auth/github/callback/route.ts` that safely exchanges the OAuth code and sets `HttpOnly` cookies.
3. **Middleware Protection**: Wrote `middleware.ts` to intercept unauthorized visits to `/dashboard` and boot users back to the login screen.
4. **UI Construction**: Designed a responsive sidebar layout, a high-level statistics overview, and a paginated profiles table with visual gender probability indicators.

---

## 4. How to Run the Ecosystem Locally

### Prerequisite: Configure the Backend Environment
Ensure your `/home/adenife/Documents/HNG14-Backend-Track/.env` file is populated with valid GitHub OAuth credentials.
```env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
```
*(Note: Your GitHub OAuth App must have `http://localhost:8000/auth/github/callback` and `http://localhost:8899/callback` listed as valid authorization callback URLs).*

### 1. Run the Backend
```bash
cd /home/adenife/Documents/HNG14-Backend-Track
source .venv/bin/activate

# Apply migrations (already done, but good practice)
alembic upgrade head

# Start the server
uvicorn main:app --reload
```
*The backend is now live at `http://localhost:8000`.*

### 2. Run the CLI
Open a *new* terminal window.
```bash
cd /home/adenife/Documents/insighta-cli

# Install the CLI package in editable mode
pip install -e .

# Log in using the CLI (opens your browser)
insighta login --backend http://localhost:8000

# Fetch profiles
insighta profiles list --limit 5

# Search via Natural Language
insighta profiles search "young developers from Nigeria"

# Export data
insighta profiles export --format csv
```

### 3. Run the Web Portal
Open a *third* terminal window.
```bash
cd /home/adenife/Documents/insighta-web

# Install dependencies (if not already done)
npm install

# Start the Next.js development server
npm run dev
```
*The web portal is now live at `http://localhost:3000`. Open it in your browser, click "Login with GitHub", and you will be securely redirected to your dashboard.*
