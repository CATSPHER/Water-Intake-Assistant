import os
from datetime import date, timedelta
from typing import List
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
from ai_feedback import generate_feedback

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hydration Tracker AI Service")

# Restrict this to your actual Vercel + Node domains in production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/api/hydration/log", response_model=schemas.HydrationLogOut)
def log_intake(payload: schemas.HydrationLogCreate, db: Session = Depends(get_db)):
    entry = models.HydrationLog(
        user_id=payload.user_id,
        amount_ml=payload.amount_ml,
        log_date=date.today(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/api/hydration/logs/today", response_model=List[schemas.HydrationLogOut])
def get_today_logs(user_id: str, db: Session = Depends(get_db)):
    entries = (
        db.query(models.HydrationLog)
        .filter(models.HydrationLog.user_id == user_id, models.HydrationLog.log_date == date.today())
        .order_by(models.HydrationLog.logged_at.asc())
        .all()
    )
    return entries


@app.get("/api/hydration/logs/monthly", response_model=List[schemas.DailyTotal])
def get_monthly_totals(user_id: str, db: Session = Depends(get_db)):
    start = date.today() - timedelta(days=30)
    rows = (
        db.query(models.HydrationLog.log_date, func.sum(models.HydrationLog.amount_ml).label("total_ml"))
        .filter(models.HydrationLog.user_id == user_id, models.HydrationLog.log_date >= start)
        .group_by(models.HydrationLog.log_date)
        .order_by(models.HydrationLog.log_date.asc())
        .all()
    )
    return [{"log_date": r.log_date, "total_ml": r.total_ml} for r in rows]


@app.post("/api/hydration/feedback", response_model=schemas.FeedbackResponse)
def get_feedback(payload: schemas.FeedbackRequest, db: Session = Depends(get_db)):
    today_total = (
        db.query(func.sum(models.HydrationLog.amount_ml))
        .filter(models.HydrationLog.user_id == payload.user_id, models.HydrationLog.log_date == date.today())
        .scalar()
    ) or 0

    start = date.today() - timedelta(days=7)
    history_rows = (
        db.query(models.HydrationLog.log_date, func.sum(models.HydrationLog.amount_ml).label("total_ml"))
        .filter(models.HydrationLog.user_id == payload.user_id, models.HydrationLog.log_date >= start)
        .group_by(models.HydrationLog.log_date)
        .order_by(models.HydrationLog.log_date.asc())
        .all()
    )
    recent_history = [r.total_ml for r in history_rows]

    try:
        feedback_text = generate_feedback(today_total, payload.daily_goal_ml, recent_history)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI feedback generation failed: {e}")

    percent = round((today_total / payload.daily_goal_ml) * 100, 1) if payload.daily_goal_ml else 0

    return {
        "feedback": feedback_text,
        "today_total_ml": today_total,
        "goal_ml": payload.daily_goal_ml,
        "percent_of_goal": percent,
    }
