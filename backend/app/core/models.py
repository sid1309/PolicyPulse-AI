from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class TableData(BaseModel):
    headers: List[str] = []
    rows: List[List[str]] = []
    markdown_representation: str = ""
    page_number: int
    bbox: Optional[List[float]] = None

class ClauseChunk(BaseModel):
    chunk_id: str
    policy_id: str
    insurer: str = "Unknown Insurer"
    plan_name: str = "Standard Health"
    version: str = "1.0"
    section_name: str = "General Provisions"
    clause_id: str = "Clause"
    clause_title: str = "Terms"
    page_number: int = 1
    page_range: List[int] = [1]
    chunk_type: str = "clause"  # "clause", "table", "definition", "condition"
    content_text: str
    bbox: Optional[List[float]] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    
class PolicyMetadata(BaseModel):
    policy_id: str
    filename: str
    insurer: str
    plan_name: str
    version: str
    total_pages: int
    chunk_count: int
    file_path: str
    created_at: str

class CitationItem(BaseModel):
    policy_id: str
    insurer: str
    plan_name: str
    section_name: str
    clause_id: str
    clause_title: str
    page_number: int
    excerpt: str
    bbox: Optional[List[float]] = None
    relevance_score: Optional[float] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatQueryRequest(BaseModel):
    query: str
    policy_ids: List[str] = []
    enable_graph: bool = False
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationItem] = []
    confidence_score: float = 0.0
    intent: str = "GENERAL"
    retrieved_chunks_count: int = 0
    insufficient_evidence: bool = False

class ExplainClauseRequest(BaseModel):
    clause_title: str
    clause_text: str
    verdict: Optional[str] = None
    insurer: Optional[str] = None

class ExplainClauseResponse(BaseModel):
    clause_title: str
    simple_explanation: str
    wallet_impact: str
    action_checklist: List[str]

class PolicySummaryResponse(BaseModel):
    policy_id: str
    insurer: str
    plan_name: str
    version: str
    total_pages: int
    sum_insured: str
    room_rent_cap: str
    icu_limit: str
    ped_waiting_period: str
    specific_illness_waiting: str
    initial_waiting_period: str
    pre_post_hospitalization: str
    copay: str
    restoration_benefit: str
    day_care: str
    key_exclusions: List[str]
    plain_english_summary: str
    citations: List[CitationItem] = []

class ComparisonMatrixItem(BaseModel):
    feature_category: str
    policies: Dict[str, Dict[str, Any]]
    recommendation: str = ""

class ComparisonResponse(BaseModel):
    policy_ids: List[str]
    matrix: List[ComparisonMatrixItem]
    executive_verdict: str

class PolicyDiffItem(BaseModel):
    category: str
    change_type: str  # "EXPANSION", "RESTRICTION", "PROCEDURAL"
    old_clause_text: str
    new_clause_text: str
    old_page: int
    new_page: int
    impact_analysis: str

class PolicyDiffResponse(BaseModel):
    old_policy_id: str
    new_policy_id: str
    summary_of_changes: str
    changes: List[PolicyDiffItem]

class ClaimsAssessmentRequest(BaseModel):
    policy_id: str
    treatment_name: str
    hospital_type: str = "network_cashless"  # "network_cashless" or "non_network_reimbursement"
    room_category_chosen: str = "Single Private Room"
    actual_room_rent_per_day: float = 0.0
    total_room_rent_bill: float = 0.0
    associated_medical_bills: float = 0.0
    incident_date: str = "2026-01-01"
    policy_inception_date: str = "2024-01-01"
    is_pre_existing: bool = False

class ClaimsAssessmentResult(BaseModel):
    policy_id: str
    treatment_name: str
    admissibility_status: str  # "Eligible", "Ineligible (Waiting Period Active)", "Excluded", "Conditional"
    status_reason: str
    waiting_period_details: Dict[str, Any] = {}
    room_rent_math: Dict[str, Any] = {}
    financial_breakdown: Dict[str, float] = {}
    document_checklist: List[str] = []
    citations: List[CitationItem] = []
