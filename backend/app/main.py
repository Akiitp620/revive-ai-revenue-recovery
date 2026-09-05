from app.api import endpoints
from app.schemas.base import HealthCheckResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS for local development with Next.js
origins = ["http://localhost:3000", "http://localhost:3001"]
if settings.FRONTEND_URL:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    return HealthCheckResponse(status="ok")


app.include_router(endpoints.router, prefix="/api/v1")
