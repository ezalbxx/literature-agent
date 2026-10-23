"""每个角色交付的数据契约；不让下游靠解析散乱聊天猜上游结果。"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Citation(StrictModel):
    chunk_id: str
    quote: str = Field(min_length=12, max_length=1200)


class Claim(StrictModel):
    text: str = Field(min_length=1, max_length=2000)
    citations: list[Citation] = Field(min_length=1, max_length=5)


class Review(StrictModel):
    synthesis: str = Field(min_length=1, max_length=8000)
    evidence: list[Claim] = Field(min_length=1, max_length=12)


class GapCandidate(StrictModel):
    question: str = Field(min_length=1, max_length=500)
    rationale: str = Field(min_length=1, max_length=2000)
    # Hypotheses about gaps, not assertions that no one has studied a subject.
    uncertainty: str = Field(min_length=1, max_length=1000)


class Gaps(StrictModel):
    candidates: list[GapCandidate] = Field(min_length=1, max_length=5)
    evidence: list[Claim] = Field(min_length=1, max_length=12)


class Experiment(StrictModel):
    hypothesis: str = Field(min_length=1, max_length=2000)
    steps: list[str] = Field(min_length=1, max_length=10)
    controls: list[str] = Field(min_length=1, max_length=10)
    metrics: list[str] = Field(min_length=1, max_length=10)
    risks: list[str] = Field(min_length=1, max_length=10)
    evidence: list[Claim] = Field(min_length=1, max_length=12)


class Draft(StrictModel):
    background: str = Field(min_length=1, max_length=8000)
    proposed_methods: str = Field(min_length=1, max_length=8000)
    outline: list[str] = Field(min_length=1, max_length=10)
    evidence: list[Claim] = Field(min_length=1, max_length=12)


SCHEMAS = {'review': Review, 'gaps': Gaps, 'experiment': Experiment, 'draft': Draft}
STAGES = list(SCHEMAS)
ROLES = {'review': 'ReviewAgent', 'gaps': 'GapAgent', 'experiment': 'ExperimentAgent', 'draft': 'WritingAgent'}
