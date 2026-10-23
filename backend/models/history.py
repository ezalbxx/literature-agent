"""历史记录相关 Pydantic 模型"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SaveRequest(BaseModel):
    module: str = Field(..., pattern="^(literature|gap|experiment|paper)$")
    title: str = Field(..., min_length=1)
    query: str = ""
    data: Dict[str, Any]


class SaveResponse(BaseModel):
    id: str
    message: str = "保存成功"


class SavedItem(BaseModel):
    id: str
    module: str
    title: str
    query: str
    timestamp: str
    preview: str


class ListResponse(BaseModel):
    items: List[SavedItem]
    total: int


class GetResponse(BaseModel):
    id: str
    module: str
    title: str
    query: str
    timestamp: str
    data: Dict[str, Any]


class DeleteResponse(BaseModel):
    success: bool
    message: str
