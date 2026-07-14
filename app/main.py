from fastapi import FastAPI
from app.routes import jobs, applications, users, auth
from dotenv import load_dotenv
from app.database import create_tables

app = FastAPI()
load_dotenv()
create_tables()

app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(users.router)
app.include_router(auth.router)
