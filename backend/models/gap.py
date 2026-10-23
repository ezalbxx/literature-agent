"""研究空白分析相关 Pydantic 模型"""

from pydantic import BaseModel, Field
from typing import List


class GapAnalyzeRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="研究领域/主题")
    deep_search: bool = True


class GapHotspotsRequest(BaseModel):
    topic: str = Field(..., min_length=1)


class GapDetectRequest(BaseModel):
    topic: str = Field(..., min_length=1)


class GapAnalysisResponse(BaseModel):
    topic: str
    hotspots: str
    trends: str
    gaps: str
    hot_keywords: List[str]
    emerging_keywords: List[str]


class HotspotsOnlyResponse(BaseModel):
    topic: str
    hotspots: str
    hot_keywords: List[str]
    emerging_keywords: List[str]


class DetectGapsResponse(BaseModel):
    topic: str
    gaps: str
    trends: str
    suggestions: List[str]
