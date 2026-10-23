"""研究空白分析 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.models.gap import (
    GapAnalyzeRequest,
    GapHotspotsRequest,
    GapDetectRequest,
    GapAnalysisResponse,
    HotspotsOnlyResponse,
    DetectGapsResponse,
)
from agents.gap_analyzer import GapAnalyzer

router = APIRouter(prefix="/api/gap", tags=["Gap Analysis"])


@router.post("/analyze", response_model=GapAnalysisResponse)
def analyze(request: GapAnalyzeRequest):
    """完整分析：热点 + 趋势 + 空白"""
    try:
        analyzer = GapAnalyzer()
        result = analyzer.analyze(request.topic, deep_search=request.deep_search)
        return GapAnalysisResponse(
            topic=result.topic,
            hotspots=result.hotspots,
            trends=result.trends,
            gaps=result.gaps,
            hot_keywords=result.hot_keywords,
            emerging_keywords=result.emerging_keywords,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hotspots", response_model=HotspotsOnlyResponse)
def hotspots(request: GapHotspotsRequest):
    """仅热点分析（轻量）"""
    try:
        analyzer = GapAnalyzer()
        result = analyzer.analyze_hotspots_only(request.topic)
        return HotspotsOnlyResponse(
            topic=result['topic'],
            hotspots=result['hotspots'],
            hot_keywords=result['hot_keywords'],
            emerging_keywords=result['emerging_keywords'],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-gaps", response_model=DetectGapsResponse)
def detect_gaps(request: GapDetectRequest):
    """仅空白探测（深度分析）"""
    try:
        analyzer = GapAnalyzer()
        result = analyzer.detect_gaps_only(request.topic)
        return DetectGapsResponse(
            topic=result['topic'],
            gaps=result['gaps'],
            trends=result['trends'],
            suggestions=result['suggestions'],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
