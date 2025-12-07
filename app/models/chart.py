from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base

class ChartUpload(Base):
    __tablename__ = "chart_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    asset = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChartAnalysisResult(Base):
    __tablename__ = "chart_analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, nullable=False)
    asset = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    result_json = Column(Text, nullable=False)  # Store full JSON response
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
