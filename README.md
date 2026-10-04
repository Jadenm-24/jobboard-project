# Job Board API

A RESTful Job Board API built with FastAPI.  
Implements JWT authentication and role-based access control (Admin/User).

## Tech Stack

- Python
- FastAPI
- JWT (python-jose)
- Passlib (bcrypt)
- Uvicorn

## Features

- User registration
- User login with JWT
- Protected routes
- Admin-only job creation, update, and deletion
- Public job listings

## Run with Docker

Make sure Docker Desktop is installed and running. From the project folder, the folder containing the Dockerfile, run:

docker build -t job-board-api .
docker run --rm -p 8000:8000 job-board-api

## Run with Python

1. Create virtual environment

python -m venv venv
source venv/bin/activate

2. Install dependencies

pip install -r requirements.txt

3. Run the server

uvicorn app.main:app --reload

## AI-Assisted Development

Used AI tools to help structure the project and stay on track while developing it. Used the process as an opportunity to learn and understand the concepts involved.

## API Docs

Available at:

http://127.0.0.1:8000/docs
