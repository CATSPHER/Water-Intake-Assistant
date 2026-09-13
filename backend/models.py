from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.sql import func
from database import Base


class HydrationLog(Base):
    __tablename__ = "hydration_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # MongoDB _id from MERN app
    amount_ml = Column(Integer, nullable=False)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    log_date = Column(Date, index=True, nullable=False)  # for fast daily/monthly queries
