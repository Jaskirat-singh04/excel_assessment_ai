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
    score: Optional[int] = Field(default=None, ge=0, le=100, description="Overall score out of 100")
    technical_accuracy: Optional[int] = Field(default=None, ge=0, le=30, description="Technical accuracy score out of 30")
    pivot_tables: Optional[int] = Field(default=None, ge=0, le=25, description="Pivot tables score out of 25")
    visualization: Optional[int] = Field(default=None, ge=0, le=20, description="Charts and visualization score out of 20")
    data_organization: Optional[int] = Field(default=None, ge=0, le=15, description="Data organization score out of 15")
    presentation: Optional[int] = Field(default=None, ge=0, le=10, description="Professional presentation score out of 10")
    feedback: Optional[str] = Field(default=None, description="Qualitative feedback")
    recommendations: Optional[List[str]] = Field(
        default_factory=list,
        description="Recommended improvements or next steps"
    ) 