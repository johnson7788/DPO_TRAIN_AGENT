"""
FastAPI 后端服务 - 读取 DPO 数据集并提供给前端
"""
import json
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

DATA_FILE = os.path.join(os.path.dirname(__file__), "dpo_dataset.jsonl")

# 内存缓存数据集
_dataset_cache: list[dict] = []
_cache_loaded = False


def load_dataset():
    """加载数据集到内存"""
    global _dataset_cache, _cache_loaded
    if _cache_loaded:
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                _dataset_cache.append(json.loads(line))
    _cache_loaded = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dataset()
    yield


app = FastAPI(
    title="DPO Dataset API",
    description="RLHF DPO 数据集浏览 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DataItem(BaseModel):
    tools: list
    messages: list
    rejected_messages: Optional[list] = None
    metadata: dict


class TotalResponse(BaseModel):
    total: int


@app.get("/", response_model=TotalResponse)
async def root():
    """获取数据集总数"""
    return {"total": len(_dataset_cache)}


@app.get("/count")
async def get_count():
    """获取数据集总数（简化端点）"""
    return {"total": len(_dataset_cache)}


@app.get("/data/{index}", response_model=DataItem)
async def get_data_by_index(index: int = Path(..., ge=0, description="数据索引")):
    """根据索引获取数据项"""
    if index < 0 or index >= len(_dataset_cache):
        raise HTTPException(status_code=404, detail=f"索引 {index} 超出范围")
    return _dataset_cache[index]


@app.get("/data", response_model=DataItem)
async def get_data(
    index: int = Query(0, ge=0, description="数据索引")
):
    """获取指定索引的数据（可选参数）"""
    if index < 0 or index >= len(_dataset_cache):
        raise HTTPException(status_code=404, detail=f"索引 {index} 超出范围")
    return _dataset_cache[index]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
