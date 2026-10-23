"""论文写作相关 Pydantic 模型"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class GenerateSectionRequest(BaseModel):
    section: str = Field(
        ...,
        pattern="^(abstract|introduction|methods|results|discussion)$",
        description="章节名称"
    )
    context: Dict[str, Any]
    style: str = "通用学术规范 (General Academic)"


class GenerateFullRequest(BaseModel):
    context: Dict[str, Any]
    style: str = "通用学术规范 (General Academic)"


class WritingTipsRequest(BaseModel):
    section: str = Field(
        ...,
        pattern="^(abstract|introduction|methods|results|discussion)$"
    )
    style: str = "通用学术规范 (General Academic)"


class FormatCheckRequest(BaseModel):
    text: str = Field(..., min_length=1)
    style: str = "通用学术规范 (General Academic)"


class SectionResponse(BaseModel):
    section: str
    content: str


class FullPaperResponse(BaseModel):
    title: str
    abstract: str
    introduction: str
    methods: str
    results: str
    discussion: str
    references: List[str]
    target_journal_style: str


class WritingTipsResponse(BaseModel):
    section: str
    style: str
    tips: str


class FormatCheckResponse(BaseModel):
    checks: Dict[str, bool]
    style: str
    score: float
