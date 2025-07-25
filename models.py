from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Pydantic models for structured evaluation output
class DetailedAnalysis(BaseModel):
    technical_accuracy: Optional[str] = Field(default=None, description="Assessment of formulas and calculations")
    pivot_tables: Optional[str] = Field(default=None, description="Assessment of pivot table usage")
    charts_visualization: Optional[str] = Field(default=None, description="Assessment of charts and visual elements")
    data_organization: Optional[str] = Field(default=None, description="Assessment of data structure and organization")
    advanced_features: Optional[str] = Field(default=None, description="Assessment of advanced Excel features used")

class EvaluationFeedback(BaseModel):
    score: Optional[int] = Field(default=None, ge=0, le=10, description="Score out of 10")
    feedback: Optional[str] = Field(default=None, description="Qualitative feedback")
    recommendations: Optional[List[str]] = Field(
        default_factory=list,
        description="Recommended improvements or next steps"
    ) 