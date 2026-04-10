# HNG Stage 0 Backend: Name Classification API

This project is a RESTful API built with **Python (FastAPI)** that classifies names based on gender data retrieved from the Genderize.io API. It processes the data to determine classification confidence and provides standardized JSON responses.

## 🚀 Live Demo

**Public API URL:** `[INSERT_YOUR_DEPLOYED_URL_HERE]`  
**Endpoint:** `GET /api/classify?name=<name>`

---

## 🛠️ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Language:** Python 3.9+
- **HTTP Client:** [HTTPX](https://www.python-httpx.org/) (Asynchronous)
- **Deployment:** [Render / Railway / Fly.io]
- **CORS:** Enabled for all origins (`*`)

---

## 📌 API Specification

### GET `/api/classify`

Takes a name as a query parameter and returns processed gender classification data.

#### Query Parameters

| Parameter | Type | Required | Description |

| :-------- | :----- | :------- | :------------------------------ |
`

| `name` | string | Yes | The name to be classified. |

#### Successful Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "name": "Peter",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-10T12:00:00Z"
  }
}
```

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
uv add fastapi uvicorn httpx

```

#### 4. Directory Structure

Your project should look like this:

```
hng_backend_stage0/
├── main.py             # Main API logic
├── requirements.txt    # Project dependencies
├── .gitignore          # Files to ignore (venv, __pycache__)
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
