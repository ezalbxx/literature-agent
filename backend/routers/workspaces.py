from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from backend.routers.library import library
from coordination.workspace import WorkspaceStore, ResearchCoordinator, OfflineStageModel
from rag.assistant import OpenAIToolModel

router = APIRouter(prefix='/api/workspaces', tags=['Research coordination'])


class Create(BaseModel):
    topic: str = Field(min_length=1, max_length=1000)
    collection: str | None = None


class Run(BaseModel):
    stage: Literal['review','gaps','experiment','draft']
    offline_demo: bool = True


class Select(BaseModel):
    candidate_index: int = Field(ge=0, le=4)


def execute(action):
    try:
        return action()
    except KeyError:
        raise HTTPException(404,'研究工作区不存在') from None
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from None
    except RuntimeError as exc:
        raise HTTPException(502,str(exc)) from None


@router.post('')
def create(request: Create):
    return execute(lambda: WorkspaceStore(library()).create(request.topic, request.collection))


@router.get('/{identifier}')
def get(identifier: str):
    return execute(lambda: ResearchCoordinator(library()).sync(identifier))


@router.post('/{identifier}/select')
def select(identifier: str, request: Select):
    return execute(lambda: ResearchCoordinator(library()).select(identifier, request.candidate_index))


@router.post('/{identifier}/run')
def run(identifier: str, request: Run):
    def action():
        model = OfflineStageModel() if request.offline_demo else OpenAIToolModel()
        return ResearchCoordinator(library()).run(identifier, request.stage, model, request.offline_demo)
    return execute(action)
