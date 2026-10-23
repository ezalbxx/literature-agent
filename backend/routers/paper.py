"""论文写作辅助 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.models.paper import (
    GenerateSectionRequest,
    GenerateFullRequest,
    WritingTipsRequest,
    FormatCheckRequest,
    SectionResponse,
    FullPaperResponse,
    WritingTipsResponse,
    FormatCheckResponse,
)
from agents.paper_writer import PaperWriter

router = APIRouter(prefix="/api/paper", tags=["Paper Writing"])


@router.post("/generate-section", response_model=SectionResponse)
def generate_section(request: GenerateSectionRequest):
    """生成单个章节草稿"""
    try:
        writer = PaperWriter()
        content = writer.generate_section(
            request.section,
            request.context,
            request.style,
        )
        return SectionResponse(
            section=request.section,
            content=content,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-full", response_model=FullPaperResponse)
def generate_full(request: GenerateFullRequest):
    """生成完整论文草稿（所有章节）"""
    try:
        writer = PaperWriter()
        draft = writer.generate_full_paper(request.context, request.style)
        return FullPaperResponse(
            title=draft.title,
            abstract=draft.abstract,
            introduction=draft.introduction,
            methods=draft.methods,
            results=draft.results,
            discussion=draft.discussion,
            references=draft.references,
            target_journal_style=draft.target_journal_style,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writing-tips", response_model=WritingTipsResponse)
def writing_tips(request: WritingTipsRequest):
    """获取写作提示"""
    try:
        writer = PaperWriter()
        tips = writer.get_writing_tips(request.section, request.style)
        return WritingTipsResponse(
            section=request.section,
            style=request.style,
            tips=tips,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/format-check", response_model=FormatCheckResponse)
def format_check(request: FormatCheckRequest):
    """检查格式规范"""
    try:
        writer = PaperWriter()
        result = writer.format_check(request.text, request.style)
        return FormatCheckResponse(
            checks=result['checks'],
            style=result['style'],
            score=result['score'],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
