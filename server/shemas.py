# Модель для анализа ролей
from pydantic import BaseModel
from typing import List, Dict

class RoleAnalysis(BaseModel):
    text: str
    speaker: str
    role: str
    start_time: int
    end_time: int

# Модель для анализа этапов
class StageAnalysis(BaseModel):
    qualified: bool
    reason: str
    recommendation: str

# Модель для анализа лида
class LeadAnalysis(BaseModel):
    stages: Dict[str, StageAnalysis]
    final_verdict: str
    final_reason: str

# Модель для основного JSON
class TranscriptionData(BaseModel):
    status: str
    transcript: str
    role_analysis: List[RoleAnalysis]
    lead_analysis: LeadAnalysis