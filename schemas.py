"""
Pydantic schemas for request validation and response serialization.
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The user's display name.")
    email: EmailStr = Field(..., description="The user's email address.")


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class CarbonProfileCreate(BaseModel):
    housing_electricity_kwh: float = Field(0.0, ge=0.0, description="Monthly housing electricity usage in kWh.")
    housing_gas_kwh: float = Field(0.0, ge=0.0, description="Monthly housing natural gas usage in kWh.")
    transport_car_km: float = Field(0.0, ge=0.0, description="Weekly car travel distance in kilometers.")
    transport_car_type: str = Field("gasoline", description="Type of car: gasoline, diesel, hybrid, electric.")
    transport_public_hours: float = Field(0.0, ge=0.0, description="Weekly public transit travel duration in hours.")
    diet_type: str = Field("moderate_meat", description="Diet: vegan, vegetarian, moderate_meat, high_meat.")
    shopping_frequency: str = Field("moderate", description="Shopping volume: low, moderate, high.")
    reduction_goal_percentage: float = Field(20.0, ge=5.0, le=50.0, description="Carbon reduction goal target in percentage.")


class CarbonProfileResponse(BaseModel):
    id: int
    user_id: int
    housing_electricity_kwh: float
    housing_gas_kwh: float
    transport_car_km: float
    transport_car_type: str
    transport_public_hours: float
    diet_type: str
    shopping_frequency: str
    reduction_goal_percentage: float
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionItemResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    co2_savings_kg: float

    class Config:
        from_attributes = True


class DailyLogCreate(BaseModel):
    action_id: int = Field(..., description="The carbon-reducing action ID.")
    logged_date: date = Field(default_factory=date.today, description="The date the action occurred.")
    quantity: float = Field(1.0, ge=0.0, description="Quantity/occurrences of the action.")


class DailyLogResponse(BaseModel):
    id: int
    user_id: int
    action_id: int
    logged_date: date
    quantity: float
    created_at: datetime
    action: ActionItemResponse

    class Config:
        from_attributes = True


class CategoryEmissions(BaseModel):
    category: str
    co2_kg_monthly: float


class DashboardResponse(BaseModel):
    user_id: int
    has_profile: bool
    baseline_total_co2_kg_monthly: float
    category_baselines: List[CategoryEmissions]
    logged_savings_co2_kg_monthly: float
    actual_total_co2_kg_monthly: float
    reduction_goal_percentage: float = 20.0
    recent_logs: List[DailyLogResponse]
    insights: List[str]
    unlocked_badges: List[str] = []
