# REDLINE Backend

## Project Overview
Redline is an Autonomous Contract Intelligence platform. This repository contains the FastAPI backend, which handles contract uploading, reviewing, risk analysis, and negotiation suggestions powered by AI (Gemini).

## Features
*   **Contract Upload:** Upload PDF or DOCX contracts and extract text.
*   **Contract Review:** AI-powered review of the contract content.
*   **Risk Analysis:** Identify potential risks, clauses, and calculate a risk score.
*   **Negotiation Suggestions:** Generate alternate clauses and negotiation points.
*   **Explainability:** Understand complex legal clauses in plain English.
*   **Authentication:** Secure user authentication using JWT and bcrypt.

## Tech Stack
*   **Framework:** FastAPI (Python 3.10+)
*   **Database:** PostgreSQL
*   **ORM:** SQLAlchemy
*   **Migrations:** Alembic
*   **AI Integration:** Google Gemini API
*   **Containerization:** Docker & Docker Compose

## Installation Steps
1.  Clone the repository:
    ```bash
    git clone https://github.com/K-Gopi2007/REDLINE-BACKEND.git
    cd REDLINE-BACKEND
    ```
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Environment Variables
Create a `.env` file in the root directory based on `.env.example`:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/redline
SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
```

## Database Setup
Ensure you have a running PostgreSQL instance matching your `DATABASE_URL`.
If using Docker, you can start the database using:
```bash
docker-compose up db -d
```

## Alembic Migration Commands
To apply the latest database migrations:
```bash
alembic upgrade head
```
To create a new migration after updating models:
```bash
alembic revision --autogenerate -m "Description"
```

## Run Commands
To run the FastAPI server locally for development:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Or, to run the entire stack (web + db) with Docker Compose:
```bash
docker-compose up --build
```

## API Documentation
Once the server is running, the interactive API documentation (Swagger UI) is available at:
[http://localhost:8000/docs](http://localhost:8000/docs)
