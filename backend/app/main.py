"""
LuxeStay Hotel Management API — Application entry point.
FastAPI application with lifespan management, middleware, and exception handlers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import (
    connect_to_mongo,
    close_mongo_connection,
    get_user_collection,
    get_room_collection,
    get_booking_collection,
    create_indexes,
)
from app.routes import auth, rooms, bookings, dashboard
from app.utils.security import get_password_hash
from app.middleware.logging import RequestLoggingMiddleware
from app.core.exceptions import register_exception_handlers
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("LuxeStayAPI")


async def seed_database():
    """
    Seed the database with default admin user, rooms, and bookings
    if the respective collections are empty. Safe to run on every startup.
    """
    try:
        users_col = get_user_collection()
        rooms_col = get_room_collection()
        bookings_col = get_booking_collection()

        # 1. Seed default Admin user
        admin_count = await users_col.count_documents({"email": "admin@luxestay.com"})
        if admin_count == 0:
            hashed_pw = get_password_hash("admin123")
            await users_col.insert_one({
                "email": "admin@luxestay.com",
                "hashed_password": hashed_pw,
                "role": "admin",
                "name": "LuxeStay Administrator",
                "created_at": datetime.now(timezone.utc),
            })
            logger.info("Seeded default administrator: admin@luxestay.com / admin123")

        # 2. Rooms and Bookings (Removed per requirements)
        # We start with 0 rooms and allow staff to create them manually.
    except Exception as e:
        logger.error(f"Error seeding database: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — connect to DB, create indexes, seed data on startup."""
    # Startup
    await connect_to_mongo()
    await create_indexes()
    await seed_database()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="LuxeStay Hotel Management API",
    description="Backend services for room booking, reservation dashboard, and staff management.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────
# Request logging (added first so it wraps all other middleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS configuration to allow frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
# Mount static files for Aadhaar uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Exception Handlers ─────────────────────────────────────────────
register_exception_handlers(app)

# ── Routes ──────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/", tags=["Health"])
def read_root():
    """Health check endpoint."""
    return {
        "message": "Welcome to LuxeStay Hotel Management API!",
        "docs_url": "/docs",
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Explicit health check endpoint for monitoring."""
    return {"status": "ok"}
