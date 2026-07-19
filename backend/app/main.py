from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import (
    budget_routes, category_routes, dashboard_routes, demo_routes, forecast_routes,
    goal_routes, import_routes, investment_routes, profile_routes, report_routes,
    settings_routes, transaction_routes,
)
from app.core.config import get_settings
from app.database.session import Base, SessionLocal, engine
from app.middleware.rate_limit import limiter
from app.seed.seed_defaults import seed_default_category_rules

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local/dev convenience: create tables directly. In staging/production,
    # Alembic migrations (backend/alembic/) are the source of truth --
    # see DEPLOYMENT_GUIDE.md.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_category_rules(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="ExpenseCast: Intelligent Expense Tracking and Financial Forecasting Using Deep Learning-Based LSTM",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Ensures unhandled errors never leak internal details (stack traces,
    file paths, query text) to the client."""
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred. Please try again."})


app.include_router(profile_routes.router)
app.include_router(transaction_routes.router)
app.include_router(category_routes.router)
app.include_router(budget_routes.router)
app.include_router(goal_routes.router)
app.include_router(investment_routes.router)
app.include_router(import_routes.router)
app.include_router(forecast_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(report_routes.router)
app.include_router(settings_routes.router)
app.include_router(demo_routes.router)


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "status": "running", "environment": settings.ENVIRONMENT}


@app.get("/health")
def health():
    return {"status": "ok"}
