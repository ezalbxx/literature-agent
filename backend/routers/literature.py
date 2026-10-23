"""文献检索 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.models.literature import (
    SearchRequest,
    SearchAndReviewRequest,
    ExportBibtexRequest,
    SearchOnlyResponse,
    SearchResultResponse,
    BibtexResponse,
)
from agents.literature_agent import LiteratureAgent

router = APIRouter(prefix="/api/literature", tags=["Literature"])


@router.post("/search", response_model=SearchOnlyResponse)
def search(request: SearchRequest):
    """跨库检索文献（仅检索，不生成综述）"""
    try:
        agent = LiteratureAgent()
        articles = agent.cross_search(
            request.query,
            request.pubmed_max,
            request.arxiv_max,
        )
        pubmed_count = sum(1 for a in articles if a.get('source') == 'PubMed')
        arxiv_count = sum(1 for a in articles if a.get('source') == 'arXiv')
        return SearchOnlyResponse(
            query=request.query,
            total_pubmed=pubmed_count,
            total_arxiv=arxiv_count,
            articles=articles,
            source_status=agent.source_status,
            warnings=agent.warnings,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-and-review", response_model=SearchResultResponse)
def search_and_review(request: SearchAndReviewRequest):
    """一站式：检索 + 生成结构化综述 + 生成简明摘要"""
    try:
        agent = LiteratureAgent()
        result = agent.search_and_review(
            request.query,
            request.pubmed_max,
            request.arxiv_max,
        )
        return SearchResultResponse(
            query=result.query,
            total_pubmed=result.total_pubmed,
            total_arxiv=result.total_arxiv,
            articles=result.articles,
            structured_review=result.structured_review,
            abstract_summary=result.abstract_summary,
            source_status=result.source_status,
            warnings=result.warnings,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-bibtex", response_model=BibtexResponse)
def export_bibtex(request: ExportBibtexRequest):
    """导出文献为BibTeX格式"""
    try:
        agent = LiteratureAgent()
        bibtex = agent.export_bibtex(request.articles)
        return BibtexResponse(
            bibtex=bibtex,
            count=len(request.articles),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
