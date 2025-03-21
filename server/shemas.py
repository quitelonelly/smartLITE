from pydantic import BaseModel
from typing import List, Dict, Optional

class RoleAnalysis(BaseModel):
    text: str
    speaker: str
    role: str
    start_time: int
    end_time: int

class StageAnalysis(BaseModel):
    qualified: bool
    reason: str
    recommendation: Optional[str] = None

class LeadAnalysis(BaseModel):
    stages: Dict[str, StageAnalysis]
    final_verdict: str
    final_reason: str
    final_full_reason: str
    kval_percentage: float

class TranscriptionData(BaseModel):
    status: str
    transcript: str
    role_analysis: List[RoleAnalysis]
    lead_analysis: LeadAnalysis
    parasite_words_analysis: str
    agreement: str  # Добавляем поле agreement