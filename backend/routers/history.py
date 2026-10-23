"""历史记录管理 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.models.history import (
    SaveRequest, SaveResponse,
    ListResponse, GetResponse, DeleteResponse,
)
from utils.storage import save_result, list_saved, get_saved, delete_saved

router = APIRouter(prefix="/api/history", tags=["History"])


@router.post("/save", response_model=SaveResponse)
def save(request: SaveRequest):
    """保存查询结果"""
    try:
        item_id = save_result(
            module=request.module,
            title=request.title,
            query=request.query,
            data=request.data,
        )
        return SaveResponse(id=item_id, message="保存成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ListResponse)
def list_records(module: str = None):
    """列出所有已保存结果（可按模块筛选）"""
    try:
        items = list_saved(module=module)
        return ListResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{item_id}", response_model=GetResponse)
def get_record(item_id: str):
    """获取单条保存记录详情"""
    record = get_saved(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return GetResponse(
        id=record["id"],
        module=record["module"],
        title=record["title"],
        query=record["query"],
        timestamp=record["timestamp"],
        data=record["data"],
    )


@router.delete("/delete/{item_id}", response_model=DeleteResponse)
def delete_record(item_id: str):
    """删除保存记录"""
    success = delete_saved(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return DeleteResponse(success=True, message="已删除")
