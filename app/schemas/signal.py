from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class SignalBase(BaseModel):
    asset_type: str
    symbol: str
    pair: str
    signal_type: str
    oracle_score: int
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    risk_reward_ratio: float
    reasoning_summary: str
    reasoning_factors: Dict[str, str]
    timeframe: str

class SignalCreate(SignalBase):
    model_version: str
    input_snapshot: Dict[str, Any]
    data_sources: List[str]
    expires_at: datetime
    position_size_suggestion: Optional[float] = None

class SignalResponse(SignalBase):
    id: int
    status: str
    outcome_pnl_percent: Optional[float]
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True

class SignalListResponse(BaseModel):
    signals: List[SignalResponse]
    total: int
    page: int
    per_page: int

class SignalOutcome(BaseModel):
    status: str
    outcome_price: float
    outcome_pnl_percent: float
