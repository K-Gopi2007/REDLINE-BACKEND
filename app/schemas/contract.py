from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class ContractBase(BaseModel):
    title: str

class ContractCreate(ContractBase):
    content: str

class ContractResponse(ContractBase):
    id: int
    user_id: int
    created_at: datetime
    content: str

    class Config:
        from_attributes = True

class RiskIssue(BaseModel):
    clause: str
    category: str
    severity: str
    reason: str

class RiskReportResponse(BaseModel):
    risk_score: int
    risk_level: str
    issues: List[RiskIssue]

class NegotiationSuggestion(BaseModel):
    original_clause: str
    suggested_clause: str
    reasoning: str

class NegotiationReportResponse(BaseModel):
    suggestions: List[NegotiationSuggestion]

class DraftRequest(BaseModel):
    prompt: str
