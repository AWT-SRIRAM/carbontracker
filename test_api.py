import unittest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, seed_database
from database import get_db
from models import Base
import models

# Set up an isolated in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency in the app
app.dependency_overrides[get_db] = override_get_db

# Create tables and seed data
Base.metadata.create_all(bind=engine)
db = TestingSessionLocal()
seed_database(db)
db.close()

client = TestClient(app)


class TestEcoTraceAPI(unittest.TestCase):
    def setUp(self):
        # Clean up users, profiles, and logs before each test
        self.db = TestingSessionLocal()
        self.db.query(models.DailyLog).delete()
        self.db.query(models.CarbonProfile).delete()
        self.db.query(models.User).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_create_and_get_users(self):
        """Test user registration and listing."""
        # Create user
        payload = {"name": "Test User", "email": "test@example.com"}
        response = client.post("/api/users", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Test User")
        self.assertEqual(data["email"], "test@example.com")
        self.assertIn("id", data)
        user_id = data["id"]

        # Duplicate email should return the existing user (for demo ease)
        response_dup = client.post("/api/users", json=payload)
        self.assertEqual(response_dup.status_code, 201)
        self.assertEqual(response_dup.json()["id"], user_id)

        # Get list
        response_list = client.get("/api/users")
        self.assertEqual(response_list.status_code, 200)
        users = response_list.json()
        self.assertGreaterEqual(len(users), 1)
        self.assertEqual(users[0]["email"], "test@example.com")

    def test_baseline_profile_flow(self):
        """Test onboarding and fetching carbon baseline profiles."""
        # Create user first
        user_payload = {"name": "Onboard User", "email": "onboard@example.com"}
        user_res = client.post("/api/users", json=user_payload)
        user_id = user_res.json()["id"]

        # Try to fetch non-existent profile
        profile_res = client.get(f"/api/profile/baseline?user_id={user_id}")
        self.assertEqual(profile_res.status_code, 404)

        # Create baseline profile
        profile_payload = {
            "housing_electricity_kwh": 350.0,
            "housing_gas_kwh": 150.0,
            "transport_car_km": 100.0,
            "transport_car_type": "hybrid",
            "transport_public_hours": 3.0,
            "diet_type": "vegetarian",
            "shopping_frequency": "moderate",
            "reduction_goal_percentage": 25.0
        }
        create_res = client.post(f"/api/profile/baseline?user_id={user_id}", json=profile_payload)
        self.assertEqual(create_res.status_code, 200)
        data = create_res.json()
        self.assertEqual(data["user_id"], user_id)
        self.assertEqual(data["reduction_goal_percentage"], 25.0)

        # Retrieve again and verify
        get_res = client.get(f"/api/profile/baseline?user_id={user_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["transport_car_type"], "hybrid")

    def test_get_actions(self):
        """Test fetching baseline seeded carbon offset activities catalog."""
        response = client.get("/api/actions")
        self.assertEqual(response.status_code, 200)
        actions = response.json()
        self.assertGreaterEqual(len(actions), 1)
        # Check standard item is seeded
        titles = [act["title"] for act in actions]
        self.assertIn("Eat a Vegan Meal", titles)

    def test_daily_logs_flow(self):
        """Test logging actions, listing logs, duplicate upserts, deleting, and dashboard calculations."""
        # Setup user
        user_res = client.post("/api/users", json={"name": "Log User", "email": "log@example.com"})
        user_id = user_res.json()["id"]

        # Setup baseline
        client.post(f"/api/profile/baseline?user_id={user_id}", json={
            "housing_electricity_kwh": 100.0,
            "housing_gas_kwh": 50.0,
            "transport_car_km": 50.0,
            "transport_car_type": "gasoline",
            "transport_public_hours": 2.0,
            "diet_type": "moderate_meat",
            "shopping_frequency": "moderate",
            "reduction_goal_percentage": 10.0
        })

        # Fetch action item ID (e.g. Eat a Vegan Meal)
        actions = client.get("/api/actions").json()
        vegan_action = next(a for a in actions if a["title"] == "Eat a Vegan Meal")
        action_id = vegan_action["id"]

        # Post daily action log
        today_str = date.today().strftime("%Y-%m-%d")
        log_payload = {
            "action_id": action_id,
            "logged_date": today_str,
            "quantity": 2.0
        }
        log_res = client.post(f"/api/logs?user_id={user_id}", json=log_payload)
        self.assertEqual(log_res.status_code, 201)
        self.assertEqual(log_res.json()["quantity"], 2.0)

        # Duplicate logs on same day should upsert (add quantity)
        log_res_dup = client.post(f"/api/logs?user_id={user_id}", json=log_payload)
        self.assertEqual(log_res_dup.status_code, 201)
        self.assertEqual(log_res_dup.json()["quantity"], 4.0)

        # Get logs list
        logs_list_res = client.get(f"/api/logs?user_id={user_id}")
        self.assertEqual(logs_list_res.status_code, 200)
        logs = logs_list_res.json()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["quantity"], 4.0)
        log_id = logs[0]["id"]

        # Verify dashboard statistics
        dash_res = client.get(f"/api/analytics/dashboard?user_id={user_id}")
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.json()
        self.assertTrue(dash_data["has_profile"])
        # Expected savings: 4 meals * 1.50 kg = 6.00 kg
        self.assertEqual(dash_data["logged_savings_co2_kg_monthly"], 6.00)
        self.assertGreater(dash_data["baseline_total_co2_kg_monthly"], 0.0)

        # Export CSV endpoint
        csv_res = client.get(f"/api/logs/export?user_id={user_id}")
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn("text/csv", csv_res.headers["content-type"])
        self.assertIn("Net CO2 Saved (kg)", csv_res.text)

        # Delete log
        del_res = client.delete(f"/api/logs/{log_id}?user_id={user_id}")
        self.assertEqual(del_res.status_code, 204) # HTTP 204 No Content

        # Verify log is gone
        logs_after = client.get(f"/api/logs?user_id={user_id}").json()
        self.assertEqual(len(logs_after), 0)


if __name__ == "__main__":
    unittest.main()
