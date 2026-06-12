"""
Main application entry point.
Initializes FastAPI, creates database tables, seeds actions, and mounts static assets.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine, SessionLocal
import models
from routes import router

# Pre-defined actions to seed the database on startup
DEFAULT_ACTIONS = [
    {
        "title": "Commute by Bike or Walk",
        "description": "Walked or biked instead of driving. Savings calculated per kilometer.",
        "category": "Transport",
        "co2_savings_kg": 0.19
    },
    {
        "title": "Use Public Transit",
        "description": "Took a bus, train, or subway instead of driving a personal car. Savings per kilometer.",
        "category": "Transport",
        "co2_savings_kg": 0.15
    },
    {
        "title": "Eat a Vegan Meal",
        "description": "Consumed a fully plant-based meal. Savings calculated per meal.",
        "category": "Food",
        "co2_savings_kg": 1.50
    },
    {
        "title": "Eat a Vegetarian Meal",
        "description": "Consumed a meat-free meal. Savings calculated per meal.",
        "category": "Food",
        "co2_savings_kg": 1.00
    },
    {
        "title": "Hang Dry Laundry",
        "description": "Air-dried a load of clothing instead of running an electric dryer. Savings per load.",
        "category": "Energy",
        "co2_savings_kg": 0.60
    },
    {
        "title": "Eco-adjust Thermostat",
        "description": "Lowered heating or raised cooling settings by at least 2°C for the day. Savings per day.",
        "category": "Energy",
        "co2_savings_kg": 0.80
    },
    {
        "title": "Buy Pre-owned Item",
        "description": "Purchased clothing, furniture, or electronics second-hand rather than new. Savings per item.",
        "category": "Consumption",
        "co2_savings_kg": 10.00
    },
    {
        "title": "Compost Waste",
        "description": "Composted organic food scraps and waste instead of sending to a landfill. Savings per kg.",
        "category": "Waste",
        "co2_savings_kg": 0.50
    }
]


def seed_database(db):
    """Seed default action catalog into database if empty."""
    for act in DEFAULT_ACTIONS:
        existing = db.query(models.ActionItem).filter(models.ActionItem.title == act["title"]).first()
        if not existing:
            action_item = models.ActionItem(
                title=act["title"],
                description=act["description"],
                category=act["category"],
                co2_savings_kg=act["co2_savings_kg"]
            )
            db.add(action_item)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure static directories exist
    os.makedirs("static", exist_ok=True)
    
    # Initialize Database Tables
    models.Base.metadata.create_all(bind=engine)
    
    # Run automatic SQLite migration if reduction_goal_percentage is missing
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(carbon_profiles)")).fetchall()
            columns = [row[1] for row in result]
            if "reduction_goal_percentage" not in columns:
                conn.execute(text("ALTER TABLE carbon_profiles ADD COLUMN reduction_goal_percentage FLOAT DEFAULT 20.0"))
                conn.commit()
    except Exception as e:
        print("Migration error details:", e)
    
    # Seed Data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
        
    yield


app = FastAPI(
    title="EcoTrace - Carbon Footprint Analytics API",
    description="Backend microservice to log daily footprint reductions and calculate personalized footprints.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for developer testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(router)

# Serve Frontend static assets
# If file exists, mount static folder.
@app.get("/")
def read_index():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to EcoTrace. Please place index.html in the static/ folder to view the frontend dashboard."}

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
