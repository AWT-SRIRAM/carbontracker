"""
Analytics module using Pandas and NumPy to compute carbon footprints and reduction insights.
"""

from typing import List, Dict, Any
import pandas as pd
import numpy as np
from models import CarbonProfile, DailyLog, ActionItem

# Emission Factors (expressed in kg CO2 per unit)
CO2_FACTORS = {
    "electricity_kwh": 0.40,  # kg CO2 per kWh
    "gas_kwh": 0.18,          # kg CO2 per kWh
    "public_transit_hour": 1.20,  # kg CO2 per hour (assuming 30 km/h average at 0.04 kg CO2/km)
    "car": {
        "gasoline": 0.19,  # kg CO2 per km
        "diesel": 0.17,
        "hybrid": 0.10,
        "electric": 0.05
    },
    "diet": {
        "vegan": 80.0,       # kg CO2 per month
        "vegetarian": 120.0,
        "moderate_meat": 200.0,
        "high_meat": 300.0
    },
    "shopping": {
        "low": 100.0,        # kg CO2 per month
        "moderate": 220.0,
        "high": 400.0
    }
}


def calculate_baseline(profile: CarbonProfile) -> Dict[str, float]:
    """
    Calculate baseline monthly carbon footprint (in kg CO2) broken down by category.
    """
    # 1. Housing energy
    electricity_co2 = profile.housing_electricity_kwh * CO2_FACTORS["electricity_kwh"]
    gas_co2 = profile.housing_gas_kwh * CO2_FACTORS["gas_kwh"]
    housing_total = electricity_co2 + gas_co2

    # 2. Transportation
    # Convert weekly car travel to monthly (average 4.33 weeks per month)
    car_factor = CO2_FACTORS["car"].get(profile.transport_car_type.lower(), CO2_FACTORS["car"]["gasoline"])
    car_co2 = profile.transport_car_km * 4.33 * car_factor
    
    # Convert weekly public transit to monthly
    public_co2 = profile.transport_public_hours * 4.33 * CO2_FACTORS["public_transit_hour"]
    transport_total = car_co2 + public_co2

    # 3. Diet
    diet_total = CO2_FACTORS["diet"].get(profile.diet_type.lower(), CO2_FACTORS["diet"]["moderate_meat"])

    # 4. Shopping
    shopping_total = CO2_FACTORS["shopping"].get(profile.shopping_frequency.lower(), CO2_FACTORS["shopping"]["moderate"])

    return {
        "Energy": round(housing_total, 2),
        "Transport": round(transport_total, 2),
        "Food": round(diet_total, 2),
        "Consumption": round(shopping_total, 2)
    }


def calculate_savings(logs: List[DailyLog]) -> Dict[str, Any]:
    """
    Calculate carbon savings from logs using Pandas.
    Returns monthly savings and category breakdown.
    """
    if not logs:
        return {
            "total_savings_kg": 0.0,
            "category_savings": {"Energy": 0.0, "Transport": 0.0, "Food": 0.0, "Waste": 0.0}
        }

    # Extract log data for Pandas DataFrame
    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "date": log.logged_date,
            "category": log.action.category,
            "co2_savings_kg": log.action.co2_savings_kg,
            "quantity": log.quantity,
            "net_savings": log.quantity * log.action.co2_savings_kg
        })

    df = pd.DataFrame(data)

    # Calculate total savings
    total_savings = float(df["net_savings"].sum())

    # Calculate savings by category
    category_grouped = df.groupby("category")["net_savings"].sum().to_dict()

    # Fill default categories if missing
    categories = ["Energy", "Transport", "Food", "Waste"]
    category_savings = {cat: float(category_grouped.get(cat, 0.0)) for cat in categories}

    return {
        "total_savings_kg": round(total_savings, 2),
        "category_savings": category_savings
    }


