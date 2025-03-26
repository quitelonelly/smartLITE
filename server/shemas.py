from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union

class RoleAnalysis(BaseModel):
    text: str
    role: str
    start_time: int
    end_time: int

class ManagerEvaluationDetail(BaseModel):
    score: int
    reason: str

class ManagerEvaluation(BaseModel):
    score: int
    explanation: str
    details: Dict[str, ManagerEvaluationDetail]

class LeadQualification(BaseModel):
    qualified: str  # "да" или "нет"
    criteria: List[str] = Field(default_factory=list)

class ObjectionHandling(BaseModel):
    evaluation: str  # "да" или "нет"
    has_objections: bool
    na_option: bool = False

class ClientReadiness(BaseModel):
    level: str  # "Не интересно", "Слабый интерес", "Сильный интерес"
    explanation: str

class ManagerConfidence(BaseModel):
    confidence: str  # "уверен" или "не уверен"
    criteria: List[str]

class ProductExpertise(BaseModel):
    level: str  # уровень экспертизы
    is_na: bool  # True если вопросы о продукте отсутствовали

class RecommendationItem(BaseModel):
    quote: Optional[str] = None
    analysis: Optional[str] = None
    advice: Optional[str] = None

class Recommendation(BaseModel):
    error: RecommendationItem

class TranscriptionData(BaseModel):
    summary: str
    transcript: str
    role_analysis: List[RoleAnalysis]
    manager_evaluation: ManagerEvaluation
    manager_errors: List[str]
    dialogue_outcomes: str
    lead_qualification: LeadQualification
    lead_lost: Optional[str] = None
    objection_handling: ObjectionHandling
    client_readiness: ClientReadiness
    manager_confidence: ManagerConfidence
    product_expertise: ProductExpertise
    recommendations: List[Dict[str, RecommendationItem]]
    token_usage: Optional[Dict] = None