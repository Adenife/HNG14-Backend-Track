# HNG Stage 1 Backend: Profile Intelligence & Persistence API

This project is a high-performance profile management system built with FastAPI. It enriches user identities by concurrently fetching data from three external demographic APIs, applies custom classification logic, and ensures idempotent data persistence through an in-memory storage system.

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

## 📌 API Specification

#### 1. Create Profile

`POST /api/profiles`

Processes a name and fetches data from Genderize, Agify, and Nationalize APIs.

Request Body:

#### Query Parameters

| Parameter | Type | Required | Description |

| :-------- | :----- | :------- | :------------------------------ |
`

| `name` | string | Yes | The name to be classified. |

#### 2. Get Single Profile

`GET /api/profiles/{id}`

Retrieves a stored profile by its UUID v7.

#### 3. Get All Profiles (Filtered)

`GET /api/profiles?gender=male&country_id=NG&age_group=adult`

Returns a list of all profiles with optional case-insensitive filtering.

#### 4. Delete Profile

`DELETE /api/profiles/{id}`

Removes a profile from the persistent storage.

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
