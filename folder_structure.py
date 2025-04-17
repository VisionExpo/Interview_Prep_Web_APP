import os

# Define the project folder structure
folders = [
    "backend/app/routes",
    "backend/app/models",
    "backend/app/services",
    "backend/app/utils",
    "backend/app/db",
    "frontend/src/components",
    "frontend/src/pages",
    "frontend/src/services",
    "frontend/src/utils",
    "media/local_cache",
    "media/uploads",
    "docs",
    "scripts"
]

# Files with default content
files = {
    "backend/requirements.txt": "fastapi\nuvicorn\npython-dotenv\npydantic\nrequests\ncassandra-driver",
    "backend/app/main.py": """
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
""",
    "frontend/package.json": """
{
  "name": "interview-prep-assistant-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-scripts": "4.0.3"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
""",
}

def create_folders():
    """Create all the necessary folders for the project"""
    for folder in folders:
        folder_path = os.path.join(os.getcwd(), folder)
        os.makedirs(folder_path, exist_ok=True)
        # Create __init__.py in Python package directories
        if folder.startswith('backend/app'):
            init_file = os.path.join(folder_path, '__init__.py')
            if not os.path.exists(init_file):
                open(init_file, 'a').close()

def create_files():
    """Create all the necessary files with their default content"""
    for file_path, content in files.items():
        full_path = os.path.join(os.getcwd(), file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)

def main():
    """Main function to set up the project structure"""
    print("Creating project structure...")
    create_folders()
    create_files()
    print("Project structure created successfully!")

if __name__ == "__main__":
    main()