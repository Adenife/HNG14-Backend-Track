# HNG Stage 2 Backend: Natural Language Querying & Seeding

This stage focuses on enhancing the Profile API with automated data seeding and a Natural Language Query (NLQ) engine that allows users to search for profiles using plain English.

## 🚀 Live Demo

**Public API URL:** `[INSERT_YOUR_DEPLOYED_URL_HERE]`  
**API Documentation (Swagger):** `[INSERT_YOUR_DEPLOYED_URL_HERE]/docs`

---

## 🛠️ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Language:** Python 3.9+
- **HTTP Client:** [HTTPX](https://www.python-httpx.org/) (Asynchronous)
- **Deployment:** [Render / Railway / Fly.io]
- **CORS:** Enabled for all origins (`*`)

---

## 🧠 Natural Language Parsing (NLQ) Approach

The parser follows a Pattern-Matching Strategy rather than using heavy AI models. This ensures the search is fast, deterministic, and easily debuggable.

#### 1. Keyword Mapping & Extraction

The logic uses a series of Regular Expressions (Regex) to extract intent from the search string:

| Keyword/Pattern | Captured Value | Logic / Filter Mapping |

|-----------------|----------------|------------------------|

| `(?:from\|in)\s+([a-zA-Z\s]{2,})` | Country Name/Code | Mapped via pycountry to a 2-letter ISO code (country_id). |

| `(?:male\|female\|other)` | Gender | Normalized to lowercase and mapped to gender. |

| `\d+ (standalone)` | Age | If one number is found, it is treated as a specific age. |

| `(\d+)\s+to\s+(\d+)` | Age Range | Mapped to min_age and max_age. |

#### 2. The Logic Flow

- Sanitization: The query is converted to lowercase and stripped of extra whitespace.

- Entity Recognition: The engine runs regex patterns for countries first. It uses the pycountry.countries.lookup() method to handle both full names ("Nigeria") and codes ("NG") interchangeably.

- Numeric Analysis: It scans for numbers to determine age boundaries.

- Filter Assembly: Extracted values are packed into a filters dictionary.

- Fallback: If no recognizable keywords are found, it returns an empty filter set (fetching all profiles by default) or a 400 error if the status is explicitly set to "error".

---

## ⚠️ Limitations & Edge Cases

While robust for standard queries, the following limitations apply:

#### 1. Linguistic Limitations

- Conjunctions: The parser does not handle complex "AND/OR" logic. A query like "Males from Kenya OR females from Nigeria" will likely only capture the last detected entities.

- Negation: It cannot handle negative constraints (e.g., "People who are NOT from Nigeria"). It will see "Nigeria" and filter for it.

- Stop-word interference: If a country name is also a common word that isn't preceded by "in" or "from," it may be missed.

#### 2. Edge Cases Left Out

- Ambiguous Abbreviations: Short 2-letter strings that aren't intended as country codes (e.g., "I am in in") may cause pycountry to return a LookupError, which the code catches and ignores.

- Multi-Country Queries: If a user enters two countries (e.g., "People in Kenya and Nigeria"), the current regex implementation typically captures the first match and ignores the rest.

- Non-English Input: The keywords (male, female, from, in) are hardcoded in English.

---

## 🚦 API Endpoints

| Method | Endpoint | Description |

|--------|----------|-------------|

| GET | `/api/seed-profiles` | Seeds the database with initial profile data from seed_profiles.json. |

| GET | `/api/profiles/search` | Performs NLQ search using search, page, and limit params. |

---

## 🛠️ Local Installation

#### Step 1: Clone the Repository

Open your terminal and run:

```
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

#### Step 2: Set Up a Virtual Environment

It is highly recommended to use a virtual environment to manage your dependencies.

```
uv init
```

#### Step 3: Install Dependencies

Install dependencies using uv:

```
uv add -r requirements.txt

```

#### 4. Directory Structure

Your project should look like this:

```
hng_backend_stage0/
├── main.py             # Main API logic
├── requirements.txt    # Project dependencies
├── .gitignore          # Files to ignore (venv, __pycache__)
├── app                 # main App logic
   ├── core             # contains main configration logic
   ├── models           # contains the schema logic
   ├── routers          # contains router logic
   ├── services         # contains logic for external services
   ├── utils            # contains utility services
└── README.md           # Project documentation
```

#### 5. Running the Application

To start the local development server, run:

```
uv run uvicorn main:app --reload
```

The --reload flag allows the server to restart automatically whenever you save changes to your code.

By default, the API will be accessible at: http://127.0.0.1:8000/docs

---

## License

[MIT](https://choosealicense.com/licenses/mit/)
