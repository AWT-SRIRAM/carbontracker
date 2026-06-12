import unittest
from datetime import date
import sys
import os

# Add workspace directory to path if running directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import CarbonProfile, DailyLog, ActionItem
from analytics import (
    calculate_baseline,
    calculate_savings,
    generate_personalized_insights,
    calculate_unlocked_badges
)


class TestEcoTraceAnalytics(unittest.TestCase):
    def test_calculate_baseline(self):
        """Test baseline carbon emissions breakdown calculations."""
        profile = CarbonProfile(
            housing_electricity_kwh=100.0,
            housing_gas_kwh=50.0,
            transport_car_km=100.0,
            transport_car_type="gasoline",
            transport_public_hours=5.0,
            diet_type="vegan",
            shopping_frequency="low"
        )
        baseline = calculate_baseline(profile)
        # Expected Energy: 100 * 0.40 + 50 * 0.18 = 40.0 + 9.0 = 49.0
        # Expected Transport: (100 * 4.33 * 0.19) + (5 * 4.33 * 1.20) = 82.27 + 25.98 = 108.25
        # Expected Food: 80.0
        # Expected Consumption: 100.0
        self.assertEqual(baseline["Energy"], 49.0)
        self.assertEqual(baseline["Transport"], 108.25)
        self.assertEqual(baseline["Food"], 80.0)
        self.assertEqual(baseline["Consumption"], 100.0)

    def test_calculate_savings(self):
        """Test carbon savings log summation calculations."""
        action1 = ActionItem(category="Transport", co2_savings_kg=0.19)
        action2 = ActionItem(category="Food", co2_savings_kg=1.50)

        logs = [
            DailyLog(id=1, action=action1, quantity=10.0, logged_date=date.today()),
            DailyLog(id=2, action=action2, quantity=4.0, logged_date=date.today())
        ]
        
        savings = calculate_savings(logs)
        # Expected total: 10 * 0.19 + 4 * 1.50 = 1.9 + 6.0 = 7.9
        self.assertEqual(savings["total_savings_kg"], 7.9)
        self.assertEqual(savings["category_savings"]["Transport"], 1.9)
        self.assertEqual(savings["category_savings"]["Food"], 6.0)
        self.assertEqual(savings["category_savings"]["Energy"], 0.0)

    def test_calculate_savings_empty(self):
        """Test savings calculation with an empty logs list."""
        savings = calculate_savings([])
        self.assertEqual(savings["total_savings_kg"], 0.0)
        self.assertEqual(savings["category_savings"]["Transport"], 0.0)

    def test_unlocked_badges_eco_champion(self):
        """Test unlocking the Eco Champion badge."""
        profile = CarbonProfile(reduction_goal_percentage=10.0)
        action = ActionItem(category="Transport", co2_savings_kg=1.0)
        logs = [DailyLog(id=1, action=action, quantity=15.0, logged_date=date.today())]
        
        # 15% savings compared to baseline, which exceeds the 10% goal
        badges = calculate_unlocked_badges(profile, logs, baseline_total=100.0, total_savings=15.0)
        self.assertIn("Eco Champion", badges)

        # Savings below goal (5% savings vs 10% goal) should remain locked
        badges_locked = calculate_unlocked_badges(profile, logs, baseline_total=100.0, total_savings=5.0)
        self.assertNotIn("Eco Champion", badges_locked)

    def test_unlocked_badges_transit_hero(self):
        """Test unlocking the Transit Hero badge."""
        profile = CarbonProfile(reduction_goal_percentage=20.0)
        action_transit = ActionItem(category="Transport", co2_savings_kg=0.15)
        # Log 35 km of transit (threshold is 30 km)
        logs = [DailyLog(id=1, action=action_transit, quantity=35.0, logged_date=date.today())]
        
        badges = calculate_unlocked_badges(profile, logs, baseline_total=200.0, total_savings=5.25)
        self.assertIn("Transit Hero", badges)

    def test_unlocked_badges_plant_powered(self):
        """Test unlocking the Plant-Powered badge."""
        profile = CarbonProfile(reduction_goal_percentage=20.0)
        action_meal = ActionItem(category="Food", co2_savings_kg=1.5)
        # Log 12 meals (threshold is 10 meals)
        logs = [DailyLog(id=1, action=action_meal, quantity=12.0, logged_date=date.today())]
        
        badges = calculate_unlocked_badges(profile, logs, baseline_total=200.0, total_savings=18.0)
        self.assertIn("Plant-Powered", badges)


if __name__ == "__main__":
    unittest.main()
