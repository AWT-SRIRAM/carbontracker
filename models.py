"""
Database models for the Carbon Footprint Tracker (EcoTrace).
Adheres to Third Normal Form (3NF) to support users, profiles, carbon action items, and daily logs.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import ForeignKey, String, DateTime, Date, Integer, Float, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""
    pass


class User(Base):
    """
    Represents an application user.
    Stores core identity details without transitive dependencies.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    profile: Mapped[Optional["CarbonProfile"]] = relationship("CarbonProfile", back_populates="user", cascade="all, delete-orphan")
    logs: Mapped[List["DailyLog"]] = relationship("DailyLog", back_populates="user", cascade="all, delete-orphan")


class CarbonProfile(Base):
    """
    Stores a user's initial baseline carbon footprint parameters.
    Normalized to depend directly on user_id with zero transitive dependencies.
    """
    __tablename__ = "carbon_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Housing Metrics
    housing_electricity_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    housing_gas_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Transport Metrics
    transport_car_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transport_car_type: Mapped[str] = mapped_column(String(50), default="gasoline", nullable=False) # gasoline, diesel, hybrid, electric
    transport_public_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Diet and Consumption
    diet_type: Mapped[str] = mapped_column(String(50), default="moderate_meat", nullable=False) # vegan, vegetarian, moderate_meat, high_meat
    shopping_frequency: Mapped[str] = mapped_column(String(50), default="moderate", nullable=False) # low, moderate, high
    reduction_goal_percentage: Mapped[float] = mapped_column(Float, default=20.0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")


class ActionItem(Base):
    """
    Represents a carbon-saving activity a user can perform (e.g. Commute by Bike).
    Normalized catalog of actions with pre-calculated CO2 offset scores.
    """
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Transport, Energy, Food, Waste
    co2_savings_kg: Mapped[float] = mapped_column(Float, nullable=False)  # Savings per unit quantity

    # Relationships
    logs: Mapped[List["DailyLog"]] = relationship("DailyLog", back_populates="action")


class DailyLog(Base):
    """
    Tracks daily actions logged by users.
    Fact table referencing the User and ActionItem dimensions.
    """
    __tablename__ = "daily_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("action_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    logged_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Prevent duplicate action logs for the same user on the same date
    __table_args__ = (
        UniqueConstraint("user_id", "action_id", "logged_date", name="uq_user_action_date"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="logs")
    action: Mapped["ActionItem"] = relationship("ActionItem", back_populates="logs")