def generate_personalized_insights(profile: CarbonProfile, baseline_breakdown: Dict[str, float], savings_data: Dict[str, Any]) -> List[str]:
    """
    Generate dynamic suggestions and recommendations based on the user's footprint data.
    """
    insights = []

    # 1. Analyze baseline breakdown
    total_baseline = sum(baseline_breakdown.values())
    if total_baseline == 0:
        return ["Please complete your onboarding profile to receive carbon footprint insights!"]

    # Identify the highest emission category
    highest_cat = max(baseline_breakdown, key=baseline_breakdown.get)
    highest_val = baseline_breakdown[highest_cat]
    percentage = (highest_val / total_baseline) * 100

    insights.append(
        f"Your highest footprint category is **{highest_cat}**, making up **{percentage:.1f}%** of your total baseline profile."
    )

    # 2. Category-specific suggestions
    if highest_cat == "Transport":
        if profile.transport_car_type == "gasoline" or profile.transport_car_type == "diesel":
            insights.append("Consider carpooling, using public transit, or upgrading to a hybrid/electric vehicle to reduce transport emissions.")
        insights.append("Tip: Replacing just one driving trip a week with walking, biking, or transit saves significant CO2.")
    
    elif highest_cat == "Energy":
        if profile.housing_electricity_kwh > 400:
            insights.append("Your electricity usage is higher than average. Switching to LED lightbulbs and energy-efficient appliances can cut utility emissions by up to 20%.")
        if profile.housing_gas_kwh > 300:
            insights.append("Reducing heating thermostat settings by 2°C in winter can save up to 10% on natural gas carbon footprint.")
        insights.append("Tip: Unplug idle appliances and chargers to prevent vampire power draw.")
        
    elif highest_cat == "Food":
        if profile.diet_type in ["high_meat", "moderate_meat"]:
            insights.append("Adopting a 'Meatless Monday' or a vegetarian diet just 2 days a week will lower your food footprint by over 15%.")
        insights.append("Tip: Try to buy local, seasonal produce to minimize food transportation mileage (food miles).")

    elif highest_cat == "Consumption":
        if profile.shopping_frequency == "high":
            insights.append("Your shopping footprint is high. Try checking local thrift stores or peer-to-peer platforms for second-hand items before buying new ones.")
        insights.append("Tip: Embrace minimalism by focusing on high-quality, long-lasting products.")

    # 3. Savings achievements
    total_saved = savings_data["total_savings_kg"]
    if total_saved > 0:
        insights.append(f"Fantastic job! You saved **{total_saved:.1f} kg of CO2** this month. That is equivalent to planting **{total_saved / 2.0:.1f}** tree saplings (growth over 10 years)!")
    else:
        insights.append("You haven't logged any eco-friendly actions yet this month. Start with small steps like eating a vegetarian meal or hang-drying laundry today!")

    # 4. Goal progress insight
    goal = getattr(profile, "reduction_goal_percentage", 20.0)
    if total_baseline > 0:
        percent_reduced = (total_saved / total_baseline) * 100
        insights.append(f"You have reduced your footprint by **{percent_reduced:.1f}%** this month, targeting a custom goal of **{goal:.1f}%**.")
        if percent_reduced >= goal:
            insights.append("Congratulations! You've achieved your customized footprint reduction target for this month! Keep up the amazing work.")
        else:
            remaining = goal - percent_reduced
            insights.append(f"You are **{remaining:.1f}%** away from achieving your customized monthly reduction target of {goal:.1f}%.")

    return insights


def calculate_unlocked_badges(profile: CarbonProfile, logs: List[DailyLog], baseline_total: float, total_savings: float) -> List[str]:
    """
    Calculate gamified badges based on user's logged actions and baseline profile.
    """
    badges = []
    if not logs:
        return badges

    # Extract log details
    data = []
    for log in logs:
        data.append({
            "category": log.action.category,
            "title": log.action.title,
            "quantity": log.quantity
        })
    df = pd.DataFrame(data)

    # 1. Transit Hero: Commuting via green methods (Bike/Walk or Transit) > 30 units (km)
    transport_logs = df[df["category"] == "Transport"]
    if not transport_logs.empty:
        total_transport_qty = transport_logs["quantity"].sum()
        if total_transport_qty >= 30:
            badges.append("Transit Hero")

    # 2. Plant-Powered: Eaten 10 or more vegetarian/vegan meals
    food_logs = df[df["category"] == "Food"]
    if not food_logs.empty:
        total_food_qty = food_logs["quantity"].sum()
        if total_food_qty >= 10:
            badges.append("Plant-Powered")

    # 3. Energy Saver: Logged energy-saving activities 5 or more times
    energy_logs = df[df["category"] == "Energy"]
    if not energy_logs.empty:
        total_energy_qty = energy_logs["quantity"].sum()
        if total_energy_qty >= 5:
            badges.append("Energy Saver")

    # 4. Eco Champion: Achieved or exceeded the user's customized reduction goal
    goal = getattr(profile, "reduction_goal_percentage", 20.0)
    if baseline_total > 0:
        percent_reduced = (total_savings / baseline_total) * 100
        if percent_reduced >= goal:
            badges.append("Eco Champion")

    return badges
