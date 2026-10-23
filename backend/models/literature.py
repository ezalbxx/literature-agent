"""文献检索相关 Pydantic 模型"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


# --- 请求模型 ---
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="搜索查询关键词")
    pubmed_max: int = Field(30, ge=5, le=100)
    arxiv_max: int = Field(20, ge=5, le=50)


class SearchAndReviewRequest(BaseModel):
    query: str = Field(..., min_length=1)
    pubmed_max: int = Field(30, ge=5, le=100)
    arxiv_max: int = Field(20, ge=5, le=50)


class ExportBibtexRequest(BaseModel):
    articles: List[Dict[str, Any]]


# --- 响应模型 ---
class SearchOnlyResponse(BaseModel):
    query: str
    total_pubmed: int
    total_arxiv: int
    articles: List[Dict[str, Any]]
    source_status: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class SearchResultResponse(BaseModel):
    query: str
    total_pubmed: int
    total_arxiv: int
    articles: List[Dict[str, Any]]
    structured_review: str
    abstract_summary: str
    source_status: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class BibtexResponse(BaseModel):
    bibtex: str
    count: int
