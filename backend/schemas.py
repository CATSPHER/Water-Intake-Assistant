from datetime import datetime, date
from pydantic import BaseModel, Field


class HydrationLogCreate(BaseModel):
    user_id: str
    amount_ml: int = Field(gt=0, le=5000, description="Amount of water in ml, e.g. 250")


class HydrationLogOut(BaseModel):
    id: int
    user_id: str
    amount_ml: int
    logged_at: datetime
    log_date: date

    class Config:
        from_attributes = True


class DailyTotal(BaseModel):
    log_date: date
    total_ml: int


class FeedbackRequest(BaseModel):
    user_id: str
    daily_goal_ml: int = 2500  # user's target, default 2.5L


class FeedbackResponse(BaseModel):
    feedback: str
    today_total_ml: int
    goal_ml: int
    percent_of_goal: float
