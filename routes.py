"""
API Routes for EcoTrace.
Handles Users, Profiles, Daily logs, and Analytics endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from datetime import date

from database import get_db
import models
import schemas
import analytics

router = APIRouter(prefix="/api")


# --- USER ENDPOINTS ---

@router.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user profile."""
    # Check if user already exists
    existing = db.execute(select(models.User).where(models.User.email == payload.email)).scalar_one_or_none()
    if existing:
        return existing  # Return existing user for ease of demo logging
    
    new_user = models.User(name=payload.name, email=payload.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users", response_model=List[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    """List all users (useful for user switcher in demo)."""
    users = db.execute(select(models.User)).scalars().all()
    return list(users)


# --- CARBON PROFILE ENDPOINTS ---

@router.post("/profile/baseline", response_model=schemas.CarbonProfileResponse)
def save_profile_baseline(user_id: int, payload: schemas.CarbonProfileCreate, db: Session = Depends(get_db)):
    """Create or update the user's initial baseline carbon profile."""
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    profile = db.execute(select(models.CarbonProfile).where(models.CarbonProfile.user_id == user_id)).scalar_one_or_none()
    
    if profile:
        # Update existing
        for key, val in payload.model_dump().items():
            setattr(profile, key, val)
    else:
        # Create new
        profile = models.CarbonProfile(user_id=user_id, **payload.model_dump())
        db.add(profile)
        
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile/baseline", response_model=schemas.CarbonProfileResponse)
def get_profile_baseline(user_id: int, db: Session = Depends(get_db)):
    """Retrieve the user's baseline carbon profile."""
    profile = db.execute(select(models.CarbonProfile).where(models.CarbonProfile.user_id == user_id)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Baseline profile not completed yet.")
    return profile


# --- ACTIONS LOG ENDPOINTS ---

@router.get("/actions", response_model=List[schemas.ActionItemResponse])
def get_action_items(db: Session = Depends(get_db)):
    """List all standard carbon-reducing actions."""
    actions = db.execute(select(models.ActionItem)).scalars().all()
    return list(actions)


@router.post("/logs", response_model=schemas.DailyLogResponse, status_code=status.HTTP_201_CREATED)
def log_daily_action(user_id: int, payload: schemas.DailyLogCreate, db: Session = Depends(get_db)):
    """Log a daily carbon-reducing action. Upserts if same user, action, and date."""
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    action = db.get(models.ActionItem, payload.action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action item not found.")

    # Check for existing log on this day to upsert
    existing_log = db.execute(
        select(models.DailyLog).where(
            models.DailyLog.user_id == user_id,
            models.DailyLog.action_id == payload.action_id,
            models.DailyLog.logged_date == payload.logged_date
        )
    ).scalar_one_or_none()

    if existing_log:
        existing_log.quantity += payload.quantity
        db.commit()
        db.refresh(existing_log)
        return existing_log

    new_log = models.DailyLog(
        user_id=user_id,
        action_id=payload.action_id,
        logged_date=payload.logged_date,
        quantity=payload.quantity
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/logs", response_model=List[schemas.DailyLogResponse])
def get_user_logs(user_id: int, db: Session = Depends(get_db)):
    """List all logged daily activities for a user."""
    logs = db.execute(
        select(models.DailyLog)
        .where(models.DailyLog.user_id == user_id)
        .order_by(models.DailyLog.logged_date.desc(), models.DailyLog.created_at.desc())
    ).scalars().all()
    return list(logs)


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log_entry(log_id: int, user_id: int, db: Session = Depends(get_db)):
    """Delete a daily log entry."""
    log = db.get(models.DailyLog, log_id)
    if not log or log.user_id != user_id:
        raise HTTPException(status_code=404, detail="Log entry not found.")
    db.delete(log)
    db.commit()
    return


# --- ANALYTICS DASHBOARD ---

@router.get("/analytics/dashboard", response_model=schemas.DashboardResponse)
def get_dashboard_data(user_id: int, db: Session = Depends(get_db)):
    """Generate dynamic dashboard response containing baselines, savings, and insights."""
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    profile = db.execute(select(models.CarbonProfile).where(models.CarbonProfile.user_id == user_id)).scalar_one_or_none()
    
    # 1. Base default calculations if profile doesn't exist
    if not profile:
        return schemas.DashboardResponse(
            user_id=user_id,
            has_profile=False,
            baseline_total_co2_kg_monthly=0.0,
            category_baselines=[],
            logged_savings_co2_kg_monthly=0.0,
            actual_total_co2_kg_monthly=0.0,
            recent_logs=[],
            insights=["Please set up your profile to generate carbon baseline statistics."]
        )

    # 2. Compute category baselines
    baselines = analytics.calculate_baseline(profile)
    baseline_total = sum(baselines.values())

    # 3. Pull recent logs to calculate savings
    logs = db.execute(
        select(models.DailyLog)
        .where(models.DailyLog.user_id == user_id)
    ).scalars().all()

    savings_calc = analytics.calculate_savings(list(logs))
    total_savings = savings_calc["total_savings_kg"]

    # 4. Generate dynamic insights
    insights = analytics.generate_personalized_insights(profile, baselines, savings_calc)

    # 5. Fetch recent 10 logs for display
    recent_logs = db.execute(
        select(models.DailyLog)
        .where(models.DailyLog.user_id == user_id)
        .order_by(models.DailyLog.logged_date.desc(), models.DailyLog.created_at.desc())
        .limit(10)
    ).scalars().all()

    category_emissions_list = [
        schemas.CategoryEmissions(category=cat, co2_kg_monthly=val)
        for cat, val in baselines.items()
    ]

    actual_total = max(0.0, baseline_total - total_savings)
    unlocked = analytics.calculate_unlocked_badges(profile, list(logs), baseline_total, total_savings)

    return schemas.DashboardResponse(
        user_id=user_id,
        has_profile=True,
        baseline_total_co2_kg_monthly=round(baseline_total, 2),
        category_baselines=category_emissions_list,
        logged_savings_co2_kg_monthly=round(total_savings, 2),
        actual_total_co2_kg_monthly=round(actual_total, 2),
        reduction_goal_percentage=profile.reduction_goal_percentage,
        recent_logs=[schemas.DailyLogResponse.model_validate(log) for log in recent_logs],
        insights=insights,
        unlocked_badges=unlocked
    )


@router.get("/logs/export")
def export_user_logs_csv(user_id: int, db: Session = Depends(get_db)):
    """Export daily action log history for a user as a CSV file."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    logs = db.execute(
        select(models.DailyLog)
        .where(models.DailyLog.user_id == user_id)
        .order_by(models.DailyLog.logged_date.desc(), models.DailyLog.created_at.desc())
    ).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV Header
    writer.writerow(["Date", "Action Category", "Action Title", "Action Description", "Quantity", "CO2 Savings (kg/unit)", "Net CO2 Saved (kg)"])
    
    # Write CSV Rows
    for log in logs:
        writer.writerow([
            log.logged_date.strftime("%Y-%m-%d"),
            log.action.category,
            log.action.title,
            log.action.description,
            log.quantity,
            log.action.co2_savings_kg,
            round(log.quantity * log.action.co2_savings_kg, 2)
        ])
    
    output.seek(0)
    filename = f"ecotrace_logs_user_{user_id}_{date.today().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.StringIO(output.getvalue()), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
