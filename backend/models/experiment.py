"""实验设计相关 Pydantic 模型"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ExperimentDesignRequest(BaseModel):
    research_question: str = Field(..., min_length=1, description="研究问题")
    search_methods: bool = True


class RecommendMethodsRequest(BaseModel):
    research_question: str = Field(..., min_length=1)


class DesignWithRecommendationsRequest(BaseModel):
    research_question: str = Field(..., min_length=1)


class ValidateDesignRequest(BaseModel):
    design_text: str = Field(..., min_length=1)


class ExperimentDesignResponse(BaseModel):
    research_question: str
    full_design: str
    method_recommendations: str = ""


class RecommendMethodsResponse(BaseModel):
    research_question: str
    recommendations: str


class ValidateDesignResponse(BaseModel):
    checks: Dict[str, bool]
    completeness: str
    missing: List[str]
