from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_routes import router
from config import API_INFO

# Create FastAPI app instance
app = FastAPI(
    title=API_INFO["title"],
    version=API_INFO["version"]
)

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
