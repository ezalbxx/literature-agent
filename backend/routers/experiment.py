"""实验方案设计 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.models.experiment import (
    ExperimentDesignRequest,
    RecommendMethodsRequest,
    DesignWithRecommendationsRequest,
    ValidateDesignRequest,
    ExperimentDesignResponse,
    RecommendMethodsResponse,
    ValidateDesignResponse,
)
from agents.experiment_designer import ExperimentDesigner

router = APIRouter(prefix="/api/experiment", tags=["Experiment Design"])


@router.post("/design", response_model=ExperimentDesignResponse)
def design(request: ExperimentDesignRequest):
    """生成实验设计方案"""
    try:
        designer = ExperimentDesigner()
        result = designer.design_experiment(
            request.research_question,
            search_methods=request.search_methods,
        )
        return ExperimentDesignResponse(
            research_question=result.research_question,
            full_design=result.full_design,
            method_recommendations=result.method_recommendations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-methods", response_model=RecommendMethodsResponse)
def recommend_methods(request: RecommendMethodsRequest):
    """推荐实验方法和数据分析技术"""
    try:
        designer = ExperimentDesigner()
        recommendations = designer.recommend_methods(request.research_question)
        return RecommendMethodsResponse(
            research_question=request.research_question,
            recommendations=recommendations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design-with-recommendations", response_model=ExperimentDesignResponse)
def design_with_recommendations(request: DesignWithRecommendationsRequest):
    """一站式：方法推荐 + 完整实验设计"""
    try:
        designer = ExperimentDesigner()
        result = designer.design_with_recommendations(request.research_question)
        return ExperimentDesignResponse(
            research_question=result.research_question,
            full_design=result.full_design,
            method_recommendations=result.method_recommendations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidateDesignResponse)
def validate(request: ValidateDesignRequest):
    """验证实验设计完整性"""
    try:
        designer = ExperimentDesigner()
        result = designer.validate_design(request.design_text)
        return ValidateDesignResponse(
            checks=result['checks'],
            completeness=result['completeness'],
            missing=result['missing'],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
