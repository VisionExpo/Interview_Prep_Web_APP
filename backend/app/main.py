
from fastapi import FastAPI
from backend.app.routes import user_routes, media_routes, interview_routes, job_routes

app = FastAPI()

app.include_router(user_routes.router)
app.include_router(media_routes.router)
app.include_router(interview_routes.router)
app.include_router(job_routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Interview Preparation Assistant API!"}
